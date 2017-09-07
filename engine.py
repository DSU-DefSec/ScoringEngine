from loader import Loader
from threading import Thread
import time

class ScoringEngine(object):

    def __init__(self):
        self.loader = Loader()

    def start(self):
        self.check()

    def check(self):
        self.loader.reload()
        for service in self.loader.services:
            service.check(self.loader.teams)

        
if __name__ == '__main__':
    engine = ScoringEngine()
    engine.start()
