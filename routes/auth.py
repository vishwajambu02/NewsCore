"""
routes/auth.py
──────────────
Signup flow (email OTP verification, then choose your own password):

  1. /signup         -> collects name, phone, email. Sends a 6-digit code.
  2. /verify-email    -> user enters the code. Once correct, email is
                        confirmed but no account exists yet.
  3. /set-password    -> user chooses their own password. Account is
                        created at this point and the user is logged in.

Login is plain email + password, no OTP:

  /login -> username is the account email, password is whatever was set
            in step 3 above.

Password recovery:

  /change-password  -> logged-in users change their own password.
  /forgot-password   -> request an OTP code to email.
  /reset-password    -> verify that OTP + set a new password.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, make_response
from extensions import db
from models.user import EmailSubscriber, User, OTPCode, LoginLog
from services.email_service import send_otp_email
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


# -- Step 1: Create Your Own Account (name + phone + email) ------

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html',
                               categories=Config.CATEGORIES,
                               category_colors=Config.CATEGORY_COLORS)

    name  = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip().lower()

    if not name:
        flash('Enter your name.', 'error')
        return redirect(url_for('auth.signup'))

    if not phone:
        flash('Enter your phone number.', 'error')
        return redirect(url_for('auth.signup'))

    if not email or '@' not in email:
        flash('Enter a valid email.', 'error')
        return redirect(url_for('auth.signup'))

    if User.query.filter_by(email=email).first():
        flash('An account already exists for this email. Try signing in instead.', 'error')
        return redirect(url_for('auth.login'))

    otp = OTPCode.generate(email, purpose='signup')
    sent = send_otp_email(email, otp.code, purpose='signup')
    if not sent:
        flash('Could not send code. Try again shortly.', 'error')
        return redirect(url_for('auth.signup'))

    session['pending_email'] = email
    session['pending_name']  = name
    session['pending_phone'] = phone
    return redirect(url_for('auth.verify_email'))


# -- Step 2: Verify the email with a 6-digit code -----------------

@auth_bp.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    email = session.get('pending_email')
    if not email:
        return redirect(url_for('auth.signup'))

    if request.method == 'GET':
        return render_template('verify_otp.html',
                               email=email,
                               categories=Config.CATEGORIES,
                               category_colors=Config.CATEGORY_COLORS)

    code = request.form.get('code', '').strip()
    ip = _client_ip()

    otp = (OTPCode.query
           .filter_by(email=email, code=code, purpose='signup', used=False)
           .order_by(OTPCode.created_at.desc())
           .first())

    if not otp or not otp.is_valid():
        LoginLog.record(email=email, purpose='signup', success=False, ip_address=ip, method='otp')
        flash('Invalid or expired code.', 'error')
        return redirect(url_for('auth.verify_email'))

    otp.used = True
    db.session.commit()

    session['email_verified'] = True
    return redirect(url_for('auth.set_password'))


# -- Resend the code (AJAX-friendly, also works as a normal POST) --

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    email = session.get('pending_email')
    if not email:
        return jsonify({'error': 'No pending signup'}), 400

    otp = OTPCode.generate(email, purpose='signup')
    sent = send_otp_email(email, otp.code, purpose='signup')
    if not sent:
        return jsonify({'error': 'Failed to send code'}), 500

    return jsonify({'ok': True})


# -- Step 3: Choose your own password, account is created here ----

@auth_bp.route('/set-password', methods=['GET', 'POST'])
def set_password():
    email = session.get('pending_email')
    if not email or not session.get('email_verified'):
        return redirect(url_for('auth.signup'))

    if request.method == 'GET':
        return render_template('set_password.html',
                               email=email,
                               categories=Config.CATEGORIES,
                               category_colors=Config.CATEGORY_COLORS)

    password         = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    if len(password) < 6:
        flash('Password must be at least 6 characters.', 'error')
        return redirect(url_for('auth.set_password'))

    if password != confirm_password:
        flash('Passwords do not match.', 'error')
        return redirect(url_for('auth.set_password'))

    if User.query.filter_by(email=email).first():
        flash('An account already exists for this email. Try signing in instead.', 'error')
        return redirect(url_for('auth.login'))

    name  = session.get('pending_name')
    phone = session.get('pending_phone')

    user = User(email=email, name=name, phone=phone, is_verified=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    LoginLog.record(email=email, purpose='signup', success=True, ip_address=_client_ip(), method='otp')

    session.pop('pending_email', None)
    session.pop('pending_name', None)
    session.pop('pending_phone', None)
    session.pop('email_verified', None)

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
        LoginLog.record(email=email, purpose='login', success=False, ip_address=ip, method='password')
        flash('Incorrect email or password.', 'error')
        return redirect(url_for('auth.login', next=next_url))

    LoginLog.record(email=email, purpose='login', success=True, ip_address=ip, method='password')
    _log_in_user(user, remember=remember)
    return redirect(next_url)


# -- Logout ------------------------------------------------------

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.permanent = False
    return redirect(url_for('main.index'))


# -- Change password (for logged-in users) --------------------------

@auth_bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)

    if request.method == 'GET':
        return render_template('change_password.html',
                               categories=Config.CATEGORIES,
                               category_colors=Config.CATEGORY_COLORS)

    current_password = request.form.get('current_password', '')
    new_password     = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not user.check_password(current_password):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('auth.change_password'))

    if len(new_password) < 6:
        flash('New password must be at least 6 characters.', 'error')
        return redirect(url_for('auth.change_password'))

    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('auth.change_password'))

    user.set_password(new_password)
    db.session.commit()
    flash('Password updated successfully.', 'success')
    return redirect(url_for('main.index'))


# -- Forgot password: request OTP -----------------------------------

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('forgot_password.html',
                               categories=Config.CATEGORIES,
                               category_colors=Config.CATEGORY_COLORS)

    email = request.form.get('email', '').strip().lower()
    user = User.query.filter_by(email=email).first()

    if not user:
        flash('No account found with that email.', 'error')
        return redirect(url_for('auth.forgot_password'))

    otp = OTPCode.generate(email, purpose='reset')
    sent = send_otp_email(email, otp.code, purpose='reset')
    if not sent:
        flash('Could not send code. Try again shortly.', 'error')
        return redirect(url_for('auth.forgot_password'))

    session['reset_email'] = email
    return redirect(url_for('auth.reset_password'))


# -- Forgot password: verify OTP + set new password ------------------

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    email = session.get('reset_email')
    if not email:
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'GET':
        return render_template('reset_password.html',
                               email=email,
                               categories=Config.CATEGORIES,
                               category_colors=Config.CATEGORY_COLORS)

    code             = request.form.get('code', '').strip()
    new_password     = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    otp = (OTPCode.query
           .filter_by(email=email, code=code, purpose='reset', used=False)
           .order_by(OTPCode.created_at.desc())
           .first())

    if not otp or not otp.is_valid():
        flash('Invalid or expired code.', 'error')
        return redirect(url_for('auth.reset_password'))

    if len(new_password) < 6:
        flash('Password must be at least 6 characters.', 'error')
        return redirect(url_for('auth.reset_password'))

    if new_password != confirm_password:
        flash('Passwords do not match.', 'error')
        return redirect(url_for('auth.reset_password'))

    otp.used = True
    user = User.query.filter_by(email=email).first()
    user.set_password(new_password)
    db.session.commit()

    session.pop('reset_email', None)
    flash('Password reset. You can log in now.', 'success')
    return redirect(url_for('auth.login'))


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
