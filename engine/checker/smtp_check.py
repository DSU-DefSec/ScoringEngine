
def sent_successfully(poll_result, expected):
    if poll_result.exception != "None":
        return False

    return poll_result.sent
