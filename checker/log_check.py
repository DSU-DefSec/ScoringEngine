
def line_in_log(poll_result, expected):
    if poll_result.exception is not None:
        return False

    for line in poll_result.contents:
        log = ''.join(line.split('|')[1:])
        if log == expected[0]:
            return True
    return False

