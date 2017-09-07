from .. import config

import logging
logger=logging.getLogger(__name__)

from paramiko import client
from paramiko.ssh_exception import *
import socket, errno

ERROR_STRINGS = {
    'BadHostKeyException':     'Could not verify host key: %s',
    'AuthenticationException': 'Authentication Failed: %s:%s',
    'SSHException':            'General SSH Error: %s',
    'NoValidConnectionsError': 'Unable to connect: %s',
    errno.EHOSTUNREACH: 'No route to host',
}

def run(options):
    ip = options['ip']
    port = options['port']
    username = options['username']
    password = options['password']

    try:
        cli = client.SSHClient()
        cli.load_host_keys('/dev/null')
        cli.set_missing_host_key_policy(client.AutoAddPolicy())
        cli.connect(ip, port, username, password)
        return True
    except socket.timeout:
        logger.debug('Timeout')
        return False
    except AuthenticationException as e:
        error_string = ERROR_STRINGS[e.__class__.__name__]
        logger.debug(error_string % (username, password))
        return False
    except (BadHostKeyException, SSHException, NoValidConnectionsError) as e:
        error_string = ERROR_STRINGS[e.__class__.__name__]
        logger.debug(error_string % e)
        return False
    except socket.error as e:
        logger.debug(ERROR_STRINGS[e.errno])
        return False
