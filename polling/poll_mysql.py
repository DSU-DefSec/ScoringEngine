import pymysql

from .poller import PollInput, PollResult, Poller

class MySqlPollInput(PollInput):
    
    def __init__(self, db, query, server=None, port=None):
        super(MySqlPollInput, self).__init__(server, port)
        self.db = db
        self.query = query

class MySqlPollResult(PollResult):

    def __init__(self, output, exceptions=None):
        super(MySqlPollResult, self).__init__(exceptions)
        self.output = output

class MySqlPoller(Poller):

    def poll(self, poll_input):
        username = poll_input.credentials.username
        password = poll_input.credentials.password
    
        try:
            conn = pymysql.connect(host=poll_input.server, port=poll_input.port,
                                   user=username, password=password, 
                                   database=poll_input.db)
            cursor = conn.cursor()
            cursor.execute(poll_input.query)
            output = ' '.join([res[0] for res in cursor.fetchall()])
            conn.close()
    
            result = MySqlPollResult(output)
            return result
        except Exception as e:
            result = MySqlPollResult(None, e)
            return result
