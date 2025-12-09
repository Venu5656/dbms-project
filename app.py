import os
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, g
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from middleware import log_activity, setup_activity_logging
from extensions import db, migrate
from models import User, Goal, Transaction, SavingsRule, ActivityLog, ExpenseCategory, UserSession

# Import config (single source of truth)
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.environ.get('SECRET_KEY') or 'dev-secret-key'

# Import models after db is defined
from models import User, Goal, Transaction, SavingsRule, ExpenseCategory, UserSession, ActivityLog

# Initialize extensions
db.init_app(app)
migrate.init_app(app, db)

# Set up activity logging
setup_activity_logging(app)

# Create tables and seed a default demo user (for local development)
with app.app_context():
    db.create_all()

    # Ensure a demo user exists for quick login
    demo_username = 'gowrisankar'
    demo_email = 'gowrisankar@example.com'
    demo_password = 'pass'

    existing_demo = User.query.filter_by(username=demo_username).first()
    if not existing_demo:
        demo_user = User(
            username=demo_username,
            email=demo_email,
            password_hash=generate_password_hash(demo_password)
        )
        db.session.add(demo_user)
        db.session.commit()

# Helper functions
def decimalize(value):
    """Convert value to Decimal if it's not already."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value)) if value is not None else None

def add_tx(goal_id, amount, tx_type, description=None, user_id=None, is_undoable=True):
    """Add a new transaction."""
    if not user_id and 'user_id' in session:
        user_id = session['user_id']
    
    tx = Transaction(
        user_id=user_id,
        goal_id=goal_id,
        amount=amount,
        transaction_type=tx_type,
        description=description,
        is_undoable=is_undoable
    )
    db.session.add(tx)
    return tx

def apply_saving_to_goal(goal, amount):
    """Apply savings to a goal."""
    goal.current_amount += decimalize(amount)
    
    # Check if goal is completed
    if goal.current_amount >= goal.target_amount and not goal.completed_at:
        goal.completed_at = datetime.utcnow()
    
    return goal

# Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/home')
def home_landing():
    """Public marketing homepage with animations and product overview."""
    return render_template('home.html')

@app.route('/goals/<int:goal_id>')
def goal_detail(goal_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    goal = Goal.query.filter_by(id=goal_id, user_id=session['user_id']).first_or_404()
    return render_template('goal.html', goal_id=goal.id)

@app.route('/debug/users')
def debug_users():
    """Debug endpoint to check users in database"""
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'email': u.email
    } for u in users])

@app.route('/api/goals', methods=['GET'])
@log_activity
def get_goals():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    goals = Goal.query.filter_by(user_id=session['user_id'], is_active=True).all()
    return jsonify([{
        'id': g.id,
        'name': g.name,
        'target_amount': float(g.target_amount) if g.target_amount else None,
        'current_amount': float(g.current_amount) if g.current_amount else 0.0,
        'progress': float(g.current_amount / g.target_amount * 100) if g.target_amount else 0.0,
        'description': g.description,
        'image_url': g.image_url,
        'savings_pace': g.savings_pace
    } for g in goals])

@app.route('/api/goals/<int:goal_id>', methods=['GET'])
@log_activity
def get_goal(goal_id):
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    goal = Goal.query.filter_by(id=goal_id, user_id=session['user_id']).first_or_404()
    return jsonify({
        'id': goal.id,
        'name': goal.name,
        'target_amount': float(goal.target_amount) if goal.target_amount else None,
        'current_amount': float(goal.current_amount) if goal.current_amount else 0.0,
        'progress': float(goal.current_amount / goal.target_amount * 100) if goal.target_amount else 0.0,
        'description': goal.description,
        'image_url': goal.image_url,
        'savings_pace': goal.savings_pace,
        'created_at': goal.created_at.isoformat() if goal.created_at else None,
        'completed_at': goal.completed_at.isoformat() if goal.completed_at else None
    })

@app.route('/api/transactions', methods=['GET'])
@log_activity
def get_transactions():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    transactions = Transaction.query.filter_by(user_id=session['user_id']).order_by(Transaction.created_at.desc()).limit(50).all()
    return jsonify([t.to_dict() for t in transactions])

@app.route('/api/goals/<int:goal_id>/transactions', methods=['GET'])
@log_activity
def get_goal_transactions(goal_id):
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    goal = Goal.query.filter_by(id=goal_id, user_id=session['user_id']).first_or_404()
    transactions = Transaction.query.filter_by(user_id=session['user_id'], goal_id=goal.id).order_by(Transaction.created_at.asc()).all()
    return jsonify([t.to_dict() for t in transactions])

@app.route('/api/savings-rules', methods=['GET'])
@log_activity
def get_savings_rules():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    rules = SavingsRule.query.filter_by(user_id=session['user_id'], is_active=True).all()
    return jsonify([r.to_dict() for r in rules])

@app.route('/api/goals/create', methods=['POST'])
@log_activity
def create_goal():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    data = request.get_json()
    
    goal = Goal(
        user_id=session['user_id'],
        name=data['name'],
        target_amount=decimalize(data['target_amount']),
        current_amount=Decimal('0.00'),
        savings_pace=data.get('savings_pace', 'Moderate'),
        description=data.get('description'),
        image_url=data.get('image_url'),
        is_active=True
    )
    
    db.session.add(goal)
    db.session.commit()
    
    return jsonify({"message": "Goal created successfully", "goal_id": goal.id}), 201

@app.route('/api/rules/create', methods=['POST'])
@log_activity
def create_rule():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    data = request.get_json()
    
    rule = SavingsRule(
        user_id=session['user_id'],
        goal_id=data['goal_id'],
        rule_type=data['rule_type'],
        rule_name=data['rule_name'],
        amount=decimalize(data['amount']),
        frequency=data.get('frequency'),
        trigger_category=data.get('trigger_category'),
        is_active=True
    )
    
    db.session.add(rule)
    db.session.commit()
    
    return jsonify({"message": "Rule created successfully", "rule_id": rule.id}), 201

@app.route('/api/rules/<int:rule_id>', methods=['PUT', 'PATCH'])
@log_activity
def update_rule(rule_id):
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    rule = SavingsRule.query.filter_by(id=rule_id, user_id=session['user_id']).first()
    if not rule:
        return jsonify({"error": "Rule not found"}), 404

    data = request.get_json() or {}

    if 'rule_name' in data:
        rule.rule_name = data['rule_name']
    if 'amount' in data and data['amount'] is not None:
        rule.amount = decimalize(data['amount'])
    if 'frequency' in data:
        rule.frequency = data['frequency'] or None
    if 'trigger_category' in data:
        rule.trigger_category = data['trigger_category'] or None

    db.session.commit()

    return jsonify({
        "message": "Rule updated successfully",
        "rule": rule.to_dict()
    })

@app.route('/api/goals/<int:goal_id>/contribute', methods=['POST'])
@log_activity
def contribute_to_goal(goal_id):
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    goal = Goal.query.filter_by(id=goal_id, user_id=session['user_id']).first_or_404()
    data = request.get_json() or {}

    amount = data.get('amount')
    investment_type = data.get('investment_type') or 'manual'

    if amount is None:
        return jsonify({"error": "Amount is required"}), 400

    amount_dec = decimalize(amount)
    if amount_dec <= Decimal('0'):
        return jsonify({"error": "Amount must be positive"}), 400

    tx_type = investment_type

    add_tx(goal.id, amount_dec, tx_type, description=None, user_id=session['user_id'])
    apply_saving_to_goal(goal, amount_dec)
    db.session.commit()

    return jsonify({
        "message": "Contribution added",
        "goal_id": goal.id,
        "current_amount": float(goal.current_amount),
        "progress": float(goal.current_amount / goal.target_amount * 100) if goal.target_amount else 0.0
    }), 201

# Habit reward endpoint
@app.route('/api/habit/<int:rule_id>/log', methods=['POST'])
@log_activity
def log_habit(rule_id):
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    rule = SavingsRule.query.get_or_404(rule_id)
    if rule.rule_type != 'habit_reward' or not rule.is_active:
        return jsonify({"error": "Invalid habit rule"}), 400
    
    amount = decimalize(rule.amount)
    add_tx(rule.goal_id, amount, 'habit_reward', description=rule.rule_name, user_id=session['user_id'])
    
    goal = Goal.query.get(rule.goal_id)
    apply_saving_to_goal(goal, amount)
    db.session.commit()
    
    return jsonify({
        "message": "Habit logged", 
        "added": float(amount), 
        "goal_balance": float(goal.current_amount)
    })

# Recurring savings execution
@app.route('/recurring/run', methods=['POST'])
def recurring_run():
    now = datetime.utcnow()
    executed = []

    def due(rule: SavingsRule) -> bool:
        if not rule.last_executed:
            return True
        delta = now - rule.last_executed
        if rule.frequency == 'daily':
            return delta >= timedelta(days=1)
        if rule.frequency == 'weekly':
            return delta >= timedelta(weeks=1)
        if rule.frequency == 'monthly':
            # naive monthly check: 28 days cadence
            return delta >= timedelta(days=28)
        return False

    rules = SavingsRule.query.filter_by(rule_type='recurring', is_active=True).all()
    for r in rules:
        if due(r):
            amount = decimalize(r.amount)
            add_tx(r.goal_id, amount, 'recurring', description=r.rule_name, user_id=r.user_id)
            goal = Goal.query.get(r.goal_id)
            apply_saving_to_goal(goal, amount)
            r.last_executed = now
            executed.append(r.id)

    db.session.commit()
    return jsonify({"message": "Recurring processed", "executed_rule_ids": executed})

# Undo a transaction
@app.route('/api/transactions/<int:tx_id>/undo', methods=['POST'])
@log_activity
def undo(tx_id):
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    tx = Transaction.query.get_or_404(tx_id)
    if not tx.is_undoable:
        return jsonify({"error": "Transaction not undoable"}), 400
    
    # Create a compensating transaction
    neg_amount = decimalize(tx.amount) * Decimal('-1')
    add_tx(tx.goal_id, neg_amount, 'undo', 
          description=f"Undo #{tx.id}", 
          user_id=session['user_id'],
          is_undoable=False)
    
    # Update the goal balance
    goal = Goal.query.get(tx.goal_id)
    apply_saving_to_goal(goal, neg_amount)
    
    # Mark original transaction as undone
    tx.is_undoable = False
    db.session.commit()
    
    return jsonify({
        "message": "Transaction undone", 
        "goal_balance": float(goal.current_amount)
    })

# Authentication routes (simplified for demo)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        error = None

        if not username or not email or not password:
            error = 'All fields are required.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        else:
            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()
            if existing_user:
                error = 'Username or email already in use.'

        if error:
            return f"<p>{error}</p>", 400

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"Login attempt - Username: {username}, Password: {password}")
        print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # Check total users
        total_users = User.query.count()
        print(f"Total users in database: {total_users}")
        
        all_users = User.query.all()
        print(f"All usernames: {[u.username for u in all_users]}")
        
        user = User.query.filter_by(username=username).first()
        
        if user:
            print(f"User found: {user.username}")
            print(f"Password hash: {user.password_hash}")
            password_valid = check_password_hash(user.password_hash, password)
            print(f"Password valid: {password_valid}")
            
            if password_valid:
                session['user_id'] = user.id
                print(f"Login successful for user {user.id}")
                return redirect(url_for('index'))
        else:
            print("User not found")
        
        return "Invalid credentials", 401
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Initialize database
@app.cli.command('init-db')
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Initialized the database.')

@app.cli.command('cleanup-manual-contributions')
def cleanup_manual_contributions():
    """Remove legacy manual_contribution transactions and adjust goal balances."""
    with app.app_context():
        txs = Transaction.query.filter_by(transaction_type='manual_contribution').all()
        count = len(txs)

        for tx in txs:
            goal = Goal.query.get(tx.goal_id)
            if goal and tx.amount is not None:
                try:
                    goal.current_amount = (goal.current_amount or Decimal('0')) - tx.amount
                except Exception:
                    # Fallback without Decimal if needed
                    goal.current_amount = goal.current_amount - tx.amount

        Transaction.query.filter_by(transaction_type='manual_contribution').delete(synchronize_session=False)
        db.session.commit()
        print(f"Removed {count} manual_contribution transactions and updated goal balances.")

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))