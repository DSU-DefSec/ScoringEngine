import os

from poller import PollInput, PollResult, Poller

class PingPollInput(PollInput):

    def __init__(self, server=None, port=None):
        super(PingPollInput, self).__init__(server, port)

class PingPollResult(PollResult):

    def __init__(self, output, exceptions=None):
        super(PingPollResult, self).__init__(exceptions)
        self.output = output

class PingPoller(Poller):
    def poll(self, poll_input):
        server = poll_input.server
        output = os.system('ping -W2 -c 5 -q {} > /dev/null'.format(server))
        
        result = PingPollResult(output)
        return result
