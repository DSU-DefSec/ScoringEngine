from .engine_model import EngineModel
from threading import Thread
import db
import time, datetime
import random

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
                return

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

        check_round = db.execute('INSERT INTO check_log () VALUES ()')
        for vapp in self.em.vapps:
            for system in vapp.systems:
                if self.team_num is None:
                    system.check(check_round, self.em.teams)
                else:
                    system.check(check_round, [self.em.teams[self.team_num]])

    def log_default_creds(self):
        cmd = ('INSERT INTO default_creds_log (team_id, perc_default) '
                'SELECT team_id,AVG(is_default) FROM credential GROUP BY team_id')
        db.execute(cmd)

