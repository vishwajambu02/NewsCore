from functools import wraps
from flask import session, redirect, url_for, request


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return wrapper


def current_user():
    from models.user import User
    uid = session.get('user_id')
    if not uid:
        return None
    return User.query.get(uid)
