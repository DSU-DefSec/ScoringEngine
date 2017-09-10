import pymssql
import socket

from poller import PollInput, PollResult, Poller

class MsSqlPollInput(PollInput):

    def __init__(self, domain, db, query, server=None, port=None):
        super(MsSqlPollInput, self).__init__(server, port)
        self.domain = domain
        self.db = db
        self.query = query

class MsSqlPollResult(PollResult):

    def __init__(self, output, exceptions):
        super(MsSqlPollResult, self).__init__(exceptions)
        self.output = output

class MsSqlPoller(Poller):

    def poll(self, poll_input):
        socket.setdefaulttimeout(10)
    
        username = poll_input.credentials.username
        password = poll_input.credentials.password
    
        try:
            conn = pymssql.connect(poll_input.server,
                                   '{}\\{}'.format(poll_input.domain, username),
                                   password, poll_input.db,timeout=2)
            cursor = conn.cursor()
            cursor.execute(poll_input.query)
            output = ' '.join([str(row[0]) for row in cursor.fetchall()])
            
            result = MsSqlPollResult(output)
            return result
        except Exception as e:
            result = MsSqlPollResult(None, e)
            return result
