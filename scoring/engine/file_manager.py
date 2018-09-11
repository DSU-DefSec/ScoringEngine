import db
import time
import os
import subprocess
import hashlib

CHECK_FILES_PATH = 'checkfiles'
EXPECTED_FILES_PATH = 'checkfiles/expected'

class FileManager(object):
    def __init__(self):
        self.files = []
        self.hashes = {}
        self.master_files = {}

    def manage_files(self):
        while True:
            self.deduplicate_files()
            self.push_files()
            time.sleep(5)

    def get_files(self):
        paths = []
        for dir_part, dirs, files in os.walk(CHECK_FILES_PATH):
            for file in files:
                if file[0] != '.':
                    path = os.path.join(dir_part, file)
                    if not os.path.islink(path):
                        paths.append(path)
        return paths

    def update_hashes(self, paths):
        for path in paths:
            if path not in self.hashes: 
                f = open(path, 'rb')
                m = hashlib.sha1()
                m.update(f.read())
                f.close()
                hash = m.hexdigest()
                self.hashes[path] = hash
                if hash not in self.master_files:
                    self.master_files[hash] = path
                
    def relative_path(self, master, file):
        file_dir = os.path.dirname(file)
        rel_master = os.path.relpath(master, file_dir)
        return rel_master
    
    def deduplicate_files(self):
        files = self.get_files()
        self.update_hashes(files)
        for file in files:
            hash = self.hashes[file]
            master = self.master_files[hash]
            if master != file:
                rel_path = self.relative_path(master, file)
                os.remove(file)
                os.symlink(rel_path, file)
    
    def push_files(self):
        webserver_ip = db.get('settings', ['value'], where='skey=%s', args=['webserver_ip'])[0][0]
        remote = 'rsync://%s/checkfiles' % webserver_ip
        local_files = os.listdir(CHECK_FILES_PATH)
        for local_file in local_files:
            local_file = '%s/%s' % (CHECK_FILES_PATH, local_file)
            subprocess.call(['rsync', '-rl', local_file, remote])
