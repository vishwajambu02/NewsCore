class LoginLog(db.Model):
    """Every login/signup attempt — visible to the admin (you) in the dashboard."""
    __tablename__ = 'login_logs'

    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(300), nullable=False, index=True)
    method     = db.Column(db.String(20), default='password')
    purpose    = db.Column(db.String(20), default='login')  # 'login' or 'signup'
    success    = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(64))
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def record(email, purpose, success, ip_address=None, method='password'):
        entry = LoginLog(
            email=email,
            method=method,
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
