
def any_match(poll_result, expected):
    if poll_result.exception != "None":
        return False

    host = poll_result.answer
    return host in expected
