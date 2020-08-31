from flask import render_template, request, redirect, url_for, Blueprint
from web.forms import PasswordChangeForm
import flask_login
from flask_login import login_required
from engine.model import PasswordChangeRequest, PCRStatus
import db
import re
from . import wm

blueprint = Blueprint('pcr', __name__, url_prefix='/pcr')

@blueprint.route('', methods=['GET', 'POST'])
@login_required
def pcr():
    """
    Render the password change request overview page.
    """
    user = flask_login.current_user
    if request.method == 'GET':
        if user.is_admin:
            where = None
            orderby = None
            args = None
        else:
            team_id = user.team.id
            where = 'team_id = %s'
            orderby = 'submitted DESC'
            args = (team_id)
        pcr_ids = db.get('pcr', ['id'], where=where, orderby=orderby, args=args)
        pcrs = [PasswordChangeRequest.load(pcr_id) for pcr_id in pcr_ids]
        for pcr in pcrs:
            if pcr.status == PCRStatus.PENDING:
                pcr.service_request()
        checks = {c.id:c for c in wm.checks}
        return render_template('pcr/pcr_overview.html', pcrs=pcrs, checks=checks)
    elif request.method == 'POST':
        pcr_id = request.form['reqId']
        pcr = PasswordChangeRequest.load(pcr_id)
        if (not user.is_admin and user.team.id != pcr.team_id) or pcr.status == PCRStatus.COMPLETE:
            pass # Show error?
        else:
            pcr.delete()
        return redirect(url_for('pcr.pcr'))

@blueprint.route('/details', methods=['GET', 'POST'])
@login_required
def pcr_details():
    """
    Render the password change request details page.
    """
    user = flask_login.current_user
    if request.method == 'GET':
        pcr_id = request.args.get('id')
        pcr = PasswordChangeRequest.load(pcr_id)
        domains = {d.fqdn:d for d in wm.domains}
        checks = {c.id:c for c in wm.checks}
        if user.is_admin or user.team.id == pcr.team_id:
            return render_template('pcr/pcr_details.html', pcr=pcr, checks=checks, domains=domains)
        else:
            return redirect(url_for('pcr.pcr'))
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
        return redirect(url_for('pcr.pcr_details') + '?id={}'.format(pcr_id))

@blueprint.route('/new', methods=['GET', 'POST'])
@login_required
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

            domain = form.domain.data
            check_id = form.check.data
            pwchange = form.pwchange.data

            pwchange = [line.split(':') for line in pwchange.split('\r\n')]
            creds = []
            for line in pwchange:
                if len(line) >= 2:
                    username = re.sub('\s+', '', line[0])
                    password = re.sub('\s+', '', ':'.join(line[1:]))
                    creds.append((username, password))
            pcr = PasswordChangeRequest(team_id, PCRStatus.PENDING, creds, check_id=check_id, domain=domain)
            pcr.service_request()
            pcr_id = pcr.id
            return redirect(url_for('pcr.pcr'))
    return render_template('pcr/pcr_new.html', form=form, pcr_id=pcr_id, success=success)
