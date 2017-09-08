#!/bin/python
import sys
import json
import cPickle
from model import *
from dm import DataManager
from dm import load_module
import validate

def load_config(filename):
    f = open(filename, 'r')
    contents = [line.strip() for line in f.readlines()]
    print("Parsing teams...")
    teams = parse_teams(contents)
    print(teams)
    print("Parsing services...")
    services = parse_services(contents)
    print(services)
    print("Parsing checks...")
    checks = parse_checks(contents, services)
    print(checks)
    print("Parsing poll inputs...")
    poll_inputs = parse_poll_inputs(contents)
    print(poll_inputs)
    print("Parsing checkIOs...")
    check_ios = parse_check_ios(contents, poll_inputs, checks)
    print(check_ios)
    print("Parsing credentials...")
    credentials = parse_credentials(contents, check_ios)
    print(credentials)

    dm = DataManager()
    print("Emptying existing database...")
    dm.reset_db()
    print("Writing teams to DB...")
    team_ids = dm.write_teams(teams)
    print("Writing services to DB...")
    service_ids = dm.write_services(services)
    print("Writing checks to DB...")
    check_ids = dm.write_checks(checks, service_ids)
    print("Writing checkIOs to DB...")
    check_io_ids = dm.write_check_ios(check_ios, poll_inputs, check_ids)
    print("Writing credentials to DB...")
    credential_ids = dm.write_credentials(credentials, team_ids, check_io_ids)

def parse_teams(contents):
    teams = {}

    portion = get_portion(contents, '[Teams]')
    for line in portion:
        if line.startswith('#') or line.strip() == '': # Comment
            continue
        id, args = line.split(':')
        name, subnet = args.split(',')

        validate.ip(subnet)
        teams[id] = (name, subnet)
    return teams

def parse_services(contents):
    services = {}

    portion = get_portion(contents, '[Services]')
    for line in portion:
        if line.startswith('#') or line.strip() == '': # Comment
            continue
        id, args = line.split(':')
        host, port = args.split(',')

        validate.integer(host)
        validate.integer(port)

        services[id] = (host, port)
    return services

def parse_checks(contents, services):
    checks = {}

    portion = get_portion(contents, '[Checks]')
    for line in portion:
        if line.startswith('#') or line.strip() == '': # Comment
            continue
        id, args = line.split(':')
        name, check_function, poller, service_id = args.split(',')

        validate.check_function(check_function)
        validate.poller(poller)
        validate.id_exists(service_id, services)

        checks[id] = (name, check_function, poller, service_id)
    return checks

def parse_check_ios(contents, poll_inputs, checks):
    check_ios = {}

    portion = get_portion(contents, '[CheckIOs]')
    for line in portion:
        if line.startswith('#') or line.strip() == '': # Comment
            continue
        id, args = line.split(':')
        args = args.split(',')
        input_id, check_id = args[0], args[1]
        expected = ','.join(args[2:])

        validate.id_exists(input_id, poll_inputs)
        validate.json(expected)
        validate.id_exists(check_id, checks)

        check_ios[id] = (input_id, expected, check_id)
    return check_ios

def parse_poll_inputs(contents):
    poll_inputs = {}
    portion = get_portion(contents, '[PollInputs]')
    for line in portion:
        if line.startswith('#') or line.strip() == '': # Comment
            continue
        id, args = line.split(':')
        args = args.split(',')
        input_class_str = args[0]

        validate.input_class(input_class_str)

        input_class = load_module(input_class_str)
        input = input_class(*args[1:])
        
        poll_inputs[id] = cPickle.dumps(input)
    return poll_inputs


def parse_credentials(contents, check_ios):
    credentials = {}

    portion = get_portion(contents, '[Credentials]')
    for line in portion:
        if line.startswith('#') or line.strip() == '': # Comment
            continue
        id, args = line.split(':')
        args = args.split(',')
        user, passwd = args[0], args[1]
        check_io_ids = json.loads(','.join(args[2:]))

        for check_io_id in check_io_ids:
            validate.id_exists(check_io_id, check_ios)
        
        credentials[id] = (user, passwd, check_io_ids)
    return credentials

def get_portion(contents, section):
    portion = []
    for i in range(len(contents)):
        if contents[i].startswith(section):
            for j in range(i+1, len(contents)):
                if contents[j].startswith('['):
                    break
                portion.append(contents[j])
            break
    return portion


if __name__ == '__main__':
    load_config(sys.argv[1])
