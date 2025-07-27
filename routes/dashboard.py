from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.user import User
from models.task import Task
from app import db
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('dashboard.user'))
    
    users = User.query.all()
    total_tasks = Task.query.count()
    completed_tasks = Task.query.filter_by(status='completed').count()
    
    # Recent activity
    recent_tasks = Task.query.order_by(Task.created_at.desc()).limit(10).all()
    
    return render_template('dashboard/admin.html', 
                         users=users, 
                         total_tasks=total_tasks,
                         completed_tasks=completed_tasks,
                         recent_tasks=recent_tasks,
                         Task=Task)

@dashboard_bp.route('/user')
@login_required
def user():
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.created_at.desc()).all()
    
    # Statistics
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.status == 'completed'])
    pending_tasks = len([t for t in tasks if t.status == 'pending'])
    
    return render_template('dashboard/user.html',
                         tasks=tasks,
                         total_tasks=total_tasks,
                         completed_tasks=completed_tasks,
                         pending_tasks=pending_tasks)

@dashboard_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.username = request.form['username']
        current_user.email = request.form['email']
        current_user.theme_preference = request.form['theme']
        
        # Handle profile photo upload
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and file.filename:
                filename = secure_filename(f"{current_user.id}_{file.filename}")
                file.save(os.path.join('static/uploads', filename))
                current_user.profile_photo = filename
        
        db.session.commit()
        flash('Profile updated successfully')
    
    return render_template('dashboard/profile.html')