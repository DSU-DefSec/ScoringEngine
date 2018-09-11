import requests
from requests.exceptions import *
import re
from .poller import PollInput, PollResult, Poller
from .file_poller import FilePoller


class HttpPollInput(PollInput):

    def __init__(self, proto, path, server=None, port=None):
        super(HttpPollInput, self).__init__(server, port)
        self.proto = proto
        self.path = path

class HttpPollResult(PollResult):

    def __init__(self, file_name, exceptions):
        super(HttpPollResult, self).__init__(exceptions)
        self.file_name = file_name

class HttpPoller(FilePoller):
    
    def poll(self, poll_input):
        try:
            proto = poll_input.proto
            server = poll_input.server
            port = poll_input.port
            path = poll_input.path
            url = '{}://{}:{}/{}'.format(proto, server, port, path)
            r = requests.get(url, verify=False)
            r.raise_for_status()

            content = r.text
#            content = re.sub(r'\?[^"]*', '', content)

            f = self.open_file('html')
            f.write(content.encode('utf-8'))
            f.close()

            result = HttpPollResult(f.name, None)
            return result
        except Exception as e:
            result = HttpPollResult(None, e)
            return result
