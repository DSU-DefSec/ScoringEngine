#!/bin/python

from dm import DataManager
from flask import Flask
from flask import render_template
from flask import request
from functools import wraps
import plot

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
    dm.reload()
    teams = dm.teams
    checks = dm.checks
    results = dm.latest_results()
    teams.sort(key=lambda t: t.name)
    return render_template('status.html', teams=teams, checks=checks, results=results)

@app.route('/scores')
@local_only
def scores():
    dm.reload()
    teams = dm.teams
    scores = {}
    for team in teams:
        scores[team.id] = dm.calc_score(team.id)
    return render_template('scores.html', teams=teams, scores=scores)

@app.route('/credentials', methods=['GET'])
#@local_only
def credentials():
    dm.reload()
    team_id = request.args.get('tid')
    team = next(filter(lambda t: t.id == int(team_id), dm.teams))
    credentials = [cred for cred in dm.credentials if cred.team.id == int(team_id)]
    credentials.sort(key= lambda c: (c.check_io.check.name, c.username))
    return render_template('credentials.html', credentials=credentials, team=team)

@app.route('/teams')
@local_only
def teams():
    dm.reload()
    teams = dm.teams
    return render_template('teams.html', teams=teams)

@app.route('/services')
@local_only
def services():
    dm.reload()
    services = dm.services
    return render_template('services.html', services=services)

@app.route('/checks')
@local_only
def checks():
    pass

@app.route('/bulk', methods=['GET', 'POST'])
@local_only
def bulk():
    dm.reload()
    teams = dm.teams
    teams.sort(key=lambda t: t.name)
    services = dm.services
    services.sort(key=lambda s: (s.host, s.port))
    error = []
    if request.method == 'POST':
        team_id = int(request.form.get('team'))
        service_id = int(request.form.get('service'))
        pwchange = request.form.get('pwchange')
        if not dm.valid_team(team_id):
            error.append('Invalid Team')
        if not dm.valid_service(service_id):
            error.append('Invalid Service')
        if not dm.valid_pwchange(pwchange):
            error.append('Invalid Password Change Format')
        dm.change_passwords(team_id, service_id, pwchange)
    return render_template('bulk.html', error=','.join(error), teams=teams, services=services)
        

@app.route('/result_log', methods=['GET'])
#@local_only
def result_log():
    dm.reload()
    team_id = request.args.get('tid')
    check_id = request.args.get('cid')
    results = dm.get_results(team_id, check_id)
    fname = plot.plot_results(results)
    return render_template('result_log.html', results=results, fname=fname)

@app.route('/login')
@local_only
def login():
    pass

@app.route('/logout')
@local_only
def logout():
    pass
