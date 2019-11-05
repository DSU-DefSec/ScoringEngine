import time, timeout_decorator
import requests
from requests.exceptions import *
import re
from .poller import PollInput, PollResult, Poller
from .file_poller import FilePoller
import urllib3
from bs4 import BeautifulSoup
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HttpPollInput(PollInput):

    def __init__(self, proto, path, host=None, user_field=None, pass_field=None, server=None, port=None):
        super(HttpPollInput, self).__init__(server, port)
        self.proto = proto
        self.path = path
        self.host = host
        self.user_field = user_field
        self.pass_field = pass_field

class HttpPollResult(PollResult):
    def __init__(self, file_name, exceptions):
        super(HttpPollResult, self).__init__(exceptions)
        self.file_name = file_name

class HttpPoller(FilePoller):
    
    @timeout_decorator.timeout(20, use_signals=False)
    def poll(self, poll_input):
        try:
            proto = poll_input.proto
            server = poll_input.server

            port = poll_input.port
            path = poll_input.path
            url = '{}://{}/{}'.format(proto, server, path)
            if poll_input.host is None:
                headers = {}
            else:
                headers = {'Host': poll_input.host}
            
            session = requests.Session()
            r = session.get(url, headers=headers, verify=False, allow_redirects=False)
#            while 'Location' in r.headers:
#                url_parts = urllib3.util.parse_url(r.headers['Location'])
#                suburl = ''
#                if not url_parts.scheme is None:
#                    suburl += url_parts.scheme + '://'
#                suburl += poll_input.server
#                suburl += url_parts.path
#                r = sesssion.get(suburl, headers=headers, verify=False)
            r.raise_for_status()

            content = r.text

            if not poll_input.user_field is None:
                content = perform_login(poll_input, session, headers, url, content)

            f = self.open_file('html')
            f.write(content.encode('utf-8'))
            f.close()

            result = HttpPollResult(f.name, None)
            return result
        except Exception as e:
            result = HttpPollResult(None, e)
            return result

def perform_login(poll_input, session, headers, url, content):
    username = poll_input.credentials.username
    password = poll_input.credentials.password
    soup = BeautifulSoup(content, 'html.parser')
    data = {poll_input.user_field: username, poll_input.pass_field: password}
    
    for field in soup.find_all(type='hidden'):
        if not field.get('value') is None:
            data[field['name']] = field['value']

    r = session.post(url, data, headers=headers, allow_redirects=False)
    r.raise_for_status()

    while 'Location' in r.headers:
        url_parts = urllib3.util.parse_url(r.headers['Location'])
        suburl = ''
        if not url_parts.scheme is None:
            suburl += url_parts.scheme + '://'
        suburl += poll_input.server
        suburl += url_parts.path
        r = session.get(suburl, headers=headers, verify=False, allow_redirects=False)
    r.raise_for_status()

    return r.text
