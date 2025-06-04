from flask import Flask, render_template, request, redirect, session, flash, jsonify
import os
from datetime import timedelta  # used for setting session timeout
import pandas as pd
import plotly
import plotly.express as px
import json
import warnings
import support

warnings.filterwarnings("ignore")

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)


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
def home():
    if 'user_id' in session:  # if user is logged-in
        query = """select * from users where id = {} """.format(session['user_id'])
        userdata = support.execute_query("search", query)

        table_query = """select id, user_id, date, category, amount, notes from expenses where user_id = %s order by date desc"""
        table_data = support.execute_query("search", table_query, params=(session['user_id'],))
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
                               user_name=userdata[0][1],
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


@app.route('/analysis')
def analysis():
    if 'user_id' in session:  # if already logged-in
        query = """select * from user_login where user_id = {} """.format(session['user_id'])
        userdata = support.execute_query('search', query)
        query2 = """select pdate,expense, pdescription, amount from user_expenses where user_id = {}""".format(
            session['user_id'])

        data = support.execute_query('search', query2)
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
    else:  # if not logged-in
        return redirect('/')


@app.route('/login')
def login():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)
    if 'user_id' in session:  # if logged-in
        flash("Already a user is logged-in!")
        return redirect('/home')
    else:  # if not logged-in
        return render_template("login.html")


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully!")
    return redirect('/')


@app.route('/login_validation', methods=['POST'])
def login_validation():
    if 'user_id' not in session:
        email = request.form.get('email')
        passwd = request.form.get('password')
        
        # First check if user exists
        query = "SELECT * FROM users WHERE email = %s"
        users = support.execute_query("search", query, (email,))
        
        if len(users) > 0:
            # Then verify password
            if users[0][3] == passwd:  # Assuming password is in the 4th column
                session['user_id'] = users[0][0]
                flash("Login successful!")
                return redirect('/home')
        
        flash("Invalid email or password!")
        return redirect('/login')
    else:
        flash("Already logged in!")
        return redirect('/home')


@app.route('/register')
def register():
    if 'user_id' in session:  # if user is logged-in
        flash("Already a user is logged-in!")
        return redirect('/home')
    else:  # if not logged-in
        return render_template("register.html")


@app.route('/registration', methods=['POST'])
def registration():
    if 'user_id' not in session:
        username = request.form.get('username')
        email = request.form.get('email')
        passwd = request.form.get('password')
        if len(username) > 5 and len(email) > 10 and len(passwd) > 5:
            try:
                query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
                support.execute_query('insert', query, (username, email, passwd))

                user = support.execute_query('search',
                    "SELECT * FROM users WHERE email = %s", (email,))
                session['user_id'] = user[0][0]
                flash("Successfully Registered!!")
                return redirect('/home')
            except Exception as e:
                print(f"Registration error: {e}")
                flash("Email id already exists, use another email!!")
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
    return redirect('/register')


@app.route('/home/add_expense', methods=['POST'])
def add_expense():
    if 'user_id' in session:
        # Get data from the form
        e_date = request.form.get('e_date')
        e_type = request.form.get('e_type')
        amount = request.form.get('amount')
        notes = request.form.get('notes')
        user_id = session['user_id']

        # Validate data (optional but recommended)
        if not all([e_date, e_type, amount, notes]):
            flash("All fields are required to add an expense record!", "warning")
            return redirect('/home')

        try:
            # Convert amount to appropriate type (e.g., float or integer)
            amount = float(amount) # or int(amount) depending on your database schema

            # Prepare and execute the insert query
            # Assuming your expenses table has columns: user_id, date, category, amount, notes
            query = """
            INSERT INTO expenses (user_id, date, category, amount, notes)
            VALUES (%s, %s, %s, %s, %s)
            """
            support.execute_query('insert', query, (user_id, e_date, e_type, amount, notes))

            flash("Expense record added successfully!", "success")
            return redirect('/home')

        except Exception as e:
            print(f"Error adding expense record: {e}")
            flash("An error occurred while adding the expense record.", "danger")
            return redirect('/home')
    else:
        flash("You need to be logged in to add expense records.", "warning")
        return redirect('/login') # Redirect to login if user is not in session


@app.route('/profile')
def profile():
    if 'user_id' in session:
        return render_template('profile.html', active_page='profile')
    else:
        flash("You need to be logged in to view your profile.", "warning")
        return redirect('/login')


if __name__ == "__main__":
    app.run(debug=True)
