from flask import Flask, render_template, request, redirect, session, flash, jsonify, url_for, Response, send_file
import os
from datetime import timedelta, datetime, date
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
from extensions import csrf
import firebase_admin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email
from firebase_admin import credentials, auth
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from flask_session import Session
from sendgrid import SendGridAPIClient
from dateutil import parser as date_parser
from translations import get_text
from admin import admin_bp  # Import the blueprint
from utils import login_required
from rewards import rewards_bp
from financial_advisor import advisor_bp

# Email handling imports
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename
import re
from decimal import Decimal, InvalidOperation
from flask_babel import Babel
from flask_socketio import SocketIO, join_room, emit
from calendar import monthrange
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from flask_mail import Mail, Message
from flask_wtf.csrf import generate_csrf
import calendar
from flask import g
from flask_babel import _

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

babel = Babel(app)

UPLOAD_FOLDER = 'static/profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

KYC_UPLOAD_FOLDER = 'static/kyc_docs'
ALLOWED_KYC_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
app.config['KYC_UPLOAD_FOLDER'] = KYC_UPLOAD_FOLDER

csrf.init_app(app)  # Initialize CSRF protection

def allowed_file(filename):
    return '.' in filename and filename.rsplit(
        '.', 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_kyc_file(filename):
    return '.' in filename and filename.rsplit(
    '.', 1)[1].lower() in ALLOWED_KYC_EXTENSIONS



# Mail config and initialization (now using environment variables)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = ('KasiKash App', os.getenv('MAIL_USERNAME'))
mail = Mail(app)

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate(
    os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_KEY_PATH",
         "firebase-service-account.json"))
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
print(
    f"DEBUG: FIREBASE_SERVICE_ACCOUNT_KEY_PATH from .env: {os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH')}")
print(
    f"DEBUG: OPENROUTER_API_KEY loaded from .env: {'Yes' if os.getenv('OPENROUTER_API_KEY') else 'No'}")

# Debugging SendGrid environment variables
print(
    f"DEBUG: SENDGRID_API_KEY loaded from .env: {os.getenv('SENDGRID_API_KEY')}")
print(
    f"DEBUG: MAIL_SENDER_EMAIL loaded from .env: {os.getenv('MAIL_SENDER_EMAIL')}")

# Debugging B2 environment variables
print(
    f"DEBUG: B2_ACCESS_KEY_ID loaded from .env: {'Yes' if os.getenv('B2_ACCESS_KEY_ID') else 'No'}")
print(
    f"DEBUG: B2_SECRET_ACCESS_KEY loaded from .env: {'Yes' if os.getenv('B2_SECRET_ACCESS_KEY') else 'No'}")
print(f"DEBUG: B2_BUCKET_NAME loaded from .env: {os.getenv('B2_BUCKET_NAME')}")
print(
    f"DEBUG: B2_ENDPOINT_URL loaded from .env: {os.getenv('B2_ENDPOINT_URL')}")

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

app.secret_key = os.getenv('SECRET_KEY')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_FILE_DIR'] = os.path.join(
    os.getcwd(), 'flask_session_data')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
Session(app)  # Initialize Flask-Session

# Register the admin blueprint
app.register_blueprint(admin_bp, url_prefix='/admin')

# Register the admin API blueprint
from admin.api import api_bp
app.register_blueprint(api_bp, url_prefix='/admin')

# Initialize OpenRouter client at application level
try:
    # Use requests method for OpenRouter since openai client has compatibility
    # issues
    import requests
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_api_key and openrouter_api_key != 'your-openrouter-api-key-here':
        print("OpenRouter client initialized successfully with Google Gemma 3n 4B model.")
        openrouter_available = True
    else:
        print("Warning: OpenRouter API key not found. Chat features will be disabled.")
        openrouter_available = False
except Exception as e:
    print(
    f"Warning: OpenRouter client not initialized. Chat features will be disabled. Error: {e}")
    openrouter_available = False

# Dictionary for chatbot's rule-based feature explanations
feature_faq = {
    # --- User Features ---
    'dashboard': "The User Dashboard is your main hub. It shows a summary of your balance, recent activities, and provides quick access to all major features.",
    'stokvel': "To create a new stokvel:\n1. Click 'Stokvels' in the menu\n2. Click 'Create New Stokvel'\n3. Fill in the stokvel details\n4. Click 'Create'\n\nTo add members:\n1. Open your stokvel\n2. Click 'Manage Members'\n3. Click 'Add Member'\n4. Enter their email\n5. Set their role\n6. Click 'Add'",
    'create stokvel': "To create a new stokvel:\n1. Click 'Stokvels' in the menu\n2. Click 'Create New Stokvel'\n3. Fill in the stokvel details\n4. Click 'Create'",
    'add member': "To add members to your stokvel:\n1. Open your stokvel\n2. Click 'Manage Members'\n3. Click 'Add Member'\n4. Enter their email\n5. Set their role\n6. Click 'Add'",
    'contribution': "To make a contribution:\n1. Go to the 'Contributions' page\n2. Select your stokvel\n3. Enter the amount\n4. Choose your payment method\n5. Click 'Make Contribution'",
    'payout': "To request a payout:\n1. Go to your stokvel's page\n2. Click 'Request Payout'\n3. Enter the amount\n4. Provide a reason (optional)\n5. Submit your request",
    'savings goal': "To set a savings goal:\n1. Go to 'Savings Goals'\n2. Click 'Create New Goal'\n3. Enter your target amount and deadline\n4. Choose a category\n5. Click 'Create Goal'",
    'stokvel': "Stokvels are community savings groups. You can create your own, invite members, make contributions, request payouts, and view statements.",
    'contribution': "Contributions are payments you make to your stokvels. You can track your payment history and make new contributions from the Contributions page.",
    'payout': "Payouts are when you receive money from a stokvel. You can request a payout, which may need approval from the stokvel admin.",
    'savings goal': "Savings Goals let you set personal financial targets. You can create goals, contribute to them, and track your progress.",
    'payment method': "Manage your payment methods, such as bank accounts or cards, on the Payment Methods page. You can also set a default method for contributions.",
    'notification': "Notifications keep you updated on important activities, like contributions or payout requests. You can view them by clicking the bell icon.",
    'profile': "Your Profile page shows your personal information, total contributions, and active stokvels. You can update your details, upload a profile picture, and submit KYC documents here.",
    'setting': "The Settings page allows you to manage account preferences, like language, notification settings, and security options like two-factor authentication.",
    'financial analysis': "The Financial Analysis page provides charts and graphs to visualize your spending habits and understand your financial health over time.",
    'loan': "Loans can be requested from a stokvel, depending on its rules. Loan requests are typically reviewed by the stokvel's admin.",
    'kyc': "KYC (Know Your Customer) is a verification process. Upload your ID and proof of address on your Profile page to get verified.",
    'membership': "KasiKash may offer different membership plans. You can view available plans and their benefits on the Pricing page.",
    'statement': "You can download a detailed PDF statement for any of your stokvels from the stokvel's member page.",

    # --- Admin Features ---
    'admin': "The Admin Panel provides access to manage users, approve loans and KYC documents, create events, and send notifications. If you're an admin, you can access it via the admin section.",
    'admin dashboard': "The Admin Dashboard provides a high-level overview of the platform, including total users, total stokvels, and the number of pending loan approvals.",
    'manage users': "The Manage Users section in the admin panel allows you to view, search, and manage all users on the platform. You can also add new users manually.",
    'loan approval': "The Loan Approvals page is where admins can review, approve, or reject payout requests made by users. You can also view the history of approved or rejected loans.",
    'kyc approval': "The KYC Approvals page lets admins review user-submitted documents (ID and proof of address), and then approve or reject their KYC status.",
    'admin events': "The Events page allows admins to create and manage events for specific stokvels, and send notifications about these events to all members.",
    'admin memberships': "The Memberships section is for managing the different pricing plans or membership tiers offered on the platform.",
    'admin notifications': "Admins can send custom broadcast notifications to all users or specific user groups from the Admin Notifications page.",
    'admin settings': "The Admin Settings page is for configuring platform-wide settings."
}


def verification_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.')
            return redirect('/login')
        try:
            firebase_user = auth.get_user(session['user_id'])
            if not firebase_user.email_verified:
                flash(
                    'Please verify your email to access this feature. Check your inbox for a verification link.')
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
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
    "SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE",
    (user_id,
    ))
                result = cur.fetchone()
                return result[0] if result else 0
    except Exception as e:
        print(f"Error getting notification count: {e}")
        return 0


def create_notification(
    user_id,
    message,
    link_url=None,
     notification_type='general'):
    """Creates and saves an in-app notification for a user."""
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Get user's internal ID
                cur.execute(
    "SELECT id FROM users WHERE firebase_uid = %s", (user_id,))
                user_result = cur.fetchone()
                if not user_result:
                    print(f"User not found for firebase_uid: {user_id}")
                    return False
                
                internal_user_id = user_result[0]
                cur.execute("""
                    INSERT INTO notifications (user_id, type, message, link_url, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (user_id, notification_type, message, link_url))
                conn.commit()
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
    firebase_uid = session.get('user_id')
    user = {
        'username': session.get('username', 'User'),
        'profile_picture': session.get('profile_picture'),
        'email': session.get('email'),
    }
    active_stokvels_count = 0
    total_contributions = 0
    recent_activities = []

    # Calendar data generation (existing code)
    now = datetime.now()
    year = request.args.get('year', now.year, type=int)
    month = request.args.get('month', now.month, type=int)
    month_name = datetime(year, month, 1).strftime('%B')
    cal = calendar.monthcalendar(year, month)
    calendar_days = []
    today = date.today()
    flat_cal = [day for week in cal for day in week]
    for day_num in flat_cal:
        if day_num == 0:
            calendar_days.append({'is_day': False})
        else:
            current_date = date(year, month, day_num)
            calendar_days.append({
                'is_day': True,
                'date': day_num,
                'full_date': current_date.strftime('%Y-%m-%d'),
                'is_today': current_date == today,
                'is_weekend': current_date.weekday() >= 5
            })
    calendar_events = []

    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Count active stokvels for this user
                cur.execute("""
                    SELECT COUNT(DISTINCT s.id)
                    FROM stokvels s
                    JOIN stokvel_members sm ON s.id = sm.stokvel_id
                    WHERE sm.user_id = %s
                """, (firebase_uid,))
                active_stokvels_count = cur.fetchone()[0] or 0

                # Sum total contributions for this user
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0)
                    FROM transactions
                    WHERE user_id = %s AND type = 'contribution' AND status = 'completed'
                """, (firebase_uid,))
                total_contributions = cur.fetchone()[0] or 0

                # Fetch calendar events from diary
                cur.execute("""
                    SELECT event_date, event_name, description 
                    FROM diary 
                    WHERE user_id = %s AND EXTRACT(YEAR FROM event_date) = %s AND EXTRACT(MONTH FROM event_date) = %s
                """, (firebase_uid, year, month))
                for row in cur.fetchall():
                    calendar_events.append({
                        'date': row[0].strftime('%Y-%m-%d'),
                        'type': row[1].lower() if row[1] else 'custom',
                        'desc': row[2]
                    })

                # Fetch recent activities: last 7 transactions and completed goals
                cur.execute("""
                    SELECT type, amount, transaction_date
                    FROM transactions
                    WHERE user_id = %s AND status = 'completed'
                    ORDER BY transaction_date DESC
                    LIMIT 7
                """, (firebase_uid,))
                for t in cur.fetchall():
                    t_type, t_amount, t_date = t
                    title = {
                        'contribution': 'Monthly Contribution',
                        'withdrawal': 'Withdrawal',
                        'savings_contribution': 'Savings Goal Contribution',
                        'payout': 'Payout',
                    }.get(t_type, t_type.replace('_', ' ').title())
                    status = 'Processed' if t_type == 'contribution' else ('Completed' if t_type in ['withdrawal', 'savings_contribution', 'payout'] else 'Completed')
                    recent_activities.append({
                        'type': t_type,
                        'title': title,
                        'amount': float(t_amount),
                        'date': t_date,
                        'status': status
                    })
                # Add completed savings goals
                cur.execute("""
                    SELECT name, target_amount, created_at
                    FROM savings_goals
                    WHERE user_id = %s AND status = 'completed'
                    ORDER BY created_at DESC
                    LIMIT 2
                """, (firebase_uid,))
                for g in cur.fetchall():
                    g_name, g_amount, g_date = g
                    recent_activities.append({
                        'type': 'goal',
                        'title': g_name,
                        'amount': float(g_amount),
                        'date': g_date,
                        'status': 'Achieved'
                    })
                # Sort all activities by date descending
                recent_activities.sort(key=lambda x: x['date'], reverse=True)
    except Exception as e:
        print(f"Dashboard error: {e}")
        active_stokvels_count = 0
        total_contributions = 0

    print("Recent activities:", recent_activities)
    return render_template(
        'dashboard.html', 
        user=user, 
        active_stokvels_count=active_stokvels_count, 
        total_contributions=total_contributions,
        calendar_month=month_name,
        calendar_year=year,
        calendar_days=calendar_days,
        calendar_events=calendar_events,
        recent_activities=recent_activities
    )


@app.route('/analysis')
def analysis():
    if 'user_id' in session:
        userdata = support.get_userdata(session['user_id'])
        if userdata:
            df = support.get_transactions_df(session['user_id'])
            pie = support.meraPie(df, 'Expense', 'Amount(₹)', height=180)
            bar = support.meraBar(df, 'Expense', 'Amount(₹)', height=180)
            line = support.meraLine(df, 'Date', 'Amount(₹)', height=180)
            scatter = support.meraScatter(df, 'Date', 'Amount(₹)', 'Expense', 'Amount(₹)', slider=False)
            heat = support.meraHeatmap(
                df,
                'Day_name',
                'Month_name',
                height=200,
                title="Transaction count Day vs Month"
            )
            month_bar = support.month_bar(df, 280)
            sun = support.meraSunburst(df, 280)
            return render_template(
                'analysis.html',
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
            return render_template(
                'analysis.html',
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

@app.route('/financial_insight')
@login_required
def financial_insight():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to view financial insights.', 'danger')
        return redirect(url_for('login'))
    
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Get total contributions
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) as total_contributions
                    FROM transactions 
                    WHERE user_id = %s AND type = 'contribution' AND status = 'completed'
                """, (user_id,))
                total_contributions = cur.fetchone()[0]
                
                # Get monthly average
                cur.execute("""
                    SELECT COALESCE(AVG(monthly_total), 0) as monthly_average
                    FROM (
                        SELECT DATE_TRUNC('month', transaction_date) as month,
                               SUM(amount) as monthly_total
                        FROM transactions 
                        WHERE user_id = %s AND type = 'contribution' AND status = 'completed'
                        GROUP BY DATE_TRUNC('month', transaction_date)
                    ) monthly_totals
                """, (user_id,))
                monthly_average = cur.fetchone()[0]
                
                # Get savings goal progress
                cur.execute("""
                    SELECT COALESCE(SUM(current_amount) / NULLIF(SUM(target_amount), 0), 0) as progress
                    FROM savings_goals 
                    WHERE user_id = %s AND status = 'active'
                """, (user_id,))
                savings_progress = cur.fetchone()[0]
                
                # Get contribution data for chart (last 6 months)
                cur.execute("""
                    SELECT DATE_TRUNC('month', transaction_date) as month,
                           SUM(amount) as monthly_total
                    FROM transactions 
                    WHERE user_id = %s AND type = 'contribution' AND status = 'completed'
                    AND transaction_date >= NOW() - INTERVAL '6 months'
                    GROUP BY DATE_TRUNC('month', transaction_date)
                    ORDER BY month
                """, (user_id,))
                contribution_data = cur.fetchall()
                
                # Prepare chart data
                contribution_dates = []
                monthly_contributions = []
                for row in contribution_data:
                    contribution_dates.append(row[0].strftime('%b %Y'))
                    monthly_contributions.append(float(row[1]))
                
    except Exception as e:
        print(f"Error fetching financial insight data: {e}")
        total_contributions = 0
        monthly_average = 0
        savings_progress = 0
        contribution_dates = []
        monthly_contributions = []
        flash('Failed to load financial data.', 'danger')
    
    return render_template('financial_insight.html', 
                         total_contributions=total_contributions,
                         monthly_average=monthly_average,
                         savings_progress=savings_progress,
                         contribution_dates=contribution_dates,
                         monthly_contributions=monthly_contributions)

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
                session['email'] = user_record.email
                session['profile_picture'] = getattr(user_record, 'photo_url', None)
                session['is_verified'] = bool(user_record.email_verified)  # Ensure it's a boolean
                session.permanent = bool(remember)  # Ensure it's a boolean
                # Fetch and set user role and profile_picture in session
                try:
                    with support.db_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute(
    "SELECT role, profile_picture FROM users WHERE firebase_uid = %s", (user_record.uid,))
                            role_data = cur.fetchone()
                            if role_data:
                                session['role'] = role_data[0] if role_data[0] else 'user'
                                # Prefer DB profile_picture if present
                                if role_data[1]:
                                    session['profile_picture'] = role_data[1]
                            else:
                                # Default role if not set
                                session['role'] = 'user'
                except Exception as role_e:
                    print(f"Error fetching user role/profile_picture: {role_e}")
                    session['role'] = 'user'

                # Update local database with firebase_uid if not already
                # present or different
                try:
                    with support.db_connection() as conn:
                        with conn.cursor() as cur:
                            # Get current internal ID and firebase_uid from
                            # local db
                            cur.execute(
    "SELECT id, firebase_uid FROM users WHERE email = %s", (email,))
                            user_data = cur.fetchone()
                            
                            if user_data:
                                internal_user_id = user_data[0]
                                old_firebase_uid = user_data[1]
                                new_firebase_uid = user_record.uid

                                if not old_firebase_uid or old_firebase_uid != new_firebase_uid:
                                    print(
    f"Firebase UID mismatch or not set. Updating references for user {email}. Old: {old_firebase_uid}, New: {new_firebase_uid}")

                                    # Update all tables referencing
                                    # firebase_uid *before* updating users
                                    # table
                                    update_queries = [

                                        ("UPDATE stokvels SET created_by = %s WHERE created_by = %s",
                                         (new_firebase_uid, old_firebase_uid)),
                                        # Assuming stokvel_members uses
                                        # firebase_uid, not user_id for FK to
                                        # users.firebase_uid based on \d users
                                        # output
                                        ("UPDATE stokvel_members SET firebase_uid = %s WHERE firebase_uid = %s", (
                                            new_firebase_uid, old_firebase_uid)),
                                        # This still uses internal_user_id, not
                                        # firebase_uid
                                        ("UPDATE transactions SET user_id = %s WHERE user_id = %s",
                                         (internal_user_id, internal_user_id)),
                                        ("UPDATE chat_history SET user_id = %s WHERE user_id = %s",
                                         (new_firebase_uid, old_firebase_uid)),
                                        ("UPDATE chatbot_preferences SET user_id = %s WHERE user_id = %s", (
                                            new_firebase_uid, old_firebase_uid)),
                                        ("UPDATE payment_methods SET user_id = %s WHERE user_id = %s",
                                         (new_firebase_uid, old_firebase_uid)),
                                        ("UPDATE payouts SET user_id = %s WHERE user_id = %s",
                                         (new_firebase_uid, old_firebase_uid)),
                                        ("UPDATE savings_goals SET user_id = %s WHERE user_id = %s",
                                         (new_firebase_uid, old_firebase_uid)),
                                        ("UPDATE stokvels SET created_by = %s WHERE created_by = %s", (new_firebase_uid, old_firebase_uid)),
                                        ("UPDATE stokvel_members SET user_id = %s WHERE user_id = %s", (new_firebase_uid, old_firebase_uid)),
                                        ("UPDATE transactions SET user_id = %s WHERE user_id = %s", (internal_user_id, internal_user_id)),
                                        ("UPDATE chat_history SET user_id = %s WHERE user_id = %s", (new_firebase_uid, old_firebase_uid)),
                                        ("UPDATE chatbot_preferences SET user_id = %s WHERE user_id = %s", (new_firebase_uid, old_firebase_uid)),
                                        ("UPDATE payment_methods SET user_id = %s WHERE user_id = %s", (new_firebase_uid, old_firebase_uid)),
                                        ("UPDATE payouts SET user_id = %s WHERE user_id = %s", (new_firebase_uid, old_firebase_uid)),
                                        ("UPDATE savings_goals SET user_id = %s WHERE user_id = %s", (new_firebase_uid, old_firebase_uid)),
                                    ]
                                    
                                    for query, params in update_queries:
                                        try:
                                            # Special handling for transactions
                                            # if it uses internal_user_id
                                            # rather than firebase_uid as FK
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
                                                # If it's an old
                                                # internal_user_id, it will be
                                                # updated.
                                                print(
    f"Attempting to update transactions user_id from previous internal_user_id to current: {internal_user_id}")
                                                cur.execute(
    "UPDATE transactions SET user_id = %s WHERE user_id = (SELECT id FROM users WHERE firebase_uid = %s)",
    (internal_user_id,
     new_firebase_uid))
                                            else:
                                                print(
    f"Executing update query for related table: {query} with params {params}")
                                                cur.execute(query, params)
                                        except Exception as update_e:
                                            print(f"Error updating related table {query}: {str(update_e)}")
                                            # Log but don't stop the process,
                                            # as some tables might not exist or
                                            # have the column

                                    # Now update the users table with the new
                                    # firebase_uid
                                    print(
    f"Updating users.firebase_uid for {email} to {new_firebase_uid}")
                                    cur.execute(
    "UPDATE users SET firebase_uid = %s WHERE email = %s", (new_firebase_uid, email))
                                    conn.commit()
                                    print(
    f"Successfully updated firebase_uid for {email} and related tables.")
                                else:
                                    print(
    f"firebase_uid for {email} already set and matches: {new_firebase_uid}")
                            else:
                                print(
    f"User with email {email} not found in local database during login_validation for firebase_uid update.")
                except Exception as db_e:
                    print(f"Database update error during login: {str(db_e)}")
                    # This error is not critical enough to prevent login, but
                    # should be logged.

                # Update stokvel_members for pending invites
                try:
                    with support.db_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                "UPDATE stokvel_members SET user_id = %s WHERE email = %s AND user_id IS NULL",
                                (user_record.uid, email)
                            )
                            conn.commit()
                except Exception as e:
                    print(f"Error updating stokvel_members for pending invites: {e}")

                if not user_record.email_verified:
                    print("User email not verified")  # Debug log
                    flash("Please verify your email address before logging in.")
                    return redirect('/login')

                # Update last_login in the database
                from datetime import datetime
                support.execute_query(
    "update",
    "UPDATE users SET last_login = %s, email = %s WHERE firebase_uid = %s",
    (datetime.utcnow(),
    user_record.email,
     user_record.uid))

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
                    flash(
    "Password reset link has been sent to your email.",
     "success")
                else:
                    print(f"Failed to send password reset email to {email}")
                    flash(
    "Failed to send password reset email. Please try again later.",
     "error")
            except auth.UserNotFoundError as e:
                print(f"Firebase UserNotFoundError: {str(e)}")
                print(
    f"Password reset requested for non-existent email: {email}")
                # Check if user exists in local database
                try:
                    with support.db_connection() as conn:
                        with conn.cursor() as cur:
                            # First check if user exists
                            cur.execute(
    "SELECT id, firebase_uid FROM users WHERE email = %s", (email,))
                            user_data = cur.fetchone()
                            if user_data:
                                print(
    f"User found in local database but not in Firebase: {email}")
                                # Generate a random password for Firebase
                                import secrets
                                import string
                                alphabet = string.ascii_letters + string.digits
                                temp_password = ''.join(
    secrets.choice(alphabet) for i in range(12))
                                # Create Firebase account for existing user
                                firebase_user = create_firebase_user(
                                    email, temp_password)
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
                                        SET user_id = %s 
                                        WHERE user_id = %s
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
                                    print(
    f"Successfully updated all references from {old_firebase_uid} to {new_firebase_uid}")
                                    # Generate and send reset link
                                    reset_link = auth.generate_password_reset_link(
                                        email)
                                    if send_password_reset_email(
                                        email, reset_link):
                                        flash(
    "Your account has been migrated. A password reset link has been sent to your email.",
     "success")
                                    else:
                                        flash(
    "Your account has been migrated, but we couldn't send the reset email. Please try again.",
     "error")
                                else:
                                    flash(
    "There was an issue migrating your account. Please contact support.", "error")
                            else:
                                print(
    f"User not found in either Firebase or local database: {email}")
                                flash(
    "If an account exists with this email, a password reset link will be sent.",
     "success")
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
                        cur.execute(
                            "SELECT id FROM users WHERE email = %s", (email,))
                        if cur.fetchone():
                            flash(
                                "An account with this email already exists. Please log in.")
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
                    email_verified=False  # Set to False so user must verify
                )
                print(f"Created Firebase user: {user.uid}")

                # Store Firebase UID and username/email in your PostgreSQL
                # database
                # Generate email verification link and send email
                verification_link = auth.generate_email_verification_link(email)
                send_email_verification(email, verification_link)

                # Store Firebase UID and username/email in your PostgreSQL database
                with support.db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO users (firebase_uid, username, email) VALUES (%s, %s, %s) RETURNING id",
                            (user.uid, username, email)
                        )
                        local_user_id = cur.fetchone()[0]
                        # Update stokvel_members for pending invites
                        cur.execute(
                            "UPDATE stokvel_members SET user_id = %s WHERE email = %s AND user_id IS NULL",
                            (user.uid, email)
                        )
                        conn.commit()

                        if local_user_id:
                            session['user_id'] = user.uid
                            session['username'] = username
                            session['is_verified'] = True
                            session.permanent = True
                            flash("Registration successful! You can now log in.")
                            return redirect('/login')
                        else:
                            flash(
                                "Registration failed: Could not retrieve local user ID.")
                            auth.delete_user(user.uid)
                            return redirect('/register')

            except Exception as e:
                print(f"Registration error: {str(e)}")
                if "email-already-exists" in str(e):
                    flash(
                        "Email address is already in use. Please use a different email or log in.")
                else:
                    flash(
                        f"An unexpected error occurred during registration: {str(e)}")
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
                # Fetch stokvels where the current user is a member, including
                # their role
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
                user_stokvels = [
                    dict(zip([desc[0] for desc in cur.description], row)) for row in cur.fetchall()]

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
                created_stokvels = [
                    dict(zip([desc[0] for desc in cur.description], row)) for row in cur.fetchall()]

        return render_template(
    'stokvels.html',
    stokvels=user_stokvels,
     created_stokvels=created_stokvels)
    except Exception as e:
        flash(f"An error occurred while loading your stokvels: {e}")
        print(f"Stokvels page error: {e}")
        return render_template(
    'stokvels.html',
    stokvels=[],
     created_stokvels=[])


@app.route('/create_stokvel', methods=['POST'])
@login_required
def create_stokvel():
    user_id = session['user_id']
    name = request.form['name']
    description = request.form['description']
    monthly_contribution = request.form['monthly_contribution']
    
    # Insert new stokvel and get its ID
    query = "INSERT INTO stokvels (name, description, created_by, monthly_contribution) VALUES (%s, %s, %s, %s) RETURNING id"
    result = support.execute_query(
    "insert", query, (name, description, user_id, monthly_contribution))

    stokvel_id = result[0] if result else None
    if stokvel_id:
        # Add the creator as the first member
        support.execute_query(
    "insert",
    "INSERT INTO stokvel_members (stokvel_id, user_id, role) VALUES (%s, %s, %s)",
    (stokvel_id,
    user_id,
     'admin'))
        # Add the creator as the first member or update their role to admin if already a member
        existing = support.execute_query("search", "SELECT id FROM stokvel_members WHERE stokvel_id = %s AND user_id = %s", (stokvel_id, user_id))
        if existing:
            support.execute_query("update", "UPDATE stokvel_members SET role = %s WHERE stokvel_id = %s AND user_id = %s", ('admin', stokvel_id, user_id))
        else:
            support.execute_query("insert", "INSERT INTO stokvel_members (stokvel_id, user_id, role) VALUES (%s, %s, %s)", (stokvel_id, user_id, 'admin'))
        # Make the user a global admin and update session
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET role = 'admin' WHERE firebase_uid = %s", (user_id,))
                conn.commit()
        session['role'] = 'admin'
        # Create a notification for the creator
        message = f"You successfully created the stokvel '{name}'!"
        link = url_for('view_stokvel_members', stokvel_id=stokvel_id)
        create_notification(
    user_id,
    message,
    link_url=link,
     notification_type='stokvel_created')

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
                # Use firebase_uid directly since the database now uses
                # Firebase UIDs
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

                # Fetch default payment method for display
                cur.execute(
    "SELECT type, details FROM payment_methods WHERE user_id = %s AND is_default = TRUE",
    (firebase_uid,
    ))
                payment_method = cur.fetchone()
                payment_info_text = "No default payment method set. Please add one in settings."
                if payment_method:
                    method_type, details = payment_method
                    if isinstance(details, str):
                        try:
                            details = json.loads(details)
                        except json.JSONDecodeError:
                            details = {}
                    # Ensure details is a dict
                    if not isinstance(details, dict):
                        details = {}
                    if method_type in ['credit_card', 'debit_card', 'card']:
                        card_number = details.get('card_number', '')
                        last4 = card_number[-4:] if len(card_number) >= 4 else card_number
                        payment_info_text = f"Using card ending in {last4}"
                    elif method_type == 'bank_account':
                        bank_name = details.get('bank_name', 'bank')
                        account_number = details.get('account_number', '')
                        last4 = account_number[-4:] if len(account_number) >= 4 else account_number
                        payment_info_text = f"Using {bank_name} account ending in {last4}"

        # Process and render as before
                contributions_list = []
                for row in contributions:
                    try:
                        transaction_date = row[3]
                        if transaction_date:
                            try:
                                transaction_date = transaction_date.strftime(
                                    '%Y-%m-%d %H:%M')
                            except AttributeError:
                                transaction_date = str(transaction_date)
                        else:
                            transaction_date = 'N/A'
                        contribution_dict = {
                            'id': row[0],
    'amount': float(
        row[1]) if row[1] is not None else 0.0,
                            'status': row[2] or 'pending',
                            'created_at': transaction_date,
                            'stokvel_name': row[4] or 'Unknown Stokvel',
         'description': row[5] or 'No description'}
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
        return render_template(
    'contributions.html',
    contributions=contributions_list,
    stokvels=stokvels_list,
     payment_info=payment_info_text)
    except Exception as e:
        print(f"Error in contributions route: {e}")
        flash("An error occurred while loading your contributions.")
        return render_template(
    'contributions.html',
    contributions=[],
    stokvels=[],
     payment_info="Could not load payment info.")


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
            return redirect(url_for('contributions'))
        try:
            amount = float(amount)
            stokvel_id = int(stokvel_id)
            with support.db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if the user is actually a member of this stokvel
                    cur.execute(
    "SELECT 1 FROM stokvel_members WHERE stokvel_id = %s AND user_id = %s",
    (stokvel_id,
     firebase_uid))
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
                        cur.execute(
    "SELECT username FROM users WHERE firebase_uid = %s", (firebase_uid,))
                        user_info = cur.fetchone()
                        user_name = user_info[0] if user_info else "A member"
                    
                    # Insert the contribution transaction
                    cur.execute("""
                        INSERT INTO transactions (user_id, stokvel_id, amount, type, description, transaction_date, status)
                        VALUES (%s, %s, %s, 'contribution', %s, CURRENT_DATE, 'completed')
                    """, (firebase_uid, stokvel_id, amount, description))
                    conn.commit()
            flash("Contribution successful!", "success")
        except Exception as e:
            print(f"Error making contribution: {e}")
            flash("An error occurred while making your contribution.", "danger")
        return redirect(url_for('contributions'))
    # GET request fallback
    # ... existing code ...

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
                payout_keys = [
    'amount',
    'description',
    'transaction_date',
    'stokvel_name',
     'status']
                for p_tuple in payouts_tuples:
                    payouts_list.append(dict(zip(payout_keys, p_tuple)))

                # Get stokvels the user is a member of to show options for
                # payout requests
                cur.execute("""
                    SELECT s.id, s.name, s.target_amount, s.monthly_contribution, s.target_date
                    FROM stokvels s
                    JOIN stokvel_members sm ON s.id = sm.stokvel_id
                    WHERE sm.user_id = %s
                """, (firebase_uid,))
                stokvel_options = cur.fetchall()

        return render_template(
    'payouts.html',
    payouts=payouts_list,
     stokvel_options=stokvel_options)
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
                # In a real app, this would be a 'pending' status requiring
                # approval.
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

                    # Create notification for stokvel admin
                    message = f"{user_name} requested a payout of R{amount:.2f} from '{stokvel_name}' stokvel."
                    # Changed from 'payouts' to the specific admin approval
                    # page if one exists
                    link = url_for('payouts')
                    create_notification(
                        admin_user_id,
                        message,
                        link_url=link,
                        notification_type='payout_requested')

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
            with conn.cursor() as cur:
                # Use firebase_uid directly since the database now uses
                # Firebase UIDs
                cur.execute("""
                    SELECT id, name, target_amount, current_amount, target_date, status, created_at
                    FROM savings_goals
                    WHERE user_id = %s
                    ORDER BY target_date ASC
                """, (firebase_uid,))
                goals_tuples = cur.fetchall()

                # Convert tuples to dictionaries for easier access in template
                goals_list = []
                goal_keys = [
                    'id',
                    'name',
                    'target_amount',
                    'current_amount',
                    'target_date',
                    'status',
                    'created_at'
                ]
                for g_tuple in goals_tuples:
                    goals_list.append(dict(zip(goal_keys, g_tuple)))

                # Fetch default payment method for display
                cur.execute(
                    "SELECT type, details FROM payment_methods WHERE user_id = %s AND is_default = TRUE",
                    (firebase_uid,)
                )
                payment_method = cur.fetchone()
                payment_info_text = "No default payment method set. Please add one in settings."
                if payment_method:
                    method_type, details = payment_method
                    if isinstance(details, str):
                        try:
                            details = json.loads(details)
                        except json.JSONDecodeError:
                            details = {}
                    if not isinstance(details, dict):
                        details = {}
                    if method_type in ['credit_card', 'debit_card', 'card']:
                        card_number = details.get('card_number', '')
                        last4 = card_number[-4:] if len(card_number) >= 4 else card_number
                        payment_info_text = f"Using card ending in {last4}"
                    elif method_type == 'bank_account':
                        bank_name = details.get('bank_name', 'bank')
                        account_number = details.get('account_number', '')
                        last4 = account_number[-4:] if len(account_number) >= 4 else account_number
                        payment_info_text = f"Using {bank_name} account ending in {last4}"

        return render_template(
            'savings_goals.html',
            goals=goals_list,
            payment_info=payment_info_text)
    except Exception as e:
        print(f"Savings goals page error: {e}")
        flash("An error occurred while loading your savings goals. Please try again.")
        return redirect('/home')


@app.route('/create_savings_goal', methods=['POST'])
@login_required
def create_savings_goal():
    firebase_uid = session['user_id']
    name = request.form.get('name')
    target_amount = request.form.get('target_amount')
    target_date = request.form.get('target_date')  # Format 'YYYY-MM-DD'

    if not all([name, target_amount, target_date]):
        flash("All fields are required to create a savings goal.")
        return redirect('/savings_goals')

    try:
        target_amount = float(target_amount)
        # current_amount starts at 0

        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO savings_goals (user_id, name, target_amount, current_amount, target_date, status)
                    VALUES (%s, %s, %s, %s, %s, 'active')
                    RETURNING id
                """, (firebase_uid, name, target_amount, 0.0, target_date))
                conn.commit()

        flash(f"Savings goal '{name}' created successfully!")
        return redirect('/savings_goals')
    except ValueError:
        flash("Target amount must be a number.")
        return redirect('/savings_goals')
    except Exception as e:
        print(f"Error creating savings goal: {e}")
        flash("An error occurred while creating the savings goal. Please try again.")
        return redirect('/savings_goals')


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

                # Get default payment method for flash message
                cur.execute(
    "SELECT type, details FROM payment_methods WHERE user_id = %s AND is_default = TRUE",
    (firebase_uid,
    ))
                payment_method = cur.fetchone()
                payment_info = ""
                if payment_method:
                    method_type, details = payment_method
                    import json
                    if isinstance(details, str):
                        try:
                            details = json.loads(details)
                        except Exception:
                            details = {}
                    if not isinstance(details, dict):
                        details = {}
                    if method_type in ['credit_card', 'debit_card', 'card']:
                        last4 = details.get('card_number', '')[-4:]
                        payment_info = f" from your card ending in {last4}"
                    elif method_type == 'bank_account':
                        payment_info = f" from your {details.get('bank_name', 'bank')} account"

                conn.commit()

        flash(f"Successfully contributed R{amount:.2f} to your savings goal{payment_info}!")
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
    # Debug log
    print(
    f"DEBUG: Navigating to view_stokvel_members for stokvel_id: {stokvel_id}")
    try:
        # Ensure user_id is retrieved for permission checks
        user_id = session.get('user_id')
        if not user_id:
            flash("Please log in to view stokvel members.")
            return redirect('/login')

        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Get stokvel details, including id and description
                cur.execute(
    "SELECT id, name, description, monthly_contribution, target_amount, target_date, total_pool FROM stokvels WHERE id = %s",
    (stokvel_id,
    ))
                stokvel_tuple = cur.fetchone()
                # Debug log
                print(f"DEBUG: Stokvel query result: {stokvel_tuple}")

                if not stokvel_tuple:
                    flash("Stokvel not found.")
                    print(
    f"DEBUG: Stokvel with id {stokvel_id} not found.")  # Debug log
                    return redirect('/stokvels')

                # Convert stokvel tuple to a dictionary
                stokvel_keys = [
    'id',
    'name',
    'description',
    'monthly_contribution',
    'target_amount',
    'target_date',
     'total_pool']
                stokvel = dict(zip(stokvel_keys, stokvel_tuple))
                print(f"DEBUG: Converted stokvel dict: {stokvel}")  # Debug log

                # Get registered members (joined with users)
                cur.execute("""
                    SELECT u.username, u.email, sm.role, sm.id as member_id
                    FROM users u
                    JOIN stokvel_members sm ON u.firebase_uid = sm.user_id
                    WHERE sm.stokvel_id = %s
                """, (stokvel_id,))
                members_tuples = cur.fetchall()
                # Debug log
                print(f"DEBUG: Members query result: {members_tuples}")

                # Get pending members (no user_id, just email)
                cur.execute("""
                    SELECT NULL as username, sm.email, sm.role, sm.id as member_id
                    FROM stokvel_members sm
                    WHERE sm.stokvel_id = %s AND sm.user_id IS NULL AND sm.email IS NOT NULL
                """, (stokvel_id,))
                pending_members_tuples = cur.fetchall()
                # Debug log
                print(
    f"DEBUG: Pending members query result: {pending_members_tuples}")

                # Combine both lists
                all_members_tuples = list(
                    members_tuples) + list(pending_members_tuples)

                # Convert members tuples to a list of dictionaries
                members_list = []
                member_keys = ['username', 'email', 'role', 'member_id']
                for member_tuple in all_members_tuples:
                    members_list.append(dict(zip(member_keys, member_tuple)))
                # Debug log
                print(f"DEBUG: Converted members list: {members_list}")

                # Check if current user is a member and their role
                cur.execute("""
                    SELECT role FROM stokvel_members WHERE stokvel_id = %s AND user_id = %s
                """, (stokvel_id, user_id))
                user_stokvel_role = cur.fetchone()
                is_member = user_stokvel_role is not None
                user_role_in_stokvel = user_stokvel_role[0] if user_stokvel_role else 'none'
                # Debug log
                print(
    f"DEBUG: Current user {user_id} role in stokvel {stokvel_id}: {user_role_in_stokvel}, Is member: {is_member}")

        return render_template(
    'stokvel_members.html',
    stokvel=stokvel,
    members=members_list,
    stokvel_id=stokvel_id,
    is_member=is_member,
     user_role_in_stokvel=user_role_in_stokvel)
    except Exception as e:
        # Enhanced error logging
        print(f"ERROR: view_stokvel_members failed: {e}")
        flash("An error occurred while loading stokvel members. Please try again.")
        return redirect('/stokvels')


@app.route('/stokvel/<int:stokvel_id>/join', methods=['POST'])
@login_required
def join_stokvel(stokvel_id):
    user_id = session['user_id']
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Check if already a member
                cur.execute(
    "SELECT 1 FROM stokvel_members WHERE stokvel_id = %s AND user_id = %s",
    (stokvel_id,
     user_id))
                if cur.fetchone():
                    flash("You are already a member of this stokvel.")
                    return redirect(f'/stokvel/{stokvel_id}/members')

                # Get stokvel name and admin user for notification
                cur.execute("""
                    SELECT s.name, sm.user_id 
                    FROM stokvels s
                    JOIN stokvel_members sm ON s.id = sm.stokvel_id
                    WHERE s.id = %s AND sm.role = 'admin'
                """, (stokvel_id,))
                stokvel_info = cur.fetchone()
                
                # Get the joining user's name
                cur.execute(
    "SELECT username FROM users WHERE firebase_uid = %s", (user_id,))
                user_info = cur.fetchone()
                user_name = user_info[0] if user_info else "A new member"

                cur.execute(
    "INSERT INTO stokvel_members (stokvel_id, user_id) VALUES (%s, %s)",
    (stokvel_id,
     user_id))
                conn.commit()
                
                # Create notification for stokvel admin
                if stokvel_info:
                    stokvel_name, admin_user_id = stokvel_info
                    message = f"{user_name} has joined '{stokvel_name}' stokvel."
                    link = url_for(
    'view_stokvel_members',
     stokvel_id=stokvel_id)
                    create_notification(
    admin_user_id,
    message,
    link_url=link,
     notification_type='member_joined')
                
                # Create notification for the joining user
                if stokvel_info:
                    stokvel_name = stokvel_info[0]
                    user_message = f"Welcome! You have successfully joined '{stokvel_name}' stokvel."
                    create_notification(
    user_id,
    user_message,
    link_url=link,
     notification_type='joined_stokvel')
                
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
                # Get stokvel name and admin user for notification before
                # leaving
                cur.execute("""
                    SELECT s.name, sm.user_id 
                    FROM stokvels s
                    JOIN stokvel_members sm ON s.id = sm.stokvel_id
                    WHERE s.id = %s AND sm.role = 'admin'
                """, (stokvel_id,))
                stokvel_info = cur.fetchone()
                
                # Get the leaving user's name
                cur.execute(
    "SELECT username FROM users WHERE firebase_uid = %s", (user_id,))
                user_info = cur.fetchone()
                user_name = user_info[0] if user_info else "A member"

                cur.execute(
    "DELETE FROM stokvel_members WHERE stokvel_id = %s AND user_id = %s",
    (stokvel_id,
     user_id))
                conn.commit()
                
                # Create notification for stokvel admin
                if stokvel_info:
                    stokvel_name, admin_user_id = stokvel_info
                    message = f"{user_name} has left '{stokvel_name}' stokvel."
                    link = url_for(
    'view_stokvel_members',
     stokvel_id=stokvel_id)
                    create_notification(
    admin_user_id,
    message,
    link_url=link,
     notification_type='member_left')
                
                # Create notification for the leaving user
                if stokvel_info:
                    stokvel_name = stokvel_info[0]
                    user_message = f"You have successfully left '{stokvel_name}' stokvel."
                    create_notification(
    user_id,
    user_message,
    link_url=url_for('stokvels'),
     notification_type='left_stokvel')
                
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
                cur.execute(
    "DELETE FROM transactions WHERE stokvel_id = %s", (stokvel_id,))
                # Delete all members from this stokvel
                cur.execute(
    "DELETE FROM stokvel_members WHERE stokvel_id = %s", (stokvel_id,))
                # Delete the stokvel itself
                cur.execute(
    "DELETE FROM stokvels WHERE id = %s", (stokvel_id,))
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
                # Fetch notifications for the user using firebase_uid
                cur.execute("""
                    SELECT id, message, type, is_read, link_url, created_at
                    FROM notifications 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC
                """, (user_id,))
                notifications = cur.fetchall()
                
        return render_template(
    'user_notifications.html',
     notifications=notifications)
    except Exception as e:
        print(f"Error fetching notifications: {e}")
        flash("Could not load notifications.", "danger")
        return redirect(url_for('home'))


@app.route('/notifications/clear', methods=['POST'])
@login_required
def clear_notifications():
    user_id = session['user_id']
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
    "DELETE FROM notifications WHERE user_id = %s", (user_id,))
                conn.commit()
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

# API routes for notification management


@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    try:
        user_id = session.get('user_id')
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE notifications 
                    SET is_read = TRUE 
                    WHERE id = %s AND user_id = %s
                """, (notification_id, user_id))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/notifications/<int:notification_id>/unread', methods=['POST'])
@login_required
def mark_notification_unread(notification_id):
    try:
        user_id = session.get('user_id')
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE notifications 
                    SET is_read = FALSE 
                    WHERE id = %s AND user_id = %s
                """, (notification_id, user_id))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error marking notification as unread: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    try:
        user_id = session.get('user_id')
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE notifications 
                    SET is_read = TRUE 
                    WHERE user_id = %s
                """, (user_id,))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error marking all notifications as read: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/notifications/mark-all-unread', methods=['POST'])
@login_required
def mark_all_notifications_unread():
    try:
        user_id = session.get('user_id')
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE notifications 
                    SET is_read = FALSE 
                    WHERE user_id = %s
                """, (user_id,))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error marking all notifications as unread: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/payment_methods')
@login_required
def payment_methods():
    import json
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

                payment_methods_list = []
                payment_method_keys = [
    'id', 'type', 'details', 'is_default', 'created_at']
                for pm_tuple in payment_methods_tuples:
                    pm_dict = dict(zip(payment_method_keys, pm_tuple))
                    # Parse details and mask sensitive info
                    masked_details = ''
                    try:
                        details = pm_dict['details']
                        if isinstance(details, str):
                            details_json = json.loads(details)
                        else:
                            details_json = details
                        if pm_dict['type'] in [
    'credit_card', 'debit_card', 'card']:
                            card_number = details_json.get('card_number', '')
                            last4 = card_number[-4:] if len(
                                card_number) >= 4 else card_number
                            masked_number = '**** **** **** ' + last4
                            exp = details_json.get('expiry_date', '')
                            card_holder = details_json.get(
                                'card_holder_name', 'N/A')
                            masked_details = f"{masked_number}  Exp: {exp}"
                            pm_dict['card_holder_name'] = card_holder
                        elif pm_dict['type'] == 'bank_account':
                            acc = details_json.get('account_number', '')
                            last4 = acc[-4:] if len(acc) >= 4 else acc
                            bank = details_json.get('bank_name', '')
                            account_holder = details_json.get(
                                'account_holder_name', 'N/A')
                            masked_details = f"Account: ****{last4}  ({bank})"
                            pm_dict['account_holder_name'] = account_holder
                        elif pm_dict['type'] == 'mobile_money':
                            phone = details_json.get('phone', '')
                            last4 = phone[-4:] if len(phone) >= 4 else phone
                            provider = details_json.get('provider', '')
                            masked_details = f"Mobile: ****{last4}  {provider}"
                        else:
                            # fallback: show only non-sensitive fields
                            masked_details = ', '.join(
    f"{k}: {v}" for k,
     v in details_json.items() if 'number' not in k and 'card' not in k)
                    except Exception as e:
                        masked_details = 'Payment details unavailable'
                    pm_dict['masked_details'] = masked_details
                    payment_methods_list.append(pm_dict)
        return render_template(
    'payment_methods.html',
     payment_methods=payment_methods_list)
    except Exception as e:
        print(f"Payment methods page error: {e}")
        flash("An error occurred while loading your payment methods. Please try again.")
        return render_template('payment_methods.html', payment_methods=[])


@app.route('/add_payment_method', methods=['POST'])
@login_required
def add_payment_method():
    user_id = session['user_id']
    payment_type = request.form.get('type')
    is_default = request.form.get('is_default') == 'true'
    details_dict = {}
    import json

    if payment_type in ['credit_card', 'debit_card']:
        card_holder_name = request.form.get('card_holder_name')
        card_number = request.form.get('card_number')
        expiry_date = request.form.get('expiry_date')
        cvv = request.form.get('cvv')
        if not all([card_holder_name, card_number, expiry_date, cvv]):
            flash("All card fields are required.", "danger")
            return redirect(url_for('payment_methods'))
        details_dict = {
            "card_holder_name": card_holder_name,
            "card_number": card_number,
            "expiry_date": expiry_date,
            # "cvv": cvv
        }
    elif payment_type == 'bank_account':
        account_holder_name = request.form.get('account_holder_name')
        account_number = request.form.get('account_number')
        bank_name = request.form.get('bank_name')
        if not all([account_holder_name, account_number, bank_name]):
            flash("All bank account fields are required.", "danger")
            return redirect(url_for('payment_methods'))
        details_dict = {
            "account_holder_name": account_holder_name,
            "account_number": account_number,
            "bank_name": bank_name
        }
    else:
        flash("Invalid payment type selected.", "danger")
        return redirect(url_for('payment_methods'))

    details_json = json.dumps(details_dict)

    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                if is_default:
                    cur.execute(
    "UPDATE payment_methods SET is_default = FALSE WHERE user_id = %s", (user_id,))
                
                cur.execute("""
                    INSERT INTO payment_methods (user_id, type, details, is_default)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, payment_type, details_json, is_default))
                conn.commit()

                # Create notification for payment method addition
                payment_type_name = "credit card" if payment_type in [
                    'credit_card', 'debit_card'] else "bank account"
                message = f"Your {payment_type_name} has been added successfully!"
                create_notification(user_id, message, link_url=url_for(
                    'payment_methods'), notification_type='payment_method_added')

        flash("Payment method added successfully!", "success")
        return redirect(url_for('payment_methods'))
    except Exception as e:
        print(f"Error adding payment method: {e}")
        flash(
    "An error occurred while adding the payment method. Please try again.",
     "danger")
        return redirect(url_for('payment_methods'))


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
                cur.execute(
    "UPDATE payment_methods SET is_default = FALSE WHERE user_id = %s", (user_id,))
                # Set new default
                cur.execute("""
                    UPDATE payment_methods 
                    SET is_default = TRUE 
                    WHERE id = %s AND user_id = %s
                """, (method_id, user_id))
                conn.commit()

                # Create notification for default payment method change
                message = "Your default payment method has been updated successfully!"
                create_notification(user_id, message, link_url=url_for(
                    'payment_methods'), notification_type='default_payment_updated')

        flash("Default payment method updated successfully!")
        return redirect('/payment_methods')
    except Exception as e:
        print(f"Error setting default payment method: {e}")
        flash(
            "An error occurred while updating the default payment method. Please try again.")
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

                # Create notification for payment method deletion
                message = "Your payment method has been deleted successfully!"
                create_notification(user_id, message, link_url=url_for(
                    'payment_methods'), notification_type='payment_method_deleted')

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
            user_settings['language_preference'] = session.get(
                'language_preference', 'en')

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
            UPDATE user_settings
            SET email_notifications = %s, sms_notifications = %s, weekly_summary = %s, receive_promotions = %s
            WHERE user_id = %s
        """
        params = (
            email_notifications,
            sms_notifications,
            weekly_summary,
            receive_promotions,
            user_id)

    elif form_section == 'security':
        two_factor_enabled = 'two_factor_enabled' in request.form
        query = "UPDATE users SET two_factor_enabled = %s WHERE firebase_uid = %s"
        params = (two_factor_enabled, user_id)

    if query and params:
        try:
            support.execute_query("update", query, params)
            
            # Create notification for settings update
            message = "Your settings have been updated successfully!"
            create_notification(user_id, message, link_url=url_for(
                'settings'), notification_type='settings_updated')
            
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
                # Get user data, ensuring all columns including kyc_status are selected
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
    support.execute_query(
        "update",
        query,
        (username, phone, date_of_birth, bio, full_name, id_number, address, user_id))
    
    # Create notification for profile update
    message = "Your profile has been updated successfully!"
    create_notification(user_id, message, link_url=url_for(
        'profile'), notification_type='profile_updated')
    
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
        support.execute_query(
    "update",
    "UPDATE users SET profile_picture = %s WHERE firebase_uid = %s",
    (filename,
     user_id))
        
        # Update session variable so new picture is immediately visible
        session['profile_picture'] = filename
        
        # Create notification for profile picture update
        message = "Your profile picture has been updated successfully!"
        create_notification(user_id, message, link_url=url_for(
            'profile'), notification_type='profile_picture_updated')
        
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

    try:
        id_filename = secure_filename(f"{user_id}_id_{id_doc.filename}")
        address_filename = secure_filename(
            f"{user_id}_address_{address_doc.filename}")

        id_filepath = os.path.join(
    app.config['KYC_UPLOAD_FOLDER'], id_filename)
        address_filepath = os.path.join(
    app.config['KYC_UPLOAD_FOLDER'], address_filename)

        id_doc.save(id_filepath)
        address_doc.save(address_filepath)

        # Update user's KYC info in the database and set status to 'pending'
        query = "UPDATE users SET id_document = %s, proof_of_address = %s, kyc_status = 'pending' WHERE firebase_uid = %s"
        support.execute_query(
    "update", query, (id_filename, address_filename, user_id))

        # Create notification for KYC upload
        message = "Your KYC documents have been uploaded successfully and are pending review."
        create_notification(
    user_id,
    message,
    link_url=url_for('profile'),
     notification_type='kyc_uploaded')

        flash(
    'KYC documents uploaded successfully. They are now pending review.',
     'success')
    except Exception as e:
        print(f'An error occurred during KYC upload: {e}')
        flash(f'An error occurred during KYC upload: {e}', 'danger')

    return redirect(url_for('profile'))           
    
    
def inject_user_name():
    username = None
    language_preference = 'en'  # Default language
    notification_count = 0  # Default notification count
    
    if 'user_id' in session:
        # Changed to firebase_uid
        user_query = "SELECT username FROM users WHERE firebase_uid = %s"
        user_data = support.execute_query(
    "search", user_query, (session['user_id'],))
        if user_data:
            username = user_data[0][0]
        
        # Get notification count
        notification_count = get_notification_count(session['user_id'])
        
        # Get user's language preference from session first, then try database
        if 'language_preference' in session:
            language_preference = session['language_preference']
        else:
            # Try to get from database, but fall back to session if column
            # doesn't exist
            try:
                lang_query = "SELECT language_preference FROM users WHERE firebase_uid = %s"
                lang_data = support.execute_query(
    "search", lang_query, (session['user_id'],))
                if lang_data and lang_data[0][0]:
                    language_preference = lang_data[0][0]
                    # Store in session for future use
                    session['language_preference'] = language_preference
            except Exception as e:
                print(f"Error getting language preference from database: {e}")
                # Use session default or fallback to English
                language_preference = session.get('language_preference', 'en')
    
    return dict(
    username=username,
    user_language=language_preference,
    notification_count=notification_count,
     t=get_text)


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
        print(f"DEBUG: send_email - SMTP_PASSWORD: {'*' * len(str(smtp_password))}")  # Mask password for security
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
        return render_template('pricing.html', pricing_plans=[])  # Render with empty list on error


# Add this dictionary to store temporary stokvel creation data
stokvel_creation_state = {}


def rule_based_chat(user_message, user_id, user_name):
    user_message_lower = user_message.lower()
    response = None

    # Get or initialize user's creation state
    creation_state = stokvel_creation_state.get(user_id, {})

    # Direct Stokvel Creation Flow
    if 'create stokvel' in user_message_lower or creation_state.get(
        'creating_stokvel'):
        if not creation_state.get('creating_stokvel'):
            # Start the creation flow
            stokvel_creation_state[user_id] = {
                'creating_stokvel': True,
                'step': 'name',
                'data': {}
            }
            return "Let's create your stokvel! What would you like to name it?"

        current_step = stokvel_creation_state[user_id]['step']
        data = stokvel_creation_state[user_id]['data']

        if current_step == 'name':
            data['name'] = user_message.strip()
            stokvel_creation_state[user_id]['step'] = 'monthly_contribution'
            return "Great! How much should the monthly contribution be? (Enter amount in Rands)"

        elif current_step == 'monthly_contribution':
            try:
                amount = float(
    user_message.replace(
        'R',
        '').replace(
            ',',
             '').strip())
                data['monthly_contribution'] = amount
                stokvel_creation_state[user_id]['step'] = 'target_amount'
                return "What's the target amount for this stokvel? (Enter 0 if no specific target)"

            except ValueError:
                return "Please enter a valid amount (e.g., 500 or R500)"

        elif current_step == 'target_amount':
            try:
                amount = float(
    user_message.replace(
        'R',
        '').replace(
            ',',
             '').strip())
                data['target_amount'] = amount
                stokvel_creation_state[user_id]['step'] = 'target_date'
                return "When do you want to reach this target? (Format: YYYY-MM-DD, or type 'none' for no specific date)"

            except ValueError:
                return "Please enter a valid amount (e.g., 5000 or R5000)"

        elif current_step == 'target_date':
            if user_message_lower == 'none':
                data['target_date'] = None
            else:
                try:
                    data['target_date'] = datetime.strptime(
                        user_message.strip(), '%Y-%m-%d')
                except ValueError:
                    return "Please enter a valid date (YYYY-MM-DD) or 'none'"

            # Create the stokvel with all collected data
            try:
                description = f"Stokvel created via chat by {user_name}"
                query = """
                    INSERT INTO stokvels 
                    (name, description, created_by, monthly_contribution, target_amount, target_date) 
                    VALUES (%s, %s, %s, %s, %s, %s) 
                    RETURNING id
                """
                result = support.execute_query("insert", query, (
                    data['name'],
                    description,
                    user_id,
                    data['monthly_contribution'],
                    data.get('target_amount', 0),
                    data.get('target_date')
                ))

                if result and result[0]:
                    stokvel_id = result[0]
                    # Add creator as admin
                    support.execute_query("insert",
                        "INSERT INTO stokvel_members (stokvel_id, user_id, role) VALUES (%s, %s, %s)",
                        (stokvel_id, user_id, 'admin'))

                    # Create success notification
                    message = f"You successfully created the stokvel '{data['name']}'!"
                    link = url_for(
    'view_stokvel_members',
     stokvel_id=stokvel_id)
                    create_notification(
    user_id,
    message,
    link_url=link,
     notification_type='stokvel_created')

                    # Clear the creation state
                    del stokvel_creation_state[user_id]

                    summary = (
                        f"Perfect! I've created your stokvel with these details:\n\n"
                        f"Name: {data['name']}\n"
                        f"Monthly Contribution: R{data['monthly_contribution']:.2f}\n"
                        f"Target Amount: {'R{:.2f}'.format(data['target_amount']) if data.get('target_amount') else 'Not set'}\n"
                        f"Target Date: {data['target_date'].strftime('%Y-%m-%d') if data.get('target_date') else 'Not set'}\n\n"
                        f"To add members, say: add member email@example.com to '{data['name']}'"
                    )
                    return summary
                else:
                    # Clear the creation state on error
                    if user_id in stokvel_creation_state:
                        del stokvel_creation_state[user_id]
                    return "Sorry, I couldn't create the stokvel. Please try again."

            except Exception as e:
                print(f"Error creating stokvel: {e}")
                # Clear the creation state on error
                if user_id in stokvel_creation_state:
                    del stokvel_creation_state[user_id]
                return "Sorry, I couldn't create the stokvel due to a system error. Please try again."

    # Direct Member Addition (keep existing code)
    if 'add member' in user_message_lower:
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', user_message)
        stokvel_match = re.search(r'to\s+["\']?([^"\']+)["\']?', user_message)

        if not email_match or not stokvel_match:
            return "Please specify both the email and stokvel name. Example: add member user@example.com to 'My Stokvel'"

        email = email_match.group(0)
        stokvel_name = stokvel_match.group(1).strip()

        try:
            # Find stokvel
            query = "SELECT id FROM stokvels WHERE name = %s AND created_by = %s"
            result = support.execute_query(
    "select", query, (stokvel_name, user_id))

            if result and result[0]:
                stokvel_id = result[0][0]
                # Add member
                support.execute_query("insert",
                    "INSERT INTO stokvel_members (stokvel_id, user_id, role, email) VALUES (%s, NULL, %s, %s)",
                    (stokvel_id, 'member', email))
                return f"✅ Added {email} to '{stokvel_name}'. They'll receive an invitation email."
            else:
                return "Sorry, I couldn't add the member. Please check the stokvel name and try again."
        except Exception as e:
            print(f"Error adding member: {e}")
            return "Sorry, I couldn't add the member due to a system error. Please try again."

    # Existing feature explanations
    sorted_features = sorted(feature_faq.keys(), key=len, reverse=True)
    for feature in sorted_features:
        if feature in user_message_lower:
            response = feature_faq[feature]
            break

    if response is None:
        response = "Try these commands:\n- Create stokvel\n- Add member email@example.com to 'stokvel name'"

    return response


@app.route('/chat', methods=['POST'])
@login_required
def handle_chat():
    """
    Handles incoming chat messages from the frontend.
    """
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        mode = data.get('mode', 'rule')  # Default to 'rule'
        user_id = session.get('user_id')
        user_name = session.get('username', 'User')
        response = ""

        if not user_message:
            return jsonify(
                {'response': 'Empty message received.', 'mode': mode}), 400

        if mode == 'ai':
            if not openrouter_available:
                response = "Sorry, AI Mode is currently unavailable."
            else:
                try:
                    # Using requests to call OpenRouter API
                    api_response = requests.post(
                        url="https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {openrouter_api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "google/gemma-2-9b-it",
                            "messages": [{"role": "user", "content": user_message}]
                        }
                    )
                    api_response.raise_for_status()
                    response = api_response.json(
                    )['choices'][0]['message']['content']
                except Exception as e:
                    print(f"OpenRouter API error: {e}")
                    response = "Sorry, I encountered an error with the AI service. Please try again later."
        else:  # mode == 'rule'
            response = rule_based_chat(user_message, user_id, user_name)

        # Save chat history (for both modes)
        try:
            with support.db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO chat_history (user_id, message, response)
                        VALUES (%s, %s, %s)
                    """, (user_id, user_message, response))
                    conn.commit()
        except Exception as e:
            print(f"Error saving chat history: {e}")

        # Return the response to the frontend
        return jsonify(
    response=response,
    mode=mode,
     timestamp=datetime.now().strftime('%H:%M'))

    except Exception as e:
        print(f"Chat handler error: {e}")
        return jsonify(
            {'response': 'An unexpected error occurred. Please try again.', 'mode': 'error'}), 500


@app.route('/stokvel/<int:stokvel_id>/statement/download')
@login_required
def download_stokvel_statement_pdf(stokvel_id):
    period = request.args.get('period', 'all')
    user_id = session.get('user_id')
    # Fetch stokvel info and transactions
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
    "SELECT name FROM stokvels WHERE id = %s", (stokvel_id,))
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
    from reportlab.platypus import Image, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib import colors
    from reportlab.graphics.shapes import Drawing, Line
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    logo_path = os.path.join('static', 'kasikash-logo.png')
    if not os.path.exists(logo_path):
        logo_path = os.path.join('static', 'logo.png.png')
    logo_img = None
    if os.path.exists(logo_path):
        try:
            logo_img = Image(logo_path, width=65, height=65)
            logo_img.hAlign = 'LEFT'
        except Exception as e:
            print(f"Error adding logo: {e}")
    # Custom styles
    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], fontSize=22, alignment=TA_CENTER, spaceAfter=6)
    timestamp_style = ParagraphStyle('TimestampStyle', parent=styles['Normal'], fontSize=10, alignment=TA_RIGHT, textColor=colors.HexColor('#666'))
    statement_title_style = ParagraphStyle('StatementTitle', parent=styles['Title'], fontSize=18, alignment=TA_CENTER, spaceAfter=8)
    # Title and timestamp
    from datetime import datetime
    generated_str = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by KasiKash"
    main_title = f"KasiKash {stokvel_name} Statement"
    title = Paragraph(f'<b>{main_title}</b>', title_style)
    timestamp = Paragraph(generated_str, timestamp_style)
    # Header table: logo | title | timestamp
    header_data = [[logo_img, title, timestamp]]
    header_table = Table(header_data, colWidths=[70, 350, 140])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(header_table)
    # Cyan horizontal line
    line = Drawing(560, 2)
    line.add(Line(0, 0, 540, 0, strokeColor=colors.HexColor('#22d3ee'), strokeWidth=3))
    elements.append(line)
    elements.append(Spacer(1, 16))
    # Table header and data
    data = [["Date", "Type", "Description", "Amount", "Member Email"]]
    for row in transactions:
        date_str = row[0].strftime('%Y-%m-%d') if row[0] else ''
        data.append([date_str, row[1], row[2], f"R{row[3]:.2f}", row[4] or ''])
    table = Table(data, repeatRows=1, hAlign='LEFT', colWidths=[75, 65, 160, 80, 170])
    # Table style
    table_style = TableStyle([
        ('BOX', (0,0), (-1,-1), 1.2, colors.HexColor('#2453c7')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#2453c7')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2453c7')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 13),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ])
    # Alternating row colors (stronger contrast)
    for i in range(1, len(data)):
        if i % 2 == 0:
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#e3f2fd'))
        else:
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)
    table.setStyle(table_style)
    elements.append(table)
    # Footer with page number
    def add_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.HexColor('#888'))
        canvas.drawRightString(550, 15, f"Page {doc.page}")
        canvas.restoreState()
    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    buffer.seek(0)
    return send_file(
    buffer,
    as_attachment=True,
    download_name=f"statement_{stokvel_id}_{period}.pdf",
     mimetype='application/pdf')


@app.route('/virtual-rewards')
def virtual_rewards():
    # You can add login checks or user context here if needed
    return render_template('virtual_rewards.html')


# Register the rewards blueprint
app.register_blueprint(rewards_bp, url_prefix='/rewards')

# Debug: Print all registered endpoints
print('Registered endpoints:')
for rule in app.url_map.iter_rules():
    print(rule.endpoint, rule)

print("Registered endpoints:")
for rule in app.url_map.iter_rules():
    print(rule.endpoint, rule)

# ... after app = Flask(__name__) ...

app.register_blueprint(advisor_bp)

# ... rest of the code ...

# Initialize Flask-SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Real-time Stokvel Chat Events ---
@socketio.on('join_stokvel_room')
def handle_join_stokvel_room(data):
    stokvel_id = data.get('stokvel_id')
    user_id = session.get('user_id')
    if stokvel_id and user_id:
        join_room(f'stokvel_{stokvel_id}')
        emit('status', {'msg': f'User joined stokvel chat.'}, room=f'stokvel_{stokvel_id}')

@socketio.on('send_message')
def handle_send_message(data):
    stokvel_id = data.get('stokvel_id')
    message = data.get('message')
    user_id = session.get('user_id')
    username = None
    if not (stokvel_id and message and user_id):
        return
    # Save message to DB
    with support.db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO stokvel_chat_messages (stokvel_id, user_id, message) VALUES (%s, %s, %s) RETURNING timestamp", (stokvel_id, user_id, message))
            timestamp = cur.fetchone()[0]
            conn.commit()
            # Get username for display
            cur.execute("SELECT username FROM users WHERE firebase_uid = %s", (user_id,))
            user_row = cur.fetchone()
            if user_row:
                username = user_row[0]
    emit('receive_message', {
        'stokvel_id': stokvel_id,
        'user_id': user_id,
        'username': username,
        'message': message,
        'timestamp': str(timestamp)
    }, room=f'stokvel_{stokvel_id}')

@socketio.on('fetch_messages')
def handle_fetch_messages(data):
    stokvel_id = data.get('stokvel_id')
    if not stokvel_id:
        return
    messages = []
    with support.db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT m.user_id, u.username, m.message, m.timestamp
                FROM stokvel_chat_messages m
                JOIN users u ON m.user_id = u.firebase_uid
                WHERE m.stokvel_id = %s
                ORDER BY m.timestamp ASC
            """, (stokvel_id,))
            for row in cur.fetchall():
                messages.append({
                    'user_id': row[0],
                    'username': row[1],
                    'message': row[2],
                    'timestamp': str(row[3])
                })
    emit('chat_history', {'messages': messages})

@app.route('/stokvel/<int:stokvel_id>/add_member', methods=['POST'])
@login_required
def add_stokvel_member(stokvel_id):
    email = request.form.get('email')
    if not email:
        flash("Email is required to add a member.", "danger")
        return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))

    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Add a pending member with just an email (user_id is NULL)
                cur.execute(
                    "INSERT INTO stokvel_members (stokvel_id, email, role) VALUES (%s, %s, %s)",
                    (stokvel_id, email, 'member')
                )
                conn.commit()
        # Send invitation email
        from flask import url_for
        stokvel_name = None
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM stokvels WHERE id = %s", (stokvel_id,))
                row = cur.fetchone()
                if row:
                    stokvel_name = row[0]
        invite_link = url_for('register', _external=True)
        subject = f"You've been invited to join the stokvel '{stokvel_name}' on KasiKash!"
        html_content = f"""
        <html><body>
        <p>Hello,</p>
        <p>You have been invited to join the stokvel <b>{stokvel_name}</b> on KasiKash.</p>
        <p>If you already have an account, simply log in with this email address. If not, click below to register:</p>
        <p><a href='{invite_link}'>Join KasiKash</a></p>
        <p>Once you register or log in, you'll see your stokvel automatically.</p>
        <p>Thanks,<br>The KasiKash Team</p>
        </body></html>
        """
        send_email(email, subject, html_content)
        flash("Member invitation sent!", "success")
    except Exception as e:
        print(f"Error adding member: {e}")
        flash("Failed to add member. Please try again.", "danger")
    return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))

@app.route('/stokvel/<int:stokvel_id>/remove_member/<int:member_id>', methods=['POST'])
@login_required
def remove_stokvel_member(stokvel_id, member_id):
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM stokvel_members WHERE id = %s AND stokvel_id = %s",
                    (member_id, stokvel_id)
                )
                conn.commit()
        flash("Member removed successfully.", "success")
    except Exception as e:
        flash(f"Failed to remove member: {e}", "danger")
    return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))

@app.route('/referral', methods=['GET', 'POST'])
@login_required
def referral():
    if request.method == 'POST':
        email = request.form.get('email')
        inviter_name = request.form.get('inviter_name')
        stokvel_name = request.form.get('stokvel_name')
        if email and inviter_name and stokvel_name:
            try:
                msg = Message(
                    subject=f"You've been invited to join {stokvel_name}!",
                    recipients=[email],
                    body=f"Hi! {inviter_name} has invited you to join {stokvel_name}. Click here to register: https://your-app-url/register"
                )
                mail.send(msg)
                flash(f'Referral email sent to {email}!', 'success')
            except Exception as e:
                print(f"Error sending email: {e}")
                flash('Failed to send referral email. Please try again later.', 'danger')
        else:
            flash('Please enter all required fields.', 'danger')
        return redirect(url_for('referral'))
    return render_template('referral.html')

@app.context_processor
def inject_global():
    return dict(csrf_token=generate_csrf)

@app.route('/test_csrf')
def test_csrf():
    return render_template('test_csrf.html')

@app.route('/pay_back_loan', methods=['GET', 'POST'])
@login_required
def pay_back_loan():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to access loan repayment.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        loan_id = request.form.get('loan_id')
        repayment_amount = request.form.get('repayment_amount')
        payment_method_id = request.form.get('payment_method_id')
        
        if not all([loan_id, repayment_amount, payment_method_id]):
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('pay_back_loan'))
        
        try:
            with support.db_connection() as conn:
                with conn.cursor() as cur:
                    # Get loan details
                    cur.execute("""
                        SELECT t.amount, t.description, t.stokvel_id, s.name as stokvel_name
                        FROM transactions t
                        LEFT JOIN stokvels s ON t.stokvel_id = s.id
                        WHERE t.id = %s AND t.user_id = %s AND t.type = 'payout' AND t.status = 'approved'
                    """, (loan_id, user_id))
                    loan = cur.fetchone()
                    
                    if not loan:
                        flash('Loan not found or not eligible for repayment.', 'danger')
                        return redirect(url_for('pay_back_loan'))
                    
                    loan_amount, loan_description, stokvel_id, stokvel_name = loan
                    repayment_amount = float(repayment_amount)
                    
                    if repayment_amount <= 0:
                        flash('Repayment amount must be greater than 0.', 'danger')
                        return redirect(url_for('pay_back_loan'))
                    
                    # Record the repayment transaction
                    cur.execute("""
                        INSERT INTO transactions (user_id, stokvel_id, amount, type, description, transaction_date, status)
                        VALUES (%s, %s, %s, 'loan_repayment', %s, NOW(), 'completed')
                    """, (user_id, stokvel_id, repayment_amount, f"Loan repayment for: {loan_description}"))
                    
                    # Update the original loan with repayment info
                    cur.execute("""
                        UPDATE transactions 
                        SET description = CONCAT(description, ' | Repayment: R', %s, ' on ', NOW()::date)
                        WHERE id = %s
                    """, (repayment_amount, loan_id))
                    
                    conn.commit()
                    
                    flash(f'Loan repayment of R{repayment_amount:.2f} recorded successfully!', 'success')
                    return redirect(url_for('pay_back_loan'))
                    
        except Exception as e:
            print(f"Error processing loan repayment: {e}")
            flash('Failed to process loan repayment. Please try again.', 'danger')
            return redirect(url_for('pay_back_loan'))
    
    # GET request - show loan repayment form
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Get user's approved loans
                cur.execute("""
                    SELECT t.id, t.amount, t.description, t.transaction_date, s.name as stokvel_name
                    FROM transactions t
                    LEFT JOIN stokvels s ON t.stokvel_id = s.id
                    WHERE t.user_id = %s AND t.type = 'payout' AND t.status = 'approved'
                    ORDER BY t.transaction_date DESC
                """, (user_id,))
                loans = cur.fetchall()
                
                # Get user's payment methods
                cur.execute("""
                    SELECT id, type, details, is_default
                    FROM payment_methods
                    WHERE user_id = %s
                    ORDER BY is_default DESC, id ASC
                """, (user_id,))
                payment_methods_raw = cur.fetchall()
                import json
                payment_methods = []
                for pm in payment_methods_raw:
                    details = pm[2]
                    try:
                        details_dict = json.loads(details) if details else {}
                    except Exception:
                        details_dict = {}
                    payment_methods.append({
                        'id': pm[0],
                        'type': pm[1],
                        'details': details_dict,
                        'is_default': pm[3],
                    })
                
    except Exception as e:
        print(f"Error fetching loan data: {e}")
        loans = []
        payment_methods = []
        flash('Failed to load loan data.', 'danger')
    
    return render_template('pay_back_loan.html', loans=loans, payment_methods=payment_methods)

@app.route('/request_loan', methods=['GET', 'POST'])
@login_required
def request_loan():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to request a loan.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        stokvel_id = request.form.get('stokvel_id')
        amount = request.form.get('amount')
        description = request.form.get('description')
        
        if not all([stokvel_id, amount, description]):
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('request_loan'))
        
        try:
            amount = float(amount)
            stokvel_id = int(stokvel_id)
            
            if amount <= 0:
                flash('Loan amount must be greater than 0.', 'danger')
                return redirect(url_for('request_loan'))
            
            with support.db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if the user is a member of this stokvel
                    cur.execute("""
                        SELECT 1 FROM stokvel_members
                        WHERE stokvel_id = %s AND user_id = %s
                    """, (stokvel_id, user_id))
                    if not cur.fetchone():
                        flash('You are not a member of this stokvel.', 'danger')
                        return redirect(url_for('request_loan'))
                    
                    # Check if user already has a pending loan from this stokvel
                    cur.execute("""
                        SELECT 1 FROM transactions
                        WHERE user_id = %s AND stokvel_id = %s AND type = 'payout' AND status = 'pending'
                    """, (user_id, stokvel_id))
                    if cur.fetchone():
                        flash('You already have a pending loan request from this stokvel.', 'danger')
                        return redirect(url_for('request_loan'))
                    
                    # Insert loan request
                    cur.execute("""
                        INSERT INTO transactions (user_id, stokvel_id, amount, type, description, transaction_date, status)
                        VALUES (%s, %s, %s, 'payout', %s, NOW(), 'pending')
                    """, (user_id, stokvel_id, amount, f"Loan request: {description}"))
                    
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
                        cur.execute("SELECT username FROM users WHERE firebase_uid = %s", (user_id,))
                        user_info = cur.fetchone()
                        user_name = user_info[0] if user_info else "A member"
                        
                        # Create notification for stokvel admin
                        message = f"{user_name} requested a loan of R{amount:.2f} from '{stokvel_name}' stokvel."
                        link = url_for('admin.loan_approvals')
                        create_notification(
                            admin_user_id,
                            message,
                            link_url=link,
                            notification_type='loan_requested')
                    
                    conn.commit()
                    flash(f'Loan request of R{amount:.2f} submitted successfully! It will be reviewed by the stokvel admin.', 'success')
                    return redirect(url_for('request_loan'))
                    
        except ValueError:
            flash('Amount must be a valid number.', 'danger')
            return redirect(url_for('request_loan'))
        except Exception as e:
            print(f"Error requesting loan: {e}")
            flash('Failed to submit loan request. Please try again.', 'danger')
            return redirect(url_for('request_loan'))
    
    # GET request - show loan request form
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Get stokvels the user is a member of
                cur.execute("""
                    SELECT s.id, s.name, s.target_amount, s.monthly_contribution, s.target_date
                    FROM stokvels s
                    JOIN stokvel_members sm ON s.id = sm.stokvel_id
                    WHERE sm.user_id = %s
                    ORDER BY s.name ASC
                """, (user_id,))
                stokvel_options = cur.fetchall()
                
                # Get user's existing loan requests
                cur.execute("""
                    SELECT t.id, t.amount, t.description, t.transaction_date, t.status, s.name as stokvel_name
                    FROM transactions t
                    LEFT JOIN stokvels s ON t.stokvel_id = s.id
                    WHERE t.user_id = %s AND t.type = 'payout'
                    ORDER BY t.transaction_date DESC
                """, (user_id,))
                loan_requests = cur.fetchall()
                
    except Exception as e:
        print(f"Error fetching loan data: {e}")
        stokvel_options = []
        loan_requests = []
        flash('Failed to load loan data.', 'danger')
    
    return render_template('request_loan.html', stokvel_options=stokvel_options, loan_requests=loan_requests)

# ... existing code ...
    return render_template('referral.html', referral_link=referral_link, message=message, stokvels=stokvels, selected_stokvel_id=selected_stokvel_id)

if __name__ == "__main__":
    # Use 127.0.0.1 which is accessible in the browser
    socketio.run(app, host="127.0.0.1", port=5001, debug=True)

# Inject _ into Jinja2 context for translations
try:
    from flask_babel import _
except ImportError:
    def _(s): return s

@app.route('/dashboard')
@login_required
def dashboard():
    firebase_uid = session.get('user_id')
    user = {
        'username': session.get('username', 'User'),
        'profile_picture': session.get('profile_picture'),
        'email': session.get('email'),
    }
    active_stokvels_count = 0
    total_contributions = 0
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Count active stokvels for this user
                cur.execute("""
                    SELECT COUNT(DISTINCT s.id)
                    FROM stokvels s
                    JOIN stokvel_members sm ON s.id = sm.stokvel_id
                    WHERE sm.user_id = %s
                """, (firebase_uid,))
                active_stokvels_count = cur.fetchone()[0] or 0

                # Sum total contributions for this user
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0)
                    FROM transactions
                    WHERE user_id = %s AND type = 'contribution' AND status = 'completed'
                """, (firebase_uid,))
                total_contributions = cur.fetchone()[0] or 0
    except Exception as e:
        print(f"Dashboard error: {e}")
        active_stokvels_count = 0
        total_contributions = 0
    return render_template('dashboard.html', user=user, active_stokvels_count=active_stokvels_count, total_contributions=total_contributions)

@app.route('/api/recent_activity')
@login_required
def recent_activity_api():
    firebase_uid = session.get('user_id')
    activities = []
    try:
        with support.db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Fetch recent transactions
                cur.execute("""
                    SELECT 'transaction' as activity_type, type, amount, transaction_date as date
                    FROM transactions
                    WHERE user_id = %s AND status = 'completed'
                    ORDER BY transaction_date DESC
                    LIMIT 5
                """, (firebase_uid,))
                transactions = cur.fetchall()
                for t in transactions:
                    activities.append({
                        'type': t['type'],
                        'title': t['type'].replace('_', ' ').title(),
                        'amount': float(t['amount']),
                        'date': t['date'].isoformat(),
                        'status': 'Completed'
                    })

                # Fetch recent savings goals reached
                cur.execute("""
                    SELECT 'goal' as activity_type, name, target_amount as amount, created_at as date
                    FROM savings_goals
                    WHERE user_id = %s AND status = 'completed'
                    ORDER BY created_at DESC
                    LIMIT 2
                """, (firebase_uid,))
                goals = cur.fetchall()
                for g in goals:
                    activities.append({
                        'type': 'goal',
                        'title': g['name'],
                        'amount': float(g['amount']),
                        'date': g['date'].isoformat(),
                        'status': 'Achieved'
                    })
        activities.sort(key=lambda x: x['date'], reverse=True)
        # If no activities, return dummy data for debugging
        if not activities:
            from datetime import datetime, timedelta
            now = datetime.now()
            activities = [
                {'type': 'contribution', 'title': 'Monthly Contribution', 'amount': 1500.00, 'date': (now-timedelta(hours=2)).isoformat(), 'status': 'Processed'},
                {'type': 'goal', 'title': 'Savings Goal Reached', 'amount': 10000.00, 'date': (now-timedelta(days=1)).isoformat(), 'status': 'Achieved'},
                {'type': 'withdrawal', 'title': 'Emergency Withdrawal', 'amount': 500.00, 'date': (now-timedelta(days=3)).isoformat(), 'status': 'Completed'}
            ]
        return jsonify(activities[:7])
    except Exception as e:
        print(f"ERROR fetching recent activity: {e}")
        return jsonify({"error": "Could not fetch recent activity"}), 500

