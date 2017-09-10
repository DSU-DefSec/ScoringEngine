from smtplib import *
import socket
import random

from poller import PollInput, PollResult, Poller

class SmtpPollInput(PollInput):

    def __init__(self, addresses, message, server=None, port=None):
        super(SmtpPollInput, self).__init__(server, port)
        self.addresses = addresses
        self.message = message


class SmtpPollResult(PollResult):

    def __init__(self, sent, exceptions=None):
        super(SmtpPollResult, self).__init__(exceptions)
        self.sent = sent


class SmtpPoller(Poller):
    def poll(self, poll_input):
        socket.setdefaulttimeout(10)
        
        from_addr = random.choice(poll_input.addresses)
        to_addr = random.choice(poll_input.addresses)
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
