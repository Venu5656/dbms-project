import os
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash

# Import models and config
try:
    from models import db, User, Goal, Transaction, SavingsRule, ExpenseCategory, UserSession
    from config_fixed import config as Config
    print("Using fixed config")
except ImportError:
    # Fallback for local development
    from config import Config
    from models import db, User, Goal, Transaction, SavingsRule, ExpenseCategory, UserSession

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.environ.get('SECRET_KEY') or 'dev-secret-key'

# Initialize the database
db.init_app(app)
migrate = Migrate(app, db)

# Create tables if they don't exist (for local development)
with app.app_context():
    db.create_all()

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
        'image_url': g.image_url
    } for g in goals])

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    transactions = Transaction.query.filter_by(user_id=session['user_id']).order_by(Transaction.created_at.desc()).limit(50).all()
    return jsonify([t.to_dict() for t in transactions])

@app.route('/api/savings-rules', methods=['GET'])
def get_savings_rules():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    rules = SavingsRule.query.filter_by(user_id=session['user_id'], is_active=True).all()
    return jsonify([r.to_dict() for r in rules])

@app.route('/api/goals/create', methods=['POST'])
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

# Habit reward endpoint
@app.route('/api/habit/<int:rule_id>/log', methods=['POST'])
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
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Milestone Savings App</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .login-container {
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                width: 300px;
            }
            h2 {
                margin-top: 0;
                color: #333;
                text-align: center;
            }
            input {
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                border: 1px solid #ddd;
                border-radius: 5px;
                box-sizing: border-box;
                font-size: 14px;
            }
            button {
                width: 100%;
                padding: 12px;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                margin-top: 10px;
            }
            button:hover {
                background: #5568d3;
            }
            .hint {
                margin-top: 20px;
                padding: 10px;
                background: #f0f0f0;
                border-radius: 5px;
                font-size: 12px;
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h2>🎯 Milestone Savings</h2>
            <form method="post">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
            <div class="hint">
                <strong>Test Account:</strong><br>
                Username: gowrisankar<br>
                Password: pass
            </div>
        </div>
    </body>
    </html>
    """

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