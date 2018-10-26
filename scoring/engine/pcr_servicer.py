from threading import Thread
import random
import datetime
import time
import db
from .model import PasswordChangeRequest, PCRStatus

class PCRServicer(object):

    def __init__(self, em):
        self.window = em.settings['pcr_service_window']
        self.jitter = em.settings['pcr_service_jitter']

    def start(self):
        thread = Thread(target=self.service_requests)
        thread.start()

    def service_requests(self):
        while True:
            pcr_ids = db.get('pcr', ['id'], 'status = %s', args=[int(PCRStatus.PENDING)])
            pcrs = [PasswordChangeRequest.load(pcr_id) for pcr_id in pcr_ids]
            window = self.window + random.uniform(-self.jitter, self.jitter)
            window = datetime.timedelta(minutes=window)
            for pcr in pcrs:
                if datetime.datetime.now() >= pcr.submitted + window:
                    pcr.service_request()
            time.sleep(30)
