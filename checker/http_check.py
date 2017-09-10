#!/bin/python
import difflib

REF_PAGES_DIR = 'checkfiles'

def diff_match(poll_input, expected):
    if poll_input.file is None:
        return False

    f = poll_input.file
    tolerance = expected['tolerance']
    expected_file = open('%s/%s' % (REF_PAGES_DIR, expected['file']), 'r')

    page = f.readlines()
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
