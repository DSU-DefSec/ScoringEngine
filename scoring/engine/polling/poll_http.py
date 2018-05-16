import requests
from requests.exceptions import *
import tempfile
import re

from .poller import PollInput, PollResult, Poller

class HttpPollInput(PollInput):

    def __init__(self, proto, path, server=None, port=None):
        super(HttpPollInput, self).__init__(server, port)
        self.proto = proto
        self.path = path

class HttpPollResult(PollResult):

    def __init__(self, file_contents, exceptions):
        super(HttpPollResult, self).__init__(exceptions)
        self.file_contents = None

class HttpPoller(Poller):
    
    def poll(self, poll_input):
        try:
            proto = poll_input.proto
            server = poll_input.server
            port = poll_input.port
            path = poll_input.path
            url = '{}://{}:{}/{}'.format(proto, server, port, path)
            r = requests.get(url, verify=False)
            r.raise_for_status()

            content = re.sub(r'\?[^"]*', '', r.text)
            result = HttpPollResult(content, None)
            return result
        except Exception as e:
            result = HttpPollResult(None, e)
            return result
