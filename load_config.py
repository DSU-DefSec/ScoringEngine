#!/usr/bin/env python3
import sys
import json
import pickle
from engine.model import *
from dm import DataManager
from dm import load_module
import validate

def load_config(filename):
    f = open(filename, 'r')
    contents = [line.strip() for line in f.readlines()]
    print("Parsing global settings...")
    settings = parse_global(contents)
    print("Parsing teams...")
    teams = parse_teams(contents)
    print(teams)
    print("Parsing users...")
    users = parse_users(contents, teams)
    print(users)
    print("Parsing domains...")
    domains = parse_domains(contents)
    print(domains)
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
    credentials = parse_credentials(contents, domains, check_ios)
    print(credentials)

    dm = DataManager()
    print("Emptying existing database...")
    dm.reset_db()
    print("Writing global settings to DB...")
    dm.write_settings(settings)
    print("Writing teams to DB...")
    team_ids = dm.write_teams(teams)
    print("Writing users to DB...")
    user_ids = dm.write_web_users(users, team_ids)
    print("Writing domains to DB...")
    domain_ids = dm.write_domains(domains)
    print("Writing services to DB...")
    service_ids = dm.write_services(services)
    print("Writing checks to DB...")
    check_ids = dm.write_checks(checks, service_ids)
    print("Writing checkIOs to DB...")
    check_io_ids = dm.write_check_ios(check_ios, poll_inputs, check_ids)
    print("Writing credentials to DB...")
    credential_ids = dm.write_credentials(credentials, team_ids, domain_ids, check_io_ids)

def parse_global(contents):
    settings = {}

    portion = get_portion(contents, '[Global]')
    lines = parse_portion(portion)
    for key, value in lines:
        settings[key] = value
    return settings

def parse_teams(contents):
    teams = {}

    portion = get_portion(contents, '[Teams]')
    lines = parse_portion(portion)
    for id, args in lines:
        id = int(id)
        name, subnet, netmask = args

        validate.ip(subnet)
        validate.ip(netmask)

        teams[id] = (name, subnet, netmask)
    return teams

def parse_users(contents, teams):
    users = {}
    portion = get_portion(contents, '[Users]')
    lines = parse_portion(portion)
    for id, args in lines:
        id = int(id)
        team_id, username, password, is_admin = args

        validate.integer(team_id)
        validate.integer(is_admin)

        team_id = int(team_id)
        is_admin = int(is_admin)

        if team_id != 0:
            validate.id_exists(team_id, teams)
        validate.boolean(is_admin)

        user = (team_id, username, password, is_admin)
        users[id] = user
    return users


def parse_domains(contents):
    domains = {}
    
    portion = get_portion(contents, '[Domains]')
    lines = parse_portion(portion)
    for id, fqdn in lines:
        validate.integer(id)
        id = int(id)

        domains[id] = (fqdn)
    return domains

def parse_services(contents):
    services = {}

    portion = get_portion(contents, '[Services]')
    lines = parse_portion(portion)
    for id, args in lines:
        validate.integer(id)
        id = int(id)

        host, port = args

        validate.integer(host)
        validate.integer(port)

        services[id] = (host, port)
    return services

def parse_checks(contents, services):
    checks = {}

    portion = get_portion(contents, '[Checks]')
    lines = parse_portion(portion)
    for id, args in lines:
        validate.integer(id)
        id = int(id)

        name, check_function, poller, service_id = args
        check_function = 'engine.checker.' + check_function
        poller = 'engine.polling.' + poller

        validate.check_function(check_function)
        validate.poller(poller)

        validate.integer(service_id)
        service_id = int(service_id)
        validate.id_exists(service_id, services)

        checks[id] = (name, check_function, poller, service_id)
    return checks

def parse_check_ios(contents, poll_inputs, checks):
    check_ios = {}

    portion = get_portion(contents, '[CheckIOs]')
    lines = parse_portion(portion)
    for id, args in lines:
        validate.integer(id)
        id = int(id)

        input_id, check_id = args[0], args[1]
        expected = ','.join(args[2:])

        validate.integer(input_id)
        input_id = int(input_id)
        validate.id_exists(input_id, poll_inputs)

        validate.jsondata(expected)

        validate.integer(check_id)
        check_id = int(check_id)
        validate.id_exists(check_id, checks)

        check_ios[id] = (input_id, expected, check_id)
    return check_ios

def parse_poll_inputs(contents):
    poll_inputs = {}
    portion = get_portion(contents, '[PollInputs]')
    lines = parse_portion(portion)
    for id, args in lines:
        validate.integer(id)
        id = int(id)

        input_class_str = 'engine.polling.' + args[0]
        args = ','.join(args[1:])

        validate.input_class(input_class_str)
        validate.jsondata(args)

        input_class = load_module(input_class_str)
        args = json.loads(args)
        input = input_class(*args)
        
        poll_inputs[id] = pickle.dumps(input)
    return poll_inputs


def parse_credentials(contents, domains, check_ios):
    credentials = {}

    portion = get_portion(contents, '[Credentials]')
    lines = parse_portion(portion)
    for id, args in lines:
        validate.integer(id)
        id = int(id)
        domain_id = None
        if '[' not in args[2]:
            domain_id = args[0]
            args = args[1:]

        user, passwd = args[0], args[1]
        check_io_ids = json.loads(','.join(args[2:]))

        if domain_id is not None:
            validate.integer(domain_id)
            domain_id = int(domain_id)
            validate.id_exists(domain_id, domains)
        for check_io_id in check_io_ids:
            validate.integer(check_io_id)
            check_io_id = int(check_io_id)
            validate.id_exists(check_io_id, check_ios)
        
        credentials[id] = (user, passwd, domain_id, check_io_ids)
    return credentials

def parse_portion(portion):
    lines = []
    for line in portion:
        if line.startswith('#') or line.strip() == '': # Comment
            continue
        colon = line.index(':')
        id = line[:colon]
        args = line[colon+1:].split(',')
        lines.append((id, args))
    return lines

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
    if len(sys.argv) < 2:
        print("Usage: ./load_config CONFIG_FILE")
    else:
        load_config(sys.argv[1])
