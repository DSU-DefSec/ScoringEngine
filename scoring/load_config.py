#!/usr/bin/python3
import sys
import yaml
import json
from engine.model import *
import db
import db_writer
import utils
import validate

def load_config(filename):
    print("Loading config...")
    with open(filename, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    settings = flatten_settings(config['settings'])
    vapps = config['vapps']
    teams = config['teams']
    admins = config['web_users']
    credentials = config['credentials']

    print("Emptying existing database...")
    db.reset_all_tables()
    print("Writing global settings to DB...")
    db_writer.write_settings(settings)
    print("Writing vapps to DB...")
    db_writer.write_vapps(vapps)
    print("Writing systems to DB...")
    db_writer.write_systems(vapps)
    print("Writing teams to DB...")
    team_ids = db_writer.write_teams(teams)
    print("Writing users to DB...")
    user_ids = db_writer.write_web_users(admins, teams, team_ids)
    print("Writing domains to DB...")
    if 'domain' in credentials:
        domain_ids = db_writer.write_domains(credentials['domain'].keys())
    else:
        domain_ids = []
    print("Writing checks to DB...")
    check_ids = db_writer.write_checks(vapps)
    print("Writing checkIOs to DB...")
    check_io_ids = db_writer.write_check_ios(vapps, check_ids)
    print(check_io_ids)
    print("Writing credentials to DB...")
    credential_ids = db_writer.write_credentials(credentials, team_ids, domain_ids, check_io_ids)
    return

def flatten_settings(config_settings):
    settings = {}
    for key, value in config_settings.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                key_name = '{}_{}'.format(key, subkey)
                settings[key_name] = subvalue
        else:
            settings[key] = value

    return settings

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: ./load_config CONFIG_FILE")
    else:
        load_config(sys.argv[1])
