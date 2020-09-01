from flask import render_template, request, Blueprint
from flask_login import login_required
from .decorators import admin_required
from . import wm

blueprint = Blueprint('status', __name__, url_prefix='')

@blueprint.route('/')
@blueprint.route('/status')
def status():
    """
    Render the main status page.
    """
    teams = wm.teams
    checks = wm.checks
    checks.sort(key=lambda c: c.name)
    results = wm.latest_results()
    teams.sort(key=lambda t: t.name)
    times = []
    for team_id,team_results in results.items():
        for check_id,result in team_results.items():
            times.append(result.time.strftime('%Y-%m-%d %I:%M %p'))
    if len(times) == 0:
        last_time = ''
    else:
        last_time = max(times)
    return render_template('status.html', teams=teams, checks=checks, results=results, last_time=last_time)

@blueprint.route('/credentials', methods=['GET'])
@login_required
@admin_required
def credentials():
    """
    Render a page showing all of the credentials for the team given by a GET parameter.
    """
    wm.reload_credentials()
    team_id = int(request.args.get('tid'))
    team = next(filter(lambda t: t.id == team_id, wm.teams))
    credentials = [cred for cred in wm.credentials if cred.team.id == team_id]
    credentials.sort(key= lambda c: (c.check_io.check.name, c.username))
    return render_template('credentials.html', credentials=credentials, team=team)

@blueprint.route('/result_log', methods=['GET'])
@login_required
@admin_required
def result_log():
    """
    Render the log of all of the checks for the team and check given by GET parameters.
    """
    wm.reload_credentials()
    wm.load_results()

    team_id = int(request.args.get('tid'))
    check_id = int(request.args.get('cid'))
    results = sorted(wm.results[team_id][check_id], key= lambda r: r.time, reverse=True)

    fname = ''
    return render_template('result_log.html', results=results, fname=fname)
