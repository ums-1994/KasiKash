from flask import Flask, render_template, request, redirect, session, flash, jsonify
import os
from datetime import timedelta  # used for setting session timeout
import pandas as pd
import plotly
import plotly.express as px
import json
import warnings
import support
import bcrypt

warnings.filterwarnings("ignore")

app = Flask(__name__)
app.secret_key = os.urandom(24)


@app.route('/')
def welcome():
    return render_template("welcome.html")


@app.route('/login')
def login():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)
    if 'user_id' in session:  # if logged-in
        flash("Already a user is logged-in!")
        return redirect('/home')
    else:  # if not logged-in
        return render_template("login.html")


@app.route('/login_validation', methods=['POST'])
def login_validation():
    if 'user_id' not in session:  # if user not logged-in
        email_or_username = request.form.get('email_or_username') # Changed to accept username or email
        password = request.form.get('password')

        # Attempt to fetch user by username first
        query = """SELECT id, username, password FROM users WHERE username = %s"""
        user = support.execute_query(query, params=(email_or_username,), fetch=True)

        # If no user found by username, attempt to fetch by email
        if not user:
            query = """SELECT id, username, password FROM users WHERE email = %s"""
            user = support.execute_query(query, params=(email_or_username,), fetch=True)

        if user and bcrypt.checkpw(password.encode('utf-8'), user[0][2].encode('utf-8')):
            session['user_id'] = user[0][0]  # set session user id
            session['username'] = user[0][1] # set session username
            flash('Login successful!', 'success')
            return redirect('/home')
        else:
            flash('Invalid username/email or password', 'danger')
            return redirect('/login')


@app.route('/reset', methods=['POST'])
def reset():
    if 'user_id' not in session:
        email = request.form.get('femail')
        pswd = request.form.get('pswd')
        userdata = support.execute_query('select * from users where email = %s', params=(email,), fetch=True)
        if len(userdata) > 0:
            try:
                query = """update users set password = %s where email = %s"""
                support.execute_query(query, params=(pswd, email))
                flash("Password has been changed!!")
                return redirect('/login')
            except:
                flash("Something went wrong!!")
                return redirect('/login')
        else:
            flash("Invalid email address!!")
            return redirect('/login')
    else:
        return redirect('/home')


@app.route('/register')
def register():
    if 'user_id' in session:  # if user is logged-in
        flash("Already a user is logged-in!")
        return redirect('/home')
    else:  # if not logged-in
        return render_template("register.html")


@app.route('/register_validation', methods=['POST'])
def register_validation():
    if 'user_id' not in session:  # if user not logged-in
        username = request.form.get('username') # Get username from form
        email = request.form.get('email')
        passwd = request.form.get('password')

        # Check if username or email already exists
        existing_user = support.execute_query(
            """SELECT id FROM users WHERE username = %s OR email = %s""",
            params=(username, email), fetch=True)

        if existing_user:
            flash('Username or Email already exists. Please use different credentials.', 'danger')
            return redirect('/register')

        # Hash password
        hashed_password = bcrypt.hashpw(passwd.encode('utf-8'), bcrypt.gensalt())

        # Insert new user into database
        query = """INSERT INTO users(username, email, password) VALUES(%s,%s,%s)"""
        support.execute_query(query, params=(username, email, hashed_password.decode('utf-8')))

        # Fetch the newly created user to get the id and username
        new_user = support.execute_query(
            """SELECT id, username FROM users WHERE username = %s""",
            params=(username,), fetch=True)

        if new_user:
            session['user_id'] = new_user[0][0]  # set session on successful registration
            session['username'] = new_user[0][1] # set session username
            flash('Registration successful!', 'success')
            return redirect('/home')
        else:
            flash('Registration failed. Please try again.', 'danger')
            return redirect('/register')

    else:
        flash("Already logged in!", 'info')
        return redirect('/home')


@app.route('/contact')
def contact():
    return render_template("contact.html")


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
def home():
    if 'user_id' in session:  # if user is logged-in
        query = """select * from users where id = %s """
        userdata = support.execute_query(query, params=(session['user_id'],), fetch=True)

        # Explicitly select the 6 columns that should match the DataFrame columns
        # Assuming the expenses table has columns: id, user_id, date, category, amount, notes
        table_query = """select id, user_id, date, category, amount, notes from expenses where user_id = %s order by date desc"""
        table_data = support.execute_query(table_query, params=(session['user_id'],), fetch=True)

        # Match the DataFrame column names to the selected database columns
        # The '#' column in the original DataFrame names seems to be the row index in the table display,
        # which is not a database column needed for the DataFrame construction itself.
        # We will use the actual column names from the select query.
        df = pd.DataFrame(table_data, columns=['id', 'user_id', 'Date', 'Expense', 'Amount', 'Note'])

        df = support.generate_df(df)
        try:
            earning, spend, invest, saving = support.top_tiles(df)
        except:
            earning, spend, invest, saving = 0, 0, 0, 0

        try:
            bar, pie, line, stack_bar = support.generate_Graph(df)
        except:
            bar, pie, line, stack_bar = None, None, None, None
        try:
            monthly_data = support.get_monthly_data(df, res=None)
        except:
            monthly_data = []
        try:
            card_data = support.sort_summary(df)
        except:
            card_data = []

        try:
            goals = support.expense_goal(df)
        except:
            goals = []
        try:
            size = 240
            pie1 = support.makePieChart(df, 'Earning', 'Month_name', size=size)
            pie2 = support.makePieChart(df, 'Spend', 'Day_name', size=size)
            pie3 = support.makePieChart(df, 'Investment', 'Year', size=size)
            pie4 = support.makePieChart(df, 'Saving', 'Note', size=size)
            pie5 = support.makePieChart(df, 'Saving', 'Day_name', size=size)
            pie6 = support.makePieChart(df, 'Investment', 'Note', size=size)
        except:
            pie1, pie2, pie3, pie4, pie5, pie6 = None, None, None, None, None, None

        # Placeholder data for new dashboard elements
        active_stokvels = 3 # Example value
        upcoming_payments = [ # Example data structure
            {'stokvel_name': 'Ubuntu Savings Circle', 'due_date': '01 Feb 2024', 'amount': 1200},
            {'stokvel_name': 'Festive Season Fund', 'due_date': '05 Feb 2024', 'amount': 800},
            {'stokvel_name': 'Property Investment Club', 'due_date': '10 Feb 2024', 'amount': 2000},
        ]
        next_payout_date = "Apr 15" # Example value
        next_payout_amount = 14400 # Example value


        return render_template('home.html',
                               user_name=userdata[0][1], # Assuming username is at index 1 in the users table
                               df_size=df.shape[0],
                               df=jsonify(df.to_json()),
                               earning=earning,
                               spend=spend,
                               invest=invest,
                               saving=saving,
                               monthly_data=monthly_data,
                               card_data=card_data,
                               goals=goals,
                               table_data=table_data, # Pass the full table_data
                               bar=bar,
                               line=line,
                               stack_bar=stack_bar,
                               pie1=pie1,
                               pie2=pie2,
                               pie3=pie3,
                               pie4=pie4,
                               pie5=pie5,
                               pie6=pie6,
                               active_stokvels=active_stokvels, # Pass placeholder data
                               upcoming_payments=upcoming_payments, # Pass placeholder data
                               next_payout_date=next_payout_date, # Pass placeholder data
                               next_payout_amount=next_payout_amount # Pass placeholder data
                               )
    else:  # if not logged-in
        return redirect('/')


@app.route('/home/add_expense', methods=['POST'])
def add_expense():
    if 'user_id' in session:
        user_id = session['user_id']
        if request.method == 'POST':
            date = request.form.get('e_date')
            expense = request.form.get('e_type')
            amount = request.form.get('amount')
            notes = request.form.get('notes')
            try:
                query = """INSERT INTO expenses (user_id, date, category, amount, notes) VALUES (%s, %s, %s, %s, %s)"""
                support.execute_query(query, params=(user_id, date, expense, amount, notes))
                flash("Saved!!")
            except Exception as e:
                flash("Something went wrong.")
                print(f"Add expense error: {e}") # Log the error for debugging
                return redirect("/home")
            return redirect('/home')
    else:
        return redirect('/')


@app.route('/analysis')
def analysis():
    if 'user_id' in session:  # if already logged-in
        query = """select * from users where id = %s """
        userdata = support.execute_query(query, params=(session['user_id'],), fetch=True)
        # Note: Updated column names based on new schema
        query2 = """select date, category, notes, amount from expenses where user_id = %s"""

        data = support.execute_query(query2, params=(session['user_id'],), fetch=True)
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
                                   user_name=userdata[0][1], # Assuming username is at index 1
                                   pie=pie,
                                   bar=bar,
                                   line=line,
                                   scatter=scatter,
                                   heat=heat,
                                   month_bar=month_bar,
                                   sun=sun
                                   )
        else:
            flash("No data records to analyze.")
            return redirect('/home')

    else:  # if not logged-in
        return redirect('/')


@app.route('/profile')
def profile():
    if 'user_id' in session:  # if logged-in
        query = """select * from users where id = %s """
        userdata = support.execute_query(query, params=(session['user_id'],), fetch=True)
        return render_template('profile.html', user_name=userdata[0][1], email=userdata[0][2]) # Assuming username at 1, email at 2
    else:  # if not logged-in
        return redirect('/')


@app.route("/updateprofile", methods=['POST'])
def update_profile():
    name = request.form.get('name')
    email = request.form.get("email")
    # Fetch current user data
    query_current = """select * from users where id = %s """
    userdata = support.execute_query(query_current, params=(session['user_id'],), fetch=True)
    
    # Check if the new email already exists for another user
    query_email_exists = """select * from users where email = %s AND id != %s"""
    email_exists = support.execute_query(query_email_exists, params=(email, session['user_id']), fetch=True)
    
    if email_exists:
        flash("Email already exists, try another!!")
        return redirect('/profile')

    # Update username and/or email if they have changed
    if name != userdata[0][1] or email != userdata[0][2]:
        if name != userdata[0][1] and email != userdata[0][2]:
            query_update = """UPDATE users SET username = %s, email = %s WHERE id = %s"""
            support.execute_query(query_update, params=(name, email, session['user_id']))
            flash("Name and Email updated!!")
        elif name != userdata[0][1]:
            query_update = """UPDATE users SET username = %s WHERE id = %s"""
            support.execute_query(query_update, params=(name, session['user_id']))
            flash("Name updated!!")
        elif email != userdata[0][2]:
             query_update = """UPDATE users SET email = %s WHERE id = %s"""
             support.execute_query(query_update, params=(email, session['user_id']))
             flash("Email updated!!")
    else:
        flash("No Change!!")
        
    return redirect('/profile')


@app.route('/logout')
def logout():
    try:
        session.pop("user_id")  # delete the user_id in session (deleting session)
        return redirect('/')
    except:  # if already logged-out but in another tab still logged-in
        return redirect('/')

def init_db():
    with support.db_connection() as conn:
        with conn.cursor() as cursor:
            # Drop existing tables (optional, but good for development resets)
            cursor.execute("DROP TABLE IF EXISTS expenses CASCADE")
            cursor.execute("DROP TABLE IF EXISTS users CASCADE")

            # Create users table
            cursor.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")

            # Create expenses table
            cursor.execute("""
            CREATE TABLE expenses (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                amount DECIMAL(10,2) NOT NULL,
                category VARCHAR(50) NOT NULL,
                date DATE NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            conn.commit() # Commit the schema changes
    print("Database schema initialized")


if __name__ == "__main__":
    init_db()  # Initialize database schema
    app.run(debug=True)
