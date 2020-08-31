from flask import render_template, request, Blueprint
import datetime
from flask_login import current_user, login_required
from .decorators import admin_required
import db
from . import wm

def init(web_model, app):
    """
    Initialize the module with necessary data

    Arguments:
        web_model (WebModel): The web model
    """
    global wm
    wm = web_model

blueprint = Blueprint('reporting', __name__, url_prefix='/reporting')

@blueprint.route('/score', methods=['GET'])
@login_required
@admin_required
def score():
    """
    Score information page
    """
    start = request.args.get('start')
    end = request.args.get('end')
    today = datetime.datetime.today()
    if start == '':
        start = None
    if end == '':
        end = None
    if not start is None:
        start = datetime.datetime.strptime(start, '%H:%M')
        start = start.replace(year=today.year, month=today.month, day=today.day)
    if not end is None:
        end = datetime.datetime.strptime(end, '%H:%M')
        end = end.replace(year=today.year, month=today.month, day=today.day)

    wm.load_results()
    results = wm.results
    simple_results = {}
    for team,tresults in results.items():
        simple_results[team] = {}
        for check,cresults in tresults.items():
            simple_results[team][check] = []
            for res in cresults:
                if (start is None or res.time >= start) and (end is None or res.time <= end):
                    simple_results[team][check].append([res.time.strftime('%Y-%m-%d %H:%M:%S'), res.result])

    teams = {}
    for team in wm.teams:
        teams[team.id] = team.name
    checks = {}
    for check in wm.checks:
        checks[check.id] = check.name

    systems = wm.systems
    reverts = wm.get_reverts()

    return render_template('reports/score.html', results=simple_results, teams=teams, checks=checks, systems=systems, reverts=reverts)

@blueprint.route('/default', methods=['GET'])
@login_required
@admin_required
def default():
    """
    Default passwords information page.
    """
    teams = {}
    for team in wm.teams:
        teams[team.id] = team.name

    defaults = {}
    for team_id in teams.keys():
        res = db.get('default_creds_log', ['time', 'perc_default'], where='team_id=%s', args=(team_id,))
        res = list(res)
        for i in range(len(res)):
            res[i] = [res[i][0].strftime('%Y-%m-%d %H:%M:%S'), res[i][1]*100]
        defaults[team_id] = res

    return render_template('reports/default.html', defaults=defaults, teams=teams)

@blueprint.route('/revert_log', methods=['GET'])
@login_required
def revert_log():
    teams = {}
    for team in wm.teams:
        teams[team.id] = team.name

    if current_user.name == 'admin':
        reverts = db.getall('revert_log', orderby='time DESC')
    else:
        reverts = db.get('revert_log', ['*'], where='team_id=%s', orderby='time DESC', args=(current_user.team.id,))
    return render_template('reports/revert_log.html', teams=teams, reverts=reverts)
