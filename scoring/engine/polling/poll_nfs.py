from .poller import PollInput, PollResult, Poller
import os
import subprocess

class NfsPollInput(PollInput):

    def __init__(self, file=None, server=None):
        self.file = file
        super(NfsPollInput, self).__init__(server)


class NfsPollResult(PollResult):

    def __init__(self, output, exceptions=None):
        super(NfsPollResult, self).__init__(exceptions)
        self.output = output


class NfsPoller(Poller):
    def poll(self, poll_input):
        server = poll_input.server
        path = '/tmp/'+server
        file = poll_input.file
        try:
            if (not os.path.isdir(path)):
                os.mkdir(path)
            if (os.path.ismount(path)):
                subprocess.call(['umount','-f',path])
            subprocess.call(['mount','-t', 'nfs', server+':/',path])
            with open(path+file, 'r') as f:
                output = f.read()
            subprocess.call(['umount','-f',path])

            result = NfsPollResult(output)

            return result
        except Exception as e:
            result = NfsPollResult(False, exceptions=Exception(str(e)))
            return result
