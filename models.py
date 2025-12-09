from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import CheckConstraint, JSON, event
from datetime import datetime
from extensions import db

# Association table for many-to-many relationship between users and goals
user_goals = db.Table('user_goals',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('goal_id', db.Integer, db.ForeignKey('goals.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    goals = db.relationship('Goal', secondary=user_goals, backref=db.backref('users', lazy=True))
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    savings_rules = db.relationship('SavingsRule', backref='user', lazy=True)
    activity_logs = db.relationship('ActivityLog', backref='user', lazy=True, cascade='all, delete-orphan')

class Goal(db.Model):
    __tablename__ = 'goals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Numeric(10,2), nullable=False)
    current_amount = db.Column(db.Numeric(10,2), server_default='0.00', nullable=False)
    image_url = db.Column(db.String(255))
    savings_pace = db.Column(db.String(20), server_default='Conservative')
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, server_default=db.text('true'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    completed_at = db.Column(db.DateTime)


# TRANSACTIONS
class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=False)
    amount = db.Column(db.Numeric(10,2), nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    original_expense_amount = db.Column(db.Numeric(10,2))
    expense_category = db.Column(db.String(50))
    transaction_metadata = db.Column(JSON, name='metadata')
    is_undoable = db.Column(db.Boolean, server_default=db.text('true'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    __table_args__ = (
        CheckConstraint('amount IS NOT NULL'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'goal_id': self.goal_id,
            'amount': float(self.amount) if self.amount else None,
            'transaction_type': self.transaction_type,
            'description': self.description,
            'original_expense_amount': float(self.original_expense_amount) if self.original_expense_amount else None,
            'expense_category': self.expense_category,
            'metadata': self.transaction_metadata,
            'is_undoable': self.is_undoable,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# SAVINGS RULES
class SavingsRule(db.Model):
    __tablename__ = 'savings_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=False)
    rule_type = db.Column(db.String(50), nullable=False)  # recurring, habit_reward, guilty_pleasure_tax
    rule_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(10,2), nullable=False)
    frequency = db.Column(db.String(20))  # daily, weekly, monthly (for recurring)
    trigger_category = db.Column(db.String(50))  # for guilty pleasure
    rule_config = db.Column(JSON)
    is_active = db.Column(db.Boolean, server_default=db.text('true'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    last_executed = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'goal_id': self.goal_id,
            'rule_type': self.rule_type,
            'rule_name': self.rule_name,
            'amount': float(self.amount) if self.amount else None,
            'frequency': self.frequency,
            'is_active': self.is_active
        }

# EXPENSE CATEGORIES
class ExpenseCategory(db.Model):
    __tablename__ = 'expense_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_name = db.Column(db.String(50), nullable=False)
    is_default = db.Column(db.Boolean, server_default=db.text('false'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category_name': self.category_name,
            'is_default': self.is_default
        }

# Activity Logs
class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    endpoint = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    status_code = db.Column(db.Integer)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    request_data = db.Column(JSON)
    response_data = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'endpoint': self.endpoint,
            'method': self.method,
            'status_code': self.status_code,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# SESSIONS (simple demo)
class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    def is_expired(self):
        from datetime import datetime
        return datetime.utcnow() > self.expires_at