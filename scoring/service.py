#!/usr/bin/python3
from web.pcr_servicer import PCRServicer
from web.web_model import WebModel
wm = WebModel()
wm.load_db()

pcr = PCRServicer(wm)
pcr.start()

