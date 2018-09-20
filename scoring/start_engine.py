#!/usr/bin/python3
from engine.engine_model import EngineModel
from engine.file_manager import FileManager
from threading import Thread
import db
import time, datetime
import random
import sys

class ScoringEngine(object):

    def __init__(self, team_num=None):
        self.em = EngineModel()
        self.em.load_db()
        self.em.teams.sort(key=lambda t: t.name)
        self.team_num = team_num

    def start(self):
        while True:
            self.em.load_settings()
            running = self.em.settings['running']
            interval = self.em.settings['interval']
            jitter = self.em.settings['jitter']

            if running:
                self.log_default_creds()
                self.check()
            else:
                print("Stopped")

            wait = interval
            print("Interval: " + str(wait))
            offset = random.randint(-jitter, jitter)
            print("Jitter: " + str(offset))
            wait += offset
            print("Wait: " + str(wait))
            time.sleep(wait)

    def check(self):
        print("New Round of Checks")
        self.em.reload_credentials()
        for service in self.em.services:
            if self.team_num is None:
                service.check(self.em.teams)
            else:
                service.check([self.em.teams[self.team_num]])

    def log_default_creds(self):
        cmd = ('INSERT INTO default_creds_log (team_id, perc_default) '
                'SELECT team_id,AVG(is_default) FROM credential GROUP BY team_id')
        db.execute(cmd)


if __name__ == '__main__':
    if len(sys.argv) > 2:
        print("Usage: ./engine [team_number]")
    if len(sys.argv) == 1:
        engine = ScoringEngine()
    if len(sys.argv) == 2:
        team_num = int(sys.argv[1]) - 1
        engine = ScoringEngine(team_num)

    file_manager = FileManager()
    file_manager_thread = Thread(target=file_manager.manage_files)
    file_manager_thread.start()

    engine.start()
