from app import app, db
from models import User, Goal, SavingsRule
from werkzeug.security import generate_password_hash
from decimal import Decimal


with app.app_context():
    db.drop_all()
    db.create_all()

    u = User(username='gowrisankar', email='gowri@example.com', password_hash=generate_password_hash('pass'))
    db.session.add(u)
    db.session.commit()

    g1 = Goal(user_id=u.id, name='Buy a Car', target_amount=Decimal('10000.00'), savings_pace='Aggressive')
    g2 = Goal(user_id=u.id, name='New Running Shoes', target_amount=Decimal('150.00'), savings_pace='Moderate')
    db.session.add_all([g1, g2])
    db.session.commit()

    gp = SavingsRule(user_id=u.id, goal_id=g1.id, rule_type='guilty_pleasure_tax', rule_name='Food Delivery Tax', amount=Decimal('1.00'), trigger_category='Food Delivery')
    hr = SavingsRule(user_id=u.id, goal_id=g2.id, rule_type='habit_reward', rule_name='Morning Run', amount=Decimal('2.00'))
    rc = SavingsRule(user_id=u.id, goal_id=g1.id, rule_type='recurring', rule_name='Weekly Car Fund', amount=Decimal('25.00'), frequency='weekly')
    db.session.add_all([gp, hr, rc])
    db.session.commit()

    print('Seeded users/goals/rules.')