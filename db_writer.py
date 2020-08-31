"""
This module contains functions used to write config data to the database in the proper format.
"""
import db
import bcrypt
import json

def get_poller(check_type):
    """
    Determine the Poller module path based on the check type

    Arguments:
        check_type (str): The service type of the check (ssh, ldap, etc.)

    Returns:
        str: The module path of the Poller
    """
    poller_fmt = 'engine.polling.poll_{}.{}Poller'
    poller = poller_fmt.format(check_type, check_type.title())
    return poller

def get_poll_input(check_type):
    """
    Determine the PollInput module path based on the check type

    Arguments:
        check_type (str): The service type of the check (ssh, ldap, etc.)

    Returns:
        str: The module path of the PollInput
    """
    poller_fmt = 'engine.polling.poll_{}.{}PollInput'
    poller = poller_fmt.format(check_type, check_type.title())
    return poller

def get_checker(check_type, check_function):
    """
    Determine the check function path based on the check type and function.

    Arguments:
        check_type (str): The service type of the check (ssh, ldap, etc.)
        check_function (str): The check function to use

    Returns:
        str: The path of the check function
    """

    # Mapping of check types to check function modules
    check_modules = {
        # File based checkers
        'http':  'file_check',
        'ftp':   'file_check',
        'smb':   'file_check',

        # SQL checkers
        'mysql': 'sql_check',
        'mssql': 'sql_check',

        # Type-specific checkers
        'ssh':   'ssh_check',
        'smtp':  'smtp_check',
        'ldap':  'ldap_check',
        'dns':   'dns_check',
        'log':   'log_check',
    }
    if check_function == 'authenticated':
        check_module = 'auth_check'
    else:
        check_module = check_modules[check_type]

    checker = 'engine.checker.{}.{}'.format(check_module, check_function)
    return checker

def write_settings(settings):
    """
    Write global settings to the database.

    Arguments:
        settings (Dict(str->str)): A mapping of setting keys and values
    """
    for key, value in settings.items():
        db.insert('settings', ['skey', 'value'], (key, value))

def write_vapps(vapps):
    """
    Write vApp data to the database.

    Arguments:
        vapps (Dict(str->Dict)): Mapping of vApp base names to vApp data
    """
    for base_name,vapp_data in vapps.items():
        subnet = vapp_data['subnet']
        netmask = vapp_data['netmask']
        db.insert('vapp', ['base_name', 'subnet', 'netmask'],
                  (base_name, subnet, netmask,))

def write_systems(vapps):
    """
    Write systems to the database.

    Arguments:
        vapps (Dict(str->Dict)): Mapping of vApp base names to vApp data
    """
    for base_name, vapp_data in vapps.items():
        for system, system_data in vapp_data['systems'].items():
            host = system_data['host']
            db.insert('system', ['system', 'vapp', 'host'],
                      (system, base_name, host,))

def write_teams(teams):
    """
    Write teams to the database.

    Arguments:
        teams (Dict(int->Team args)): Mapping of team IDs to team data
    """
    for name, team_data in teams.items():
        team_num = team_data['team_num']
        db.insert('team', ['id', 'name'], (team_num, name,))

def write_web_users(admins, teams):
    """
    Write web interface users to the database, hashing their passwords.

    Arguments:
        admins (Dict(str->str)): Mapping of admin usernames to passwords
        teams (Dict(str->Dict)): Mapping of team names to team data
    """
    # Admin users
    for username, password in admins.items():
        password = password.encode('utf-8')
        pwhash = bcrypt.hashpw(password, bcrypt.gensalt())
        db.insert('users',
            ['username', 'password', 'team_id', 'is_admin'],
            (username, pwhash, None, True))

    # Regular users
    for team_name, data in teams.items():
        tid = teams[team_name]['team_num']
        username = data['user']['username']
        password = data['user']['password']
        password = password.encode('utf-8')
        pwhash = bcrypt.hashpw(password, bcrypt.gensalt())

        db.insert('users',
            ['username', 'password', 'team_id', 'is_admin'],
            (username, pwhash, tid, False))

def write_domains(domains):
    """
    Write domains to the database.

    Arguments:
        domains (List(str)): A list of FQDNs

    Returns:
        Dict(str->int): A mapping of FQDNs to domain database IDs
    """
    domain_ids = {}
    for domain in domains:
        db_id = db.insert('domain', ['fqdn'], (domain,))
        domain_ids[domain] = db_id
    return domain_ids

def write_checks(vapps):
    """
    Write checks to the database.

    Arguments:
        vapps (Dict(str->Dict)): Mapping of vApp base names to vApp data

    Returns:
        Dict(str->int): A mapping of check config names to database IDs
    """
    check_ids = {}
    for vapp, vapp_data in vapps.items():
        for system, system_data in vapp_data['systems'].items():
            # Check that a system has checks, some systems may be unscored
            if 'checks' in system_data:
                checks = system_data['checks']
                for name, check_data in checks.items():
                    check_type = check_data['type']
                    port = check_data['port']
                    checker = check_data['checker']
        
                    poller = get_poller(check_type)
                    checker = get_checker(check_type, checker)
            
                    db_id = db.insert('service_check',
                        ['name', 'port', 'check_function', 'poller', 'system'],
                        (name, port, checker, poller, system))
                    check_ids[name] = db_id
    return check_ids

def write_check_ios(vapps, check_ids):
    """
    Write CheckIOs to the database.

    Arguments:
        vapps (Dict(str->Dict)): Mapping of vApp base names to vApp data
        check_ids (Dict(int->int)): A mapping of check config IDs to check database IDs

    Returns:
        Dict(str->int): A mapping of CheckIO config names to database IDs
    """
    check_io_ids = {}

    for vapp, vapp_data in vapps.items():
        for system, system_data in vapp_data['systems'].items():
            if 'checks' in system_data:
                for check, check_data in system_data['checks'].items():
                    for check_io_name, check_io_data in check_data['ios'].items():
                        # Construct poll input data
                        poll_input_class = get_poll_input(check_data['type'])
                        poll_input = [poll_input_class, check_io_data['input']]
                        poll_input = json.dumps(poll_input)

                        expected = check_io_data['output']
                        expected = json.dumps(expected)
                        cid = check_ids[check]
                
                        db_id = db.insert('check_io',
                            ['input', 'expected', 'check_id'],
                            (poll_input, expected, cid))
                        check_io_ids[check_io_name] = db_id
    return check_io_ids

def write_credentials(credentials, teams, check_io_ids):
    """
    Write credentials to the database.

    Arguments:
        credentials (Dict): A dictionary of credential data
        team (Dict(str->Dict)): Mapping of team names to team data
        check_io_ids (Dict(str->int)): A mapping of CheckIO config names to CheckIO
            database IDs
    """
    default_pass = credentials['default_password']
    local_creds = credentials['local']

    if 'domain' in credentials:
        domain_creds = credentials['domain']
    else:
        domain_creds = {}

    for team in teams.values():
        team_id = team['team_num']

        # Write local credential set
        write_cred_set(local_creds, default_pass, team_id, check_io_ids)

        # Write domain credential sets
        for domain, dcreds in domain_creds.items():
            write_cred_set(dcreds, default_pass, team_id, check_io_ids, domain)

def write_cred_set(creds, default_pass, team_id, check_io_ids, domain=None):
    """
    Write a set of credentials for the given team to the database.

    Arguments:
        creds (Dict(str->Dict)): A mapping of usernames to credential data
        default_pass (str): The default password
        team_id (int): ID of the team the credentials are for
        check_io_ids (List(int)): List of IDs for the associated CheckIOs
        domain (str, optional): Active Directory domain of the credentials
    """
    for user, cred_data in creds.items():
        # Check for user-specific password
        if 'password' in cred_data:
            passwd = cred_data['password']
        else:
            passwd = default_pass
        cio_names = cred_data['ios']

        # Gather all of the check IOs for which this credential is used
        cio_ids = [check_io_ids[cio_name] for cio_name in cio_names]
        cred_input = {}   # cred_id -> List(checkio_id)
        cred_check = {}   # check_id -> cred_id

        for cio_id in cio_ids:
            # Get the check and service this check IO belongs to
            check_id = db.get('check_io', ['check_id'],
                              where='id=%s', args=(cio_id))[0]

            if check_id in cred_check:
                # The credential has already been inserted into the table
                cred_input[cred_check[check_id]].append(cio_id)
            else:
                # Insert the credential into the credential table
                if domain is None:
                    cred_id = db.insert('credential',
                                        ['username', 'password', 'team_id',
                                         'check_id'],
                                        (user, passwd, team_id, check_id))
                else:
                    cred_id = db.insert('credential',
                                        ['username', 'password', 'team_id',
                                         'check_id', 'domain'],
                                        (user, passwd, team_id,
                                         check_id, domain))
                cred_input[cred_id] = [cio_id]
                cred_check[check_id] = cred_id

        # Insert relations into the cred-input table
        for cred_id, io_ids in cred_input.items():
            for io_id in io_ids:
                db.insert('cred_input', ['cred_id', 'check_io_id'],
                          (cred_id, io_id))
