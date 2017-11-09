from .poller import PollInput, PollResult, Poller

class LogPollInput(PollInput):
    """Wrapper for the inputs to a LogPoller.
    
    Attributes:
        log_file (str): Log file to search.
        start_time (str): Start of the time range to search.
        end_time (str): End of the time range to search.
    """
    def __init__(self, log_file, start_time, end_time, server=None, port=None):
        super(LogPollInput, self).__init__(server, port)
        self.log_file = log_file
        self.start_time = start_time
        self.end_time = start_time

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
                time = line.split('|')[0]
                if poll_input.start_time < time < poll_input.end_time:
                    period_contents.append(line.strip())
            result = LogPollResult(contents)
            return result
        except Exception as e:
            result = LogPollResult(None, e)
            return result
