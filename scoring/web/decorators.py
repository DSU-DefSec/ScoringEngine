from functools import wraps
import flask_login
from flask import request

def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not flask_login.current_user.is_admin:
            return "Access Denied"
        return f(*args, **kwargs)
    return wrapped

def local_only(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if request.remote_addr != '127.0.0.1':
            return "Access Denied"
        return f(*args, **kwargs)
    return wrapped
