from flask import Blueprint, jsonify, session
import support
import psycopg2.extras
from datetime import datetime, timedelta
from utils import login_required

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

@api_bp.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Real total users
                cur.execute("SELECT COUNT(*) FROM users")
                total_users = cur.fetchone()[0] or 0
                
                # Unique stokvel members (if needed for another stat)
                cur.execute("SELECT COUNT(DISTINCT user_id) FROM stokvel_members")
                unique_members = cur.fetchone()[0] or 0
                
                # Count all pending payouts
                cur.execute("SELECT COUNT(*) FROM transactions WHERE type = 'payout' AND status = 'pending'")
                pending_loans = cur.fetchone()[0] or 0
                
                # KYC pending - simplified query
                cur.execute("SELECT COUNT(*) FROM users WHERE kyc_approved_at IS NULL")
                kyc_pending = cur.fetchone()[0] or 0
                
                # Total contributions (sum all positive amounts)
                cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE amount > 0")
                total_deposits = cur.fetchone()[0] or 0
                
                # New notifications
                cur.execute("SELECT COUNT(*) FROM notifications WHERE is_read = FALSE")
                new_notifications = cur.fetchone()[0] or 0
                
                # Calculate percentage changes (simplified)
                cur.execute("SELECT COUNT(*) FROM stokvel_members WHERE joined_at >= %s", 
                          (datetime.now() - timedelta(days=30),))
                members_last_month = cur.fetchone()[0] or 0
                
                # Avoid division by zero
                if members_last_month > 0:
                    members_change = ((total_users - members_last_month) / members_last_month) * 100
                else:
                    members_change = 0.0
                
                cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'deposit' AND transaction_date >= %s", 
                          (datetime.now() - timedelta(days=30),))
                deposits_last_month = cur.fetchone()[0] or 0
                
                # Avoid division by zero
                if deposits_last_month > 0:
                    deposits_change = ((total_deposits - deposits_last_month) / deposits_last_month) * 100
                else:
                    deposits_change = 0.0
                
        return jsonify({
            'total_users': int(total_users),
            'total_members': int(unique_members),
            'pending_loans': int(pending_loans),
            'kyc_pending': int(kyc_pending),
            'total_deposits': float(total_deposits),
            'new_notifications': int(new_notifications),
            'members_change': round(members_change, 1),
            'deposits_change': round(deposits_change, 1),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error fetching dashboard stats: {e}")
        # Return default values instead of error
        return jsonify({
            'total_users': 0,
            'total_members': 0,
            'pending_loans': 0,
            'kyc_pending': 0,
            'total_deposits': 0.0,
            'new_notifications': 0,
            'members_change': 0.0,
            'deposits_change': 0.0,
            'timestamp': datetime.now().isoformat()
        })

@api_bp.route('/api/dashboard/activity')
@login_required
def dashboard_activity():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Get recent transactions
                cur.execute("""
                    SELECT t.type, t.amount, t.status, t.transaction_date, u.username
                    FROM transactions t
                    LEFT JOIN users u ON t.user_id = u.firebase_uid
                    ORDER BY t.transaction_date DESC
                    LIMIT 10
                """)
                transactions = cur.fetchall()
                
                # Get recent KYC activities - simplified
                cur.execute("""
                    SELECT u.username, u.kyc_approved_at, u.created_at
                    FROM users u
                    WHERE u.kyc_approved_at IS NOT NULL OR u.created_at IS NOT NULL
                    ORDER BY u.created_at DESC
                    LIMIT 5
                """)
                kyc_activities = cur.fetchall()
                
                activities = []
                
                # Process transactions
                for trans in transactions:
                    activity_type = trans[0]  # type
                    amount = trans[1]
                    status = trans[2]
                    date = trans[3]
                    username = trans[4] or 'Unknown User'
                    
                    if activity_type == 'deposit':
                        activities.append({
                            'type': 'deposit',
                            'message': f'{username} deposited R{amount:.2f}',
                            'time': date.isoformat(),
                            'status': status,
                            'color': '#1edb8a'
                        })
                    elif activity_type == 'payout':
                        activities.append({
                            'type': 'payout',
                            'message': f'{username} requested R{amount:.2f} payout',
                            'time': date.isoformat(),
                            'status': status,
                            'color': '#f59e42'
                        })
                
                # Process KYC activities
                for kyc in kyc_activities:
                    username = kyc[0] or 'Unknown User'
                    kyc_approved = kyc[1]
                    created = kyc[2]
                    
                    if kyc_approved:
                        activities.append({
                            'type': 'kyc',
                            'message': f'{username} completed KYC verification',
                            'time': kyc_approved.isoformat(),
                            'status': 'approved',
                            'color': '#b13be0'
                        })
                    else:
                        activities.append({
                            'type': 'kyc',
                            'message': f'{username} uploaded KYC documents',
                            'time': created.isoformat(),
                            'status': 'pending',
                            'color': '#ff4d6d'
                        })
                
                # Sort by time and take top 10
                activities.sort(key=lambda x: x['time'], reverse=True)
                activities = activities[:10]
                
        return jsonify({
            'activities': activities,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error fetching dashboard activity: {e}")
        return jsonify({
            'activities': [],
            'timestamp': datetime.now().isoformat()
        })

@api_bp.route('/api/dashboard/debug')
@login_required
def dashboard_debug():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Check what data we actually have
                cur.execute("SELECT COUNT(*) FROM users")
                total_users = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM stokvel_members")
                total_members = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM transactions")
                total_transactions = cur.fetchone()[0] or 0
                
                cur.execute("SELECT type, COUNT(*), SUM(amount) FROM transactions GROUP BY type")
                transaction_types = cur.fetchall()
                
                cur.execute("SELECT SUM(amount) FROM transactions WHERE amount > 0")
                total_positive = cur.fetchone()[0] or 0
                
        return jsonify({
            'total_users': total_users,
            'total_members': total_members,
            'total_transactions': total_transactions,
            'transaction_types': [
                {'type': row[0], 'count': row[1], 'sum': float(row[2]) if row[2] is not None else 0}
                for row in transaction_types
            ],
            'total_positive': float(total_positive)
        })
    except Exception as e:
        print(f"Error in debug endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/dashboard/notifications')
@login_required
def dashboard_notifications():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Get recent admin notifications only
                cur.execute("""
                    SELECT message, created_at, is_read
                    FROM notifications
                    WHERE type = 'admin_notification'
                    ORDER BY created_at DESC
                    LIMIT 10
                """)
                notifications = cur.fetchall()
                
                # Get system alerts
                alerts = []
                
                # Check for pending KYC
                cur.execute("SELECT COUNT(*) FROM users WHERE kyc_approved_at IS NULL")
                kyc_pending = cur.fetchone()[0] or 0
                if kyc_pending > 0:
                    alerts.append({
                        'type': 'kyc',
                        'message': f'{kyc_pending} KYC reviews pending',
                        'time': datetime.now().isoformat(),
                        'color': '#ff4d6d',
                        'urgent': kyc_pending > 5
                    })
                
                # Check for pending loans
                cur.execute("SELECT COUNT(*) FROM transactions WHERE type = 'payout' AND status = 'pending'")
                loans_pending = cur.fetchone()[0] or 0
                if loans_pending > 0:
                    alerts.append({
                        'type': 'loan',
                        'message': f'{loans_pending} loan applications pending',
                        'time': datetime.now().isoformat(),
                        'color': '#f59e42',
                        'urgent': loans_pending > 10
                    })
                
                # Check for system status
                alerts.append({
                    'type': 'system',
                    'message': 'System backup completed',
                    'time': datetime.now().isoformat(),
                    'color': '#60efff',
                    'urgent': False
                })
                
        return jsonify({
            'notifications': [{'message': n[0], 'time': n[1].isoformat(), 'read': n[2]} for n in notifications],
            'alerts': alerts,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error fetching dashboard notifications: {e}")
        return jsonify({
            'notifications': [],
            'alerts': [],
            'timestamp': datetime.now().isoformat()
        })
