#!/bin/python

from dm import DataManager
from flask import Flask
from flask import render_template
from flask import request
from functools import wraps

app = Flask(__name__)
dm = DataManager()

def local_only(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        print(request.remote_addr)
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
    return render_template('status.html', teams=teams, checks=checks, results=results)

@app.route('/scores')
def scores():
    dm.reload()
    teams = dm.teams
    scores = {1:0, 2:0}
    return render_template('scores.html', teams=teams, scores=scores)

@app.route('/credentials', methods=['GET'])
@local_only
def credentials():
    dm.reload()
    team_id = request.args.get('tid')
    team = next(filter(lambda t: t.id == int(team_id), dm.teams))
    credentials = [cred for cred in dm.credentials if cred.team.id == int(team_id)]
    credentials.sort(key= lambda c: (c.check_io.check.name, c.username))
    return render_template('credentials.html', credentials=credentials, team=team)

@app.route('/teams')
def teams():
    dm.reload()
    teams = dm.teams
    return render_template('teams.html', teams=teams)

@app.route('/services')
def services():
    dm.reload()
    services = dm.services
    return render_template('services.html', services=services)

@app.route('/checks')
def checks():
    pass

@app.route('/bulk_password')
def bulk_password():
    pass

@app.route('/result_log', methods=['GET'])
def result_log():
    dm.reload()
    team_id = request.args.get('tid')
    check_id = request.args.get('cid')
    results = dm.get_results(team_id, check_id)
    return render_template('result_log.html', results=results)

@app.route('/login')
def login():
    pass

@app.route('/logout')
def logout():
    pass
