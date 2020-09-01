
def line_in_log(poll_result, expected):
    if poll_result.exception is None:
        return False

    for log in poll_result.contents:
        if log == expected['contents']:
            return True
    return False

