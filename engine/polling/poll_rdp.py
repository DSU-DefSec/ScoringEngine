import time, timeout_decorator
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

    @timeout_decorator.timeout(20, use_signals=False)
    def poll(self, poll_input):
        username = poll_input.credentials.username
        password = poll_input.credentials.password
        domain = poll_input.credentials.domain
        cmd = ['xfreerdp', '--ignore-certificate', '--authonly', '-u', username, '-p', password]
        if not domain is None:
            cmd.extend(['-d', domain.domain])
            opt_str = '--ignore-certificate --authonly -u \'{}\' -p \'{}\' {}:{}'
        cmd.append('{}:{}'.format(poll_input.server, poll_input.port))

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            result = RdpPollResult(True)
            return result
        except Exception as e:
#            if e.returncode == 131 and 'negotiation' in str(e.output) and not 'Connection reset by peer' in str(e.output):
#                result = RdpPollResult(True)
#                return result
            #print("{{{{%s}}}}" % e.output)
            result = RdpPollResult(False, e)
            return result
