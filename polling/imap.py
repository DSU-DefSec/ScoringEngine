from .. import config

import logging
logger=logging.getLogger(__name__)

from imaplib import IMAP4
import socket, errno

socket.setdefaulttimeout(5)

ERROR_STRINGS = {
    'abort':    'Mail Server Aborted: %s',
    'readonly': 'Could not read mailbox: %s',
    'error':    'IMAP Error: %s',
    errno.EHOSTUNREACH: 'No route to host',
}

def run(options):
    ip = options['ip']
    port = options['port']
    username = options['username']
    password = options['password']
    
    try:
        imap = IMAP4(ip, port)
        imap.starttls()
        imap.login(username, password)
        imap.logout()
        return True
    except socket.timeout:
        logger.debug('Timeout')
        return False
    except socket.error as e:
        logger.debug(ERROR_STRINGS[e.errno])
        return False
    except IMAP4.error as e:
        error_string = ERROR_STRINGS[e.__class__.__name__]
        logger.debug(error_string % e)
        return False
