import socket
import time, timeout_decorator
from .poller import PollInput, PollResult
from .file_poller import FilePoller
import subprocess

class SmbPollInput(PollInput):

    def __init__(self, hostname, sharename, path, server=None, port=None):
        super(SmbPollInput, self).__init__(server, port)
        self.hostname = hostname
        self.sharename = sharename
        self.path = path

class SmbPollResult(PollResult):

    def __init__(self, file_name, exceptions=None):
        super(SmbPollResult, self).__init__(exceptions)
        self.file_name = file_name

class SmbPoller(FilePoller):

    @timeout_decorator.timeout(20, use_signals=False)
    def poll(self, poll_input):
        username = poll_input.credentials.username
        password = poll_input.credentials.password
        domain = poll_input.credentials.domain

        share = '//{}/{}'.format(poll_input.server, poll_input.sharename)

        extension = self.get_extension(poll_input.path)
        f = self.open_file(extension)
        f.close()
        cmd = 'get "{}" "{}"'.format(poll_input.path, f.name)
        smbcli = ['smbclient', '-U', username, share, password, '-c', cmd]
        if not domain is None:
            smbcli.extend(['-W', domain.domain])
        try:
            subprocess.check_output(smbcli, stderr=subprocess.STDOUT)
            result = SmbPollResult(f.name)
            return result
        except Exception as e:
            result = SmbPollResult(None, e.output)
            return result
