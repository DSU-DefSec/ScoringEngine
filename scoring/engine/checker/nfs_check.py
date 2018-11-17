
def output_check(poll_result, expected):

    if poll_result.output is None:
        return False

    output = poll_result.output
    expected = expected['output']
    return output == expected
