#!/usr/bin/python3
from engine.engine import ScoringEngine
from engine.file_manager import FileManager
import db
import sys
from threading import Thread

if __name__ == '__main__':
    if len(sys.argv) > 3:
        print("Usage: ./engine [start|stop] [team_number]")
    if len(sys.argv) == 2:
        engine = ScoringEngine()
    if len(sys.argv) == 3:
        team_num = int(sys.argv[2]) - 1
        engine = ScoringEngine(team_num)
    
    if sys.argv[1] == 'start':
        file_manager = FileManager()
        file_manager_thread = Thread(target=file_manager.manage_files)
        file_manager_thread.start()

        db.modify('settings', set='value=%s', where='skey=%s', args=(True, 'running'))
        engine.start()
    elif sys.argv[1] == 'stop':
        db.modify('settings', set='value=%s', where='skey=%s', args=(False, 'running'))
    else:
        print("Usage: ./engine [start|stop] [team_number]")

