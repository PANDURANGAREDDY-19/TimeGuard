from datetime import datetime
from app import db

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    estimated_time = db.Column(db.Float)  
    actual_time = db.Column(db.Float)  
    status = db.Column(db.String(20), default='pending')  
    priority = db.Column(db.String(10), default='medium') 
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def duration_minutes(self):
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() / 60
        return 0
    
    def is_overdue(self):
        if self.estimated_time and self.actual_time:
            return self.actual_time > self.estimated_time * 1.2  