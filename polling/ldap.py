from .. import config

import logging
logger=logging.getLogger(__name__)

import ldap
from ldap import *
import random

ERROR_STRINGS = {
    'INVALID_CREDENTIALS': 'Invalid Credentials: %s %s',
}

def run(options):
    ip = options['ip']
    port = options['port']
    username = options['username']
    password = options['password']

    test = random.choice(config.LDAP_QUERIES)
    dn = test['dn'] % username
    base = test['base']
    scope = ldap.SCOPE_SUBTREE
    filt = test['filter']
    attrs = test['attributes']
    expected = test['expected']
    
    try:
        uri = 'ldap://%s:%d' % (ip, port)
        con = ldap.initialize(uri)
        con.simple_bind_s(dn, password)
        output = con.search_s(base, scope, filt, attrs)
        output = output[0][1] # Only check first value
    except TIMEOUT as e:
        logger.debug('Timeout')
        return False
    except INVALID_CREDENTIALS:
        logger.debug(ERROR_STRINGS['INVALID_CREDENTIALS'] % (dn, password))
    except ldap.LDAPError as e:
        name = e.__class__.__name__
        if name in ERROR_STRINGS:
            error_string = ERROR_STRINGS[name]
            logger.debug(error_string % e)
        else:
            logger.debug('%s: %s' % (name, e))
        return False

    # Decode all strings in output
    for key in output.keys():
        for i in range(len(output[key])):
            output[key][i] = output[key][i].decode()

    if output == expected:
        return True
    else:
        logger.debug('Check failed: output: %s | expected: %s' % (output, expected))
        return False
