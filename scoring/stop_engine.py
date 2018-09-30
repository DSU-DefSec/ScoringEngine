#!/usr/bin/python3
import db

db.modify('settings', set='value=%s', where='skey=%s', args=(False, 'running'))
