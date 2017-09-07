
def any_match(poll_result, expected):
    if poll_result.answer is not None:
        output = poll_result.answer[0].to_text()
        result = output in expected
    else:
        result = False
    return result
