# auth.py
from functools import wraps
from flask import request, jsonify
from config import config
import logging

logger = logging.getLogger(__name__)

def require_api_key(f):
    """Decorator to require API key for endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get(config.API_KEY_NAME)
        
        if not api_key:
            return jsonify({
                "success": False,
                "error": "You are not authorized. API key not provided.",
                "code": "MISSING_API_KEY",
                "message": f"Please provide your API key in the '{config.API_KEY_NAME}' header"
            }), 401
        
        if api_key != config.API_KEY:
            return jsonify({
                "success": False,
                "error": "You are not authorized. API key is invalid.",
                "code": "INVALID_API_KEY",
                "message": "The provided API key is incorrect. Please check your API key."
            }), 401
        
        return f(*args, **kwargs)
    return decorated_function