import db
from data_model import *
from web.model import User
import json
import re
import bcrypt

class WebModel(DataModel):

    def load_db(self):
        """
        Load all data from the database, including web-specific data."
        """
        super().load_db()
        self.users = self.load_web_users(self.teams)

    def load_web_users(self, teams):
        """
        Load the web application users from the database.

        Arguments:
            teams (Dict(int->Team)): Mapping of team database IDs to Teams

        Returns:
            Dict(str->User): Mapping of usernames to User objects for users who
                can login to the web application.
        """
        users = {}
        user_rows = db.get('users', ['username', 'team_id', 'is_admin'])
        for user,team_id,is_admin in user_rows:
            teams_match = filter(lambda t: t.id == team_id, teams)
            if len(teams_match):
                team = None
            else:
                team = next(teams_match)
            users[user] = User(user, team, is_admin)
        return users

    def latest_results(self):
        """
        Gather the latest results for each team/check combo.

        Returns:
            results (Dict(int->Dict(int->(Result)))): A mapping of each team and check to its latest result
        """
        self.load_results()
        results = {}
        for team in self.teams:
            results[team.id] = {}
            for check in self.checks:
                if len(self.results[team.id][check.id]) > 0:
                    res = self.results[team.id][check.id][-1]
                    results[team.id][check.id] = res
        return results

    def change_passwords(self, team_id, domain_id, service_id, pwchange):
        """
        Change the passwords for the given credentials.

        Arguments:
            team_id (int): The ID of the team the credential belongs to
            domain_id (int): The ID of the domain the credential belongs to
            service_id (int): The ID of the service the credential belongs to
            pwchange (str): A series of user:pass combos separated by CRLFs
        """
        pwchange = [line.split(':') for line in pwchange.split('\r\n')]
        for line in pwchange:
            if len(line) >= 2:
                username = re.sub('\s+', '', line[0])
                password = re.sub('\s+', '', ':'.join(line[1:]))
                db.set_credential_password(username, password, team_id,
                                           service_id, domain_id)
       
    def change_user_password(self, username, newpw):
        """
        Set the given user's password to the given password.

        Arguments:
            username (str): The user to change the password for
            newpw (str): The new password
        """
        newpw = newpw.encode('utf-8')
        pwhash = bcrypt.hashpw(newpw, bcrypt.gensalt())
        db.modify('users', 'password=%s', (pwhash, username),
                  where='username=%s')

    def get_user_password(self, username):
        """
        Get the password hash for the given user.

        Arguments:
            username (str): The username to get the hash for

        Returns:
            (str): The password hash
        """
        username = username.lower()
        hash_rows = db.get('users', ['password'], where='username=%s',
                           args=(username))
        pwhash = hash_rows[0][0]
        return pwhash

    def update_setting(self, key, value):
        """
        Update the value of a setting in the database.

        Arguments:
            key (str): The setting to change
            value (str): The value to change the setting to
        """
        db.modify('settings', 'value=%s', (value, key), where='skey=%s')
