import pymysql

from .poller import PollInput, PollResult, Poller

class MysqlPollInput(PollInput):
    
    def __init__(self, db, query, server=None, port=None):
        super(MysqlPollInput, self).__init__(server, port)
        self.db = db
        self.query = query

class MysqlPollResult(PollResult):

    def __init__(self, output, exceptions=None):
        super(MysqlPollResult, self).__init__(exceptions)
        self.output = output

class MysqlPoller(Poller):

    def poll(self, poll_input):
        username = poll_input.credentials.username
        password = poll_input.credentials.password
    
        try:
            conn = pymysql.connect(host=poll_input.server, port=poll_input.port,
                                   user=username, password=password, 
                                   database=poll_input.db)
            cursor = conn.cursor()
            cursor.execute(poll_input.query)
            output = cursor.fetchone()[0]
            conn.close()
    
            result = MysqlPollResult(output)
            return result
        except Exception as e:
            result = MysqlPollResult(None, e)
            return result
