from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import DataRequired
import bcrypt

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

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

