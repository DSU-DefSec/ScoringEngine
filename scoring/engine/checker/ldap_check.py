from base64 import b64encode
def match_ldap_output(poll_result, expected):
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
