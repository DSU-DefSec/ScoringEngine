from dm import DataManager
from threading import Thread
import time

class ScoringEngine(object):

    def __init__(self):
        self.dm = DataManager()

    def start(self):
        self.check()

    def check(self):
        self.dm.reload()
        for service in self.dm.services:
            service.check(self.dm.teams)

        
if __name__ == '__main__':
    engine = ScoringEngine()
    engine.start()
