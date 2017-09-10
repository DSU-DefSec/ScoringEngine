
def match_ldap_output(poll_result, expected):
    if poll_result.output is None:
        return False

    output = poll_result.output
    # Decode all strings in output
    for key in output.keys():
        for i in range(len(output[key])):
            output[key][i] = output[key][i].decode()

    return output == expected
