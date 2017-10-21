#!/usr/bin/python3

from dm import DataManager
from flask import Flask
from flask import render_template
from flask import request
from functools import wraps
import plot
import score
import validate

app = Flask(__name__)
dm = DataManager()

def local_only(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if request.remote_addr != '127.0.0.1':
            return "Access Denied"
        return f(*args, **kwargs)
    return wrapped

@app.route('/')
@app.route('/status')
def status():
    teams = dm.teams
    checks = dm.checks
    results = dm.latest_results()
    teams.sort(key=lambda t: t.name)
    return render_template('status.html', teams=teams, checks=checks, results=results)

@app.route('/scores')
@local_only
def scores():
    teams = dm.teams
    scores = {}
    sla_limit = dm.settings['sla_limit']
    sla_penalty = dm.settings['sla_penalty']
    max_score = dm.settings['max_score']
    for team in teams:
        scores[team.id] = score.calc_score(team.id, sla_limit,
                                           sla_penalty, max_score)
    return render_template('scores.html', teams=teams, scores=scores)

@app.route('/credentials', methods=['GET'])
#@local_only
def credentials():
    dm.reload_credentials()
    team_id = request.args.get('tid')
    team = next(filter(lambda t: t.id == int(team_id), dm.teams))
    credentials = [cred for cred in dm.credentials if cred.team.id == int(team_id)]
    credentials.sort(key= lambda c: (c.check_io.check.name, c.username))
    return render_template('credentials.html', credentials=credentials, team=team)

@app.route('/bulk', methods=['GET', 'POST'])
@local_only
def bulk():
    teams = dm.teams
    teams.sort(key=lambda t: t.name)
    services = dm.services
    services.sort(key=lambda s: (s.host, s.port))
    error = []
    if request.method == 'POST':
        team_id = int(request.form.get('team'))
        service_id = int(request.form.get('service'))
        pwchange = request.form.get('pwchange')
        if not validate.valid_team(team_id, dm.teams):
            error.append('Invalid Team')
        if not validate.valid_service(service_id, dm.services):
            error.append('Invalid Service')
        if not validate.valid_pwchange(pwchange):
            error.append('Invalid Password Change Format')
        dm.change_passwords(team_id, service_id, pwchange)
    return render_template('bulk.html', error=','.join(error), teams=teams, services=services)

@app.route('/result_log', methods=['GET'])
#@local_only
def result_log():
    dm.reload_credentials()
    dm.load_results()
    team_id = request.args.get('tid')
    check_id = request.args.get('cid')
    results = dm.results[team_id][check_id]
    fname = plot.plot_results(results)
    return render_template('result_log.html', results=results, fname=fname)

# TODO Implement
@app.route('/login')
@local_only
def login():
    pass

@app.route('/logout')
@local_only
def logout():
    pass

@app.route('/teams')
@local_only
def teams():
    pass

@app.route('/services')
@local_only
def services():
    pass

@app.route('/checks')
@local_only
def checks():
    pass
