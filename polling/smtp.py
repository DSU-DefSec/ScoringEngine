from .. import config

import logging
logger=logging.getLogger(__name__)

from smtplib import *
import random, socket, errno

socket.setdefaulttimeout(2)

ERROR_STRINGS = {
    'SMTPNotSupportedError': 'Unsupported Command: %s',
    errno.EHOSTUNREACH: 'No route to host',
}

message = 'Hello from the Scoring Engine!'

def run(options):
    ip = options['ip']
    port = options['port']
    
    from_addr = random.choice(config.SMTP_ADDRESSES)
    to_addr = random.choice(config.SMTP_ADDRESSES)

    try:
        smtp = SMTP(ip, port)
        smtp.sendmail(from_addr, to_addr, 'Subject: {}'.format(message))
        smtp.quit()
        return True
    except socket.timeout:
        logger.debug('Timeout')
        return False
    except socket.error as e:
        logger.debug(ERROR_STRINGS[e.errno])
        return False
    except SMTPException as e:
        name = e.__class__.__name__
        if name in ERROR_STRINGS:
            error_string = ERROR_STRINGS[name]
            logger.debug(error_string % e)
        else:
            logger.debug('%s: %s' % (name, e))
        return False
