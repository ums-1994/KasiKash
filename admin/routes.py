from flask import render_template, request, redirect, session, flash, url_for, jsonify, Response
import support
import psycopg2
import psycopg2.extras
from firebase_admin import auth
from . import admin_bp
from utils import login_required, create_notification
import csv
import pandas as pd
from io import BytesIO
from fpdf import FPDF
from translations import t

def get_user_language():
    return session.get('language_preference', 'en')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    user_language = get_user_language()
    if session.get('role') != 'admin':
        flash(t('error', user_language), 'danger')
        return redirect(url_for('home'))
    
    firebase_uid = session.get('user_id')
    stokvels = []
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Count all stokvel members with a user_id
                cur.execute("SELECT COUNT(*) FROM stokvel_members WHERE user_id IS NOT NULL")
                total_members = cur.fetchone()[0]
                # Count all pending payouts
                cur.execute("SELECT COUNT(*) FROM transactions WHERE type = 'payout' AND status = 'pending'")
                pending_loans = cur.fetchone()[0]
                # KYC and notifications as before
                cur.execute("SELECT COUNT(*) FROM users WHERE (id_document IS NOT NULL AND id_document != '') AND (proof_of_address IS NOT NULL AND proof_of_address != '') AND kyc_approved_at IS NULL")
                kyc_pending = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM notifications WHERE is_read = FALSE")
                new_notifications = cur.fetchone()[0]
                # Fetch stokvels created by the admin
                cur.execute("""
                    SELECT id, name, monthly_contribution, target_date
                    FROM stokvels
                    WHERE created_by = %s
                """, (firebase_uid,))
                stokvels = cur.fetchall()
                # Fetch total deposits
                cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'deposit'")
                total_deposits = cur.fetchone()[0]
        print("Total members:", total_members)
        print("Pending loans:", pending_loans)
        print("KYC pending:", kyc_pending)
        print("New notifications:", new_notifications)
        print("Total deposits:", total_deposits)
    except Exception as e:
        print(f"Error fetching admin dashboard data: {e}")
        total_members, pending_loans, kyc_pending, new_notifications, total_deposits = 0, 0, 0, 0, 0
        stokvels = []

    return render_template(
        'admin_dashboard.html', 
        total_members=total_members, 
        pending_loans=pending_loans, 
        kyc_pending=kyc_pending, 
        new_notifications=new_notifications,
        stokvels=stokvels,
        total_deposits=total_deposits
    )

@admin_bp.route('/manage-users')
@login_required
def manage_users():
    user_language = get_user_language()
    if session.get('role') != 'admin':
        flash(t('error', user_language), 'danger')
        return redirect(url_for('home'))

    search_query = request.args.get('search', '')
    users = []
    stokvels = []
    try:
        with support.db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Fetch users with their stokvel name (if any)
                if search_query:
                    cur.execute("""
                        SELECT u.id, u.username, u.email, u.role, u.created_at, u.last_login, s.name AS stokvel_name
                        FROM users u
                        LEFT JOIN stokvel_members sm ON u.id = sm.user_id
                        LEFT JOIN stokvels s ON sm.stokvel_id = s.id
                        WHERE u.username ILIKE %s OR u.email ILIKE %s
                        ORDER BY u.created_at DESC
                    """, (f'%{search_query}%', f'%{search_query}%'))
                else:
                    cur.execute("""
                        SELECT u.id, u.username, u.email, u.role, u.created_at, u.last_login, s.name AS stokvel_name
                        FROM users u
                        LEFT JOIN stokvel_members sm ON u.id = sm.user_id
                        LEFT JOIN stokvels s ON sm.stokvel_id = s.id
                        ORDER BY u.created_at DESC
                    """)
                users = cur.fetchall()
                # Fetch all stokvels for the Add User modal
                cur.execute("SELECT id, name FROM stokvels ORDER BY name")
                stokvels = cur.fetchall()
    except Exception as e:
        print(f"Error fetching users or stokvels for admin: {e}")
        flash('Could not load users or stokvels.', 'danger')

    return render_template('admin_manage_users.html', users=users, search_query=search_query, stokvels=stokvels, t=t, user_language=user_language)

@admin_bp.route('/users/add', methods=['POST'])
@login_required
def add_user():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role', 'user')
    stokvel_id = request.form.get('stokvel_id')  # Get stokvel_id from form

    if not all([username, email]):
        return jsonify({'success': False, 'message': 'Username and email are required.'}), 400

    try:
        firebase_uid = None
        # Only create Firebase user if password is provided
        if password:
            user_record = auth.create_user(
                email=email,
                password=password,
                display_name=username,
                email_verified=True
            )
            firebase_uid = user_record.uid
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Insert user and get user_id
                cur.execute(
                    "INSERT INTO users (firebase_uid, username, email, role) VALUES (%s, %s, %s, %s) RETURNING id",
                    (firebase_uid, username, email, role)
                )
                user_id = cur.fetchone()[0]
                # If stokvel_id is provided, insert into stokvel_members
                if stokvel_id:
                    cur.execute(
                        "INSERT INTO stokvel_members (user_id, stokvel_id) VALUES (%s, %s)",
                        (user_id, stokvel_id)
                    )
                conn.commit()
        flash(f'User {username} created successfully!', 'success')
        return jsonify({'success': True})
    except auth.EmailAlreadyExistsError:
        return jsonify({'success': False, 'message': 'An account with this email already exists in Firebase.'}), 409
    except Exception as e:
        print(f"Error adding user from admin: {e}")
        if 'user_record' in locals():
            try:
                auth.delete_user(user_record.uid)
            except Exception:
                pass
        return jsonify({'success': False, 'message': f'An error occurred: {e}'}), 500

@admin_bp.route('/loan-approvals')
@login_required
def loan_approvals():
    user_language = get_user_language()
    if session.get('role') != 'admin':
        flash(t('error', user_language), 'danger')
        return redirect(url_for('home'))

    status = request.args.get('status', 'pending')
    loans = []
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                 cur.execute("""
                    SELECT t.id, u.username, u.email, t.amount, t.status, t.transaction_date, t.description as comment
                    FROM transactions t
                    LEFT JOIN users u ON t.user_id = u.id
                    WHERE t.type = 'payout' AND t.status = %s
                    ORDER BY t.transaction_date DESC
                """, (status,))
                 loans = cur.fetchall()
    except Exception as e:
        print(f"Error fetching loan approvals: {e}")
        flash('Could not load loan approvals.', 'danger')
    return render_template('admin_loan_approvals.html', loans=loans, current_status=status, t=t, user_language=user_language)

@admin_bp.route('/loans/approve', methods=['POST'])
@login_required
def approve_loan():
    if session.get('role') != 'admin':
        flash('Permission denied.', 'danger')
        return redirect(url_for('admin.loan_approvals'))
    
    loan_id = request.form.get('loan_id')
    comment = request.form.get('comment', 'Approved by admin.')
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE transactions SET status = 'approved', description = CONCAT(description, ' | Admin Comment: ', %s) WHERE id = %s", (comment, loan_id,))
                conn.commit()
        flash('Loan approved successfully.', 'success')
    except Exception as e:
        print(f"Error approving loan: {e}")
        flash('Failed to approve loan.', 'danger')
    return redirect(url_for('admin.loan_approvals', status='pending'))

@admin_bp.route('/loans/reject', methods=['POST'])
@login_required
def reject_loan():
    if session.get('role') != 'admin':
        flash('Permission denied.', 'danger')
        return redirect(url_for('admin.loan_approvals'))

    loan_id = request.form.get('loan_id')
    comment = request.form.get('comment', 'Rejected by admin.')
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE transactions SET status = 'rejected', description = CONCAT(description, ' | Admin Comment: ', %s) WHERE id = %s", (comment, loan_id,))
                conn.commit()
        flash('Loan rejected successfully.', 'success')
    except Exception as e:
        print(f"Error rejecting loan: {e}")
        flash('Failed to reject loan.', 'danger')
    return redirect(url_for('admin.loan_approvals', status='pending'))

@admin_bp.route('/loans/undo', methods=['POST'])
@login_required
def undo_loan():
    if session.get('role') != 'admin':
        flash('Permission denied.', 'danger')
        return redirect(url_for('admin.loan_approvals'))

    loan_id = request.form.get('loan_id')
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE transactions SET status = 'pending' WHERE id = %s", (loan_id,))
                conn.commit()
        flash('Loan status reset to pending.', 'success')
    except Exception as e:
        print(f"Error undoing loan status: {e}")
        flash('Failed to undo loan status.', 'danger')
    previous_status = request.referrer.split('status=')[-1] if 'status=' in (request.referrer or '') else 'approved'
    return redirect(url_for('admin.loan_approvals', status=previous_status))

@admin_bp.route('/loans/details/<int:loan_id>')
@login_required
def loan_details(loan_id):
    if session.get('role') != 'admin':
        return "Permission Denied", 403
    try:
        with support.db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT t.*, u.username, u.email, s.name as stokvel_name
                    FROM transactions t
                    LEFT JOIN users u ON t.user_id = u.firebase_uid
                    LEFT JOIN stokvels s ON t.stokvel_id = s.id
                    WHERE t.id = %s
                """, (loan_id,))
                loan = cur.fetchone()
        if not loan:
            return "Loan not found", 404
        return render_template('admin_loan_details_snippet.html', loan=loan)
    except Exception as e:
        print(f"Error fetching loan details: {e}")
        return "Error fetching details", 500

@admin_bp.route('/loans/user_history/<email>')
@login_required
def user_loan_history(email):
    if session.get('role') != 'admin':
        return "Permission Denied", 403
    try:
        with support.db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT firebase_uid, username FROM users WHERE email = %s", (email,))
                user_info = cur.fetchone()
                if not user_info:
                    return "User not found", 404
                user_id, username = user_info['firebase_uid'], user_info['username']
                cur.execute("""
                    SELECT * FROM transactions
                    WHERE user_id = %s AND type = 'payout'
                    ORDER BY transaction_date DESC
                    LIMIT 10
                """, (user_id,))
                history = cur.fetchall()
        return render_template('admin_user_loan_history_snippet.html', history=history, username=username)
    except Exception as e:
        print(f"Error fetching user loan history: {e}")
        return "Error fetching history", 500

@admin_bp.route('/events', methods=['GET', 'POST'])
@login_required
def events():
    user_language = get_user_language()
    if 'user_id' not in session or session.get('role') != 'admin':
        flash(t('error', user_language), 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        stokvel_id = request.form.get('stokvel')
        name = request.form.get('name')
        description = request.form.get('description')
        target_date = request.form.get('target_date')
        send_notification = 'send_notification' in request.form
        try:
            with support.db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO events (stokvel_id, name, description, target_date) VALUES (%s, %s, %s, %s)",
                        (stokvel_id, name, description, target_date)
                    )
                    conn.commit()
                    if send_notification:
                        cur.execute("SELECT user_id FROM stokvel_members WHERE stokvel_id = %s", (stokvel_id,))
                        members = cur.fetchall()
                        for member in members:
                            user_id = member[0]
                            if user_id:
                                message = f"New event '{name}' has been scheduled for your stokvel."
                                link = url_for('home')
                                create_notification(user_id, message, link_url=link, notification_type='event')
            flash('Event created successfully!', 'success')
        except Exception as e:
            print(f"Error creating event: {e}")
            flash('Failed to create event.', 'danger')
        return redirect(url_for('admin.events'))

    events, stokvels = [], []
    try:
        with support.db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT e.*, s.name as stokvel_name FROM events e LEFT JOIN stokvels s ON e.stokvel_id = s.id ORDER BY e.created_at DESC")
                events = cur.fetchall()
                cur.execute("SELECT id, name FROM stokvels ORDER BY name")
                stokvels = cur.fetchall()
    except Exception as e:
        print(f"Error fetching events or stokvels: {e}")
        flash('Could not load page data.', 'danger')
    return render_template('admin_events.html', events=events, stokvels=stokvels, t=t, user_language=user_language)

@admin_bp.route('/memberships', methods=['GET'])
@login_required
def memberships():
    user_language = get_user_language()
    if 'user_id' not in session or session.get('role') != 'admin':
        flash(t('error', user_language), 'danger')
        return redirect(url_for('home'))
    search_query = request.args.get('q', '').strip()
    memberships = []
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                if search_query:
                    cur.execute("SELECT id, name, monthly_contribution, target_amount, total_pool, created_at FROM membership_plans WHERE name ILIKE %s ORDER BY created_at DESC", (f'%{search_query}%',))
                else:
                    cur.execute("SELECT id, name, monthly_contribution, target_amount, total_pool, created_at FROM membership_plans ORDER BY created_at DESC")
                memberships = cur.fetchall()
    except Exception as e:
        print(f"Error fetching membership plans: {e}")
        flash('Could not load membership plans.', 'danger')
    return render_template('admin_memberships.html', memberships=memberships, search_query=search_query, t=t, user_language=user_language)

@admin_bp.route('/memberships/add', methods=['POST'])
@login_required
def add_membership_plan():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('home'))
    name = request.form.get('name')
    monthly_contribution = request.form.get('monthly_contribution')
    target_amount = request.form.get('target_amount')
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO membership_plans (name, monthly_contribution, target_amount) VALUES (%s, %s, %s)", (name, monthly_contribution, target_amount))
                conn.commit()
        flash('Membership plan added successfully!', 'success')
    except Exception as e:
        print(f"Error adding membership plan: {e}")
        flash('Failed to add membership plan.', 'danger')
    return redirect(url_for('admin.memberships'))

@admin_bp.route('/notifications')
@login_required
def notifications():
    user_language = get_user_language()
    if 'user_id' not in session or session.get('role') != 'admin':
        flash(t('error', user_language), 'danger')
        return redirect(url_for('home'))
    return render_template('admin_notifications.html', t=t, user_language=user_language)

@admin_bp.route('/notifications/send', methods=['POST'])
@login_required
def send_notification():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('home'))
    
    notification_type = request.form.get('notification_type', 'stokvel')  # stokvel, all_users, specific_user
    stokvel = request.form.get('stokvel')
    specific_user_email = request.form.get('specific_user_email')
    urgent = request.form.get('urgent') == 'on'
    message = request.form.get('message')
    notif_type = request.form.get('type', 'admin_notification')
    
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                user_ids = []
                
                if notification_type == 'stokvel' and stokvel:
                    # Find all firebase_uid in the selected stokvel
                    cur.execute("""
                        SELECT u.firebase_uid 
                        FROM stokvel_members sm
                        JOIN users u ON sm.user_id = u.id
                        WHERE sm.stokvel_id = (SELECT id FROM stokvels WHERE name = %s)
                        AND u.firebase_uid IS NOT NULL
                    """, (stokvel,))
                    user_ids = cur.fetchall()
                elif notification_type == 'all_users':
                    # Get all firebase_uid
                    cur.execute("SELECT firebase_uid FROM users WHERE firebase_uid IS NOT NULL")
                    user_ids = cur.fetchall()
                elif notification_type == 'specific_user' and specific_user_email:
                    # Get specific firebase_uid
                    cur.execute("SELECT firebase_uid FROM users WHERE email = %s AND firebase_uid IS NOT NULL", (specific_user_email,))
                    user_result = cur.fetchone()
                    if user_result:
                        user_ids = [user_result]
                    else:
                        user_ids = []
                else:
                    user_ids = []
                
                # Send notifications to all target users
                for (firebase_uid,) in user_ids:
                    if firebase_uid:
                        cur.execute("""
                            INSERT INTO notifications (user_id, type, message, created_at) 
                            VALUES (%s, %s, %s, NOW())
                        """, (firebase_uid, notif_type, message))
                
                conn.commit()
                
                # Create success message with count
                recipient_count = len(user_ids)
                if recipient_count == 1:
                    flash(f'Notification sent successfully to 1 user!', 'success')
                else:
                    flash(f'Notification sent successfully to {recipient_count} users!', 'success')
                    
    except Exception as e:
        print(f"Error sending notification: {e}")
        flash('Failed to send notification.', 'danger')
    return redirect(url_for('admin.notifications'))

@admin_bp.route('/kyc-approvals')
@login_required
def kyc_approvals():
    user_language = get_user_language()
    if 'user_id' not in session or session.get('role') != 'admin':
        flash(t('error', user_language), 'danger')
        return redirect(url_for('home'))

    search_query = request.args.get('q', '').strip()
    kyc_users = []
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                if search_query:
                    cur.execute("""
                        SELECT id, email, id_document, proof_of_address, created_at
                        FROM users
                        WHERE (id_document IS NOT NULL AND id_document != '')
                          AND (proof_of_address IS NOT NULL AND proof_of_address != '')
                          AND (email ILIKE %s)
                        ORDER BY created_at DESC
                    """, (f'%{search_query}%',))
                else:
                    cur.execute("""
                        SELECT id, email, id_document, proof_of_address, created_at
                        FROM users
                        WHERE (id_document IS NOT NULL AND id_document != '')
                          AND (proof_of_address IS NOT NULL AND proof_of_address != '')
                        ORDER BY created_at DESC
                    """)
                kyc_users = cur.fetchall()
    except Exception as e:
        import traceback
        print(f"Error fetching KYC approvals: {e}")
        traceback.print_exc()
        flash('Could not load KYC approvals.', 'danger')
    return render_template('admin_kyc_approvals.html', kyc_users=kyc_users, search_query=search_query, debug_kyc_users=kyc_users, t=t, user_language=user_language)

@admin_bp.route('/kyc-approve/<int:user_id>', methods=['POST'])
@login_required
def approve_kyc(user_id):
    if session.get('role') != 'admin':
        flash('Permission denied.', 'danger')
        return redirect(url_for('admin.kyc_approvals'))
    try:
        with support.db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Get email from the provided user_id to ensure we update the correct, active user
                cur.execute("SELECT email, firebase_uid FROM users WHERE id = %s", (user_id,))
                user_data = cur.fetchone()
                if not user_data:
                    flash(f"User with ID {user_id} not found.", "danger")
                    return redirect(url_for('admin.kyc_approvals'))

                email = user_data['email']
                
                # Update the user record using the email, targeting the active, firebase-linked account
                cur.execute("UPDATE users SET kyc_status = 'approved', kyc_verified_at = NOW() WHERE email = %s AND firebase_uid IS NOT NULL", (email,))
                
                # Get the firebase_uid for notification
                cur.execute("SELECT firebase_uid FROM users WHERE email = %s AND firebase_uid IS NOT NULL", (email,))
                user_to_notify = cur.fetchone()

                if user_to_notify and user_to_notify['firebase_uid']:
                    firebase_uid = user_to_notify['firebase_uid']
                    message = "Congratulations! Your KYC documents have been approved. You are now fully verified."
                    link = url_for('profile')
                    create_notification(firebase_uid, message, link_url=link, notification_type='kyc_approved')
                
                conn.commit()
        flash(f'KYC for {email} approved successfully.', 'success')
    except Exception as e:
        print(f"Error approving KYC: {e}")
        flash('Failed to approve KYC.', 'danger')
    return redirect(url_for('admin.kyc_approvals'))

@admin_bp.route('/kyc-reject/<int:user_id>', methods=['POST'])
@login_required
def reject_kyc(user_id):
    if session.get('role') != 'admin':
        flash('Permission denied.', 'danger')
        return redirect(url_for('admin.kyc_approvals'))

    rejection_reason = request.form.get('reason', 'Your documents could not be verified. Please re-upload clear and valid documents.')
    try:
        with support.db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Get email from the provided user_id to ensure we update the correct, active user
                cur.execute("SELECT email, firebase_uid FROM users WHERE id = %s", (user_id,))
                user_data = cur.fetchone()
                if not user_data:
                    flash(f"User with ID {user_id} not found.", "danger")
                    return redirect(url_for('admin.kyc_approvals'))

                email = user_data['email']
                
                # Update the user record using the email, targeting the active, firebase-linked account
                cur.execute("UPDATE users SET kyc_status = 'rejected', kyc_rejection_reason = %s WHERE email = %s AND firebase_uid IS NOT NULL", (rejection_reason, email,))
                
                # Get the firebase_uid for notification
                cur.execute("SELECT firebase_uid FROM users WHERE email = %s AND firebase_uid IS NOT NULL", (email,))
                user_to_notify = cur.fetchone()

                if user_to_notify and user_to_notify['firebase_uid']:
                    firebase_uid = user_to_notify['firebase_uid']
                    message = f"Your KYC submission was rejected. Reason: {rejection_reason}"
                    link = url_for('profile')
                    create_notification(firebase_uid, message, link_url=link, notification_type='kyc_rejected')

                conn.commit()
        flash(f'KYC for {email} rejected successfully.', 'success')
    except Exception as e:
        print(f"Error rejecting KYC: {e}")
        flash('Failed to reject KYC.', 'danger')
    return redirect(url_for('admin.kyc_approvals'))

@admin_bp.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def settings():
    user_language = get_user_language()
    if 'user_id' not in session or session.get('role') != 'admin':
        flash(t('error', user_language), 'danger')
        return redirect(url_for('home'))

    # Ensure the admin_settings table exists
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS admin_settings (
                        id SERIAL PRIMARY KEY,
                        contribution_amount INTEGER,
                        late_penalty INTEGER,
                        grace_period INTEGER,
                        max_loan_percent INTEGER,
                        interest_rate INTEGER,
                        repayment_period INTEGER,
                        language VARCHAR(10),
                        role_management VARCHAR(50),
                        loan_approval_roles TEXT,
                        meeting_frequency VARCHAR(20),
                        meeting_time VARCHAR(5),
                        meeting_reminders BOOLEAN,
                        data_retention VARCHAR(10),
                        enable_2fa BOOLEAN,
                        meeting_day VARCHAR(10)
                    )
                ''')
                # Ensure at least one row exists
                cur.execute('SELECT COUNT(*) FROM admin_settings')
                if cur.fetchone()[0] == 0:
                    cur.execute('''
                        INSERT INTO admin_settings (contribution_amount, late_penalty, grace_period, max_loan_percent, interest_rate, repayment_period, language, role_management, loan_approval_roles, meeting_frequency, meeting_time, meeting_reminders, data_retention, enable_2fa, meeting_day)
                        VALUES (100, 10, 7, 50, 5, 6, 'en', '', '', 'monthly', '14:00', FALSE, '5', FALSE, 'Monday')
                    ''')
                    conn.commit()
    except Exception as e:
        print(f"Error ensuring admin_settings table: {e}")

    if request.method == 'POST':
        contribution_amount = request.form.get('contribution_amount', type=int)
        late_penalty = request.form.get('late_penalty', type=int)
        grace_period = request.form.get('grace_period', type=int)
        max_loan_percent = request.form.get('max_loan_percent', type=int)
        interest_rate = request.form.get('interest_rate', type=int)
        repayment_period = request.form.get('repayment_period', type=int)
        language = request.form.get('language')
        role_management = request.form.get('role_management')
        loan_approval_roles = ','.join(request.form.getlist('loan_approval_roles'))
        meeting_frequency = request.form.get('meeting_frequency')
        meeting_time = request.form.get('meeting_time')
        meeting_reminders = request.form.get('meeting_reminders') == 'on'
        data_retention = request.form.get('data_retention')
        enable_2fa = request.form.get('enable_2fa') == 'on'
        meeting_day = request.form.get('meeting_day')

        try:
            with support.db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('SELECT id FROM admin_settings LIMIT 1')
                    row = cur.fetchone()
                    if row:
                        cur.execute('''
                            UPDATE admin_settings SET
                                contribution_amount=%s,
                                late_penalty=%s,
                                grace_period=%s,
                                max_loan_percent=%s,
                                interest_rate=%s,
                                repayment_period=%s,
                                language=%s,
                                role_management=%s,
                                loan_approval_roles=%s,
                                meeting_frequency=%s,
                                meeting_time=%s,
                                meeting_reminders=%s,
                                data_retention=%s,
                                enable_2fa=%s,
                                meeting_day=%s
                            WHERE id=%s
                        ''', (
                            contribution_amount, late_penalty, grace_period, max_loan_percent, interest_rate, repayment_period,
                            language, role_management, loan_approval_roles, meeting_frequency, meeting_time, meeting_reminders,
                            data_retention, enable_2fa, meeting_day, row[0]
                        ))
                    else:
                        cur.execute('''
                            INSERT INTO admin_settings (
                                contribution_amount, late_penalty, grace_period, max_loan_percent, interest_rate, repayment_period,
                                language, role_management, loan_approval_roles, meeting_frequency, meeting_time, meeting_reminders,
                                data_retention, enable_2fa, meeting_day
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ''', (
                            contribution_amount, late_penalty, grace_period, max_loan_percent, interest_rate, repayment_period,
                            language, role_management, loan_approval_roles, meeting_frequency, meeting_time, meeting_reminders,
                            data_retention, enable_2fa, meeting_day
                        ))
                conn.commit()
            session['language_preference'] = language  # Ensure session is updated for immediate effect
            flash('Settings saved successfully!', 'success')
        except Exception as e:
            flash(f'Error saving settings: {e}', 'danger')
        return redirect(url_for('admin.settings'))

    # Load settings for display
    default_settings = {
        'contribution_amount': 100,
        'late_penalty': 10,
        'grace_period': 7,
        'max_loan_percent': 50,
        'interest_rate': 5,
        'repayment_period': 6,
        'language': 'en',
        'role_management': '',
        'loan_approval_roles': '',
        'meeting_frequency': 'monthly',
        'meeting_time': '14:00',
        'meeting_reminders': False,
        'data_retention': '5',
        'enable_2fa': False,
        'meeting_day': 'Monday'
    }
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM admin_settings LIMIT 1')
                row = cur.fetchone()
                if row:
                    colnames = [desc[0] for desc in cur.description]
                    for i, col in enumerate(colnames):
                        default_settings[col] = row[i]
                    # Convert comma-separated roles to list if needed
                    if 'loan_approval_roles' in default_settings and default_settings['loan_approval_roles']:
                        default_settings['loan_approval_roles'] = default_settings['loan_approval_roles'].split(',')
    except Exception as e:
        flash(f'Error loading settings: {e}', 'danger')

    # Fetch audit logs from the database
    audit_logs = []
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT action, \"user\", target, amount, date FROM audit_logs ORDER BY date DESC LIMIT 20")
                audit_logs = [
                    {
                        'action': row[0],
                        'user': row[1],
                        'target': row[2],
                        'amount': row[3],
                        'date': row[4].strftime('%Y-%m-%d %H:%M') if row[4] else ''
                    }
                    for row in cur.fetchall()
                ]
    except Exception as e:
        print(f"Error fetching audit logs: {e}")

    return render_template(
        'admin_settings.html',
        default_settings=default_settings,
        audit_logs=audit_logs,
        t=t,
        user_language=user_language
    )

@admin_bp.route('/export/members')
@login_required
def export_members():
    export_format = request.args.get('format', 'csv')
    with support.db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT username, email, role, created_at FROM users")
            rows = cur.fetchall()
            columns = ['Username', 'Email', 'Role', 'Created At']
    if export_format == 'csv':
        def generate():
            data = [columns] + list(rows)
            for row in data:
                yield ','.join([str(item) for item in row]) + '\n'
        return Response(generate(), mimetype='text/csv',
                        headers={"Content-Disposition": "attachment;filename=members.csv"})
    elif export_format == 'excel':
        df = pd.DataFrame(rows, columns=columns)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        return Response(output.getvalue(), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        headers={"Content-Disposition": "attachment;filename=members.xlsx"})
    elif export_format == 'pdf':
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        col_width = 40
        # Table header
        for col in columns:
            pdf.cell(col_width, 10, str(col), 1)
        pdf.ln()
        # Table rows
        for row in rows:
            for item in row:
                pdf.cell(col_width, 10, str(item), 1)
            pdf.ln()
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        return Response(pdf_bytes, mimetype='application/pdf',
                        headers={"Content-Disposition": "attachment;filename=members.pdf"})
    else:
        flash('Unsupported export format.', 'danger')
        return redirect(url_for('admin.settings'))

@admin_bp.route('/export/transactions')
@login_required
def export_transactions():
    export_format = request.args.get('format', 'csv')
    with support.db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, user_id, stokvel_id, amount, type, status, transaction_date FROM transactions")
            rows = cur.fetchall()
            columns = ['ID', 'User ID', 'Stokvel ID', 'Amount', 'Type', 'Status', 'Date']
    if export_format == 'csv':
        def generate():
            data = [columns] + list(rows)
            for row in data:
                yield ','.join([str(item) for item in row]) + '\n'
        return Response(generate(), mimetype='text/csv',
                        headers={"Content-Disposition": "attachment;filename=transactions.csv"})
    elif export_format == 'excel':
        df = pd.DataFrame(rows, columns=columns)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        return Response(output.getvalue(), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        headers={"Content-Disposition": "attachment;filename=transactions.xlsx"})
    elif export_format == 'pdf':
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        col_width = 40
        for col in columns:
            pdf.cell(col_width, 10, str(col), 1)
        pdf.ln()
        for row in rows:
            for item in row:
                pdf.cell(col_width, 10, str(item), 1)
            pdf.ln()
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        return Response(pdf_bytes, mimetype='application/pdf',
                        headers={"Content-Disposition": "attachment;filename=transactions.pdf"})
    else:
        flash('Unsupported export format.', 'danger')
        return redirect(url_for('admin.settings'))

@admin_bp.route('/set-language', methods=['POST'])
def set_language():
    """
    Allows the user to switch to any language. Stores the selected language in the session.
    Expects a 'language' field in the POST form data.
    Redirects back to the referring page or dashboard.
    """
    language = request.form.get('language')
    valid_codes = ['en', 'zu', 'xh', 'af', 'st', 'ts', 'tn', 'ss', 've', 'nr']
    if language not in valid_codes:
        language = 'en'
    session['language_preference'] = language
    flash(f'Language switched to {language}.', 'success')
    return redirect(request.referrer or url_for('admin.dashboard'))

@admin_bp.route('/financial-reports')
@login_required
def financial_reports():
    if session.get('role') != 'admin':
        flash('Permission denied.', 'danger')
        return redirect(url_for('home'))
    # Placeholder: In the future, fetch and filter report data here
    return render_template('admin_financial_reports.html')

@admin_bp.route('/virtual-rewards')
@login_required
def virtual_rewards():
    if session.get('role') != 'admin':
        flash('Permission denied.', 'danger')
        return redirect(url_for('home'))
    
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Get all users with their reward card balances
                cur.execute("""
                    SELECT u.id, u.username, u.email, vrc.balance, vrc.card_number
                    FROM users u
                    LEFT JOIN virtual_reward_cards vrc ON u.id = vrc.user_id
                    ORDER BY u.username
                """)
                users = cur.fetchall()
                
                # Get recent reward transactions
                cur.execute("""
                    SELECT rt.amount, rt.transaction_type, rt.description, rt.created_at, u.username, u.email
                    FROM reward_transactions rt
                    JOIN users u ON rt.user_id = u.id
                    ORDER BY rt.created_at DESC
                    LIMIT 20
                """)
                transactions = cur.fetchall()
                
                # Get total reward statistics
                cur.execute("""
                    SELECT 
                        COUNT(DISTINCT vrc.user_id) as total_users_with_cards,
                        COALESCE(SUM(vrc.balance), 0) as total_balance,
                        COUNT(rt.id) as total_transactions
                    FROM virtual_reward_cards vrc
                    LEFT JOIN reward_transactions rt ON vrc.user_id = rt.user_id
                """)
                stats = cur.fetchone()
                
    except Exception as e:
        print(f"Error fetching virtual rewards data: {e}")
        users = []
        transactions = []
        stats = (0, 0, 0)
    
    return render_template('admin_virtual_rewards.html', 
                         users=users, 
                         transactions=transactions, 
                         stats=stats)

@admin_bp.route('/virtual-rewards/distribute', methods=['POST'])
@login_required
def distribute_rewards():
    if session.get('role') != 'admin':
        flash('Permission denied.', 'danger')
        return redirect(url_for('admin.virtual_rewards'))
    
    email = request.form.get('email')
    reward_type = request.form.get('reward_type')
    amount = request.form.get('amount')
    description = request.form.get('description', 'Admin reward distribution')
    
    if not all([email, reward_type, amount]):
        flash('Email, reward type, and amount are required.', 'danger')
        return redirect(url_for('admin.virtual_rewards'))
    
    try:
        amount = int(amount)
        if amount <= 0:
            flash('Amount must be positive.', 'danger')
            return redirect(url_for('admin.virtual_rewards'))
            
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Get user by email
                cur.execute("SELECT firebase_uid FROM users WHERE email = %s", (email,))
                user = cur.fetchone()
                
                if not user:
                    flash('User not found.', 'danger')
                    return redirect(url_for('admin.virtual_rewards'))
                
                firebase_uid = user[0]
                
                # Import and use the add_reward function from rewards module
                from rewards import add_reward
                success = add_reward(firebase_uid, amount, reward_type, description)
                
                if success:
                    flash(f'Successfully distributed {amount} {reward_type} to {email}', 'success')
                else:
                    flash('Failed to distribute reward. User may not have a reward card.', 'danger')
                    
    except ValueError:
        flash('Amount must be a valid number.', 'danger')
    except Exception as e:
        print(f"Error distributing reward: {e}")
        flash('An error occurred while distributing the reward.', 'danger')
    
    return redirect(url_for('admin.virtual_rewards'))

@admin_bp.route('/virtual-rewards/bulk-distribute', methods=['POST'])
@login_required
def bulk_distribute_rewards():
    if session.get('role') != 'admin':
        flash('Permission denied.', 'danger')
        return redirect(url_for('admin.virtual_rewards'))
    
    reward_type = request.form.get('reward_type')
    amount = request.form.get('amount')
    description = request.form.get('description', 'Bulk admin reward distribution')
    user_filter = request.form.get('user_filter', 'all')  # all, active, new_users
    
    if not all([reward_type, amount]):
        flash('Reward type and amount are required.', 'danger')
        return redirect(url_for('admin.virtual_rewards'))
    
    try:
        amount = int(amount)
        if amount <= 0:
            flash('Amount must be positive.', 'danger')
            return redirect(url_for('admin.virtual_rewards'))
            
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Build query based on filter
                if user_filter == 'active':
                    # Users with recent activity (last 30 days)
                    cur.execute("""
                        SELECT DISTINCT u.id 
                        FROM users u
                        JOIN reward_transactions rt ON u.id = rt.user_id
                        WHERE rt.created_at >= CURRENT_DATE - INTERVAL '30 days'
                    """)
                elif user_filter == 'new_users':
                    # Users who joined in last 30 days
                    cur.execute("""
                        SELECT id FROM users 
                        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    """)
                else:
                    # All users
                    cur.execute("SELECT id FROM users")
                
                users = cur.fetchall()
                success_count = 0
                
                from rewards import add_reward
                for user in users:
                    # Get firebase_uid for the user
                    cur.execute("SELECT firebase_uid FROM users WHERE id = %s", (user[0],))
                    firebase_uid_result = cur.fetchone()
                    if firebase_uid_result and firebase_uid_result[0]:
                        if add_reward(firebase_uid_result[0], amount, reward_type, description):
                            success_count += 1
                
                flash(f'Successfully distributed {amount} {reward_type} to {success_count} users', 'success')
                    
    except ValueError:
        flash('Amount must be a valid number.', 'danger')
    except Exception as e:
        print(f"Error bulk distributing rewards: {e}")
        flash('An error occurred during bulk distribution.', 'danger')
    
    return redirect(url_for('admin.virtual_rewards'))

@admin_bp.route('/virtual-rewards/analytics')
@login_required
def reward_analytics():
    if session.get('role') != 'admin':
        flash('Permission denied.', 'danger')
        return redirect(url_for('admin.virtual_rewards'))
    
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Monthly reward distribution
                cur.execute("""
                    SELECT 
                        DATE_TRUNC('month', created_at) as month,
                        SUM(amount) as total_amount,
                        COUNT(*) as transaction_count
                    FROM reward_transactions
                    WHERE amount > 0
                    GROUP BY DATE_TRUNC('month', created_at)
                    ORDER BY month DESC
                    LIMIT 12
                """)
                monthly_data = cur.fetchall()
                
                # Top reward earners
                cur.execute("""
                    SELECT u.username, u.email, SUM(rt.amount) as total_earned
                    FROM reward_transactions rt
                    JOIN users u ON rt.user_id = u.id
                    WHERE rt.amount > 0
                    GROUP BY u.id, u.username, u.email
                    ORDER BY total_earned DESC
                    LIMIT 10
                """)
                top_earners = cur.fetchall()
                
                # Reward type distribution
                cur.execute("""
                    SELECT transaction_type, COUNT(*) as count, SUM(amount) as total
                    FROM reward_transactions
                    GROUP BY transaction_type
                    ORDER BY total DESC
                """)
                type_distribution = cur.fetchall()
                
    except Exception as e:
        print(f"Error fetching reward analytics: {e}")
        monthly_data = []
        top_earners = []
        type_distribution = []
    
    return render_template('admin_reward_analytics.html', 
                         monthly_data=monthly_data,
                         top_earners=top_earners,
                         type_distribution=type_distribution)

@admin_bp.route('/virtual-rewards/export')
@login_required
def export_reward_data():
    if session.get('role') != 'admin':
        flash('Permission denied.', 'danger')
        return redirect(url_for('admin.virtual_rewards'))
    
    export_type = request.args.get('type', 'transactions')
    export_format = request.args.get('format', 'csv')
    
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                if export_type == 'transactions':
                    cur.execute("""
                        SELECT rt.created_at, u.username, u.email, rt.transaction_type, 
                               rt.description, rt.amount
                        FROM reward_transactions rt
                        JOIN users u ON rt.user_id = u.id
                        ORDER BY rt.created_at DESC
                    """)
                    data = cur.fetchall()
                    columns = ['Date', 'Username', 'Email', 'Type', 'Description', 'Amount']
                    filename = 'reward_transactions'
                elif export_type == 'balances':
                    cur.execute("""
                        SELECT u.username, u.email, vrc.balance, vrc.card_number
                        FROM users u
                        LEFT JOIN virtual_reward_cards vrc ON u.id = vrc.user_id
                        ORDER BY vrc.balance DESC
                    """)
                    data = cur.fetchall()
                    columns = ['Username', 'Email', 'Balance', 'Card Number']
                    filename = 'user_balances'
                else:
                    flash('Invalid export type.', 'danger')
                    return redirect(url_for('admin.virtual_rewards'))
        
        if export_format == 'csv':
            def generate():
                yield ','.join(columns) + '\n'
                for row in data:
                    yield ','.join([str(item) if item else '' for item in row]) + '\n'
            
            return Response(generate(), mimetype='text/csv',
                          headers={"Content-Disposition": f"attachment;filename={filename}.csv"})
        
        elif export_format == 'excel':
            df = pd.DataFrame(data, columns=columns)
            output = BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)
            return Response(output.getvalue(), 
                          mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                          headers={"Content-Disposition": f"attachment;filename={filename}.xlsx"})
        
        else:
            flash('Unsupported export format.', 'danger')
            
    except Exception as e:
        print(f"Error exporting reward data: {e}")
        flash('An error occurred while exporting data.', 'danger')
    
    return redirect(url_for('admin.virtual_rewards'))

@admin_bp.route('/virtual-rewards/rules', methods=['GET', 'POST'])
@login_required
def reward_rules():
    if session.get('role') != 'admin':
        flash('Permission denied.', 'danger')
        return redirect(url_for('admin.virtual_rewards'))
    
    if request.method == 'POST':
        # Save reward rules
        try:
            with support.db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if table exists, create if not
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS reward_rules (
                            id SERIAL PRIMARY KEY,
                            rule_name VARCHAR(100) NOT NULL UNIQUE,
                            rule_value VARCHAR(255) NOT NULL,
                            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Clear existing rules
                    cur.execute("DELETE FROM reward_rules")
                    
                    # Insert new rules
                    rules = [
                        ('contribution_multiplier', request.form.get('contribution_multiplier', '1')),
                        ('welcome_bonus', request.form.get('welcome_bonus', '0')),
                        ('referral_bonus', request.form.get('referral_bonus', '0')),
                        ('monthly_bonus', request.form.get('monthly_bonus', '0')),
                        ('event_attendance_bonus', request.form.get('event_attendance_bonus', '0')),
                        ('loan_payment_bonus', request.form.get('loan_payment_bonus', '0')),
                    ]
                    
                    for rule_name, rule_value in rules:
                        cur.execute("""
                            INSERT INTO reward_rules (rule_name, rule_value, created_at)
                            VALUES (%s, %s, CURRENT_TIMESTAMP)
                        """, (rule_name, rule_value))
                    
                    conn.commit()
                    flash('Reward rules updated successfully!', 'success')
                    
        except Exception as e:
            print(f"Error updating reward rules: {e}")
            flash('An error occurred while updating rules.', 'danger')
    
    # Load current rules
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Check if table exists first
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'reward_rules'
                    );
                """)
                table_exists = cur.fetchone()[0]
                
                if table_exists:
                    cur.execute("SELECT rule_name, rule_value FROM reward_rules")
                    rules = dict(cur.fetchall())
                else:
                    rules = {}
    except Exception as e:
        print(f"Error loading reward rules: {e}")
        rules = {}
    
    return render_template('admin_reward_rules.html', rules=rules)

@admin_bp.route('/member-rewards')
@login_required
def member_rewards():
    if session.get('role') != 'admin':
        flash('Permission denied.', 'danger')
        return redirect(url_for('home'))
    return render_template('admin_member_rewards.html')
