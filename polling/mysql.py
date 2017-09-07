from .. import config

import logging
logger=logging.getLogger(__name__)

import pymysql, random

ERROR_STRINGS = {
    'NotSupportedError': 'Operation Not Supported: %s',
}
def run(options):
    ip = options['ip']
    port = options['port']
    username = options['username']
    password = options['password']

    test = random.choice(config.MYSQL_QUERIES)
    expected = test['response']

    try:
        conn = pymysql.connect(host=ip, port=port, user=username, password=password, database=test['db'])
        cursor = conn.cursor()
        cursor.execute(test['query'])
        response = ' '.join([res[0] for res in cursor.fetchall()])
        conn.close()
    except pymysql.Error as e:
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
