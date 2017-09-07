#!/bin/python

from .loader import Loader
from flask import Flask
from flask import render_template
app = Flask(__name__)
loader = Loader()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def status():
    return render_template('scoreboard.html')

@app.route('/teams')
def teams():
    loader.reload()
    teams = loader.teams
    return render_template('teams.html', teams=teams)

@app.route('/services')
def services():
    loader.reload()
    services = loader.services
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

@app.route('/login')
def login():
    pass

@app.route('/logout')
def logout():
    pass
