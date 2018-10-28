from ..timeout import timeout
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
#        del attrs['server']
#        del attrs['port']
        return attrs

    def serialize(self, obj):
        class_str = '%s.%s' % (self.__module__, self.__class__.__name__)
        args = self.__dict__
        if 'team' in args:
            args['team'] = args['team'].id
        if 'credentials' in args:
            args['credentials'] = args['credentials'].id
        return [class_str, args]

    def __str__(self):
        return str(self.attrs())

    def deserialize(input_class, args, teams, credentials):
        team = None
        creds = None
        if args is None:
            args = {}
        if 'team' in args:
            id = args['team']
            del args['team']
            team = [t for t in teams if t.id == id][0]
        if 'credentials' in args:
            id = args['credentials']
            del args['credentials']
            creds = [c for c in credentials if c.id == id][0]

        poll_input = input_class(**args)
        if team:
            poll_input.team = team
        if creds:
            poll_input.credentials = creds
        return poll_input


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

    def serialize(self, obj):
        class_str = '%s.%s' % (self.__module__, self.__class__.__name__)
        args = self.__dict__
        return [class_str, args]

    def __str__(self):
        return str(self.attrs())

class Poller(object):
    """
    
    """
    def poll_timed(self, poll_input):
        try:
            poll_result = self.poll(poll_input)
        except Exception as e:
            poll_result = PollResult(e)
        return poll_result

    @timeout(20)
    def poll(self, poll_input):
        """Poll a service and return a PollResult.

        Args:
            poll_input (PollInput): Input used to interact with the service.

        Returns:
            PollResult: Results of polling the service
        """
