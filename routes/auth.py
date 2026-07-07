"""
routes/auth.py
──────────────
Simple username/password auth:

- /signup  -> "Create Your Own Account" - collects name, phone, email, and a
              password the user chooses themself. Account is created and the
              user is logged in immediately, no email verification step.
- /login   -> username is the account email, password is whatever was set at
              signup.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, make_response
from extensions import db
from models.user import EmailSubscriber, User, LoginLog
from config import Config
import json

auth_bp = Blueprint('auth', __name__)


def _client_ip():
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or 'unknown'


def _log_in_user(user, remember):
    session.permanent = bool(remember)
    session['user_id'] = user.id


# -- Create Your Own Account (name + phone + email + password) ---

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html',
                               categories=Config.CATEGORIES,
                               category_colors=Config.CATEGORY_COLORS)

    name             = request.form.get('name', '').strip()
    phone            = request.form.get('phone', '').strip()
    email            = request.form.get('email', '').strip().lower()
    password         = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not name:
        flash('Enter your name.', 'error')
        return redirect(url_for('auth.signup'))

    if not phone:
        flash('Enter your phone number.', 'error')
        return redirect(url_for('auth.signup'))

    if not email or '@' not in email:
        flash('Enter a valid email.', 'error')
        return redirect(url_for('auth.signup'))

    if len(password) < 6:
        flash('Password must be at least 6 characters.', 'error')
        return redirect(url_for('auth.signup'))

    if password != confirm_password:
        flash('Passwords do not match.', 'error')
        return redirect(url_for('auth.signup'))

    if User.query.filter_by(email=email).first():
        flash('An account already exists for this email. Try signing in instead.', 'error')
        return redirect(url_for('auth.login'))

    user = User(email=email, name=name, phone=phone, is_verified=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    LoginLog.record(email=email, purpose='signup', success=True, ip_address=_client_ip())

    _log_in_user(user, remember=True)
    flash('Account created, welcome to NewsCore!', 'success')
    return redirect(url_for('main.index'))


# -- Sign in with email + password ----------------------------------

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        next_url = request.args.get('next', '')
        return render_template('login.html',
                               next_url=next_url,
                               categories=Config.CATEGORIES,
                               category_colors=Config.CATEGORY_COLORS)

    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    remember = request.form.get('remember') == 'on'
    next_url = request.form.get('next', '') or url_for('main.index')
    ip = _client_ip()

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        LoginLog.record(email=email, purpose='login', success=False, ip_address=ip)
        flash('Incorrect email or password.', 'error')
        return redirect(url_for('auth.login', next=next_url))

    LoginLog.record(email=email, purpose='login', success=True, ip_address=ip)
    _log_in_user(user, remember=remember)
    return redirect(next_url)


# -- Logout ------------------------------------------------------

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.permanent = False
    return redirect(url_for('main.index'))


# -- Digest signup page (unchanged) ------------------------------

@auth_bp.route('/digest')
def digest():
    return render_template(
        'digest_signup.html',
        categories=Config.CATEGORIES,
        category_colors=Config.CATEGORY_COLORS,
    )


# -- Unsubscribe (unchanged) ---------------------------------------

@auth_bp.route('/unsubscribe')
def unsubscribe():
    email = request.args.get('email', '').strip().lower()

    if not email:
        flash('Invalid unsubscribe link.', 'error')
        return redirect(url_for('main.index'))

    sub = EmailSubscriber.query.filter_by(email=email).first()

    if sub:
        sub.active = False
        db.session.commit()
        flash(f'Successfully unsubscribed {email}.', 'success')
    else:
        flash('Email not found in our list.', 'error')

    return redirect(url_for('main.index'))


# -- Guest category preference (unchanged) -------------------------

@auth_bp.route('/preferences', methods=['POST'])
def save_preferences():
    data = request.get_json(silent=True) or {}
    cats = data.get('categories', [])

    if not isinstance(cats, list):
        return jsonify({'error': 'Invalid format'}), 400

    valid = [c for c in cats if c in Config.CATEGORIES]

    response = make_response(jsonify({'saved': valid}))
    response.set_cookie(
        'nc_preferred_cats',
        json.dumps(valid),
        max_age=60 * 60 * 24 * 365,
        samesite='Lax',
        httponly=True,
    )
    return response
