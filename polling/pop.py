from  .. import config

import logging
logger=logging.getLogger(__name__)

import poplib, socket

ERROR_STRINGS = {
    'error_proto':    'Protocol Error: %s',
}

def run(options):
    ip = options['ip']
    port = options['port']
    username = options['username']
    password = options['password']

    try:
        pop = poplib.POP3(ip, port, 2)
        pop.stls()
        pop.user(username)
        pop.pass_(password)
        pop.quit()
        return True
    except socket.timeout:
        logger.debug('Timeout')
        return False
    except poplib.error_proto as e:
        error_string = ERROR_STRINGS[e.__class__.__name__]
        logger.debug(error_string % e)
        return False
