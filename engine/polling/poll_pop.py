import poplib

from polling.poller import PollInput, PollResult, Poller

class PopPollInput(PollInput):

    def __init__(self, starttls, server=None, port=None):
        super(PopPollInput, self).__init__(server, port)
        self.starttls = starttls

class PopPollResult(PollResult):

    def __init__(self, authenticated, exceptions=None):
        super(PopPollResult, self).__init__(exceptions)
        self.authenticated = authenticated

class PopPoller(Poller):
    def poll(self, poll_input):
        username = poll_input.credentials.username
        password = poll_input.credentials.password
#        domain = poll_input.credentials.domain
#        if domain is not None:
#            username = '%s@%s' % (username, domain)
    
        try:
            pop = poplib.POP3(poll_input.server, poll_input.port, 2)

            if poll_input.starttls:
                pop.stls()

            pop.user(username)
            pop.pass_(password)
            pop.quit()
            
            result = PopPollResult(True)
        except Exception as e:
            result = PopPollResult(False, e)
        finally:
            return result
