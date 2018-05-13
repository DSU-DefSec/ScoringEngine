from . import db

def write_settings(settings):
    """
    Write global settings to the database.

    Arguments:
        settings (Dict(str->str)): A mapping of setting keys and values
    """
    for key, value in settings.items():
        db.insert('settings', ['skey', 'value'], (key, value))

def write_teams(teams):
    """
    Write the given teams to the database.

    Arguments:
        teams (Dict(int->Team args)): A mapping of team config IDs to team
            initialization arguments

    Returns:
        Dict(int->int): A mapping of team config IDs to 
            team database IDs
    """
    team_ids = {}
    for id, team in teams.items():
        db_id = db.insert('team', ['name', 'subnet', 'netmask'], team)
        team_ids[id] = db_id
    return team_ids

def write_web_users(users, teams):
    """
    Write the given users to the database, hashing their passwords.

    Arguments:
        users (Dict(int->User args)): A mapping of user config IDs to user initialization arguments
        teams (Dict(int->int)): A mapping of team config IDs to team database IDs

    Returns:
        Dict(int->int): A mapping of user config IDs to user database IDs
    """
    user_ids = {}
    for id, user_args in users.items():
        ptid, username, password, is_admin = user_args
        tid = teams[ptid] if ptid in teams else None
        password = password.encode('utf-8')
        pwhash = bcrypt.hashpw(password, bcrypt.gensalt())

        db_id = db.insert('users',
            ['username', 'password', 'team_id', 'is_admin'],
            (username, pwhash, tid, is_admin))
        user_ids[id] = db_id
    return user_ids

def write_domains(domains):
    """
    Write the given domains to the database.

    Arguments:
        domains (Dict(int->Domain args)): A mapping of domain config IDs to
            domain initialization arguments

    Returns:
        Dict(int->int): A mapping of domain config IDs to
            domain database IDs
    """
    domain_ids = {}
    for id, domain in domains.items():
        db_id = db.insert('domain', ['fqdn'], domain)
        domain_ids[id] = db_id
    return domain_ids

def write_services(services):
    """
    Write the given services to the database.

    Arguments:
        services (Dict(int->Service args)): A mapping of service config IDs to
            service initialization arguments

    Returns:
        Dict(int->int): A mapping of service config IDs to 
            service database IDs
    """
    service_ids = {}
    for id, service in services.items():
        db_id = db.insert('service', ['host', 'port'], service)
        service_ids[id] = db_id
    return service_ids

def write_checks(checks, service_ids):
    """
    Write the given checks to the database.

    Arguments:
        checks (Dict(int->Check args)): A mapping of check config IDs to check 
            initialization arguments
        service_ids (Dict(int->int)): A mapping of service config IDs to 
            service database IDs

    Returns:
        Dict(int->int): A mapping of check config IDs to 
            check database IDs
    """
    check_ids = {}
    for id, check in checks.items():
        name, check_func, poller, psid = check
        sid = service_ids[psid]

        db_id = db.insert('service_check',
            ['name', 'check_function', 'poller', 'service_id'],
            (name, check_func, poller, sid))
        check_ids[id] = db_id
    return check_ids

def write_check_ios(check_ios, poll_inputs, check_ids):
    """
    Write the given input-output pairs to the database.

    Arguments:
        check_ios (Dict(int->CheckIO args)): A mapping of check input-output
            pair config IDs to check input-output pair initializaiton
            arguments
        poll_inputs (Dict(int->Serialized PollInput)): A mapping of poll
            input config IDs to serialized poll inputs
        check_ids (Dict(int->int)): A mapping of check config IDs to 
            check database IDs

    Returns:
        Dict(int->int): A mapping of check input-output pair config IDs
            to check input-output pair database IDs
    """
    check_io_ids = {}
    for id, check_io in check_ios.items():
        piid, expected, pcid = check_io
        poll_input = poll_inputs[piid]
        cid = check_ids[pcid]

        db_id = db.insert('check_io',
            ['input', 'expected', 'check_id'],
            (poll_input, expected, cid))
        check_io_ids[id] = db_id
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
    for id, credential in credentials.items():
        user, passwd, pdomain_id, pcio_ids = credential

        # Gather all of the check IOs this credential belongs to
        cio_ids = [check_io_ids[pcio_id] for pcio_id in pcio_ids]
        for team_id in team_ids.values():
            cred_input = {}   # cred_id -> List(checkio_id)
            cred_service = {} # service_id -> cred_id

            for cio_id in cio_ids:
                # Get the check and service this check IO belongs to
                check_id = db.get('check_io', ['check_id'],
                                  where='id=%s', args=(cio_id))[0]
                service_id = db.get('service_check', ['service_id'],
                                    where='id=%s', args=(check_id))[0]

                if service_id in cred_service:
                    # The credential has already been inserted into the table
                    cred_input[cred_service[service_id]].append(cio_id)
                else:
                    # Insert the credential into the credential table
                    if pdomain_id is None:
                        cred_id = db.insert('credential',
                                            ['username', 'password', 'team_id',
                                             'service_id', 'domain_id'],
                                            (user, passwd, team_id, service_id))
                    else:
                        domain_id = domain_ids[pdomain_id]
                        cred_id = db.insert('credential',
                                            ['username', 'password', 'team_id',
                                             'service_id', 'domain_id'],
                                            (user, passwd, team_id,
                                             service_id, domain_id))
                    cred_service[service_id] = cred_id
                    cred_input[cred_id] = [cio_id]

            # Insert relations into the cred-input table
            for cred_id, io_ids in cred_input.items():
                for io_id in io_ids:
                    db.insert('cred_input', ['cred_id', 'check_io_id'],
                              (cred_id, io_id))
