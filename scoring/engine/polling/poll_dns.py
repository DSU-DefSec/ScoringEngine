import time, timeout_decorator
from dns import resolver
from dns.resolver import *
from .poller import PollInput, PollResult, Poller

class DnsPollInput(PollInput):
    """
    Wrapper for the inputs to a DnsPoller.
    
    Attributes:
        record_type (str): DNS record type to query for.
        query (str): Query string to send to server.
        server (str, optional): IP or FQDN of a DNS server to query.
    """
    def __init__(self, record_type, query, server=None, port=None):
        super(DnsPollInput, self).__init__(server, port)
        self.record_type = record_type
        self.query = query

class DnsPollResult(PollResult):
    """
    Wrapper for the results of polling a DNS service.

    Attributes:
        answer (dns.resolver.Answer): DNS query answer. None if there
            was an error.
        exceptions (Exception): Exceptions raised in polling, if any. None
            if there was no error.
    """
    def __init__(self, answer, exception=None):
        super(DnsPollResult, self).__init__(exception)
        self.answer = answer

class DnsPoller(Poller):
    """
    A poller for DNS services.

    This Poller uses a DNS stub resolver to perform DNS queries against
    a server.
    """
    @timeout_decorator.timeout(20, use_signals=False)
    def poll(self, poll_input):
        res = resolver.Resolver()
        res.nameservers = [poll_input.server]
        res.port = poll_input.port
    
        try:
            answer = res.query(poll_input.query, 
                    poll_input.record_type).rrset[0]
            result = DnsPollResult(str(answer))
            return result
        except Exception as e:
            result = DnsPollResult(None, e)
            return result
