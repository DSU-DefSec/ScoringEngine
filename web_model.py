from flask_login import UserMixin

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
    """
    def __init__(self, id, team):
        self.id = id
        self.name = id
        self.team = team

    def get_id(self):
        """
        Get the ID of the user.

        Returns:
            (str): A unicode identifier for the user
        """
        return self.id
