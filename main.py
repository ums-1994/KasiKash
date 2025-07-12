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
from wtforms.validators import DataRequired, Email, Length, ValidationError
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
from utils import login_required, get_notification_count, create_notification
from financial_advisor import advisor_bp

# Email handling imports
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename
import re
import calendar
from decimal import Decimal, InvalidOperation
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
                flash('Please verify your email to access this feature. Check your inbox for a verification link.')
                return redirect('/home')
        except Exception as e:
            print(f"Email verification check error: {e}")
            flash('Could not verify email status. Please try again or contact support.')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# Helper function to get notification count (simulate for now)
# This function is now imported from utils.py

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
        # Parse month parameter with validation
        month_param = request.args.get('month')
        if month_param:
            try:
                month_start = datetime.strptime(month_param, '%Y-%m').date()
            except ValueError:
                logger.warning(f"Invalid month parameter: {month_param}")
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
        user = None
        outstanding_loan_id = None
        # Initialize new variables for enhanced profile card
        user_stokvels = []
        active_stokvels_count = 0
        
        try:
            with support.db_connection() as conn:
                with conn.cursor() as cur:
                    # Validate user_id before using in query
                    user_id = session.get('user_id')
                    if not user_id:
                        raise ValueError("User ID not found in session")
                    
                    cur.execute("SELECT username, email, profile_picture, joined_date FROM users WHERE firebase_uid = %s", (user_id,))
                    user_row = cur.fetchone()
                    if user_row:
                        username = str(user_row[0])
                        user = {
                            'username': user_row[0],
                            'email': user_row[1],
                            'profile_picture': user_row[2],
                            'joined_date': user_row[3]
                        }
                    
                    # Fetch user's stokvel memberships for the profile card
                    cur.execute("""
                        SELECT s.id, s.name, sm.role, 
                               COALESCE(SUM(t.amount), 0) as total_contributed,
                               s.monthly_contribution as target_amount,
                               (SELECT COUNT(*) FROM stokvel_members sm2 WHERE sm2.stokvel_id = s.id) as member_count
                        FROM stokvel_members sm
                        JOIN stokvels s ON sm.stokvel_id = s.id
                        LEFT JOIN transactions t ON t.stokvel_id = s.id AND t.user_id = %s AND t.type = 'contribution'
                        WHERE sm.user_id = %s AND sm.status = 'active'
                        GROUP BY s.id, s.name, sm.role, s.monthly_contribution
                        ORDER BY s.created_at DESC
                    """, (user_id, user_id))
                    
                    user_stokvels = []
                    active_stokvels_count = 0
                    total_contributions = 0
                    
                    for stokvel_row in cur.fetchall():
                        stokvel_id, stokvel_name, role, contributed, target, member_count = stokvel_row
                        active_stokvels_count += 1
                        total_contributions += contributed
                        
                        # Calculate progress percentage
                        progress = 0
                        if target and target > 0:
                            progress = min((contributed / target) * 100, 100)
                        
                        user_stokvels.append({
                            'id': stokvel_id,
                            'name': stokvel_name,
                            'role': role,
                            'contributed': contributed,
                            'target': target,
                            'progress': progress,
                            'member_count': member_count
                        })
                    print('DEBUG user_stokvels:', user_stokvels)
                    
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
                    """, (user_id,))
                    loan_row = cur.fetchone()
                    if loan_row:
                        outstanding_loan_id = loan_row[0]
                    
                    # --- Calendar Events Integration ---
                    # Contributions
                    cur.execute("""
                        SELECT transaction_date, amount FROM transactions
                        WHERE user_id = %s AND type = 'contribution' AND transaction_date >= %s AND transaction_date < %s
                    """, (user_id, month_start, next_month))
                    for tdate, amount in cur.fetchall():
                        calendar_events.append({'date': tdate.strftime('%Y-%m-%d'), 'desc': f'Contribution: R{amount:.2f}', 'type': 'contribution'})
                    
                    # Payouts
                    cur.execute("""
                        SELECT transaction_date, amount FROM transactions
                        WHERE user_id = %s AND type = 'payout' AND transaction_date >= %s AND transaction_date < %s
                    """, (user_id, month_start, next_month))
                    for tdate, amount in cur.fetchall():
                        calendar_events.append({'date': tdate.strftime('%Y-%m-%d'), 'desc': f'Payout: R{amount:.2f}', 'type': 'payout'})
                    
                    # Savings goal deadlines
                    cur.execute("""
                        SELECT target_date, name FROM savings_goals
                        WHERE user_id = %s AND target_date >= %s AND target_date < %s
                    """, (user_id, month_start, next_month))
                    for tdate, name in cur.fetchall():
                        if tdate:
                            calendar_events.append({'date': tdate.strftime('%Y-%m-%d'), 'desc': f'Savings Goal: {name}', 'type': 'goal'})
                    
                    # Loan repayments
                    cur.execute("""
                        SELECT date, amount FROM loan_repayments
                        WHERE user_id = %s AND date >= %s AND date < %s
                    """, (user_id, month_start, next_month))
                    for tdate, amount in cur.fetchall():
                        calendar_events.append({'date': tdate.strftime('%Y-%m-%d'), 'desc': f'Loan Repayment: R{amount:.2f}', 'type': 'repayment'})
                    
                    # Custom user events (future support)
                    try:
                        cur.execute("""
                            SELECT event_date, description FROM user_events
                            WHERE user_id = %s AND event_date >= %s AND event_date < %s
                        """, (user_id, month_start, next_month))
                        for tdate, desc in cur.fetchall():
                            calendar_events.append({'date': tdate.strftime('%Y-%m-%d'), 'desc': desc, 'type': 'custom'})
                    except Exception as table_error:
                        logger.debug(f"User events table may not exist: {table_error}")
                        pass  # Table may not exist yet
                        
        except Exception as db_error:
            logger.error(f"Database error in home route: {str(db_error)}")
            # Continue with default values if database query fails
            flash("Some data could not be loaded. Please refresh the page.")
        
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
                            calendar_month=calendar_month,
                            calendar_year=calendar_year,
                            calendar_month_num=month_start.month,
                            prev_month_url=prev_month_url,
                            next_month_url=next_month_url,
                            calendar_days=calendar_days,
                            # New data for enhanced profile card
                            user_stokvels=user_stokvels,
                            active_stokvels_count=active_stokvels_count) # Pass notification count
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        flash("Error loading dashboard. Please try again.")
        return redirect('/login')


@app.route('/analysis')
@login_required
def analysis():
    if 'user_id' in session:
        user_id = session.get('user_id')
        
        # Get user data
        query = "SELECT username FROM users WHERE firebase_uid = %s"
        userdata = support.execute_query('search', query, (user_id,))
        if not userdata or userdata[0] is None:
            flash('User data not found for analysis.')
            return redirect('/home')
        
        # Get transaction data for analysis
        query2 = """
            SELECT transaction_date, type, description, amount 
            FROM transactions 
            WHERE user_id = %s
            ORDER BY transaction_date DESC
        """
        data = support.execute_query('search', query2, (user_id,))
        
        if data and len(data) > 0:
            # Convert to DataFrame for analysis
            df = pd.DataFrame(data, columns=['Date', 'Type', 'Description', 'Amount'])
            
            # Clean and process the data
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.dropna(subset=['Date'])
            
            # Add derived columns for analysis
            df['Month'] = df['Date'].dt.month
            df['Year'] = df['Date'].dt.year
            df['Day'] = df['Date'].dt.day
            df['Day_name'] = df['Date'].dt.day_name()
            df['Month_name'] = df['Date'].dt.month_name()
            
            # Generate charts using support functions if available
            try:
                # Pie chart by transaction type
                type_summary = df.groupby('Type')['Amount'].sum().reset_index()
                pie = support.meraPie(df=type_summary, names='Type', values='Amount', hole=0.7, 
                                    hole_text='Transactions', hole_font=20, height=180, width=180, 
                                    margin=dict(t=1, b=1, l=1, r=1))
                
                # Bar chart by description
                desc_summary = df.groupby(['Description', 'Type'])['Amount'].sum().reset_index()
                bar = support.meraBarChart(df=desc_summary, x='Description', y='Amount', color="Type", 
                                         height=180, x_label="Category", show_xtick=False)
                
                # Line chart over time
                time_summary = df.groupby('Date')['Amount'].sum().reset_index()
                line = support.meraLine(df=time_summary, x='Date', y='Amount', color='Type', 
                                      slider=False, show_legend=False, height=180)
                
                # Scatter plot
                scatter = support.meraScatter(df, 'Date', 'Amount', 'Type', 'Amount', slider=False)
                
                # Heatmap by day vs month
                heat = support.meraHeatmap(df, 'Day_name', 'Month_name', height=200, 
                                         title="Transaction count Day vs Month")
                
                # Monthly bar chart
                month_bar = support.month_bar(df, 280)
                
                # Sunburst chart
                sun = support.meraSunburst(df, 280)
                
            except Exception as e:
                print(f"Error generating charts: {e}")
                # Fallback to simple charts or empty data
                pie = None
                bar = None
                line = None
                scatter = None
                heat = None
                month_bar = None
                sun = None
            
            return render_template('analysis.html',
                                   username=userdata[0][0],
                                   pie=pie,
                                   bar=bar,
                                   line=line,
                                   scatter=scatter,
                                   heat=heat,
                                   month_bar=month_bar,
                                   sun=sun)
        else:
            return render_template('analysis.html',
                                   username=userdata[0][0],
                                   pie=None,
                                   bar=None,
                                   line=None,
                                   scatter=None,
                                   heat=None,
                                   month_bar=None,
                                   sun=None)
    else:
        return redirect('/login')


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
            email = form.email.data.strip().lower()  # Normalize email
            password = form.password.data
            remember = form.remember.data

            logger.info(f"Login attempt for email: {email}")

            # Validate input
            if not email or not password:
                flash('Email and password are required.')
                return redirect('/login')

            # Try to get user by email first
            try:
                logger.info("Attempting to get user from Firebase...")
                user_record = auth.get_user_by_email(email)
                logger.info(f"User found: {user_record.uid}")

                # Verify email verification status
                if not user_record.email_verified:
                    logger.warning("User email not verified")
                    flash("Please verify your email address before logging in.")
                    return redirect('/login')

                # Clear any existing session data
                session.clear()
                session['user_id'] = str(user_record.uid)
                session['username'] = str(user_record.display_name or email)
                session['is_verified'] = bool(user_record.email_verified)
                session.permanent = bool(remember)

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
                    logger.error(f"Error fetching user role: {role_e}")
                    session['role'] = 'user'

                # Update last_login in the database
                try:
                    from datetime import datetime
                    support.execute_query("update", "UPDATE users SET last_login = %s, email = %s WHERE firebase_uid = %s", 
                                         (datetime.utcnow(), user_record.email, user_record.uid))
                except Exception as update_e:
                    logger.error(f"Error updating last_login: {update_e}")
                    # Non-critical error, continue with login

                logger.info("Login successful, redirecting to home")
                flash("Login successful!")
                return redirect('/home')

            except auth.UserNotFoundError as e:
                logger.warning(f"User not found error: {str(e)}")
                flash('Invalid email or password')
                return redirect('/login')
            except auth.InvalidPasswordError as e:
                logger.warning(f"Invalid password error: {str(e)}")
                flash('Invalid email or password')
                return redirect('/login')
            except Exception as e:
                logger.error(f"Firebase auth error: {str(e)}")
                flash('An error occurred during login. Please try again.')
                return redirect('/login')

        except Exception as e:
            logger.error(f"Login validation (outer) error: {str(e)}")
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
def registration():
    if 'user_id' in session:
        flash("Already a user is logged-in!", "warning")
        return redirect('/home')
    try:
        # Get and validate form data
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        passwd = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        id_number = request.form.get('id_number', '').strip()
        address = request.form.get('address', '').strip()
        date_of_birth = request.form.get('date_of_birth')
        bio = request.form.get('bio', '').strip()

        logger.info(f"Registration attempt - Username: {username}, Email: {email}")

        # Enhanced validation with specific error messages
        validation_errors = []
        # Username validation
        if len(username) < 3:
            validation_errors.append("Username must be at least 3 characters long.")
        elif len(username) > 30:
            validation_errors.append("Username must be less than 30 characters.")
        elif not username.replace('_', '').replace('-', '').isalnum():
            validation_errors.append("Username can only contain letters, numbers, underscores, and hyphens.")
        # Email validation
        if len(email) < 5 or '@' not in email:
            validation_errors.append("Please enter a valid email address.")
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            validation_errors.append("Please enter a valid email address format.")
        # Password validation
        if len(passwd) < 6:
            validation_errors.append("Password must be at least 6 characters long.")
        elif len(passwd) > 128:
            validation_errors.append("Password must be less than 128 characters.")
        # Full name validation
        if len(full_name) < 2:
            validation_errors.append("Full name must be at least 2 characters long.")
        elif len(full_name) > 100:
            validation_errors.append("Full name must be less than 100 characters.")
        # Phone validation
        if not phone:
            validation_errors.append("Phone number is required.")
        elif not re.match(r'^[\+]?[0-9\s\-\(\)]{10,}$', phone):
            validation_errors.append("Please enter a valid phone number.")
        # ID number validation (South African ID format)
        if not id_number:
            validation_errors.append("ID number is required.")
        elif not re.match(r'^\d{13}$', id_number.replace(' ', '')):
            validation_errors.append("Please enter a valid 13-digit South African ID number.")
        # Address validation
        if len(address) < 10:
            validation_errors.append("Address must be at least 10 characters long.")
        elif len(address) > 500:
            validation_errors.append("Address must be less than 500 characters.")
        # Date of birth validation
        if not date_of_birth:
            validation_errors.append("Date of birth is required.")
        else:
            try:
                dob = datetime.strptime(date_of_birth, '%Y-%m-%d')
                age = (datetime.now() - dob).days / 365.25
                if age < 18:
                    validation_errors.append("You must be at least 18 years old to register.")
                elif age > 120:
                    validation_errors.append("Please enter a valid date of birth.")
            except ValueError:
                validation_errors.append("Please enter a valid date of birth.")
        # Bio validation (optional)
        if bio and len(bio) > 1000:
            validation_errors.append("Bio must be less than 1000 characters.")
        # If there are validation errors, return them
        if validation_errors:
            for error in validation_errors:
                flash(error, "danger")
            return redirect('/register')
        # Check if email already exists in PostgreSQL database
        try:
            with support.db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                    if cur.fetchone():
                        flash("An account with this email already exists. Please log in.", "warning")
                        return redirect('/login')
                    # Check if username already exists
                    cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                    if cur.fetchone():
                        flash("Username is already taken. Please choose a different username.", "warning")
                        return redirect('/register')
        except Exception as db_e:
            logger.error(f"Database check error during registration: {db_e}")
            flash("An error occurred during registration. Please try again.", "danger")
            return redirect('/register')
        # Create user in Firebase Authentication
        try:
            user = auth.create_user(
                email=email,
                password=passwd,
                display_name=username,
                email_verified=True  # Set to True since we're using email/password auth
            )
            logger.info(f"Created Firebase user: {user.uid}")
            # Store Firebase UID and user data in PostgreSQL database
            with support.db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO users (firebase_uid, username, email, password, full_name, phone, id_number, address, date_of_birth, bio, joined_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                        (user.uid, username, email, passwd, full_name, phone, id_number, address, date_of_birth, bio, datetime.utcnow())
                    )
                    local_user_id = cur.fetchone()[0]
                    # Create default user settings
                    cur.execute("""
                        INSERT INTO user_settings (user_id, email_notifications, sms_notifications, weekly_summary, 
                                                 receive_promotions, reminders_enabled, stokvel_updates, profile_visible, activity_sharing)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (user.uid, True, False, True, False, True, True, True, False))
                    conn.commit()
                    if local_user_id:
                        # Set session data
                        session['user_id'] = user.uid
                        session['username'] = username
                        session['is_verified'] = True
                        session.permanent = True
                        # Create welcome notification
                        welcome_message = f"Welcome to KasiKash, {username}! Your account has been created successfully."
                        create_notification(user.uid, welcome_message, notification_type='welcome')
                        flash("Registration successful! Welcome to KasiKash!", "success")
                        logger.info(f"User {username} registered successfully")
                        return redirect('/home')
                    else:
                        flash("Registration failed: Could not retrieve local user ID.", "danger")
                        auth.delete_user(user.uid)
                        return redirect('/register')
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            if "email-already-exists" in str(e):
                flash("Email address is already in use. Please use a different email or log in.", "warning")
            elif "password-too-weak" in str(e):
                flash("Password is too weak. Please choose a stronger password.", "warning")
            elif "invalid-email" in str(e):
                flash("Please enter a valid email address.", "warning")
            else:
                flash("An unexpected error occurred during registration. Please try again.", "danger")
            return redirect('/register')
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        flash("An error occurred during registration. Please try again.", "danger")
        return redirect('/register')


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
                        (SELECT COUNT(*) FROM stokvel_members sm2 WHERE sm2.stokvel_id = s.id) as member_count,
                        (SELECT SUM(t.amount) FROM transactions t WHERE t.stokvel_id = s.id) as total_contributions,
                        s.target_date,
                        sm.role
                    FROM stokvels s
                    JOIN stokvel_members sm ON s.id = sm.stokvel_id
                    WHERE sm.user_id = %s
                """, (firebase_uid,))
                user_stokvels = [dict(zip([desc[0] for desc in cur.description], row)) for row in cur.fetchall()]

        return render_template('stokvels.html', stokvels=user_stokvels, created_stokvels=[])
    except Exception as e:
        flash(f"An error occurred while loading your stokvels: {e}")
        print(f"Stokvels page error: {e}")
        return render_template('stokvels.html', stokvels=[])

@app.route('/create_stokvel', methods=['POST'])
@login_required
def create_stokvel():
    user_id = session['user_id']
    name = request.form['name']
    description = request.form['description']
    monthly_contribution = request.form['monthly_contribution']
    target_amount = request.form.get('target_amount', 0)
    target_date = request.form.get('target_date')
    
    # Insert new stokvel and get its ID
    query = "INSERT INTO stokvels (name, description, created_by, monthly_contribution, target_amount, target_date) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id"
    result = support.execute_query("insert", query, (name, description, user_id, monthly_contribution, target_amount, target_date))

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

                # Fetch default payment method for display
                cur.execute("SELECT type, details FROM payment_methods WHERE user_id = %s AND is_default = TRUE", (firebase_uid,))
                payment_method = cur.fetchone()
                payment_info_text = "No default payment method set. Please add one in settings."
                if payment_method:
                    method_type, details = payment_method
                    if isinstance(details, str):
                        try:
                            details = json.loads(details)
                        except json.JSONDecodeError:
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
        return render_template('contributions.html', contributions=contributions_list, stokvels=stokvels_list, payment_info=payment_info_text)
    except Exception as e:
        print(f"Error in contributions route: {e}")
        flash("An error occurred while loading your contributions.")
        return render_template('contributions.html', contributions=[], stokvels=[], payment_info="Could not load payment info.")

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

                    # Get default payment method for flash message
                    cur.execute("SELECT type, details FROM payment_methods WHERE user_id = %s AND is_default = TRUE", (firebase_uid,))
                    payment_method = cur.fetchone()
                    payment_info = ""
                    if payment_method:
                        method_type, details = payment_method
                        if isinstance(details, str):
                            details = json.loads(details)
                        if method_type in ['credit_card', 'debit_card', 'card']:
                            last4 = details.get('card_number', '')[-4:]
                            payment_info = f" from your card ending in {last4}"
                        elif method_type == 'bank_account':
                            payment_info = f" from your {details.get('bank_name', 'bank')} account"
                        
            flash(f"Contribution of R{amount:.2f} recorded successfully{payment_info}!")
            return redirect(url_for('contributions'))
        except ValueError:
            flash("Amount must be a number.")
            return redirect(url_for('contributions'))
        except Exception as e:
            print(f"Error making contribution: {e}")
            flash("An error occurred while recording your contribution. Please try again.")
            return redirect(url_for('contributions'))
    # For GET requests, just show the contributions page with the modal
    return redirect(url_for('contributions'))

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

                    # Create notification for stokvel admin
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

                # Get default payment method for flash message
                cur.execute("SELECT type, details FROM payment_methods WHERE user_id = %s AND is_default = TRUE", (firebase_uid,))
                payment_method = cur.fetchone()
                payment_info = ""
                if payment_method:
                    method_type, details = payment_method
                    if isinstance(details, str):
                        details = json.loads(details)
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
                    SELECT NULL as username, sm.email, sm.role, sm.id as member_id
                    FROM stokvel_members sm
                    WHERE sm.stokvel_id = %s AND sm.user_id IS NULL AND sm.email IS NOT NULL
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
                payment_method_keys = ['id', 'type', 'details', 'is_default', 'created_at']
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
                        if pm_dict['type'] in ['credit_card', 'debit_card', 'card']:
                            card_number = details_json.get('card_number', '')
                            last4 = card_number[-4:] if len(card_number) >= 4 else card_number
                            masked_number = '**** **** **** ' + last4
                            exp = details_json.get('expiry_date', '')
                            card_holder = details_json.get('card_holder_name', 'N/A')
                            masked_details = f"{masked_number}  Exp: {exp}"
                            pm_dict['card_holder_name'] = card_holder
                        elif pm_dict['type'] == 'bank_account':
                            acc = details_json.get('account_number', '')
                            last4 = acc[-4:] if len(acc) >= 4 else acc
                            bank = details_json.get('bank_name', '')
                            account_holder = details_json.get('account_holder_name', 'N/A')
                            masked_details = f"Account: ****{last4}  ({bank})"
                            pm_dict['account_holder_name'] = account_holder
                        elif pm_dict['type'] == 'mobile_money':
                            phone = details_json.get('phone', '')
                            last4 = phone[-4:] if len(phone) >= 4 else phone
                            provider = details_json.get('provider', '')
                            masked_details = f"Mobile: ****{last4}  {provider}"
                        else:
                            # fallback: show only non-sensitive fields
                            masked_details = ', '.join(f"{k}: {v}" for k, v in details_json.items() if 'number' not in k and 'card' not in k)
                    except Exception as e:
                        masked_details = 'Payment details unavailable'
                    pm_dict['masked_details'] = masked_details
                    payment_methods_list.append(pm_dict)
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
    is_default = request.form.get('is_default') == 'true'
    details_dict = {}
    import json

    if payment_type in ['credit_card', 'debit_card']:
        card_holder_name = request.form.get('card_holder_name')
        card_number = request.form.get('card_number')
        expiry_date = request.form.get('expiry_date')
        cvv = request.form.get('cvv') # Note: Storing CVV is not PCI compliant. This is for demonstration.
        if not all([card_holder_name, card_number, expiry_date, cvv]):
            flash("All card fields are required.", "danger")
            return redirect(url_for('payment_methods'))
        details_dict = {
            "card_holder_name": card_holder_name,
            "card_number": card_number,
            "expiry_date": expiry_date,
            # "cvv": cvv  # Do not persist CVV
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
                    cur.execute("UPDATE payment_methods SET is_default = FALSE WHERE user_id = %s", (user_id,))
                
                cur.execute("""
                    INSERT INTO payment_methods (user_id, type, details, is_default)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, payment_type, details_json, is_default))
                conn.commit()

        flash("Payment method added successfully!", "success")
        return redirect(url_for('payment_methods'))
    except Exception as e:
        print(f"Error adding payment method: {e}")
        flash("An error occurred while adding the payment method. Please try again.", "danger")
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
                    SELECT email_notifications, sms_notifications, weekly_summary, receive_promotions,
                           reminders_enabled, stokvel_updates, profile_visible, activity_sharing
                    FROM user_settings
                    WHERE user_id = %s
                """, (user_id,))
                app_settings = cur.fetchone() or {}
                
                # Merge settings with defaults for missing values
                user_settings.update(app_settings)
                
                # Set default values for missing settings
                defaults = {
                    'email_notifications': False,
                    'sms_notifications': False,
                    'weekly_summary': False,
                    'receive_promotions': False,
                    'reminders_enabled': True,
                    'stokvel_updates': True,
                    'profile_visible': True,
                    'activity_sharing': False,
                    'two_factor_enabled': False,
                    'language_preference': 'en'
                }
                
                for key, default_value in defaults.items():
                    if key not in user_settings or user_settings[key] is None:
                        user_settings[key] = default_value
        
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

    try:
        if form_section == 'language_preference':
            language = request.form.get('language_preference')
            if language:
                session['language_preference'] = language
                support.execute_query("update", "UPDATE users SET language_preference = %s WHERE firebase_uid = %s", (language, user_id))
                flash("Language preference updated successfully!", "success")

        elif form_section == 'app_preferences':
            # Get all notification preferences
            email_notifications = 'email_notifications' in request.form
            sms_notifications = 'sms_notifications' in request.form
            weekly_summary = 'weekly_summary' in request.form
            receive_promotions = 'receive_promotions' in request.form
            reminders_enabled = 'reminders_enabled' in request.form
            stokvel_updates = 'stokvel_updates' in request.form
            # First, ensure user_settings record exists
            with support.db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO user_settings (user_id, email_notifications, sms_notifications, weekly_summary, 
                                                 receive_promotions, reminders_enabled, stokvel_updates)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (user_id) DO UPDATE SET
                            email_notifications = EXCLUDED.email_notifications,
                            sms_notifications = EXCLUDED.sms_notifications,
                            weekly_summary = EXCLUDED.weekly_summary,
                            receive_promotions = EXCLUDED.receive_promotions,
                            reminders_enabled = EXCLUDED.reminders_enabled,
                            stokvel_updates = EXCLUDED.stokvel_updates
                    """, (user_id, email_notifications, sms_notifications, weekly_summary, 
                         receive_promotions, reminders_enabled, stokvel_updates))
                    conn.commit()
            flash("App preferences updated successfully!", "success")

        elif form_section == 'privacy':
            profile_visible = 'profile_visible' in request.form
            activity_sharing = 'activity_sharing' in request.form
            with support.db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO user_settings (user_id, profile_visible, activity_sharing)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (user_id) DO UPDATE SET
                            profile_visible = EXCLUDED.profile_visible,
                            activity_sharing = EXCLUDED.activity_sharing
                    """, (user_id, profile_visible, activity_sharing))
                    conn.commit()
            flash("Privacy settings updated successfully!", "success")

        elif form_section == 'security':
            two_factor_enabled = 'two_factor_enabled' in request.form
            support.execute_query("update", "UPDATE users SET two_factor_enabled = %s WHERE firebase_uid = %s", (two_factor_enabled, user_id))
            flash("Security settings updated successfully!", "success")
        else:
            flash("Invalid settings update request.", "warning")
    except Exception as e:
        print(f"Error updating settings for section {form_section}: {e}")
        flash("An error occurred while updating settings.", "danger")
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
                    SELECT 
                           COUNT(DISTINCT s.id) as active_stokvels_count,
                           COALESCE(SUM(CASE WHEN t.type = 'contribution' THEN t.amount ELSE 0 END), 0) as total_contributions,
                        COALESCE(SUM(CASE WHEN t.type = 'payout' THEN t.amount ELSE 0 END), 0) as total_withdrawals
                    FROM users u
                    LEFT JOIN stokvel_members sm ON u.firebase_uid = sm.user_id
                    LEFT JOIN stokvels s ON sm.stokvel_id = s.id
                    LEFT JOIN transactions t ON u.firebase_uid = t.user_id
                    WHERE u.firebase_uid = %s
                    GROUP BY u.firebase_uid
                """, (session['user_id'],))
                stats = cur.fetchone()

                if stats:
                    user.update(stats)
                else:
                    user['active_stokvels_count'] = 0
                    user['total_contributions'] = 0
                    user['total_withdrawals'] = 0
                
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
                                     active_stokvels_count=user.get('active_stokvels_count', 0),
                                     total_contributions=user.get('total_contributions', 0),
                                     total_withdrawals=user.get('total_withdrawals', 0))
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

    try:
        id_filename = secure_filename(f"{user_id}_id_{id_doc.filename}")
        address_filename = secure_filename(f"{user_id}_address_{address_doc.filename}")

        id_filepath = os.path.join(app.config['KYC_UPLOAD_FOLDER'], id_filename)
        address_filepath = os.path.join(app.config['KYC_UPLOAD_FOLDER'], address_filename)

        id_doc.save(id_filepath)
        address_doc.save(address_filepath)

        # Update user's KYC info in the database and set status to 'pending'
        query = "UPDATE users SET id_document = %s, proof_of_address = %s, kyc_status = 'pending' WHERE firebase_uid = %s"
        support.execute_query("update", query, (id_filename, address_filename, user_id))

        flash('KYC documents uploaded successfully. They are now pending review.', 'success')
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
        user_data = support.execute_query("search", user_query, (session['user_id'],))
        if user_data:
            username = user_data[0][0]
        
        # Get notification count
        notification_count = get_notification_count(session['user_id'])
        
        # Get user's language preference from session first, then try database
        if 'language_preference' in session:
            language_preference = session['language_preference']
        else:
            # Try to get from database, but fall back to session if column doesn't exist
            try:
                lang_query = "SELECT language_preference FROM users WHERE firebase_uid = %s"
                lang_data = support.execute_query("search", lang_query, (session['user_id'],))
                if lang_data and lang_data[0][0]:
                    language_preference = lang_data[0][0]
                    # Store in session for future use
                    session['language_preference'] = language_preference
            except Exception as e:
                print(f"Error getting language preference from database: {e}")
                # Use session default or fallback to English
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

# Add this dictionary to store temporary stokvel creation data
stokvel_creation_state = {}

def rule_based_chat(user_message, user_id, user_name):
    user_message_lower = user_message.lower()
    response = None

    # Get or initialize user's creation state
    creation_state = stokvel_creation_state.get(user_id, {})

    # Direct Stokvel Creation Flow
    if 'create stokvel' in user_message_lower or creation_state.get('creating_stokvel'):
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
                amount = float(user_message.replace('R', '').replace(',', '').strip())
                data['monthly_contribution'] = amount
                stokvel_creation_state[user_id]['step'] = 'target_amount'
                return "What's the target amount for this stokvel? (Enter 0 if no specific target)"

            except ValueError:
                return "Please enter a valid amount (e.g., 500 or R500)"

        elif current_step == 'target_amount':
            try:
                amount = float(user_message.replace('R', '').replace(',', '').strip())
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
                    data['target_date'] = datetime.strptime(user_message.strip(), '%Y-%m-%d')
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
                    link = url_for('view_stokvel_members', stokvel_id=stokvel_id)
                    create_notification(user_id, message, link_url=link, notification_type='stokvel_created')

                    # Clear the creation state
                    del stokvel_creation_state[user_id]

                    summary = f"""✅ Perfect! I've created your stokvel with these details:

Name: {data['name']}
Monthly Contribution: R{data['monthly_contribution']:.2f}
Target Amount: {'R{:.2f}'.format(data['target_amount']) if data.get('target_amount') else 'Not set'}
Target Date: {data['target_date'].strftime('%Y-%m-%d') if data.get('target_date') else 'Not set'}

To add members, say: add member email@example.com to '{data['name']}'"""
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
            result = support.execute_query("select", query, (stokvel_name, user_id))

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
            return jsonify({'response': 'Empty message received.', 'mode': mode}), 400

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
                    response = api_response.json()['choices'][0]['message']['content']
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
                    return jsonify({'response': response, 'mode': mode, 'timestamp': datetime.now().strftime('%H:%M')})
                else:
                    response = "Something went wrong. Please type 'cancel' to start over."
                return jsonify({'response': response, 'mode': mode, 'timestamp': datetime.now().strftime('%H:%M')})

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
                return jsonify({'response': response, 'mode': mode, 'timestamp': datetime.now().strftime('%H:%M')})

            # Start stokvel creation (move this above generic Q&A)
            if user_message_lower in [
                'create stokvel', 'i want to create a stokvel', 'start stokvel', 'open stokvel',
                'create a stokvel', 'new stokvel', 'add stokvel', 'begin stokvel creation'
            ]:
                session['chat_state'] = 'stokvel_creation'
                session['stokvel_data'] = {}
                return jsonify({'response': 'Great! What would you like to name your stokvel? (Type "cancel" to stop at any time)', 'mode': mode, 'timestamp': datetime.now().strftime('%H:%M')})

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
                return jsonify({'response': response, 'mode': mode, 'timestamp': datetime.now().strftime('%H:%M')})

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
                return jsonify({'response': response, 'mode': mode, 'timestamp': datetime.now().strftime('%H:%M')})

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
                        INSERT INTO chat_history (user_id, message, response)
                        VALUES (%s, %s, %s)
                    """, (user_id, user_message, response))
                    conn.commit()
        except Exception as e:
            print(f"Error saving chat history: {e}")

        # Return the response to the frontend
        return jsonify(response=response, mode=mode, timestamp=datetime.now().strftime('%H:%M'))

    except Exception as e:
        print(f"Chat handler error: {e}")
        return jsonify({'response': 'An unexpected error occurred. Please try again.', 'mode': 'error'}), 500

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

print("Registered endpoints:")
for rule in app.url_map.iter_rules():
    print(rule.endpoint, rule)

# ... after app = Flask(__name__) ...

from financial_advisor import advisor_bp
app.register_blueprint(advisor_bp)

# ... rest of the code ...

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf())

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
    stokvels = []
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
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

@app.route('/loan_requests')
@login_required
def loan_requests():
    user_id = session.get('user_id')
    loan_requests = []
    repayment_histories = {}
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT lr.id, s.name, lr.amount, lr.status, lr.reason, lr.created_at
                    FROM loan_requests lr
                    JOIN stokvels s ON lr.stokvel_id = s.id
                    WHERE lr.user_id = %s
                    ORDER BY lr.created_at DESC
                ''', (user_id,))
                for row in cur.fetchall():
                    loan_id, stokvel_name, amount, status, reason, created_at = row
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

@app.route('/financial_insight', methods=['GET', 'POST'])
@login_required
def financial_insight():
    user_id = session.get('user_id')
    if not user_id:
        flash("User not found in session, please log in again.", "error")
        return redirect('/login')

    # Get filter parameters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    contrib_type = request.args.get('type', '')

    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Build date filter
                date_filter = ""
                params = [user_id]
                if date_from:
                    date_filter += " AND t.transaction_date >= %s"
                    params.append(date_from)
                if date_to:
                    date_filter += " AND t.transaction_date <= %s"
                    params.append(date_to)
                if contrib_type:
                    date_filter += " AND t.type = %s"
                    params.append(contrib_type)

                # Get user's total contributions
                cur.execute(f"""
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM transactions 
                    WHERE user_id = %s AND type = 'contribution'{date_filter}
                """, params)
                total_contributions = cur.fetchone()[0] or 0

                # Get user's savings progress
                cur.execute("""
                    SELECT COALESCE(SUM(current_amount), 0), COALESCE(SUM(target_amount), 0)
                    FROM savings_goals 
                    WHERE user_id = %s
                """, (user_id,))
                current_saved, total_target = cur.fetchone()
                savings_progress = (current_saved / total_target) if total_target > 0 else 0

                # Calculate monthly average
                cur.execute(f"""
                    SELECT COALESCE(AVG(monthly_total), 0)
                    FROM (
                        SELECT DATE_TRUNC('month', transaction_date) as month,
                               SUM(amount) as monthly_total
                        FROM transactions 
                        WHERE user_id = %s AND type = 'contribution'{date_filter}
                        GROUP BY DATE_TRUNC('month', transaction_date)
                    ) monthly_data
                """, params)
                monthly_average = cur.fetchone()[0] or 0

                # Get loan statistics
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM loan_requests 
                    WHERE user_id = %s AND status = 'approved'
                """, (user_id,))
                total_loans_taken = cur.fetchone()[0] or 0

                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM loan_repayments 
                    WHERE user_id = %s
                """, (user_id,))
                total_loans_repaid = cur.fetchone()[0] or 0

                outstanding_loans = total_loans_taken - total_loans_repaid

                # Calculate financial health score (simplified)
                health_score = min(100, max(0, int(
                    (savings_progress * 40) +  # 40% from goal progress
                    (min(monthly_average / 1000, 1) * 30) +  # 30% from monthly average
                    (min(total_contributions / 5000, 1) * 30)  # 30% from total contributions
                )))

                # Get recent activity
                cur.execute(f"""
                    SELECT t.type, t.amount, t.transaction_date, s.name
                    FROM transactions t
                    LEFT JOIN stokvels s ON t.stokvel_id = s.id
                    WHERE t.user_id = %s{date_filter}
                    ORDER BY t.transaction_date DESC
                    LIMIT 10
                """, params)
                recent_activity = cur.fetchall()

                # Get savings goals
                cur.execute("""
                    SELECT name, current_amount, target_amount
                    FROM savings_goals 
                    WHERE user_id = %s
                    ORDER BY target_date ASC
                """, (user_id,))
                savings_goals = cur.fetchall()

                # Generate milestones and suggestions
                milestones = []
                suggestions = []
                
                if total_contributions >= 1000:
                    milestones.append("R1,000+ Total Contributions")
                if total_contributions >= 5000:
                    milestones.append("R5,000+ Total Contributions")
                if savings_progress >= 0.5:
                    milestones.append("50%+ Goal Progress")
                if monthly_average >= 500:
                    milestones.append("R500+ Monthly Average")

                if savings_progress < 0.3:
                    suggestions.append("Increase savings rate")
                if monthly_average < 300:
                    suggestions.append("Set up recurring contributions")
                if outstanding_loans > 0:
                    suggestions.append("Focus on loan repayment")

                # Goal forecast
                goal_forecast = None
                if savings_goals:
                    avg_monthly_needed = sum((goal[2] - goal[1]) for goal in savings_goals if goal[2] > goal[1]) / len(savings_goals)
                    if monthly_average > 0:
                        months_to_complete = avg_monthly_needed / monthly_average
                        goal_forecast = f"Complete goals in {months_to_complete:.1f} months"

                # Community data (simplified)
                cur.execute("SELECT COUNT(DISTINCT user_id) FROM transactions WHERE type = 'contribution'")
                active_members = cur.fetchone()[0] or 0

                cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'contribution'")
                community_total_contributions = cur.fetchone()[0] or 0

                cur.execute("SELECT COALESCE(AVG(monthly_total), 0) FROM (SELECT DATE_TRUNC('month', transaction_date) as month, SUM(amount) as monthly_total FROM transactions WHERE type = 'contribution' GROUP BY DATE_TRUNC('month', transaction_date)) monthly_data")
                community_monthly_average = cur.fetchone()[0] or 0

                # Top contributors
                cur.execute("""
                    SELECT u.username, COALESCE(SUM(t.amount), 0) as total
                    FROM users u
                    LEFT JOIN transactions t ON u.firebase_uid = t.user_id AND t.type = 'contribution'
                    GROUP BY u.firebase_uid, u.username
                    ORDER BY total DESC
                    LIMIT 5
                """)
                top_contributors = cur.fetchall()

                # Stokvel comparisons
                cur.execute("""
                    SELECT s.name, s.total_pool,
                           (SELECT AVG(total_pool) FROM stokvels) as avg_pool
                    FROM stokvels s
                    JOIN stokvel_members sm ON s.id = sm.stokvel_id
                    WHERE sm.user_id = %s
                """, (user_id,))
                stokvel_comparisons = []
                for row in cur.fetchall():
                    stokvel_comparisons.append({
                        'name': row[0],
                        'total_pool': row[1] or 0,
                        'avg_pool': row[2] or 0,
                        'above_avg': (row[1] or 0) > (row[2] or 0)
                    })

                # Community badges and milestones
                community_badges = []
                community_milestones = []
                
                if community_total_contributions >= 100000:
                    community_milestones.append("R100K+ Community Contributions")
                if active_members >= 50:
                    community_badges.append("Active Community")
                if community_monthly_average >= 1000:
                    community_badges.append("High Engagement")

                # Calculate comparison to community average
                comparison = total_contributions - (community_total_contributions / max(active_members, 1))

        return render_template('financial_insight.html',
                             # Personal data
                             total_contributions=total_contributions,
                             savings_progress=savings_progress,
                             monthly_average=monthly_average,
                             health_score=health_score,
                             goal_forecast=goal_forecast,
                             milestones=milestones,
                             suggestions=suggestions,
                             recent_activity=recent_activity,
                             savings_goals=savings_goals,
                             total_loans_taken=total_loans_taken,
                             total_loans_repaid=total_loans_repaid,
                             outstanding_loans=outstanding_loans,
                             
                             # Community data
                             active_members=active_members,
                             community_total_contributions=community_total_contributions,
                             community_monthly_average=community_monthly_average,
                             community_savings_progress=savings_progress,  # Simplified
                             top_contributors=top_contributors,
                             stokvel_comparisons=stokvel_comparisons,
                             community_badges=community_badges,
                             community_milestones=community_milestones,
                             comparison=comparison,
                             
                             # Filter data
                             date_from=date_from,
                             date_to=date_to,
                             contrib_type=contrib_type)

    except Exception as e:
        print(f"Error in financial insight: {e}")
        flash("An error occurred while loading financial insights. Please try again.")
        return redirect('/home')

@app.route('/financial_insight/data')
@login_required
def financial_insight_data():
    """AJAX endpoint to get chart data for financial insights"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401

    # Get filter parameters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    contrib_type = request.args.get('type', '')

    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Build date filter
                date_filter = ""
                params = [user_id]
                if date_from:
                    date_filter += " AND t.transaction_date >= %s"
                    params.append(date_from)
                if date_to:
                    date_filter += " AND t.transaction_date <= %s"
                    params.append(date_to)
                if contrib_type:
                    date_filter += " AND t.type = %s"
                    params.append(contrib_type)

                # Personal trend data (monthly contributions)
                cur.execute(f"""
                    SELECT DATE_TRUNC('month', transaction_date)::date as month,
                           SUM(amount) as total
                    FROM transactions 
                    WHERE user_id = %s AND type = 'contribution'{date_filter}
                    GROUP BY DATE_TRUNC('month', transaction_date)
                    ORDER BY month
                """, params)
                personal_trend = [[row[0].strftime('%Y-%m'), float(row[1])] for row in cur.fetchall()]

                # Personal bar chart data (monthly breakdown by type)
                cur.execute(f"""
                    SELECT DATE_TRUNC('month', transaction_date)::date as month,
                           SUM(CASE WHEN type = 'contribution' THEN amount ELSE 0 END) as contributions,
                           SUM(CASE WHEN type = 'withdrawal' THEN amount ELSE 0 END) as withdrawals,
                           SUM(CASE WHEN type = 'payout' THEN amount ELSE 0 END) as payouts
                    FROM transactions 
                    WHERE user_id = %s{date_filter}
                    GROUP BY DATE_TRUNC('month', transaction_date)
                    ORDER BY month
                """, params)
                personal_bar_data = []
                for row in cur.fetchall():
                    personal_bar_data.append({
                        'month': row[0].strftime('%Y-%m'),
                        'contributions': float(row[1]),
                        'withdrawals': float(row[2]),
                        'payouts': float(row[3])
                    })

                # Community trend data
                cur.execute("""
                    SELECT DATE_TRUNC('month', transaction_date)::date as month,
                           SUM(amount) as total
                    FROM transactions 
                    WHERE type = 'contribution'
                    GROUP BY DATE_TRUNC('month', transaction_date)
                    ORDER BY month
                """)
                community_trend = [[row[0].strftime('%Y-%m'), float(row[1])] for row in cur.fetchall()]

                # Community bar chart data
                cur.execute("""
                    SELECT DATE_TRUNC('month', transaction_date)::date as month,
                           SUM(CASE WHEN type = 'contribution' THEN amount ELSE 0 END) as contributions,
                           SUM(CASE WHEN type = 'withdrawal' THEN amount ELSE 0 END) as withdrawals,
                           SUM(CASE WHEN type = 'payout' THEN amount ELSE 0 END) as payouts
                    FROM transactions 
                    GROUP BY DATE_TRUNC('month', transaction_date)
                    ORDER BY month
                """)
                community_bar_data = []
                for row in cur.fetchall():
                    community_bar_data.append({
                        'month': row[0].strftime('%Y-%m'),
                        'contributions': float(row[1]),
                        'withdrawals': float(row[2]),
                        'payouts': float(row[3])
                    })

                # Loan monthly data
                cur.execute("""
                    SELECT DATE_TRUNC('month', lr.created_at)::date as month,
                           SUM(lr.amount) as loaned,
                           COALESCE(SUM(lr2.amount), 0) as repaid
                    FROM loan_requests lr
                    LEFT JOIN loan_repayments lr2 ON lr.id = lr2.loan_id 
                        AND DATE_TRUNC('month', lr.created_at) = DATE_TRUNC('month', lr2.date)
                    WHERE lr.user_id = %s AND lr.status = 'approved'
                    GROUP BY DATE_TRUNC('month', lr.created_at)
                    ORDER BY month
                """, (user_id,))
                loan_monthly_data = []
                for row in cur.fetchall():
                    loan_monthly_data.append({
                        'month': row[0].strftime('%Y-%m'),
                        'loaned': float(row[1]),
                        'repaid': float(row[2])
                    })

        return jsonify({
            'personal_trend': personal_trend,
            'personal_bar_data': personal_bar_data,
            'community_trend': community_trend,
            'community_bar_data': community_bar_data,
            'loan_monthly_data': loan_monthly_data
        })

    except Exception as e:
        print(f"Error in financial insight data: {e}")
        return jsonify({'error': 'Failed to load data'}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
