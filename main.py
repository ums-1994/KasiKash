from flask import Flask, render_template, request, redirect, session, flash, jsonify, url_for
import os
from datetime import timedelta  # used for setting session timeout
import pandas as pd
import plotly
import plotly.express as px
import json
import warnings
import support
import datetime

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
    if 'user_id' in session:
        user_id = session['user_id']

        # Fetch user data
        # Explicitly select username to avoid dependency on column order
        user_query = "SELECT username FROM users WHERE id = %s"
        # Corrected call to execute_query
        user_data = support.execute_query("search", user_query, (user_id,))
        user_name = user_data[0][0] if user_data else "User" # Default to "User" if not found

        # Fetch user's stokvel memberships and associated stokvels
        # This query gets the stokvel details the user is a member of
        memberships_query = """
            SELECT sm.stokvel_id, s.name, s.monthly_contribution, s.total_pool, s.target_amount, s.target_date
            FROM stokvel_members sm
            JOIN stokvels s ON sm.stokvel_id = s.id
            WHERE sm.user_id = %s
        """
        # Corrected call to execute_query
        memberships_data = support.execute_query("search", memberships_query, (user_id,))

        active_stokvels = len(memberships_data)
        # Calculate total monthly contribution based on memberships
        total_monthly_contribution = sum([row[2] for row in memberships_data if row[2] is not None])

        # Calculate Total Saved (sum of user's contributions across all stokvels)
        # Filters by user, transaction type 'contribution', and status 'completed'
        total_saved_query = """
            SELECT SUM(amount) FROM transactions
            WHERE user_id = %s AND type = 'contribution' AND status = 'completed'
        """
        # Corrected call to execute_query
        total_saved_data = support.execute_query("search", total_saved_query, (user_id,))
        # SUM returns None if there are no matching rows, so handle that case
        total_saved = total_saved_data[0][0] if total_saved_data and total_saved_data[0] and total_saved_data[0][0] is not None else 0

        # Fetch Recent Activity (latest transactions for the user)
        # Joins with stokvels to get the stokvel name for the transaction
        recent_activity_query = """
            SELECT t.amount, t.transaction_date, t.description, s.name as stokvel_name, t.type
            FROM transactions t
            JOIN stokvels s ON t.stokvel_id = s.id
            WHERE t.user_id = %s
            ORDER BY t.transaction_date DESC
            LIMIT 5
        """
        # Corrected call to execute_query
        recent_activity_data = support.execute_query("search", recent_activity_query, (user_id,))

        recent_transactions = []
        if recent_activity_data:
            for row in recent_activity_data:
                # Format data for the template
                recent_transactions.append({
                    'amount': row[0],
                    # Ensure row[1] is not None before calling strftime
                    'date': row[1].strftime('%d %b %Y') if row[1] else "N/A",
                    'description': row[2] if row[2] is not None else "N/A",
                    'stokvel_name': row[3] if row[3] is not None else "N/A",
                    'type': row[4] if row[4] is not None else "N/A"
                })

        # Determine Next Payout and Upcoming Payments (Simplified Placeholder Logic)
        # IMPORTANT: This logic is simplified. A real stokvel app needs robust scheduling.
        # This finds the single nearest future transaction marked as 'payout' for the user.
        next_payout_query = """
            SELECT t.transaction_date, t.amount, s.name
            FROM transactions t
            JOIN stokvels s ON t.stokvel_id = s.id
            WHERE t.user_id = %s AND t.type = 'payout' AND t.transaction_date >= CURRENT_DATE
            ORDER BY t.transaction_date ASC
            LIMIT 1
        """
        # Corrected call to execute_query
        next_payout_data = support.execute_query("search", next_payout_query, (user_id,))
        # Format next payout date and amount, handling cases where no payout is found
        next_payout_date = next_payout_data[0][0].strftime('%b %d') if next_payout_data and next_payout_data[0] and next_payout_data[0][0] else "N/A"
        next_payout_amount = next_payout_data[0][1] if next_payout_data and next_payout_data[0] and next_payout_data[0][1] is not None else 0

        # For Upcoming Payments, let's list the monthly contribution amount for each stokvel
        # This is a placeholder. A real app needs a contribution schedule.
        upcoming_payments = []
        for membership in memberships_data:
             upcoming_payments.append({
                 'stokvel_name': membership[1] if membership[1] is not None else "N/A",
                 'amount': membership[2] if membership[2] is not None else 0, # Monthly contribution
                 'due_date': 'Check Stokvel Schedule' # Placeholder text
             })

        # The following variables and logic seem to be from the older expense-tracking
        # dashboard. Assuming you are moving to the stokvel dashboard, these might
        # not be needed or would be calculated differently. Passing placeholders
        # to avoid template errors if dashboard.html still expects them.
        df_size = 0 # Placeholder
        df = jsonify({}) # Placeholder (should pass a pandas DataFrame if needed)
        earning, spend, invest, saving = 0, 0, 0, 0 # Placeholders
        monthly_data = [] # Placeholder
        card_data = [] # Placeholder
        goals = [] # Placeholder
        # CORRECTED CALL HERE:
        table_query = "select id, user_id, date, category, amount, notes from expenses where user_id = %s order by date desc"
        table_data = support.execute_query("search", table_query, (user_id,)) # Corrected call

        bar, line, stack_bar = None, None, None # Placeholders for graphs
        pie1, pie2, pie3, pie4, pie5, pie6 = None, None, None, None, None, None # Placeholders for pie charts


        # Render the dashboard template, passing all the collected data
        return render_template('dashboard.html',
                               user_name=user_name,
                               total_saved=total_saved,
                               monthly_contribution=total_monthly_contribution,
                               active_stokvels=active_stokvels,
                               next_payout_date=next_payout_date,
                               next_payout_amount=next_payout_amount,
                               upcoming_payments=upcoming_payments,
                               recent_transactions=recent_transactions,
                               # Include placeholders for older variables if the template expects them
                               df_size=df_size,
                               df=df,
                               earning=earning,
                               spend=spend,
                               invest=invest,
                               saving=saving,
                               monthly_data=monthly_data,
                               card_data=card_data,
                               goals=goals,
                               table_data=table_data,
                               bar=bar,
                               line=line,
                               stack_bar=stack_bar,
                               pie1=pie1,
                               pie2=pie2,
                               pie3=pie3,
                               pie4=pie4,
                               pie5=pie5,
                               pie6=pie6,
                               )
    else:
        # If user is not logged in, redirect to the welcome/landing page
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
    return redirect('/login')


@app.route('/stokvels')
def stokvels():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    # Get user's stokvels - Explicitly select columns by name
    query = """
        SELECT
            s.id,
            s.name,
            s.description,
            s.monthly_contribution,
            s.total_pool,
            s.target_amount,
            s.target_date,
            s.created_at,
            s.created_by,
            sm.role
        FROM stokvels s
        JOIN stokvel_members sm ON s.id = sm.stokvel_id
        WHERE sm.user_id = %s
    """
    # Fetch data
    stokvel_data = support.execute_query('search', query, (user_id,))

    # Convert list of tuples to list of dictionaries for easier template access
    stokvels_list = []
    # Define column names corresponding to the SELECT statement
    columns = [
        'id', 'name', 'description', 'monthly_contribution', 'total_pool',
        'target_amount', 'target_date', 'created_at', 'created_by', 'role'
    ]
    if stokvel_data:
        for row in stokvel_data:
            stokvels_list.append(dict(zip(columns, row)))

    return render_template('stokvels.html', stokvels=stokvels_list)


@app.route('/create_stokvel', methods=['POST'])
def create_stokvel():
    if 'user_id' not in session:
        return redirect('/login')

    name = request.form.get('name')
    description = request.form.get('description')
    monthly_contribution = request.form.get('monthly_contribution')
    target_amount = request.form.get('target_amount')
    target_date = request.form.get('target_date')

    try:
        query = """
            INSERT INTO stokvels (name, description, monthly_contribution, target_amount, target_date, created_by)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """
        stokvel_id_result = support.execute_query('insert', query, (
            name, description, monthly_contribution, target_amount, target_date, session['user_id']
        ))
        stokvel_id = stokvel_id_result[0] if stokvel_id_result else None

        if stokvel_id:
            # Add creator as admin member
            member_query = """
                INSERT INTO stokvel_members (stokvel_id, user_id, role)
                VALUES (%s, %s, 'admin')
            """
            support.execute_query('insert', member_query, (stokvel_id, session['user_id']))

            flash('Stokvel created successfully!')
            return redirect('/stokvels')
        else:
            flash('Error creating stokvel: Could not retrieve stokvel ID.')
            return redirect('/stokvels')

    except Exception as e:
        flash('Error creating stokvel: ' + str(e))
        return redirect('/stokvels')


@app.route('/contributions')
def contributions():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    # Get user's contributions - Explicitly select columns by name
    contributions_query = """
        SELECT
            t.id,
            t.stokvel_id,
            t.user_id,
            t.type,
            t.amount,
            t.status,
            t.description,
            t.transaction_date,
            s.name as stokvel_name
        FROM transactions t
        JOIN stokvels s ON t.stokvel_id = s.id
        WHERE t.user_id = %s AND t.type = 'contribution'
        ORDER BY t.transaction_date DESC
    """
    contributions_data = support.execute_query('search', contributions_query, (user_id,))

    # Convert list of tuples to list of dictionaries for easier template access
    contributions_list = []
    columns = [
        'id', 'stokvel_id', 'user_id', 'type', 'amount', 'status',
        'description', 'transaction_date', 'stokvel_name'
    ]
    if contributions_data:
        for row in contributions_data:
            # Convert tuple to dictionary
            contribution_dict = dict(zip(columns, row))
            # Ensure transaction_date is a datetime object if it's not none
            # This assumes the database returns datetime objects. If not, parsing might be needed here.

            contributions_list.append(contribution_dict)


    # Get stokvels the user is a member of to populate the dropdown
    stokvels_query = """
        SELECT s.id, s.name
        FROM stokvels s
        JOIN stokvel_members sm ON s.id = sm.stokvel_id
        WHERE sm.user_id = %s
        ORDER BY s.name ASC
    """
    stokvels_list_for_dropdown = support.execute_query('search', stokvels_query, (user_id,))


    return render_template('contributions.html', contributions=contributions_list, stokvels=stokvels_list_for_dropdown) # Pass both lists


@app.route('/make_contribution', methods=['POST'])
def make_contribution():
    if 'user_id' not in session:
        return redirect('/login')

    stokvel_id = request.form.get('stokvel_id')
    amount = request.form.get('amount')
    description = request.form.get('description')

    if not stokvel_id or not amount:
        flash('Stokvel and amount are required for a contribution.')
        return redirect('/contributions')

    try:
        # Create contribution transaction
        query = """
            INSERT INTO transactions (stokvel_id, user_id, type, amount, description)
            VALUES (%s, %s, 'contribution', %s, %s)
        """
        support.execute_query('insert', query, (stokvel_id, session['user_id'], amount, description))

        # Update stokvel total pool
        update_query = """
            UPDATE stokvels
            SET total_pool = total_pool + %s
            WHERE id = %s
        """
        support.execute_query('insert', update_query, (amount, stokvel_id))

        flash('Contribution made successfully!')
        return redirect('/contributions')
    except Exception as e:
        flash('Error making contribution: ' + str(e))
        print(f"Error making contribution: {e}")
        return redirect('/contributions')


@app.route('/payouts')
def payouts():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    # Get user's payouts
    query = """
        SELECT t.*, s.name as stokvel_name
        FROM transactions t
        JOIN stokvels s ON t.stokvel_id = s.id
        WHERE t.user_id = %s AND t.type = 'payout'
        ORDER BY t.transaction_date DESC
    """
    payouts = support.execute_query('search', query, (user_id,))

    # Convert list of tuples to list of dictionaries for easier template access
    payouts_list = []
    columns = [
        'id', 'stokvel_id', 'user_id', 'type', 'amount', 'status',
        'description', 'transaction_date', 'stokvel_name'
    ]
    if payouts:
        for row in payouts:
            payouts_list.append(dict(zip(columns, row)))

    return render_template('payouts.html', payouts=payouts_list)


@app.route('/savings_goals')
def savings_goals():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    # Get user's savings goals - Explicitly select columns by name
    query = """
        SELECT
            id,
            user_id,
            name,
            target_amount,
            current_amount,
            target_date,
            status,
            created_at
        FROM savings_goals
        WHERE user_id = %s
        ORDER BY created_at DESC
    """
    # Fetch data
    goals_data = support.execute_query('search', query, (user_id,))

    # Convert list of tuples to list of dictionaries for easier template access
    goals_list = []
    # Define column names corresponding to the SELECT statement
    columns = [
        'id', 'user_id', 'name', 'target_amount', 'current_amount',
        'target_date', 'status', 'created_at'
    ]
    if goals_data:
        for row in goals_data:
            goals_list.append(dict(zip(columns, row)))

    return render_template('savings_goals.html', goals=goals_list)


@app.route('/create_savings_goal', methods=['POST'])
def create_savings_goal():
    if 'user_id' not in session:
        return redirect('/login')

    name = request.form.get('name')
    target_amount = request.form.get('target_amount')
    target_date = request.form.get('target_date')

    try:
        query = """
            INSERT INTO savings_goals (user_id, name, target_amount, target_date)
            VALUES (%s, %s, %s, %s)
        """
        support.execute_query('insert', query, (session['user_id'], name, target_amount, target_date))

        flash('Savings goal created successfully!')
        return redirect('/savings_goals')
    except Exception as e:
        flash('Error creating savings goal: ' + str(e))
        return redirect('/savings_goals')


@app.route('/stokvel/<int:stokvel_id>/members')
def view_stokvel_members(stokvel_id):
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    # Check if the user is a member of this stokvel
    membership_check_query = """
        SELECT 1 FROM stokvel_members
        WHERE stokvel_id = %s AND user_id = %s
    """
    is_member = support.execute_query('search', membership_check_query, (stokvel_id, user_id))

    if not is_member:
        flash("You are not a member of this stokvel.")
        return redirect('/stokvels')

    # Get stokvel details - explicitly select columns by name
    stokvel_query = """
        SELECT 
            id,
            name,
            description,
            monthly_contribution,
            total_pool,
            target_amount,
            target_date,
            created_at,
            created_by
        FROM stokvels 
        WHERE id = %s
    """
    stokvel_data = support.execute_query('search', stokvel_query, (stokvel_id,))
    
    # Convert tuple to dictionary with explicit column names
    stokvel_columns = [
        'id', 'name', 'description', 'monthly_contribution', 'total_pool',
        'target_amount', 'target_date', 'created_at', 'created_by'
    ]
    stokvel = dict(zip(stokvel_columns, stokvel_data[0])) if stokvel_data else None

    if not stokvel:
        flash("Stokvel not found.")
        return redirect('/stokvels')

    # Get members of the stokvel
    members_query = """
        SELECT sm.id, u.username, u.email, sm.role
        FROM stokvel_members sm
        JOIN users u ON sm.user_id = u.id
        WHERE sm.stokvel_id = %s
    """
    members_data = support.execute_query('search', members_query, (stokvel_id,))

    members_list = []
    if members_data:
        # Assuming columns are id, username, email, role
        member_columns = ['member_id', 'username', 'email', 'role']
        for row in members_data:
            members_list.append(dict(zip(member_columns, row)))

    return render_template('stokvel_members.html', stokvel=stokvel, members=members_list)


@app.route('/stokvel/<int:stokvel_id>/members/add', methods=['POST'])
def add_stokvel_member(stokvel_id):
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    member_email = request.form.get('email')

    # Check if the current user is an admin of this stokvel
    is_admin_query = """
        SELECT 1 FROM stokvel_members
        WHERE stokvel_id = %s AND user_id = %s AND role = 'admin'
    """
    is_admin = support.execute_query('search', is_admin_query, (stokvel_id, user_id))

    if not is_admin:
        flash("You do not have permission to add members to this stokvel.")
        return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))

    # Find the user by email
    find_user_query = "SELECT id FROM users WHERE email = %s"
    user_to_add_data = support.execute_query('search', find_user_query, (member_email,))

    if not user_to_add_data:
        flash(f"User with email {member_email} not found.")
        return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))

    user_to_add_id = user_to_add_data[0][0]

    # Check if user is already a member
    already_member_query = """
        SELECT 1 FROM stokvel_members
        WHERE stokvel_id = %s AND user_id = %s
    """
    already_member = support.execute_query('search', already_member_query, (stokvel_id, user_to_add_id))

    if already_member:
        flash(f"User {member_email} is already a member of this stokvel.")
        return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))

    try:
        # Add the user as a member (default role 'member')
        add_member_query = """
            INSERT INTO stokvel_members (stokvel_id, user_id, role)
            VALUES (%s, %s, 'member')
        """
        support.execute_query('insert', add_member_query, (stokvel_id, user_to_add_id))
        flash(f"User {member_email} added to stokvel successfully!")
    except Exception as e:
        flash(f"Error adding member: {e}")
        print(f"Error adding member: {e}")

    return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))


@app.route('/stokvel/<int:stokvel_id>/members/remove', methods=['POST'])
def remove_stokvel_member(stokvel_id):
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    member_to_remove_id = request.form.get('member_id')

    # Check if the current user is an admin of this stokvel
    is_admin_query = """
        SELECT 1 FROM stokvel_members
        WHERE stokvel_id = %s AND user_id = %s AND role = 'admin'
    """
    is_admin = support.execute_query('search', is_admin_query, (stokvel_id, user_id))

    if not is_admin:
        flash("You do not have permission to remove members from this stokvel.")
        return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))

    # Prevent removing the last admin (optional, but good practice)
    # Count admins
    admin_count_query = """
        SELECT COUNT(*) FROM stokvel_members
        WHERE stokvel_id = %s AND role = 'admin'
    """
    admin_count_data = support.execute_query('search', admin_count_query, (stokvel_id,))
    admin_count = admin_count_data[0][0] if admin_count_data else 0

    # Check if the member to remove is the current user and the last admin
    member_role_query = "SELECT role FROM stokvel_members WHERE id = %s AND stokvel_id = %s"
    member_role_data = support.execute_query('search', member_role_query, (member_to_remove_id, stokvel_id))
    member_role = member_role_data[0][0] if member_role_data else None

    if member_role == 'admin' and admin_count == 1:
        flash("Cannot remove the last admin of the stokvel.")
        return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))

    try:
        # Remove the member
        remove_member_query = """
            DELETE FROM stokvel_members WHERE id = %s AND stokvel_id = %s
        """
        support.execute_query('insert', remove_member_query, (member_to_remove_id, stokvel_id))
        flash("Member removed successfully!")
    except Exception as e:
        flash(f"Error removing member: {e}")
        print(f"Error removing member: {e}")

    return redirect(url_for('view_stokvel_members', stokvel_id=stokvel_id))


@app.route('/stokvel/<int:stokvel_id>/delete', methods=['POST'])
def delete_stokvel(stokvel_id):
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    # Check if the user is an admin of this stokvel
    is_admin_query = """
        SELECT 1 FROM stokvel_members
        WHERE stokvel_id = %s AND user_id = %s AND role = 'admin'
    """
    is_admin = support.execute_query('search', is_admin_query, (stokvel_id, user_id))

    if not is_admin:
        flash("You do not have permission to delete this stokvel.")
        return redirect('/stokvels')

    try:
        # Delete all related records first (transactions and members)
        delete_transactions_query = "DELETE FROM transactions WHERE stokvel_id = %s"
        support.execute_query('insert', delete_transactions_query, (stokvel_id,))

        delete_members_query = "DELETE FROM stokvel_members WHERE stokvel_id = %s"
        support.execute_query('insert', delete_members_query, (stokvel_id,))

        # Finally, delete the stokvel
        delete_stokvel_query = "DELETE FROM stokvels WHERE id = %s"
        support.execute_query('insert', delete_stokvel_query, (stokvel_id,))

        flash("Stokvel deleted successfully!")
    except Exception as e:
        flash(f"Error deleting stokvel: {e}")
        print(f"Error deleting stokvel: {e}")

    return redirect('/stokvels')


@app.route('/payment_methods')
def payment_methods():
    print("Registering /payment_methods route") # Debug print
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    # Get user's payment methods
    query = """
        SELECT id, user_id, type, details, is_default, created_at
        FROM payment_methods
        WHERE user_id = %s
        ORDER BY is_default DESC, created_at DESC
    """
    payment_methods_data = support.execute_query('search', query, (user_id,))

    # Convert to list of dictionaries
    payment_methods_list = []
    columns = ['id', 'user_id', 'type', 'details', 'is_default', 'created_at']
    if payment_methods_data:
        for row in payment_methods_data:
            payment_methods_list.append(dict(zip(columns, row)))

    return render_template('payment_methods.html', payment_methods=payment_methods_list)


@app.route('/add_payment_method', methods=['POST'])
def add_payment_method():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    payment_type = request.form.get('type')
    details = request.form.get('details')
    is_default = request.form.get('is_default') == 'true'

    try:
        # If this is set as default, unset any existing defaults
        if is_default:
            update_query = """
                UPDATE payment_methods
                SET is_default = false
                WHERE user_id = %s
            """
            support.execute_query('insert', update_query, (user_id,))

        # Add the new payment method
        query = """
            INSERT INTO payment_methods (user_id, type, details, is_default)
            VALUES (%s, %s, %s, %s)
        """
        support.execute_query('insert', query, (user_id, payment_type, details, is_default))
        flash('Payment method added successfully!')
    except Exception as e:
        flash(f'Error adding payment method: {e}')
        print(f"Error adding payment method: {e}")

    return redirect('/payment_methods')


@app.route('/set_default_payment_method', methods=['POST'])
def set_default_payment_method():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    payment_method_id = request.form.get('payment_method_id')

    try:
        # First unset all defaults
        update_query = """
            UPDATE payment_methods
            SET is_default = false
            WHERE user_id = %s
        """
        support.execute_query('insert', update_query, (user_id,))

        # Then set the new default
        set_default_query = """
            UPDATE payment_methods
            SET is_default = true
            WHERE id = %s AND user_id = %s
        """
        support.execute_query('insert', set_default_query, (payment_method_id, user_id))
        flash('Default payment method updated successfully!')
    except Exception as e:
        flash(f'Error updating default payment method: {e}')
        print(f"Error updating default payment method: {e}")

    return redirect('/payment_methods')


@app.route('/delete_payment_method', methods=['POST'])
def delete_payment_method():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    payment_method_id = request.form.get('payment_method_id')

    try:
        # Check if this is the default payment method
        check_query = """
            SELECT is_default FROM payment_methods
            WHERE id = %s AND user_id = %s
        """
        result = support.execute_query('search', check_query, (payment_method_id, user_id))
        
        if result and result[0][0]:
            flash('Cannot delete the default payment method. Please set another payment method as default first.')
            return redirect('/payment_methods')

        # Delete the payment method
        delete_query = """
            DELETE FROM payment_methods
            WHERE id = %s AND user_id = %s
        """
        support.execute_query('insert', delete_query, (payment_method_id, user_id))
        flash('Payment method deleted successfully!')
    except Exception as e:
        flash(f'Error deleting payment method: {e}')
        print(f"Error deleting payment method: {e}")

    return redirect('/payment_methods')


if __name__ == "__main__":
    app.run(debug=True)
