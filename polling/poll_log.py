from .poller import PollInput, PollResult, Poller
import datetime

class LogPollInput(PollInput):
    """Wrapper for the inputs to a LogPoller.
    
    Attributes:
        log_file (str): Log file to search.
        time_period (int): The amount of time (in seconds) before the
            time of check to include in the log search.
    """
    def __init__(self, log_file, time_period, server=None, port=None):
        super(LogPollInput, self).__init__(server, port)
        self.log_file = log_file
        self.time_period = time_period

class LogPollResult(PollResult):
    """Wrapper for the results of polling a log file.

    Attributes:
        contents (str): Contents of the log file in the given time range.
        exceptions (Exception): Exceptions raised in polling, if any. None
            if there was no error.
    """
    def __init__(self, contents, exception=None):
        super(LogPollResult, self).__init__(exception)
        self.contents = contents

class LogPoller(Poller):
    """A Poller for log files.

    This Poller searches a log file and returns the logs for a given
    period of time.

    Logs are expected to be of the form:
    yyyy-mm-dd HH:MM:SS|log values
    """
    def poll(self, poll_input):
        try:
            log = open(poll_input.log_file, 'r')
            contents = log.readlines()
            period_contents = []
            for line in contents:
                logtime = line.split('|')[0]
                logtime = datetime.strptime(logtime, '%y-%m-%d %H:%M:%S')
                now = datetime.datetime.now()
                tdelta = (now - logtime).total_seconds()

                if tdelta < poll_input.time_period:
                    period_contents.append(line.strip())
            result = LogPollResult(contents)
            return result
        except Exception as e:
            result = LogPollResult(None, e)
            return result
