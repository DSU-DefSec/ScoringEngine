
def match_sql_output(poll_result, expected):
    if poll_result.output is None:
        return False

    output = expected['output']
    return poll_result.output == output
