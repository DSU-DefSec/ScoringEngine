#!/usr/bin/python3
import sys
from datetime import datetime
from socketserver import TCPServer, BaseRequestHandler

class RevShellHandler(BaseRequestHandler):
    def handle(self):
        date = datetime.now().strftime('%y-%m-%d %H:%M:%S')
        with open(sys.argv[2], 'a') as f:
            f.write('{}|1\n'.format(date))

if __name__ == '__main__':
    with TCPServer(('0.0.0.0', int(sys.argv[1])), RevShellHandler) as server:
        server.serve_forever()
