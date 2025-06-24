from flask import Flask, render_template

app = Flask(__name__)

@app.route('/dashboard')
def dashboard():
    # Example data to pass to the dashboard
    user_stats = {
        'total_users': 120,
        'active_users': 85,
        'new_signups': 10,
        'total_stokvels': 15,
        'pending_kyc': 3
    }
    recent_activity = [
        {'user': 'Alice', 'action': 'Joined Stokvel', 'time': '2024-06-25 10:00'},
        {'user': 'Bob', 'action': 'Made Contribution', 'time': '2024-06-25 09:45'},
        {'user': 'Carol', 'action': 'Requested Payout', 'time': '2024-06-25 09:30'},
    ]
    return render_template('dashboard.html', user_stats=user_stats, recent_activity=recent_activity)

if __name__ == '__main__':
    app.run(debug=True) 