import subprocess

from .poller import PollInput, PollResult, Poller

class RdpPollInput(PollInput):

    def __init__(self, server=None, port=None):
        super(RdpPollInput, self).__init__(server, port)

class RdpPollResult(PollResult):

    def __init__(self, authenticated, exceptions=None):
        super(RdpPollResult, self).__init__(exceptions)
        self.authenticated = authenticated

class RdpPoller(Poller):

    def poll(self, poll_input):
        username = poll_input.credentials.username
        password = poll_input.credentials.password
        domain = poll_input.credentials.domain
        
        if domain is None:
            opt_str = '--ignore-certificate --authonly -u \'{}\' -p \'{}\' {}:{}'
            options = opt_str.format(
                    username, password,
                    poll_input.server, poll_input.port)
        else:
            opt_str = '--ignore-certificate --authonly -d {} -u \'{}\' -p \'{}\' {}:{}'
            options = opt_str.format(
                    domain.domain, username, password,
                    poll_input.server, poll_input.port)

        try:
            output = subprocess.check_output('xfreerdp {}'.format(options), shell=True, stderr=subprocess.STDOUT)
            result = RdpPollResult(True)
            return result
        except Exception as e:
            if ('connected to' in str(e.output) and 'Authentication failure' not in str(e.output)) or (e.returncode == 131 and 'negotiation' in str(e.output)):
                result = RdpPollResult(True)
                return result
            print("{{{{%s}}}}" % e.output)
            result = RdpPollResult(False, e)
            return result
