#!/bin/python

import hashlib
import difflib
REF_PAGES_DIR = 'checkfiles'

def hash_match(poll_result, expected):
    if poll_result.file_contents is None:
        return False

    sha1 = hashlib.sha1()
    sha1.update(str(poll_result.file_contents).encode('utf-8'))
    hex_hash = sha1.hexdigest()

    return expected[0] == hex_hash

def diff_match(poll_result, expected):
    if poll_result.file_contents is None:
        return False

    f = poll_result.file_contents
    tolerance = expected['tolerance']
    expected_file = open('%s/%s' % (REF_PAGES_DIR, expected['file']), 'r')

    page = [line + '\n' for line in f.split('\n')]
    expected_page = expected_file.readlines()
    
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
        return False 
