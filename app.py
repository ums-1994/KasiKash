from flask import jsonify, session
from flask_login import login_required
import support

@app.route('/dashboard/recent_activities')
@login_required
def dashboard_recent_activities():
    if 'user_id' not in session:
        return jsonify({'recent_activities': []})
    recent_activities = []
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT t.type, t.amount, t.status, t.transaction_date, t.description, s.name as stokvel_name
                    FROM transactions t
                    JOIN stokvels s ON t.stokvel_id = s.id
                    WHERE t.user_id = %s
                    ORDER BY t.transaction_date DESC
                    LIMIT 5
                """, (session['user_id'],))
                rows = cur.fetchall()
                for row in rows:
                    t_type, amount, status, t_date, description, stokvel_name = row
                    # Format date for display
                    if t_date:
                        try:
                            from datetime import datetime
                            now = datetime.now()
                            if isinstance(t_date, str):
                                t_date = datetime.fromisoformat(t_date)
                            delta = now - t_date
                            if delta.days == 0:
                                if delta.seconds < 3600:
                                    date_str = f"{delta.seconds//60} minutes ago"
                                else:
                                    date_str = f"{delta.seconds//3600} hours ago"
                            elif delta.days == 1:
                                date_str = "Yesterday"
                            else:
                                date_str = f"{delta.days} days ago"
                        except Exception:
                            date_str = str(t_date)
                    else:
                        date_str = 'N/A'
                    # Title and badge
                    if t_type == 'contribution':
                        title = f"Contribution to {stokvel_name}"
                    elif t_type == 'withdrawal':
                        title = f"Withdrawal from {stokvel_name}"
                    elif t_type == 'payout':
                        title = f"Payout from {stokvel_name}"
                    elif t_type == 'goal':
                        title = f"Savings Goal: {description}"
                    else:
                        title = description or t_type.capitalize()
                    recent_activities.append({
                        'type': t_type,
                        'title': title,
                        'amount': float(amount) if amount is not None else 0.0,
                        'date': date_str,
                        'status': status.capitalize() if status else '',
                    })
    except Exception as e:
        print(f"Error fetching recent activities (AJAX): {e}")
    return jsonify({'recent_activities': recent_activities}) 