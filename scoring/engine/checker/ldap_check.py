from base64 import b64encode

def match_ldap_output(poll_result, expected):
    """
    Check whether the output of an LDAP poll matches what is expected.

    Arguments:
        poll_result (LdapPollResult): The result of an LDAP poll
        expected (Dict): The expected output

    Returns:
        bool: Whether the poll result matches the expected output
    """
    if poll_result.output is None:
        return False

    output = poll_result.output

    # Decode all strings in output
    for key in output.keys():
        for i in range(len(output[key])):
            val = output[key][i]
            try:
                output[key][i] = val.decode('utf8')
            except:
                output[key][i] = b64encode(val).decode('utf8')

    return output == expected
