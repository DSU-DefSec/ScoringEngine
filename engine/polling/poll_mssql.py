import time, timeout_decorator
import pymssql
import socket

from .poller import PollInput, PollResult, Poller

class MssqlPollInput(PollInput):

    def __init__(self, db, query, server=None, port=None):
        super(MssqlPollInput, self).__init__(server, port)
        self.db = db
        self.query = query

class MssqlPollResult(PollResult):

    def __init__(self, output, exceptions=None):
        super(MssqlPollResult, self).__init__(exceptions)
        self.output = output

class MssqlPoller(Poller):

    @timeout_decorator.timeout(20, use_signals=False)
    def poll(self, poll_input):
        username = poll_input.credentials.username
        password = poll_input.credentials.password
    
        try:
            user = username
            conn = pymssql.connect(poll_input.server,
                                   user,
                                   password, poll_input.db)
            cursor = conn.cursor()
            cursor.execute(poll_input.query)
            output = ' '.join([str(row[0]) for row in cursor.fetchall()])
            
            result = MssqlPollResult(output)
            return result
        except Exception as e:
            result = MssqlPollResult(None, e)
            return result
