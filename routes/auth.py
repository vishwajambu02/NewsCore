"""
routes/auth.py
──────────────
Two separate entry points, both ending in an email OTP check:

- /login   → "Sign in with Email" — just an email, nothing else. Fastest path.
             Creates a bare account (email only) automatically if none exists.
- /signup  → "Create Your Own Account" — collects name, phone number, email.
             Saves that profile info once the OTP is verified.

Both funnel through the same /verify page and OTPCode model, but they are
independent flows — using one doesn't require or touch the other.
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


# ── Create Your Own Account (name + phone + email) ──────────────

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

    # Stash the profile info until the OTP is confirmed — nothing is
    # written to the User table until then.
    session['pending_email'] = email
    session['pending_name']  = name
    session['pending_phone'] = phone
    return redirect(url_for('auth.verify', purpose='signup'))


# ── Sign in with Email (email only, no profile info) ─────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        next_url = request.args.get('next', '')
        return render_template('login.html',
                               next_url=next_url,
                               categories=Config.CATEGORIES,
                               category_colors=Config.CATEGORY_COLORS)

    email = request.form.get('email', '').strip().lower()
    remember = request.form.get('remember') == 'on'
    next_url = request.form.get('next', '') or url_for('main.index')

    if not email or '@' not in email:
        flash('Enter a valid email.', 'error')
        return redirect(url_for('auth.login'))

    otp = OTPCode.generate(email, purpose='login')
    sent = send_otp_email(email, otp.code, purpose='login')
    if not sent:
        flash('Could not send code. Try again shortly.', 'error')
        return redirect(url_for('auth.login'))

    session['pending_email'] = email
    session['pending_next'] = next_url
    session['pending_remember'] = remember
    return redirect(url_for('auth.verify', purpose='login'))


# ── OTP send (AJAX, kept for resend-code use) ───────────────────

@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip().lower()
    purpose = data.get('purpose', 'login')

    if not email or '@' not in email:
        return jsonify({'error': 'Invalid email'}), 400

    if purpose == 'signup' and User.query.filter_by(email=email).first():
        return jsonify({'error': 'Account already exists'}), 400

    otp = OTPCode.generate(email, purpose=purpose)
    sent = send_otp_email(email, otp.code, purpose=purpose)
    if not sent:
        return jsonify({'error': 'Failed to send code'}), 500

    session['pending_email'] = email
    return jsonify({'ok': True})


# ── OTP verify page + handler (shared by both flows) ─────────────

@auth_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    email = session.get('pending_email')
    if not email:
        return redirect(url_for('auth.login'))

    if request.method == 'GET':
        purpose = request.args.get('purpose', 'login')
        return render_template('verify_otp.html',
                               email=email,
                               purpose=purpose,
                               categories=Config.CATEGORIES,
                               category_colors=Config.CATEGORY_COLORS)

    code = request.form.get('code', '').strip()
    purpose = request.form.get('purpose', 'login')
    ip = _client_ip()

    otp = (OTPCode.query
           .filter_by(email=email, code=code, purpose=purpose, used=False)
           .order_by(OTPCode.created_at.desc())
           .first())

    if not otp or not otp.is_valid():
        LoginLog.record(email=email, purpose=purpose, success=False, ip_address=ip)
        flash('Invalid or expired code.', 'error')
        return redirect(url_for('auth.verify', purpose=purpose))

    otp.used = True

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, is_verified=True)
        db.session.add(user)
    else:
        user.is_verified = True

    # Only the signup flow carries name/phone — apply them if present.
    pending_name  = session.pop('pending_name', None)
    pending_phone = session.pop('pending_phone', None)
    if pending_name:
        user.name = pending_name
    if pending_phone:
        user.phone = pending_phone

    db.session.commit()

    LoginLog.record(email=email, purpose=purpose, success=True, ip_address=ip)

    session.pop('pending_remember', None)
    session.permanent = True

    session['user_id'] = user.id
    session.pop('pending_email', None)
    next_url = session.pop('pending_next', None) or url_for('main.index')
    return redirect(next_url)


# ── Logout ────────────────────────────────────────────────────

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.permanent = False
    return redirect(url_for('main.index'))


# ── Digest signup page (unchanged) ──────────────────────────────

@auth_bp.route('/digest')
def digest():
    return render_template(
        'digest_signup.html',
        categories=Config.CATEGORIES,
        category_colors=Config.CATEGORY_COLORS,
    )


# ── Unsubscribe (unchanged) ──────────────────────────────────────

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


# ── Guest category preference (unchanged) ────────────────────────

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