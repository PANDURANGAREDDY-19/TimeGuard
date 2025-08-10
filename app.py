
from flask import Flask, redirect, url_for
from flask_login import current_user
from config import Config
from extensions import db, login_manager, migrate
from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app
import atexit

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Import models to register user_loader
    from models.user import User
    from models.task import Task
    
    # Register user_loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.api import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Root route
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.admin' if current_user.is_admin else 'dashboard.user'))
        return redirect(url_for('auth.login'))
    

    # --- APScheduler: Weekly Summary Email Job ---
    from models.user import User
    from models.task import Task
    from utils.email_utils import send_weekly_summary_email
    def send_weekly_summaries():
        with app.app_context():
            users = User.query.all()
            for user in users:
                tasks = Task.query.filter_by(user_id=user.id).all()
                try:
                    send_weekly_summary_email(user, tasks)
                except Exception as e:
                    print(f"[SCHEDULER ERROR] Could not send summary to {user.email}: {e}")

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=send_weekly_summaries, trigger='cron', day_of_week='mon', hour=8, minute=0)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)