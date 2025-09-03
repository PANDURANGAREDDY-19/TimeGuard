
from flask import Blueprint, request, jsonify, render_template_string
from flask_login import login_required, current_user
from models.task import Task
from models.user import User
from models.notification import AdminNotification
from ml.time_predictor import TimePredictor
from app import db
from datetime import datetime
from utils.timezone_utils import now_ist, format_ist_datetime
from utils.email_utils import send_task_history_email, generate_task_history_text, send_task_completion_alert

api_bp = Blueprint('api', __name__)
predictor = TimePredictor()

# Send user task history to their email (admin only)
@api_bp.route('/tasks/user/<int:user_id>/send_history', methods=['POST'])
@login_required
def send_user_task_history(user_id):
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Access denied'}), 403
        user = User.query.get_or_404(user_id)
        tasks = Task.query.filter_by(user_id=user.id).order_by(Task.created_at.desc()).all()
        text = generate_task_history_text(user, tasks)
        send_task_history_email(user.email, f"Your Task History - {user.username}", text)
        return jsonify({'message': f'Task history sent to {user.email}.'})
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@api_bp.route('/analytics/activity/weekly')
@login_required
def weekly_activity():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    from collections import defaultdict
    import calendar
    # Map: weekday (0=Mon) -> {'total_time': float, 'task_count': int}
    stats = defaultdict(lambda: {'total_time': 0.0, 'task_count': 0})
    tasks = Task.query.filter(Task.completed_at != None).all()
    for t in tasks:
        weekday = t.completed_at.weekday()  # 0=Mon
        stats[weekday]['total_time'] += t.actual_time or 0
        stats[weekday]['task_count'] += 1
    # Prepare ordered result for Mon-Sun
    result = []
    for i in range(7):
        result.append({
            'day': calendar.day_name[i],
            'total_time': round(stats[i]['total_time'], 2),
            'task_count': stats[i]['task_count']
        })
    return jsonify(result)

@api_bp.route('/tasks/user/<int:user_id>/history')
@login_required
def user_task_history(user_id):
    if not current_user.is_admin and current_user.id != user_id:
        return jsonify({'error': 'Access denied'}), 403
    user = User.query.get_or_404(user_id)
    tasks = Task.query.filter_by(user_id=user.id).order_by(Task.created_at.desc()).all()
    result = []
    for t in tasks:
        result.append({
            'id': t.id,
            'title': t.title,
            'status': t.status,
            'priority': t.priority,
            'category': t.category,
            'created_at': format_ist_datetime(t.created_at),
            'started_at': format_ist_datetime(t.started_at),
            'completed_at': format_ist_datetime(t.completed_at),
            'actual_time': t.actual_time
        })
    return jsonify(result)

@api_bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    try:
        data = request.get_json()
        if not data or not data.get('title'):
            return jsonify({'error': 'Task title is required'}), 400

        task = Task(
            title=data['title'],
            description=data.get('description', ''),
            category=data.get('category', ''),
            priority=data.get('priority', 'medium'),
            estimated_time=1.0,
            user_id=current_user.id
        )

        db.session.add(task)
        db.session.commit()

        return jsonify({
            'id': task.id,
            'message': 'Task created successfully'
        })
    except Exception as e:
        db.session.rollback()
        print(f'Task creation error: {e}')
        return jsonify({'error': 'Failed to create task'}), 500

@api_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deleted successfully'})

@api_bp.route('/tasks/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    actual_time = request.json.get('actual_time')
    task.actual_time = actual_time
    task.status = 'completed'
    task.completed_at = now_ist().replace(tzinfo=None)
    
    db.session.commit()
    
    # Send notification to admin if task was assigned by admin
    if task.assigned_by:
        admin = User.query.get(task.assigned_by)
        if admin:
            # Create in-app notification
            notification = AdminNotification(
                admin_id=admin.id,
                task_id=task.id,
                message=f"{current_user.username} completed task: {task.title}"
            )
            db.session.add(notification)
            db.session.commit()
            
            # Send email alert
            try:
                send_task_completion_alert(
                    admin.email, 
                    task.title, 
                    current_user.username, 
                    task.completed_at, 
                    task.actual_time
                )
            except Exception as e:
                print(f"Failed to send completion alert: {e}")
    
    # Check for deviation
    is_deviation, deviation_percent = predictor.detect_deviation(task)
    
    # Retrain model with new data
    predictor.train(current_user.id)
    
    return jsonify({
        'message': 'Task completed',
        'deviation_detected': is_deviation,
        'deviation_percent': deviation_percent
    })

@api_bp.route('/analytics/user/<int:user_id>')
@login_required
def user_analytics(user_id):
    if not current_user.is_admin and current_user.id != user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    user = User.query.get_or_404(user_id)
    tasks = user.tasks.filter_by(status='completed').all()
    
    analytics = {
        'total_completed': len(tasks),
        'avg_completion_time': sum(t.actual_time for t in tasks) / len(tasks) if tasks else 0,
        'accuracy_rate': len([t for t in tasks if not t.is_overdue()]) / len(tasks) if tasks else 0,
        'categories': {}
    }
    
    # Category breakdown
    for task in tasks:
        cat = task.category or 'general'
        if cat not in analytics['categories']:
            analytics['categories'][cat] = {'count': 0, 'avg_time': 0}
        analytics['categories'][cat]['count'] += 1
        analytics['categories'][cat]['avg_time'] += task.actual_time
    
    for cat in analytics['categories']:
        analytics['categories'][cat]['avg_time'] /= analytics['categories'][cat]['count']
    
    return jsonify(analytics)

@api_bp.route('/notifications')
@login_required
def get_notifications():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    notifications = AdminNotification.query.filter_by(
        admin_id=current_user.id
    ).order_by(AdminNotification.created_at.desc()).limit(10).all()
    
    result = []
    for n in notifications:
        result.append({
            'id': n.id,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': format_ist_datetime(n.created_at),
            'task_title': n.task.title if n.task else 'Unknown Task'
        })
    
    return jsonify(result)

@api_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    notification = AdminNotification.query.filter_by(
        id=notification_id, admin_id=current_user.id
    ).first()
    
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'message': 'Notification marked as read'})

@api_bp.route('/notifications/unread-count')
@login_required
def unread_notifications_count():
    if not current_user.is_admin:
        return jsonify({'count': 0})
    
    count = AdminNotification.query.filter_by(
        admin_id=current_user.id, is_read=False
    ).count()
    
    return jsonify({'count': count})

@api_bp.route('/admin/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def admin_delete_task(task_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Admin can delete tasks they assigned or any completed task
        if task.assigned_by == current_user.id or task.status == 'completed':
            # Delete related notifications first
            AdminNotification.query.filter_by(task_id=task_id).delete()
            # Delete the task
            db.session.delete(task)
            db.session.commit()
            return jsonify({'message': 'Task deleted successfully'})
        else:
            return jsonify({'error': 'Cannot delete this task'}), 403
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete task'}), 500