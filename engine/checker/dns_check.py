"""
This module contains different functions for checking the result of DNS pollers.
"""
def any_match(poll_result, expected):
    """
    Check whether the DNS answer in the given poll_result matches *any* of the
    answers in expected.

    Arguments:
        poll_result (DnsPollResult): The result of the DNS poll
        expected (Dict(str->List(str))): The expected answers

    Returns:
        bool: Whether the poller's answer matched any of the expected answers
    """
    if poll_result.exception != "None":
        return False

    host = poll_result.answer.split('.')[3]
    host = int(host)
    ans = expected['answer']
    return host in ans
