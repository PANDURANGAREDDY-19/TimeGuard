from app import create_app
from extensions import db
from models.password_reset import PasswordReset

app = create_app()

with app.app_context():
    db.create_all()
    print("Password reset table created successfully!")