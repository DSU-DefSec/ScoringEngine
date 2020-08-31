import timeout_decorator
from imaplib import IMAP4
from .poller import PollInput, PollResult, Poller

class ImapPollInput(PollInput):
    """
    Wrapper for the inputs to an ImapPoller

    Attributes:
        starttls (bool): Whether to use STARTTLS
    """
    def __init__(self, starttls, server=None, port=None):
        super(ImapPollInput, self).__init__(server, port)
        self.starttls = starttls

class ImapPollResult(PollResult):
    """
    Wrapper for the results of polling an IMAP service.

    Attributes:
        authenticated (bool): Whether the poller authenticated successfully
    """
    def __init__(self, authenticated, exceptions=None):
        super(ImapPollResult, self).__init__(exceptions)
        self.authenticated = authenticated

class ImapPoller(Poller):
    """
    A poller for IMAP services.
    """
    @timeout_decorator.timeout(20, use_signals=False)
    def poll(self, poll_input):
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
