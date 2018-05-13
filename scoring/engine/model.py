import random
import copy
from .. import db
from threading import Thread

class Team(object):
    """
    A Team in the competition.

    Attributes:
        id (int): ID of the team in the database
        name (str): Name of the team
        subnet (IP): Subnet of the team
        netmask (IP): Netmask of the subnet
    """
    def __init__(self, id, name, subnet, netmask):
        self.id = int(id)
        self.name = name
        self.subnet = subnet
        self.netmask = netmask

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
    """

    def __init__(self, id, username, password, team, domain):
        self.id = int(id)
        self.username = username
        self.password = password
        self.team = team
        self.domain = domain

    def __str__(self):
        return "%s\\%s:%s:%s" % (self.domain, self.team.name, self.username, self.password)


class Service(object):
    """
    A Service to be checked.

    Attributes:
        id (int): The ID of the service in the database
        host (int): The host number of the service
        port (int): The port of the service
        checks (Check): A list of checks to be run on the service
    """

    def __init__(self, id, host, port, checks):
        self.id = int(id)
        self.host = host
        self.port = port
        self.checks = checks

    def check(self, teams):
        """
        Conduct all checks on this service for every given team in parallel.
        
        Arguments:
            teams (List(Team)): The teams to run checks on
        """
        for check in self.checks:
            thread = Thread(target=check.check,
                            args=(teams, self.host, self.port))
            thread.start()

    def get_ip(self, subnet):
        """
        Calculate an IP from the given subnet and this service's host number.

        Arguments:
            subnet (IP): The subnet used to calculate the IP
        """
        octets = subnet.split('.')
        octets[3] = str(self.host)
        ip = '.'.join(octets)
        return ip

    def __str__(self):
        return "%s:%s" % (self.host, self.port)


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

    def __init__(self, id, name, check_function, check_ios, poller):
        self.id = int(id)
        self.name = name
        self.check_function = check_function
        self.check_ios = check_ios
        self.poller = poller

    def check(self, teams, host, port):
        """
        Select a random input-output pair and run a check against all
        teams in parallel.

        Arguments:
            teams (List(Team)): The list of teams to check
            host (int): The host in the team's subnet to check
            port (int): The port of the host to check
        """
        check_io = random.choice(self.check_ios)
        poll_inputs = check_io.get_poll_inputs(teams, host, port)
        for poll_input in poll_inputs:
            thread = Thread(target=self.check_single,
                            args=(check_io.id, poll_input,check_io.expected))
            thread.start()

    def check_single(self, check_io_id, poll_input, expected):
        """
        Conduct a check against a single team and store the result.
        
        Arguments:
            check_io (CheckIO): The ID of the check input-output pair used in the check
            poll_input (PollInput): The input to the poller
            expected (List or Dict): The expected output from the poller
        """
        max_tries = 5 # TODO make this configurable
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
        self.store_result(check_io_id, team_id, poll_input,
                          poll_result, result)

    def store_result(self, check_io_id, team_id, poll_input,
                     poll_result, result):
        """
        Store the result of a check in the database.

        Arguments:
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
	       "time, poll_input, poll_result, result) "
               "VALUES (%s, %s, %s, NOW(), %s, %s, %s)")
        poll_input = json.dumps(poll_input, default=poll_input.serialize)
        poll_result = json.dumps(poll_result, default=poll_result.serialize)
        db.execute(cmd, (self.id, check_io_id, team_id, 
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
        self.id = int(id)
        self.poll_input = poll_input
        self.expected = expected
        self.credentials = credentials

    def get_poll_inputs(self, teams, host, port):
        """
        Generate team-specific poll inputs from this input-output pair.

        Arguments:
            teams (List(Team)): The teams to generate inputs for
            host (int): The host in the team's subnet to check
            port (int): The port of the host to check
        """
        if len(self.credentials) == 0:
            return self.get_poll_inputs_no_creds(teams, host, port)
        else:
            return self.get_poll_inputs_creds(teams, host, port)

    def get_poll_inputs_no_creds(self, teams, host, port):
        """
        Generate team-specific poll inputs from this input-output pair
        which don't use credentials.

        Arguments:
            teams (List(Team)): The teams to generate inputs for
            host (int): The host in the team's subnet to check
            port (int): The port of the host to check
        """
        poll_inputs = []
        for team in teams:
            poll_input = self.make_poll_input(team, host, port)
            poll_inputs.append(poll_input)
        return poll_inputs

    def get_poll_inputs_creds(self, teams, host, port):
        """
        Generate team-specific poll inputs from this input-output pair
        which use credentials.

        Arguments:
            teams (List(Team)): The teams to generate inputs for
            host (int): The host in the team's subnet to check
            port (int): The port of the host to check
        """
        poll_inputs = []
        credential = random.choice(self.credentials)
        creds = [cred for cred in self.credentials 
                 if cred.username == credential.username]
        for c in creds:
            team = c.team
            if team in teams:
                poll_input = self.make_poll_input(team, host, port)
                poll_input.credentials = c
                poll_inputs.append(poll_input)
        return poll_inputs

    def make_poll_input(self, team, host, port):
        """
        Create a team-specific poll input from the general one in this
        input-output pair

        Arguments:
            team (Team): The team to generate an input for
            host (int): The host in the team's subnet to check
            port (int): The port of the host to check
        """
        poll_input = copy.copy(self.poll_input)
        server = self.check.service.get_ip(team.subnet)
        poll_input.server = server
        poll_input.port = port
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
        poll_input (PollInput): The specific poller input used in the check
        poll_result (PollResult): The specific poller output retrieved from
            the poller
        result (bool): The result of the check
    """
    
    def __init__(self, id, check, check_io, team, 
                 time, poll_input, poll_result, result):
        self.id = int(id)
        self.check = check
        self.check_io = check_io
        self.team = team
        self.time = time
        self.poll_input = poll_input
        self.poll_result = poll_result
        self.result = result
