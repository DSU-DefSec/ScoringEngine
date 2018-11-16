
def noerror(poll_result, expected):
    print('checkerror')
    print(poll_result.__dict__)
    print(poll_result.exception)
    return poll_result.exception == 'None'
