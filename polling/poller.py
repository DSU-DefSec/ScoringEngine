from threading import Thread, Lock

class PollInput(object):
    """Wrapper for the inputs to a Poller.

    This should be subclassed for each subclass of Poller.

    Attributes:
        server (str, optional): IP address or FQDN of a service to poll
        port (int, optional): Port of the service to poll
    """
    def __init__(self, server=None, port=None):
        self.server = server
        self.port = port


class PollResult(object):
    """Wrapper for the results of polling a service.

    This should be sublcassed for every subclass of Poller.
    """
    def __init__(self, exceptions):
        self.exceptions = exceptions

class Poller(object):
    """
    
    """
    def poll(self, poll_input):
        """Poll a service and return a PollResult.

        Args:
            poll_input (PollInput): Input used to interact with the service.

        Returns:
            PollResult: Results of polling the service
        """
