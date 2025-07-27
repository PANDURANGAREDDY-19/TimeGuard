
from app import create_app, db

app = create_app()

with app.app_context():
    from models.user import User
    from models.task import Task
    # Drop all tables and recreate (for development)
    try:
        db.drop_all()
    except Exception as e:
        print(f"Warning: {e}")
        # Force drop with raw SQL if needed
        db.session.execute(db.text("DROP SCHEMA public CASCADE;"))
        db.session.execute(db.text("CREATE SCHEMA public;"))
        db.session.commit()
    
    db.create_all()
    
    # Create admin user
    admin = User(
        username='admin',
        email='admin@timeguard.com',
        is_admin=True
    )
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print("Admin user created: admin/admin123")
    
    print("Database initialized successfully!")