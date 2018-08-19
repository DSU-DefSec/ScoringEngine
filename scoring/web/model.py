import db
from flask_login import UserMixin
from enum import IntEnum
import datetime
import json

class User(UserMixin):
    """
    A Flask-Login user.

    Attributes:
        is_authenticated (bool): Is the user authenticated?
        is_active (bool): Has the account been activated?
        is_anonymous (bool): Is this an anonymous user?
        id (str): A unicode identifier for this user
        name (str): Name of the user
        team (Team): Team the user belongs to
        is_admin (bool): Is the user an admin?
    """
    def __init__(self, id, team, is_admin):
        self.id = id
        self.name = id
        self.team = team
        self.is_admin = is_admin

    def get_id(self):
        """
        Get the ID of the user.

        Returns:
            str: A unicode identifier for the user
        """
        return self.id

class PCRStatus(IntEnum):
    COMPLETE = 0
    PENDING = 1
    APPROVAL = 2
    DENIED = 3

class PasswordChangeRequest(object):
    """
    A password change request.

    Attributes:
        
        team_id (int): ID of the team to change passwords for
        status (PCRStatus): The status of the request
        creds (List(str,str)): List of tuples (username, new_password)
        service_id (int): ID of the service to change passwords for
        domain_id (int): ID of the domain to change passwords for
        submitted (datetime): Submission time for the request
        completed (datetime): Completition time for the request
        id (int): ID of the request
    """
    def __init__(self, team_id, status, creds, id=None, service_id=None, domain_id=None, submitted=None, completed=None, team_comment='', admin_comment=''):
        self.id = id
        self.team_id = team_id
        self.service_id = service_id
        self.domain_id = domain_id
        if submitted is None:
            submitted = datetime.datetime.now()
        self.submitted = submitted
        self.completed = completed
        self.status = status
        self.creds = creds
        self.team_comment = team_comment
        self.admin_comment = admin_comment
        
        if id is None:
            self.save()

    def load(pcr_id):
        """
        Load a PasswordChangeRequest with the given database ID.

        Arguments:
            pcr_id (int): ID of PasswordChangeRequest in database

        Returns:
            PasswordChangeRequest: The password change request with the given ID
        """
        pcr_data = db.get('pcr', ['*'], where='id=%s', args=[pcr_id])[0]
        id, team_id, service_id, domain_id, submitted, completed, status, creds, team_comment, admin_comment = pcr_data
        creds = json.loads(creds)
        pcr = PasswordChangeRequest(team_id, status, creds, id, service_id, domain_id, submitted, completed, team_comment, admin_comment)
        return pcr

    def save(self):
        """
        Save this new password change request to the database.
        """
        columns = ['team_id', 'service_id', 'domain_id', 'submitted', 'completed', 'status', 'creds']
        data = [self.team_id, self.service_id, self.domain_id, self.submitted, self.completed, int(self.status), json.dumps(self.creds)]
        self.id = db.insert('pcr', columns, data)

    def delete(self):
        """
        Delete this password change request from the database. The object should not be used after this method is called.
        """
        db.delete('pcr', [self.id], 'id=%s')

    def conflicts(self, window):
        """
        Is there an account conflict for requests submitted in the window of time before this request.

        Arguments:
            window (int): Window for flagging conflicting requests in minutes

        Returns:
            bool: Does this request conflict with an earlier one?
        """
        # Load list of possible conflicting password change requests
        where = 'id != %s AND team_id = %s AND status != %s '
        if self.service_id is None:
            where += 'AND service_id is %s AND domain_id = %s'
        else:
            where += 'AND service_id = %s AND domain_id is %s'

        pcr_ids = db.get('pcr', ['id'], where=where, args=[self.id, self.team_id, int(PCRStatus.DENIED), self.service_id, self.domain_id])
        pcrs = [PasswordChangeRequest.load(pcr_id) for pcr_id in pcr_ids]
        # Check list for conflicts
        window = datetime.timedelta(minutes=window)
        users = [cred[0] for cred in self.creds]
        for pcr in pcrs:
            if pcr.submitted + window >= self.submitted:
                for cred in pcr.creds:
                    if cred[0] in users:
                        return True
        return False

    def set_status(self, new_status):
        """
        Set the status of the request, and update the database to reflect the new status

        Arguments:
            new_status (PCRStatus): New status for the request
        """
        self.status = new_status
        db.modify('pcr', 'status=%s', (int(self.status), self.id), where='id=%s')

    def set_team_comment(self, team_comment):
        """
        Set the team comment for this request and save it to the database.

        Arguments:
            team_comment (str): New team comment
        """
        self.team_comment = team_comment
        db.modify('pcr', 'team_comment=%s', (team_comment, self.id), where='id=%s')

    def set_admin_comment(self, admin_comment):
        """
        Set the admin comment for this request and save it to the database.

        Arguments:
            admin_comment (str): New admin comment
        """
        self.admin_comment = admin_comment
        db.modify('pcr', 'admin_comment=%s', (admin_comment, self.id), where='id=%s')

    def service_request(self):
        """
        Service this request, updating account credentials in the database, and updating the current status of the request
        """
        for cred in self.creds:
            username, password = cred
            db.set_credential_password(username, password, self.team_id, self.service_id, self.domain_id)
        self.completed = datetime.datetime.now()
        db.modify('pcr', 'completed=%s', (self.completed, self.id), where='id=%s')
        self.set_status(PCRStatus.COMPLETE)
