#!/usr/bin/python3

# Flask and system imports
import flask
from flask import Flask, render_template, request, redirect, url_for
import flask_login
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from urllib.parse import urlparse, urljoin
import datetime

# Custom imports
from engine.model import PasswordChangeRequest, RedTeamReport, REQStatus
from .web_model import WebModel
from .model import User
from .decorators import *
from .forms import *
from . import score
import validate
import ialab
import db
import re

app = Flask(__name__)
app.secret_key = 'this is a secret'

wm = WebModel()
wm.load_db()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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
@deny_redteam
def pcr():
    """
    Render the password change request overview page.
    """
    user = flask_login.current_user
    if request.method == 'GET':
        if user.is_admin:
            orderby = 'submitted DESC'
            pcr_ids = db.get('pcr', ['id'], orderby=orderby)
            pcrs = [PasswordChangeRequest.load(pcr_id) for pcr_id in pcr_ids ]
            for pcr in pcrs:
                where = 'id = ' + str(pcr.team_id)
                pcr.team_num = db.get('team', ['team_num'], where=where)
            domains = {d.id:d for d in wm.domains}
            checks = {c.id:c for c in wm.checks}
            return render_template('pcr_overview.html', pcrs=pcrs, checks=checks, domains=domains)
        else:
            team_id = user.team.id
            where = 'team_id = %s'
            orderby = 'submitted DESC'
            args = (team_id)
            pcr_ids = db.get('pcr', ['id'], where=where, orderby=orderby, args=args)
            pcrs = [PasswordChangeRequest.load(pcr_id) for pcr_id in pcr_ids]
            domains = {d.id:d for d in wm.domains}
            checks = {c.id:c for c in wm.checks}
            return render_template('pcr_overview.html', pcrs=pcrs, checks=checks, domains=domains)
    elif request.method == 'POST':
        pcr_id = request.form['reqId']
        pcr = PasswordChangeRequest.load(pcr_id)
        if (not user.is_admin and user.team.id != pcr.team_id) or pcr.status == REQStatus.COMPLETE:
            pass # Show error?
        else:
            pcr.delete()
        return redirect(url_for('pcr'))

@app.route('/pcr_details')
@login_required
@deny_redteam
def pcr_details():
    """
    Render the password change request details page.
    """
    user = flask_login.current_user
    pcr_id = request.args.get('id')
    pcr = PasswordChangeRequest.load(pcr_id)
    domains = {d.id:d for d in wm.domains}
    checks = {c.id:c for c in wm.checks}
    if user.is_admin or user.team.id == pcr.team_id:
        return render_template('pcr_details.html', pcr=pcr, checks=checks, domains=domains)
    else:
        return redirect(url_for('pcr'))
    

@app.route('/new_pcr', methods=['GET', 'POST'])
@login_required
@deny_redteam
def new_pcr():
    """
    Render the password change request form.
    """
    pcr_id = 0
    form = PasswordChangeForm(wm)
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
            check_id = form.check.data
            pwchange = form.pwchange.data

            pwchange = [line.split(':') for line in pwchange.split('\r\n')]
            creds = []
            for line in pwchange:
                if len(line) >= 2:
                    username = re.sub('\s+', '', line[0])
                    password = re.sub('\s+', '', ':'.join(line[1:]))
                    creds.append((username, password))
            pcr = PasswordChangeRequest(team_id, int(REQStatus.PENDING), creds, check_id=check_id, domain_id=domain_id)
            pcr.service_request()            
            return redirect(url_for('pcr'))
    return render_template('pcr_new.html', form=form, pcr_id=pcr_id, success=success)

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
@redorwhite_required
def score():
    """
    Score information page
    """
  
    # tests n stuff
    megastring = ''

    rows = db.getall('team')
    for team_id, name, team_num, service_points, sla_violations, inject_points, redteam_points, ir_points in rows:
        megastring += '<br><strong>Team ' + str(team_num) + ':</strong><br><br>'
        megastring += '<i>Service points gained:</i> ' + str(service_points) + '<br>'
        megastring += '<i>SLA violation points lost:</i> ' + str(sla_violations) + '<br>'
        megastring += '<i>Inject points gained:</i> ' + str(inject_points) + '<br>'
        megastring += '<i>Red team points lost:</i> ' + str(redteam_points) + '<br>'
        megastring += '<i>Incident report points gained:</i> ' + str(ir_points) + '<br><br>'
        megastring += '    TOTAL SCORE: ' + str((service_points + inject_points) - (sla_violations + (redteam_points - ir_points))) + '<br>'

    return megastring

    # sorry to nic's code below
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

    return render_template('score.html', results=simple_results, teams=teams, checks=checks, systems=systems, reverts=reverts)


@app.route('/reporting/default', methods=['GET'])
@login_required
@redorwhite_required
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

@app.route('/reporting/all', methods=['GET'])
@login_required
@redorwhite_required
def score_all(): # TODO
    """
    Scoring information for every score factor for each team.
    """
    # add get input validation for tid
    teams = {}
    #for team in wm.teams:
    #    teams[team.id] = team.name

    # add teams selector above. for now, just team 1

    #team_id = int(request.args.get('tid'))
    team_id=1    
    defaults = {}
    #for team_id in teams.keys():
    # for now, just sla violations
    teams[1] = 'Team1'

    res = db.get('score_log', ['time', 'sla_violations'], where='team_id=%s', args=(team_id,))
    res = list(res)
    for i in range(len(res)):
        res[i] = [res[i][0].strftime('%Y-%m-%d %H:%M:%S'), res[i][1]]
    defaults[team_id] = res

    return render_template('score_all.html', defaults=defaults, teams=teams)

@app.route('/systems', methods=['GET', 'POST'])
@login_required
def systems():
    """
    Page for powering on, powering off, restarting, and reverting systems.
    """
    errors = None
    if request.method == 'POST':
        tid = current_user.team.id
        system = request.form['system']
        action = request.form['action']
        team = [t for t in wm.teams if t.id == tid][0]
        system = [s for s in wm.systems if s.name == system][0]
        vapp = system.vapp.base_name
        vapp = '{}_{}'.format(team.name, vapp)
        print(vapp, system.name)

        if request.form['action'] == 'power on':
            errors = ialab.power_on(vapp, system.name)
        elif request.form['action'] == 'power off':
            errors = ialab.power_off(vapp, system.name)
        elif request.form['action'] == 'restart':
            errors = ialab.restart(vapp, system.name)
        elif request.form['action'] == 'revert':
            errors = ialab.revert(vapp, system.name)
            if errors == '':
                db.insert('revert_log', ['team_id', 'system'], [tid, system.name])
    systems = wm.systems
    return render_template('systems.html', systems=systems, penalty=wm.settings['revert_penalty'], errors=errors)

@app.route('/rtr', methods=['GET', 'POST'])
@login_required
@redteam_required
def rtr():
    """
    Page for red team to claim access on systems.
    """
    systems = wm.systems
    return render_template('rtr_systems.html', systems=systems)
    
@app.route('/rtr_overview', methods=['GET', 'POST'])
@login_required
@redorwhite_required
def rtr_overview():
    """
    Render the password change request overview page.
    """
    user = flask_login.current_user
    if request.method == 'GET':
        orderby = 'submitted DESC'
        rtr_ids = db.get('rtr', ['id'], orderby=orderby)
        rtrs = [RedTeamReport.load(rtr_id) for rtr_id in rtr_ids ]
        for rtr in rtrs:
            where = 'id = ' + str(rtr.team_id)
            rtr.team_num = db.get('team', ['team_num'], where=where)

        return render_template('rtr_overview.html', rtrs=rtrs)
     
    elif request.method == 'POST':
        rtr_id = request.form['reqId']
        rtr = RedTeamReport.load(rtr_id)
        if user.is_admin:
            return render_template('access_denied.html')
        else:
            rtr.delete()
        return redirect(url_for('rtr'))

@app.route('/rtr_submit', methods=['GET', 'POST'])
@login_required
@redteam_required
def rtr_submit():
    """
    Form for red team to claim access on systems.
    """    
    rtr_id = 0
    success = False
    if 'system_id' in request.args:    
        system_id = request.args['system_id']
    elif 'system_id' in request.form:
        system_id = request.form['system_id']
    form = RedTeamActionReportForm(wm)
    if request.method == 'POST':
        if form.validate_on_submit():
            success = True
            team_id = form.team.data
            btype = form.btype.data
            if btype == 'root':
                point_penalty = 100
            elif btype == 'user':
                point_penalty = 25
            elif btype == 'userids':
                point_penalty = 50
            elif btype == 'sensitive_files':
                point_penalty = 25
            elif btype == 'pii':
                point_penalty = 200
            elif btype == 'other':
                point_penalty = 50
            else:
                point_penalty = 0

            description = form.describe.data
            rtr = RedTeamReport(team_id, int(REQStatus.PENDING), system_id, btype, description=description, point_penalty=point_penalty)
            return redirect(url_for('rtr'))
    return render_template('rtr_submit.html', form=form, rtr_id=rtr_id, success=success, system_id=system_id)     

@app.route('/rtr_details', methods=['GET', 'POST'])
@login_required
@redorwhite_required
def rtr_details():
    """
    Location to view and edit red team action reports.
    """
    user = flask_login.current_user
    if request.method == 'GET':
        rtr_id = request.args.get('id')
        rtr = RedTeamReport.load(rtr_id)
        domains = {d.id:d for d in wm.domains}
        checks = {c.id:c for c in wm.checks}
        return render_template('rtr_details.html', rtr=rtr, checks=checks, domains=domains)


    elif request.method == 'POST':
        rtr_id = request.form['reqId']
        rtr = RedTeamReport.load(rtr_id)
        if user.is_admin:
            if rtr.status == REQStatus.PENDING or rtr.status == REQStatus.APPROVAL:
                if 'approval' in request.form:
                    if request.form['approval'] == 'Approve':
                        status = REQStatus.PENDING
                        rtr.set_status(status)
                        rtr.service_request(wm.teams[rtr.team_id-1])
                    else:
                        status = REQStatus.DENIED
                        rtr.set_status(status)
            comment = request.form['admin_comment']
            rtr.set_admin_comment(comment)
        return redirect(url_for('rtr_details') + '?id={}'.format(rtr_id))

@app.route('/ir', methods=['GET', 'POST'])
@login_required
def ir():
    """
    Systems for the blue team to file incident reports on.
    """
    return render_template('ir_systems.html')

@app.route('/ir_overview', methods=['GET', 'POST'])
@login_required
def ir_overview():
    """
    Dashboard with incident reports information.
    """
    return render_template('ir_overview.html')

@app.route('/revert_log', methods=['GET'])
@login_required
def revert_log():
    teams = {}
    for team in wm.teams:
        teams[team.id] = team.name

    if current_user.name == 'admin':
        reverts = db.getall('revert_log', orderby='time DESC')
    else:
        reverts = db.get('revert_log', ['*'], where='team_id=%s', orderby='time DESC', args=(current_user.team.id,))
    return render_template('revert_log.html', teams=teams, reverts=reverts)

def get_team_slas(team_id): # This code is redundant with that in scoring_engine. Find a better wayt to calc and store slas?
                            # Could create sla database and store per team, or add team values to system rather than calculating from result log
    results = db.get('result', ['time', 'check_id', 'result'], where='team_id=%s', orderby='time ASC', args=(team_id,))
    down_counts = {}
    slas = []
    for time, check_id, result in results:
        if not check_id in down_counts:
            down_counts[check_id] = 0
        if not result:
            down_counts[check_id] += 1
        else:
            down_counts[check_id] = 0
        if down_counts[check_id] >= 6:
            down_counts[check_id] = 0
            slas.append((time, check_id))
    return slas

def get_slas():
    slas = {}
    for team in wm.teams:
        slas[team.id] = get_team_slas(team.id)
    return slas

@app.route('/sla/log', methods=['GET'])
@login_required
@deny_redteam
def sla_log():
    slas = get_slas()

    user = flask_login.current_user

    cs = {}
    for check in wm.checks:
        cs[check.id] = check

    return render_template('sla_log.html', slas=slas, checks=cs)

@app.route('/sla/totals', methods=['GET'])
@login_required
@deny_redteam
def sla_totals():
    cs = {}
    for check in wm.checks:
        cs[check.id] = check

    slas = get_slas()
    totals = {}
    for team in wm.teams:
        totals[team.id] = {}
        for check in wm.checks:
            totals[team.id][check.id] = 0

    for team in wm.teams:
        for time, check_id in slas[team.id]:
            totals[team.id][check_id] += 1

    return render_template('sla_totals.html', totals=totals, checks=cs, teams=wm.teams)

