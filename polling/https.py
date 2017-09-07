from .. import config

import logging
logger=logging.getLogger(__name__)

import requests
from requests.exceptions import *
import hashlib, random

REF_PAGES_DIR = 'engine/http_pages'

def run(options):
    ip = options['ip']
    port = options['port']

    test = random.choice(config.HTTPS_PAGES)
    tolerance = test['tolerance']

    try:
        expected = open('%s/%s' % (REF_PAGES_DIR, test['expected']), 'r')
    except IOError as e:
        logger.debug('Could not open file %s/%s' % (REF_PAGES_DIR, test['expected']))
        raise e

    try:
        r = requests.get('https://{}:{}/{}'.format(ip, port, test['url']), verify=False, timeout=2)
        r.raise_for_status()
    except Timeout:
        logger.debug('Timeout')
        return False
    except RequestException as e:
        logger.debug('%s: %s' % (e.__class__.__name__, e))
        return False

    page = [line + '\n' for line in r.text.split('\n')]
    expected_page = expected.readlines()

    diff = difflib.unified_diff(page, expected_page)
    diff_lines = [line for line in diff][2:]
    headings = [line for line in diff_lines if line[0] == '@']
    diffs = [line for line in diff_lines if line[0] in ['+', '-']]
    
    num_diff = 0
    for heading in headings:
        locations = heading.split(' ')[1:-1]
        lengths = []
        for location in locations:
            if ',' in location:
                lengths.append(int(location.split(',')[1]))
            else:
                lengths.append(0)
        num_diff += abs(lengths[1] - lengths[0])
    num_diff += (len(diffs) - num_diff) / 2

    difference = num_diff / float(len(expected_page))
    if difference <= tolerance:
        return True
    else:
        logger.debug('Check failed: Difference: %0.2f | Tolerance: %f' % (difference, tolerance))
        return False
