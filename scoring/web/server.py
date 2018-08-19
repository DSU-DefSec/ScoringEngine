#!/usr/bin/python3

from .web_model import WebModel
import flask
from flask import Flask, render_template, request, redirect, url_for
from urllib.parse import urlparse, urljoin
from .forms import *
#from . import plot
from . import score
from .. import validate
import flask_login
from flask_login import LoginManager, login_user, logout_user, login_required
from .model import User, PasswordChangeRequest, PCRStatus
from .decorators import *
import db

app = Flask(__name__)
app.secret_key = 'this is a secret'

wm = WebModel()
wm.load_db()

login_manager = LoginManager()
login_manager.init_app(app)

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

@app.route('/scores')
@login_required
@admin_required
def scores():
    """
    Render a page showing scores for each team.
    """
    teams = wm.teams
    checks = wm.checks
    team_ids = [t.id for t in teams]
    check_ids = [c.id for c in checks]
    results = score.get_results_list(team_ids, check_ids)
    uptime = score.uptime(results)
    return render_template('scores.html', teams=teams, checks=checks, uptime=uptime, results=results, team_ids=team_ids, check_ids=check_ids)

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
        else:
            team_id = user.team.id
            where = 'team_id = %s'
            args = (team_id)
        pcr_ids = db.get('pcr', ['id'], where=where, args=args)
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
        print(request.form)
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
        return redirect(url_for('pcr'))

@app.route('/new-pcr', methods=['GET', 'POST'])
@login_required
def new_pcr():
    """
    Render the password change request form.
    """
    form = PasswordChangeForm(wm)
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

            wm.change_passwords(team_id, domain_id, service_id, pwchange)
            success = True
    return render_template('pcr_new.html', form=form, success=success)

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

#    fname = plot.plot_results(results) # Results plot
    fname = ''
    print([r.check_io.expected for r in results])
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
