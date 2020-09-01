from functools import wraps
import flask_login
from flask import request

def admin_required(f):
    """
    Decorator requiring that the user who requested the website is an admin.

    Agruments:
        f (function): The function to restrict access to

    Returns:
        (function): The wrapped function
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not flask_login.current_user.is_admin:
            return "Access Denied"
        return f(*args, **kwargs)
    return wrapped

def local_only(f):
    """
    Decorator requiring that the request is coming from localhost.

    Agruments:
        f (function): The function to restrict access to

    Returns:
        (function): The wrapped function
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        if request.remote_addr != '127.0.0.1':
            return "Access Denied"
        return f(*args, **kwargs)
    return wrapped
