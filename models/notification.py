from datetime import datetime
from extensions import db
from utils.timezone_utils import now_ist

class AdminNotification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: now_ist().replace(tzinfo=None))
    
    admin = db.relationship('User', backref='notifications')
    task = db.relationship('Task', backref='notifications')