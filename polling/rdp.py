from .. import config

import logging
logger=logging.getLogger(__name__)

import subprocess

def run(options):
    ip = options['ip']
    port = options['port']
    username = options['username']
    password = options['password']
    

    options = '/d:{} /u:{} /p:{} /v:{}:{} /auth-only'.format(
            config.DOMAIN, username, password, ip, port)

    try:
        subprocess.check_call('xfreerdp {}'.format(options), shell=True)
        return True
    except CalledProcessError as e:
        logger.debug(e)
        return False
