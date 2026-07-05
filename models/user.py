from datetime import datetime, timedelta
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
import random


class EmailSubscriber(db.Model):
    __tablename__ = 'email_subscribers'

    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(300), unique=True, nullable=False)
    categories    = db.Column(db.String(500), default='World')
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    active        = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Subscriber {self.email}>'


class AdminLog(db.Model):
    __tablename__ = 'admin_logs'

    id         = db.Column(db.Integer, primary_key=True)
    action     = db.Column(db.String(500))
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow)
    detail     = db.Column(db.Text)

    def __repr__(self):
        return f'<AdminLog {self.action}>'


class User(db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(300), unique=True, nullable=False, index=True)

    # Only populated when someone goes through "Create Your Own Account" —
    # left null for people who just used quick "Sign in with Email".
    name          = db.Column(db.String(200), nullable=True)
    phone         = db.Column(db.String(30), nullable=True)

    # kept for backward compatibility with any pre-OTP accounts — unused
    # for new signups, never required to log in.
    password_hash = db.Column(db.String(300), nullable=True)

    is_verified   = db.Column(db.Boolean, default=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'


class OTPCode(db.Model):
    __tablename__ = 'otp_codes'

    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(300), nullable=False, index=True)
    code       = db.Column(db.String(10), nullable=False)
    purpose    = db.Column(db.String(20), default='login')  # 'login' or 'signup'
    expires_at = db.Column(db.DateTime, nullable=False)
    used       = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def generate(email, purpose='login'):
        code = f'{random.randint(0, 999999):06d}'
        otp = OTPCode(
            email=email,
            code=code,
            purpose=purpose,
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        db.session.add(otp)
        db.session.commit()
        return otp

    def is_valid(self):
        return (not self.used) and datetime.utcnow() < self.expires_at


class LoginLog(db.Model):
    """Every login/signup attempt — visible to the admin (you) in the dashboard."""
    __tablename__ = 'login_logs'

    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(300), nullable=False, index=True)
    method     = db.Column(db.String(20), default='otp')
    purpose    = db.Column(db.String(20), default='login')  # 'login' or 'signup'
    success    = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(64))
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def record(email, purpose, success, ip_address=None):
        entry = LoginLog(
            email=email,
            purpose=purpose,
            success=success,
            ip_address=ip_address,
        )
        db.session.add(entry)
        db.session.commit()
        return entry

    def __repr__(self):
        status = 'OK' if self.success else 'FAIL'
        return f'<LoginLog {self.email} {self.purpose} {status}>'


class SiteStat(db.Model):
    """Single-row table tracking total site page views."""
    __tablename__ = 'site_stats'

    id           = db.Column(db.Integer, primary_key=True)
    total_visits = db.Column(db.Integer, default=0)

    @staticmethod
    def increment():
        stat = SiteStat.query.first()
        if not stat:
            stat = SiteStat(total_visits=1)
            db.session.add(stat)
        else:
            stat.total_visits += 1
        db.session.commit()

    @staticmethod
    def get_total():
        stat = SiteStat.query.first()
        return stat.total_visits if stat else 0