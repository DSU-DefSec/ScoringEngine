from .. import config

import logging
logger=logging.getLogger(__name__)
from smb.base import *
from smb.smb_structs import *

from nmb.NetBIOS import NetBIOS
from smb.SMBConnection import SMBConnection
import smb, random, hashlib, tempfile
import socket

ERROR_STRINGS = {
    'NotReadyError': 'Authentication failed: %s %s',
    'NotConnectedError': 'Server Disconnected: %s',
}

def run(options):
    ip = options['ip']
    port = options['port']
    username = options['username']
    password = options['password']

    test = random.choice(config.SMB_FILES)
    expected = test['checksum']

    try:
        n = NetBIOS()
        hostname = n.queryIPForName(ip)[0]
        n.close()

        conn = SMBConnection(username, password, '', hostname, config.DOMAIN)
        conn.connect(ip, port)
        t = tempfile.TemporaryFile()
        conn.retrieveFile(test['sharename'], test['path'], t)
    except (SMBTimeout, socket.timeout):
        logger.debug('Timeout')
        return False
    except NotReadyError:
        logger.debug(ERROR_STRINGS['NotReadyError'] % (username, password))
        return False
    except (NotConnectedError, UnsupportedFeature, ProtocolError, OperationFailure) as e:
        name = e.__class__.__name__
        if name in ERROR_STRINGS:
            logger.debug(ERROR_STRINGS[name] % e)
        else:
            logger.debug('%s: %s' % (name, e))
        return False

    sha1 = hashlib.sha1()
    t.seek(0)
    sha1.update(t.read())
    t.close()
    checksum = sha1.hexdigest()

    if checksum == expected:
        return True
    else:
        logger.debug('Check failed: output: %s | expected: %s' % (checksum, expected))
        return False
