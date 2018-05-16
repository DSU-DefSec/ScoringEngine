import smb
from smb.base import *
from smb.smb_structs import *
from nmb.NetBIOS import NetBIOS
from smb.SMBConnection import SMBConnection
import tempfile
import socket

from .poller import PollInput, PollResult, Poller

class SmbPollInput(PollInput):

    def __init__(self, hostname, sharename, path, server=None, port=None):
        super(SmbPollInput, self).__init__(server, port)
        self.hostname = hostname
        self.sharename = sharename
        self.path = path

class SmbPollResult(PollResult):

    def __init__(self, file_contents, exceptions=None):
        super(SmbPollResult, self).__init__(exceptions)
        self.file_contents = file_contents

class SmbPoller(Poller):

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
            t = tempfile.TemporaryFile()
            conn.retrieveFile(poll_input.sharename, poll_input.path, t)
            conn.close()

            t.seek(0)
            content = t.read()
            result = SmbPollResult(content)
            return result
        except Exception as e:
            result = SmbPollResult(None, e)
            return result
