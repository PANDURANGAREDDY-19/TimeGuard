from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from extensions import db
from utils.timezone_utils import now_ist

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    profile_photo = db.Column(db.String(255), default='default.jpg')
    created_at = db.Column(db.DateTime, default=lambda: now_ist().replace(tzinfo=None))
    
    tasks = db.relationship('Task', foreign_keys='Task.user_id', backref='user', lazy=True, cascade='all, delete-orphan')
    assigned_tasks = db.relationship('Task', foreign_keys='Task.assigned_by', backref='assigner', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
