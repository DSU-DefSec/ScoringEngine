import time
import os
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
            time.sleep(60)

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
        master_parts = master.split('/')
        file_parts = file.split('/')
        rel_master_parts = []
        i = 0
        while i < len(file_parts) - 1:
            if master_parts[i] != file_parts[i]:
                break
            i += 1
        while i < len(file_parts) - 1:
            rel_master_parts.append('..')
            i += 1
        rel_master_parts.append(master_parts[-1])
        rel_master = '/'.join(rel_master_parts)
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
        pass
