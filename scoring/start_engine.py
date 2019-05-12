#!/usr/bin/python3
from engine.engine_model import EngineModel
from engine.file_manager import FileManager
from threading import Thread
import db
import time, datetime
from time import sleep
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

            wait = interval
            offset = random.randint(-jitter, jitter)
            wait += offset

            if running:
                self.log_default_creds()
                self.log_score()
                self.check()
                 # Calculate SLAs only after all checks are done
                sla_calculator = Thread(target=self.calc_sla(wait))
                sla_calculator.start()
            else:
                print("Stopped")
                return

            print("Default Interval: " + str(wait))
            print("Jitter (delay): " + str(offset))
            print("Wait Until Next Check: " + str(wait))
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

    def log_score(self):
        rows = db.getall('team')
        for team_id, name, team_num, service_points, sla_violations, inject_points, redteam_points, ir_points in rows:
            db.insert('score_log', ['team_id', 'service_points', 'sla_violations', 'inject_points', 'redteam_points', 'ir_points'], (team_id, service_points, sla_violations, inject_points, redteam_points, ir_points,))

    def calc_sla(self, wait):
        sleep(wait)
        down_counts = {}
        slas = {}
        for team in self.em.teams:
            results = db.get('result', ['time', 'check_id', 'result'], where='team_id=%s', orderby='time ASC', args=(team.id,))
            sla_counter = 0
            for time, check_id, result in results:
                if not check_id in down_counts:
                    down_counts[check_id] = 0
                if not result:
                    down_counts[check_id] += 1
                else:
                    down_counts[check_id] = 0
                if down_counts[check_id] >= 6:
                    down_counts[check_id] = 0
                    sla_counter += 1

            db.modify('team', 'sla_violations=%s', (str(sla_counter * 20), str(team.id)), where='id=%s') # loss of 20 points per sla violation
        return slas


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

    db.modify('settings', set='value=%s', where='skey=%s', args=(True, 'running'))
    engine.start()
