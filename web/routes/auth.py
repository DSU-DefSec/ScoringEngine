import flask
from flask import render_template, request, redirect, url_for, Blueprint
from .utils import is_safe_url
from web.forms import LoginForm, PasswordResetForm
import flask_login
from flask_login import LoginManager, login_user, logout_user, login_required
from . import wm

login_manager = LoginManager()
blueprint  = Blueprint('auth', __name__, url_prefix='/auth')

@login_manager.user_loader
def load_user(user_id):
    if user_id not in wm.users:
        return None
    return wm.users[user_id]

@blueprint.route('/login', methods=['GET', 'POST'])
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
        
                next = request.args.get('next')
                if not is_safe_url(next): # Open redirect protection
                    return flask.abort(400)

                return redirect(next or flask.url_for('status.status'))
        else:
            error = "Invalid username/password"
    return render_template('auth/login.html', form=form, error=error)

@blueprint.route('/logout')
@login_required
def logout():
    """
    Log out the user and redirect them to the status page.
    """
    logout_user()
    return redirect(flask.url_for('status.status'))

@blueprint.route('/password_reset', methods=['GET', 'POST'])
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
    return render_template('auth/pw_reset.html', success=success, form=form)
