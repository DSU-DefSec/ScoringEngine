from flask import render_template, Blueprint
from flask_login import login_required
import db
from . import wm

blueprint = Blueprint('sla', __name__, '/sla')

def get_team_slas(team_id):
    results = db.get('result', ['time', 'check_id', 'result'], where='team_id=%s', orderby='time ASC', args=(team_id,))
    down_counts = {}
    slas = []
    for time, check_id, result in results:
        if not check_id in down_counts:
            down_counts[check_id] = 0
        if not result:
            down_counts[check_id] += 1
        else:
            down_counts[check_id] = 0
        if down_counts[check_id] >= 6:
            down_counts[check_id] = 0
            slas.append((time, check_id))
    return slas

def get_slas():
    slas = {}
    for team in wm.teams:
        slas[team.id] = get_team_slas(team.id)
    return slas

@blueprint.route('/log', methods=['GET'])
@login_required
def sla_log():
    slas = get_slas()

    cs = {}
    for check in wm.checks:
        cs[check.id] = check

    return render_template('sla/sla_log.html', slas=slas, checks=cs)

@blueprint.route('/totals', methods=['GET'])
@login_required
def sla_totals():
    cs = {}
    for check in wm.checks:
        cs[check.id] = check

    slas = get_slas()
    totals = {}
    for team in wm.teams:
        totals[team.id] = {}
        for check in wm.checks:
            totals[team.id][check.id] = 0

    for team in wm.teams:
        for time, check_id in slas[team.id]:
            totals[team.id][check_id] += 1

    return render_template('sla/sla_totals.html', totals=totals, checks=cs)
