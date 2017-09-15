#!/usr/bin/env python3
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
        while True:
            self.dm.reload()
            for service in self.dm.services:
                service.check(self.dm.teams)
            wait = self.dm.interval + random.randint(-self.dm.jitter,
                                                     self.dm.jitter)
            time.sleep(wait)

        
if __name__ == '__main__':
    engine = ScoringEngine()
    engine.start()
