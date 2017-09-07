from .. import config

import logging
logger=logging.getLogger(__name__)
import socket, errno

import ftplib
import random, hashlib, tempfile

ERROR_STRINGS = {
    'error_reply': 'Unexpected Reply: %s',
    'error_temp':  'Temporary Error: %s',
    'error_perm':  'Permanent Error: %s',
    'error_proto': 'Protocol Error: %s',
    errno.ECONNREFUSED: 'Connection Refused',
}

def run(options):
    ip = options['ip']
    port = options['port']
    username = options['username']
    password = options['password']

    test = random.choice(config.FTP_FILES)
    expected = test['checksum']

    ftp = ftplib.FTP()
    t = tempfile.TemporaryFile()

    try:
        ftp.connect(ip, port, timeout=2)
        ftp.login(user=username, password=password)
        ftp.retrbinary('RETR {}'.format(test['path']), t.write)
        ftp.quit()
    except socket.timeout:
        logger.debug('Timeout')
        return False
    except socket.error as e:
        logger.debug(ERROR_STRINGS[e.errno])
        return False
    except ftplib.all_errors as e:
        error_string = ERROR_STRINGS[e.__class__.__name__]
        logger.debug(error_string % e)
        return False

    sha1 = hashlib.sha1()
    t.seek(0)
    sha1.update(t.read())
    t.close()

    checksum = sha1.hexdigest()

    if checksum == expected:
        return True
    else:
        logger.debug('Checksum failed: Output: %s | Expected: %s' % (checksum, expected))
        return False
