#!/usr/bin/env python3
"""
Migration script to convert existing UTC timestamps to IST in the database.
This script should be run once after implementing IST timezone support.
"""

from app import create_app
from extensions import db
from models.user import User
from models.task import Task
from models.password_reset import PasswordReset
from models.notification import AdminNotification
from models.registration_otp import RegistrationOTP
from utils.timezone_utils import utc_to_ist
from datetime import timezone

def migrate_timestamps():
    app = create_app()
    
    with app.app_context():
        print("Starting IST migration...")
        
        # Update User timestamps
        users = User.query.all()
        for user in users:
            if user.created_at and user.created_at.tzinfo is None:
                # Assume existing timestamps are UTC and convert to IST
                user.created_at = utc_to_ist(user.created_at.replace(tzinfo=timezone.utc)).replace(tzinfo=None)
        
        # Update Task timestamps
        tasks = Task.query.all()
        for task in tasks:
            if task.created_at and task.created_at.tzinfo is None:
                task.created_at = utc_to_ist(task.created_at.replace(tzinfo=timezone.utc)).replace(tzinfo=None)
            if task.started_at and task.started_at.tzinfo is None:
                task.started_at = utc_to_ist(task.started_at.replace(tzinfo=timezone.utc)).replace(tzinfo=None)
            if task.completed_at and task.completed_at.tzinfo is None:
                task.completed_at = utc_to_ist(task.completed_at.replace(tzinfo=timezone.utc)).replace(tzinfo=None)
            if task.deadline and task.deadline.tzinfo is None:
                task.deadline = utc_to_ist(task.deadline.replace(tzinfo=timezone.utc)).replace(tzinfo=None)
        
        # Update PasswordReset timestamps
        resets = PasswordReset.query.all()
        for reset in resets:
            if reset.created_at and reset.created_at.tzinfo is None:
                reset.created_at = utc_to_ist(reset.created_at.replace(tzinfo=timezone.utc)).replace(tzinfo=None)
            if reset.expires_at and reset.expires_at.tzinfo is None:
                reset.expires_at = utc_to_ist(reset.expires_at.replace(tzinfo=timezone.utc)).replace(tzinfo=None)
        
        # Update AdminNotification timestamps
        notifications = AdminNotification.query.all()
        for notification in notifications:
            if notification.created_at and notification.created_at.tzinfo is None:
                notification.created_at = utc_to_ist(notification.created_at.replace(tzinfo=timezone.utc)).replace(tzinfo=None)
        
        # Update RegistrationOTP timestamps
        otps = RegistrationOTP.query.all()
        for otp in otps:
            if otp.created_at and otp.created_at.tzinfo is None:
                otp.created_at = utc_to_ist(otp.created_at.replace(tzinfo=timezone.utc)).replace(tzinfo=None)
            if otp.expires_at and otp.expires_at.tzinfo is None:
                otp.expires_at = utc_to_ist(otp.expires_at.replace(tzinfo=timezone.utc)).replace(tzinfo=None)
        
        # Commit all changes
        db.session.commit()
        print(f"Migration completed successfully!")
        print(f"Updated {len(users)} users, {len(tasks)} tasks, {len(resets)} password resets,")
        print(f"{len(notifications)} notifications, and {len(otps)} registration OTPs")

if __name__ == '__main__':
    migrate_timestamps()