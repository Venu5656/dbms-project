from flask import request, g, jsonify, make_response
import json
from datetime import datetime
from functools import wraps
from models import db, ActivityLog

def log_activity(f):
    """Decorator to log activity for authenticated users"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the response by calling the actual view function
        response = f(*args, **kwargs)
        
        # Check if user is authenticated (you might need to adjust this based on your auth system)
        user_id = None
        if hasattr(g, 'user') and g.user:
            user_id = g.user.id
        elif hasattr(request, 'user') and request.user:
            user_id = request.user.id
        
        # Only log if we have a user ID
        if user_id:
            try:
                # Get response data if it's JSON
                response_data = None
                if response and hasattr(response, 'get_data'):
                    try:
                        response_data = response.get_data(as_text=True)
                        # Try to parse as JSON to ensure it's valid
                        if response_data:
                            json.loads(response_data)
                    except:
                        # If not JSON, truncate to avoid large text fields
                        response_data = str(response_data)[:1000] if response_data else None
                
                # Create log entry
                log = ActivityLog(
                    user_id=user_id,
                    endpoint=request.endpoint,
                    method=request.method,
                    status_code=response.status_code if hasattr(response, 'status_code') else None,
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string if request.user_agent else None,
                    request_data=request.get_json(silent=True) or dict(request.form) or None,
                    response_data=response_data
                )
                
                db.session.add(log)
                db.session.commit()
                
            except Exception as e:
                db.session.rollback()
                print(f"Error logging activity: {str(e)}")
        
        return response
    
    return decorated_function

def setup_activity_logging(app):
    """Set up activity logging for the Flask app"""
    @app.before_request
    def before_request():
        # You can add user identification logic here if needed
        pass
    
    @app.after_request
    def after_request(response):
        # This will be handled by the decorator on individual routes
        return response
