import db
from model import *
import importlib
import pickle
import json

class DataManager(object):

    def reload(self):
        self.teams = self.load_teams()
        self.credentials = self.load_credentials(self.teams)
        self.check_ios = self.load_check_ios(self.credentials)
        self.checks = self.load_checks(self.check_ios)
        self.services = self.load_services(self.checks)
    
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
                    schecks.append(schecks)

            service = Service(host, port, checks, service_id)
            services.append(service)
        return services
    
    def load_checks(self, check_ios):
        checks = []
        cmd = "SELECT * FROM service_check" 
        check_rows = db.get(cmd)
        for check_id, name, check_string, poller_string, service_id in check_rows:
            ios = []
            for check_io in check_ios:
                if check_io.check_id == check_id:
                    ios.append(check_io)

            check_function = self.load_module(check_string)
            poller_class = self.load_module(poller_string)
            poller = poller_class()
            check = Check(check_id, name, check_function, ios, poller, service_id)
            checks.append(check)
        return checks
    
    
    def load_check_ios(self, credentials):
        check_ios = []
    
        check_io_rows = db.get("SELECT * FROM check_input")
        for check_io_id, check_input, expected, check_id in check_io_rows:
            check_creds = []
            cmd = "SELECT * FROM cred_input WHERE check_input_id=%d" % check_io_id
            cred_input_rows = db.get(cmd)
            for cred_input_id, cred_id, check_io_id in cred_input_rows:
                for cred in credentials:
                    if cred.id == cred_id:
                        check_creds.append(cred)
                        break
    
            poll_input = pickle.loads(check_input.encode())
            expected = json.loads(expected)
            check_io = CheckIO(check_io_id, poll_input, expected, check_creds, check_id)
            check_ios.append(check_io)
        return check_ios
    
    def load_credentials(self, teams):
        creds = []
        cred_rows = db.get("SELECT * FROM credential")
        for cred_id, username, password, team_id in cred_rows:
            for t in teams:
                if t.id == team_id:
                    team = t
                    break
            cred = Credential(cred_id, username, password, team)
            creds.append(cred)
        return creds

    def write_teams(self, teams):
        team_ids = {}

        stmt = "INSERT INTO team (name, subnet) VALUES ('%s', '%s')"
        for id, team in teams.iteritems():
            cmd = stmt % team
            print(cmd)
            db_id = db.execute(cmd)
            team_ids[id] = db_id
        return team_ids

    def reset_db(self):
        db.execute("DELETE FROM team")
        db.execute("DELETE FROM service")
        db.execute("DELETE FROM service_check")
        db.execute("DELETE FROM check_input")
        db.execute("DELETE FROM credential")
        db.execute("DELETE FROM cred_input")
        db.execute("DELETE FROM result")

    def write_services(self, services):
        service_ids = {}

        stmt = 'INSERT INTO service (host, port) VALUES (%s, %s)'
        for id, service in services.iteritems():
            cmd = stmt % service
            print(cmd)
            db_id = db.execute(cmd)
            service_ids[id] = db_id
        return service_ids

    def write_checks(self, checks, service_ids):
        check_ids = {}

        stmt = ('INSERT INTO service_check (name, check_function, '
                'poller, service_id) VALUES ("%s", "%s", "%s", %d)')
        for id, check in checks.iteritems():
            name, check_func, poller, psid = check
            sid = service_ids[psid]
            cmd = stmt % (name, check_func, poller, sid)
            print(cmd)
            db_id = db.execute(cmd)
            check_ids[id] = db_id
        return check_ids

    def write_check_ios(self, check_ios, poll_inputs, check_ids):
        check_io_ids = {}

        stmt = ('INSERT INTO check_input (input, expected, check_id) '
                'VALUES ("%s", "%s", %d)')
        for id, check_io in check_ios.iteritems():
            piid, expected, pcid = check_io
            poll_input = poll_inputs[piid]
            cid = check_ids[pcid]
            cmd = stmt % (poll_input, expected, cid)
            print(cmd)
            db_id = db.execute(cmd)
            check_io_ids[id] = db_id
        return check_io_ids

    def write_credentials(self, credentials, team_ids, check_io_ids):
        credential_ids = {}

        print("Team_ids: ", team_ids)
        print("CheckIO_ids: ", check_io_ids)
        cred_stmt = ('INSERT INTO credential (username, password, '
                     'team_id) VALUES ("%s", "%s", %d)')
        ci_stmt = ('INSERT INTO cred_input (cred_id, check_input_id) '
                   'VALUES (%d, %d)')
        for id, credential in credentials.iteritems():
            user, passwd, pcio_ids = credential
            for team_id in team_ids.values():
                cmd = cred_stmt % (user, passwd, team_id)
                db_id = db.execute(cmd)
                print(cmd)
                credential_ids[id] = db_id
                for pcio_id in pcio_ids:
                    cio_id = check_io_ids[str(pcio_id)]
                    cmd = ci_stmt % (db_id, cio_id)
                    print(cmd)
                    db.execute(cmd)
        return check_io_ids

    def latest_results(self):
        results = {}
        for team in self.teams:
            results[team.id] = {}
            for check in self.checks:
                cmd = ("SELECT * FROM result WHERE team_id=%d AND check_id=%d "
                       "ORDER BY time DESC LIMIT 1")
                cmd = cmd % (team.id, check.id)
                result_id, check_id, team_id, time, result = db.get(cmd)[0]
                res = Result(result_id, check_id, team_id, time, result)
                results[team.id][check.id] = res
        return results


def load_module(module_str):
    parts = module_str.split('.')
    par_module_str = '.'.join(parts[:len(parts)-1])
    module = importlib.import_module(par_module_str)
    module_obj = getattr(module, parts[-1])
    return module_obj
