import ftplib
import tempfile
from poller import PollInput, PollResult, Poller

class FtpPollInput(PollInput):
    """Wrapper for the inputs to a FtpPoller.
    
    Attributes:
        filepath (str): Path of file to get
    """
    def __init__(self, filepath, server=None, port=None):
        super(FtpPollInput, self).__init__(server, port)
        self.filepath = filepath

class FtpPollResult(PollResult):
    """Wrapper for the results of polling an FTP service.

    Attributes:
        file (file handle): File retrieved. None if there was an error.
        exceptions (Exception): Exceptions raised in polling, if any. None
            if there was no error.
    """
    def __init__(self, file, exceptions):
        super(FtpPollResult, self).__init__(exceptions)
        self.file = file

class FtpPoller(Poller):
    """
    """
    def poll(self, poll_input):
        username = poll_input.credentials.username
        password = poll_input.credentials.password

        ftp = ftplib.FTP()
        t = tempfile.TemporaryFile()
        try:
            ftp.connect(poll_input.server, poll_input.port, timeout=2)
            ftp.login(user=username, password=password)
            ftp.retrbinary('RETR {}'.format(poll_input.filepath), t.write)
            ftp.quit()
            result = FtpPollResult(t, e)
        except Exception as e:
            result = FtpPollResult(None, e)
            return result
