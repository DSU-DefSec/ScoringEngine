import subprocess

from poller import PollInput, PollResult, Poller

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
        
        options = '/d:{} /u:{} /p:{} /v:{}:{} /auth-only'.format(
                poll_input.domain, username, password,
                poll_input.server, poll_input.port)
        try:
            output = subprocess.check_call('xfreerdp {} 2 >&1 > /dev/null'.format(options), shell=True)
            result = RdpPollResult(True)
            return result
        except Exception as e:
            result = RdpPollResult(False, e)
            return result
