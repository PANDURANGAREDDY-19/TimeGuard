from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.user import User
from models.task import Task
from utils.email_utils import send_task_assignment_email
from app import db
from datetime import datetime, timedelta
from utils.timezone_utils import format_ist_datetime
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
        current_user.theme_preference = request.form.get('theme', 'default')
        
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

@dashboard_bp.route('/assign-task', methods=['POST'])
@login_required
def assign_task():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    user_id = request.json.get('user_id')
    title = request.json.get('title')
    description = request.json.get('description')
    priority = request.json.get('priority', 'medium')
    category = request.json.get('category')
    deadline = request.json.get('deadline')
    
    if not user_id or not title:
        return jsonify({'success': False, 'message': 'User and title are required'})
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    if user.is_admin:
        return jsonify({'success': False, 'message': 'Cannot assign tasks to admin users'})
    
    task = Task(
        title=title,
        description=description,
        priority=priority,
        category=category,
        user_id=user_id,
        assigned_by=current_user.id
    )
    
    if deadline:
        try:
            task.deadline = datetime.strptime(deadline, '%Y-%m-%dT%H:%M')
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid deadline format'})
    
    db.session.add(task)
    db.session.commit()
    
    # Send email notification
    try:
        send_task_assignment_email(user.email, task.title, task.deadline)
    except Exception as e:
        print(f"Failed to send email notification: {e}")
    
    return jsonify({'success': True, 'message': f'Task assigned to {user.username}'})

@dashboard_bp.route('/assigned-tasks')
@login_required
def assigned_tasks():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('dashboard.user'))
    
    tasks = Task.query.filter(Task.assigned_by == current_user.id).order_by(Task.created_at.desc()).all()
    return render_template('dashboard/assigned_tasks.html', tasks=tasks)