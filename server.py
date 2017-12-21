#!/usr/bin/python3

from dm import DataManager
from forms import *
import flask
from flask import Flask, render_template, request, redirect
from urllib.parse import urlparse, urljoin
from functools import wraps
import plot
import score
import validate
import flask_login
from flask_login import LoginManager, login_user, logout_user, login_required
from web_model import User

app = Flask(__name__)
app.secret_key = 'this is a secret'

dm = DataManager()
dm.load_db()

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    if user_id not in dm.users:
        return None
    return dm.users[user_id]

def is_safe_url(target):
    ref_url = urlparse(flask.request.host_url)
    test_url = urlparse(urljoin(flask.request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not flask_login.current_user.is_admin:
            return "Access Denied"
        return f(*args, **kwargs)
    return wrapped

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
@login_required
@admin_required
def scores():
    teams = dm.teams
    scores = {}
    sla_limit = 0
    sla_penalty = 0
    max_score = 0
    for team in teams:
        scores[team.id] = score.calc_score(team.id, sla_limit,
                                           sla_penalty, max_score)
    return render_template('scores.html', teams=teams, scores=scores)

@app.route('/credentials', methods=['GET'])
@login_required
@admin_required
def credentials():
    dm.reload_credentials()
    team_id = request.args.get('tid')
    team = next(filter(lambda t: t.id == int(team_id), dm.teams))
    credentials = [cred for cred in dm.credentials if cred.team.id == int(team_id)]
    credentials.sort(key= lambda c: (c.check_io.check.name, c.username))
    return render_template('credentials.html', credentials=credentials, team=team)

@app.route('/bulk', methods=['GET', 'POST'])
@login_required
def bulk():
    form = PasswordChangeForm(dm)
    success = False
    if request.method == 'POST':
        if form.validate_on_submit():
            user = flask_login.current_user

            if user.is_admin:
                team_id = form.team.data
            else:
                team_id = user.team.id
            domain_id = form.domain.data
            service_id = form.service.data
            pwchange = form.pwchange.data

            dm.change_passwords(team_id, domain_id, service_id, pwchange)
            success = True
    return render_template('bulk.html', form=form, success=success)

@app.route('/result_log', methods=['GET'])
@login_required
@admin_required
def result_log():
    dm.reload_credentials()
    dm.load_results()
    team_id = int(request.args.get('tid'))
    check_id = int(request.args.get('cid'))
    results = sorted(dm.results[team_id][check_id], key= lambda r: r.time, reverse=True)
    fname = plot.plot_results(results)
    return render_template('result_log.html', results=results, fname=fname)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(dm)
    error = None
    if request.method == 'POST':
        if form.validate_on_submit():
            user = load_user(form.username.data.lower())
            if user is not None: 
                login_user(user)
        
                flask.flash('Logged in successfully!')
        
                next = flask.request.args.get('next')
                if not is_safe_url(next):
                    return flask.abort(400)
                return redirect(next or flask.url_for('status'))
        else:
            error = "Invalid username/password"
    return render_template('login.html', form=form, error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(flask.url_for('status'))
