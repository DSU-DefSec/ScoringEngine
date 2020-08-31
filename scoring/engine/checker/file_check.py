"""
This module contains different functions for checking the integrity of files
pulled by file-based pollers.
"""

import hashlib
import difflib
REF_PAGES_DIR = 'checkfiles/expected'

def direct_match(poll_result, expected):
    """
    Check whether the contents of the file matches the expected contents
    exactly using a direct match. This should only be used if the expected content
    is small.

    Arguments:
        poll_result (PollResult): The result of polling a file-based service
        expected (List(str)): The expected file contents

    Returns:
        bool: Whether the file matched the expected content
    """
    if poll_result.file_contents is None:
        return False
    return expected[0] == poll_result.file_contents


def hash_match(poll_result, expected):
    """
    Check whether the contents of the file matches the expected contents
    using a cryptographic hashing algorithm.

    Arguments:
        poll_result (PollResult): The result of polling a file-based service
        expected (Dict(str->str)): A dictionary containing the expected hash of the file

    Returns:
        bool: Whether the file matched the expected hash
    """
    if poll_result.file_name is None: # Failed to pull a file
        return False

    f = open(poll_result.file_name, 'rb')
    content = f.read()
    f.close()

    sha1 = hashlib.sha1()
    sha1.update(content)
    hex_hash = sha1.hexdigest()

    return hex_hash == expected['hash']

def diff_match(poll_result, expected):
    """
    Check whether the contents of the file matches the expected contents
    within a given tolerance based on a line-by-line diff of the two files.

    Arguments:
        poll_result (PollResult): The result of polling a file-based service
        expected (Dict(str->str)): A dictionary containing the name of the file to check against and the tolerance of the check

    Returns:
        bool: Whether the file was within tolerance levels
    """
    if poll_result.file_name is None:
        return False

    tolerance = expected['tolerance']

    # Get polled file
    f = open(poll_result.file_name, 'r')
    page = f.readlines()

    # Get expected file
    expected_file = open('%s/%s' % (REF_PAGES_DIR, expected['file']), 'r')
    expected_page = expected_file.readlines()
    
    # Diff the files and separate the headings and differences
    diff = difflib.unified_diff(page, expected_page)
    diff_lines = [line for line in diff][2:]
    headings = [line for line in diff_lines if line[0] == '@']
    diffs = [line for line in diff_lines if line[0] in ['+', '-']]

    # Count the number of lines that are different based on the diff headings
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
    
    # Determine the percent difference from the expected page
    difference = num_diff / float(len(expected_page))

    if difference <= tolerance:
        return True
    else:
        return False 
