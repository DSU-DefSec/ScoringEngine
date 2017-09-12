
def any_match(poll_result, expected):
    if poll_result.exception != "None":
        return False

    print(poll_result.answer)
    print(expected)
    return poll_result.answer in expected
