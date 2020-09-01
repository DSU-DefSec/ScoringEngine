import random
import copy
import json
import db
from threading import Thread
from enum import IntEnum
import datetime
from .polling.poller import PollResult

class Team(object):
    """
    A Team in the competition.

    Attributes:
        id (int): ID of the team in the database
        name (str): Name of the team
    """
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __str__(self):
        return self.name


class Domain(object):
    """
    An Active Directory domain.

    Attributes:
        domain (str): First part of the FQDN
        fqdn (str): The fully qualified domain name of the domain
    """
    def __init__(self, fqdn):
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
        is_default (bool): Does the credential still have the default password?
        check_io (CheckIO): The input-output pair this credential is for
    """

    def __init__(self, id, username, password, team, domain, is_default):
        self.id = id
        self.username = username
        self.password = password
        self.team = team
        self.domain = domain
        self.is_default = is_default
        # check_io is set later

    def __str__(self):
        return "{}\\{}:{}:{}".format(self.domain, self.team.name, self.username, self.password)

class Vapp(object):
    """
    A vApp.

    Attributes:
        base_name (str): The base name for the vApp to which 'Team X_' is prepended for the actual vApp name
        subnet (str): A format string for the subnet of the vApp
        netmask (str): The netmask for the vApp's subnet
        systems (List(System)): List of Systems in the vApp
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

    def check(self, check_round, teams):
        """
        Conduct all checks on this service for every team in parallel.
        
        Arguments:
            check_round (int): The check round
            teams (List(Team)): The teams to run checks on
        """
        for check in self.checks:
            thread = Thread(target=check.check,
                            args=(check_round, teams))
            thread.start()

    def get_ip(self, team_id):
        """
        Calculate an IP from the given subnet and this system's host number.

        Arguments:
            team_id (int): The team id to calculate an IP for
        """
        subnet = self.vapp.subnet.format(team_id)
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
        port (int): The port of the service tested by the check
        check_function ((PollResult, List or Dict) -> bool): The function used to check the output of the poller
        check_ios (List(CheckIO)): All of the possible input-output pairs which can be used with this check
        poller (Poller): The poller used to run this check against the service
    """

    def __init__(self, id, name, port, check_function, check_ios, poller):
        self.id = id
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
        try:
            poll_result = self.poller.poll(poll_input)
        except Exception as e:
            poll_result = PollResult(e)

        try:
            result = self.check_function(poll_result, expected)
        except:
            result = False

        team_id = poll_input.team.id
        self.store_result(check_round, check_io_id, team_id, poll_input,
                          poll_result, result)

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
            return

        db.execute(cmd, (self.id, check_io_id, team_id, check_round,
                         poll_input, poll_result, result))


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
        self.id = id
        self.poll_input = poll_input
        self.expected = expected
        self.credentials = credentials

    def get_poll_inputs(self, teams):
        """
        Generate team-specific poll inputs from this input-output pair.

        Arguments:
            teams (List(Team)): The teams to generate inputs for
        """
        poll_inputs = []
        if len(self.credentials) == 0:
            for team in teams:
                poll_input = self.make_poll_input(team)
                poll_inputs.append(poll_input)
        else:
            username = random.choice(self.credentials).username
            creds = filter(lambda c: c.username == username, self.credentials)
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

class PasswordChangeRequest(object):
    """
    A password change request.

    Attributes:
        
        team_id (int): ID of the team to change passwords for
        status (PCRStatus): The status of the request
        creds (List(str,str)): List of tuples (username, new_password)
        check_id (int): ID of the service to change passwords for
        domain (str): FQDN of the domain to change passwords for
        submitted (datetime): Submission time for the request
        completed (datetime): Completion time for the request
        id (int): ID of the request
    """
    def __init__(self, team_id, status, creds, id=None, check_id=None, domain=None, submitted=None, completed=None):
        self.team_id = team_id
        self.status = status
        self.creds = creds
        self.id = id
        self.check_id = check_id
        self.domain = domain
        if submitted is None:
            submitted = datetime.datetime.now()
        self.submitted = submitted
        self.completed = completed
        
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
        id, team_id, check_id, domain, submitted, completed, status, creds = pcr_data
        creds = json.loads(creds)
        pcr = PasswordChangeRequest(team_id, status, creds, id, check_id, domain, submitted, completed)
        return pcr

    def save(self):
        """
        Save this new password change request to the database.
        """
        columns = ['team_id', 'check_id', 'domain', 'submitted', 'completed', 'status', 'creds']
        data = [self.team_id, self.check_id, self.domain, self.submitted, self.completed, int(self.status), json.dumps(self.creds)]
        self.id = db.insert('pcr', columns, data)

    def delete(self):
        """
        Delete this password change request from the database. The object should not be used after this method is called.
        """
        db.delete('pcr', [self.id], 'id=%s')

    def set_status(self, new_status):
        """
        Set the status of the request, and update the database to reflect the new status

        Arguments:
            new_status (PCRStatus): New status for the request
        """
        self.status = new_status
        db.modify('pcr', 'status=%s', (int(self.status), self.id), where='id=%s')

    def service_request(self):
        """
        Service this request, updating account credentials in the database, and updating the current status of the request
        """
        for cred in self.creds:
            username, password = cred
            db.set_credential_password(username, password, self.team_id, self.check_id, self.domain)
        self.completed = datetime.datetime.now()
        db.modify('pcr', 'completed=%s', (self.completed, self.id), where='id=%s')
        self.set_status(PCRStatus.COMPLETE)
