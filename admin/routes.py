from flask import render_template, request, redirect, session, flash, url_for, jsonify, Response, send_file
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
from extensions import csrf
from translations import get_text
from datetime import datetime
import os
from flask_babel import _

# Add this context processor to make 't' available in all templates
@admin_bp.app_context_processor
def inject_t():
    return dict(t=get_text, _=get_text)

@admin_bp.app_context_processor
def inject_admin_globals():
    return dict(_=_)

def get_user_language():
    return session.get('language_preference', 'en')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    user_language = get_user_language()
    if session.get('role') != 'admin':
        flash('Permission denied.', 'danger')
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
        flash('Permission denied.', 'danger')
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
                        LEFT JOIN stokvel_members sm ON CAST(u.id AS VARCHAR) = sm.user_id
                        LEFT JOIN stokvels s ON sm.stokvel_id = s.id
                        WHERE u.username ILIKE %s OR u.email ILIKE %s
                        ORDER BY u.created_at DESC
                    """, (f'%{search_query}%', f'%{search_query}%'))
                else:
                    cur.execute("""
                        SELECT u.id, u.username, u.email, u.role, u.created_at, u.last_login, s.name AS stokvel_name
                        FROM users u
                        LEFT JOIN stokvel_members sm ON CAST(u.id AS VARCHAR) = sm.user_id
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

    return render_template('admin_manage_users.html', users=users, search_query=search_query, stokvels=stokvels, user_language=user_language)

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
        flash('Permission denied.', 'danger')
        return redirect(url_for('home'))

    status = request.args.get('status', 'pending')
    loans = []
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                 cur.execute("""
                    SELECT t.id, u.username, u.email, t.amount, t.status, t.transaction_date, t.description as comment
                    FROM transactions t
                    LEFT JOIN users u ON t.user_id = u.firebase_uid
                    WHERE t.type = 'payout' AND t.status = %s
                    ORDER BY t.transaction_date DESC
                """, (status,))
                 loans = cur.fetchall()
    except Exception as e:
        print(f"Error fetching loan approvals: {e}")
        flash('Could not load loan approvals.', 'danger')
    return render_template('admin_loan_approvals.html', loans=loans, current_status=status, user_language=user_language)

@admin_bp.route('/loans/approve', methods=['POST'])
@csrf.exempt
@login_required
def approve_loan():
    import sys
    print('DEBUG: Form data:', dict(request.form), file=sys.stderr)
    print('DEBUG: Cookies:', request.cookies, file=sys.stderr)
    if session.get('role') != 'admin':
        flash('Permission denied.', 'danger')
        return redirect(url_for('admin.loan_approvals'))
    
    loan_id = request.form.get('loan_id')
    comment = request.form.get('comment', 'Approved by admin.')
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Update loan status
                cur.execute("UPDATE transactions SET status = 'approved', description = CONCAT(description, ' | Admin Comment: ', %s) WHERE id = %s", (comment, loan_id,))
                # Fetch user firebase_uid for notification
                cur.execute("SELECT user_id FROM transactions WHERE id = %s", (loan_id,))
                user_id_row = cur.fetchone()
                if user_id_row and user_id_row[0]:
                    cur.execute("SELECT firebase_uid FROM users WHERE firebase_uid = %s", (user_id_row[0],))
                    firebase_row = cur.fetchone()
                    if firebase_row and firebase_row[0]:
                        message = "Your loan request has been approved."
                        link = url_for('profile')
                        create_notification(firebase_row[0], message, link_url=link, notification_type='loan_approved')
                conn.commit()
        flash('Loan approved successfully.', 'success')
    except Exception as e:
        print(f"Error approving loan: {e}")
        flash('Failed to approve loan.', 'danger')
    return redirect(url_for('admin.loan_approvals', status='pending'))

@admin_bp.route('/loans/reject', methods=['POST'])
@csrf.exempt
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
                # Update loan status
                cur.execute("UPDATE transactions SET status = 'rejected', description = CONCAT(description, ' | Admin Comment: ', %s) WHERE id = %s", (comment, loan_id,))
                # Fetch user firebase_uid for notification
                cur.execute("SELECT user_id FROM transactions WHERE id = %s", (loan_id,))
                user_id_row = cur.fetchone()
                if user_id_row and user_id_row[0]:
                    cur.execute("SELECT firebase_uid FROM users WHERE firebase_uid = %s", (user_id_row[0],))
                    firebase_row = cur.fetchone()
                    if firebase_row and firebase_row[0]:
                        message = "Your loan request has been rejected."
                        link = url_for('profile')
                        create_notification(firebase_row[0], message, link_url=link, notification_type='loan_rejected')
                if cur.rowcount == 0:
                    flash('No loan was updated. Please check the loan ID.', 'danger')
                else:
                    flash('Loan rejected successfully.', 'success')
                conn.commit()
    except Exception as e:
        print(f"Error rejecting loan: {e}")
        flash('Failed to reject loan.', 'danger')
    return redirect(url_for('admin.loan_approvals', status='rejected'))

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
        flash('An error occurred.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        stokvel_id = request.form.get('stokvel')
        name = request.form.get('name')
        description = request.form.get('description')
        event_type = request.form.get('event_type')
        target_date = request.form.get('target_date')
        send_notification = 'send_notification' in request.form
        try:
            with support.db_connection() as conn:
                with conn.cursor() as cur:
                    # Insert event
                    cur.execute(
                        "INSERT INTO events (stokvel_id, name, description, event_type, target_date) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                        (stokvel_id, name, description, event_type, target_date)
                    )
                    event_id = cur.fetchone()[0]
                    # Fetch all members of the stokvel
                    cur.execute("SELECT user_id FROM stokvel_members WHERE stokvel_id = %s", (stokvel_id,))
                    members = cur.fetchall()
                    # Add event to each member's diary (calendar)
                    if not members:
                        print(f"No members found for stokvel {stokvel_id}, event {event_id}")
                    for member in members:
                        user_id = member[0]
                        if user_id:
                            try:
                                cur.execute("INSERT INTO diary (user_id, event_id, event_name, event_date, description) VALUES (%s, %s, %s, %s, %s)",
                                    (user_id, event_id, event_type, target_date, description))
                            except Exception as diary_e:
                                print(f"Could not add to diary for user {user_id}: {diary_e}")
                    conn.commit()
                    # Notify all members and the creator
                    if send_notification:
                        for member in members:
                            user_id = member[0]
                            if user_id:
                                message = f"New event of type '{event_type}' has been scheduled for your stokvel."
                                link = url_for('home')
                                create_notification(user_id, message, link_url=link, notification_type='event')
                        # Also notify the creator (admin)
                        creator_id = session.get('user_id')
                        if creator_id:
                            message = f"You have created a new event '{event_type}' for your stokvel."
                            link = url_for('admin.events')
                            create_notification(creator_id, message, link_url=link, notification_type='event')
            flash('Event created and notifications sent!', 'success')
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
    return render_template('admin_events.html', events=events, stokvels=stokvels, user_language=user_language)

@admin_bp.route('/memberships', methods=['GET'])
@login_required
def memberships():
    user_language = get_user_language()
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('An error occurred.', 'danger')
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
    return render_template('admin_memberships.html', memberships=memberships, search_query=search_query, user_language=user_language)

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
        flash('Could not add membership plan.', 'danger')
    return redirect(url_for('admin.memberships'))

@admin_bp.route('/notifications')
@login_required
def notifications():
    user_language = get_user_language()
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('An error occurred.', 'danger')
        return redirect(url_for('home'))
    
    notif_type = request.args.get('type', 'all')
    notifications = []
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                if notif_type == 'all':
                    cur.execute("""
                        SELECT n.id, n.user_id, n.message, n.type, n.created_at, u.username, u.email, s.name as stokvel_name
                        FROM notifications n
                        LEFT JOIN users u ON n.user_id = u.firebase_uid
                        LEFT JOIN stokvel_members sm ON sm.user_id = u.firebase_uid
                        LEFT JOIN stokvels s ON sm.stokvel_id = s.id
                        ORDER BY n.created_at DESC
                        LIMIT 100
                    """)
                else:
                    cur.execute("""
                        SELECT n.id, n.user_id, n.message, n.type, n.created_at, u.username, u.email, s.name as stokvel_name
                        FROM notifications n
                        LEFT JOIN users u ON n.user_id = u.firebase_uid
                        LEFT JOIN stokvel_members sm ON sm.user_id = u.firebase_uid
                        LEFT JOIN stokvels s ON sm.stokvel_id = s.id
                        WHERE n.type = %s
                        ORDER BY n.created_at DESC
                        LIMIT 100
                    """, (notif_type,))
                notifications = cur.fetchall()
    except Exception as e:
        print(f"Error fetching notifications: {e}")
        flash('Could not load notifications.', 'danger')
    
    return render_template('admin_notifications.html', notifications=notifications, user_language=user_language)

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
                    flash('Notification sent successfully to 1 user!', 'success')
                else:
                    flash(f'Notification sent successfully to {recipient_count} users!', 'success')
                    
    except Exception as e:
        print(f"Error sending notification: {e}")
        flash('Could not send notification.', 'danger')
    return redirect(url_for('admin.notifications'))

@admin_bp.route('/notifications/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    if session.get('role') != 'admin':
        flash('Permission denied.', 'danger')
        return redirect(url_for('admin.notifications'))
    
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Delete the notification
                cur.execute("DELETE FROM notifications WHERE id = %s", (notification_id,))
                if cur.rowcount == 0:
                    flash('Notification not found.', 'danger')
                else:
                    conn.commit()
                    flash('Notification deleted successfully!', 'success')
    except Exception as e:
        print(f"Error deleting notification: {e}")
        flash('Could not delete notification.', 'danger')
    
    return redirect(url_for('admin.notifications'))

@admin_bp.route('/api/notifications/<int:notification_id>/delete', methods=['POST'])
@login_required
def api_delete_notification(notification_id):
    user_id = session.get('user_id')
    user_role = session.get('role')
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Only allow delete if user owns the notification or is admin
                if user_role == 'admin':
                    cur.execute("DELETE FROM notifications WHERE id = %s", (notification_id,))
                else:
                    cur.execute("DELETE FROM notifications WHERE id = %s AND user_id = %s", (notification_id, user_id))
                if cur.rowcount == 0:
                    return jsonify({'success': False, 'message': 'Notification not found or not authorized.'}), 404
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error deleting notification via API: {e}")
        return jsonify({'success': False, 'message': 'Could not delete notification.'}), 500

@admin_bp.route('/kyc-approvals')
@login_required
def kyc_approvals():
    user_language = get_user_language()
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('An error occurred.', 'danger')
        return redirect(url_for('home'))

    search_query = request.args.get('q', '').strip()
    kyc_users = []
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                if search_query:
                    cur.execute("""
                        SELECT id, email, id_document, proof_of_address, created_at, kyc_approved_at
                        FROM users
                        WHERE (id_document IS NOT NULL AND id_document != '')
                          AND (proof_of_address IS NOT NULL AND proof_of_address != '')
                          AND (email ILIKE %s)
                        ORDER BY created_at DESC
                    """, (f'%{search_query}%',))
                else:
                    cur.execute("""
                        SELECT id, email, id_document, proof_of_address, created_at, kyc_approved_at
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
    return render_template('admin_kyc_approvals.html', kyc_users=kyc_users, search_query=search_query, debug_kyc_users=kyc_users, user_language=user_language)

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
        flash('Could not approve KYC.', 'danger')
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
        flash('Could not reject KYC.', 'danger')
    return redirect(url_for('admin.kyc_approvals'))

@admin_bp.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def settings():
    user_language = get_user_language()
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('An error occurred.', 'danger')
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
                        meeting_day VARCHAR(10),
                        enable_dual_approval BOOLEAN,
                        withdrawal_threshold INTEGER,
                        enable_attendance_tracking BOOLEAN,
                        absence_penalty INTEGER,
                        missed_meetings_threshold INTEGER
                    )
                ''')
                # Ensure at least one row exists
                cur.execute('SELECT COUNT(*) FROM admin_settings')
                if cur.fetchone()[0] == 0:
                    cur.execute('''
                        INSERT INTO admin_settings (
                            contribution_amount, late_penalty, grace_period, max_loan_percent, interest_rate, repayment_period, language, role_management, loan_approval_roles, meeting_frequency, meeting_time, meeting_reminders, data_retention, enable_2fa, meeting_day, enable_dual_approval, withdrawal_threshold, enable_attendance_tracking, absence_penalty, missed_meetings_threshold
                        )
                        VALUES (100, 10, 7, 50, 5, 6, 'en', '', '', 'monthly', '14:00', FALSE, '5', FALSE, 'Monday', FALSE, 1000, FALSE, 50, 3)
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
        enable_dual_approval = request.form.get('enable_dual_approval') == 'on'
        withdrawal_threshold = request.form.get('withdrawal_threshold', type=int)
        enable_attendance_tracking = request.form.get('enable_attendance_tracking') == 'on'
        absence_penalty = request.form.get('absence_penalty', type=int)
        missed_meetings_threshold = request.form.get('missed_meetings_threshold', type=int)

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
                                meeting_day=%s,
                                enable_dual_approval=%s,
                                withdrawal_threshold=%s,
                                enable_attendance_tracking=%s,
                                absence_penalty=%s,
                                missed_meetings_threshold=%s
                            WHERE id=%s
                        ''', (
                            contribution_amount, late_penalty, grace_period, max_loan_percent, interest_rate, repayment_period,
                            language, role_management, loan_approval_roles, meeting_frequency, meeting_time, meeting_reminders,
                            data_retention, enable_2fa, meeting_day, enable_dual_approval, withdrawal_threshold, enable_attendance_tracking, absence_penalty, missed_meetings_threshold, row[0]
                        ))
                    else:
                        cur.execute('''
                            INSERT INTO admin_settings (
                                contribution_amount, late_penalty, grace_period, max_loan_percent, interest_rate, repayment_period,
                                language, role_management, loan_approval_roles, meeting_frequency, meeting_time, meeting_reminders,
                                data_retention, enable_2fa, meeting_day, enable_dual_approval, withdrawal_threshold, enable_attendance_tracking, absence_penalty, missed_meetings_threshold
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ''', (
                            contribution_amount, late_penalty, grace_period, max_loan_percent, interest_rate, repayment_period,
                            language, role_management, loan_approval_roles, meeting_frequency, meeting_time, meeting_reminders,
                            data_retention, enable_2fa, meeting_day, enable_dual_approval, withdrawal_threshold, enable_attendance_tracking, absence_penalty, missed_meetings_threshold
                        ))
                conn.commit()
            session['language_preference'] = language  # Ensure session is updated for immediate effect
            if '_settings_updated' not in session:
                flash('Settings updated successfully!', 'success')
                session['_settings_updated'] = True
        except Exception as e:
            flash(f'Error saving settings: {e}', 'danger')
        return redirect(url_for('admin.settings'))

    # Remove the flag after redirect
    session.pop('_settings_updated', None)

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
        'meeting_day': 'Monday',
        'enable_dual_approval': False,
        'withdrawal_threshold': 1000,
        'enable_attendance_tracking': False,
        'absence_penalty': 50,
        'missed_meetings_threshold': 3
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
        # Sync session language with admin settings
        if default_settings.get('language'):
            session['language_preference'] = default_settings['language']
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

    # Fetch meeting attendance data
    attendance_data = []
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT meeting_name, meeting_date, present_count, absent_count FROM meeting_attendance ORDER BY meeting_date DESC LIMIT 20")
                attendance_data = [
                    {
                        'meeting': row[0],
                        'date': row[1].strftime('%Y-%m-%d') if row[1] else '',
                        'present': row[2],
                        'absent': row[3]
                    }
                    for row in cur.fetchall()
                ]
    except Exception as e:
        print(f'Error fetching attendance data: {e}')

    return render_template(
        'admin_settings.html',
        default_settings=default_settings,
        audit_logs=audit_logs,
        attendance_data=attendance_data
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

@admin_bp.route('/admin/add_attendance', methods=['POST'])
@login_required
def add_attendance():
    print('add_attendance route called')
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('admin.settings'))
    meeting_name = request.form.get('meeting_name')
    meeting_date = request.form.get('meeting_date')
    present_count = request.form.get('present_count', type=int)
    absent_count = request.form.get('absent_count', type=int)
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO meeting_attendance (meeting_name, meeting_date, present_count, absent_count)
                    VALUES (%s, %s, %s, %s)
                ''', (meeting_name, meeting_date, present_count, absent_count))
            conn.commit()
        flash('Attendance record added.', 'success')
    except Exception as e:
        flash(f'Error adding attendance record: {e}', 'danger')
    return redirect(url_for('admin.settings'))

@admin_bp.route('/admin/edit_attendance/<int:attendance_id>', methods=['POST'])
@login_required
def edit_attendance(attendance_id):
    print(f'edit_attendance route called for id={attendance_id}')
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('admin.settings'))
    meeting_name = request.form.get('meeting_name')
    meeting_date = request.form.get('meeting_date')
    present_count = request.form.get('present_count', type=int)
    absent_count = request.form.get('absent_count', type=int)
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    UPDATE meeting_attendance
                    SET meeting_name=%s, meeting_date=%s, present_count=%s, absent_count=%s
                    WHERE id=%s
                ''', (meeting_name, meeting_date, present_count, absent_count, attendance_id))
            conn.commit()
        flash('Attendance record updated.', 'success')
    except Exception as e:
        print(f"Error updating attendance record: {e}")
        flash(f'Error updating attendance record: {e}', 'danger')
    return redirect(url_for('admin.settings'))

@admin_bp.route('/admin/delete_attendance/<int:attendance_id>', methods=['POST'])
@login_required
def delete_attendance(attendance_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('admin.settings'))
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM meeting_attendance WHERE id=%s', (attendance_id,))
            conn.commit()
        flash('Attendance record deleted.', 'success')
    except Exception as e:
        flash(f'Error deleting attendance record: {e}', 'danger')
    return redirect(url_for('admin.settings'))

@admin_bp.route('/set-language', methods=['POST'])
def set_language():
    """
    Allows the user to switch to any language. Stores the selected language in the session.
    Expects a 'language' field in the POST form data.
    Redirects back to the referring page or dashboard.
    """
    language = request.form.get('language')
    valid_codes = ['en', 'zu', 'xh', 'af', 'st', 'ts', 'tn', 'ss', 've', 'nr', 'nso']
    if language not in valid_codes:
        language = 'en'
    session['language_preference'] = language
    flash('Language updated successfully!', 'success')
    return redirect(request.referrer or url_for('admin.dashboard'))
csrf.exempt(set_language)

@admin_bp.route('/set_language')
def admin_set_language():
    lang = request.args.get('lang')
    from flask import current_app, make_response, request, url_for
    supported = current_app.config.get('BABEL_SUPPORTED_LOCALES', ['en'])
    resp = make_response(redirect(request.referrer or url_for('dashboard')))
    if lang and lang in supported:
        resp.set_cookie('language_preference', lang, max_age=60*60*24*30)  # 30 days
        flash(f"Admin language changed to {lang}", "success")
    else:
        flash("Invalid language selected.", "error")
    return resp

@admin_bp.route('/financial-reports')
@login_required
def financial_reports():
    user_language = get_user_language()
    financial_data = {}
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Total contributions
                cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE LOWER(type) = 'contribution'")
                total_contributions = cur.fetchone()[0]
                # Total withdrawals
                cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE LOWER(type) = 'payout'")
                total_withdrawals = cur.fetchone()[0]
                # Current balance
                cur.execute("""
                    SELECT COALESCE(SUM(
                        CASE 
                            WHEN LOWER(type) = 'contribution' THEN amount
                            WHEN LOWER(type) = 'payout' THEN -amount
                            ELSE 0
                        END
                    ), 0) FROM transactions
                """)
                current_balance = cur.fetchone()[0]
                # Breakdown by stokvel
                cur.execute("""
                    SELECT s.name, 
                        COALESCE(SUM(
                            CASE 
                                WHEN LOWER(t.type) = 'contribution' THEN t.amount
                                WHEN LOWER(t.type) = 'payout' THEN -t.amount
                                ELSE 0
                            END
                        ), 0) as balance
                    FROM stokvels s
                    LEFT JOIN transactions t ON s.id = t.stokvel_id
                    GROUP BY s.name
                    ORDER BY s.name
                """)
                stokvel_balances = cur.fetchall()
                # Fetch latest 100 transactions for the report table (fix type mismatch)
                cur.execute("""
                    SELECT t.transaction_date, t.type, t.amount, u.username, t.status
                    FROM transactions t
                    LEFT JOIN users u ON t.user_id = CAST(u.id AS VARCHAR)
                    ORDER BY t.transaction_date DESC
                    LIMIT 100
                """)
                transactions = cur.fetchall()
                financial_data['transactions'] = transactions
                # Monthly contributions and payouts for the last 6 months
                cur.execute("""
                    SELECT 
                        TO_CHAR(DATE_TRUNC('month', transaction_date), 'YYYY-MM') AS month,
                        SUM(CASE WHEN LOWER(type) = 'contribution' THEN amount ELSE 0 END) AS contributions,
                        SUM(CASE WHEN LOWER(type) = 'payout' THEN amount ELSE 0 END) AS payouts
                    FROM transactions
                    GROUP BY month
                    ORDER BY month
                    LIMIT 6
                """)
                monthly_data = []
                for row in cur.fetchall():
                    month = row[0] if row[0] is not None else ""
                    contrib = row[1] if row[1] is not None else 0
                    payout = row[2] if row[2] is not None else 0
                    monthly_data.append([month, contrib, payout])
                financial_data['monthly_data'] = monthly_data
                # Cumulative balance over time (by month)
                cur.execute("""
                    SELECT 
                        TO_CHAR(DATE_TRUNC('month', transaction_date), 'YYYY-MM') AS month,
                        SUM(CASE WHEN LOWER(type) = 'contribution' THEN amount ELSE -amount END) AS net
                    FROM transactions
                    GROUP BY month
                    ORDER BY month
                """)
                rows = cur.fetchall()
                cumulative = []
                total = 0
                for row in rows:
                    month = row[0] if row[0] is not None else ""
                    net = row[1] if row[1] is not None else 0
                    total += net
                    cumulative.append({'month': month, 'balance': total})
                financial_data['cumulative'] = cumulative
        financial_data = {
            'total_contributions': total_contributions,
            'total_withdrawals': total_withdrawals,
            'current_balance': current_balance,
            'stokvel_balances': stokvel_balances
        }
        # Guarantee chart data is always present and serializable
        if 'monthly_data' not in financial_data or not financial_data['monthly_data']:
            financial_data['monthly_data'] = []
        if 'cumulative' not in financial_data or not financial_data['cumulative']:
            financial_data['cumulative'] = []
    except Exception as e:
        print(f"Error fetching financial report data: {e}")
        flash('Could not load financial report data.', 'danger')
    return render_template('admin_financial_reports.html', financial_data=financial_data, user_language=user_language)

class PDF(FPDF):
    def header(self):
        logo_path = os.path.join('static', 'logo.png.png')
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 25)
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'KasiKash Financial Report', ln=True, align='C')
        self.set_draw_color(34, 211, 238)
        self.set_line_width(1)
        self.line(40, 25, 200, 25)
        self.ln(10)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()} | Powered by KasiKash', 0, 0, 'C')

@admin_bp.route('/financial-reports/export/pdf')
@login_required
def export_financial_report_pdf():
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE LOWER(type) = 'contribution'")
                total_contributions = cur.fetchone()[0]
                cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE LOWER(type) = 'payout'")
                total_withdrawals = cur.fetchone()[0]
                cur.execute("""
                    SELECT COALESCE(SUM(
                        CASE 
                            WHEN LOWER(type) = 'contribution' THEN amount
                            WHEN LOWER(type) = 'payout' THEN -amount
                            ELSE 0
                        END
                    ), 0) FROM transactions
                """)
                current_balance = cur.fetchone()[0]
                cur.execute("""
                    SELECT s.name, 
                        COALESCE(SUM(
                            CASE 
                                WHEN LOWER(t.type) = 'contribution' THEN t.amount
                                WHEN LOWER(t.type) = 'payout' THEN -t.amount
                                ELSE 0
                            END
                        ), 0) as balance
                    FROM stokvels s
                    LEFT JOIN transactions t ON s.id = t.stokvel_id
                    GROUP BY s.name
                    ORDER BY s.name
                """)
                stokvel_balances = cur.fetchall()
    except Exception as e:
        flash('Could not generate PDF.', 'danger')
        return redirect(url_for('admin.financial_reports'))

    pdf = PDF()
    pdf.add_page()

    # Timestamp and generated by
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(100)
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by KasiKash", ln=True, align='R')
    pdf.ln(5)

    # Summary Table
    pdf.set_text_color(0)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Summary", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.set_fill_color(240, 248, 255)
    pdf.cell(60, 10, "Total Contributions", 1, 0, 'L', True)
    pdf.cell(60, 10, "Total Payouts", 1, 0, 'L', True)
    pdf.cell(60, 10, "Current Balance", 1, 1, 'L', True)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(60, 10, f"R {total_contributions:,.2f}", 1, 0, 'L', True)
    pdf.cell(60, 10, f"R {total_withdrawals:,.2f}", 1, 0, 'L', True)
    pdf.cell(60, 10, f"R {current_balance:,.2f}", 1, 1, 'L', True)
    pdf.ln(10)

    # Stokvel Balances Table
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Stokvel Balances", ln=True)
    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(34, 211, 238)
    pdf.set_text_color(255)
    pdf.cell(90, 8, "Stokvel", 1, 0, 'C', True)
    pdf.cell(90, 8, "Balance", 1, 1, 'C', True)
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(0)
    fill = False
    for stokvel in stokvel_balances:
        if fill:
            pdf.set_fill_color(240, 248, 255)
        else:
            pdf.set_fill_color(255, 255, 255)
        pdf.cell(90, 8, str(stokvel[0]), 1, 0, 'L', True)
        pdf.cell(90, 8, f"R {stokvel[1]:,.2f}", 1, 1, 'R', True)
        fill = not fill

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    pdf_output = BytesIO(pdf_bytes)
    pdf_output.seek(0)
    return send_file(pdf_output, as_attachment=True, download_name='financial_report.pdf', mimetype='application/pdf')

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
                    flash('Rewards distributed successfully!', 'success')
                else:
                    flash('Failed to distribute reward. User may not have a reward card.', 'danger')
                    
    except ValueError:
        flash('Amount must be a valid number.', 'danger')
    except Exception as e:
        print(f"Error distributing reward: {e}")
        flash('Could not distribute rewards.', 'danger')

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
                
                flash(f'Bulk rewards distributed successfully!', 'success')
                    
    except ValueError:
        flash('Amount must be a valid number.', 'danger')
    except Exception as e:
        print(f"Error bulk distributing rewards: {e}")
        flash('Could not bulk distribute rewards.', 'danger')
    
    return redirect(url_for('admin.virtual_rewards'))

@admin_bp.route('/virtual-rewards/analytics')
@login_required
def reward_analytics():
    if session.get('role') != 'admin':
        flash('Permission denied.', 'danger')
        return redirect(url_for('admin.virtual_rewards'))

    monthly_data = []
    top_earners = []
    type_distribution = []

    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Monthly reward distribution (last 6 months)
                cur.execute("""
                    SELECT DATE_TRUNC('month', created_at) AS month, SUM(amount)
                    FROM reward_transactions
                    GROUP BY month
                    ORDER BY month DESC
                    LIMIT 6
                """)
                monthly_data = cur.fetchall()

                # Top reward earners
                cur.execute("""
                    SELECT u.username, u.email, SUM(rt.amount) as total_earned
                    FROM reward_transactions rt
                    JOIN users u ON rt.user_id = u.id
                    GROUP BY u.username, u.email
                    ORDER BY total_earned DESC
                    LIMIT 10
                """)
                top_earners = cur.fetchall()

                # Reward type distribution
                cur.execute("""
                    SELECT rt.transaction_type, COUNT(*), SUM(rt.amount)
                    FROM reward_transactions rt
                    GROUP BY rt.transaction_type
                """)
                type_distribution = cur.fetchall()
    except Exception as e:
        print(f"Error fetching analytics data: {e}")

    return render_template(
        'admin_reward_analytics.html',
        monthly_data=monthly_data,
        top_earners=top_earners,
        type_distribution=type_distribution
    )
