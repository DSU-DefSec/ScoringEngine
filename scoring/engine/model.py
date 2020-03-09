import random
import copy
import json
import db
from threading import Thread
from enum import IntEnum
import datetime

class Team(object):
    """
    A Team in the competition.

    Attributes:
        id (int): ID of the team in the database
        name (str): Name of the team
        subnet (IP): Subnet of the team
        netmask (IP): Netmask of the subnet
        vapp (str): Name of team vApp
    """
    def __init__(self, id, name):
        self.id = int(id)
        self.name = name

    def __str__(self):
        return self.name


class Domain(object):
    """
    An Active Directory domain.

    Attributes:
        id (int): ID of the domain in the database
        domain (str): First part of the FQDN
        fqdn (str): The fully qualified domain name of the domain
    """
    def __init__(self, id, fqdn):
        self.id = int(id)
        self.domain = fqdn.split('.')[0]
        self.fqdn = fqdn

    def __str__(self):
        return self.fqdn


class Credential(object):
    """
    A Credential used to log in to a service.

    Attributes:
        id (int): The ID of the credential in the database
        username (str): The username used to log in
        password (str): The password used to log in
        team (Team): The team this credential applies to
        domain (Domain): The domain this credential applies to
        check_io (CheckIO): The input-output pair this credential is for
        is_default (bool): Does the credential still have the default password?
    """

    def __init__(self, id, username, password, team, domain, is_default):
        self.id = int(id)
        self.username = username
        self.password = password
        self.team = team
        self.domain = domain
        self.is_default = is_default

    def __str__(self):
        return "%s\\%s:%s:%s" % (self.domain, self.team.name, self.username, self.password)

class Vapp(object):
    """
    A vApp.

    Attributes:
        base_name (str): The base name for the vApp
        subnet (str): A format string for the subnet of the vApp
        netmask (str): The netmask for the vApp's subnet
    """
    def __init__(self, base_name, subnet, netmask):
        self.base_name = base_name
        self.subnet = subnet
        self.netmask = netmask
        self.systems = []

class System(object):
    """
    A Service to be checked.

    Attributes:
        name (str): The name of the system in the database
        vapp (Vapp): The vApp containing the system
        host (int): The host number of the system
        checks (Check): A list of checks to be run on the system
    """

    def __init__(self, name, vapp, host, checks):
        self.name = name
        self.vapp = vapp
        self.host = host
        self.checks = checks
        self.persistence = {}

    def reload_persistence(self):
        pers = db.get('persistence', ['owner', 'attacker','active'], where='system=%s', args=[self.name])
        for owner,attacker,active in pers:
            if owner not in self.persistence:
                self.persistence[owner] = {}
            self.persistence[owner][attacker] = active

    def check(self, check_round, teams):
        """
        Conduct all checks on this service for every given team in parallel.
        
        Arguments:
            check_round (int): The check round
            teams (List(Team)): The teams to run checks on
        """
        for check in self.checks:
            thread = Thread(target=check.check,
                            args=(check_round, teams))
            thread.start()

    def get_ip(self, team_num):
        """
        Calculate an IP from the given subnet and this system's host number.

        Arguments:
            team_num (int): The team number to calculate an IP for
        """
        subnet = self.vapp.subnet.format(team_num)
        octets = subnet.split('.')
        octets[3] = str(self.host)
        ip = '.'.join(octets)
        return ip

    def __str__(self):
        return self.name


class Check(object):
    """
    A Check to be run against a service.

    Attributes:
        id (int): The ID of the check in the database
        name (str): The display name of the check
        check_function ((PollResult, List or Dict) -> bool): The function used to check the output of the poller
        check_ios (List(CheckIO)): All of the possible input-output pairs which can be used with this check
        poller (Poller): The poller used to run this check against the service
        service (Service): The service this check is for
    """

    def __init__(self, id, name, port, check_function, check_ios, poller):
        self.id = int(id)
        self.name = name
        self.port = port
        self.check_function = check_function
        self.check_ios = check_ios
        self.poller = poller

    def check(self, check_round, teams):
        """
        Select a random input-output pair and run a check against all
        teams in parallel.

        Arguments:
            check_round (int): The check round
            teams (List(Team)): The list of teams to check
        """
        check_io = random.choice(self.check_ios)
        poll_inputs = check_io.get_poll_inputs(teams)
        for poll_input in poll_inputs:
            thread = Thread(target=self.check_single,
                            args=(check_round, check_io.id, poll_input,check_io.expected))
            thread.start()

    def check_single(self, check_round, check_io_id, poll_input, expected):
        """
        Conduct a check against a single team and store the result.
        
        Arguments:
            check_round (int): The check round
            check_io (CheckIO): The ID of the check input-output pair used in the check
            poll_input (PollInput): The input to the poller
            expected (List or Dict): The expected output from the poller
        """
        max_tries = 1 # TODO make this configurable
        tries = 0
        while tries < max_tries: 
            tries += 1
            poll_result = self.poller.poll_timed(poll_input)
            if poll_result.exception is None or str(poll_result.exception) == 'None':
                break

        try:
            result = self.check_function(poll_result, expected)
        except:
            result = False
        team_id = poll_input.team.id
        res_id = self.store_result(check_round, check_io_id, team_id, poll_input,
                                   poll_result, result)
        if res_id != -1:
            defender, attackers = self.get_persistence(res_id)
            if self.system.checks[0].id == self.id:
                self.update_persistence(defender, attackers)
            if result:
                self.update_scores(defender, attackers)

    def store_result(self, check_round, check_io_id, team_id, poll_input,
                     poll_result, result):
        """
        Store the result of a check in the database.

        Arguments:
            check_round (int): The check round
            check_io_id (int): The ID of the check input-output pair
                in the database
            team_id (int): The ID of the team checked in the database
            poll_input (PollInput): The input with credentials used in
                the check
            poll_result (PollResult): The output of the poller used in
                the check
            result (bool): The result of the check
        """
        cmd = ("INSERT INTO result (check_id, check_io_id, team_id, "
	       "check_round, time, poll_input, poll_result, result) "
               "VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s)")
        poll_input = json.dumps(poll_input, default=poll_input.serialize)
        try:
            poll_result = json.dumps(poll_result, default=poll_result.serialize)
        except Exception as e:
            print("Dump failed: {}".format(str(e)))
            print(poll_result.__class__.__name__)
            print(poll_result.__dict__)
            return -1
        res_id = db.execute(cmd, (self.id, check_io_id, team_id, check_round,
                                  poll_input, poll_result, result))
        return res_id

    def get_persistence(self, res_id):
        # Gather relevant data from DB
        last_res = db.get('result', ['team_id','check_round','time','result'], where='id=%s', args=[res_id])
        defender,check_round,end_time,result = last_res[0]

        start_time = db.get('result', ['time'], where='check_round=%s AND check_id=%s', args=[check_round-1, self.id])
        if len(start_time) == 0:
            start_time = 0
        else:
            start_time = start_time[0][0]
        system = self.system.name

        # Find attackers with persistence on the system since last check
        where = 'defender=%s AND time > %s AND time < %s AND system=%s'
        groupby = 'attacker'
        attackers = db.get('persistence_log', ['attacker'], where=where, groupby=groupby, args=[defender, start_time, end_time, system])
        attackers = [a[0] for a in attackers if a[0] != defender]
        return defender, attackers

    def update_scores(self, defender, attackers):
        # Calculate point split
        teams = attackers + [defender]
        split = len(teams) * len(self.system.checks)
        points = 100 / split

        # Update scores
        for team in teams:
            db.modify('score', 'score=score+%s', where='team_id=%s', args=[points, team])

    def update_persistence(self, defender, attackers):
        system = self.system.name
        db.modify('persistence', 'active=0', where='owner=%s AND system=%s', args=[defender, system])
        for attacker in attackers:
            db.modify('persistence', 'active=1', where='owner=%s AND system=%s AND attacker=%s', args=[defender, system, attacker])
            

class CheckIO(object):
    """
    A input-output pair used in a check.

    Attributes:
        id (int): The ID of the input-output pair in the database
        poll_input (PollInput): The input to be used in the check
        expected (List or Dict): The output expected from the check
        credentials (List(Credential)): All of the possible credentials to be combined with the poll input
        check (Check): The check this input-output pair is for
    """
    
    def __init__(self, id, poll_input, expected, credentials):
        self.id = int(id)
        self.poll_input = poll_input
        self.expected = expected
        self.credentials = credentials

    def get_poll_inputs(self, teams):
        """
        Generate team-specific poll inputs from this input-output pair.

        Arguments:
            teams (List(Team)): The teams to generate inputs for
        """
        if len(self.credentials) == 0:
            return self.get_poll_inputs_no_creds(teams)
        else:
            return self.get_poll_inputs_creds(teams)

    def get_poll_inputs_no_creds(self, teams):
        """
        Generate team-specific poll inputs from this input-output pair
        which don't use credentials.

        Arguments:
            teams (List(Team)): The teams to generate inputs for
        """
        poll_inputs = []
        for team in teams:
            poll_input = self.make_poll_input(team)
            poll_inputs.append(poll_input)
        return poll_inputs

    def get_poll_inputs_creds(self, teams):
        """
        Generate team-specific poll inputs from this input-output pair
        which use credentials.

        Arguments:
            teams (List(Team)): The teams to generate inputs for
        """
        poll_inputs = []
        credential = random.choice(self.credentials)
        creds = [cred for cred in self.credentials 
                 if cred.username == credential.username]
        for c in creds:
            team = c.team
            if team in teams:
                poll_input = self.make_poll_input(team)
                poll_input.credentials = c
                poll_inputs.append(poll_input)
        return poll_inputs

    def make_poll_input(self, team):
        """
        Create a team-specific poll input from the general one in this
        input-output pair

        Arguments:
            team (Team): The team to generate an input for
        """
        poll_input = copy.copy(self.poll_input)
        server = self.check.system.get_ip(team.id)
        poll_input.server = server
        poll_input.port = self.check.port
        poll_input.team = team
        return poll_input


class Result(object):
    """
    The result of a check.

    Attributes:
        id (int): The ID of the result in the database
        check (Check): The check this result resulted from
        check_io (CheckIO): The input-output pair used in the check
        team (Team): The team this result is for
        check_round (int): The check round this result belongs to
        poll_input (PollInput): The specific poller input used in the check
        poll_result (PollResult): The specific poller output retrieved from
            the poller
        result (bool): The result of the check
    """
    
    def __init__(self, id, check, check_io, team, check_round,
                 time, poll_input, poll_result, result):
        self.id = int(id)
        self.check = check
        self.check_io = check_io
        self.team = team
        self.check_round = check_round
        self.time = time
        self.poll_input = poll_input
        self.poll_result = poll_result
        self.result = result


class PCRStatus(IntEnum):
    COMPLETE = 0
    PENDING = 1
    APPROVAL = 2
    DENIED = 3

class PasswordChangeRequest(object):
    """
    A password change request.

    Attributes:
        
        team_id (int): ID of the team to change passwords for
        status (PCRStatus): The status of the request
        creds (List(str,str)): List of tuples (username, new_password)
        check_id (int): ID of the service to change passwords for
        domain_id (int): ID of the domain to change passwords for
        submitted (datetime): Submission time for the request
        completed (datetime): Completition time for the request
        id (int): ID of the request
    """
    def __init__(self, team_id, status, creds, id=None, check_id=None, domain_id=None, submitted=None, completed=None, team_comment='', admin_comment=''):
        self.id = id
        self.team_id = team_id
        self.check_id = check_id
        self.domain_id = domain_id
        if submitted is None:
            submitted = datetime.datetime.now()
        self.submitted = submitted
        self.completed = completed
        self.status = status
        self.creds = creds
        self.team_comment = team_comment
        self.admin_comment = admin_comment
        
        if id is None:
            self.save()

    def load(pcr_id):
        """
        Load a PasswordChangeRequest with the given database ID.

        Arguments:
            pcr_id (int): ID of PasswordChangeRequest in database

        Returns:
            PasswordChangeRequest: The password change request with the given ID
        """
        pcr_data = db.get('pcr', ['*'], where='id=%s', args=[pcr_id])[0]
        id, team_id, check_id, domain_id, submitted, completed, status, creds, team_comment, admin_comment = pcr_data
        creds = json.loads(creds)
        pcr = PasswordChangeRequest(team_id, status, creds, id, check_id, domain_id, submitted, completed, team_comment, admin_comment)
        return pcr

    def save(self):
        """
        Save this new password change request to the database.
        """
        columns = ['team_id', 'check_id', 'domain_id', 'submitted', 'completed', 'status', 'creds']
        data = [self.team_id, self.check_id, self.domain_id, self.submitted, self.completed, int(self.status), json.dumps(self.creds)]
        self.id = db.insert('pcr', columns, data)

    def delete(self):
        """
        Delete this password change request from the database. The object should not be used after this method is called.
        """
        db.delete('pcr', [self.id], 'id=%s')

    def conflicts(self, window):
        """
        Is there an account conflict for requests submitted in the window of time before this request.

        Arguments:
            window (int): Window for flagging conflicting requests in minutes

        Returns:
            bool: Does this request conflict with an earlier one?
        """
        # Load list of possible conflicting password change requests
        where = 'id != %s AND team_id = %s AND status != %s '
        if self.check_id is None:
            where += 'AND check_id is %s AND domain_id = %s'
        else:
            where += 'AND check_id = %s AND domain_id is %s'

        pcr_ids = db.get('pcr', ['id'], where=where, args=[self.id, self.team_id, int(PCRStatus.DENIED), self.check_id, self.domain_id])
        pcrs = [PasswordChangeRequest.load(pcr_id) for pcr_id in pcr_ids]
        # Check list for conflicts
        window = datetime.timedelta(minutes=window)
        users = [cred[0] for cred in self.creds]
        for pcr in pcrs:
            if pcr.submitted + window >= self.submitted:
                for cred in pcr.creds:
                    if cred[0] in users:
                        return True
        return False

    def set_status(self, new_status):
        """
        Set the status of the request, and update the database to reflect the new status

        Arguments:
            new_status (PCRStatus): New status for the request
        """
        self.status = new_status
        db.modify('pcr', 'status=%s', (int(self.status), self.id), where='id=%s')

    def set_team_comment(self, team_comment):
        """
        Set the team comment for this request and save it to the database.

        Arguments:
            team_comment (str): New team comment
        """
        self.team_comment = team_comment
        db.modify('pcr', 'team_comment=%s', (team_comment, self.id), where='id=%s')

    def set_admin_comment(self, admin_comment):
        """
        Set the admin comment for this request and save it to the database.

        Arguments:
            admin_comment (str): New admin comment
        """
        self.admin_comment = admin_comment
        db.modify('pcr', 'admin_comment=%s', (admin_comment, self.id), where='id=%s')

    def service_request(self):
        """
        Service this request, updating account credentials in the database, and updating the current status of the request
        """
        for cred in self.creds:
            username, password = cred
            db.set_credential_password(username, password, self.team_id, self.check_id, self.domain_id)
        self.completed = datetime.datetime.now()
        db.modify('pcr', 'completed=%s', (self.completed, self.id), where='id=%s')
        self.set_status(PCRStatus.COMPLETE)
