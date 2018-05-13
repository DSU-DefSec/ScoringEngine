from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *
import bcrypt
import flask_login

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])

    def __init__(self, dm):
        super(LoginForm, self).__init__()
        self.dm = dm

    def validate(self):
        if not super(LoginForm, self).validate():
            return False

        pwhash = self.dm.get_hash(self.username.data)
        pwhash = pwhash.encode('utf-8')
        passwd = self.password.data.encode('utf-8')

        return bcrypt.checkpw(passwd, pwhash)


class PasswordChangeForm(FlaskForm):
    team = SelectField('Team', coerce=int)
    ctype = SelectField('Credential Type')
    domain = SelectField('Domain', coerce=int)
    service = SelectField('Service', coerce=int)
    pwchange = TextAreaField('Password Changes')

    def __init__(self, dm):
        super(PasswordChangeForm, self).__init__()
        self.dm = dm

        self.team.choices=[(t.id, t.name) for t in dm.teams]
        self.team.validators=[Optional()]

        self.ctype.choices=[('Local', 'Local'), ('Domain', 'Domain')]
        self.ctype.validators=[InputRequired()]
        
        self.domain.choices=[(d.id, d.fqdn) for d in dm.domains]
        self.domain.validators=[Optional()]

        self.service.choices=[(s.id, 'Host: %d, Port: %d' % (s.host, s.port)) for s in dm.services]
        self.service.validators=[Optional()]

        self.pwchange.validators=[InputRequired(),
                Regexp('^(.*[^\s]+:[^\s]+.*(\r\n)*)+$',
                    message='Invalid format: Use user:password, one per line')]

class PasswordResetForm(FlaskForm):
    user = SelectField('User', validators=[Optional()])
    current_pw = PasswordField('Current Password', validators=[Optional()])
    new_pw = PasswordField('New Password', validators=[InputRequired()])
    confirm_new_pw = PasswordField('Confirm New Password', validators=[InputRequired()])

    def __init__(self, dm):
        super(PasswordResetForm, self).__init__()
        self.dm = dm
        self.user.choices=[(username, username) for username in dm.users.keys()]

    def validate(self):
        if not super(PasswordResetForm, self).validate():
            return False

        if self.new_pw.data != self.confirm_new_pw.data:
            self.errors['samepw'] = 'Passwords don\'t match'
            return False

        if not flask_login.current_user.is_admin:
            username = self.user.data
            print('formdata', username)
            if username == 'None':
                username = flask_login.current_user.name
            print(username)
            username = username.lower()
    
            pwhash = self.dm.get_hash(username)
            pwhash = pwhash.encode('utf-8')
            passwd = self.current_pw.data.encode('utf-8')
    
            if not bcrypt.checkpw(passwd, pwhash):
                self.errors['validpw'] = 'Invalid Password'
                return False
        return True
