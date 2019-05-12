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
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])

    def __init__(self, wm):
        super().__init__()
        self.wm = wm

    def validate(self):
        """
        Check whether the username / password combo is correct

        Returns:
            bool: Are the credentials valid?
        """
        if not super(LoginForm, self).validate():
            return False

        pwhash = self.wm.get_user_password(self.username.data)
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
    team = SelectField('Team', coerce=int)
    ctype = SelectField('Credential Type')
    domain = SelectField('Domain', coerce=int)
    check = SelectField('Service', coerce=int)
    pwchange = TextAreaField('Password Changes')

    def __init__(self, wm):
        super(PasswordChangeForm, self).__init__()
        self.wm = wm

        # Add options and validators for each field
        self.team.choices=[(t.id, t.name) for t in wm.teams]
        self.team.validators=[Optional()]

        self.ctype.choices=[('Local', 'Local'), ('Domain', 'Domain')]
        self.ctype.validators=[InputRequired()]
        
        self.domain.choices=[(d.id, d.fqdn) for d in wm.domains]
        self.domain.validators=[Optional()]

        self.check.choices=[(c.id, c.name) for c in wm.checks]
        self.check.validators=[Optional()]

        # Regex validator: "user:pass\r\nuser2:pass2"
        self.pwchange.validators=[InputRequired(),
                Regexp('^(.*[^\s]+:[^\s]+.*(\r\n)*)+$',
                    message='Invalid format: Use user:password, one per line')]

class RedTeamActionReportForm(FlaskForm):
    """
    A form for the red team to claim access on a box.

    Attributes:
        team (SelectField): Field for selecting the credential's team
        btype (SelectField): Field for selecting the type of breach
        describe (TextAreaField): Field for selecting the credential's domain
        wm (WebModel): The web model
    """
    team = SelectField('Team', coerce=int)
    btype = SelectField('Type of Action')
    describe = TextAreaField('Description of Action')
    # Todo: add file upload (flask-upload?)

    def __init__(self, wm):
        super(RedTeamActionReportForm, self).__init__()
        self.wm = wm

        # Add options
        self.team.choices=[(t.id, t.name) for t in wm.teams]
        self.btype.choices=[('root', 'Obtained root level access'), ('user', 'Obtained user level access'), ('userids', 'Obtained userids and passwords (encrypted or unencrypted)'), ('sensitive_files', 'Recovered sensitive files or pieces of information'), ('pii', 'Recovered customer PII from system'), ('other', 'Other')]

class IncidentReportForm(FlaskForm):
    """
    A form for the blue team to file an incident report.

    Attributes:
        btype (SelectField): Field for selecting the type of breach
        describe (TextAreaField): Field for selecting the credential's domain
        wm (WebModel): The web model
    """
    btype = SelectField('Type of Action')
    describe = TextAreaField('Description of Action')
    # Todo: add file upload (flask-upload?)

    def __init__(self, wm):
        super(IncidentReportForm, self).__init__()
        self.wm = wm
        # Add options
        self.btype.choices=[('root', 'Obtained root level access'), ('user', 'Obtained user level access'), ('userids', 'Obtained userids and passwords (encrypted or unencrypted)'), ('sensitive_files', 'Recovered sensitive files or pieces of information'), ('pii', 'Recovered customer PII from system'), ('other', 'Other')]


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
    user = SelectField('User', validators=[Optional()])
    current_pw = PasswordField('Current Password', validators=[Optional()])
    new_pw = PasswordField('New Password', validators=[InputRequired()])
    confirm_new_pw = PasswordField('Confirm New Password', validators=[InputRequired()])

    def __init__(self, wm):
        super(PasswordResetForm, self).__init__()
        self.wm = wm
        self.user.choices=[(username, username) for username in wm.users.keys()]
        self.user.choices.sort()

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
    
            pwhash = self.wm.get_user_password(username)
            pwhash = pwhash.encode('utf-8')
            passwd = self.current_pw.data.encode('utf-8')
    
            if not bcrypt.checkpw(passwd, pwhash):
                self.errors['validpw'] = 'Invalid Password'
                return False
        return True
