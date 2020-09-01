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
    """
    Wrapper for the inputs to an HttpPoller.

    Attributes:
        proto (str): Protocol (http or https) of the request
        path (str): HTTP path of the request
        host (str, optional): The HTTP host of the request. If None, the server IP is used instead
        user_field (str, optional): The name of the user field of a login form if any
        pass_field (str, optional): The name of the password field of a login form if any
    """
    def __init__(self, proto, path, host=None, user_field=None, pass_field=None, server=None, port=None):
        super(HttpPollInput, self).__init__(server, port)
        self.proto = proto
        self.path = path
        self.host = host
        self.user_field = user_field
        self.pass_field = pass_field

class HttpPollResult(PollResult):
    """
    Wrapper for the results of polling an HTTP service.

    Attributes:
        file_name (str): The file name of the saved HTTP response
    """
    def __init__(self, file_name, exception):
        super(HttpPollResult, self).__init__(exception)
        self.file_name = file_name

class HttpPoller(FilePoller):
    """
    A poller for HTTP services.

    This poller works with http and https, and it can log in to authenticated pages.
    """
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
    """
    Log in to an HTTP site.

    Arguments:
        poll_input (HttpPollInput): 
        session (Session): The request session which keeps track of authentication
        headers (Dict(str->str)): The HTTP headers
        url (str): The url of the login page
        content (str): The HTML content of the login page
    """
    username = poll_input.credentials.username
    password = poll_input.credentials.password
    data = {poll_input.user_field: username, poll_input.pass_field: password}

    # Retrieve the values of hidden inputs to the login form
    soup = BeautifulSoup(content, 'html.parser')
    for field in soup.find_all(type='hidden'):
        if not field.get('value') is None:
            data[field['name']] = field['value']

    # Log in
    r = session.post(url, data, headers=headers, allow_redirects=False)
    r.raise_for_status()

    # Follow redirects past the login page
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
