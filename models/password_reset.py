from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from extensions import db
from utils.timezone_utils import now_ist
import random
import string

class PasswordReset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: now_ist().replace(tzinfo=None))
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref='password_resets')
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.otp_code = ''.join(random.choices(string.digits, k=6))
        self.expires_at = now_ist().replace(tzinfo=None) + timedelta(minutes=10)
    
    def is_valid(self):
        return not self.is_used and now_ist().replace(tzinfo=None) < self.expires_at
    
    def mark_used(self):
        self.is_used = True
        db.session.commit()
    
    def belongs_to_user(self, user_id):
        """Verify OTP belongs to specific user"""
        return self.user_id == user_id and self.is_valid()