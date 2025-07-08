from flask import Blueprint, jsonify
import support
import psycopg2.extras
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/dashboard/financial')
def dashboard_financial():
    # Example: last 7 days balances
    labels = []
    values = []
    try:
        with support.db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                for i in range(6, -1, -1):
                    day = (datetime.now() - timedelta(days=i)).date()
                    cur.execute("""
                        SELECT COALESCE(SUM(CASE WHEN type='deposit' THEN amount WHEN type='withdrawal' THEN -amount ELSE 0 END), 0) as balance
                        FROM transactions
                        WHERE DATE(created_at) <= %s
                    """, (day,))
                    row = cur.fetchone()
                    labels.append(day.strftime('%b %d'))
                    values.append(float(row['balance']) if row else 0)
    except Exception as e:
        return jsonify({'labels': [], 'values': [], 'error': str(e)})
    return jsonify({'labels': labels, 'values': values})

@api_bp.route('/api/dashboard/user-growth')
def dashboard_user_growth():
    # Example: new users per day for last 7 days
    labels = []
    values = []
    try:
        with support.db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                for i in range(6, -1, -1):
                    day = (datetime.now() - timedelta(days=i)).date()
                    cur.execute("""
                        SELECT COUNT(*) as new_users
                        FROM users
                        WHERE DATE(created_at) = %s
                    """, (day,))
                    row = cur.fetchone()
                    labels.append(day.strftime('%b %d'))
                    values.append(row['new_users'] if row else 0)
    except Exception as e:
        return jsonify({'labels': [], 'values': [], 'error': str(e)})
    return jsonify({'labels': labels, 'values': values})
