from utils import load_module
import json
import db
from engine.model import *

class DataModel(object):

    def reset_db(self):
        """
        Delete all data from the database.
        """
        db.reset_all_tables()

    def load_db(self):
        """
        Load all data from the database.
        """
        self.load_settings()
        teams = self.load_teams()
        self.teams = list(teams.values())
        self.domains = self.load_domains()
        self.credentials = self.load_credentials(self.teams, self.domains)

        # Load check IOs
        check_ios = self.load_check_ios(self.credentials)
        self.check_ios = list(check_ios.values())
        self.check_ios = [ci for sublist in self.check_ios for ci in sublist]

        # Load checks
        checks = self.load_checks(check_ios)
        self.checks = [check[0] for check in checks]

        vapps = self.load_vapps()
        self.vapps = [vapp for vapp in vapps.values()]
        self.systems = self.load_systems(vapps, checks)
        self.results = None

    def load_settings(self):
        """
        Load global settings from the database.
        """
        settings = {}

        # Load settings from db
        settings_rows = db.get('settings', ['skey', 'value'])
        for key, value in settings_rows:
            settings[key] = value

        # Cast to correct data types
        settings['interval'] = int(settings['polling_interval'])
        settings['jitter'] = int(settings['polling_jitter'])
        settings['timeout'] = int(settings['polling_timeout'])
        settings['running'] = int(settings['running'])
        settings['revert_penalty'] = int(settings['revert_penalty'])

        self.settings = settings

    def load_teams(self):
        """
        Load teams from the database.

        Returns:
            Dict(int->Team): A mapping of team database IDs to Teams
        """
        teams = {}
        rows = db.getall('team')
        for team_id, name, team_num in rows:
            team = Team(team_id, name, team_num)
            teams[team_id] = team
        return teams

    def load_domains(self):
        """
        Load domains from the database.

        Returns:
            List(Domain): List of domains
        """
        domains = []
        domain_rows = db.getall('domain')
        for domain_id, fqdn in domain_rows:
            domain = Domain(domain_id, fqdn)
            domains.append(domain)
        return domains
    
    def load_credentials(self, teams, domains):
        """
        Load credentials from the database.
        
        Arguments:
            teams (Dict(int->Team)): Mapping of team database IDs to Teams to associate credentials with
            domains (List(Domain)): List of domains to associate credentials with

        Returns:
            List(Credential): List of credentials
        """
        creds = []
        cred_rows = db.getall('credential')
        for cred_id, username, password, team_id, service_id, domain_id, is_default in cred_rows:
            team = next(filter(lambda t: t.id == team_id, teams))
            domain_lst = list(filter(lambda d: d.id == domain_id, domains))
            if len(domain_lst) == 0:
                domain = None
            else:
                domain = domain_lst[0]

            cred = Credential(cred_id, username, password, team, domain, is_default)
            creds.append(cred)
        return creds
    
    def load_check_ios(self, credentials):
        """
        Load check input-output pairs from the database. Poll inputs will
        be left in the following format:
        List(input_class_str, Dict(attr->value)).

        Arguments:
            credentials (List(Credential)): List of credentials to associate input-output pairs with

        Returns:
            Dict(int->List(CheckIO)): Mapping of check IDs to a list of check input-output pairs
        """
        check_ios = {}
   
        # Gather all of the check IOs
        check_io_rows = db.getall('check_io')
        for check_io_id, poll_input, expected, check_id in check_io_rows:
            # Gather all of the credentials which belong to this check IO
            cred_input_rows = db.get('cred_input', ['*'],
                                     where='check_io_id=%s', args=(check_io_id))
            check_creds = []
            for cred_input_id, cred_id, _check_io_id in cred_input_rows:
                cred = next(filter(lambda c: c.id == cred_id, credentials))
                check_creds.append(cred)

            # Build check IO
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
            check_ios (Dict(int->List(CheckIO))): Mapping of check IDs to a list of check input-output pairs to associate checks with 

        Returns:
            List(Check,int): A list of checks and the ID of their associated services
        """
        checks = []
        check_rows = db.getall('service_check')
        for check_id, name, system, port, check_string, \
            poller_string in check_rows:

            # Build check
            ios = check_ios[check_id]
            check_function = load_module(check_string)
            poller_class = load_module(poller_string)
            poller = poller_class()
            check = Check(check_id, name, port, check_function,
                          ios, poller)

            # Update link from check IOs to this check
            for check_io in ios:
                check_io.check = check

            checks.append((check, system))
        return checks
    
    def load_systems(self, vapps, checks):
        """
        Load systems from the database.

        Arguments:
            checks (List(Check,int)): List of pairs of systems and the
                check to associate a system with

        Returns:
            List(Service): A list of systems
        """
        systems = []
        system_rows = db.getall('system')
        for system_name, vapp_name, host in system_rows:
            schecks = []
            for check, sid in checks:
                if sid == system_name:
                    schecks.append(check)

            vapp = vapps[vapp_name]
            system = System(system_name, vapp, host, schecks)
            vapp.systems.append(system)
            # Update link from checks to this system
            for check in schecks:
               check.system = system
            systems.append(system)
        return systems

    def load_vapps(self):
        vapps = {}
        vapp_rows = db.getall('vapp')
        for base_name, subnet, netmask in vapp_rows:
            vapp = Vapp(base_name, subnet, netmask)
            vapps[base_name] = vapp
        return vapps

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
