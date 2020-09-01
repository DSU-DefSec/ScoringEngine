def authenticated(poll_result, expected):
    """
    Check whether the poller authenticated successfully.

    Arguments:
        poll_result (PollResult): The poll result
        expected (List or Dict): The expected output

    Returns:
        bool: Whether the poller authenticated successfully
    """
    return poll_result.authenticated
