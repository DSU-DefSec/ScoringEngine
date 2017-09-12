#!/bin/python

from dm import DataManager
from flask import Flask
from flask import render_template
from flask import request
app = Flask(__name__)
dm = DataManager()

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

@app.route('/credentials')
def credentials():
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
