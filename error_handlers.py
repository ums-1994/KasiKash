from flask import render_template, flash, redirect, url_for, request, jsonify
import logging
from werkzeug.exceptions import HTTPException
from firebase_admin import auth

logger = logging.getLogger(__name__)

def handle_404_error(error):
    """Handle 404 Not Found errors"""
    logger.warning(f"404 error: {request.url}")
    return render_template('errors/404.html'), 404

def handle_500_error(error):
    """Handle 500 Internal Server errors"""
    logger.error(f"500 error: {error}")
    return render_template('errors/500.html'), 500

def handle_database_error(error):
    """Handle database-related errors"""
    logger.error(f"Database error: {error}")
    flash("A database error occurred. Please try again later.", "error")
    return redirect(url_for('home'))

def handle_firebase_error(error):
    """Handle Firebase-related errors"""
    logger.error(f"Firebase error: {error}")
    flash("An authentication error occurred. Please try logging in again.", "error")
    return redirect(url_for('login'))

def handle_validation_error(error):
    """Handle validation errors"""
    logger.warning(f"Validation error: {error}")
    flash("Please check your input and try again.", "warning")
    return redirect(request.referrer or url_for('home'))

def handle_file_upload_error(error):
    """Handle file upload errors"""
    logger.error(f"File upload error: {error}")
    flash("There was an error uploading your file. Please try again.", "error")
    return redirect(request.referrer or url_for('home'))

def handle_csrf_error(error):
    """Handle CSRF token errors"""
    logger.warning(f"CSRF error: {error}")
    flash("Your session has expired. Please try again.", "warning")
    return redirect(url_for('login'))

def handle_permission_error(error):
    """Handle permission/authorization errors"""
    logger.warning(f"Permission error: {error}")
    flash("You don't have permission to perform this action.", "error")
    return redirect(url_for('home'))

def handle_api_error(error):
    """Handle API-related errors"""
    logger.error(f"API error: {error}")
    return jsonify({
        'success': False,
        'error': 'An error occurred while processing your request.'
    }), 500

def handle_generic_error(error):
    """Handle generic/unexpected errors"""
    logger.error(f"Unexpected error: {error}")
    flash("An unexpected error occurred. Please try again later.", "error")
    return redirect(url_for('home'))

def register_error_handlers(app):
    """Register all error handlers with the Flask app"""
    
    # HTTP error handlers
    app.register_error_handler(404, handle_404_error)
    app.register_error_handler(500, handle_500_error)
    
    # Custom error handlers for specific exceptions
    app.register_error_handler(Exception, handle_generic_error)
    
    # Firebase error handlers
    app.register_error_handler(auth.UserNotFoundError, handle_firebase_error)
    app.register_error_handler(auth.InvalidPasswordError, handle_firebase_error)
    app.register_error_handler(auth.EmailAlreadyExistsError, handle_firebase_error)
    
    # Database error handlers
    try:
        import psycopg2
        app.register_error_handler(psycopg2.OperationalError, handle_database_error)
        app.register_error_handler(psycopg2.IntegrityError, handle_database_error)
    except ImportError:
        pass
    
    # Validation error handlers
    from wtforms import ValidationError
    app.register_error_handler(ValidationError, handle_validation_error)
    
    # CSRF error handlers
    from flask_wtf.csrf import CSRFError
    app.register_error_handler(CSRFError, handle_csrf_error)

class AppError(Exception):
    """Base exception class for application errors"""
    def __init__(self, message, status_code=500, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status_code'] = self.status_code
        return rv

class ValidationError(AppError):
    """Exception for validation errors"""
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=400, payload=payload)

class PermissionError(AppError):
    """Exception for permission errors"""
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=403, payload=payload)

class NotFoundError(AppError):
    """Exception for not found errors"""
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=404, payload=payload)

def safe_execute(func, *args, **kwargs):
    """
    Safely execute a function with error handling
    
    Args:
        func: Function to execute
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Tuple of (success, result, error_message)
    """
    try:
        result = func(*args, **kwargs)
        return True, result, None
    except Exception as e:
        logger.error(f"Error in {func.__name__}: {e}")
        return False, None, str(e)

def validate_input(data, required_fields=None, optional_fields=None):
    """
    Validate input data
    
    Args:
        data: Dictionary of input data
        required_fields: List of required field names
        optional_fields: List of optional field names
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if required_fields:
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Field '{field}' is required"
    
    if optional_fields:
        for field in optional_fields:
            if field in data and data[field] is not None:
                # Add specific validation for each field type
                if field == 'email' and '@' not in data[field]:
                    return False, f"Field '{field}' must be a valid email"
                elif field == 'amount' and not isinstance(data[field], (int, float)):
                    return False, f"Field '{field}' must be a number"
    
    return True, None 