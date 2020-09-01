def pingable(poll_result, expected):
    """
    Check whether a ping poll was successful.

    Arguments:
        poll_result (PingPollResult): The result of a ping poll
        expected (None): The expected output of the ping poll

    Returns:
        bool: Whether the ping poll was successful
    """
    return poll_result.output == 0
