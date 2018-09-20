#!/usr/bin/python3

from .web_model import WebModel
import flask
from flask import Flask, render_template, request, redirect, url_for
from urllib.parse import urlparse, urljoin
from .forms import *
from . import score
from .. import validate
import flask_login
from flask_login import LoginManager, login_user, logout_user, login_required
from .model import User, PasswordChangeRequest, PCRStatus
from .pcr_servicer import PCRServicer
from .decorators import *
import db
import re

app = Flask(__name__)
app.secret_key = 'this is a secret'

wm = WebModel()
wm.load_db()

login_manager = LoginManager()
login_manager.init_app(app)

pcr_servicer = PCRServicer(wm)
pcr_servicer.start()

@login_manager.user_loader
def load_user(user_id):
    if user_id not in wm.users:
        return None
    return wm.users[user_id]

def is_safe_url(target):
    ref_url = urlparse(flask.request.host_url)
    test_url = urlparse(urljoin(flask.request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

@app.route('/')
@app.route('/status')
def status():
    """
    Render the main status page.
    """
    teams = wm.teams
    checks = wm.checks
    results = wm.latest_results()
    teams.sort(key=lambda t: t.name)
    return render_template('status.html', teams=teams, checks=checks, results=results)

@app.route('/credentials', methods=['GET'])
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

@app.route('/pcr', methods=['GET', 'POST'])
@login_required
def pcr():
    """
    Render the password change request overview page.
    """
    user = flask_login.current_user
    if request.method == 'GET':
        if user.is_admin:
            where = 'status = %s'
            args = (int(PCRStatus.APPROVAL))
            orderby = None
        else:
            team_id = user.team.id
            where = 'team_id = %s'
            orderby = 'submitted DESC'
            args = (team_id)
        pcr_ids = db.get('pcr', ['id'], where=where, orderby=orderby, args=args)
        pcrs = [PasswordChangeRequest.load(pcr_id) for pcr_id in pcr_ids]
        domains = {d.id:d for d in wm.domains}
        services = {s.id:s for s in wm.services}
        return render_template('pcr_overview.html', pcrs=pcrs, services=services, domains=domains)
    elif request.method == 'POST':
        pcr_id = request.form['reqId']
        pcr = PasswordChangeRequest.load(pcr_id)
        if (not user.is_admin and user.team.id != pcr.team_id) or pcr.status == PCRStatus.COMPLETE:
            pass # Show error?
        else:
            pcr.delete()
        return redirect(url_for('pcr'))

@app.route('/pcr_details', methods=['GET', 'POST'])
@login_required
def pcr_details():
    """
    Render the password change request details page.
    """
    user = flask_login.current_user
    if request.method == 'GET':
        pcr_id = request.args.get('id')
        pcr = PasswordChangeRequest.load(pcr_id)
        domains = {d.id:d for d in wm.domains}
        services = {s.id:s for s in wm.services}
        if user.is_admin or user.team.id == pcr.team_id:
            return render_template('pcr_details.html', pcr=pcr, services=services, domains=domains)
        else:
            return redirect(url_for('pcr'))
    elif request.method == 'POST':
        pcr_id = request.form.get('reqId')
        pcr = PasswordChangeRequest.load(pcr_id)
        if user.is_admin:
            if request.form['approval'] == 'Approve':
                status = PCRStatus.PENDING
            else:
                status = PCRStatus.DENIED
            comment = request.form['admin_comment']
            pcr.set_status(status)
            pcr.set_admin_comment(comment)
        elif user.team.id == pcr.team_id:
            comment = request.form['team_comment']
            pcr.set_team_comment(comment)
        return redirect(url_for('pcr_details') + '?id={}'.format(pcr_id))

@app.route('/new_pcr', methods=['GET', 'POST'])
@login_required
def new_pcr():
    """
    Render the password change request form.
    """
    window = wm.settings['pcr_approval_window']
    pcr_id = 0
    form = PasswordChangeForm(wm)
    conflict = False
    success = False
    if request.method == 'POST':
        if form.validate_on_submit():
            success = True
            user = flask_login.current_user
            if user.is_admin:
                team_id = form.team.data
            else:
                team_id = user.team.id

            domain_id = form.domain.data
            service_id = form.service.data
            pwchange = form.pwchange.data

            pwchange = [line.split(':') for line in pwchange.split('\r\n')]
            creds = []
            for line in pwchange:
                if len(line) >= 2:
                    username = re.sub('\s+', '', line[0])
                    password = re.sub('\s+', '', ':'.join(line[1:]))
                    creds.append((username, password))
            pcr = PasswordChangeRequest(team_id, PCRStatus.PENDING, creds, service_id=service_id, domain_id=domain_id)
            conflict = pcr.conflicts(window)
            if conflict:
                pcr.set_status(PCRStatus.APPROVAL)
            pcr_id = pcr.id
    return render_template('pcr_new.html', form=form, window=window, pcr_id=pcr_id, success=success, conflict=conflict)

@app.route('/result_log', methods=['GET'])
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

@app.route('/competition', methods=['GET', 'POST'])
@login_required
@admin_required
def competition():
    """
    Render page with a button for starting and stopping the engine.
    """
    running = wm.settings['running']
    if request.method =='POST':
        if request.form['running'] == 'Start':
            running = True
        elif request.form['running'] == 'Stop':
            running = False
        wm.update_setting('running', running)
    return render_template('competition.html', running=running)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Render the user login page.
    """
    form = LoginForm(wm)
    error = None
    if request.method == 'POST':
        if form.validate_on_submit():
            user = load_user(form.username.data.lower())
            if user is not None: # Valid user
                login_user(user)
        
                flask.flash('Logged in successfully!')
        
                next = flask.request.args.get('next')
                if not is_safe_url(next): # Open redirect protection
                    return flask.abort(400)

                return redirect(next or flask.url_for('status'))
        else:
            error = "Invalid username/password"
    return render_template('login.html', form=form, error=error)

@app.route('/logout')
@login_required
def logout():
    """
    Log out the user and redirect them to the status page.
    """
    logout_user()
    return redirect(flask.url_for('status'))

@app.route('/password_reset', methods=['GET', 'POST'])
@login_required
def pw_reset():
    """
    Render a password reset form.
    """
    form = PasswordResetForm(wm)
    success = False
    if request.method == 'POST':
        if form.validate_on_submit():
            username = form.user.data
            if username == 'None':
                username = flask_login.current_user.name
            username = username.lower()
            
            wm.change_user_password(username, form.new_pw.data)
            success = True
    return render_template('pw_reset.html', success=success, form=form)

@app.route('/reporting/score', methods=['GET'])
@login_required
@admin_required
def score():
    """
    Score information page
    """
    results = wm.results
    simple_results = {}
    for team,tresults in results.items():
        simple_results[team] = {}
        for check,cresults in tresults.items():
            simple_results[team][check] = []
            for res in cresults:
                simple_results[team][check].append([res.time.strftime('%Y-%m-%d %H:%M:%S'), res.result])

    teams = {}
    for team in wm.teams:
        teams[team.id] = team.name
    checks = {}
    for check in wm.checks:
        checks[check.id] = check.name

    return render_template('score.html', results=simple_results, teams=teams, checks=checks)

@app.route('/reporting/default', methods=['GET'])
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

    return render_template('default.html', defaults=defaults, teams=teams)
