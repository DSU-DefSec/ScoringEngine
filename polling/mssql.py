from .. import config

import logging
logger=logging.getLogger(__name__)

import pymssql, socket, random

ERROR_STRINGS = {
    'NotSupportedError': 'Operation Not Supported: %s',
}

def run(options):
    socket.setdefaulttimeout(2)

    ip = options['ip']
    username = options['username']
    password = options['password']

    test = random.choice(config.MSSQL_QUERIES)
    expected = test['response']

    try:
        conn = pymssql.connect(ip, '{}\\{}'.format(config.DOMAIN, username), password, test['db'])
        cursor = conn.cursor()
        cursor.execute(test['query'])
        response = ' '.join([str(row[0]) for row in cursor.fetchall()])
    except pymssql.Error as e:
        name = e.__class__.__name__
        if name in ERROR_STRINGS:
            error_string = ERROR_STRINGS[name]
            logger.debug(error_string % e)
        else: 
            logger.debug('%s: %s' % (name, e))
        return False

    if response == expected:
        return True
    else:
        logger.debug('Check failed: output: %s | expected: %s' % (response, expected))
        return False
