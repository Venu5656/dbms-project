from datetime import datetime
from flask import request, has_request_context
from models import db
import json

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    endpoint = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    status_code = db.Column(db.Integer)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    request_data = db.Column(db.JSON)
    response_data = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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

def log_activity(user_id, endpoint, method, status_code=None, request_data=None, response_data=None):
    """Log user activity to the database"""
    if not has_request_context():
        return None
        
    try:
        # Convert request data to JSON-serializable format
        req_data = None
        if request_data is None and hasattr(request, 'get_json'):
            try:
                req_data = request.get_json(silent=True)
            except:
                req_data = str(request.get_data())
        
        # Create log entry
        log = ActivityLog(
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None,
            request_data=req_data,
            response_data=str(response_data)[:1000] if response_data else None  # Limit size
        )
        
        db.session.add(log)
        db.session.commit()
        return log
    except Exception as e:
        db.session.rollback()
        print(f"Error logging activity: {str(e)}")
        return None
