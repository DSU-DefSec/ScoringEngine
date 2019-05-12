#!/usr/bin/python3
import db
import logging

log = logging.getLogger(__name__)
db.modify('settings', set='value=%s', where='skey=%s', args=(False, 'running'))
log.info("Stopped scoring engine.")
log.info("---------------------------------------------------")