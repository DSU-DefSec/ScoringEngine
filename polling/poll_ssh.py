from paramiko import client
from paramiko.ssh_exception import *
import socket

from .poller import PollInput, PollResult, Poller

class SshPollInput(PollInput):

    def __init__(self, server=None, port=None):
        super(SshPollInput, self).__init__(server, port)


class SshPollResult(PollResult):

    def __init__(self, authenticated, exceptions=None):
        super(SshPollResult, self).__init__(exceptions)
        self.authenticated = authenticated


class SshPoller(Poller):
    def poll(self, poll_input):
        username = poll_input.credentials.username
        password = poll_input.credentials.password
    
        try:
            cli = client.SSHClient()
            cli.load_host_keys('/dev/null')
            cli.set_missing_host_key_policy(client.AutoAddPolicy())
            cli.connect(poll_input.server, poll_input.port, username, password, timeout=poll_input.timeout)
            cli.close()
    
            result = SshPollResult(True)
            return result
        except (Exception, socket.error) as e:
            result = SshPollResult(False, e)
            return result
        except SSHException as e:
            result = SshPollResult(False, e)
            return result
