import db
from model import *
import importlib
import pickle
import json
import re

def load_module(module_str):
    """
    Get the module specified by the given string.
    
    Arguments:
        module_str (str): String representing the module's import path

    Returns:
        Module: The module represented by the string
    """
    parts = module_str.split('.')
    par_module_str = '.'.join(parts[:len(parts)-1])
    module = importlib.import_module(par_module_str)
    module_obj = getattr(module, parts[-1])
    return module_obj

class DataManager(object):

    def reset_db(self):
        """
        Delete all data from the database.
        """
        db.execute("DELETE FROM settings")
        db.execute("DELETE FROM team")
        db.execute("DELETE FROM domain")
        db.execute("DELETE FROM service")
        db.execute("DELETE FROM service_check")
        db.execute("DELETE FROM check_io")
        db.execute("DELETE FROM credential")
        db.execute("DELETE FROM result")

    def load_db(self):
        """
        Load all data from the database.
        """
        self.settings = self.load_settings()
        self.teams = self.load_teams()
        self.domains = self.load_domains()
        self.credentials = self.load_credentials(self.teams, self.domains)

        # Load check IOs
        check_ios = self.load_check_ios(self.credentials)
        self.check_ios = list(check_ios.values())
        self.check_ios = [ci for sublist in self.check_ios for ci in sublist]

        # Load checks
        checks = self.load_checks(check_ios)
        self.checks = [check[0] for check in checks]

        self.services = self.load_services(checks)
        self.results = None

    def load_settings(self):
        """
        Load global settings from the database.

        Returns:
            Dict(str->Any): Settings dictionary
        """
        settings = {}

        # Load settings from db
        cmd = "SELECT skey,value FROM settings"
        settings_rows = db.get(cmd)
        for key, value in settings_rows:
            settings[key] = value

        # Cast to correct data types
        settings["interval"] = int(settings["interval"])
        settings["jitter"] = int(settings["jitter"])
        settings["timeout"] = int(settings["timeout"])

        return settings
    
    def load_teams(self):
        """
        Load teams from the database.

        Returns:
            List(Team): A list of Teams
        """
        teams = []
        rows = db.get("SELECT * FROM team")
        for team_id, name, subnet, netmask in rows:
            team = Team(team_id, name, subnet, netmask)
            teams.append(team)
        return teams

    def load_domains(self):
        """
        Load domains from the database.

        Returns:
            List(Domain): List of domains
        """
        domains = []
        domain_rows = db.get("SELECT * FROM domain")
        for domain_id, fqdn in domain_rows:
            domain = Domain(domain_id, fqdn)
            domains.append(domain)
        return domains
    
    def load_credentials(self, teams, domains):
        """
        Load credentials from the database.
        
        Arguments:
            teams (List(Team)): List of teams to associate credentials with
            domains (List(Domain)): List of domains to associate credentials with

        Returns:
            List(Credential): List of credentials
        """
        creds = []
        cred_rows = db.get("SELECT * FROM credential")
        for cred_id, username, password, team_id, service_id, domain_id in cred_rows:
            team = next(filter(lambda t: t.id == team_id, teams))
            domain_lst = list(filter(lambda d: d.id == domain_id, domains))
            if len(domain_lst) == 0:
                domain = None
            else:
                domain = domain_lst[0]

            cred = Credential(cred_id, username, password, team, domain)
            creds.append(cred)
        return creds
    
    def load_check_ios(self, credentials):
        """
        Load check input-output pairs from the database.

        Arguments:
            credentials (List(Credential)): List of credentials to associate
            input-output pairs with

        Returns:
            Dict(int->List(CheckIO)): Mapping of check IDs to a list of
                check input-output pairs
        """
        check_ios = {}
   
        # Gather all of the check IOs
        check_io_rows = db.get("SELECT * FROM check_io")
        for check_io_id, check_input, expected, check_id in check_io_rows:
            # Gather all of the credentials which belong to this check IO
            cmd = "SELECT * FROM cred_input WHERE check_io_id=%s"
            cred_input_rows = db.get(cmd, (check_io_id))
            check_creds = []
            for cred_input_id, cred_id, _check_io_id in cred_input_rows:
                cred = next(filter(lambda c: c.id == cred_id, credentials))
                check_creds.append(cred)

            # Build check IO
            poll_input = pickle.loads(check_input)
            poll_input.timeout = self.settings["timeout"]
            expected = json.loads(expected)
            check_io = CheckIO(check_io_id, poll_input, 
                               expected, check_creds)

            # Update link from credential to this check IO
            for cred in check_creds:
                cred.check_io = check_io

            if check_id not in check_ios:
                check_ios[check_id] = []
            check_ios[check_id].append(check_io)
        return check_ios

    def load_checks(self, check_ios):
        """
        Load checks from the database.

        Arguments:
            check_ios (Dict(int->List(CheckIO))): Mapping of check IDs to a
                list of check input-output pairs to associate checks with 

        Returns:
            List(Check,int): A list of checks and the ID of their associated
                services
        """
        checks = []
        cmd = "SELECT * FROM service_check" 
        check_rows = db.get(cmd)
        for check_id, name, check_string, \
            poller_string, service_id in check_rows:

            # Build check
            ios = check_ios[check_id]
            check_function = load_module(check_string)
            poller_class = load_module(poller_string)
            poller = poller_class()
            check = Check(check_id, name, check_function,
                          ios, poller)

            # Update link from check IOs to this check
            for check_io in ios:
                check_io.check = check

            checks.append((check, service_id))
        return checks
    
    def load_services(self, checks):
        """
        Load services from the database.

        Arguments:
            checks (List(Check,int)): List of pairs of service IDs and the
                check to associate a service with

        Returns:
            List(Service): A list of services
        """
        services = []
        service_rows = db.get("SELECT * FROM service")
        for service_id, host, port in service_rows:
            schecks = []
            for check in checks:
                if check[1] == service_id:
                    schecks.append(check[0])

            service = Service(service_id, host, port, schecks)
            # Update link from checks to this service
            for check in schecks:
               check.service = service
            services.append(service)
        return services

    def reload_credentials(self):
        """
        Reload the credentials from the database, modifying the Credential
        objects already in use.
        """
        creds_list = self.load_credentials(self.teams, self.domains)
        creds_map = {}
        for c in creds_list:
            creds_map[c.id] = c
        for c in self.credentials:
            c.password = creds_map[c.id].password
    
    def load_results(self):
        """
        Update self.results with any results not yet loaded from the database.
        """
        cmd = ("SELECT * FROM result WHERE id > %s ORDER BY time ASC")

        if self.results is None:
            last_id = 0
            self.results = {}
        else:
            # If results exist, we can just load the latest ones and keep the old ones
            # Here we find the id of the last result we already have
            last_ids = []
            for team_results in self.results.values():
                for check_results in team_results.values():
                    last_ids.append(check_results[-1].id)
            last_id = max(last_ids)

        rows = db.get(cmd, (last_id))

        # Gather the results
        for result_id, check_id, check_io_id, team_id, time, poll_input, poll_result, result in rows:
            # Construct the result from the database info
            check = [c for c in self.checks if c.id == check_id][0]
            check_io = [cio for cio in self.check_ios if cio.id == check_io_id]
            team = [t for t in self.teams if t.id == team_id][0]
            poll_input = pickle.loads(poll_input)
            poll_result = pickle.loads(poll_result)
            res = Result(result_id, check, check_io, team, time, poll_input, poll_result, result)

            # Prepare to add the result to the dict
            if team_id not in self.results:
                self.results[team_id] = {}
            if check_id not in self.results[team_id]:
                self.results[team_id][check_id] = []

            self.results[team_id][check_id].append(res)

    def latest_results(self):
        """
        Gather the latest results for each team/check combo.

        Returns:
            results (Dict(int->Dict(int->(Result)))): A mapping of each team and check to its latest result
        """
        self.load_results()
        results = {}
        for team in self.teams:
            results[team.id] = {}
            for check in self.checks:
                try:
                    res = self.results[team.id][check.id][-1]
                    results[team.id][check.id] = res
                except:
                    print("[ERROR] Results retrieval failed")
        return results

    def change_passwords(self, team_id, service_id, pwchange):
        """
        Change the passwords for the given credentials.

        Arguments:
            team_id (int): The ID of the team the credential belongs to
            service_id (int): The ID of the service the credential belongs to
            pwchange (str): A series of user:pass combos separated by CRLFs
        """
        pwchange = [line.split(':') for line in pwchange.split('\r\n')]
        cmd = ('UPDATE credential SET password=%s WHERE team_id=%s '
               'AND service_id=%s AND username=%s')
        for line in pwchange:
            if len(line) >= 2:
                username = re.sub('\s+', '', line[0]).lower()
                password = re.sub('\s+', '', ':'.join(line[1:]))
                db.execute(cmd, (password, team_id, service_id, username))
   
    ## Config Saving Methods 
    def write_settings(self, settings):
        """
        Write global settings to the database.

        Arguments:
            settings (Dict(str->str)): A mapping of setting keys and values
        """
        cmd = ("INSERT INTO settings (skey, value) "
               "VALUES (%s, %s)")
        for key, value in settings.items():
            db.execute(cmd, (key, value))

    def write_teams(self, teams):
        """
        Write the given teams to the database.

        Arguments:
            teams (Dict(int->Team args)): A mapping of team config IDs to team
                initialization arguments

        Returns:
            Dict(int->int): A mapping of team config IDs to 
                team database IDs
        """
        team_ids = {}

        cmd = "INSERT INTO team (name, subnet, netmask) VALUES (%s, %s, %s)"
        for id, team in teams.items():
            db_id = db.execute(cmd, team)
            team_ids[id] = db_id
        return team_ids

    def write_domains(self, domains):
        """
        Write the given domains to the database.

        Arguments:
            domains (Dict(int->Domain args)): A mapping of domain config IDs to
                domain initialization arguments

        Returns:
            Dict(int->int): A mapping of domain config IDs to
                domain database IDs
        """
        domain_ids = {}

        cmd = "INSERT INTO domain (fqdn) VALUES (%s)"
        for id, domain in domains.items():
            db_id = db.execute(cmd, domain)
            domain_ids[id] = db_id
        return domain_ids

    def write_services(self, services):
        """
        Write the given services to the database.

        Arguments:
            services (Dict(int->Service args)): A mapping of service config IDs to
                service initialization arguments

        Returns:
            Dict(int->int): A mapping of service config IDs to 
                service database IDs
        """
        service_ids = {}

        cmd = 'INSERT INTO service (host, port) VALUES (%s, %s)'
        for id, service in services.items():
            db_id = db.execute(cmd, service)
            service_ids[id] = db_id
        return service_ids

    def write_checks(self, checks, service_ids):
        """
        Write the given checks to the database.

        Arguments:
            checks (Dict(int->Check args)): A mapping of check config IDs to check 
                initialization arguments
            service_ids (Dict(int->int)): A mapping of service config IDs to 
                service database IDs

        Returns:
            Dict(int->int): A mapping of check config IDs to 
                check database IDs
        """
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
        """
        Write the given input-output pairs to the database.

        Arguments:
            check_ios (Dict(int->CheckIO args)): A mapping of check input-output
                pair config IDs to check input-output pair initializaiton
                arguments
            poll_inputs (Dict(int->Serialized PollInput)): A mapping of poll
                input config IDs to serialized poll inputs
            check_ids (Dict(int->int)): A mapping of check config IDs to 
                check database IDs

        Returns:
            Dict(int->int): A mapping of check input-output pair config IDs
                to check input-output pair database IDs
        """
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

    def write_credentials(self, credentials, team_ids, domain_ids, check_io_ids):
        """
        Write the given input-output pairs to the database.

        Arguments:
            credentials (Dict(int->Credential args)): A mapping of credential
                config IDs to credential initialization arguments
            team_ids (Dict(int->int)): A mapping of team config IDs to team database IDs
            domain_ids (Dict(int->int)): A mapping of domain config IDs to
                domain database IDs
            check_io_ids (Dict(int->int)): A mapping of check input-output pair
                config IDs to check input-output pair database IDs
        """
        # SQL queries
        cred_cmd_domain = ('INSERT INTO credential (username, password, '
                           'team_id, service_id, domain_id) '
                           'VALUES (%s, %s, %s, %s, %s)')
        cred_cmd_no_domain = ('INSERT INTO credential (username, password, '
                              'team_id, service_id) '
                              'VALUES (%s, %s, %s, %s)')

        cred_io_cmd = ('INSERT INTO cred_input (cred_id, check_io_id) '
                    'VALUES (%s, %s)')
        check_get = 'SELECT check_id FROM check_io WHERE id=%s'
        service_get = 'SELECT service_id FROM service_check WHERE id=%s'

        for id, credential in credentials.items():
            user, passwd, pdomain_id, pcio_ids = credential

            cred_cmd = cred_cmd_no_domain
            if pdomain_id is not None:
                domain_id = domain_ids[pdomain_id]
                cred_cmd = cred_cmd_domain
            
            # Gather all of the check IOs this credential belongs to
            cio_ids = [check_io_ids[str(pcio_id)] for pcio_id in pcio_ids]
            for team_id in team_ids.values():
                cred_input = {}   # cred_id -> List(checkio_id)
                cred_service = {} # service_id -> cred_id

                for cio_id in cio_ids:
                    # Get the check and service this check IO belongs to
                    check_id = db.get(check_get, (cio_id))[0]
                    service_id = db.get(service_get, (check_id))[0]

                    if service_id in cred_service:
                        # The credential has already been inserted into the table
                        cred_input[cred_service[service_id]].append(cio_id)
                    else:
                        if pdomain_id is None:
                            args = (user, passwd, team_id, service_id)
                        else:
                            args = (user, passwd, team_id, service_id, domain_id)
                        cred_id = db.execute(cred_cmd, args)
                        # Insert the credential into the credential table
                        cred_id = db.execute(cred_cmd, (user, passwd, team_id, service_id))
                        cred_service[service_id] = cred_id
                        cred_input[cred_id] = [cio_id]

                # Insert relations into the cred-input table
                for cred_id, io_ids in cred_input.items():
                    for io_id in io_ids:
                        db.execute(cred_io_cmd, (cred_id, io_id))

    def load_results(self):
        """
        Update self.results with any results not yet loaded from the database.
        """
        cmd = ("SELECT * FROM result WHERE id > %s ORDER BY time ASC")
        if self.results is None:
            last_id = 0
            self.results = {}
        else:
            last_ids = []
            for team_results in self.results.values():
                for check_results in team_results.values():
                    last_ids.append(check_results[-1].id)
            last_id = max(last_ids)
        rows = db.get(cmd, (last_id))

        for result_id, check_id, check_io_id, team_id, time, poll_input, poll_result, result in rows:
            check = [c for c in self.checks if c.id == check_id][0]
            check_io = [cio for cio in self.check_ios if cio.id == check_io_id]
            team = [t for t in self.teams if t.id == team_id][0]
            poll_input = pickle.loads(poll_input)
            poll_result = pickle.loads(poll_result)
            res = Result(result_id, check, check_io, team, time, poll_input, poll_result, result)

            if team_id not in self.results:
                self.results[team_id] = {}
            if check_id not in self.results[team_id]:
                self.results[team_id][check_id] = []

            self.results[team_id][check_id].append(res)

    def latest_results(self):
        self.load_results()
        results = {}
        for team in self.teams:
            results[team.id] = {}
            for check in self.checks:
                try:
                    res = self.results[team.id][check.id][-1]
                    results[team.id][check.id] = res
                except:
                    # Log this
                    pass
        return results

    def change_passwords(self, team_id, domain_id, service_id, pwchange):
        pwchange = [line.split(':') for line in pwchange.split('\r\n')]
        if service_id is not None:
            cmd = ('UPDATE credential SET password=%s WHERE team_id=%s '
                   'AND service_id=%s AND username=%s')
        elif domain_id is not None:
            cmd = ('UPDATE credential SET password=%s WHERE team_id=%s '
                   'AND domain_id=%s AND username=%s')
        for line in pwchange:
            if len(line) >= 2:
                username = re.sub('\s+', '', line[0]).lower()
                password = re.sub('\s+', '', ':'.join(line[1:]))
                if service_id is not None:
                    args = (password, team_id, service_id, username)
                elif domain_id is not None:
                    args = (password, team_id, domain_id, username)
                db.execute(cmd, args)