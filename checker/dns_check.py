
def any_match(poll_result, expected):
    if poll_result.exception != "None":
        return False

    return poll_result.answer.split('.')[3] in expected
