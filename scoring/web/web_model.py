import db
from data_model import *
from .model import User
import utils
import json
import re
import bcrypt

class WebModel(DataModel):

    def load_db(self):
        """
        Load all data from the database, including web-specific data.
        """
        super().load_db()
        self.users = self.load_web_users(self.teams)
        self.load_results()

    def load_web_users(self, teams):
        """
        Load the web application users from the database.

        Arguments:
            teams (Dict(int->Team)): Mapping of team database IDs to Teams

        Returns:
            Dict(str->User): Mapping of usernames to User objects for users who can login to the web application.
        """
        users = {}
        user_rows = db.get('users', ['username', 'team_id', 'is_admin'])
        for user,team_id,is_admin in user_rows:
            teams_match = [t for t in teams if t.id == team_id]
            if len(teams_match) == 0:
                team = None
            else:
                team = teams_match[0]
            users[user] = User(user, team, is_admin)
        return users

    def latest_results(self):
        """
        Gather the latest results for each team/check combo.

        Returns:
            Dict(int->Dict(int->(Result))): A mapping of each team and check to its latest result
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
            str: The password hash
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

    def load_results(self):
        """
        Update results with any results not yet loaded from the database.
        """
        if self.results is None:
            last_id = 0
            # Setup dict
            self.results = {}
            for team in self.teams:
                self.results[team.id] = {}
                for check in self.checks:
                    self.results[team.id][check.id] = []
        else:
            # If results exist, we can just load the latest ones and keep the old ones
            # Here we find the id of the last result we already have
            last_ids = []
            for team_results in self.results.values():
                for check_results in team_results.values():
                    if len(check_results) != 0:
                        last_ids.append(check_results[-1].id)
            last_id = -1
            if len(last_ids) != 0:
                last_id = max(last_ids)

        rows = db.get('result', ['*'], where='id > %s',
                      orderby='time ASC', args=(last_id))

        # Gather the results
        for result_id, check_id, check_io_id, team_id, time, poll_input, poll_result, result in rows:
            # Construct the result from the database info
            check = [c for c in self.checks if c.id == check_id][0]
            check_io = [cio for cio in self.check_ios if cio.id == check_io_id][0]
            team = [t for t in self.teams if t.id == team_id][0]

            input_class_str, input_args = json.loads(poll_input)
            input_class = utils.load_module(input_class_str)
            poll_input = input_class.deserialize(input_class, input_args, self.teams, self.credentials)

            poll_result = json.loads(poll_result)[1]

            res = Result(result_id, check, check_io, team, time, poll_input, poll_result, result)

            self.results[team_id][check_id].append(res)
