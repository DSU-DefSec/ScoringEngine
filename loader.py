import db
from model import *
import importlib
import pickle

class Loader(object):

    def __init__(self):
        self.reload()

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
            team = Team(team_id, name, subnet)
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

            service = Service(service_id, host, port, checks)
            services.append(service)
        return services
    
    def load_checks(self, check_ios):
        checks = []
        cmd = "SELECT * FROM service_check" 
        check_rows = db.get(cmd)
        for check_id, check_string, poller_string, service_id in check_rows:
            ios = []
            for check_io in check_ios:
                if check_io.check_id == check_id:
                    ios.append(check_io)

            check_function = self.load_check_func(check_string)
            poller = self.load_poller(poller_string)
            check = Check(check_id, check_function, ios, poller, service_id)
            checks.append(check)
        return checks
    
    def load_check_func(self, check_string):
        parts = check_string.split('.')
        module_str = '.'.join(parts[:len(parts)-1])
        check_module = importlib.import_module(module_str)
        func = getattr(check_module, parts[-1])
        return func

    def load_poller(self, poller_string):
        parts = poller_string.split('.')
        module_str = '.'.join(parts[:len(parts)-1])
        check_module = importlib.import_module(module_str)
        poller_class = getattr(check_module, parts[-1])
        poller = poller_class()
        return poller
    
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
    
            poll_input = pickle.loads(check_input)
            check_io = CheckIO(check_io_id, poll_input, expected, check_creds, check_id)
            check_ios.append(check_io)
        return check_ios
    
    def load_credentials(cursor, teams):
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
