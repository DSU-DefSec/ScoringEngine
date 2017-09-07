import random
import copy
import db
from threading import Thread

class Team(object):

    def __init__(self, id, name, subnet, credentials=None):
        self.id = id
        self.name = name
        self.subnet = subnet


class Credential(object):

    def __init__(self, id, username, password, team):
        self.id = id
        self.username = username
        self.password = password
        self.team = team


class Service(object):

    def __init__(self, id, host, port, checks):
        self.id = id
        self.host = host
        self.port = port
        self.checks = checks

    def check(self, teams):
        for check in self.checks:
            thread = Thread(target=check.check, args=(teams, self.host, self.port))
            thread.start()
            print("Service Check Thread Started")


class Check(object):

    def __init__(self, id, check_function, check_ios, poller, service_id):
        self.id = id
        self.check_function = check_function
        self.check_ios = check_ios
        self.poller = poller
        self.service_id = service_id

    def check(self, teams, host, port):
        check_io = random.choice(self.check_ios)
        poll_inputs = check_io.get_poll_inputs(teams, host, port)
        for poll_input in poll_inputs:
            thread = Thread(target=self.check_single, args=(poll_input,check_io.expected))
            thread.start()
            print("Single Check Thread Started")

    def check_single(self, poll_input, expected):
        poll_result = self.poller.poll(poll_input)
        print("Polling Finished")
        result = self.check_function(poll_result, expected)
        print("Result Checked")
        team = poll_input.team
        self.store_result(team, result)

    def store_result(self, team, result):
        team_id = team.id
        cmd = ("INSERT INTO result (check_id, team_id, time, result) "
               "VALUES (%d, %d, NOW(), %s)")
        cmd = cmd % (self.id, team_id, result)
        print(cmd)
        db.execute(cmd)
        print("Result Stored")


class CheckIO(object):
    
    def __init__(self, id, poll_input, expected, credentials_set, check_id):
        self.id = id
        self.poll_input = poll_input
        self.expected = expected
        self.credentials_set = credentials_set
        self.check_id = check_id

    def get_poll_inputs(self, teams, host, port):
        if len(self.credentials_set) == 0:
            return self.get_poll_inputs_no_creds(teams, host, port)
        else:
            return self.get_poll_inputs_creds(host, port)

    def get_poll_inputs_no_creds(self, teams, host, port):
        poll_inputs = []
        for team in teams:
            poll_input = self.make_poll_input(team, host, port)
            poll_inputs.append(poll_input)
        return poll_inputs

    def get_poll_inputs_creds(self, host, port):
        poll_inputs = []
        credentials = random.choice(self.credentials_set)
        for credential in credentials:
            team = credential.team
            poll_input = self.make_poll_input(team, host, port)
            poll_input.credentials = credential
            poll_inputs.append(poll_input)
        return poll_inputs

    def make_poll_input(self, team, host, port):
        poll_input = copy.copy(self.poll_input)
        server = self.get_ip(team.subnet, host)
        poll_input.server = server
        poll_input.port = port
        poll_input.team = team
        return poll_input

    def get_ip(self, subnet, host):
        octets = subnet.split('.')
        octets[3] = str(host)
        ip = '.'.join(octets)
        return ip
