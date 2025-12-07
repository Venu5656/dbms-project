import os
from app import app, db
from models import User, Goal, Transaction, SavingsRule, ExpenseCategory, UserSession, ActivityLog
from datetime import datetime, timedelta

def init_db():
    print("Initializing database...")
    
    with app.app_context():
        # Drop all tables and recreate them
        print("Dropping all tables...")
        db.drop_all()
        
        print("Creating all tables...")
        db.create_all()
        print("Tables created successfully!")
        
        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("Creating admin user...")
            from werkzeug.security import generate_password_hash
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123', method='pbkdf2:sha256')
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created with username: admin, password: admin123")
        else:
            print("Admin user already exists")
        
        print("Database initialization complete!")

if __name__ == '__main__':
    init_db()
