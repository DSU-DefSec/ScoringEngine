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
        running = int(db.get('settings', ['value'], where='skey=%s', args=['running'])[0][0])
        while running:
            self.deduplicate_files()
#            self.push_files()
            time.sleep(5)
            running = int(db.get('settings', ['value'], where='skey=%s', args=['running'])[0][0])

    def get_files(self):
        paths = []
        for dir_part, dirs, files in os.walk(CHECK_FILES_PATH):
            if dir_part != EXPECTED_FILES_PATH:
                for file in files:
                    if file[0] != '.':
                        path = os.path.join(dir_part, file)
                        if not os.path.islink(path):
                            paths.append(path)
        return paths

    def update_hashes(self, paths):
        for path in paths:
            if path not in self.hashes: 
                m = hashlib.sha1()
                with open(path, 'rb') as f:
                    m.update(f.read())
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
