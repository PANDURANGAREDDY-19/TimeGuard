from datetime import datetime, timedelta
from extensions import db
from utils.timezone_utils import now_ist
import random
import string

class RegistrationOTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: now_ist().replace(tzinfo=None))
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    
    def __init__(self, email, username, password_hash):
        self.email = email
        self.username = username
        self.password_hash = password_hash
        self.otp_code = ''.join(random.choices(string.digits, k=6))
        self.expires_at = now_ist().replace(tzinfo=None) + timedelta(minutes=10)
    
    def is_valid(self):
        return not self.is_used and now_ist().replace(tzinfo=None) < self.expires_at
    
    def mark_used(self):
        self.is_used = True
        db.session.commit()