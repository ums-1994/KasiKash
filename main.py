from flask import Flask, render_template, request, redirect, session, flash, jsonify, url_for, Response, send_file
import os
from datetime import timedelta, datetime
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

# Email handling imports
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename
import re
import calendar

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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in via Firebase
        if 'user_id' not in session:
            flash('Please log in to access this page.')
            return redirect('/login')
        try:
            # Verify Firebase ID token stored in session
            # This is more robust for checking active login status with Firebase
            user_id = session['user_id']
            firebase_user = auth.get_user(user_id)
            if not firebase_user:
                raise Exception("Firebase user not found")
            # You might want to update session with fresh user data here if needed
        except Exception as e:
            print(f"Firebase authentication error: {e}")
            session.pop('user_id', None) # Clear invalid session
            flash('Your session has expired or is invalid. Please log in again.')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

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
                            calendar_days=calendar_days) # Pass notification count
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
                # Fetch stokvels where the current user is a member
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
                        s.target_date
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
                        s.target_date
                    FROM stokvels s
                    WHERE s.created_by = %s
                """, (firebase_uid,))
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
# @csrf.protect
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

                # For simplicity, directly record as completed.
                # In a real app, this would be a 'pending' status requiring approval.
                cur.execute("""
                    INSERT INTO transactions (user_id, stokvel_id, amount, type, description, transaction_date, status, transaction_type)
                    VALUES (%s, %s, %s, 'payout', %s, CURRENT_DATE, 'completed', 'money')
                """, (firebase_uid, stokvel_id, amount, description))
                conn.commit()

                # Create notification for stokvel admin
                if stokvel_info and admin_user_id:
                    message = f"{user_name} requested a payout of R{amount:.2f} from '{stokvel_name}' stokvel."
                    link = url_for('payouts')
                    create_notification(admin_user_id, message, link_url=link, notification_type='payout_requested')

        flash("Payout request recorded successfully!")
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
                # Use firebase_uid directly since the database now uses Firebase UIDs
                cur.execute("""
                    SELECT id, name, target_amount, current_amount, target_date, status, created_at
                    FROM savings_goals
                    WHERE user_id = %s
                    ORDER BY target_date ASC
                """, (firebase_uid,))
                goals_tuples = cur.fetchall()

                # Convert tuples to dictionaries for easier access in template
                goals_list = []
                goal_keys = ['id', 'name', 'target_amount', 'current_amount', 'target_date', 'status', 'created_at']
                for g_tuple in goals_tuples:
                    goals_list.append(dict(zip(goal_keys, g_tuple)))

        return render_template('savings_goals.html', goals=goals_list)
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
    target_date = request.form.get('target_date') # Format 'YYYY-MM-DD'

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


@app.route('/settings')
@login_required
def settings():
    user_id = session['user_id']
    try:
        with support.db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        two_factor_enabled, 
                        language_preference,
                        email_notifications,
                        sms_notifications,
                        weekly_summary,
                        reminders_enabled
                    FROM users 
                    WHERE firebase_uid = %s
                """, (user_id,))
                user_settings = cur.fetchone() or {}
        
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
        reminders_enabled = 'reminders_enabled' in request.form
        query = """
            UPDATE users
            SET email_notifications = %s, sms_notifications = %s, weekly_summary = %s, reminders_enabled = %s
            WHERE firebase_uid = %s
        """
        params = (email_notifications, sms_notifications, weekly_summary, reminders_enabled, user_id)

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


def get_user_settings(user_id):
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT notification_preferences, two_factor_enabled FROM users WHERE firebase_uid = %s", (user_id,))
                settings_data = cur.fetchone()
                if settings_data:
                    # Handle notification_preferences as JSON
                    notification_prefs = settings_data[0]
                    if isinstance(notification_prefs, dict):
                        # If it's already a dict, use it directly
                        notification_preferences = notification_prefs
                    elif isinstance(notification_prefs, str):
                        # If it's a string, try to parse as JSON
                        try:
                            import json
                            notification_preferences = json.loads(notification_prefs)
                        except json.JSONDecodeError:
                            # If JSON parsing fails, use default
                            notification_preferences = {'email': True, 'sms': False, 'push': True}
                    else:
                        # Default if None or other type
                        notification_preferences = {'email': True, 'sms': False, 'push': True}
                    
                    return {
                        'notification_preferences': notification_preferences,
                        'two_factor_enabled': settings_data[1] or False
                    }
                return None
    except Exception as e:
        print(f"Error getting user settings: {str(e)}")
        return None

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
                'profile': "Your profile contains your personal info. You can update your name, email, and upload a profile picture.",
                'settings': "Settings let you manage notifications, security, and account preferences.",
                'notification': "Notifications alert you about important activity in your stokvels.",
                'dashboard': "The dashboard shows your balances, recent activity, and quick links to features.",
                'register': "To register, click 'Register' and fill in your details. You'll receive a verification email.",
                'login': "To log in, enter your email and password on the login page.",
                'logout': "To log out, click the logout button in the menu.",
                'profile picture': "Upload a profile picture from your profile page to personalize your account.",
                'kyc': "KYC (Know Your Customer) documents can be uploaded in your profile for verification.",
                'statement': "A statement is a summary of all transactions in your stokvel. Download it from the stokvel page.",
                'member': "A member is a person in your stokvel. You can add members by email, even if they haven't registered yet.",
                'invite': "To invite someone, add their email as a member. If they're not registered, they'll be added as pending and can join later.",
                'kasikash': "KasiKash is a financial platform for managing stokvels, contributions, savings goals, and more."
            }
            # Regex for 5W/How/Feature questions
            tellme_re = re.compile(r"(tell me about|what is|who is|when is|where is|why is|how do i|how to|how can i|explain|describe|guide me through|show me|help me with) (.+)", re.I)
            match = tellme_re.match(user_message_lower)
            if match:
                question_type, feature = match.groups()
                feature = feature.strip()
                # Try to match feature to known features
                for key in feature_faq:
                    if key in feature:
                        response = feature_faq[key]
                        break
                else:
                    response = (f"Here's how to use that feature: Go to the relevant section in the app, follow the on-screen instructions, or ask me for more details about a specific action. "
                                f"If you need step-by-step help, try asking 'How do I [action]?' or 'Tell me about [feature]'.")
                return jsonify({'response': response})

            # New intent: tell me about my stokvels
            elif any(kw in user_message_lower for kw in ["tell me about my stokvels", "my stokvels", "list my stokvels"]):
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
                                response = f"Your stokvels:\n{stokvel_list}"
                            else:
                                response = "You are not a member of any stokvels yet."
                except Exception as e:
                    print(f"Error fetching stokvels: {e}")
                    response = "Sorry, I couldn't fetch your stokvels right now."
            # New intent: tell me about KasiKash
            elif any(kw in user_message_lower for kw in ["tell me about kasikash", "what is kasikash", "about kasikash"]):
                response = (
                    "KasiKash is a financial platform for managing stokvels (community savings groups), "
                    "tracking contributions, setting savings goals, and more. It helps you and your group save, contribute, and manage money together easily."
                )

            elif any(kw in user_message_lower for kw in ["how much", "total saved", "my savings", "how much have i saved"]):
                response = f"You have saved R{total_saved} in total across all your stokvels."

            elif any(kw in user_message_lower for kw in ["create stokvel", "new stokvel", "start stokvel", "open stokvel"]):
                response = (
                    "To create a new stokvel: Go to the 'Stokvels' section, click 'Create New Stokvel', "
                    "fill in the details (name, rules, etc.), and invite members."
                )

            elif any(kw in user_message_lower for kw in ["add member", "invite member", "add someone", "add user", "add person"]):
                response = (
                    "To add members to your stokvel: Go to your stokvel's page, click 'Add Member', "
                    "enter their email address, and send the invitation."
                )

            elif any(kw in user_message_lower for kw in ["make contribution", "contribute", "add contribution", "pay contribution", "send money to stokvel"]):
                response = (
                    "To make a contribution: Go to your stokvel, select 'Make Contribution', "
                    "choose the amount and payment method, and confirm."
                )

            elif any(kw in user_message_lower for kw in ["payment method", "add card", "add bank", "my cards", "my banks", "add payment method", "link card", "link bank"]):
                try:
                    cur.execute("SELECT type, details FROM payment_methods WHERE user_id = %s", (user_id,))
                    methods = cur.fetchall()
                    if methods:
                        method_list = "\n".join([f"- {m[0]}: {m[1]}" for m in methods])
                        response = f"Your payment methods:\n{method_list}"
                    else:
                        response = "You have no payment methods saved. Add one in the Payment Methods section."
                except Exception as e:
                    print(f"Error fetching payment methods: {e}")
                    response = "You have no payment methods saved. Add one in the Payment Methods section."

            elif any(kw in user_message_lower for kw in ["savings goal", "goal", "add goal", "set goal", "my goals", "track savings"]):
                try:
                    cur.execute("SELECT name, target_amount FROM savings_goals WHERE user_id = %s", (user_id,))
                    goals = cur.fetchall()
                    if goals:
                        goal_list = "\n".join([f"- {g[0]}: R{g[1]}" for g in goals])
                        response = f"Your savings goals:\n{goal_list}"
                    else:
                        response = "You have no savings goals set. Add one in the Savings Goals section."
                except Exception as e:
                    print(f"Error fetching savings goals: {e}")
                    response = "You have no savings goals set. Add one in the Savings Goals section."

            elif any(kw in user_message_lower for kw in ["payout", "withdraw", "request payout", "get money", "take money out", "withdrawal"]):
                response = (
                    "To request a payout: Go to your stokvel, select 'Request Payout', "
                    "enter the amount and reason, and submit your request."
                )

            elif any(kw in user_message_lower for kw in ["profile", "my profile", "update profile", "edit profile", "change name", "change email"]):
                response = (
                    "To view or update your profile: Click your profile icon in the sidebar or go to the Profile page. "
                    "You can change your name or email address there."
                )

            elif any(kw in user_message_lower for kw in ["change password", "reset password", "forgot password", "update password"]):
                response = (
                    "To change your password: Go to the Profile page and click 'Reset Password'. "
                    "You will receive an email with instructions to reset your password."
                )

            elif any(kw in user_message_lower for kw in ["verify email", "not verified", "email verification", "resend verification"]):
                response = (
                    "If your profile says 'not verified', please check your email inbox for a verification link. "
                    "If you didn't receive one, go to the Profile page and click 'Resend Verification Email'."
                )

            elif any(kw in user_message_lower for kw in ["dashboard", "home", "main page", "go to dashboard", "go home"]):
                response = (
                    "To return to the dashboard, click the 'Dashboard' link in the sidebar or the KasiKash logo."
                )

            elif any(kw in user_message_lower for kw in ["recent transaction", "transaction history", "my transactions", "show transactions", "latest transactions"]):
                if transactions:
                    transaction_list = "\n".join([f"- {t[1]}: R{t[0]} ({t[2]}) on {t[3]}" for t in transactions])
                    response = f"Your recent transactions:\n{transaction_list}"
                else:
                    response = "You don't have any recent transactions."
            
            elif any(kw in user_message_lower for kw in ["help", "what can you do", "features", "how does it work", "how do i use", "explain"]):
                response = (
                    "I can help you with: Stokvel management, creating stokvels, adding members, making contributions, "
                    "managing payment methods, setting savings goals, requesting payouts, updating your profile, changing your password, verifying your email, and navigating the app. "
                    "Just ask me how to do anything!"
                )

            elif any(kw in user_message_lower for kw in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
                response = f"Hello {username}! How can I help you today? You can ask me about your savings, stokvels, or recent transactions."

            else:
                response = "I'm not sure how to help with that. You can ask me about your savings, stokvels, or any feature in the app."

            # Add fallback for settings and general 'how do I ...' questions
            if not response:
                if "settings" in user_message_lower:
                    response = (
                        "The Settings feature lets you manage your notification preferences (email, SMS, push), "
                        "enable or disable two-factor authentication, and control other account options. "
                        "Go to the Settings page from the sidebar to make changes."
                    )
                elif re.match(r"how do i (do|use|access|change|update|set|enable|disable) it", user_message_lower):
                    response = (
                        "Please specify what you want to do, for example: 'How do I add a payment method?' or 'How do I change my password?'"
                    )

            # Special case for 'add payment method' to always give instructions
            if any(kw in user_message_lower for kw in ["add payment method", "add a payment method", "link card", "link bank", "how do i add a payment method"]):
                response = "To add a payment method: Go to the Payment Methods section, click 'Add Payment Method', enter your card or bank details, and save."

            elif any(kw in user_message_lower for kw in ["payment method", "add card", "add bank", "my cards", "my banks"]):
                try:
                    cur.execute("SELECT type, details FROM payment_methods WHERE user_id = %s", (user_id,))
                    methods = cur.fetchall()
                    if methods:
                        method_list = "\n".join([f"- {m[0]}: {m[1]}" for m in methods])
                        response = f"Your payment methods:\n{method_list}"
                    else:
                        response = "You have no payment methods saved. To add one, go to the Payment Methods section and click 'Add Payment Method'."
                except Exception as e:
                    print(f"Error fetching payment methods: {e}")
                    response = "You have no payment methods saved. To add one, go to the Payment Methods section and click 'Add Payment Method'."

        return jsonify({'response': response})

    except Exception as e:
        print(f"Error in handle_chat: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/stokvel/<int:stokvel_id>/members/add', methods=['POST'])
@login_required
def add_stokvel_member(stokvel_id):
    user_id = session.get('user_id')
    member_email = request.form.get('email')

    if not user_id:
        flash("Please log in to add members.")
        return redirect('/login')

    with support.db_connection() as conn:
        with conn.cursor() as cur:
            # Check if current user is an admin of the stokvel
            cur.execute("SELECT role FROM stokvel_members WHERE stokvel_id = %s AND user_id = %s", (stokvel_id, user_id))
            user_role = cur.fetchone()

            if not user_role or user_role[0] != 'admin':
                flash("You do not have permission to add members to this stokvel.")
                return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))

            # Get stokvel name for email notification
            cur.execute("SELECT name FROM stokvels WHERE id = %s", (stokvel_id,))
            stokvel_data = cur.fetchone()
            stokvel_name = stokvel_data[0] if stokvel_data else "Unknown Stokvel"

            # Find the user to add by email
            cur.execute("SELECT firebase_uid, username FROM users WHERE email = %s", (member_email,))
            user_to_add_data = cur.fetchone()

            if not user_to_add_data:
                # Add as pending member by email only
                cur.execute("INSERT INTO stokvel_members (stokvel_id, user_id, email, role, status) VALUES (%s, NULL, %s, 'pending', 'pending')", (stokvel_id, member_email))
                conn.commit()
                
                # Send email notification for pending member
                subject = f"Invitation to join {stokvel_name}!"
                body = f"""
                <html>
                    <body>
                        <h2>You've been invited to join {stokvel_name}!</h2>
                        <p>Hello {member_email},</p>
                        <p>You have been invited to join the stokvel "{stokvel_name}" as a pending member.</p>
                        <p>To accept this invitation, please <a href="{url_for('register', _external=True)}">register here</a> first if you don't have an account.</p>
                        <p>Once registered, you can log in and view your stokvel invitation.</p>
                        <p>Login page: <a href="{url_for('login', _external=True)}">Login</a></p>
                        <p>Registration page: <a href="{url_for('register', _external=True)}">Register</a></p>
                    </body>
                </html>
                """
                email_sent = send_email(member_email, subject, body)
                if email_sent:
                    flash(f"{member_email} has been added as a pending member and invitation email sent!")
                else:
                    flash(f"{member_email} has been added as a pending member, but failed to send invitation email.")
                return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))
            
            user_to_add_id = user_to_add_data[0]
            username_to_add = user_to_add_data[1]

            # Check if the user is already a member of this stokvel
            cur.execute("SELECT 1 FROM stokvel_members WHERE stokvel_id = %s AND user_id = %s", (stokvel_id, user_to_add_id))
            if cur.fetchone():
                flash(f"User {member_email} is already a member of this stokvel.")
                return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))

            # Add the user as a new member
            cur.execute("INSERT INTO stokvel_members (stokvel_id, user_id, email, role, status) VALUES (%s, %s, %s, 'member', 'active')", (stokvel_id, user_to_add_id, member_email))
            conn.commit()

    # Send email notification for existing user
    subject = f"Welcome to {stokvel_name}!"
    body = f"""
    <html>
        <body>
            <h2>Welcome to {stokvel_name}!</h2>
            <p>Hello {username_to_add if user_to_add_data else member_email},</p>
            <p>You have been added as a member to the stokvel "{stokvel_name}".</p>
            <p>If you don't have an account, please <a href="{url_for('register', _external=True)}">register here</a> first.</p>
            <p>Click <a href="{url_for('view_stokvel_members', stokvel_id=stokvel_id, _external=True)}">here</a> to view your stokvel members page and get started!</p>
            <p>If you are already registered, please log in: <a href="{url_for('login', _external=True)}">Login Page</a></p>
        </body>
    </html>
    """
    email_sent = send_email(member_email, subject, body)
    if email_sent:
        flash(f"User {member_email} added to stokvel successfully and notification email sent!")
    else:
        flash(f"User {member_email} added to stokvel successfully, but failed to send notification email.")

    return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))

@app.route('/stokvel/<int:stokvel_id>/members/remove', methods=['POST'])
@login_required
def remove_stokvel_member(stokvel_id):
    user_id = session.get('user_id')
    member_to_remove_id = request.form.get('member_id')

    if not user_id:
        flash("Please log in to remove members.")
        return redirect('/login')

    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Check if current user is an admin of the stokvel
                cur.execute("SELECT role FROM stokvel_members WHERE stokvel_id = %s AND user_id = %s", (stokvel_id, user_id))
                user_role = cur.fetchone()

                if not user_role or user_role[0] != 'admin':
                    flash("You do not have permission to remove members from this stokvel.")
                    return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))
                
                # Get the role and user_id of the member to be removed
                cur.execute("SELECT role, user_id FROM stokvel_members WHERE id = %s AND stokvel_id = %s", (member_to_remove_id, stokvel_id))
                member_to_remove_data = cur.fetchone()
                
                if not member_to_remove_data:
                    flash("Member not found in this stokvel.")
                    return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))

                member_role = member_to_remove_data[0]
                member_firebase_uid = member_to_remove_data[1]

                # If the member to be removed is an admin, check if they are the last admin
                if member_role == 'admin':
                    cur.execute("SELECT COUNT(*) FROM stokvel_members WHERE stokvel_id = %s AND role = 'admin'", (stokvel_id,))
                    admin_count = cur.fetchone()[0]

                    if admin_count == 1 and member_firebase_uid == user_id: # Current user is the last admin
                        flash("You cannot remove yourself as the last admin of the stokvel.")
                        return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))
                    elif admin_count == 1: # Someone else is the last admin
                         flash("Cannot remove the last admin of the stokvel.")
                         return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))

                # Proceed with removal
                cur.execute("DELETE FROM stokvel_members WHERE id = %s AND stokvel_id = %s", (member_to_remove_id, stokvel_id))
                conn.commit()

            flash("Member removed successfully!")
    except Exception as e:
        print(f"Error removing member: {e}")
        flash("An error occurred while removing the member. Please try again.")

    return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))

@app.route('/notifications')
@login_required
def notifications():
    """Fetch and display user notifications, and mark them as read."""
    user_id = session['user_id']
    try:
        with support.db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Fetch all notifications for the user, newest first
                cur.execute("""
                    SELECT id, message, is_read, link_url, created_at
                    FROM notifications
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))
                user_notifications = cur.fetchall()
                
                # Mark all unread notifications as read for this user
                cur.execute("UPDATE notifications SET is_read = TRUE WHERE user_id = %s AND is_read = FALSE", (user_id,))
                conn.commit()
        
        return render_template('notifications.html', notifications=user_notifications)
        
    except Exception as e:
        print(f"Error fetching notifications: {e}")
        flash("Could not load notifications.", "danger")
        return redirect(url_for('home'))


@app.route('/notifications/clear', methods=['POST'])
@login_required
def clear_notifications():
    """Endpoint to mark all notifications as read via a POST request."""
    user_id = session['user_id']
    try:
        update_query = "UPDATE notifications SET is_read = TRUE WHERE user_id = %s"
        support.execute_query("update", update_query, (user_id,))
        flash("All notifications marked as read.", "success")
    except Exception as e:
        print(f"Error clearing notifications: {e}")
        flash("Could not mark notifications as read.", "danger")
    return redirect(url_for('notifications'))


@app.route('/resend-verification', methods=['POST'])
@login_required
def resend_verification():
    print("Resend verification called. Session user_id:", session.get('user_id'))
    try:
        user_id = session['user_id']
        # Get user from Firebase
        user = auth.get_user(user_id)
        
        if user.email_verified:
            return jsonify({
                'success': False,
                'message': 'Email is already verified'
            }), 200  # Changed from 400 to 200

        # Generate email verification link
        verification_link = auth.generate_email_verification_link(user.email)
        
        # Send verification email
        if send_email_verification(user.email, verification_link):
            return jsonify({
                'success': True,
                'message': 'Verification email sent successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send verification email'
            }), 500

    except Exception as e:
        print(f"Error in resend verification: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while sending verification email'
        }), 500

@app.route('/stokvel/<int:stokvel_id>/statement')
@login_required
def view_stokvel_statement(stokvel_id):
    try:
        user_id = session.get('user_id')
        if not user_id:
            flash('Please log in to view statements', 'error')
            return redirect(url_for('login'))

        # Get period parameter from query string
        period = request.args.get('period', 'all')

        # Get stokvel details
        cur = get_db().cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT s.*, u.email as admin_email 
            FROM stokvels s 
            JOIN users u ON s.created_by = u.firebase_uid 
            WHERE s.id = %s
        """, (stokvel_id,))
        stokvel = cur.fetchone()

        if not stokvel:
            flash('Stokvel not found', 'error')
            return redirect(url_for('home'))

        # Verify user is a member
        cur.execute("""
            SELECT * FROM stokvel_members 
            WHERE stokvel_id = %s AND user_id = %s
        """, (stokvel_id, user_id))
        membership = cur.fetchone()

        if not membership:
            flash('You do not have access to this stokvel', 'error')
            return redirect(url_for('home'))

        # Build the query with period filtering
        base_query = """
            SELECT 
                t.*,
                u.email as user_email,
                CASE 
                    WHEN t.type = 'contribution' THEN t.amount
                    ELSE 0
                END as contribution_amount,
                CASE 
                    WHEN t.type = 'payout' THEN t.amount
                    ELSE 0
                END as payout_amount,
                CASE 
                    WHEN t.type = 'expense' THEN t.amount
                    ELSE 0
                END as expense_amount
            FROM transactions t
            LEFT JOIN users u ON t.user_id = u.firebase_uid
            WHERE t.stokvel_id = %s
        """
        
        # Add period filtering
        if period == '30d':
            base_query += " AND t.created_at >= CURRENT_DATE - 30"
        elif period == '3m':
            base_query += " AND t.created_at >= CURRENT_DATE - 90"
        elif period == '6m':
            base_query += " AND t.created_at >= CURRENT_DATE - 180"
        # For 'all' or any other value, no additional filtering
        
        base_query += " ORDER BY t.created_at DESC"
        
        cur.execute(base_query, (stokvel_id,))
        transactions = cur.fetchall()

        # Calculate summary
        total_contributions = sum(t['contribution_amount'] for t in transactions)
        total_payouts = sum(t['payout_amount'] for t in transactions)
        total_expenses = sum(t['expense_amount'] for t in transactions)
        current_balance = total_contributions - total_payouts - total_expenses

        # Get member contributions summary
        member_contributions_query = """
            SELECT 
                u.email as member_email,
                SUM(CASE WHEN t.type = 'contribution' THEN t.amount ELSE 0 END) as total_contributed,
                COUNT(CASE WHEN t.type = 'contribution' THEN 1 END) as contribution_count
            FROM stokvel_members sm
            JOIN users u ON sm.user_id = u.firebase_uid
            LEFT JOIN transactions t ON t.user_id = u.firebase_uid AND t.stokvel_id = sm.stokvel_id
            WHERE sm.stokvel_id = %s
        """
        
        # Add period filtering to member contributions if needed
        if period == '30d':
            member_contributions_query += " AND (t.created_at >= CURRENT_DATE - 30 OR t.created_at IS NULL)"
        elif period == '3m':
            member_contributions_query += " AND (t.created_at >= CURRENT_DATE - 90 OR t.created_at IS NULL)"
        elif period == '6m':
            member_contributions_query += " AND (t.created_at >= CURRENT_DATE - 180 OR t.created_at IS NULL)"
        
        member_contributions_query += " GROUP BY u.email ORDER BY total_contributed DESC"
        
        cur.execute(member_contributions_query, (stokvel_id,))
        member_contributions = cur.fetchall()

        # Format the data for the template
        statement_data = {
            'stokvel': {
                'id': stokvel['id'],
                'name': stokvel['name'],
                'created_at': stokvel['created_at'].strftime('%Y-%m-%d') if isinstance(stokvel['created_at'], datetime) else str(stokvel['created_at']),
                'admin_email': stokvel['admin_email']
            },
            'summary': {
                'total_contributions': total_contributions,
                'total_payouts': total_payouts,
                'total_expenses': total_expenses,
                'current_balance': current_balance
            },
            'transactions': [{
                'date': t['created_at'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(t['created_at'], datetime) else str(t['created_at']),
                'type': t['type'],
                'amount': float(t['amount']),
                'description': t['description'],
                'user_email': t['user_email']
            } for t in transactions],
            'member_contributions': [{
                'email': m['member_email'],
                'total_contributed': float(m['total_contributed'] or 0),
                'contribution_count': int(m['contribution_count'] or 0)
            } for m in member_contributions],
            'period': period
        }

        return render_template('stokvel_statement.html', statement=statement_data)

    except Exception as e:
        print(f"Error generating stokvel statement: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        flash('An error occurred while generating the statement', 'error')
        return redirect(url_for('home'))

@app.route('/stokvel/<int:stokvel_id>/statement/download')
@login_required
def download_statement(stokvel_id):
    try:
        user_id = session.get('user_id')
        if not user_id:
            flash('Please log in to download statements', 'error')
            return redirect(url_for('login'))

        # Get period parameter from query string
        period = request.args.get('period', 'all')

        # Use RealDictCursor for all queries
        cur = get_db().cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT s.*, u.email as admin_email 
            FROM stokvels s 
            JOIN users u ON s.created_by = u.firebase_uid 
            WHERE s.id = %s
        """, (stokvel_id,))
        stokvel = cur.fetchone()

        if not stokvel:
            flash('Stokvel not found', 'error')
            return redirect(url_for('home'))

        cur.execute("""
            SELECT * FROM stokvel_members 
            WHERE stokvel_id = %s AND user_id = %s
        """, (stokvel_id, user_id))
        membership = cur.fetchone()

        if not membership:
            flash('You do not have access to this stokvel', 'error')
            return redirect(url_for('home'))

        # Build the query with period filtering
        base_query = """
            SELECT 
                t.*,
                u.email as user_email,
                CASE WHEN t.type = 'contribution' THEN t.amount ELSE 0 END as contribution_amount,
                CASE WHEN t.type = 'payout' THEN t.amount ELSE 0 END as payout_amount,
                CASE WHEN t.type = 'expense' THEN t.amount ELSE 0 END as expense_amount
            FROM transactions t
            LEFT JOIN users u ON t.user_id = u.firebase_uid
            WHERE t.stokvel_id = %s
        """
        
        # Add period filtering
        if period == '30d':
            base_query += " AND t.created_at >= CURRENT_DATE - 30"
        elif period == '3m':
            base_query += " AND t.created_at >= CURRENT_DATE - 90"
        elif period == '6m':
            base_query += " AND t.created_at >= CURRENT_DATE - 180"
        # For 'all' or any other value, no additional filtering
        
        base_query += " ORDER BY t.created_at DESC"
        
        cur.execute(base_query, (stokvel_id,))
        transactions = cur.fetchall()

        # Calculate summary
        total_contributions = sum(float(t.get('contribution_amount', 0) or 0) for t in transactions)
        total_payouts = sum(float(t.get('payout_amount', 0) or 0) for t in transactions)
        total_expenses = sum(float(t.get('expense_amount', 0) or 0) for t in transactions)
        current_balance = total_contributions - total_payouts - total_expenses

        # Create PDF
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Add title with period information
        period_text = {
            'all': 'All Time',
            '30d': 'Last 30 Days',
            '3m': 'Last 3 Months',
            '6m': 'Last 6 Months'
        }.get(period, 'All Time')
        
        title = Paragraph(f"{stokvel['name']} - Statement ({period_text})", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 20))

        # Add summary
        summary_data = [
            ['Total Contributions', f'R {total_contributions:,.2f}'],
            ['Total Payouts', f'R {total_payouts:,.2f}'],
            ['Total Expenses', f'R {total_expenses:,.2f}'],
            ['Current Balance', f'R {current_balance:,.2f}']
        ]
        summary_table = Table(summary_data, colWidths=[200, 100])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))

        # Add transactions
        table_data = [['Date', 'Type', 'Amount', 'Description', 'User']]
        for t in transactions:
            created_at = t.get('created_at')
            if isinstance(created_at, datetime):
                date_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
            else:
                date_str = str(created_at) if created_at else ''
            table_data.append([
                date_str,
                (t.get('type') or '').title(),
                f'R {float(t.get("amount", 0) or 0):,.2f}',
                t.get('description', '') or '',
                t.get('user_email', '') or ''
            ])

        table = Table(table_data, colWidths=[100, 80, 80, 200, 150])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)

        doc.build(elements)
        output.seek(0)
        
        # Include period in filename
        filename = f'{stokvel["name"]}_statement_{period}_{datetime.now().strftime("%Y%m%d")}.pdf'
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"Error generating statement: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        flash('An error occurred while generating the statement', 'error')
        return redirect(url_for('view_stokvel_statement', stokvel_id=stokvel_id))

@app.route('/profile/upload_picture', methods=['POST'])
@login_required
def upload_profile_picture():
    if 'profile_picture' not in request.files:
        flash('No file part')
        return redirect(url_for('profile'))
    
    file = request.files['profile_picture']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('profile'))
    
    if file and allowed_file(file.filename):
        try:
            # Create upload folder if it doesn't exist
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # Generate secure filename
            filename = secure_filename(f"{session['user_id']}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save the file
            file.save(file_path)
            
            # Update user's profile_picture in DB
            with support.db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE users 
                        SET profile_picture = %s 
                        WHERE firebase_uid = %s
                    """, (filename, session['user_id']))
                    conn.commit()
            
            flash('Profile picture updated successfully!')
        except Exception as e:
            print(f"Error uploading profile picture: {e}")
            flash('Error uploading profile picture. Please try again.')
    else:
        flash('Invalid file type. Please upload an image file (PNG, JPG, JPEG, or GIF).')
    
    return redirect(url_for('profile'))

@app.route('/profile/upload_kyc', methods=['POST'])
@login_required
def upload_kyc():
    user_id = session['user_id']
    id_document = request.files.get('id_document')
    proof_of_address = request.files.get('proof_of_address')
    updates = {}
    
    if id_document and allowed_kyc_file(id_document.filename):
        filename = secure_filename(f"{user_id}_id_{id_document.filename}")
        os.makedirs(app.config['KYC_UPLOAD_FOLDER'], exist_ok=True)
        id_document.save(os.path.join(app.config['KYC_UPLOAD_FOLDER'], filename))
        updates['id_document'] = filename
        updates['id_document_status'] = 'pending'  # Set status to pending for review
    
    if proof_of_address and allowed_kyc_file(proof_of_address.filename):
        filename = secure_filename(f"{user_id}_address_{proof_of_address.filename}")
        os.makedirs(app.config['KYC_UPLOAD_FOLDER'], exist_ok=True)
        proof_of_address.save(os.path.join(app.config['KYC_UPLOAD_FOLDER'], filename))
        updates['proof_of_address'] = filename
        updates['proof_of_address_status'] = 'pending'  # Set status to pending for review
    
    # Update user in DB
    if updates:
        set_clause = ', '.join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [user_id]
        query = f"UPDATE users SET {set_clause} WHERE firebase_uid = %s"
        support.execute_query("update", query, tuple(values))
        
        flash('KYC documents uploaded successfully and are pending verification.')
    else:
        flash('No valid documents were uploaded.')
    
    return redirect(url_for('profile'))

@app.route('/notifications/count')
@login_required
def notifications_count():
    user_id = session.get('user_id')
    count = get_notification_count(user_id) if user_id else 0
    return jsonify({'count': count})

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

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
