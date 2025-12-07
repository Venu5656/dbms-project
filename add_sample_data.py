from app import app, db
from models import User, Goal, Transaction, SavingsRule, ExpenseCategory
from datetime import datetime, timedelta

def add_sample_data():
    with app.app_context():
        # Create test user if not exists
        user = User.query.filter_by(username='testuser').first()
        if not user:
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash='hashed_password_here'  # In production, use proper hashing
            )
            db.session.add(user)
            db.session.commit()
            print("Created test user")
        
        # Create a savings goal
        goal = Goal.query.filter_by(name='New Laptop').first()
        if not goal:
            goal = Goal(
                user_id=user.id,
                name='New Laptop',
                target_amount=1200.00,
                current_amount=350.00,
                savings_pace='Moderate',
                description='Saving for a new laptop',
                is_active=True
            )
            db.session.add(goal)
            db.session.commit()
            print("Created sample goal")
        
        # Add a transaction
        transaction = Transaction.query.filter_by(description='Initial deposit').first()
        if not transaction:
            transaction = Transaction(
                user_id=user.id,
                goal_id=goal.id,
                amount=100.00,
                transaction_type='deposit',
                description='Initial deposit',
                created_at=datetime.utcnow() - timedelta(days=5)
            )
            db.session.add(transaction)
            db.session.commit()
            print("Added sample transaction")
        
        print("Sample data added successfully!")

if __name__ == '__main__':
    add_sample_data()
