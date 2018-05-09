
def match_sql_output(poll_result, expected):
    if poll_result.output is None:
        return False

    return poll_result.output == expected[0]
