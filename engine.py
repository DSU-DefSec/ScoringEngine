#!/usr/bin/python3
from dm import DataManager
from threading import Thread
import time, datetime
import random
import sys

class ScoringEngine(object):

    def __init__(self, team_num=None):
        self.dm = DataManager()
        self.dm.load_db()
        self.dm.teams.sort(key=lambda t: t.name)
        self.team_num = team_num

    def start(self):
        while True:
            self.dm.load_settings()
            running = self.dm.settings['running']
            interval = self.dm.settings['interval']
            jitter = self.dm.settings['jitter']

            if running:
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
        self.dm.reload_credentials()
        for service in self.dm.services:
            if self.team_num is None:
                service.check(self.dm.teams)
            else:
                service.check([self.dm.teams[self.team_num]])


if __name__ == '__main__':
    if len(sys.argv) > 2:
        print("Usage: ./engine [team_number]")
    if len(sys.argv) == 1:
        engine = ScoringEngine()
    if len(sys.argv) == 2:
        team_num = int(sys.argv[1]) - 1
        engine = ScoringEngine(team_num)
    engine.start()
