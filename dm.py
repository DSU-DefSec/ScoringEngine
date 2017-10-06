import db
from model import *
import importlib
import pickle
import json
import copy

class DataManager(object):

    def reload(self):
        self.load_settings()
        self.teams = self.load_teams()
        self.credentials = self.load_credentials(self.teams)
        self.check_ios = self.load_check_ios(self.credentials)
        self.checks = self.load_checks(self.check_ios)
        self.services = self.load_services(self.checks)

    def load_settings(self):
        cmd = "SELECT * FROM settings WHERE skey=%s LIMIT 1"
        max_score = db.get(cmd, ("maxscore"))[0][2]
        interval = db.get(cmd, ("interval"))[0][2]
        jitter = db.get(cmd, ("jitter"))[0][2]
        self.max_score = int(max_score)
        self.interval = int(interval)
        self.jitter = int(jitter)
    
    def load_teams(self):
        teams = []
        rows = db.get("SELECT * FROM team")
        for team_id, name, subnet in rows:
            team = Team(name, subnet, team_id)
            teams.append(team)
        return teams
    
    def load_services(self, checks):
        services = []
        service_rows = db.get("SELECT * FROM service")
        for service_id, host, port in service_rows:
            schecks = []
            for check in checks:
                if check.service_id == service_id:
                    schecks.append(check)

            service = Service(host, port, schecks, service_id)
            for check in schecks:
               check.service = service
            services.append(service)
        return services
    
    def load_checks(self, check_ios):
        checks = []
        cmd = "SELECT * FROM service_check ORDER BY name ASC" 
        check_rows = db.get(cmd)
        for check_id, name, check_string, poller_string, service_id in check_rows:
            ios = []
            for check_io in check_ios:
                if check_io.check_id == check_id:
                    ios.append(check_io)

            check_function = load_module(check_string)
            poller_class = load_module(poller_string)
            poller = poller_class()
            check = Check(check_id, name, check_function, ios, poller, service_id)
            for check_io in ios:
                check_io.check = check

            checks.append(check)
        return checks
    
    
    def load_check_ios(self, credentials):
        check_ios = []
    
        check_io_rows = db.get("SELECT * FROM check_io")
        for check_io_id, check_input, expected, check_id in check_io_rows:
            cred_input_rows = db.get("SELECT * FROM cred_input WHERE check_io_id=%s", (check_io_id))
            check_creds = []
            for cred_input_id, cred_id, _check_io_id in cred_input_rows:
                check_creds.append(next(filter(lambda c: c.id == cred_id, credentials)))
            poll_input = pickle.loads(check_input)
            expected = json.loads(expected)
            check_io = CheckIO(check_io_id, poll_input, expected, check_creds, check_id)
            for cred in check_creds:
                cred.check_io = check_io

            check_ios.append(check_io)
        return check_ios
    
    def load_credentials(self, teams):
        creds = []
        cred_rows = db.get("SELECT * FROM credential")
        for cred_id, username, password, team_id, service_id in cred_rows:
            team = next(filter(lambda t: t.id == team_id, teams))
            cred = Credential(cred_id, username, password, team)
            creds.append(cred)
        return creds

    def reset_db(self):
        db.execute("DELETE FROM team")
        db.execute("DELETE FROM service")
        db.execute("DELETE FROM service_check")
        db.execute("DELETE FROM check_io")
        db.execute("DELETE FROM credential")
        db.execute("DELETE FROM result")

    def write_settings(self, settings):
        cmd = ("INSERT INTO settings (skey, value) "
               "VALUES (%s, %s)")
        for key, value in settings.items():
            db.execute(cmd, (key, value))

    def write_teams(self, teams):
        team_ids = {}

        cmd = "INSERT INTO team (name, subnet) VALUES (%s, %s)"
        for id, team in teams.items():
            db_id = db.execute(cmd, team)
            team_ids[id] = db_id
        return team_ids

    def write_services(self, services):
        service_ids = {}

        cmd = 'INSERT INTO service (host, port) VALUES (%s, %s)'
        for id, service in services.items():
            db_id = db.execute(cmd, service)
            service_ids[id] = db_id
        return service_ids

    def write_checks(self, checks, service_ids):
        check_ids = {}

        cmd = ('INSERT INTO service_check (name, check_function, '
                'poller, service_id) VALUES (%s, %s, %s, %s)')
        for id, check in checks.items():
            name, check_func, poller, psid = check
            sid = service_ids[psid]
            db_id = db.execute(cmd, (name, check_func, poller, sid))
            check_ids[id] = db_id
        return check_ids

    def write_check_ios(self, check_ios, poll_inputs, check_ids):
        check_io_ids = {}

        cmd = ('INSERT INTO check_io (input, expected, check_id) '
                'VALUES (%s, %s, %s)')
        for id, check_io in check_ios.items():
            piid, expected, pcid = check_io
            poll_input = poll_inputs[piid]
            cid = check_ids[pcid]
            db_id = db.execute(cmd, (poll_input, expected, cid))
            check_io_ids[id] = db_id
        return check_io_ids

    def write_credentials(self, credentials, team_ids, check_io_ids):
        credential_ids = {}

        print("Team_ids: ", team_ids)
        print("CheckIO_ids: ", check_io_ids)
        cred_cmd = ('INSERT INTO credential (username, password, '
                    'team_id, service_id) VALUES (%s, %s, %s, %s)')
        cred_io_cmd = ('INSERT INTO cred_input (cred_id, check_io_id) '
                    'VALUES (%s, %s)')
        check_get = 'SELECT check_id FROM check_io WHERE id=%s'
        service_get = 'SELECT service_id FROM service_check WHERE id=%s'
        for id, credential in credentials.items():
            user, passwd, pcio_ids = credential
            cio_ids = [check_io_ids[str(pcio_id)] for pcio_id in pcio_ids]
            service_ids = []
            for cio_id in cio_ids:
                check_id = db.get(check_get, (cio_id))[0]
                service_id = db.get(service_get, (check_id))[0]
                if service_id not in service_ids:
                    service_ids.append(service_id)
                    for team_id in team_ids.values():
                        cred_id = db.execute(cred_cmd, (user, passwd, team_id, service_id))
                        credential_ids[id] = cred_id
                        db.execute(cred_io_cmd, (cred_id, cio_id))
        return check_io_ids

    def load_results(self, rows):
        results = []
        for result_id, check_id, check_io_id, team_id, time, poll_input, poll_result, result in rows:
            check = [c for c in self.checks if c.id == check_id][0]
            check_io = [cio for cio in self.check_ios if cio.id == check_io_id][0]
            team = [t for t in self.teams if t.id == team_id][0]
            poll_input = pickle.loads(poll_input)
            poll_result = pickle.loads(poll_result)
            res = Result(result_id, check, check_io, team, time, poll_input, poll_result, result)
            results.append(res)
        return results

    def get_results(self, team_id, check_id):
        results = []
        cmd = ("SELECT * FROM result WHERE team_id=%s AND check_id=%s "
               "ORDER BY time DESC")
        rows = db.get(cmd, (team_id, check_id))
        results = self.load_results(rows)
        return results

    def latest_results(self):
        results = {}
        for team in self.teams:
            results[team.id] = {}
            for check in self.checks:
                cmd = ("SELECT * FROM result WHERE team_id=%s AND check_id=%s "
                       "ORDER BY time DESC LIMIT 1")
                rows = db.get(cmd, (team.id, check.id))
                try:
                    res = self.load_results(rows)[0]
                    results[team.id][check.id] = res
                except:
                    # Log this
                    pass
        return results


def load_module(module_str):
    parts = module_str.split('.')
    par_module_str = '.'.join(parts[:len(parts)-1])
    module = importlib.import_module(par_module_str)
    module_obj = getattr(module, parts[-1])
    return module_obj
