from flask import Flask, render_template, request, redirect, session, flash, jsonify, url_for
import os
from datetime import timedelta
import pandas as pd
import plotly
import plotly.express as px
import json
import warnings
import support
import datetime
from functools import wraps
import psycopg2
from dotenv import load_dotenv
import openai
from flask_wtf.csrf import CSRFProtect
import firebase_admin
from firebase_admin import credentials, auth

# Email handling imports
import smtplib
import ssl
from email.message import EmailMessage

# SendGrid imports
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

warnings.filterwarnings("ignore")

# Load environment variables
load_dotenv()

# Debugging .env loading
print(f"DEBUG: DB_NAME loaded from .env: {os.getenv('DB_NAME')}")
print(f"DEBUG: FIREBASE_SERVICE_ACCOUNT_KEY_PATH from .env: {os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH')}")

# Debugging SendGrid environment variables
print(f"DEBUG: SENDGRID_API_KEY loaded from .env: {os.getenv('SENDGRID_API_KEY')}")
print(f"DEBUG: MAIL_SENDER_EMAIL loaded from .env: {os.getenv('MAIL_SENDER_EMAIL')}")

# Initialize Firebase Admin SDK
# Ensure your 'firebase-service-account.json' is in the root directory
# You should have a FIREBASE_SERVICE_ACCOUNT_KEY_PATH in your .env pointing to this file.
cred = credentials.Certificate(os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH", "firebase-service-account.json"))
firebase_admin.initialize_app(cred)

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', '823d26fd5b5651cc6f9072c5b2866d909e6e5f8785a027bb713f08846cadda6f')  # Set a secure secret key
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
csrf = CSRFProtect(app)

# Initialize OpenAI client at application level
try:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    print("Warning: OpenAI client not initialized. Chat features will be disabled.")
    client = None

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
    if 'user_id' in session:
        try:
            with support.db_connection() as conn:
                with conn.cursor() as cur:
                    # Get user info by firebase_uid
                    cur.execute("SELECT username FROM users WHERE firebase_uid = %s", (session['user_id'],))
                    user = cur.fetchone()
                    user_name = user[0] if user else session.get('username', 'User')

                    # Initialize default values for new users
                    total_saved = 0
                    total_monthly_contribution = 0
                    active_stokvels = 0
                    next_payout_date = None
                    next_payout_amount = 0
                    upcoming_payments = []
                    recent_transactions = []

                    return render_template('dashboard.html',
                                        user_name=user_name,
                                        total_saved=total_saved,
                                        monthly_contribution=total_monthly_contribution,
                                        active_stokvels=active_stokvels,
                                        next_payout_date=next_payout_date,
                                        next_payout_amount=next_payout_amount,
                                        upcoming_payments=upcoming_payments,
                                        recent_transactions=recent_transactions)
        except Exception as e:
            print(f"Dashboard error: {str(e)}")
            flash("Error loading dashboard. Please try again.")
            return redirect('/login')
    else:
        return redirect('/login')


@app.route('/analysis')
def analysis():
    if 'user_id' in session:
        # Changed to firebase_uid
        query = "select * from user_login where firebase_uid = %s "
        userdata = support.execute_query('search', query, (session['user_id'],))
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
                                   user_name=userdata[0][1],
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
                                   user_name=userdata[0][1],
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
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)
    if 'user_id' in session:
        flash("Already a user is logged-in!")
        return redirect('/home')
    else:
        return render_template("login.html")


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully!")
    return redirect('/')


@app.route('/login_validation', methods=['POST'])
def login_validation():
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        
        print(f"Login attempt for email: {email}")  # Debug log
        
        # Try to get user by email first
        try:
            print("Attempting to get user from Firebase...")  # Debug log
            user_record = auth.get_user_by_email(email)
            print(f"User found: {user_record.uid}")  # Debug log
            
            # If we get here, the user exists
            session['user_id'] = user_record.uid
            session['username'] = user_record.display_name or email
            session['is_verified'] = user_record.email_verified
            session.permanent = True
            
            if not user_record.email_verified:
                print("User email not verified")  # Debug log
                flash("Please verify your email address before logging in.")
                return redirect('/login')
                
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
        print(f"Login validation error: {str(e)}")  # Debug log
        flash('An error occurred during login. Please try again.')
        return redirect('/login')


@app.route('/register')
def register():
    return render_template("register.html")


# Helper function to send email verification using SendGrid
def send_email_verification(to_email, verification_link):
    sender_email = os.getenv("MAIL_SENDER_EMAIL")
    sender_name = os.getenv("MAIL_SENDER_NAME")
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")

    if not sendgrid_api_key:
        print("Error: SENDGRID_API_KEY not found in environment variables.")
        return False
    if not sender_email:
        print("Error: MAIL_SENDER_EMAIL not found in environment variables.")
        return False

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

    message = Mail(
        from_email=(sender_email, sender_name),
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )

    try:
        sendgrid_client = SendGridAPIClient(sendgrid_api_key)
        response = sendgrid_client.send(message)
        print(f"SendGrid email sent status code: {response.status_code}")
        print(f"SendGrid email response body: {response.body}")
        print(f"SendGrid email response headers: {response.headers}")
        if response.status_code == 202:
            print(f"Verification email sent successfully to {to_email} via SendGrid!")
            return True
        else:
            print(f"Failed to send verification email via SendGrid. Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error sending verification email to {to_email} via SendGrid: {e}")
        return False


@app.route('/registration', methods=['POST'])
@csrf.exempt
def registration():
    if 'user_id' not in session:
        username = request.form.get('username')
        email = request.form.get('email')
        passwd = request.form.get('password')

        print(f"Registration attempt - Username: {username}, Email: {email}")

        if len(username) > 5 and len(email) > 10 and len(passwd) > 5:
            try:
                user = None # Initialize user to None
                # Try to get user by email first to check if they already exist
                try:
                    user = auth.get_user_by_email(email)
                    # If user exists
                    if not user.email_verified:
                        # User exists but email is not verified, resend verification email
                        verification_link = auth.generate_email_verification_link(email)
                        if send_email_verification(email, verification_link):
                            flash("Account already exists but email not verified. A new verification link has been sent to your email.")
                        else:
                            flash("Account already exists but email not verified. Failed to resend verification link. Please contact support.")
                        return redirect('/login') # Redirect to login after resending link
                    else:
                        # User exists and email is verified, prompt to login
                        flash("An account with this email already exists and is verified. Please log in.")
                        return redirect('/login')
                except auth.UserNotFoundError:
                    # User does not exist, proceed with creation
                    pass # Continue to the user creation block

                # 1. Create user in Firebase Authentication (only if not found above)
                user = auth.create_user(
                    email=email,
                    password=passwd,
                    display_name=username,
                    email_verified=False  # Initially false, Firebase will send verification email
                )

                # 2. Generate and Send email verification link via custom SMTP
                verification_link = auth.generate_email_verification_link(email)
                if send_email_verification(email, verification_link):
                    flash("Registration successful! Please check your email to verify your account.")
                else:
                    flash("Registration successful, but failed to send verification email. Please contact support.")
                    # IMPORTANT: If email sending failed, you might want to delete the Firebase user here
                    # to prevent unverified accounts from being created without a way to verify.
                    # auth.delete_user(user.uid)
                    # return redirect('/register')

                # 3. Store Firebase UID and username/email in your PostgreSQL database
                with support.db_connection() as conn:
                    with conn.cursor() as cur:
                        # Optional: Check if email already exists in your local DB
                        # (Firebase handles uniqueness for auth, this is for local DB integrity)
                        cur.execute("SELECT firebase_uid FROM users WHERE firebase_uid = %s", (user.uid,))
                        if cur.fetchone():
                            # This case should ideally not happen if Firebase creates a new user, but as a safeguard
                            flash("A database record for this Firebase user already exists.")
                            return redirect('/login')

                        # Insert new user into your local DB, linking with Firebase UID
                        cur.execute(
                            "INSERT INTO users (firebase_uid, username, email) VALUES (%s, %s, %s) RETURNING id",
                            (user.uid, username, email)
                        )
                        local_user_id = cur.fetchone()[0]
                        conn.commit()

                        if local_user_id:
                            session['user_id'] = user.uid  # Store Firebase UID in session
                            session['username'] = username
                            session['is_verified'] = False  # Will be updated after email verification by Firebase
                            session.permanent = True

                            return redirect('/home')
                        else:
                            flash("Registration failed: Could not retrieve local user ID.")
                            auth.delete_user(user.uid)  # Delete Firebase user if local DB insertion fails
                            return redirect('/register')

            except Exception as e:  # Catch all Firebase auth errors (for user creation/general issues)
                print(f"Firebase Registration error: {str(e)}")
                # If the error is still 'email-already-exists' here, it means it wasn't caught by get_user_by_email
                # which is less likely with correct handling, but keep this as a fallback.
                if "email-already-exists" in str(e) or "The user with the provided email already exists" in str(e):
                    flash("Email address is already in use. Please use a different email or log in.")
                else:
                    flash(f"An unexpected error occurred during registration: {str(e)}")
                # IMPORTANT: If a Firebase user was created but local DB insertion failed, delete Firebase user
                if 'user' in locals() and user and not user.email_verified: # Only delete if user was newly created and unverified
                    try:
                        auth.delete_user(user.uid)
                        print(f"Cleaned up Firebase user {user.uid} due to local DB error.")
                    except Exception as delete_e:
                        print(f"Error deleting Firebase user {user.uid} during cleanup: {delete_e}")
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
    user_id = session['user_id']
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Get all stokvels, and if the current user is a member, their role
                cur.execute("""
                    SELECT 
                        s.id, s.name, s.description, s.monthly_contribution, 
                        s.target_amount, s.target_date, s.created_at,
                        s.total_pool, -- Include total_pool
                        COUNT(sm.user_id) as member_count,
                        COALESCE(curr_member.role, 'none') as current_user_role -- Get current user's role or 'none'
                    FROM stokvels s
                    LEFT JOIN stokvel_members sm ON s.id = sm.stokvel_id
                    LEFT JOIN stokvel_members curr_member ON s.id = curr_member.stokvel_id AND curr_member.user_id = %s
                    GROUP BY s.id, s.name, s.description, s.monthly_contribution, 
                             s.target_amount, s.target_date, s.created_at, s.total_pool, curr_member.role
                    ORDER BY s.created_at DESC
                """, (user_id,))
                stokvels_tuples = cur.fetchall()

                # Convert all stokvels tuples to dictionaries
                stokvel_keys_all = ['id', 'name', 'description', 'monthly_contribution',
                                    'target_amount', 'target_date', 'created_at',
                                    'total_pool', 'member_count', 'role']
                stokvels_list = []
                for s_tuple in stokvels_tuples:
                    stokvels_list.append(dict(zip(stokvel_keys_all, s_tuple)))

                # Get user's stokvels (the ones they are directly a member of)
                cur.execute("""
                    SELECT 
                        s.id, s.name, s.description, s.monthly_contribution, 
                        s.target_amount, s.target_date, s.created_at,
                        s.total_pool, -- Include total_pool
                        sm.role -- Get the member's role
                    FROM stokvels s
                    JOIN stokvel_members sm ON s.id = sm.stokvel_id
                    WHERE sm.user_id = %s
                    ORDER BY s.created_at DESC
                """, (user_id,))
                my_stokvels_tuples = cur.fetchall()

                # Convert user's stokvels tuples to dictionaries
                stokvel_keys_my = ['id', 'name', 'description', 'monthly_contribution',
                                   'target_amount', 'target_date', 'created_at',
                                   'total_pool', 'role']
                my_stokvels_list = []
                for ms_tuple in my_stokvels_tuples:
                    my_stokvels_list.append(dict(zip(stokvel_keys_my, ms_tuple)))

        return render_template('stokvels.html', stokvels=stokvels_list, my_stokvels=my_stokvels_list)
    except Exception as e:
        print(f"Stokvels page error: {e}")
        flash("An error occurred while loading stokvels. Please try again.")
        return redirect('/home')

@app.route('/create_stokvel', methods=['POST'])
@login_required
def create_stokvel():
    if 'user_id' not in session:
        flash("Please log in to create a stokvel.")
        return redirect('/login')

    name = request.form.get('name')
    description = request.form.get('description')
    monthly_contribution = request.form.get('monthly_contribution')
    target_amount = request.form.get('target_amount')
    target_date = request.form.get('target_date') # Format 'YYYY-MM-DD'

    if not all([name, description, monthly_contribution, target_amount, target_date]):
        flash("All fields are required to create a stokvel.")
        return redirect('/stokvels')

    try:
        monthly_contribution = float(monthly_contribution)
        target_amount = float(target_amount)

        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Insert new stokvel
                cur.execute("""
                    INSERT INTO stokvels (name, description, monthly_contribution, target_amount, target_date, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                """, (name, description, monthly_contribution, target_amount, target_date, session['user_id']))
                stokvel_id = cur.fetchone()[0]
                conn.commit()

                # Add creator as a member
                cur.execute("""
                    INSERT INTO stokvel_members (stokvel_id, user_id, role)
                    VALUES (%s, %s, 'admin')
                """, (stokvel_id, session['user_id']))
                conn.commit()

        flash(f"Stokvel '{name}' created successfully!")
        return redirect('/stokvels')
    except ValueError:
        flash("Monthly contribution and Target amount must be numbers.")
        return redirect('/stokvels')
    except Exception as e:
        print(f"Error creating stokvel: {e}")
        flash("An error occurred while creating the stokvel. Please try again.")
        return redirect('/stokvels')


@app.route('/contributions')
@login_required
def contributions():
    user_id = session['user_id']
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Get user's contributions
                cur.execute("""
                    SELECT t.amount, t.description, t.transaction_date, s.name as stokvel_name
                    FROM transactions t
                    JOIN stokvels s ON t.stokvel_id = s.id
                    WHERE t.user_id = %s AND t.type = 'contribution'
                    ORDER BY t.transaction_date DESC
                """, (user_id,))
                contributions = cur.fetchall()

                # Get stokvels the user is a member of
                cur.execute("""
                    SELECT s.id, s.name
                    FROM stokvels s
                    JOIN stokvel_members sm ON s.id = sm.stokvel_id
                    WHERE sm.user_id = %s
                """, (user_id,))
                stokvel_options = cur.fetchall()

        return render_template('contributions.html', contributions=contributions, stokvel_options=stokvel_options)
    except Exception as e:
        print(f"Contributions page error: {e}")
        flash("An error occurred while loading contributions. Please try again.")
        return redirect('/home')

@app.route('/make_contribution', methods=['POST'])
@login_required
def make_contribution():
    stokvel_id = request.form.get('stokvel_id')
    amount = request.form.get('amount')
    description = request.form.get('description')
    user_id = session['user_id']

    if not all([stokvel_id, amount, description]):
        flash("All fields are required for contribution.")
        return redirect('/contributions')

    try:
        amount = float(amount)
        stokvel_id = int(stokvel_id)
        
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Insert the transaction
                cur.execute("""
                    INSERT INTO transactions (user_id, stokvel_id, amount, type, description, transaction_date, status)
                    VALUES (%s, %s, %s, 'contribution', %s, CURRENT_DATE, 'completed')
                """, (user_id, stokvel_id, amount, description))
                conn.commit()

        flash("Contribution recorded successfully!")
        return redirect('/contributions')
    except ValueError:
        flash("Amount must be a number.")
        return redirect('/contributions')
    except Exception as e:
        print(f"Error making contribution: {e}")
        flash("An error occurred while recording your contribution. Please try again.")
        return redirect('/contributions')


@app.route('/payouts')
@login_required
def payouts():
    user_id = session['user_id']
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Get user's payouts
                cur.execute("""
                    SELECT t.amount, t.description, t.transaction_date, s.name as stokvel_name
                    FROM transactions t
                    JOIN stokvels s ON t.stokvel_id = s.id
                    WHERE t.user_id = %s AND t.type = 'payout'
                    ORDER BY t.transaction_date DESC
                """, (user_id,))
                payouts = cur.fetchall()

                # Get stokvels the user is a member of to show options for payout requests
                cur.execute("""
                    SELECT s.id, s.name, s.target_amount, s.monthly_contribution, s.target_date
                    FROM stokvels s
                    JOIN stokvel_members sm ON s.id = sm.stokvel_id
                    WHERE sm.user_id = %s
                """, (user_id,))
                stokvel_options = cur.fetchall()

        return render_template('payouts.html', payouts=payouts, stokvel_options=stokvel_options)
    except Exception as e:
        print(f"Payouts page error: {e}")
        flash("An error occurred while loading payouts. Please try again.")
        return redirect('/home')

@app.route('/request_payout', methods=['POST'])
@login_required
def request_payout():
    stokvel_id = request.form.get('stokvel_id')
    amount = request.form.get('amount')
    description = request.form.get('description')
    user_id = session['user_id']

    if not all([stokvel_id, amount, description]):
        flash("All fields are required for payout request.")
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
                """, (stokvel_id, user_id))
                if not cur.fetchone():
                    flash("You are not a member of this stokvel.")
                    return redirect('/payouts')

                # For simplicity, directly record as completed.
                # In a real app, this would be a 'pending' status requiring approval.
                cur.execute("""
                    INSERT INTO transactions (user_id, stokvel_id, amount, type, description, transaction_date, status)
                    VALUES (%s, %s, %s, 'payout', %s, CURRENT_DATE, 'completed')
                """, (user_id, stokvel_id, amount, description))
                conn.commit()

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
    user_id = session['user_id']
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, target_amount, current_amount, target_date, status, created_at
                    FROM savings_goals
                    WHERE user_id = %s
                    ORDER BY target_date ASC
                """, (user_id,))
                goals = cur.fetchall()

        return render_template('savings_goals.html', goals=goals)
    except Exception as e:
        print(f"Savings goals page error: {e}")
        flash("An error occurred while loading your savings goals. Please try again.")
        return redirect('/home')

@app.route('/create_savings_goal', methods=['POST'])
@login_required
def create_savings_goal():
    user_id = session['user_id']
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
                """, (user_id, name, target_amount, 0.0, target_date))
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
                cur.execute("SELECT id, name, description, purpose, monthly_contribution, target_amount, target_date, total_pool FROM stokvels WHERE id = %s", (stokvel_id,))
                stokvel_tuple = cur.fetchone()
                print(f"DEBUG: Stokvel query result: {stokvel_tuple}") # Debug log

                if not stokvel_tuple:
                    flash("Stokvel not found.")
                    print(f"DEBUG: Stokvel with id {stokvel_id} not found.") # Debug log
                    return redirect('/stokvels')

                # Convert stokvel tuple to a dictionary
                stokvel_keys = ['id', 'name', 'description', 'purpose', 'monthly_contribution', 'target_amount', 'target_date', 'total_pool']
                stokvel = dict(zip(stokvel_keys, stokvel_tuple))
                print(f"DEBUG: Converted stokvel dict: {stokvel}") # Debug log

                # Get members of the stokvel, including their role and member_id
                cur.execute("""
                    SELECT u.username, u.email, sm.role, sm.id as member_id
                    FROM users u
                    JOIN stokvel_members sm ON u.firebase_uid = sm.user_id
                    WHERE sm.stokvel_id = %s
                """, (stokvel_id,))
                members_tuples = cur.fetchall()
                print(f"DEBUG: Members query result: {members_tuples}") # Debug log

                # Convert members tuples to a list of dictionaries
                members_list = []
                member_keys = ['username', 'email', 'role', 'member_id']
                for member_tuple in members_tuples:
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
    user_id = session['user_id']
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, type, details, is_default, created_at
                    FROM payment_methods
                    WHERE user_id = %s
                    ORDER BY is_default DESC, id DESC
                """, (user_id,))
                methods = cur.fetchall()
                
                # Convert tuples to dictionaries
                payment_methods_list = []
                for method in methods:
                    payment_methods_list.append({
                        'id': method[0],
                        'type': method[1],
                        'details': method[2],
                        'is_default': method[3],
                        'created_at': method[4]
                    })
                
        return render_template('payment_methods.html', payment_methods=payment_methods_list)
    except Exception as e:
        print(f"Payment methods page error: {e}")
        flash("An error occurred while loading payment methods. Please try again.")
        return redirect('/home')

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
    user_settings = {}
    try:
        # Fetch user settings from database
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT notification_preferences, two_factor_enabled FROM users WHERE firebase_uid = %s", (user_id,))
                settings_data = cur.fetchone()
                if settings_data:
                    user_settings['notification_preferences'] = settings_data[0]
                    user_settings['two_factor_enabled'] = settings_data[1]
                else:
                    # Provide default settings if not found
                    user_settings['notification_preferences'] = 'email'
                    user_settings['two_factor_enabled'] = False
        return render_template('settings.html', user_settings=user_settings)
    except Exception as e:
        print(f"Error loading settings: {e}")
        flash("An error occurred while loading settings. Please try again.")
        return redirect('/home')

@app.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    user_id = session['user_id']
    notification_preferences = request.form.get('notification_preferences')
    two_factor_enabled = request.form.get('two_factor_enabled') == 'on' # Checkbox

    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users
                    SET notification_preferences = %s, two_factor_enabled = %s
                    WHERE firebase_uid = %s
                """, (notification_preferences, two_factor_enabled, user_id))
                conn.commit()
        flash("Settings updated successfully!")
        return redirect('/settings')
    except Exception as e:
        print(f"Error updating settings: {e}")
        flash("An error occurred while updating settings. Please try again.")
        return redirect('/settings')


def get_user_settings(user_id):
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT notification_preferences, two_factor_enabled FROM users WHERE firebase_uid = %s", (user_id,))
                settings_data = cur.fetchone()
                if settings_data:
                    return {
                        'notification_preferences': settings_data[0],
                        'two_factor_enabled': settings_data[1]
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
    user_id = session['user_id'] # This is now firebase_uid
    query = "SELECT username, email FROM users WHERE firebase_uid = %s"
    user_data = support.execute_query("search", query, (user_id,))
    
    if user_data:
        # Also fetch Firebase user data for email verification status
        try:
            firebase_user = auth.get_user(user_id)
            is_verified = firebase_user.email_verified
        except Exception as e:
            print(f"Error fetching Firebase user for profile: {e}")
            is_verified = False # Assume not verified if error

        user = {
            'username': user_data[0][0],
            'email': user_data[0][1],
            'is_verified': is_verified
        }
        return render_template('profile.html', user=user)
    else:
        flash("Error fetching user data from local DB. Please try logging in again.")
        return redirect('/home')

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    user_id = session['user_id'] # This is now firebase_uid
    username = request.form.get('username')
    email = request.form.get('email')
    # Password change is now handled by Firebase client-side or specific Firebase Admin SDK methods

    try:
        # Update Firebase user profile
        auth.update_user(
            user_id,
            email=email,
            display_name=username
        )
        
        # Update username and email in your local PostgreSQL database
        # Removed password field from update, as Firebase handles password management
        query = "UPDATE users SET username = %s, email = %s WHERE firebase_uid = %s"
        support.execute_query('insert', query, (username, email, user_id))

        flash("Profile updated successfully!")
        return redirect('/profile')
    except auth.AuthError as e:
        print(f"Firebase Profile Update error: {e.code} - {e.message}")
        flash(f"Error updating profile in Firebase: {e.message}")
        return redirect('/profile')
    except Exception as e:
        flash(f"Error updating profile in local database: {str(e)}")
        return redirect('/profile')

@app.context_processor
def inject_user_name():
    user_name = None
    if 'user_id' in session:
        # Changed to firebase_uid
        user_query = "SELECT username FROM users WHERE firebase_uid = %s"
        user_data = support.execute_query("search", user_query, (session['user_id'],))
        if user_data:
            user_name = user_data[0][0]
    return dict(user_name=user_name)

@app.route('/pricing')
def pricing():
    if 'user_id' in session:
        # Changed to firebase_uid
        cursor = support.db_connection().cursor() # Assuming support.db_connection() returns a connection object directly
        cursor.execute("SELECT username FROM users WHERE firebase_uid = %s", (session['user_id'],))
        user_data = cursor.fetchone()
        cursor.close()
        # Ensure the connection is closed in support.py's context manager or explicitly here
        user_name = user_data[0] if user_data else None
        return render_template('pricing.html', user_name=user_name)
    return render_template('pricing.html', user_name=None)

@app.route('/chat', methods=['POST'])
@login_required
def handle_chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400

        user_message = data['message'].lower()
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401

        # Get user context from database
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Get user info by firebase_uid
                cur.execute("SELECT username FROM users WHERE firebase_uid = %s", (user_id,))
                user = cur.fetchone()
                if not user:
                    return jsonify({'error': 'User not found'}), 404
                
                username = user[0]
                
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

        # Simple rule-based response system
        response = "I'm not sure how to help with that. You can ask me about your savings, stokvels, or recent transactions."

        if "how much" in user_message and "saved" in user_message:
            response = f"You have saved R{total_saved} in total across all your stokvels."
        
        elif "stokvel" in user_message:
            if stokvels:
                stokvel_list = "\n".join([f"- {s[0]}: R{s[1]} monthly" for s in stokvels])
                response = f"You are a member of these stokvels:\n{stokvel_list}"
            else:
                response = "You are not currently a member of any stokvels."
        
        elif "recent" in user_message and "transaction" in user_message:
            if transactions:
                transaction_list = "\n".join([f"- {t[1]}: R{t[0]} ({t[2]}) on {t[3]}" for t in transactions])
                response = f"Your recent transactions:\n{transaction_list}"
            else:
                response = "You don't have any recent transactions."
        
        elif "hello" in user_message or "hi" in user_message:
            response = f"Hello {username}! How can I help you today? You can ask me about your savings, stokvels, or recent transactions."

        return jsonify({'response': response})

    except Exception as e:
        print(f"Error in handle_chat: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
