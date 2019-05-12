import ftplib
from .poller import PollInput, PollResult
from .file_poller import FilePoller
import time, timeout_decorator

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
    def __init__(self, file_name, exceptions):
        super(FtpPollResult, self).__init__(exceptions)
        self.file_name = file_name

class FtpPoller(FilePoller):
    """
    """

    @timeout_decorator.timeout(20, use_signals=False)
    def poll(self, poll_input):
        username = poll_input.credentials.username
        password = poll_input.credentials.password

        ftp = ftplib.FTP()

        extension = self.get_extension(poll_input.filepath)
        f = self.open_file(extension)

        try:
            ftp.connect(poll_input.server, poll_input.port)
            ftp.login(user=username, passwd=password)
            ftp.set_pasv(True)
            ftp.retrbinary('RETR {}'.format(poll_input.filepath), f.write)
            f.close()
            ftp.quit()

            result = FtpPollResult(f.name, None)
            return result
        except Exception as e:
            f.close()
            result = FtpPollResult(None, e)
            return result
