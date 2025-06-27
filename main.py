from flask import Flask, render_template, request, redirect, session, flash, jsonify, url_for, Response, send_file
import os
from datetime import timedelta, datetime
import pandas as pd
import plotly
import plotly.express as px
import json
import warnings
import support
from functools import wraps
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import openai
from flask_wtf.csrf import CSRFProtect, generate_csrf
import firebase_admin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email
from firebase_admin import credentials, auth
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from flask_session import Session
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dateutil import parser as date_parser
from translations import get_text
from admin import admin_bp  # Import the blueprint
from utils import login_required

# Email handling imports
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename
import re
<<<<<<< HEAD
import calendar
=======
from decimal import Decimal, InvalidOperation
>>>>>>> 09799e6ad57bc08de1445d08a85e35f4e73d014d

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Initialize CSRF protection
csrf = CSRFProtect(app)

UPLOAD_FOLDER = 'static/profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

KYC_UPLOAD_FOLDER = 'static/kyc_docs'
ALLOWED_KYC_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
app.config['KYC_UPLOAD_FOLDER'] = KYC_UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_kyc_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_KYC_EXTENSIONS

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate(os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH", "firebase-service-account.json"))
    firebase_admin.initialize_app(cred)

# Database connection function
def get_db():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        return None

# Define LoginForm class
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')

def create_firebase_user(email, password):
    """Create a Firebase user account for an existing database user"""
    try:
        print(f"Attempting to create Firebase user for: {email}")
        user = auth.create_user(
            email=email,
            password=password,
            email_verified=True  # Since they've been using the account
        )
        print(f"Successfully created Firebase user: {user.uid}")
        return user
    except Exception as e:
        print(f"Error creating Firebase user: {str(e)}")
        return None

warnings.filterwarnings("ignore")

# Debugging .env loading
print(f"DEBUG: DB_NAME loaded from .env: {os.getenv('DB_NAME')}")
print(f"DEBUG: FIREBASE_SERVICE_ACCOUNT_KEY_PATH from .env: {os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH')}")
print(f"DEBUG: OPENROUTER_API_KEY loaded from .env: {'Yes' if os.getenv('OPENROUTER_API_KEY') else 'No'}")

# Debugging SendGrid environment variables
print(f"DEBUG: SENDGRID_API_KEY loaded from .env: {os.getenv('SENDGRID_API_KEY')}")
print(f"DEBUG: MAIL_SENDER_EMAIL loaded from .env: {os.getenv('MAIL_SENDER_EMAIL')}")

# Debugging B2 environment variables
print(f"DEBUG: B2_ACCESS_KEY_ID loaded from .env: {'Yes' if os.getenv('B2_ACCESS_KEY_ID') else 'No'}")
print(f"DEBUG: B2_SECRET_ACCESS_KEY loaded from .env: {'Yes' if os.getenv('B2_SECRET_ACCESS_KEY') else 'No'}")
print(f"DEBUG: B2_BUCKET_NAME loaded from .env: {os.getenv('B2_BUCKET_NAME')}")
print(f"DEBUG: B2_ENDPOINT_URL loaded from .env: {os.getenv('B2_ENDPOINT_URL')}")

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

app.secret_key = os.getenv('SECRET_KEY')
csrf = CSRFProtect(app)  # Initialize CSRF protection
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session_data')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
Session(app)  # Initialize Flask-Session

# Register the admin blueprint
app.register_blueprint(admin_bp, url_prefix='/admin')

# Initialize OpenRouter client at application level
try:
    # Use requests method for OpenRouter since openai client has compatibility issues
    import requests
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_api_key and openrouter_api_key != 'your-openrouter-api-key-here':
        print("OpenRouter client initialized successfully with Google Gemma 3n 4B model.")
        openrouter_available = True
    else:
        print("Warning: OpenRouter API key not found. Chat features will be disabled.")
        openrouter_available = False
except Exception as e:
    print(f"Warning: OpenRouter client not initialized. Chat features will be disabled. Error: {e}")
    openrouter_available = False

def verification_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.')
            return redirect('/login')
        try:
            firebase_user = auth.get_user(session['user_id'])
            if not firebase_user.email_verified:
                flash('Please verify your email to access this feature. Check your inbox for a verification link.')
                return redirect('/home')
        except Exception as e:
            print(f"Email verification check error: {e}")
            flash('Could not verify email status. Please try again or contact support.')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# Helper function to get notification count (simulate for now)
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
            INSERT INTO notifications (user_id, message, link_url, type)
            VALUES (%s, %s, %s, %s)
        """
        support.execute_query("insert", query, (user_id, message, link_url, notification_type))
        print(f"Notification created for user {user_id}: '{message}'")
        return True
    except Exception as e:
        print(f"Error creating notification for user {user_id}: {e}")
        return False

@app.route('/')
def welcome():
    return render_template("welcome.html")


@app.route('/feedback', methods=['POST'])
def feedback():
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    sub = request.form.get("sub")
    message = request.form.get("message")
    flash("Thanks for reaching out to us. We will contact you soon.")
    return redirect('/')


@app.route('/home')
@login_required
def home():
    if 'user_id' not in session:
        return redirect('/login')
    try:
        from datetime import date, datetime
        # Parse month parameter
        month_param = request.args.get('month')
        if month_param:
            try:
                month_start = datetime.strptime(month_param, '%Y-%m').date()
            except Exception:
                month_start = date.today().replace(day=1)
        else:
            month_start = date.today().replace(day=1)
        today = date.today()
        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year+1, month=1, day=1)
        else:
            next_month = month_start.replace(month=month_start.month+1, day=1)
        calendar_month = month_start.strftime('%B')
        calendar_year = month_start.year
        # Initialize default values
        username = str(session.get('username', 'User'))
        current_balance = float(0.00)
        total_contributions = float(0.00)
        total_withdrawals = float(0.00)
        pending_repayments = float(0.00)
        recent_contributions = []
        upcoming_contributions = []
        missed_contributions = []
        outstanding_loans = []
        loan_requests = []
        repayment_progress = []
        member_count = int(0)
        monthly_target = float(0.00)
        total_group_balance = float(0.00)
        calendar_events = []
        # Initialize chart data with empty structures to prevent JSON serialization errors
        savings_growth_chart_data = {}
        contribution_breakdown_chart_data = {}
        loan_trends_chart_data = {}
<<<<<<< HEAD
        user = None
        outstanding_loan_id = None
        try:
            with support.db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT username, email, profile_picture, joined_date FROM users WHERE firebase_uid = %s", (session['user_id'],))
                    user_row = cur.fetchone()
                    if user_row:
                        username = str(user_row[0])
                        user = {
                            'username': user_row[0],
                            'email': user_row[1],
                            'profile_picture': user_row[2],
                            'joined_date': user_row[3]
                        }
                    # Fetch the user's first outstanding loan (approved and remaining > 0)
                    cur.execute("""
                        SELECT lr.id, lr.amount, COALESCE(SUM(r.amount), 0) as repaid
                        FROM loan_requests lr
                        LEFT JOIN loan_repayments r ON lr.id = r.loan_id
                        WHERE lr.user_id = %s AND lr.status = 'approved'
                        GROUP BY lr.id, lr.amount
                        HAVING (lr.amount - COALESCE(SUM(r.amount), 0)) > 0
                        ORDER BY lr.id ASC
                        LIMIT 1
                    """, (session['user_id'],))
                    loan_row = cur.fetchone()
                    if loan_row:
                        outstanding_loan_id = loan_row[0]
                    # --- Calendar Events Integration ---
                    # Contributions
                    cur.execute("""
                        SELECT transaction_date, amount FROM transactions
                        WHERE user_id = %s AND type = 'contribution' AND transaction_date >= %s AND transaction_date < %s
                    """, (session['user_id'], month_start, next_month))
                    for tdate, amount in cur.fetchall():
                        calendar_events.append({'date': tdate.strftime('%Y-%m-%d'), 'desc': f'Contribution: R{amount:.2f}', 'type': 'contribution'})
                    # Payouts
                    cur.execute("""
                        SELECT transaction_date, amount FROM transactions
                        WHERE user_id = %s AND type = 'payout' AND transaction_date >= %s AND transaction_date < %s
                    """, (session['user_id'], month_start, next_month))
                    for tdate, amount in cur.fetchall():
                        calendar_events.append({'date': tdate.strftime('%Y-%m-%d'), 'desc': f'Payout: R{amount:.2f}', 'type': 'payout'})
                    # Savings goal deadlines
                    cur.execute("""
                        SELECT target_date, name FROM savings_goals
                        WHERE user_id = %s AND target_date >= %s AND target_date < %s
                    """, (session['user_id'], month_start, next_month))
                    for tdate, name in cur.fetchall():
                        if tdate:
                            calendar_events.append({'date': tdate.strftime('%Y-%m-%d'), 'desc': f'Savings Goal: {name}', 'type': 'goal'})
                    # Loan repayments
                    cur.execute("""
                        SELECT date, amount FROM loan_repayments
                        WHERE user_id = %s AND date >= %s AND date < %s
                    """, (session['user_id'], month_start, next_month))
                    for tdate, amount in cur.fetchall():
                        calendar_events.append({'date': tdate.strftime('%Y-%m-%d'), 'desc': f'Loan Repayment: R{amount:.2f}', 'type': 'repayment'})
                    # Custom user events (future support)
                    try:
                        cur.execute("""
                            SELECT event_date, description FROM user_events
                            WHERE user_id = %s AND event_date >= %s AND event_date < %s
                        """, (session['user_id'], month_start, next_month))
                        for tdate, desc in cur.fetchall():
                            calendar_events.append({'date': tdate.strftime('%Y-%m-%d'), 'desc': desc, 'type': 'custom'})
                    except Exception:
                        pass  # Table may not exist yet
        except Exception as e:
            print(f"Database error: {str(e)}")
            # Continue with default values if database query fails
        notification_count = get_notification_count(session.get('user_id'))
        # Compute prev/next month URLs
        prev_month = (month_start.replace(year=month_start.year-1, month=12) if month_start.month == 1 else month_start.replace(month=month_start.month-1))
        next_month = (month_start.replace(year=month_start.year+1, month=1) if month_start.month == 12 else month_start.replace(month=month_start.month+1))
        prev_month_url = url_for('home', month=prev_month.strftime('%Y-%m'))
        next_month_url = url_for('home', month=next_month.strftime('%Y-%m'))
        # Generate calendar_days for the selected month
        first_weekday, num_days = calendar.monthrange(month_start.year, month_start.month)
        calendar_days = []
        for i in range(first_weekday):
            calendar_days.append({'date': '', 'full_date': '', 'is_today': False, 'is_weekend': False})
        for day in range(1, num_days + 1):
            d = month_start.replace(day=day)
            calendar_days.append({
                'date': str(day),
                'full_date': d.strftime('%Y-%m-%d'),
                'is_today': (d == today)
            })
=======

        # Try to get user info from database
        user = {
            "username": username,
            "profile_picture": None,
            "email": None,
            # user["joined_date"] = None  # Remove or comment out this line
        }
        try:
            with support.db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT username, email, profile_picture FROM users WHERE firebase_uid = %s", (session['user_id'],))
                    user_data = cur.fetchone()
                    if user_data:
                        user["username"] = user_data[0]
                        user["email"] = user_data[1]
                        user["profile_picture"] = user_data[2]
                        # user["joined_date"] = user_data[3]  # Remove or comment out this line
        except Exception as e:
            print(f"User info fetch error: {e}")

        notification_count = get_notification_count(session.get('user_id')) # Get notification count

        # --- Calendar logic ---
        import calendar
        from datetime import date
        today = date.today()
        year = today.year
        month = today.month
        cal = calendar.Calendar()
        month_days = cal.itermonthdays4(year, month)  # (year, month, day, weekday)
        calendar_days = []
        for y, m, d, wd in month_days:
            if m == month:
                calendar_days.append({
                    'date': d,
                    'is_today': (y, m, d) == (today.year, today.month, today.day),
                    'events': []  # Add events here if needed
                })
        calendar_month = calendar.month_name[month]
        calendar_year = year
        # --- End calendar logic ---

        # --- Recent Activities logic ---
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
                                from datetime import datetime, timedelta
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
            print(f"Error fetching recent activities: {e}")
        # --- End Recent Activities logic ---

>>>>>>> 09799e6ad57bc08de1445d08a85e35f4e73d014d
        return render_template('dashboard.html',
                            username=username,
                            user_name=username,  # for template compatibility
            user=user,
                            outstanding_loan_id=outstanding_loan_id,
                            current_balance=current_balance,
                            total_contributions=total_contributions,
                            total_withdrawals=total_withdrawals,
                            pending_repayments=pending_repayments,
                            recent_contributions=recent_contributions,
                            upcoming_contributions=upcoming_contributions,
                            missed_contributions=missed_contributions,
                            outstanding_loans=outstanding_loans,
                            loan_requests=loan_requests,
                            repayment_progress=repayment_progress,
                            member_count=member_count,
                            monthly_target=monthly_target,
                            total_group_balance=total_group_balance,
                            calendar_events=calendar_events,
                            savings_growth_chart_data=savings_growth_chart_data,
                            contribution_breakdown_chart_data=contribution_breakdown_chart_data,
                            loan_trends_chart_data=loan_trends_chart_data,
                            notification_count=notification_count,
<<<<<<< HEAD
            calendar_month=calendar_month,
            calendar_year=calendar_year,
                            calendar_month_num=month_start.month,
                            prev_month_url=prev_month_url,
                            next_month_url=next_month_url,
                            calendar_days=calendar_days) # Pass notification count
=======
                            user=user,
                            recent_activities=recent_activities,
                            calendar_days=calendar_days,
                            calendar_month=calendar_month,
                            calendar_year=calendar_year
                            ) # Pass user dictionary and calendar data
>>>>>>> 09799e6ad57bc08de1445d08a85e35f4e73d014d
    except Exception as e:
        print(f"Dashboard error: {str(e)}")
        flash("Error loading dashboard. Please try again.")
        return redirect('/login')


@app.route('/analysis')
def analysis():
    if 'user_id' in session:
        # Changed to users table
        query = "select * from users where firebase_uid = %s "
        userdata = support.execute_query('search', query, (session['user_id'],))
        if not userdata or userdata[0] is None:
            flash('User data not found for analysis.')
            return redirect('/home')
        # Changed to firebase_uid
        query2 = "select pdate,expense, pdescription, amount from user_expenses where firebase_uid = %s"
        data = support.execute_query('search', query2, (session['user_id'],))
        df = pd.DataFrame(data, columns=['Date', 'Expense', 'Note', 'Amount(₹)'])
        df = support.generate_df(df)
        if df.shape[0] > 0:
            pie = support.meraPie(df=df, names='Expense', values='Amount(₹)', hole=0.7, hole_text='Expense',
                                  hole_font=20,
                                  height=180, width=180, margin=dict(t=1, b=1, l=1, r=1))
            df2 = df.groupby(['Note', "Expense"]).sum().reset_index()[["Expense", 'Note', 'Amount(₹)']]
            bar = support.meraBarChart(df=df2, x='Note', y='Amount(₹)', color="Expense", height=180, x_label="Category",
                                       show_xtick=False)
            line = support.meraLine(df=df, x='Date', y='Amount(₹)', color='Expense', slider=False, show_legend=False,
                                    height=180)
            scatter = support.meraScatter(df, 'Date', 'Amount(₹)', 'Expense', 'Amount(₹)', slider=False, )
            heat = support.meraHeatmap(df, 'Day_name', 'Month_name', height=200, title="Transaction count Day vs Month")
            month_bar = support.month_bar(df, 280)
            sun = support.meraSunburst(df, 280)
            return render_template('analysis.html',
                                   username=userdata[0][1],
                                   pie=pie,
                                   bar=bar,
                                   line=line,
                                   scatter=scatter,
                                   heat=heat,
                                   month_bar=month_bar,
                                   sun=sun,
                                   )
        else:
            return render_template('analysis.html',
                                   username=userdata[0][1],
                                   pie=None,
                                   bar=None,
                                   line=None,
                                   scatter=None,
                                   heat=None,
                                   month_bar=None,
                                   sun=None,
                                   )
    else:
        return redirect('/')


@app.route('/login')
def login():
    form = LoginForm()
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully!")
    return redirect('/')


@app.route('/login_validation', methods=['POST'])
def login_validation():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            email = form.email.data
            password = form.password.data
            remember = form.remember.data

            print(f"Login attempt for email: {email}")  # Debug log

            # Try to get user by email first
            try:
                print("Attempting to get user from Firebase...")  # Debug log
                user_record = auth.get_user_by_email(email)
                print(f"User found: {user_record.uid}")  # Debug log

                session.clear()  # Clear any existing session data
                session['user_id'] = str(user_record.uid)  # Ensure it's a string
                session['username'] = str(user_record.display_name or email)  # Ensure it's a string
                session['is_verified'] = bool(user_record.email_verified)  # Ensure it's a boolean
                session.permanent = bool(remember)  # Ensure it's a boolean
                # Fetch and set user role in session
                try:
                    with support.db_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute("SELECT role FROM users WHERE firebase_uid = %s", (user_record.uid,))
                            role_data = cur.fetchone()
                            if role_data and role_data[0]:
                                session['role'] = role_data[0]
                            else:
                                session['role'] = 'user'  # Default role if not set
                except Exception as role_e:
                    print(f"Error fetching user role: {role_e}")
                    session['role'] = 'user'

                # Update local database with firebase_uid if not already present or different
                try:
                    with support.db_connection() as conn:
                        with conn.cursor() as cur:
                            # Get current internal ID and firebase_uid from local db
                            cur.execute("SELECT id, firebase_uid FROM users WHERE email = %s", (email,))
                            user_data = cur.fetchone()
                            
                            if user_data:
                                internal_user_id = user_data[0]
                                old_firebase_uid = user_data[1]
                                new_firebase_uid = user_record.uid

                                if not old_firebase_uid or old_firebase_uid != new_firebase_uid:
                                    print(f"Firebase UID mismatch or not set. Updating references for user {email}. Old: {old_firebase_uid}, New: {new_firebase_uid}")

                                    # Update all tables referencing firebase_uid *before* updating users table
                                    update_queries = [
                                        ("UPDATE stokvels SET created_by = %s WHERE created_by = %s", (new_firebase_uid, old_firebase_uid)),
                                        ("UPDATE stokvel_members SET firebase_uid = %s WHERE firebase_uid = %s", (new_firebase_uid, old_firebase_uid)), # Assuming stokvel_members uses firebase_uid, not user_id for FK to users.firebase_uid based on \d users output
                                        ("UPDATE transactions SET user_id = %s WHERE user_id = %s", (internal_user_id, internal_user_id)), # This still uses internal_user_id, not firebase_uid
                                        ("UPDATE chat_history SET user_id = %s WHERE user_id = %s", (new_firebase_uid, old_firebase_uid)),
                                        ("UPDATE chatbot_preferences SET user_id = %s WHERE user_id = %s", (new_firebase_uid, old_firebase_uid)),
                                        ("UPDATE payment_methods SET user_id = %s WHERE user_id = %s", (new_firebase_uid, old_firebase_uid)),
                                        ("UPDATE payouts SET user_id = %s WHERE user_id = %s", (new_firebase_uid, old_firebase_uid)),
                                        ("UPDATE savings_goals SET user_id = %s WHERE user_id = %s", (new_firebase_uid, old_firebase_uid)),
                                    ]
                                    
                                    for query, params in update_queries:
                                        try:
                                            # Special handling for transactions if it uses internal_user_id rather than firebase_uid as FK
                                            if "FROM transactions t JOIN stokvels s ON t.stokvel_id = s.id WHERE t.user_id = %s" in query:
                                                # This specific query from /contributions route has already been updated to use internal_user_id
                                                # The update logic here in login_validation is for the foreign key reference from transactions.user_id to users.firebase_uid
                                                # Based on \d users output: expenses_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)
                                                # So, transactions.user_id references users.id, not users.firebase_uid
                                                # We need to update existing transactions to ensure their user_id is the correct internal_user_id.
                                                # We need to *ensure* that internal_user_id is stable and tied to firebase_uid.
                                                # The current main.py does SELECT id FROM users WHERE firebase_uid = %s for internal_user_id.
                                                # This logic below will update existing *user_id* in transactions to the correct *internal_user_id*.
                                                # If user_id is already the correct internal_user_id then this update does nothing
                                                # If it's an old internal_user_id, it will be updated.
                                                print(f"Attempting to update transactions user_id from previous internal_user_id to current: {internal_user_id}")
                                                cur.execute("UPDATE transactions SET user_id = %s WHERE user_id = (SELECT id FROM users WHERE firebase_uid = %s)", (internal_user_id, new_firebase_uid))
                                            else:
                                                print(f"Executing update query for related table: {query} with params {params}")
                                                cur.execute(query, params)
                                        except Exception as update_e:
                                            print(f"Error updating related table {query}: {str(update_e)}")
                                            # Log but don't stop the process, as some tables might not exist or have the column

                                    # Now update the users table with the new firebase_uid
                                    print(f"Updating users.firebase_uid for {email} to {new_firebase_uid}")
                                    cur.execute("UPDATE users SET firebase_uid = %s WHERE email = %s", (new_firebase_uid, email))
                                    conn.commit()
                                    print(f"Successfully updated firebase_uid for {email} and related tables.")
                                else:
                                    print(f"firebase_uid for {email} already set and matches: {new_firebase_uid}")
                            else:
                                print(f"User with email {email} not found in local database during login_validation for firebase_uid update.")
                except Exception as db_e:
                    print(f"Database update error during login: {str(db_e)}")
                    # This error is not critical enough to prevent login, but should be logged.

                if not user_record.email_verified:
                    print("User email not verified")  # Debug log
                    flash("Please verify your email address before logging in.")
                    return redirect('/login')

                # Update last_login in the database
                from datetime import datetime
                support.execute_query("update", "UPDATE users SET last_login = %s, email = %s WHERE firebase_uid = %s", (datetime.utcnow(), user_record.email, user_record.uid))

                print("Login successful, redirecting to home")  # Debug log
                flash("Login successful!")
                return redirect('/home')

            except auth.UserNotFoundError as e:
                print(f"User not found error: {str(e)}")  # Debug log
                flash('Invalid email or password')
                return redirect('/login')
            except Exception as e:
                print(f"Firebase auth error: {str(e)}")  # Debug log
                flash('An error occurred during login. Please try again.')
                return redirect('/login')

        except Exception as e:
            print(f"Login validation (outer) error: {str(e)}")  # Debug log
            flash('An error occurred during login. Please try again.')
            return redirect('/login')
    else:
        # If form validation fails (including CSRF validation)
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {field}: {error}")
        return redirect('/login')


@app.route('/register')
def register():
    return render_template("register.html")


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        try:
            # Check if user exists in Firebase
            try:
                print(f"Attempting to find user with email: {email}")
                user = auth.get_user_by_email(email)
                print(f"Found user for password reset: {user.uid}")
                print(f"User email verified: {user.email_verified}")
                # Generate password reset link
                print("Generating password reset link...")
                reset_link = auth.generate_password_reset_link(email)
                print(f"Generated password reset link for {email}")
                # Send password reset email
                print("Attempting to send password reset email...")
                if send_password_reset_email(email, reset_link):
                    print(f"Successfully sent password reset email to {email}")
                    flash("Password reset link has been sent to your email.", "success")
                else:
                    print(f"Failed to send password reset email to {email}")
                    flash("Failed to send password reset email. Please try again later.", "error")
            except auth.UserNotFoundError as e:
                print(f"Firebase UserNotFoundError: {str(e)}")
                print(f"Password reset requested for non-existent email: {email}")
                # Check if user exists in local database
                try:
                    with support.db_connection() as conn:
                        with conn.cursor() as cur:
                            # First check if user exists
                            cur.execute("SELECT id, firebase_uid FROM users WHERE email = %s", (email,))
                            user_data = cur.fetchone()
                            if user_data:
                                print(f"User found in local database but not in Firebase: {email}")
                                # Generate a random password for Firebase
                                import secrets
                                import string
                                alphabet = string.ascii_letters + string.digits
                                temp_password = ''.join(secrets.choice(alphabet) for i in range(12))
                                # Create Firebase account for existing user
                                firebase_user = create_firebase_user(email, temp_password)
                                if firebase_user:
                                    old_firebase_uid = user_data[1]
                                    new_firebase_uid = firebase_user.uid
                                    # Update stokvels table first
                                    cur.execute("""
                                        UPDATE stokvels 
                                        SET created_by = %s 
                                        WHERE created_by = %s
                                    """, (new_firebase_uid, old_firebase_uid))
                                    # Update stokvel_members table
                                    cur.execute("""
                                        UPDATE stokvel_members 
                                        SET firebase_uid = %s 
                                        WHERE firebase_uid = %s
                                    """, (new_firebase_uid, old_firebase_uid))
                                    # Update contributions table
                                    cur.execute("""
                                        UPDATE contributions 
                                        SET firebase_uid = %s 
                                        WHERE firebase_uid = %s
                                    """, (new_firebase_uid, old_firebase_uid))
                                    # Now update the users table
                                    cur.execute("""
                                        UPDATE users 
                                        SET firebase_uid = %s 
                                        WHERE email = %s
                                    """, (new_firebase_uid, email))
                                    conn.commit()
                                    print(f"Successfully updated all references from {old_firebase_uid} to {new_firebase_uid}")
                                    # Generate and send reset link
                                    reset_link = auth.generate_password_reset_link(email)
                                    if send_password_reset_email(email, reset_link):
                                        flash("Your account has been migrated. A password reset link has been sent to your email.", "success")
                                    else:
                                        flash("Your account has been migrated, but we couldn't send the reset email. Please try again.", "error")
                                else:
                                    flash("There was an issue migrating your account. Please contact support.", "error")
                            else:
                                print(f"User not found in either Firebase or local database: {email}")
                                flash("If an account exists with this email, a password reset link will be sent.", "success")
                except Exception as db_e:
                    print(f"Database error while checking user: {str(db_e)}")
                    flash("An error occurred. Please try again later.", "error")
            except Exception as e:
                print(f"Error in password reset for {email}: {str(e)}")
                flash("An error occurred. Please try again later.", "error")
        except Exception as e:
            print(f"Unexpected error in password reset for {email}: {str(e)}")
            flash("An error occurred. Please try again later.", "error")
        return redirect(url_for('login'))
    return render_template("forgot_password.html", form=form)


def send_password_reset_email(to_email, reset_link):
    sender_email = os.getenv("MAIL_SENDER_EMAIL")
    sender_name = os.getenv("MAIL_SENDER_NAME")
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")

    print(f"Preparing to send password reset email to: {to_email}")
    print(f"Using sender email: {sender_email}")
    print(f"Using sender name: {sender_name}")

    if not sendgrid_api_key:
        print("Error: SENDGRID_API_KEY not found in environment variables.")
        return False
    if not sender_email:
        print("Error: MAIL_SENDER_EMAIL not found in environment variables.")
        return False
    if not sender_name:
        print("Error: MAIL_SENDER_NAME not found in environment variables.")
        return False

    subject = "Reset Your KasiKash Password"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c5282;">Reset Your Password</h2>
        <p>Hello,</p>
            <p>We received a request to reset your password for your KasiKash account.</p>
            <p>Click the button below to reset your password:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" style="background-color: #2c5282; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a>
            </div>
            <p>If you did not request a password reset, please ignore this email or contact support if you have concerns.</p>
            <p>This link will expire in 1 hour.</p>
            <hr style="border: 1px solid #eee; margin: 20px 0;">
            <p style="color: #666; font-size: 0.9em;">Thanks,<br>The KasiKash Team</p>
        </div>
    </body>
    </html>
    """

    message = Mail(
        from_email=(sender_email, sender_name),
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )

    try:
        print("Initializing SendGrid client...")
        sendgrid_client = SendGridAPIClient(sendgrid_api_key)
        print("Sending email via SendGrid...")
        response = sendgrid_client.send(message)
        print(f"SendGrid password reset email sent status code: {response.status_code}")
        print(f"SendGrid response headers: {response.headers}")
        if response.status_code == 202:
            print(f"Password reset email sent successfully to {to_email}")
            return True
        else:
            print(f"Failed to send password reset email. Status: {response.status_code}")
            print(f"Response body: {response.body}")
            return False
    except Exception as e:
        print(f"Error sending password reset email to {to_email}: {str(e)}")
        print(f"Error type: {type(e)}")
        print(f"Error details: {str(e)}")
        return False


@app.route('/reset')
def reset_password_landing():
    # This route is a landing page for Firebase password reset redirects
    flash("If you have successfully reset your password, you can now log in.")
    return redirect(url_for('login'))


# Helper function to send email verification using SendGrid
def send_email_verification(to_email, verification_link):
    sender_email = os.getenv("MAIL_SENDER_EMAIL")
    sender_name = os.getenv("MAIL_SENDER_NAME")
    subject = "Verify your email for KasiKash App"
    html_content = f"""
    <html>
    <body>
        <p>Hello,</p>
        <p>Thank you for registering with KasiKash App!</p>
        <p>Please click on the link below to verify your email address:</p>
        <p><a href=\"{verification_link}\">{verification_link}</a></p>
        <p>If you did not register for an account, please ignore this email.</p>
        <p>Thanks,</p>
        <p>The KasiKash App Team</p>
    </body>
    </html>
    """
    return send_email(to_email, subject, html_content)


@app.route('/registration', methods=['POST'])
@csrf.exempt
def registration():
    if 'user_id' not in session:
        username = request.form.get('username')
        email = request.form.get('email')
        passwd = request.form.get('password')
        full_name = request.form.get('full_name', '')
        phone = request.form.get('phone', '')
        id_number = request.form.get('id_number', '')
        address = request.form.get('address', '')
        date_of_birth = request.form.get('date_of_birth', None)
        bio = request.form.get('bio', '')

        print(f"Registration attempt - Username: {username}, Email: {email}")

        if len(username) > 5 and len(email) > 10 and len(passwd) > 5:
            # Check if email already exists in PostgreSQL database
            try:
                with support.db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                        if cur.fetchone():
                            flash("An account with this email already exists. Please log in.")
                            return redirect('/login')
            except Exception as db_e:
                print(f"Database check error during registration: {db_e}")
                flash("An error occurred during registration. Please try again.")
                return redirect('/register')

            try:
                # Create user in Firebase Authentication
                user = auth.create_user(
                    email=email,
                    password=passwd,
                    display_name=username,
                    email_verified=True  # Set to True since we're using email/password auth
                )
                print(f"Created Firebase user: {user.uid}")

                # Store Firebase UID and username/email in your PostgreSQL database
                with support.db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO users (firebase_uid, username, email, password) VALUES (%s, %s, %s, %s) RETURNING id",
                            (user.uid, username, email, passwd)
                        )
                        local_user_id = cur.fetchone()[0]
                        conn.commit()

                        if local_user_id:
                            session['user_id'] = user.uid
                            session['username'] = username
                            session['is_verified'] = True
                            session.permanent = True
                            flash("Registration successful! You can now log in.")
                            return redirect('/login')
                        else:
                            flash("Registration failed: Could not retrieve local user ID.")
                            auth.delete_user(user.uid)
                            return redirect('/register')

            except Exception as e:
                print(f"Registration error: {str(e)}")
                if "email-already-exists" in str(e):
                    flash("Email address is already in use. Please use a different email or log in.")
                else:
                    flash(f"An unexpected error occurred during registration: {str(e)}")
                return redirect('/register')
        else:
            flash("Not enough data to register, try again!!")
            return redirect('/register')
    else:
        flash("Already a user is logged-in!")
        return redirect('/home')


@app.route('/get_started')
def get_started():
    if 'user_id' in session:
        return redirect('/home')
    return redirect('/login')


@app.route('/test_nav')
@login_required
def test_nav():
    return render_template('test_nav.html')

@app.route('/debug_session')
def debug_session():
    """Debug route to check session status"""
    debug_info = {
        'user_id_in_session': session.get('user_id', 'Not set'),
        'all_session_keys': list(session.keys()),
        'is_logged_in': 'user_id' in session
    }
    return f"""
    <h1>Session Debug Info</h1>
    <pre>{debug_info}</pre>
    <p><a href="/login">Go to Login</a></p>
    <p><a href="/home">Go to Home</a></p>
    <p><a href="/test_nav">Go to Test Nav</a></p>
    """

@app.route('/stokvels')
@login_required
def stokvels():
    firebase_uid = session.get('user_id')
    if not firebase_uid:
        flash("User not found in session, please log in again.", "error")
        return redirect('/login')

    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Fetch stokvels where the current user is a member, including their role
                cur.execute("""
                    SELECT 
                        s.id, 
                        s.name, 
                        s.description, 
                        s.monthly_contribution,
                        s.total_pool,
                        s.target_amount,
                        s.goal_amount, 
                        (SELECT COUNT(*) FROM stokvel_members sm2 WHERE sm2.stokvel_id = s.id) as member_count,
                        (SELECT SUM(t.amount) FROM transactions t WHERE t.stokvel_id = s.id) as total_contributions,
                        s.target_date,
                        sm.role
                    FROM stokvels s
                    JOIN stokvel_members sm ON s.id = sm.stokvel_id
                    WHERE sm.user_id = %s
                """, (firebase_uid,))
                user_stokvels = [dict(zip([desc[0] for desc in cur.description], row)) for row in cur.fetchall()]

                # Fetch stokvels created by the current user
                cur.execute("""
                    SELECT 
                        s.id, 
                        s.name, 
                        s.description, 
                        s.monthly_contribution,
                        s.total_pool,
                        s.target_amount,
                        s.goal_amount, 
                        (SELECT COUNT(*) FROM stokvel_members sm2 WHERE sm2.stokvel_id = s.id) as member_count,
                        (SELECT SUM(t.amount) FROM transactions t WHERE t.stokvel_id = s.id) as total_contributions,
                        s.target_date,
                        sm.role
                    FROM stokvels s
                    JOIN stokvel_members sm ON s.id = sm.stokvel_id
                    WHERE s.created_by = %s AND sm.user_id = %s
                """, (firebase_uid, firebase_uid))
                created_stokvels = [dict(zip([desc[0] for desc in cur.description], row)) for row in cur.fetchall()]

        return render_template('stokvels.html', stokvels=user_stokvels, created_stokvels=created_stokvels)
    except Exception as e:
        flash(f"An error occurred while loading your stokvels: {e}")
        print(f"Stokvels page error: {e}")
        return render_template('stokvels.html', stokvels=[], created_stokvels=[])

@app.route('/create_stokvel', methods=['POST'])
@login_required
def create_stokvel():
    user_id = session['user_id']
    name = request.form['name']
    description = request.form['description']
    monthly_contribution = request.form['monthly_contribution']
    
    # Insert new stokvel and get its ID
    query = "INSERT INTO stokvels (name, description, created_by, monthly_contribution) VALUES (%s, %s, %s, %s) RETURNING id"
    result = support.execute_query("insert", query, (name, description, user_id, monthly_contribution))

    stokvel_id = result[0] if result else None
    if stokvel_id:
        # Add the creator as the first member
        support.execute_query("insert", "INSERT INTO stokvel_members (stokvel_id, user_id, role) VALUES (%s, %s, %s)",
                              (stokvel_id, user_id, 'admin'))
        
        # Create a notification for the creator
        message = f"You successfully created the stokvel '{name}'!"
        link = url_for('view_stokvel_members', stokvel_id=stokvel_id)
        create_notification(user_id, message, link_url=link, notification_type='stokvel_created')

        flash('Stokvel created successfully!', 'success')
    else:
        flash('Failed to create stokvel.', 'danger')
        
    return redirect(url_for('stokvels'))

@app.route('/contributions')
@login_required
def contributions():
    firebase_uid = session.get('user_id')
    if not firebase_uid:
        flash("User not found in session, please log in again.", "error")
        return redirect('/login')

    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Use firebase_uid directly since the database now uses Firebase UIDs
                cur.execute("""
                    SELECT t.id, t.amount, t.status, t.transaction_date, s.name, s.description
                    FROM transactions t
                    JOIN stokvels s ON t.stokvel_id = s.id
                    WHERE t.user_id = %s
                    ORDER BY t.transaction_date DESC
                """, (firebase_uid,))
                contributions = cur.fetchall()
                
                # Fetch stokvels the user is a member of
                cur.execute("""
                    SELECT s.id, s.name
                    FROM stokvels s
                    JOIN stokvel_members sm ON s.id = sm.stokvel_id
                    WHERE sm.user_id = %s
                """, (firebase_uid,))
                stokvels = cur.fetchall()

        # Process and render as before
                contributions_list = []
                for row in contributions:
                    try:
                        transaction_date = row[3]
                        if transaction_date:
                            try:
                                transaction_date = transaction_date.strftime('%Y-%m-%d %H:%M')
                            except AttributeError:
                                transaction_date = str(transaction_date)
                        else:
                            transaction_date = 'N/A'
                        contribution_dict = {
                            'id': row[0],
                            'amount': float(row[1]) if row[1] is not None else 0.0,
                            'status': row[2] or 'pending',
                            'created_at': transaction_date,
                            'stokvel_name': row[4] or 'Unknown Stokvel',
                            'description': row[5] or 'No description'
                        }
                        contributions_list.append(contribution_dict)
                    except Exception as e:
                        print(f"Error processing contribution row: {e}")
                stokvels_list = []
                for row in stokvels:
                    try:
                        stokvels_list.append({
                            'id': row[0],
                            'name': row[1]
                        })
                    except Exception as e:
                        print(f"Error processing stokvel row: {e}")
        return render_template('contributions.html', contributions=contributions_list, stokvels=stokvels_list)
    except Exception as e:
        print(f"Error in contributions route: {e}")
        flash("An error occurred while loading your contributions.")
        return render_template('contributions.html', contributions=[], stokvels=[])

@app.route('/make_contribution', methods=['GET', 'POST'])
@login_required
def make_contribution():
    if request.method == 'POST':
        firebase_uid = session.get('user_id')
        if not firebase_uid:
            flash("Please log in to make a contribution.", "error")
            return redirect(url_for('login'))
        stokvel_id = request.form.get('stokvel_id')
        amount = request.form.get('amount')
        description = request.form.get('description')
        if not all([stokvel_id, amount, description]):
            flash("Stokvel, amount, and description are required for a contribution.")
            return redirect('/contributions')
        try:
            amount = float(amount)
            stokvel_id = int(stokvel_id)
            with support.db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if the user is actually a member of this stokvel
                    cur.execute("SELECT 1 FROM stokvel_members WHERE stokvel_id = %s AND user_id = %s", (stokvel_id, firebase_uid))
                    if not cur.fetchone():
                        flash("You are not a member of this stokvel.")
                        return redirect('/contributions')
                    
                    # Get stokvel name and admin user for notification
                    cur.execute("""
                        SELECT s.name, sm.user_id 
                        FROM stokvels s
                        JOIN stokvel_members sm ON s.id = sm.stokvel_id
                        WHERE s.id = %s AND sm.role = 'admin'
                    """, (stokvel_id,))
                    stokvel_info = cur.fetchone()
                    
                    if stokvel_info:
                        stokvel_name, admin_user_id = stokvel_info
                        
                        # Get the contributing user's name
                        cur.execute("SELECT username FROM users WHERE firebase_uid = %s", (firebase_uid,))
                        user_info = cur.fetchone()
                        user_name = user_info[0] if user_info else "A member"
                    
                    # Insert the contribution transaction
                    cur.execute("""
                        INSERT INTO transactions (user_id, stokvel_id, amount, type, description, transaction_date, status)
                        VALUES (%s, %s, %s, 'contribution', %s, CURRENT_DATE, 'completed')
                    """, (firebase_uid, stokvel_id, amount, description))
                    conn.commit()
                    
                    # Update the stokvel's total pool
                    cur.execute("UPDATE stokvels SET total_pool = COALESCE(total_pool, 0) + %s WHERE id = %s", (amount, stokvel_id))
                    conn.commit()
                    
                    # Create notification for stokvel admin
                    if stokvel_info and admin_user_id:
                        message = f"{user_name} made a contribution of R{amount:.2f} to '{stokvel_name}' stokvel."
                        link = url_for('contributions')
                        create_notification(admin_user_id, message, link_url=link, notification_type='contribution_made')
                        
            flash("Contribution recorded successfully!")
            return redirect('/contributions')
        except ValueError:
            flash("Amount must be a number.")
            return redirect('/contributions')
        except Exception as e:
            print(f"Error making contribution: {e}")
            flash("An error occurred while recording your contribution. Please try again.")
            return redirect('/contributions')
    else: # GET request
        firebase_uid = session.get('user_id')
        if not firebase_uid:
            flash("Please log in to make a contribution.", "error")
            return redirect(url_for('login'))
        stokvels = []
        try:
            with support.db_connection() as conn:
                with conn.cursor() as cur:
                    # Fetch stokvels where the user is a member
                    cur.execute("""
                        SELECT s.id, s.name 
                        FROM stokvels s
                        JOIN stokvel_members sm ON s.id = sm.stokvel_id
                        WHERE sm.user_id = %s
                    """, (firebase_uid,))
                    stokvels_data = cur.fetchall()
                    for stokvel in stokvels_data:
                        stokvels.append({'id': stokvel[0], 'name': stokvel[1]})
            print(f"Fetched stokvels for user {firebase_uid}: {stokvels}")
        except Exception as e:
            print(f"Error fetching stokvels: {str(e)}")
            flash("Error loading stokvels. Please try again.", "error")
            stokvels = [] # Ensure stokvels is empty on error
        return render_template("make_contribution.html", stokvels=stokvels)

@app.route('/payouts')
@login_required
def payouts():
    firebase_uid = session.get('user_id')
    if not firebase_uid:
        flash("User not found in session, please log in again.", "error")
        return redirect('/login')
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Get user's payouts using firebase_uid directly
                cur.execute("""
                    SELECT t.amount, t.description, t.transaction_date, s.name as stokvel_name, t.status
                    FROM transactions t
                    JOIN stokvels s ON t.stokvel_id = s.id
                    WHERE t.user_id = %s AND t.type = 'payout'
                    ORDER BY t.transaction_date DESC
                """, (firebase_uid,))
                payouts_tuples = cur.fetchall()

                # Convert tuples to dictionaries for easier access in template
                payouts_list = []
                payout_keys = ['amount', 'description', 'transaction_date', 'stokvel_name', 'status']
                for p_tuple in payouts_tuples:
                    payouts_list.append(dict(zip(payout_keys, p_tuple)))

                # Get stokvels the user is a member of to show options for payout requests
                cur.execute("""
                    SELECT s.id, s.name, s.target_amount, s.monthly_contribution, s.target_date
                    FROM stokvels s
                    JOIN stokvel_members sm ON s.id = sm.stokvel_id
                    WHERE sm.user_id = %s
                """, (firebase_uid,))
                stokvel_options = cur.fetchall()

        return render_template('payouts.html', payouts=payouts_list, stokvel_options=stokvel_options)
    except Exception as e:
        print(f"Payouts page error: {e}")
        flash("An error occurred while loading payouts. Please try again.")
        return redirect('/home')

@app.route('/request_payout', methods=['POST'])
@login_required
def request_payout():
    firebase_uid = session.get('user_id')
    if not firebase_uid:
        flash("Please log in to request a payout.", "error")
        return redirect(url_for('login'))
    
    stokvel_id = request.form.get('stokvel_id')
    amount = request.form.get('amount')
    description = request.form.get('description')

    if not all([stokvel_id, amount, description]):
        flash("Stokvel, amount, and description are required for a payout request.")
        return redirect('/payouts')

    try:
        amount = float(amount)
        stokvel_id = int(stokvel_id)

        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Check if the user is actually a member of this stokvel
                cur.execute("""
                    SELECT 1 FROM stokvel_members
                    WHERE stokvel_id = %s AND user_id = %s
                """, (stokvel_id, firebase_uid))
                if not cur.fetchone():
                    flash("You are not a member of this stokvel.")
                    return redirect('/payouts')

                # For simplicity, directly record as 'pending'.
                # In a real app, this would be a 'pending' status requiring approval.
                cur.execute("""
                    INSERT INTO transactions (user_id, stokvel_id, amount, type, description, transaction_date, status)
                    VALUES (%s, %s, %s, 'payout', %s, CURRENT_TIMESTAMP, 'pending')
                """, (firebase_uid, stokvel_id, amount, description))
                conn.commit()
                
                # Get stokvel name and admin user for notification
                cur.execute("""
                    SELECT s.name, sm.user_id 
                    FROM stokvels s
                    JOIN stokvel_members sm ON s.id = sm.stokvel_id
                    WHERE s.id = %s AND sm.role = 'admin'
                """, (stokvel_id,))
                stokvel_info = cur.fetchone()

                if stokvel_info:
                    stokvel_name, admin_user_id = stokvel_info
                    
                    # Get the requesting user's name
                    cur.execute("SELECT username FROM users WHERE firebase_uid = %s", (firebase_uid,))
                    user_info = cur.fetchone()
                    user_name = user_info[0] if user_info else "A member"

<<<<<<< HEAD
                # For simplicity, directly record as completed.
                # In a real app, this would be a 'pending' status requiring approval.
                cur.execute("""
                    INSERT INTO transactions (user_id, stokvel_id, amount, type, description, transaction_date, status, transaction_type)
                    VALUES (%s, %s, %s, 'payout', %s, CURRENT_DATE, 'completed', 'money')
                """, (firebase_uid, stokvel_id, amount, description))
                conn.commit()

                # Create notification for stokvel admin
                if stokvel_info and admin_user_id:
=======
                    # Create notification for stokvel admin
>>>>>>> 09799e6ad57bc08de1445d08a85e35f4e73d014d
                    message = f"{user_name} requested a payout of R{amount:.2f} from '{stokvel_name}' stokvel."
                    link = url_for('payouts') # Changed from 'payouts' to the specific admin approval page if one exists
                    create_notification(admin_user_id, message, link_url=link, notification_type='payout_requested')

        flash("Payout request submitted successfully!")
        return redirect('/payouts')
    except ValueError:
        flash("Amount must be a number.")
        return redirect('/payouts')
    except Exception as e:
        print(f"Error requesting payout: {e}")
        flash("An error occurred while requesting your payout. Please try again.")
        return redirect('/payouts')

@app.route('/savings_goals')
@login_required
def savings_goals():
    firebase_uid = session['user_id']
    try:
        with support.db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Use firebase_uid directly since the database now uses Firebase UIDs
                cur.execute("""
                    SELECT id, name, target_amount, current_amount, target_date, status, created_at
                    FROM savings_goals
                    WHERE user_id = %s
                    ORDER BY target_date ASC
                """, (firebase_uid,))
                goals = cur.fetchall()

        # Calculate banner stats
        total_goals = len(goals)
        completed_goals = sum(1 for goal in goals if goal['status'] == 'completed')
        total_saved_in_goals = sum(goal['current_amount'] for goal in goals)
        total_target_of_goals = sum(goal['target_amount'] for goal in goals)
        overall_progress = (total_saved_in_goals / total_target_of_goals * 100) if total_target_of_goals > 0 else 0

        banner_stats = {
            'total_goals': total_goals,
            'completed_goals': completed_goals,
            'total_saved': total_saved_in_goals,
            'overall_progress': overall_progress
        }

        return render_template('savings_goals.html', goals=goals, banner_stats=banner_stats)
    except Exception as e:
        print(f"Savings goals page error: {e}")
        flash("An error occurred while loading your savings goals. Please try again.")
        return redirect('/home')

@app.route('/create_savings_goal', methods=['POST'])
@login_required
def create_savings_goal():
    firebase_uid = session['user_id']
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid JSON request.'}), 400

    name = data.get('name')
    target_amount = data.get('target_amount')
    target_date = data.get('target_date')

    if not all([name, target_amount, target_date]):
        return jsonify({'success': False, 'message': 'All fields are required.'}), 400

    try:
        target_amount = float(target_amount)
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO savings_goals (user_id, name, target_amount, current_amount, target_date, status)
                    VALUES (%s, %s, %s, %s, %s, 'active')
                """, (firebase_uid, name, target_amount, 0.0, target_date))
                conn.commit()

        return jsonify({'success': True, 'message': f"Savings goal '{name}' created successfully!"})
            
    except ValueError:
        return jsonify({'success': False, 'message': 'Target amount must be a number.'}), 400
            
    except Exception as e:
        print(f"Error creating savings goal: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while creating the savings goal. Please try again.'}), 500

@app.route('/contribute_to_goal', methods=['POST'])
@login_required
def contribute_to_goal():
    firebase_uid = session['user_id']
    goal_id = request.form.get('goal_id')
    amount = request.form.get('amount')

    if not all([goal_id, amount]):
        flash("Goal ID and amount are required.")
        return redirect('/savings_goals')

    try:
        amount = Decimal(amount)
        if amount <= 0:
            flash("Contribution amount must be greater than zero.")
            return redirect('/savings_goals')

        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Verify the goal belongs to the user
                cur.execute("""
                    SELECT target_amount, current_amount
                    FROM savings_goals
                    WHERE id = %s AND user_id = %s
                """, (goal_id, firebase_uid))
                goal = cur.fetchone()

                if not goal:
                    flash("Invalid savings goal.")
                    return redirect('/savings_goals')

                target_amount, current_amount = goal
                new_amount = current_amount + amount

                # Update the current amount
                cur.execute("""
                    UPDATE savings_goals
                    SET current_amount = %s,
                        status = CASE 
                            WHEN %s >= target_amount THEN 'completed'
                            ELSE status
                        END
                    WHERE id = %s
                """, (new_amount, new_amount, goal_id))

                # Record the transaction
                cur.execute("""
                    INSERT INTO transactions (user_id, amount, type, description, savings_goal_id)
                    VALUES (%s, %s, 'savings_contribution', 'Contribution to savings goal', %s)
                """, (firebase_uid, amount, goal_id))

                conn.commit()

        flash(f"Successfully contributed R{amount:.2f} to your savings goal!")
        return redirect('/savings_goals')

    except InvalidOperation:
        flash("Invalid amount specified.")
        return redirect('/savings_goals')
    except Exception as e:
        print(f"Error contributing to savings goal: {e}")
        flash("An error occurred while processing your contribution. Please try again.")
        return redirect('/savings_goals')

@app.route('/stokvel/<int:stokvel_id>/members')
@login_required
def view_stokvel_members(stokvel_id):
    print(f"DEBUG: Navigating to view_stokvel_members for stokvel_id: {stokvel_id}") # Debug log
    try:
        user_id = session.get('user_id') # Ensure user_id is retrieved for permission checks
        if not user_id:
            flash("Please log in to view stokvel members.")
            return redirect('/login')

        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Get stokvel details, including id and description
                cur.execute("SELECT id, name, description, monthly_contribution, target_amount, target_date, total_pool FROM stokvels WHERE id = %s", (stokvel_id,))
                stokvel_tuple = cur.fetchone()
                print(f"DEBUG: Stokvel query result: {stokvel_tuple}") # Debug log

                if not stokvel_tuple:
                    flash("Stokvel not found.")
                    print(f"DEBUG: Stokvel with id {stokvel_id} not found.") # Debug log
                    return redirect('/stokvels')

                # Convert stokvel tuple to a dictionary
                stokvel_keys = ['id', 'name', 'description', 'monthly_contribution', 'target_amount', 'target_date', 'total_pool']
                stokvel = dict(zip(stokvel_keys, stokvel_tuple))
                print(f"DEBUG: Converted stokvel dict: {stokvel}") # Debug log

                # Get registered members (joined with users)
                cur.execute("""
                    SELECT u.username, u.email, sm.role, sm.id as member_id
                    FROM users u
                    JOIN stokvel_members sm ON u.firebase_uid = sm.user_id
                    WHERE sm.stokvel_id = %s
                """, (stokvel_id,))
                members_tuples = cur.fetchall()
                print(f"DEBUG: Members query result: {members_tuples}") # Debug log

                # Get pending members (no user_id, just email)
                cur.execute("""
                    SELECT NULL as username, NULL as email, sm.role, sm.id as member_id
                    FROM stokvel_members sm
                    WHERE sm.stokvel_id = %s AND sm.user_id IS NULL
                """, (stokvel_id,))
                pending_members_tuples = cur.fetchall()
                print(f"DEBUG: Pending members query result: {pending_members_tuples}") # Debug log

                # Combine both lists
                all_members_tuples = list(members_tuples) + list(pending_members_tuples)

                # Convert members tuples to a list of dictionaries
                members_list = []
                member_keys = ['username', 'email', 'role', 'member_id']
                for member_tuple in all_members_tuples:
                    members_list.append(dict(zip(member_keys, member_tuple)))
                print(f"DEBUG: Converted members list: {members_list}") # Debug log

                # Check if current user is a member and their role
                cur.execute("""
                    SELECT role FROM stokvel_members WHERE stokvel_id = %s AND user_id = %s
                """, (stokvel_id, user_id))
                user_stokvel_role = cur.fetchone()
                is_member = user_stokvel_role is not None
                user_role_in_stokvel = user_stokvel_role[0] if user_stokvel_role else 'none'
                print(f"DEBUG: Current user {user_id} role in stokvel {stokvel_id}: {user_role_in_stokvel}, Is member: {is_member}") # Debug log

        return render_template('stokvel_members.html', stokvel=stokvel, members=members_list, stokvel_id=stokvel_id, is_member=is_member, user_role_in_stokvel=user_role_in_stokvel)
    except Exception as e:
        print(f"ERROR: view_stokvel_members failed: {e}") # Enhanced error logging
        flash("An error occurred while loading stokvel members. Please try again.")
        return redirect('/stokvels')

@app.route('/stokvel/<int:stokvel_id>/add_member', methods=['POST'])
@login_required
def add_stokvel_member(stokvel_id):
    current_user_id = session['user_id']
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Check if current user is an admin of this stokvel
                cur.execute("SELECT role FROM stokvel_members WHERE stokvel_id = %s AND user_id = %s", (stokvel_id, current_user_id))
                role_result = cur.fetchone()
                if not role_result or role_result[0] != 'admin':
                    flash("You do not have permission to add members to this stokvel.", "danger")
                    return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))

                email_to_add = request.form.get('email')
                if not email_to_add:
                    flash("Email is required.", "warning")
                    return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))

                # Find user by email
                cur.execute("SELECT firebase_uid FROM users WHERE email = %s", (email_to_add,))
                user_to_add = cur.fetchone()

                if not user_to_add:
                    flash(f"No registered user found with email {email_to_add}.", "danger")
                    return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))
                
                user_id_to_add = user_to_add[0]

                # Check if user is already a member
                cur.execute("SELECT 1 FROM stokvel_members WHERE stokvel_id = %s AND user_id = %s", (stokvel_id, user_id_to_add))
                if cur.fetchone():
                    flash(f"{email_to_add} is already a member of this stokvel.", "info")
                    return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))

                # Add the new member
                cur.execute("INSERT INTO stokvel_members (stokvel_id, user_id, role) VALUES (%s, %s, %s)", (stokvel_id, user_id_to_add, 'member'))
                conn.commit()

                # Send email notification to the new member
                try:
                    import sendgrid
                    from sendgrid.helpers.mail import Mail
                    import os
                    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
                    # Fetch stokvel name for the email
                    cur.execute("SELECT name FROM stokvels WHERE id = %s", (stokvel_id,))
                    stokvel_name = cur.fetchone()[0]
                    message = Mail(
                        from_email=os.environ.get('MAIL_SENDER_EMAIL', 'noreply@kasikash.com'),
                        to_emails=email_to_add,
                        subject='You have been added to a Stokvel!',
                        html_content=f'You have been added to the stokvel "{stokvel_name}". Log in to KasiKash to view details.'
                    )
                    sg.send(message)
                except Exception as e:
                    print(f"Error sending email: {e}")

                flash(f"Successfully added {email_to_add} to the stokvel.", "success")
    except Exception as e:
        print(f"Error adding stokvel member: {e}")
        flash("An error occurred while adding the member.", "danger")
    
    return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))

@app.route('/stokvel/<int:stokvel_id>/remove_member', methods=['POST'])
@login_required
def remove_stokvel_member(stokvel_id):
    current_user_id = session['user_id']
    member_id = request.form.get('member_id')
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Check if current user is an admin of this stokvel
                cur.execute("SELECT role FROM stokvel_members WHERE stokvel_id = %s AND user_id = %s", (stokvel_id, current_user_id))
                role_result = cur.fetchone()
                if not role_result or role_result[0] != 'admin':
                    flash("You do not have permission to remove members from this stokvel.", "danger")
                    return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))

                # Prevent removing the last admin
                cur.execute("SELECT COUNT(*) FROM stokvel_members WHERE stokvel_id = %s AND role = 'admin'", (stokvel_id,))
                admin_count = cur.fetchone()[0]

                cur.execute("SELECT role FROM stokvel_members WHERE id = %s", (member_id,))
                member_to_remove_role = cur.fetchone()

                if member_to_remove_role and member_to_remove_role[0] == 'admin' and admin_count <= 1:
                    flash("You cannot remove the last admin from the stokvel.", "warning")
                    return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))

                # Remove the member
                cur.execute("DELETE FROM stokvel_members WHERE id = %s", (member_id,))
                conn.commit()

                flash("Member removed successfully.", "success")
    except Exception as e:
        print(f"Error removing stokvel member: {e}")
        flash("An error occurred while removing the member.", "danger")
    
    return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))

@app.route('/stokvel/<int:stokvel_id>/join', methods=['POST'])
@login_required
def join_stokvel(stokvel_id):
    user_id = session['user_id']
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Check if already a member
                cur.execute("SELECT 1 FROM stokvel_members WHERE stokvel_id = %s AND user_id = %s", (stokvel_id, user_id))
                if cur.fetchone():
                    flash("You are already a member of this stokvel.")
                    return redirect(f'/stokvel/{stokvel_id}/members')

                cur.execute("INSERT INTO stokvel_members (stokvel_id, user_id) VALUES (%s, %s)", (stokvel_id, user_id))
                conn.commit()
        flash("Successfully joined the stokvel!")
        return redirect(f'/stokvel/{stokvel_id}/members')
    except Exception as e:
        print(f"Error joining stokvel: {e}")
        flash("An error occurred while trying to join the stokvel. Please try again.")
        return redirect('/stokvels')


@app.route('/stokvel/<int:stokvel_id>/leave', methods=['POST'])
@login_required
def leave_stokvel(stokvel_id):
    user_id = session['user_id']
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM stokvel_members WHERE stokvel_id = %s AND user_id = %s", (stokvel_id, user_id))
                conn.commit()
        flash("Successfully left the stokvel.")
        return redirect('/stokvels')
    except Exception as e:
        print(f"Error leaving stokvel: {e}")
        flash("An error occurred while trying to leave the stokvel. Please try again.")
        return redirect(f'/stokvel/{stokvel_id}/members')


@app.route('/stokvel/<int:stokvel_id>/delete', methods=['POST'])
@login_required
def delete_stokvel(stokvel_id):
    # Only the creator or an admin should be able to delete a stokvel
    # For simplicity, we'll allow any logged-in user who created it (if we tracked creation)
    # or an admin to delete it. For now, assuming direct delete access.
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Delete all related transactions first
                cur.execute("DELETE FROM transactions WHERE stokvel_id = %s", (stokvel_id,))
                # Delete all members from this stokvel
                cur.execute("DELETE FROM stokvel_members WHERE stokvel_id = %s", (stokvel_id,))
                # Delete the stokvel itself
                cur.execute("DELETE FROM stokvels WHERE id = %s", (stokvel_id,))
                conn.commit()
        flash("Stokvel deleted successfully!")
        return redirect('/stokvels')
    except Exception as e:
        print(f"Error deleting stokvel: {e}")
        flash("An error occurred while deleting the stokvel. Please try again.")
        return redirect('/stokvels')


@app.route('/notifications')
@login_required
def notifications():
    user_id = session['user_id']
    try:
        with support.db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM notifications 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC
                """, (user_id,))
                notifications = cur.fetchall()
                # Mark notifications as read
                cur.execute("UPDATE notifications SET is_read = TRUE WHERE user_id = %s", (user_id,))
                conn.commit()
        return render_template('notifications.html', notifications=notifications)
    except Exception as e:
        print(f"Error fetching notifications: {e}")
        flash("Could not load notifications.", "danger")
        return redirect(url_for('home'))

@app.route('/notifications/clear', methods=['POST'])
@login_required
def clear_notifications():
    user_id = session['user_id']
    try:
        support.execute_query("delete", "DELETE FROM notifications WHERE user_id = %s", (user_id,))
        flash("All notifications cleared.", "success")
    except Exception as e:
        print(f"Error clearing notifications: {e}")
        flash("Failed to clear notifications.", "danger")
    return redirect(url_for('notifications'))

@app.route('/notifications/count')
@login_required
def notifications_count():
    count = get_notification_count(session.get('user_id'))
    return jsonify({'count': count})


@app.route('/payment_methods')
@login_required
def payment_methods():
    firebase_uid = session['user_id']
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, type, details, is_default, created_at
                    FROM payment_methods
                    WHERE user_id = %s
                    ORDER BY is_default DESC, created_at DESC
                """, (firebase_uid,))
                payment_methods_tuples = cur.fetchall()

                # Convert tuples to dictionaries for easier access in template
                payment_methods_list = []
                payment_method_keys = ['id', 'type', 'details', 'is_default', 'created_at']
                for pm_tuple in payment_methods_tuples:
                    payment_methods_list.append(dict(zip(payment_method_keys, pm_tuple)))
                
        return render_template('payment_methods.html', payment_methods=payment_methods_list)
    except Exception as e:
        print(f"Payment methods page error: {e}")
        flash("An error occurred while loading your payment methods. Please try again.")
        return render_template('payment_methods.html', payment_methods=[])

@app.route('/add_payment_method', methods=['POST'])
@login_required
def add_payment_method():
    user_id = session['user_id']
    payment_type = request.form.get('type')
    details = request.form.get('details')
    is_default = request.form.get('is_default') == 'true' # Checkbox value

    if not all([payment_type, details]):
        flash("Payment type and details are required.")
        return redirect('/payment_methods')

    try:
        # Validate that details is valid JSON
        import json
        details_json = json.loads(details)

        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # If new method is set as default, clear existing default
                if is_default:
                    cur.execute("UPDATE payment_methods SET is_default = FALSE WHERE user_id = %s", (user_id,))
                
                cur.execute("""
                    INSERT INTO payment_methods (user_id, type, details, is_default)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, payment_type, details, is_default))
                conn.commit()

        flash("Payment method added successfully!")
        return redirect('/payment_methods')
    except json.JSONDecodeError:
        flash("Invalid payment details format. Please provide valid JSON.")
        return redirect('/payment_methods')
    except Exception as e:
        print(f"Error adding payment method: {e}")
        flash("An error occurred while adding the payment method. Please try again.")
        return redirect('/payment_methods')

@app.route('/set_default_payment_method', methods=['POST'])
@login_required
def set_default_payment_method():
    user_id = session['user_id']
    method_id = request.form.get('method_id')

    if not method_id:
        flash("Method ID is required.")
        return redirect('/payment_methods')

    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Clear existing default
                cur.execute("UPDATE payment_methods SET is_default = FALSE WHERE user_id = %s", (user_id,))
                # Set new default
                cur.execute("""
                    UPDATE payment_methods 
                    SET is_default = TRUE 
                    WHERE id = %s AND user_id = %s
                """, (method_id, user_id))
                conn.commit()

        flash("Default payment method updated successfully!")
        return redirect('/payment_methods')
    except Exception as e:
        print(f"Error setting default payment method: {e}")
        flash("An error occurred while updating the default payment method. Please try again.")
        return redirect('/payment_methods')

@app.route('/delete_payment_method', methods=['POST'])
@login_required
def delete_payment_method():
    user_id = session['user_id']
    method_id = request.form.get('method_id')

    if not method_id:
        flash("Method ID is required.")
        return redirect('/payment_methods')

    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM payment_methods 
                    WHERE id = %s AND user_id = %s
                """, (method_id, user_id))
                conn.commit()

        flash("Payment method deleted successfully!")
        return redirect('/payment_methods')
    except Exception as e:
        print(f"Error deleting payment method: {e}")
        flash("An error occurred while deleting the payment method. Please try again.")
        return redirect('/payment_methods')


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    user_id = session['user_id']
    try:
        with support.db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Fetch general user settings from users table
                cur.execute("""
                    SELECT language_preference, two_factor_enabled 
                    FROM users 
                    WHERE firebase_uid = %s
                """, (user_id,))
                user_settings = cur.fetchone() or {}

                # Fetch notification/app preferences from user_settings table
                cur.execute("""
                    SELECT email_notifications, sms_notifications, weekly_summary, receive_promotions
                    FROM user_settings
                    WHERE user_id = %s
                """, (user_id,))
                app_settings = cur.fetchone() or {}
                user_settings.update(app_settings)
        
        # Fallback for language preference if not in DB
        if 'language_preference' not in user_settings:
            user_settings['language_preference'] = session.get('language_preference', 'en')

        return render_template('settings.html', user=user_settings)
    except Exception as e:
        print(f"Error loading settings: {e}")
        flash("An error occurred while loading settings.", "danger")
        return redirect(url_for('home'))

@app.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    user_id = session['user_id']
    form_section = request.form.get('form_section')

    query = None
    params = None

    if form_section == 'language_preference':
        language = request.form.get('language_preference')
        if language:
            session['language_preference'] = language
            query = "UPDATE users SET language_preference = %s WHERE firebase_uid = %s"
            params = (language, user_id)

    elif form_section == 'app_preferences':
        email_notifications = 'email_notifications' in request.form
        sms_notifications = 'sms_notifications' in request.form
        weekly_summary = 'weekly_summary' in request.form
        receive_promotions = 'receive_promotions' in request.form
        query = """
<<<<<<< HEAD
                    UPDATE users
            SET email_notifications = %s, sms_notifications = %s, weekly_summary = %s, reminders_enabled = %s
                    WHERE firebase_uid = %s
=======
            UPDATE user_settings
            SET email_notifications = %s, sms_notifications = %s, weekly_summary = %s, receive_promotions = %s
            WHERE user_id = %s
>>>>>>> 09799e6ad57bc08de1445d08a85e35f4e73d014d
        """
        params = (email_notifications, sms_notifications, weekly_summary, receive_promotions, user_id)

    elif form_section == 'security':
        two_factor_enabled = 'two_factor_enabled' in request.form
        query = "UPDATE users SET two_factor_enabled = %s WHERE firebase_uid = %s"
        params = (two_factor_enabled, user_id)

    if query and params:
        try:
            support.execute_query("update", query, params)
            flash("Settings updated successfully!", "success")
        except Exception as e:
            print(f"Error updating settings for section {form_section}: {e}")
            flash("An error occurred while updating settings.", "danger")
    else:
        flash("Invalid settings update request.", "warning")
    return redirect(url_for('settings'))


def update_user_setting(user_id, section, setting, value):
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Map settings to database columns
                column = None
                if section == 'general':
                    if setting == 'username':
                        column = 'username'
                    elif setting == 'email':
                        column = 'email'
                elif section == 'notifications':
                    if setting == 'email_notifications':
                        column = 'notification_preferences'
                elif section == 'security':
                    if setting == 'two_factor_auth':
                        column = 'two_factor_enabled'

                if not column:
                    print(f"Debug: Invalid setting or section for update: {section}, {setting}")
                    return False

                # Update the setting in the database
                cur.execute(f"""
                    UPDATE users 
                    SET {column} = %s 
                    WHERE firebase_uid = %s
                """, (value, user_id))
                
                conn.commit()
                return True
    except Exception as e:
        print(f"Error updating user setting: {str(e)}")
        return False
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/profile')
@login_required
def profile():
    try:
        with support.db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Get user data
                cur.execute("""
                    SELECT u.*, 
                           COUNT(DISTINCT s.id) as active_stokvels_count,
                           COALESCE(SUM(CASE WHEN t.type = 'contribution' THEN t.amount ELSE 0 END), 0) as total_contributions,
                           COALESCE(SUM(CASE WHEN t.type = 'withdrawal' THEN t.amount ELSE 0 END), 0) as total_withdrawals
                    FROM users u
                    LEFT JOIN stokvel_members sm ON u.firebase_uid = sm.user_id
                    LEFT JOIN stokvels s ON sm.stokvel_id = s.id
                    LEFT JOIN transactions t ON u.firebase_uid = t.user_id
                    WHERE u.firebase_uid = %s
                    GROUP BY u.id
                """, (session['user_id'],))
                user = cur.fetchone()
                
                if not user:
                    flash('User profile not found')
                    return redirect(url_for('home'))
                
                # Get current time for greeting
                current_time = datetime.now()

                # Fetch email verification status from Firebase
                from firebase_admin import auth
                try:
                    firebase_user = auth.get_user(session['user_id'])
                    is_verified = firebase_user.email_verified
                except Exception as e:
                    print(f"Error fetching Firebase user for verification status: {e}")
                    is_verified = False
                user['is_verified'] = is_verified
                
                return render_template('profile.html', 
                                     user=user, 
                                     current_time=current_time,
                                     active_stokvels_count=user['active_stokvels_count'],
                                     total_contributions=user['total_contributions'],
                                     total_withdrawals=user['total_withdrawals'])
    except Exception as e:
        print(f"Error in profile route: {e}")
        flash('Error loading profile')
        return redirect(url_for('home'))

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    user_id = session['user_id']
    username = request.form.get('username')
    phone = request.form.get('phone')
    date_of_birth = request.form.get('date_of_birth')
    bio = request.form.get('bio')
    full_name = request.form.get('full_name')
    id_number = request.form.get('id_number')
    address = request.form.get('address')
    
    query = "UPDATE users SET username = %s, phone = %s, date_of_birth = %s, bio = %s, full_name = %s, id_number = %s, address = %s WHERE firebase_uid = %s"
    support.execute_query("update", query, (username, phone, date_of_birth, bio, full_name, id_number, address, user_id))
    return redirect(url_for('profile'))

@app.route('/profile/upload_picture', methods=['POST'])
@login_required
def upload_profile_picture():
    user_id = session['user_id']
    if 'profile_picture' not in request.files:
        flash('No file part', 'warning')
        return redirect(url_for('profile'))
    file = request.files['profile_picture']
    if file.filename == '':
        flash('No selected file', 'warning')
        return redirect(url_for('profile'))
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{user_id}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Update user profile picture path in database
        support.execute_query("update", "UPDATE users SET profile_picture = %s WHERE firebase_uid = %s", (filename, user_id))
        flash('Profile picture updated successfully!', 'success')
    else:
        flash('Invalid file type', 'danger')
    return redirect(url_for('profile'))

@app.route('/profile/upload_kyc', methods=['POST'])
@login_required
def upload_kyc():
    user_id = session['user_id']
    id_doc = request.files.get('id_document')
    address_doc = request.files.get('address_document')

    if not id_doc or not address_doc:
        flash('Both ID document and proof of address are required.', 'warning')
        return redirect(url_for('profile'))

    # Validate file types
    if not (allowed_kyc_file(id_doc.filename) and allowed_kyc_file(address_doc.filename)):
        flash('Invalid file type. Only PDF, PNG, JPG, JPEG, and GIF are allowed.', 'danger')
        return redirect(url_for('profile'))

    # Ensure upload directory exists
    os.makedirs(app.config['KYC_UPLOAD_FOLDER'], exist_ok=True)

    try:
        id_filename = secure_filename(f"{user_id}_id_{id_doc.filename}")
        address_filename = secure_filename(f"{user_id}_address_{address_doc.filename}")

        id_filepath = os.path.join(app.config['KYC_UPLOAD_FOLDER'], id_filename)
        address_filepath = os.path.join(app.config['KYC_UPLOAD_FOLDER'], address_filename)

        id_doc.save(id_filepath)
        address_doc.save(address_filepath)

        # Update user's KYC info in the database (use correct columns)
        query = "UPDATE users SET id_document = %s, proof_of_address = %s WHERE firebase_uid = %s"
        support.execute_query("update", query, (id_filename, address_filename, user_id))

        flash('KYC documents uploaded successfully. They are pending review.', 'success')
    except Exception as e:
        flash(f'An error occurred during KYC upload: {e}', 'danger')

    return redirect(url_for('profile'))           

# Register context processor for user info and translation function
@app.context_processor
def inject_user_name():
    username = None
    language_preference = 'en'  # Default language
    notification_count = 0  # Default notification count
    
    if 'user_id' in session:
        # Changed to firebase_uid
        user_query = "SELECT username FROM users WHERE firebase_uid = %s"
        user_data = support.execute_query("search", user_query, (session['user_id'],))
        if user_data:
            username = user_data[0][0]
        
        # Get notification count
        notification_count = get_notification_count(session['user_id'])
        
        # Get user's language preference from session first, then try database
        if 'language_preference' in session:
            language_preference = session['language_preference']
        else:
            try:
                lang_query = "SELECT language_preference FROM users WHERE firebase_uid = %s"
                lang_data = support.execute_query("search", lang_query, (session['user_id'],))
                if lang_data and lang_data[0][0]:
                    language_preference = lang_data[0][0]
                    session['language_preference'] = language_preference
            except Exception as e:
                print(f"Error getting language preference from database: {e}")
                language_preference = session.get('language_preference', 'en')
    
    return dict(username=username, user_language=language_preference, notification_count=notification_count, t=get_text)

def send_email(to_email, subject, body):
    try:
        # Get email settings from environment variables
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        from_email = os.getenv('FROM_EMAIL', smtp_username)

        # DEBUG: Print loaded environment variables (REMOVE IN PRODUCTION)
        print(f"DEBUG: send_email - SMTP_SERVER: {smtp_server}")
        print(f"DEBUG: send_email - SMTP_PORT: {smtp_port}")
        print(f"DEBUG: send_email - SMTP_USERNAME: {smtp_username}")
        print(f"DEBUG: send_email - SMTP_PASSWORD: {'*' * len(str(smtp_password))}") # Mask password for security
        print(f"DEBUG: send_email - FROM_EMAIL: {from_email}")

        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject

        # Add body
        msg.attach(MIMEText(body, 'html'))

        # Create SMTP session
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        
        # Send email
        server.send_message(msg)
        server.quit()
        print(f"Debug: Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Debug: Error sending email: {str(e)}")
        return False

@app.route('/pricing')
def pricing():
    try:
        # Correctly use support.db_connection() as a context manager
        with support.db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM pricing_plans")
                pricing_plans = cursor.fetchall()
        return render_template('pricing.html', pricing_plans=pricing_plans)
    except Exception as e:
        print(f"Error fetching pricing plans: {e}")
        flash("Could not load pricing plans. Please try again later.", "error")
        return render_template('pricing.html', pricing_plans=[]) # Render with empty list on error

@app.route('/chat', methods=['POST'])
@login_required
def handle_chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400

        user_message = data['message']
        mode = data.get('mode', 'ai')  # Default to AI mode if not provided
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401

        # Fetch user context from database (username, total_saved, stokvels, transactions)
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Get username
                cur.execute("SELECT username FROM users WHERE firebase_uid = %s", (user_id,))
                user = cur.fetchone()
                username = user[0] if user else 'User'
                
                # Get total savings
                cur.execute("""
                    SELECT SUM(amount) FROM transactions
                    WHERE user_id = %s AND type = 'contribution' AND status = 'completed'
                """, (user_id,))
                total_saved = cur.fetchone()[0] or 0
                
                # Get stokvel memberships
                cur.execute("""
                    SELECT s.name, s.monthly_contribution, s.target_date 
                    FROM stokvels s 
                    JOIN stokvel_members sm ON s.id = sm.stokvel_id 
                    WHERE sm.user_id = %s
                """, (user_id,))
                stokvels = cur.fetchall()
                
                # Get recent transactions
                cur.execute("""
                    SELECT amount, type, description, transaction_date 
                    FROM transactions 
                    WHERE user_id = %s 
                    ORDER BY transaction_date DESC 
                    LIMIT 5
                """, (user_id,))
                transactions = cur.fetchall()

        if mode == 'ai':
            # Use OpenRouter with Google Gemma 3n 4B model
            if openrouter_available:
                try:
                    # Broader system prompt for general financial and knowledge questions
                    system_prompt = (
                        f"You are KasiKash AI, a helpful and knowledgeable assistant. "
                        f"You can answer questions about stokvels, personal finance, the stock market, general financial topics, and more. "
                        f"User: {username}, Saved: R{total_saved}, Stokvels: {len(stokvels)}. "
                        "Be concise, accurate, and helpful. Do not use Markdown or asterisks for formatting. Respond in plain text only. "
                        "Do not invent organization names, websites, or mix languages/scripts. If you do not know the answer, say so or suggest consulting a reputable source.\n\n"
                    )
                    full_message = f"{system_prompt}{user_message}"
                    response = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={"Authorization": f"Bearer {openrouter_api_key}"},
                        json={
                            "model": "google/gemma-3n-e4b-it:free",
                            "messages": [{"role": "user", "content": full_message}],
                            "max_tokens": 300,  # Reduced for faster responses
                            "temperature": 0.7
                        },
                        timeout=10  # 10 second timeout
                    )
                    if response.status_code == 200:
                        response_data = response.json()
                        response = response_data['choices'][0]['message']['content']
                    else:
                        print(f"OpenRouter API error: {response.status_code} - {response.text}")
                        response = "I'm having trouble connecting to my AI service right now. Please try again later."
                except requests.exceptions.Timeout:
                    print("OpenRouter API timeout")
                    response = "The AI service is taking too long to respond. Please try again."
                except Exception as e:
                    print(f"OpenRouter API error: {e}")
                    response = "I'm having trouble connecting to my AI service right now. Please try again later or contact support if the issue persists."
            else:
                response = "AI mode is not available right now. Please try again later or use App Mode."
        else:
            # App Mode (formerly Rule-based Mode)
            user_message_lower = user_message.lower().strip()
            response = None
            chat_state = session.get('chat_state')
            stokvel_data = session.get('stokvel_data', {})

            # Multi-turn stokvel creation flow
            if chat_state == 'stokvel_creation':
                # Allow cancel
                if user_message_lower in ['cancel', 'stop', 'exit']:
                    session.pop('chat_state', None)
                    session.pop('stokvel_data', None)
                    response = "Stokvel creation cancelled. Let me know if you want to start again!"
                # Step 1: Name
                elif 'name' not in stokvel_data:
                    stokvel_data['name'] = user_message.strip()
                    session['stokvel_data'] = stokvel_data
                    response = "What is the monthly contribution amount? (e.g., 500)"
                # Step 2: Monthly contribution
                elif 'monthly_contribution' not in stokvel_data:
                    try:
                        amount = float(user_message.strip())
                        if amount <= 0:
                            raise ValueError
                        stokvel_data['monthly_contribution'] = amount
                        session['stokvel_data'] = stokvel_data
                        response = "What is the target date for your stokvel? (e.g., 2025-12-31)"
                    except Exception:
                        response = "Please enter a valid positive number for the monthly contribution."
                # Step 3: Target date
                elif 'target_date' not in stokvel_data:
                    try:
                        # Use dateutil to parse a wide range of date formats
                        dt = date_parser.parse(user_message.strip(), dayfirst=False, yearfirst=True)
                        stokvel_data['target_date'] = dt.strftime('%Y-%m-%d')  # Store in standard format
                        session['stokvel_data'] = stokvel_data
                        response = "Please describe the rules or purpose of your stokvel."
                    except Exception:
                        response = "That date is invalid or in the wrong format. Please enter a valid date like 2025-12-31."
                # Step 4: Rules
                elif 'rules' not in stokvel_data:
                    stokvel_data['rules'] = user_message.strip()
                    session['stokvel_data'] = stokvel_data
                    # All info collected, create stokvel
                    try:
                        with support.db_connection() as conn:
                            with conn.cursor() as cur:
                                # Insert into stokvels (store rules in description)
                                cur.execute("""
                                    INSERT INTO stokvels (name, monthly_contribution, target_date, description)
                                    VALUES (%s, %s, %s, %s) RETURNING id
                                """, (
                                    stokvel_data['name'],
                                    stokvel_data['monthly_contribution'],
                                    stokvel_data['target_date'],
                                    stokvel_data['rules']
                                ))
                                stokvel_id = cur.fetchone()[0]
                                # Add user as admin member
                                cur.execute("""
                                    INSERT INTO stokvel_members (stokvel_id, user_id, role)
                                    VALUES (%s, %s, 'admin')
                                """, (stokvel_id, user_id))
                                conn.commit()
                        # Instead of clearing state, go to member adding state
                        session['chat_state'] = 'adding_stokvel_members'
                        session['new_stokvel_id'] = stokvel_id
                        session.pop('stokvel_data', None)
                        response = f"Your stokvel '{stokvel_data['name']}' has been created! Would you like to add members now? (Type their email or 'no' to finish)"
                    except Exception as e:
                        print(f"Error creating stokvel: {e}")
                        response = "Sorry, there was an error creating your stokvel. Please try again later."
                        session.pop('chat_state', None)
                        session.pop('stokvel_data', None)
                    return jsonify({'response': response})
                else:
                    response = "Something went wrong. Please type 'cancel' to start over."
                return jsonify({'response': response})

            # Multi-turn add members to stokvel flow
            if chat_state == 'adding_stokvel_members':
                if user_message_lower in ['no', 'done', 'finish', 'skip']:
                    session.pop('chat_state', None)
                    session.pop('new_stokvel_id', None)
                    response = "Stokvel setup complete! You can add more members later from the stokvel page."
                elif re.match(r"[^@]+@[^@]+\.[^@]+", user_message.strip()):
                    member_email = user_message.strip()
                    stokvel_id = session.get('new_stokvel_id')
                    try:
                        with support.db_connection() as conn:
                            with conn.cursor() as cur:
                                # Try to find user by email
                                cur.execute("SELECT firebase_uid FROM users WHERE email = %s", (member_email,))
                                user_to_add = cur.fetchone()
                                if user_to_add:
                                    cur.execute("INSERT INTO stokvel_members (stokvel_id, user_id, email, role, status) VALUES (%s, %s, %s, 'member', 'active')", (stokvel_id, user_to_add[0], member_email))
                                    conn.commit()
                                    response = f"{member_email} has been added to your stokvel! Add another email or type 'no' to finish."
                                else:
                                    # Add as pending member by email only
                                    cur.execute("INSERT INTO stokvel_members (stokvel_id, user_id, email, role, status) VALUES (%s, NULL, %s, 'pending', 'pending')", (stokvel_id, member_email))
                                    conn.commit()
                                    response = f"{member_email} has been added as a pending member. They will be able to join once they register. Add another email or type 'no' to finish."
                    except Exception as e:
                        print(f"Error adding member: {e}")
                        response = "Sorry, there was an error adding that member. Try again or type 'no' to finish."
                else:
                    response = "Please enter a valid email address to add a member, or type 'no' to finish."
                return jsonify({'response': response})

            # Start stokvel creation (move this above generic Q&A)
            if user_message_lower in [
                'create stokvel', 'i want to create a stokvel', 'start stokvel', 'open stokvel',
                'create a stokvel', 'new stokvel', 'add stokvel', 'begin stokvel creation'
            ]:
                session['chat_state'] = 'stokvel_creation'
                session['stokvel_data'] = {}
                return jsonify({'response': 'Great! What would you like to name your stokvel? (Type "cancel" to stop at any time)'})

            # List user's stokvels (move this above generic Q&A)
            if any(kw in user_message_lower for kw in ["my stokvels", "which stokvels am i a part of", "which stokvels do i belong to", "list my stokvels"]):
                try:
                    with support.db_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                SELECT name, description FROM stokvels s
                                JOIN stokvel_members sm ON s.id = sm.stokvel_id
                                WHERE sm.user_id = %s
                            """, (user_id,))
                            stokvels = cur.fetchall()
                            if stokvels:
                                stokvel_list = "\n".join([f"- {s[0]}: {s[1]}" for s in stokvels])
                                response = f"You are a member of the following stokvels:\n{stokvel_list}"
                            else:
                                response = "You are not a member of any stokvels yet."
                except Exception as e:
                    print(f"Error fetching stokvels: {e}")
                    response = "Sorry, I couldn't fetch your stokvels right now."
                return jsonify({'response': response})

            # --- Universal 5W/How/Feature Q&A ---
            # Define feature explanations
            feature_faq = {
                'stokvel': "A stokvel is a community savings group. You can create one, add members, make contributions, and request payouts.",
                'contribution': "A contribution is a payment you make to your stokvel. Go to 'Make Contribution' to add one.",
                'payout': "A payout is money withdrawn from the stokvel pool. You can request a payout from your stokvel page.",
                'payment method': "Payment methods are your saved cards or bank accounts. Add one in the Payment Methods section.",
                'savings goal': "A savings goal helps you track your progress toward a target amount. Set one in the Savings Goals section.",
                'dashboard': "The dashboard shows a summary of your financial activity, including balance, contributions, and loans.",
                'profile': "Your profile page shows your personal details and account statistics.",
                'settings': "The settings page lets you customize your app experience, including notifications and language.",
                'notification': "Notifications keep you updated on important events, like contributions or payout requests.",
            }

            # Check for feature-related questions
            for feature, explanation in feature_faq.items():
                # What/who questions
                if any(q in user_message_lower for q in [f"what is a {feature}", f"what are {feature}s", f"who is involved in a {feature}"]):
                    response = explanation
                    break
                # Where questions
                if any(q in user_message_lower for q in [f"where do i find my {feature}", f"where are my {feature}s", f"where can i manage {feature}s"]):
                    response = f"You can manage your {feature}s in the '{feature.replace('_', ' ').title()}' section of the app."
                    break
                # When/how questions
                if any(q in user_message_lower for q in [f"when can i get a {feature}", f"how do i get a {feature}", f"how do i make a {feature}"]):
                    response = explanation + f" You can usually initiate this from the '{feature.replace('_', ' ').title()}' page."
                    break

            if response:
                return jsonify({'response': response})

            # --- Fallback Responses ---
            if response is None:
                if 'hello' in user_message_lower or 'hi' in user_message_lower:
                    response = "Hello! How can I assist you with your finances today?"
                elif 'balance' in user_message_lower:
                    response = f"Your current balance is R{total_saved:.2f}. You can view details on the dashboard."
                elif 'help' in user_message_lower:
                    response = "I can help you create a stokvel, list your stokvels, or answer questions about features. What would you like to do?"
                else:
                    response = "I'm not sure how to handle that in App Mode. Try asking me to 'create a stokvel', or switch to AI Mode for more general questions."

        # Save chat history (for both modes)
        try:
            with support.db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO chat_history (user_id, message, response, mode)
                        VALUES (%s, %s, %s, %s)
                    """, (user_id, user_message, response, mode))
                    conn.commit()
        except Exception as e:
            print(f"Error saving chat history: {e}")

        return jsonify(response={'response': response, 'mode': mode, 'timestamp': datetime.now().strftime('%H:%M')})
    except Exception as e:
        print(f"Chat handler error: {e}")
        return jsonify({'error': 'An internal error occurred.'}), 500

@app.route('/stokvel/<int:stokvel_id>/statement/download')
@login_required
def download_stokvel_statement_pdf(stokvel_id):
    period = request.args.get('period', 'all')
    user_id = session.get('user_id')
    # Fetch stokvel info and transactions
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM stokvels WHERE id = %s", (stokvel_id,))
                stokvel = cur.fetchone()
                if not stokvel:
                    flash('Stokvel not found.', 'danger')
                    return redirect('/contributions')
                stokvel_name = stokvel[0]
                # Build period filter
                date_filter = ''
                params = [stokvel_id]
                if period == '30d':
                    date_filter = 'AND t.transaction_date >= CURRENT_DATE - INTERVAL \'30 days\''
                elif period == '3m':
                    date_filter = 'AND t.transaction_date >= CURRENT_DATE - INTERVAL \'3 months\''
                elif period == '6m':
                    date_filter = 'AND t.transaction_date >= CURRENT_DATE - INTERVAL \'6 months\''
                query = f"""
                    SELECT t.transaction_date, t.type, t.description, t.amount, u.email
                    FROM transactions t
                    LEFT JOIN users u ON t.user_id = u.firebase_uid
                    WHERE t.stokvel_id = %s {date_filter}
                    ORDER BY t.transaction_date
                """
                cur.execute(query, params)
                transactions = cur.fetchall()
    except Exception as e:
        print(f"Error generating statement PDF: {e}")
        flash('Could not generate statement.', 'danger')
        return redirect('/contributions')
    # Generate PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    # Add logo
    from reportlab.platypus import Image
    logo_path = os.path.join('static', 'kasikash-logo.png')
    if os.path.exists(logo_path):
        try:
            elements.append(Image(logo_path, width=120, height=60))
        except Exception as e:
            print(f"Error adding logo: {e}")
    # Add address
    address = "KasiKash, 123 Main Street, Johannesburg, South Africa"
    elements.append(Paragraph(address, styles['Normal']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"{stokvel_name} - Statement", styles['Title']))
    elements.append(Spacer(1, 12))
    # Table header
    data = [["Date", "Type", "Description", "Amount", "Member Email"]]
    for row in transactions:
        date_str = row[0].strftime('%Y-%m-%d') if row[0] else ''
        data.append([date_str, row[1], row[2], f"R{row[3]:.2f}", row[4] or ''])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2453c7')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"statement_{stokvel_id}_{period}.pdf", mimetype='application/pdf')

<<<<<<< HEAD
@app.route('/loan_requests')
@login_required
def loan_requests():
    user_id = session.get('user_id')
    loan_requests = []
    repayment_histories = {}
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Fetch user's loan requests
                cur.execute('''
                    SELECT lr.id, s.name, lr.amount, lr.status, lr.reason, lr.created_at
                    FROM loan_requests lr
                    JOIN stokvels s ON lr.stokvel_id = s.id
                    WHERE lr.user_id = %s
                    ORDER BY lr.created_at DESC
                ''', (user_id,))
                for row in cur.fetchall():
                    loan_id, stokvel_name, amount, status, reason, created_at = row
                    # Fetch repayments for this loan
                    cur.execute('''
                        SELECT amount, date FROM loan_repayments WHERE loan_id = %s ORDER BY date
                    ''', (loan_id,))
                    repayments = cur.fetchall()
                    repaid_total = sum(float(r[0]) for r in repayments)
                    remaining = float(amount) - repaid_total
                    loan_requests.append({
                        'id': loan_id,
                        'stokvel_name': stokvel_name,
                        'amount': float(amount),
                        'repaid_total': repaid_total,
                        'remaining': remaining,
                        'reason': reason,
                        'status': status,
                        'created_at': created_at.strftime('%Y-%m-%d') if created_at else '',
                    })
                    repayment_histories[loan_id] = [
                        {'amount': float(r[0]), 'date': r[1].strftime('%Y-%m-%d') if r[1] else ''} for r in repayments
                    ]
    except Exception as e:
        print(f"Error fetching loan requests: {e}")
    return render_template('loan_requests.html', loan_requests=loan_requests, repayment_histories=repayment_histories)

@app.route('/pay_back_loan', methods=['GET', 'POST'])
@login_required
def pay_back_loan():
    loan = {
        'stokvel_name': 'Example Stokvel',
        'amount': 1000.00,
        'status': 'approved'
    }
    if request.method == 'POST':
        flash('Loan repayment submitted! (placeholder)', 'success')
        return redirect(url_for('loan_requests'))
    csrf_token = generate_csrf()
    return render_template('pay_back_loan.html', loan=loan, csrf_token=csrf_token)

@app.route('/request_loan', methods=['GET', 'POST'])
@login_required
def request_loan():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to request a loan.", "error")
        return redirect(url_for('login'))

    # Fetch user's stokvels for the dropdown
    stokvels = []
=======
@app.route('/activities')
@login_required
def activities():
    activities = []
>>>>>>> 09799e6ad57bc08de1445d08a85e35f4e73d014d
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
<<<<<<< HEAD
                    SELECT s.id, s.name 
                    FROM stokvels s
                    JOIN stokvel_members sm ON s.id = sm.stokvel_id
                    WHERE sm.user_id = %s
                """, (user_id,))
                stokvels_data = cur.fetchall()
                for stokvel in stokvels_data:
                    stokvels.append({'id': stokvel[0], 'name': stokvel[1]})
    except Exception as e:
        print(f"Error fetching stokvels: {e}")
        flash("Could not load stokvels.", "error")

    if request.method == 'POST':
        stokvel_id = request.form.get('stokvel_id')
        amount = request.form.get('amount')
        reason = request.form.get('reason')
        if not all([stokvel_id, amount, reason]):
            flash("All fields are required.", "error")
            return render_template('request_loan.html', stokvels=stokvels)
        try:
            amount = float(amount)
            with support.db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO loan_requests (user_id, stokvel_id, amount, reason)
                        VALUES (%s, %s, %s, %s)
                    """, (user_id, stokvel_id, amount, reason))
                    conn.commit()
            flash("Loan request submitted!", "success")
            return redirect(url_for('loan_requests'))
        except Exception as e:
            print(f"Error submitting loan request: {e}")
            flash("Could not submit loan request.", "error")
            return render_template('request_loan.html', stokvels=stokvels)
    else:
        return render_template('request_loan.html', stokvels=stokvels)

@app.route('/financial_insight', methods=['GET', 'POST'])
@login_required
def financial_insight():
    user_id = session.get('user_id')
    # Filters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    stokvel_id = request.args.get('stokvel_id')
    contrib_type = request.args.get('type')
    filters = []
    params = []
    if date_from:
        filters.append('transaction_date >= %s')
        params.append(date_from)
    if date_to:
        filters.append('transaction_date <= %s')
        params.append(date_to)
    if stokvel_id:
        filters.append('stokvel_id = %s')
        params.append(stokvel_id)
    if contrib_type:
        filters.append('type = %s')
        params.append(contrib_type)
    filter_sql = (' AND ' + ' AND '.join(filters)) if filters else ''
    # Personal metrics
    with support.db_connection() as conn:
        with conn.cursor() as cur:
            # Contribution trends (personal)
            cur.execute(f"""
                SELECT DATE_TRUNC('month', transaction_date) AS month, COALESCE(SUM(amount),0)
                FROM transactions WHERE user_id = %s AND type = 'contribution' {filter_sql}
                GROUP BY month ORDER BY month
            """, (user_id, *params))
            personal_trend_raw = cur.fetchall()
            personal_trend = [(m.strftime('%b %Y'), float(v)) for m, v in personal_trend_raw] if personal_trend_raw else []
            # Contribution trends (community)
            cur.execute(f"""
                SELECT DATE_TRUNC('month', transaction_date) AS month, COALESCE(SUM(amount),0)
                FROM transactions WHERE type = 'contribution' {filter_sql}
                GROUP BY month ORDER BY month
            """, tuple(params))
            community_trend_raw = cur.fetchall()
            community_trend = [(m.strftime('%b %Y'), float(v)) for m, v in community_trend_raw] if community_trend_raw else []
            # Savings goal breakdown (personal)
            cur.execute("SELECT name, current_amount, target_amount FROM savings_goals WHERE user_id = %s", (user_id,))
            savings_goals = cur.fetchall()
            # Top contributors (community)
            cur.execute("""
                SELECT u.username, COALESCE(SUM(t.amount),0) as total
                FROM transactions t JOIN users u ON t.user_id = u.firebase_uid
                WHERE t.type = 'contribution'
                GROUP BY u.username ORDER BY total DESC LIMIT 5
            """)
            top_contributors = cur.fetchall()
            # Recent activity (personal)
            cur.execute(f"""
                SELECT type, amount, transaction_date, description
                FROM transactions WHERE user_id = %s {filter_sql}
                ORDER BY transaction_date DESC LIMIT 10
            """, (user_id, *params))
            recent_activity = cur.fetchall()
            # Milestones (personal)
            cur.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id = %s AND type = 'contribution'", (user_id,))
            total_contrib = float(cur.fetchone()[0] or 0)
            milestones = []
            if total_contrib >= 10000: milestones.append('R10,000+ contributed!')
            if total_contrib >= 5000: milestones.append('R5,000+ contributed!')
            if total_contrib >= 1000: milestones.append('R1,000+ contributed!')
            # Suggestions (personal)
            suggestions = []
            if savings_goals:
                for goal in savings_goals:
                    if goal[1] / (goal[2] or 1) > 0.8:
                        suggestions.append(f"You're close to reaching your goal: {goal[0]}")
            # Comparison to community
            cur.execute("SELECT COALESCE(AVG(amount),0) FROM transactions WHERE type = 'contribution'")
            community_avg = float(cur.fetchone()[0] or 0)
            comparison = total_contrib - community_avg
            # Growth rate (community)
            cur.execute("""
                SELECT DATE_TRUNC('month', transaction_date) AS month, COALESCE(SUM(amount),0)
                FROM transactions WHERE type = 'contribution'
                GROUP BY month ORDER BY month
            """)
            growth_data = cur.fetchall()
            # Goal diversity (community)
            cur.execute("SELECT name, COUNT(*) FROM savings_goals GROUP BY name")
            goal_diversity = cur.fetchall()
            # Active members (community)
            cur.execute("""
                SELECT COUNT(DISTINCT user_id) FROM transactions
                WHERE type = 'contribution' AND DATE_TRUNC('month', transaction_date) = DATE_TRUNC('month', CURRENT_DATE)
            """)
            active_members = cur.fetchone()[0]
            # Stacked bar data (personal)
            cur.execute(f"""
                SELECT DATE_TRUNC('month', transaction_date) AS month,
                       SUM(CASE WHEN type = 'contribution' THEN amount ELSE 0 END) as contributions,
                       SUM(CASE WHEN type = 'withdrawal' THEN amount ELSE 0 END) as withdrawals,
                       SUM(CASE WHEN type = 'payout' THEN amount ELSE 0 END) as payouts
                FROM transactions WHERE user_id = %s {filter_sql}
                GROUP BY month ORDER BY month
            """, (user_id, *params))
            personal_bar_raw = cur.fetchall()
            personal_bar_data = [
                {
                    'month': m.strftime('%b %Y'),
                    'contributions': float(c),
                    'withdrawals': float(w),
                    'payouts': float(p)
                } for m, c, w, p in personal_bar_raw
            ] if personal_bar_raw else []
            # Stacked bar data (community)
            cur.execute(f"""
                SELECT DATE_TRUNC('month', transaction_date) AS month,
                       SUM(CASE WHEN type = 'contribution' THEN amount ELSE 0 END) as contributions,
                       SUM(CASE WHEN type = 'withdrawal' THEN amount ELSE 0 END) as withdrawals,
                       SUM(CASE WHEN type = 'payout' THEN amount ELSE 0 END) as payouts
                FROM transactions {('WHERE ' + ' AND '.join(filters)) if filters else ''}
                GROUP BY month ORDER BY month
            """, tuple(params))
            community_bar_raw = cur.fetchall()
            community_bar_data = [
                {
                    'month': m.strftime('%b %Y'),
                    'contributions': float(c),
                    'withdrawals': float(w),
                    'payouts': float(p)
                } for m, c, w, p in community_bar_raw
            ] if community_bar_raw else []
            # --- Personal Financial Health Score ---
            # Savings rate: total saved / total goal
            cur.execute("SELECT COALESCE(SUM(current_amount),0), COALESCE(SUM(target_amount),0) FROM savings_goals WHERE user_id = %s", (user_id,))
            total_saved, total_goal = cur.fetchone()
            savings_rate = (total_saved / total_goal) if total_goal else 0
            # Contribution consistency: number of months with contributions / months since first contribution
            cur.execute("SELECT MIN(transaction_date), MAX(transaction_date) FROM transactions WHERE user_id = %s AND type = 'contribution'", (user_id,))
            min_date, max_date = cur.fetchone()
            if min_date and max_date:
                months_active = (max_date.year - min_date.year) * 12 + (max_date.month - min_date.month) + 1
                cur.execute("SELECT COUNT(DISTINCT DATE_TRUNC('month', transaction_date)) FROM transactions WHERE user_id = %s AND type = 'contribution'", (user_id,))
                months_contributed = cur.fetchone()[0]
                consistency = (months_contributed / months_active) if months_active else 0
            else:
                consistency = 0
            # Goal progress: average progress across all goals
            cur.execute("SELECT AVG(current_amount/NULLIF(target_amount,0)) FROM savings_goals WHERE user_id = %s", (user_id,))
            avg_goal_progress = cur.fetchone()[0] or 0
            # Health score (simple weighted sum, scale 0-100)
            savings_rate = float(savings_rate)
            consistency = float(consistency)
            avg_goal_progress = float(avg_goal_progress)
            health_score = int((savings_rate * 40 + consistency * 30 + avg_goal_progress * 30) * 100)
            # --- Goal Forecasting ---
            # Find next goal not yet reached
            cur.execute("SELECT name, target_amount, current_amount FROM savings_goals WHERE user_id = %s AND current_amount < target_amount ORDER BY target_date ASC LIMIT 1", (user_id,))
            next_goal = cur.fetchone()
            goal_forecast = None
            if next_goal:
                name, target, current = next_goal
                # Calculate average monthly contribution to goals
                cur.execute("""
                    SELECT COALESCE(SUM(amount),0)/GREATEST(COUNT(DISTINCT DATE_TRUNC('month', transaction_date)),1)
                    FROM transactions WHERE user_id = %s AND type = 'contribution'""", (user_id,))
                avg_monthly = cur.fetchone()[0] or 0
                if avg_monthly > 0:
                    months_needed = max(0, int((target - current) / avg_monthly))
                    from datetime import datetime, timedelta
                    forecast_date = datetime.now() + timedelta(days=months_needed*30)
                    goal_forecast = f"You are on track to reach '{name}' by {forecast_date.strftime('%b %Y')} if you keep saving at your current rate."
                else:
                    goal_forecast = f"Set up regular contributions to reach your goal '{name}'."
            # --- Community Badges ---
            # Top contributor badge
            cur.execute("""
                SELECT user_id, SUM(amount) as total FROM transactions WHERE type = 'contribution' GROUP BY user_id ORDER BY total DESC LIMIT 1
            """)
            top_contributor = cur.fetchone()
            community_badges = []
            if top_contributor and top_contributor[0] == user_id:
                community_badges.append('Top Contributor')
            # Fastest saver badge (highest savings rate)
            cur.execute("""
                SELECT user_id, SUM(current_amount)/NULLIF(SUM(target_amount),0) as rate FROM savings_goals GROUP BY user_id ORDER BY rate DESC LIMIT 1
            """)
            fastest_saver = cur.fetchone()
            if fastest_saver and fastest_saver[0] == user_id:
                community_badges.append('Fastest Saver')
            # --- Community Milestones ---
            cur.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type = 'contribution'")
            total_community_saved = float(cur.fetchone()[0] or 0)
            community_milestones = []
            if total_community_saved >= 100000:
                community_milestones.append('Community has saved over R100,000!')
            if total_community_saved >= 50000:
                community_milestones.append('Community has saved over R50,000!')
            if total_community_saved >= 10000:
                community_milestones.append('Community has saved over R10,000!')
            # --- Stokvel Comparisons ---
            # User's stokvels vs. community averages
            cur.execute("""
                SELECT s.id, s.name, s.total_pool FROM stokvels s
                JOIN stokvel_members sm ON s.id = sm.stokvel_id
                WHERE sm.user_id = %s
            """, (user_id,))
            user_stokvels = cur.fetchall()
            cur.execute("SELECT AVG(total_pool) FROM stokvels")
            avg_pool = float(cur.fetchone()[0] or 0)
            stokvel_comparisons = []
            for stokvel in user_stokvels:
                stokvel_comparisons.append({
                    'name': stokvel[1],
                    'total_pool': stokvel[2],
                    'avg_pool': avg_pool,
                    'above_avg': stokvel[2] > avg_pool
                })
            # --- Loan and Repayment Stats (personal) ---
            # Total loans taken
            cur.execute("SELECT COALESCE(SUM(amount),0) FROM loan_requests WHERE user_id = %s", (user_id,))
            total_loans_taken = float(cur.fetchone()[0] or 0)
            # Total repaid
            cur.execute("""
                SELECT COALESCE(SUM(lr.amount),0) FROM loan_repayments lr
                JOIN loan_requests lq ON lr.loan_id = lq.id
                WHERE lq.user_id = %s
            """, (user_id,))
            total_loans_repaid = float(cur.fetchone()[0] or 0)
            # Outstanding balance
            outstanding_loans = total_loans_taken - total_loans_repaid
            # Monthly loan breakdown
            cur.execute("""
                SELECT DATE_TRUNC('month', lq.created_at) AS month, COALESCE(SUM(lq.amount),0) as total_loaned,
                       COALESCE(SUM(lr.amount),0) as total_repaid
                FROM loan_requests lq
                LEFT JOIN loan_repayments lr ON lq.id = lr.loan_id
                WHERE lq.user_id = %s
                GROUP BY month ORDER BY month
            """, (user_id,))
            loan_monthly_raw = cur.fetchall()
            loan_monthly_data = [
                {
                    'month': m.strftime('%b %Y'),
                    'loaned': float(loaned),
                    'repaid': float(repaid)
                } for m, loaned, repaid in loan_monthly_raw
            ] if loan_monthly_raw else []
    return render_template('financial_insight.html',
        total_contributions=total_contrib,
        monthly_average=0,  # Placeholder, can compute as before
        savings_progress=0, # Placeholder, can compute as before
        community_total_contributions=0, # Placeholder, can compute as before
        community_monthly_average=0, # Placeholder, can compute as before
        community_savings_progress=0, # Placeholder, can compute as before
        personal_trend=personal_trend,
        community_trend=community_trend,
        savings_goals=savings_goals,
        top_contributors=top_contributors,
        recent_activity=recent_activity,
        milestones=milestones,
        suggestions=suggestions,
        comparison=comparison,
        growth_data=growth_data,
        goal_diversity=goal_diversity,
        active_members=active_members,
        date_from=date_from,
        date_to=date_to,
        stokvel_id=stokvel_id,
        contrib_type=contrib_type,
        personal_bar_data=personal_bar_data,
        community_bar_data=community_bar_data,
        health_score=health_score,
        goal_forecast=goal_forecast,
        community_badges=community_badges,
        community_milestones=community_milestones,
        stokvel_comparisons=stokvel_comparisons,
        total_loans_taken=total_loans_taken,
        total_loans_repaid=total_loans_repaid,
        outstanding_loans=outstanding_loans,
        loan_monthly_data=loan_monthly_data
    )

@app.route('/financial_insight/data', methods=['GET'])
@login_required
def financial_insight_data():
    user_id = session.get('user_id')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    stokvel_id = request.args.get('stokvel_id')
    contrib_type = request.args.get('type')
    filters = []
    params = []
    if date_from:
        filters.append('transaction_date >= %s')
        params.append(date_from)
    if date_to:
        filters.append('transaction_date <= %s')
        params.append(date_to)
    if stokvel_id:
        filters.append('stokvel_id = %s')
        params.append(stokvel_id)
    if contrib_type:
        filters.append('type = %s')
        params.append(contrib_type)
    filter_sql = (' AND ' + ' AND '.join(filters)) if filters else ''
    with support.db_connection() as conn:
        with conn.cursor() as cur:
            # (Repeat all queries from /financial_insight, but collect results in a dict)
            # ... (copy all queries and collect results) ...
            # For brevity, only show a few key results here; in real code, include all
            cur.execute(f"""
                SELECT DATE_TRUNC('month', transaction_date) AS month, COALESCE(SUM(amount),0)
                FROM transactions WHERE user_id = %s AND type = 'contribution' {filter_sql}
                GROUP BY month ORDER BY month
            """, (user_id, *params))
            personal_trend = [(m.strftime('%b %Y'), float(v)) for m, v in cur.fetchall()]
            cur.execute(f"""
                SELECT DATE_TRUNC('month', transaction_date) AS month,
                       SUM(CASE WHEN type = 'contribution' THEN amount ELSE 0 END) as contributions,
                       SUM(CASE WHEN type = 'withdrawal' THEN amount ELSE 0 END) as withdrawals,
                       SUM(CASE WHEN type = 'payout' THEN amount ELSE 0 END) as payouts
                FROM transactions WHERE user_id = %s {filter_sql}
                GROUP BY month ORDER BY month
            """, (user_id, *params))
            personal_bar_data = [
                {
                    'month': m.strftime('%b %Y'),
                    'contributions': float(c),
                    'withdrawals': float(w),
                    'payouts': float(p)
                } for m, c, w, p in cur.fetchall()
            ]
            # ... repeat for all other metrics ...
            # --- Loan and Repayment Stats (personal) ---
            cur.execute("SELECT COALESCE(SUM(amount),0) FROM loan_requests WHERE user_id = %s", (user_id,))
            total_loans_taken = float(cur.fetchone()[0] or 0)
            cur.execute("""
                SELECT COALESCE(SUM(lr.amount),0) FROM loan_repayments lr
                JOIN loan_requests lq ON lr.loan_id = lq.id
                WHERE lq.user_id = %s
            """, (user_id,))
            total_loans_repaid = float(cur.fetchone()[0] or 0)
            outstanding_loans = total_loans_taken - total_loans_repaid
            cur.execute("""
                SELECT DATE_TRUNC('month', lq.created_at) AS month, COALESCE(SUM(lq.amount),0) as total_loaned,
                       COALESCE(SUM(lr.amount),0) as total_repaid
                FROM loan_requests lq
                LEFT JOIN loan_repayments lr ON lq.id = lr.loan_id
                WHERE lq.user_id = %s
                GROUP BY month ORDER BY month
            """, (user_id,))
            loan_monthly_raw = cur.fetchall()
            loan_monthly_data = [
                {
                    'month': m.strftime('%b %Y'),
                    'loaned': float(loaned),
                    'repaid': float(repaid)
                } for m, loaned, repaid in loan_monthly_raw
            ] if loan_monthly_raw else []
    return jsonify({
        'personal_trend': personal_trend,
        'personal_bar_data': personal_bar_data,
        # ... add all other metrics as in the main route ...
    })

@app.route('/add_calendar_event', methods=['POST'])
@login_required
def add_calendar_event():
    user_id = session.get('user_id')
    event_date = request.form.get('date')
    description = request.form.get('desc')
    if not (event_date and description):
        return jsonify({'success': False, 'error': 'Missing date or description'}), 400
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Create table if not exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_events (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(128) REFERENCES users(firebase_uid) ON DELETE CASCADE,
                        event_date DATE NOT NULL,
                        description TEXT NOT NULL
                    )
                """)
                cur.execute("""
                    INSERT INTO user_events (user_id, event_date, description)
                    VALUES (%s, %s, %s)
                """, (user_id, event_date, description))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error adding custom event: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/calendar_data')
@login_required
def calendar_data():
    import calendar
    from datetime import datetime, date, timedelta
    user_id = session.get('user_id')
    try:
        month = int(request.args.get('month', datetime.now().month))
        year = int(request.args.get('year', datetime.now().year))
    except Exception:
        month = datetime.now().month
        year = datetime.now().year
    # Build calendar days
    first_day = date(year, month, 1)
    _, last_day_num = calendar.monthrange(year, month)
    days = []
    today = date.today()
    for i in range(1, last_day_num + 1):
        d = date(year, month, i)
        days.append({
            'date': i,
            'full_date': d.strftime('%Y-%m-%d'),
            'is_today': d == today,
            'is_weekend': d.weekday() >= 5
        })
    # Fetch events (reuse dashboard logic)
    events = []
    with support.db_connection() as conn:
        with conn.cursor() as cur:
            # Contributions
            cur.execute("SELECT transaction_date, amount FROM transactions WHERE user_id=%s AND EXTRACT(MONTH FROM transaction_date)=%s AND EXTRACT(YEAR FROM transaction_date)=%s", (user_id, month, year))
            for row in cur.fetchall():
                events.append({'date': row[0].strftime('%Y-%m-%d'), 'type': 'contribution', 'desc': f'Contribution: R{row[1]}'})
            # Payouts
            cur.execute("SELECT transaction_date, amount FROM payouts WHERE user_id=%s AND EXTRACT(MONTH FROM transaction_date)=%s AND EXTRACT(YEAR FROM transaction_date)=%s", (user_id, month, year))
            for row in cur.fetchall():
                events.append({'date': row[0].strftime('%Y-%m-%d'), 'type': 'payout', 'desc': f'Payout: R{row[1]}'})
            # Savings goals
            cur.execute("SELECT target_date, name, target_amount FROM savings_goals WHERE user_id=%s AND EXTRACT(MONTH FROM target_date)=%s AND EXTRACT(YEAR FROM target_date)=%s", (user_id, month, year))
            for row in cur.fetchall():
                events.append({'date': row[0].strftime('%Y-%m-%d'), 'type': 'goal', 'desc': f'Goal: {row[1]} (R{row[2]})'})
            # Repayments
            cur.execute("SELECT date, amount FROM loan_repayments WHERE user_id=%s AND EXTRACT(MONTH FROM date)=%s AND EXTRACT(YEAR FROM date)=%s", (user_id, month, year))
            for row in cur.fetchall():
                events.append({'date': row[0].strftime('%Y-%m-%d'), 'type': 'repayment', 'desc': f'Repayment: R{row[1]}'})
            # Custom events
            try:
                cur.execute("SELECT event_date, description FROM user_events WHERE user_id=%s AND EXTRACT(MONTH FROM event_date)=%s AND EXTRACT(YEAR FROM event_date)=%s", (user_id, month, year))
                for row in cur.fetchall():
                    events.append({'date': row[0].strftime('%Y-%m-%d'), 'type': 'custom', 'desc': row[1]})
            except Exception:
                pass  # Table may not exist yet
    month_label = first_day.strftime('%B %Y')
    return jsonify({
        'days': days,
        'events': events,
        'month_label': month_label,
        'month_num': month,
        'year': year
    })

@app.route('/transactions')
@login_required
def transactions():
    user_id = session.get('user_id')
    transactions = []
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT transaction_date, type, amount, status, description, stokvel_id
                    FROM transactions
                    WHERE user_id = %s
                    ORDER BY transaction_date DESC
                """, (user_id,))
                for row in cur.fetchall():
                    transactions.append({
                        'date': row[0].strftime('%Y-%m-%d') if row[0] else '',
                        'type': row[1],
                        'amount': float(row[2]),
                        'status': row[3],
                        'description': row[4],
                        'stokvel_id': row[5]
                    })
    except Exception as e:
        print(f"Error fetching transactions: {e}")
    return render_template('transactions.html', transactions=transactions)

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf())

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
=======
                    SELECT t.type, t.amount, t.status, t.transaction_date, t.description, s.name as stokvel_name
                    FROM transactions t
                    JOIN stokvels s ON t.stokvel_id = s.id
                    WHERE t.user_id = %s
                    ORDER BY t.transaction_date DESC
                """, (session['user_id'],))
                rows = cur.fetchall()
                for row in rows:
                    t_type, amount, status, t_date, description, stokvel_name = row
                    # Format date for display
                    if t_date:
                        try:
                            from datetime import datetime, timedelta
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
                    activities.append({
                        'type': t_type,
                        'title': title,
                        'amount': float(amount) if amount is not None else 0.0,
                        'date': date_str,
                        'status': status.capitalize() if status else '',
                    })
    except Exception as e:
        print(f"Error fetching activities: {e}")
    return render_template('activities.html', activities=activities)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
>>>>>>> 09799e6ad57bc08de1445d08a85e35f4e73d014d
