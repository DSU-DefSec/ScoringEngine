#!/usr/bin/python3
import sys
import yaml
import db
import db_writer

def load_config(filename):
    """
    Load the engine configuration from a file.

    Arguments:
        filename (str): The config file to load
    """
    print("Loading config...")
    with open(filename, 'r') as f:
        config = yaml.load(f)

    settings = flatten_settings(config['settings'])
    vapps = config['vapps']
    teams = config['teams']
    admins = config['web_admins']
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
    db_writer.write_teams(teams)
    print("Writing users to DB...")
    db_writer.write_web_users(admins, teams)
    print("Writing domains to DB...")
    if 'domain' in credentials:
        domain_ids = db_writer.write_domains(credentials['domain'].keys())
    else:
        domain_ids = []
    print("Writing checks to DB...")
    check_ids = db_writer.write_checks(vapps)
    print("Writing checkIOs to DB...")
    check_io_ids = db_writer.write_check_ios(vapps, check_ids)
    print("Writing credentials to DB...")
    credential_ids = db_writer.write_credentials(credentials, teams, check_io_ids)
    print("Finished!")

def flatten_settings(config_settings):
    """
    Flatten two-level global config settings into a single-level dictionary.

    Arguments:
        config_settings (Dict): Global config settings

    Returns:
        Dict: Flattened global config settings
    """
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
