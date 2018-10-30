
def any_match(poll_result, expected):
    if poll_result.exception != "None":
        return False

    host = poll_result.answer.split('.')[3]
    host = int(host)
    ans = expected['answer']
    print(host, ans)
    return host in ans
