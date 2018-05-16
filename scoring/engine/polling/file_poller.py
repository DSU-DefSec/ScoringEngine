from datetime import datetime
import random
import string
import os
from .poller import Poller

REF_PAGES_DIR = 'checkfiles'

class FilePoller(Poller):

    def open_file(self):
        """
        Open a file with timestamp and random name of the format day-hour:minute:second.random
 
        Returns:
            file: The created file
        """
        time = datetime.now().strftime('%d-%H:%M:%S')
        while True:
            rand = ''.join([random.choice(string.ascii_letters) for i in range(10)])
            fname = '{}/{}.{}'.format(REF_PAGES_DIR, time, rand)
            if not os.path.exists(fname):
                break
        f = open(fname, 'wb')
        return f
