
def task_successful(poll_result, expected):
    """
    Determines if a task was successful by checking that the last character
    in the output is '0'.

    Typically a command should invoke 'echo $?' to get the return status of the
    last command.
    """
    if poll_result.output is None:
        return False

    output = poll_result.output[0]
    return output[-2] == '0'
