from flask import render_template, request, Blueprint
from flask_login import login_required, current_user
import db
import vcloud
from . import wm

blueprint = Blueprint('vcloud', __name__, url_prefix='/vcloud')

@blueprint.route('/systems', methods=['GET', 'POST'])
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
            errors = vcloud.power_on(vapp, system.name)
        elif request.form['action'] == 'power off':
            errors = vcloud.power_off(vapp, system.name)
        elif request.form['action'] == 'restart':
            errors = vcloud.restart(vapp, system.name)
        elif request.form['action'] == 'revert':
            errors = vcloud.revert(vapp, system.name)
            if errors == '':
                db.insert('revert_log', ['team_id', 'system'], [tid, system.name])
    systems = wm.systems
    return render_template('vcloud/systems.html', systems=systems, penalty=wm.settings['revert_penalty'], errors=errors)

@blueprint.route('/revert_log', methods=['GET'])
@login_required
def revert_log():
    teams = {}
    for team in wm.teams:
        teams[team.id] = team.name

    if current_user.name == 'admin':
        reverts = db.getall('revert_log', orderby='time DESC')
    else:
        reverts = db.get('revert_log', ['*'], where='team_id=%s', orderby='time DESC', args=(current_user.team.id,))
    return render_template('vcloud/revert_log.html', teams=teams, reverts=reverts)
