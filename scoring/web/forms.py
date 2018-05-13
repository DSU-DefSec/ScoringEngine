from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *
import bcrypt
import flask_login

class LoginForm(FlaskForm):
    """
    A form for user login.

    Attributes:
        username (StringField): A username field
        password (PasswordField): A password field
        wm (WebModel): The web model
    """

    def __init__(self, wm):
        super(LoginForm, self).__init__()
        username = StringField('Username', validators=[InputRequired()])
        password = PasswordField('Password', validators=[InputRequired()])
        self.wm = wm

    def validate(self):
        """
        Check whether the username / password combo is correct

        Returns:
            bool: Are the credentials valid?
        """
        if not super(LoginForm, self).validate():
            return False

        pwhash = self.wm.get_hash(self.username.data)
        pwhash = pwhash.encode('utf-8')
        passwd = self.password.data.encode('utf-8')

        return bcrypt.checkpw(passwd, pwhash)


class PasswordChangeForm(FlaskForm):
    """
    A form for bulk password changes.

    Attributes:
        team (SelectField): Field for selecting the credential's team
        ctype (SelectField): Field for selecting the type of credential
        domain (SelectField): Field for selecting the credential's domain
        service (SelectField): Field for selecting the credential's service
        pwchange (TextAreaField): Field for inputting password changes
        wm (WebModel): The web model
    """

    def __init__(self, wm):
        super(PasswordChangeForm, self).__init__()
        team = SelectField('Team', coerce=int)
        ctype = SelectField('Credential Type')
        domain = SelectField('Domain', coerce=int)
        service = SelectField('Service', coerce=int)
        pwchange = TextAreaField('Password Changes')
        self.wm = wm

        # Add options and validators for each field
        self.team.choices=[(t.id, t.name) for t in dm.teams]
        self.team.validators=[Optional()]

        self.ctype.choices=[('Local', 'Local'), ('Domain', 'Domain')]
        self.ctype.validators=[InputRequired()]
        
        self.domain.choices=[(d.id, d.fqdn) for d in dm.domains]
        self.domain.validators=[Optional()]

        self.service.choices=[(s.id, 'Host: %d, Port: %d' % (s.host, s.port)) for s in dm.services]
        self.service.validators=[Optional()]

        # Regex validator: "user:pass\r\nuser2:pass2"
        self.pwchange.validators=[InputRequired(),
                Regexp('^(.*[^\s]+:[^\s]+.*(\r\n)*)+$',
                    message='Invalid format: Use user:password, one per line')]

class PasswordResetForm(FlaskForm):
    """
    A form for reseting a web user's password

    Attributes:
        user (SelectField): Field to select the user whose password to reset
        current_pw (PasswordField): Field for the user's current password
        new_pw (PasswordField): Field for the user's new password
        confirm_new_pw (PasswordField): Field to confirm the user's new password
        wm (WebModel): The web model
    """

    def __init__(self, wm):
        super(PasswordResetForm, self).__init__()
        user = SelectField('User', validators=[Optional()])
        current_pw = PasswordField('Current Password', validators=[Optional()])
        new_pw = PasswordField('New Password', validators=[InputRequired()])
        confirm_new_pw = PasswordField('Confirm New Password', validators=[InputRequired()])
        self.wm = wm
        self.user.choices=[(username, username) for username in dm.users.keys()]

    def validate(self):
        """
        Check that the current password is correct and the two new passwords are the same.

        Returns:
            bool: Is the form valid?
        """
        if not super(PasswordResetForm, self).validate():
            return False

        if self.new_pw.data != self.confirm_new_pw.data:
            self.errors['samepw'] = 'Passwords don\'t match'
            return False

        # If the user is not an admin, they must enter their current password
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
