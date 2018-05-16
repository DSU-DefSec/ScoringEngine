from paramiko import client
from paramiko.ssh_exception import *
import socket

from .poller import PollInput, PollResult, Poller

class SshPollInput(PollInput):

    def __init__(self, task=None, server=None, port=None):
        self.task = task
        super(SshPollInput, self).__init__(server, port)


class SshPollResult(PollResult):

    def __init__(self, authenticated, output=None, exceptions=None):
        super(SshPollResult, self).__init__(exceptions)
        self.authenticated = authenticated
        self.output = output


class SshPoller(Poller):
    def poll(self, poll_input):
        username = poll_input.credentials.username
        password = poll_input.credentials.password
    
        try:
            cli = client.SSHClient()
            cli.load_host_keys('/dev/null')
            cli.set_missing_host_key_policy(client.AutoAddPolicy())
            cli.connect(poll_input.server, poll_input.port, username, password)
            if poll_input.task is not None:
                stdin, stdout, stderr = cli.exec_command(poll_input.task)
                out = stdout.read().decode('utf-8')
                err = stderr.read().decode('utf-8')
                output = (out, err)
                result = SshPollResult(True, output)
            else:
                result = SshPollResult(True)
            cli.close()
            return result
        except (Exception, socket.error) as e:
            result = SshPollResult(False, e)
            return result
        except SSHException as e:
            result = SshPollResult(False, e)
            return result
        except:
            result = SshPollResult(False, Exception("SSH: Other exception"))
            return result
