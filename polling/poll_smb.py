import smb
from smb.base import *
from smb.smb_structs import *
from nmb.NetBIOS import NetBIOS
from smb.SMBConnection import SMBConnection
import tempfile
import socket

from poller import PollInput, PollResult, Poller

class SmbPollInput(PollInput):

    def __init__(self, domain, sharename, path, server=None, port=None):
        super(SmbPollInput, self).__init__(server, port)
        self.domain = domain
        self.sharename = sharename
        self.path = path

class SmbPollResult(PollResult):

    def __init__(self, file, exceptions=None):
        super(SmbPollResult, self).__init__(exceptions)
        self.file = file

class SmbPoller(Poller):

    def poll(self, poll_input):
        socket.setdefaulttimeout(10)

        username = poll_input.credentials.username
        password = poll_input.credentials.password
    
        try:
            n = NetBIOS()
            hostname = n.queryIPForName(poll_input.server,timeout=10)[0]
            n.close()
    
            conn = SMBConnection(username, password, '', hostname, poll_input.domain)
            conn.connect(poll_input.server, poll_input.port,timeout=10)
            t = tempfile.TemporaryFile()
            conn.retrieveFile(poll_input.sharename, poll_input.path, t)

            result = SmbPollResult(t)
        except Exception as e:
            result = SmbPollResult(None, e)
            return result
