from imaplib import IMAP4
import socket
from polling.poller import PollInput, PollResult, Poller

class ImapPollInput(PollInput):

    def __init__(self, starttls, server=None, port=None):
        super(ImapPollInput, self).__init__(server, port)
        self.starttls = starttls

class ImapPollResult(PollResult):

    def __init__(self, authenticated, exceptions=None):
        super(ImapPollResult, self).__init__(exceptions)
        self.authenticated = authenticated

class ImapPoller(Poller):

    def poll(self, poll_input):
        socket.setdefaulttimeout(10)

        username = poll_input.credentials.username
        password = poll_input.credentials.password
        
        try:
            imap = IMAP4(poll_input.server, poll_input.port)
            if poll_input.starttls:
                imap.starttls()
            imap.login(username, password)
            imap.logout()

            result = ImapPollResult(True)
            return result
        except Exception as e:
            result = ImapPollResult(False, e)
            return result
