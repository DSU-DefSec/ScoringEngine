import subprocess

from .poller import PollInput, PollResult, Poller

class RdpPollInput(PollInput):

    def __init__(self, domain, server=None, port=None):
        super(RdpPollInput, self).__init__(server, port)
        self.domain = domain

class RdpPollResult(PollResult):

    def __init__(self, authenticated, exceptions=None):
        super(RdpPollResult, self).__init__(exceptions)
        self.authenticated = authenticated

class RdpPoller(Poller):

    def poll(self, poll_input):
        username = poll_input.credentials.username
        password = poll_input.credentials.password
        
        options = '--ignore-certificate --authonly -d {} -u {} -p {} {}:{}'.format(
                poll_input.domain, username, password,
                poll_input.server, poll_input.port)
        try:
            output = subprocess.check_output('timeout {} xfreerdp {}'.format(poll_input.timeout, options), shell=True, stderr=subprocess.STDOUT)
            result = RdpPollResult(True)
            return result
        except Exception as e:
            if ('connected to' in str(e.output) and 'Authentication failure' not in str(e.output)) or (e.returncode == 131 and 'negotiation' in str(e.output)):
                result = RdpPollResult(True)
                return result
            print("{{{{%s}}}}" % e.output)
            result = RdpPollResult(False, e)
            return result
