from .. import config
import os

def run(options):
    ip = options['ip']

    res = os.system('ping -W2 -q {} > /dev/null'.format(ip))
    if res == 0:
        return True
    else:
        return False
