import socket

from .poller import PollInput, PollResult
from .file_poller import FilePoller
import subprocess

class SmbPollInput(PollInput):

    def __init__(self, action, sharename, path, server=None, port=None):
        super(SmbPollInput, self).__init__(server, port)
        self.action = action
        self.sharename = sharename
        self.path = path

class SmbPollResult(PollResult):

    def __init__(self, file_name, exceptions=None):
        super(SmbPollResult, self).__init__(exceptions)
        self.file_name = file_name

class SmbPoller(FilePoller):

    def poll(self, poll_input):
        username = poll_input.credentials.username
        password = poll_input.credentials.password
        domain = poll_input.credentials.domain

        share = '//{}/{}'.format(poll_input.server, poll_input.sharename)

        if poll_input.action == 'get':
            extension = self.get_extension(poll_input.path)
            f = self.open_file(extension)
            f.close()
            cmd = 'get {} {}'.format(poll_input.path, f.name)
        else:
            fname = poll_input.path.split('/')[-1]
            cmd = 'put {0} {1}; rm {1}'.format(poll_input.path, fname)

        smbcli = ['smbclient', '-U', username, share, password, '-c', cmd]
        if not domain is None:
            smbcli.extend(['-W', domain.domain])
        try:
            subprocess.check_output(smbcli, stderr=subprocess.STDOUT)
            if poll_input.action == 'get':
                result = SmbPollResult(f.name)
            else:
                result = SmbPollResult(None)
            return result
        except Exception as e:
            result = SmbPollResult(None, e.output)
            return result
