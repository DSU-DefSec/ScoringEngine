
def sent_successfully(poll_result, expected):
    if poll_result.exceptions is not None:
        return False

    return poll_result.sent
