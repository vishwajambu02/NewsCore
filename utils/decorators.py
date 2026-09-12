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


def retry_on_db_error(f):
    """
    Neon's free-tier Postgres can drop an idle/serverless connection
    mid-request (shows up as 'SSL error: bad record type' or similar).
    pool_pre_ping catches most stale connections at checkout, but not
    ones that die mid-query. Retry the whole view once after rolling
    back the broken session, instead of showing the user a 500.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        from sqlalchemy.exc import OperationalError
        from extensions import db
        try:
            return f(*args, **kwargs)
        except OperationalError:
            db.session.rollback()
            return f(*args, **kwargs)
    return wrapper
