from datetime import datetime
import random
import string
import os
from .poller import Poller

REF_PAGES_DIR = 'checkfiles'

class FilePoller(Poller):

    def get_extension(self, path):
        """
        Determines the file extesion of the given path. Returns 'txt' if there is none.

        Arguments:
            path (str): File path
        
        Returns:
            str: The file extension or 'txt' if there is none
        """
        pieces = path.split('.')
        if len(pieces) > 1:
            return pieces[-1]
        else:
            return 'txt'

    def open_file(self, extension):
        """
        Open a file with timestamp and random name of the format day-hour:minute:second.random with the given extension.

        Arguments:
            extension (str): The file extension
 
        Returns:
            file: The created file
        """
        time = datetime.now().strftime('%d-%H:%M:%S')
        while True:
            rand = ''.join([random.choice(string.ascii_letters) for i in range(10)])
            fname = '{}/{}.{}.{}'.format(REF_PAGES_DIR, time, rand, extension)
            if not os.path.exists(fname):
                break
        f = open(fname, 'wb')
        return f
