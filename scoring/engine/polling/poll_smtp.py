from smtplib import *
import socket
import random
import time, timeout_decorator
from .poller import PollInput, PollResult, Poller

class SmtpPollInput(PollInput):

    def __init__(self, fqdn, users, message, server=None, port=None):
        super(SmtpPollInput, self).__init__(server, port)
        self.fqdn = fqdn
        self.users = users
        self.message = message


class SmtpPollResult(PollResult):

    def __init__(self, sent, exception=None):
        super(SmtpPollResult, self).__init__(exception)
        self.sent = sent


class SmtpPoller(Poller):

    @timeout_decorator.timeout(20, use_signals=False)
    def poll(self, poll_input):
        from_user = random.choice(poll_input.users)
        to_user = random.choice(poll_input.users)
        from_addr = "%s@%s" % (from_user, poll_input.fqdn)
        to_addr = "%s@%s" % (to_user, poll_input.fqdn)
        message = poll_input.message
    
        try:
            smtp = SMTP(poll_input.server, poll_input.port)
            smtp.sendmail(from_addr, to_addr, 'Subject: {}'.format(message))
            smtp.quit()
    
            result = SmtpPollResult(True)
            return result
        except Exception as e:
            result = SmtpPollResult(False, e)
            return result
