from web.web_model import WebModel
wm = WebModel()
wm.load_db()

from . import auth, reports, status, sla, pcr, systems
blueprints = [
    auth.blueprint,
    reports.blueprint,
    status.blueprint,
    sla.blueprint,
    pcr.blueprint,
    systems.blueprint,
]
