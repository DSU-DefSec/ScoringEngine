import requests
from requests.exceptions import *
import re
from .poller import PollInput, PollResult, Poller
from .file_poller import FilePoller
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HttpPollInput(PollInput):

    def __init__(self, proto, path, host=None, server=None, port=None):
        super(HttpPollInput, self).__init__(server, port)
        self.proto = proto
        self.path = path
        self.host = host

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
            url = '{}://{}/{}'.format(proto, server, path)
            if poll_input.host is None:
                r = requests.get(url, verify=False)
            else:
                print(url)
                r = requests.get(url, headers={'Host': poll_input.host}, verify=False, allow_redirects=False)
                if 'Location' in r.headers:
                    url_parts = urllib3.util.parse_url(r.headers['Location'])
                    print(url_parts)
                    url = ''
                    if not url_parts.scheme is None:
                        url += url_parts.scheme + '://'
                    url += poll_input.server
                    url += url_parts.path
                    print(url)
                    r = requests.get(url, headers={'Host': url_parts.host}, verify=False)

            r.raise_for_status()

            content = r.text
            content = re.sub(r'10.0.[0-9]', '', content)

            f = self.open_file('html')
            f.write(content.encode('utf-8'))
            f.close()

            result = HttpPollResult(f.name, None)
            return result
        except Exception as e:
            result = HttpPollResult(None, e)
            return result
