from functools import wraps
from flask import session, flash, redirect, url_for, request
from firebase_admin import auth
import support

def login_required(f):
    """
    Decorate routes to require login.
    https://flask.palletsprojects.com/en/2.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def get_notification_count(user_id):
    """Fetches the count of unread notifications for a user from the database."""
    if not user_id:
        return 0
    try:
        query = "SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE"
        result = support.execute_query("search", query, (user_id,))
        return result[0][0] if result else 0
    except Exception as e:
        print(f"Error getting notification count: {e}")
        return 0

def create_notification(user_id, message, link_url=None, notification_type='general'):
    """Creates and saves an in-app notification for a user."""
    try:
        query = """
            INSERT INTO notifications (user_id, type, message, link_url)
            VALUES (%s, %s, %s, %s)
        """
        support.execute_query("insert", query, (user_id, notification_type, message, link_url))
        print(f"Notification created for user {user_id}: '{message}'")
        return True
    except Exception as e:
        print(f"Error creating notification for user {user_id}: {e}")
        return False 