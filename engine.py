#!/usr/bin/python3
from dm import DataManager
from threading import Thread
import time, datetime
import random
import sys

class ScoringEngine(object):

    def __init__(self, team_num=None):
        self.dm = DataManager()
        self.dm.teams.sort(key=lambda t: t.name)
        self.team_num = team_num

    def start(self):
        self.check()

    def check(self):
        start = time.monotonic()
        while True:
            print("New Round of Checks")
            self.dm.reload_credentials()

            current = time.monotonic()
            print(datetime.timedelta(seconds=current - start))
            if (current - start) > self.dm.settings["comp_length"]:
                break
 
            for service in self.dm.services:
                if self.team_num is None:
                    service.check(self.dm.teams)
                else:
                    service.check([self.dm.teams[team_num]])

            wait = self.dm.settings["interval"]
            print("Interval: " + str(wait))
            jitter = random.randint(-self.dm.settings["jitter"],
                                    self.dm.settings["jitter"])
            print("Jitter: " + str(jitter))
            wait += jitter
            print("Wait: " + str(wait))
            time.sleep(wait)
        print("Competition End")

        
if __name__ == '__main__':
    if len(sys.argv) > 1:
        print("Usage: ./engine [team_number]")
    if len(sys.argv) == 0:
        engine = ScoringEngine()
    if len(sys.argv) == 1:
        team_num = int(sys.argv[1])
        engine = ScoringEngine(team_num)
    engine.start()
