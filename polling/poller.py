from multiprocessing import Process
import copy

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

    def attrs(self):
        attrs = copy.copy(self.__dict__)
        del attrs['server']
        del attrs['port']
        return attrs


    def __str__(self):
        return str(self.attrs())


class PollResult(object):
    """Wrapper for the results of polling a service.

    This should be sublcassed for every subclass of Poller.
    """
    def __init__(self, exception):
        self.exception = str(exception)

    def attrs(self):
        attrs = copy.copy(self.__dict__)
        del attrs['exception']
        return attrs

    def __str__(self):
        return str(self.attrs())

class Poller(object):
    """
    
    """
    def poll_timed(self, poll_input):
        output = [None]
        p = Process(target=self.poll_async, args=(poll_input, output))
        p.start()
        p.join(poll_input.timeout)
        if p.isAlive():
            p.terminate()
            return PollResult(Exception('Check Timed Out'))
        else:
            return output[0]

    def poll_async(self, poll_input, output):
        output[0] = self.poll(poll_input)

    def poll(self, poll_input):
        """Poll a service and return a PollResult.

        Args:
            poll_input (PollInput): Input used to interact with the service.

        Returns:
            PollResult: Results of polling the service
        """
