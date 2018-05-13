# Courtesy of stackoverflow
from functools import wraps
import errno
import os
import signal

def timeout(seconds, error_message=os.strerror(errno.ETIME)):
    """
    A decorator which causes the function it is applied to to timeout after the given number of seconds.

    Arguments:
        seconds (int): The number of seconds before the function times out
        error_message (str): The message to use in the error message
    """
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator
