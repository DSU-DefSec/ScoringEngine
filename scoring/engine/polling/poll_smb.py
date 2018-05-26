import smb
from smb.base import *
from smb.smb_structs import *
from nmb.NetBIOS import NetBIOS
from smb.SMBConnection import SMBConnection
import socket

from .poller import PollInput, PollResult
from .file_poller import FilePoller

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

    def poll(self, poll_input):
        username = poll_input.credentials.username
        password = poll_input.credentials.password
        domain = poll_input.credentials.domain
    
        try:
            if domain is None:
                conn = SMBConnection(username, password, '', poll_input.hostname)
            else:
                conn = SMBConnection(username, password, '', poll_input.hostname, domain.domain)

            conn.connect(poll_input.server, poll_input.port)

            extension = self.get_extension(poll_input.path)
            f = self.open_file(extension)
            conn.retrieveFile(poll_input.sharename, poll_input.path, f)
            f.close()
            conn.close()

            result = SmbPollResult(f.name)
            return result
        except Exception as e:
            result = SmbPollResult(None, e)
            return result
