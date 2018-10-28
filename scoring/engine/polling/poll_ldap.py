import ldap

from .poller import PollInput, PollResult, Poller

class LdapPollInput(PollInput):

    def __init__(self, base, filter, attributes, server=None, port=None):
        super(LdapPollInput, self).__init__(server, port)
        self.base = base
        self.filter = filter
        self.attributes = attributes

class LdapPollResult(PollResult):

    def __init__(self, output, exceptions=None):
        super(LdapPollResult, self).__init__(exceptions)
        self.output = output

class LdapPoller(Poller):

    def poll(self, poll_input):
        username = poll_input.credentials.username
        password = poll_input.credentials.password
        domain = poll_input.domain.fqdn
    
        dn = '{}@{}'.format(username, domain)
        base = poll_input.base
        scope = ldap.SCOPE_SUBTREE
        filt = poll_input.filter
        attrs = poll_input.attributes
        try:
            uri = 'ldap://%s:%d' % (poll_input.server, poll_input.port)
            con = ldap.initialize(uri)
            con.simple_bind_s(dn, password)
            output = con.search_st(base, scope, filt, attrs)
            output = output[0][1] # Only check first value
            
            result = LdapPollResult(output)
            return result
        except Exception as e:
            result = LdapPollResult(None, e)
            return result
