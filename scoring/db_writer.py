import db
import bcrypt
import json

def get_poller(check_type):
    poller_fmt = 'engine.polling.poll_{}.{}Poller'
    poller = poller_fmt.format(check_type, check_type.title())
    return poller

def get_poll_input(check_type):
    poller_fmt = 'engine.polling.poll_{}.{}PollInput'
    poller = poller_fmt.format(check_type, check_type.title())
    return poller

def get_checker(check_type, check_function):
    check_modules = {
        'ssh':   'ssh_check',
        'http':  'file_check',
        'ftp':   'file_check',
        'smb':   'file_check',
        'mysql': 'sql_check',
        'mssql': 'sql_check',
        'smtp':  'smtp_check',
        'ldap':  'ldap_check',
        'dns':   'dns_check',
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
    for base_name,vapp_data in vapps.items():
        subnet = vapp_data['subnet']
        netmask = vapp_data['netmask']
        db.insert('vapp', ['base_name', 'subnet', 'netmask'], (base_name, subnet, netmask,))

def write_systems(vapps):
    """
    Write system names to the databasae.
    """
    for base_name, vapp_data in vapps.items():
        for system,system_data in vapp_data['systems'].items():
            host = system_data['host']
            db.insert('system', ['system', 'vapp', 'host'], (system, base_name, host,))

def write_teams(teams):
    """
    Write the given teams to the database.

    Arguments:
        teams (Dict(int->Team args)): A mapping of team config IDs to team initialization arguments

    Returns:
        Dict(int->int): A mapping of team config IDs to team database IDs
    """
    team_ids = {}
    for name, team_data in teams.items():
        team_num = team_data['team_num']
        db_id = db.insert('team', ['name', 'team_num'], (name, team_num,))
        team_ids[name] = db_id
    return team_ids

def write_web_users(web_users, teams, team_ids):
    """
    Write the given users to the database, hashing their passwords.

    Arguments:
        team_ids (Dict(str->int)): A mapping of team names to team database IDs

    """
    for username, password in web_users.items():
        password = password.encode('utf-8')
        pwhash = bcrypt.hashpw(password, bcrypt.gensalt())
        if username == "admin":
            db.insert('users',
		['username', 'password', 'team_id', 'is_admin', 'is_redteam'],
		(username, pwhash, None, True, False))
        elif username == "redteam":
            db.insert('users',
                 ['username', 'password', 'team_id', 'is_admin', 'is_redteam'],
                 (username, pwhash, None, False, True))


    for team_name, data in teams.items():
        tid = team_ids[team_name]
        username = data['user']['username']
        password = data['user']['password']
        password = password.encode('utf-8')
        pwhash = bcrypt.hashpw(password, bcrypt.gensalt())

        db.insert('users',
            ['username', 'password', 'team_id', 'is_admin', 'is_redteam'],
            (username, pwhash, tid, False, False))

def write_domains(domains):
    """
    Write the given domains to the database.

    Arguments:
        domains (Dict(int->Domain args)): A mapping of domain config IDs to domain initialization arguments

    Returns:
        Dict(int->int): A mapping of domain config IDs to domain database IDs
    """
    domain_ids = {}
    for domain in domains:
        db_id = db.insert('domain', ['fqdn'], (domain,))
        domain_ids[domain] = db_id
    return domain_ids

def write_checks(vapps):
    """
    Write the given checks to the database.

    Arguments:
        checks (Dict(int->Check args)): A mapping of check config IDs to check initialization arguments
        service_ids (Dict(int->int)): A mapping of service config IDs to service database IDs

    Returns:
        Dict(int->int): A mapping of check config IDs to check database IDs
    """
    check_ids = {}
    for vapp, vapp_data in vapps.items():
        for system, system_data in vapp_data['systems'].items():
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
    Write the given input-output pairs to the database.

    Arguments:
        check_ios (Dict(int->CheckIO args)): A mapping of check input-output pair config IDs to check input-output pair initializaiton arguments
        poll_inputs (Dict(int->Serialized PollInput)): A mapping of poll input config IDs to serialized poll inputs
        check_ids (Dict(int->int)): A mapping of check config IDs to check database IDs

    Returns:
        Dict(int->int): A mapping of check input-output pair config IDs to check input-output pair database IDs
    """
    check_io_ids = {}

    for vapp, vapp_data in vapps.items():
        for system, system_data in vapp_data['systems'].items():
            if 'checks' in system_data:
                for check, check_data in system_data['checks'].items():
                    for check_io_name, check_io_data in check_data['ios'].items():
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

def write_credentials(credentials, team_ids, domain_ids, check_io_ids):
    """
    Write the given input-output pairs to the database.

    Arguments:
        credentials (Dict(int->Credential args)): A mapping of credential
            config IDs to credential initialization arguments
        team_ids (Dict(int->int)): A mapping of team config IDs to team database IDs
        domain_ids (Dict(int->int)): A mapping of domain config IDs to
            domain database IDs
        check_io_ids (Dict(int->int)): A mapping of check input-output pair
            config IDs to check input-output pair database IDs
    """
    default_pass = credentials['default_password']
    local_creds = credentials['local']
    if 'domain' in credentials:
        domain_creds = credentials['domain']
    else:
        domain_creds = {}
    for team_id in team_ids.values():
        write_cred_set(local_creds, default_pass, team_id, check_io_ids)
        for domain, dcreds in domain_creds.items():
            domain_id = domain_ids[domain]
            write_cred_set(dcreds, default_pass, team_id, check_io_ids, domain_id)

def write_cred_set(creds, default_pass, team_id, check_io_ids, domain_id=None):
    for user, cred_data in creds.items():
        if 'password' in cred_data:
            passwd = cred_data['password']
        else:
            passwd = default_pass
        cio_names = cred_data['ios']

        # Gather all of the check IOs this credential belongs to
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
                if domain_id is None:
                    cred_id = db.insert('credential',
                                        ['username', 'password', 'team_id',
                                         'check_id'],
                                        (user, passwd, team_id, check_id))
                else:
                    cred_id = db.insert('credential',
                                        ['username', 'password', 'team_id',
                                         'check_id', 'domain_id'],
                                        (user, passwd, team_id,
                                         check_id, domain_id))
                cred_check[check_id] = cred_id
                cred_input[cred_id] = [cio_id]

        # Insert relations into the cred-input table
        for cred_id, io_ids in cred_input.items():
            for io_id in io_ids:
                db.insert('cred_input', ['cred_id', 'check_io_id'],
                          (cred_id, io_id))
