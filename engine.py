#!/usr/bin/env python
from dm import DataManager
from threading import Thread
import time
import random

class ScoringEngine(object):

    def __init__(self):
        self.dm = DataManager()

    def start(self):
        self.check()

    def check(self):
        checks = 0
        while True:
            self.dm.reload()
            for service in self.dm.services:
                service.check(self.dm.teams)
            wait = self.dm.interval + random.randint(-self.dm.jitter,
                                                     self.dm.jitter)
            time.sleep(wait)
            checks += 1
            if checks == 5:
                break

        
if __name__ == '__main__':
    engine = ScoringEngine()
    engine.start()
