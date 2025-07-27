
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.task import Task
from models.user import User
from ml.time_predictor import TimePredictor
from app import db
from datetime import datetime

api_bp = Blueprint('api', __name__)
predictor = TimePredictor()

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
            'created_at': t.created_at.strftime('%Y-%m-%d %H:%M'),
            'started_at': t.started_at.strftime('%Y-%m-%d %H:%M') if t.started_at else '',
            'completed_at': t.completed_at.strftime('%Y-%m-%d %H:%M') if t.completed_at else '',
            'actual_time': t.actual_time
        })
    return jsonify(result)

@api_bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    data = request.json
    try:
        if not data or 'title' not in data or not data['title']:
            return jsonify({'error': 'Task title is required'}), 400

        # Get ML prediction
        estimated_time = predictor.predict(data, current_user)

        task = Task(
            title=data['title'],
            description=data.get('description', ''),
            category=data.get('category', 'general'),
            priority=data.get('priority', 'medium'),
            estimated_time=estimated_time,
            user_id=current_user.id
        )

        db.session.add(task)
        db.session.commit()

        return jsonify({
            'id': task.id,
            'estimated_time': estimated_time,
            'message': 'Task created successfully'
        })
    except Exception as e:
        db.session.rollback()
        import traceback
        print('Error creating task:', e)
        traceback.print_exc()
        return jsonify({'error': 'Failed to create task', 'details': str(e)}), 500

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
    task.completed_at = datetime.utcnow()
    
    db.session.commit()
    
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