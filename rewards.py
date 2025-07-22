import os
import random
import string
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
import psycopg2

rewards_bp = Blueprint('rewards', __name__)

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', 5432)
    )

def generate_card_number():
    return ''.join([str(random.randint(0, 9)) for _ in range(16)])

def get_internal_user_id(firebase_uid):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        print(f"Found user ID {row[0]} for firebase_uid {firebase_uid}")
        return row[0]
    else:
        print(f"No user found for firebase_uid {firebase_uid}")
        return None

@rewards_bp.route('/api/rewards/card', methods=['GET', 'POST'])
def get_or_create_card():
    firebase_uid = session.get('user_id')
    user_id = get_internal_user_id(firebase_uid)
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, card_number, balance FROM virtual_reward_cards WHERE user_id = %s", (user_id,))
    card = cur.fetchone()

    if card:
        card_id, card_number, balance = card
    else:
        card_number = generate_card_number()
        cur.execute(
            "INSERT INTO virtual_reward_cards (user_id, card_number, balance) VALUES (%s, %s, %s) RETURNING id",
            (user_id, card_number, 0)
        )
        card_id = cur.fetchone()[0]
        conn.commit()
        balance = 0

    cur.close()
    conn.close()
    return jsonify({'card_id': card_id, 'card_number': card_number, 'balance': balance})

@rewards_bp.route('/api/rewards/transactions', methods=['GET'])
def get_transactions():
    firebase_uid = session.get('user_id')
    user_id = get_internal_user_id(firebase_uid)
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT amount, transaction_type, description, created_at
        FROM reward_transactions
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 50
    """, (user_id,))
    transactions = [
        {'amount': row[0], 'type': row[1], 'description': row[2], 'date': row[3]}
        for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return jsonify({'transactions': transactions})

def add_reward(firebase_uid, amount, transaction_type, description):
    user_id = get_internal_user_id(firebase_uid)
    if not user_id:
        print(f"User not found for firebase_uid: {firebase_uid}")
        return False
    
    # Debug: Check if user exists in users table
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
    user_exists = cur.fetchone()
    if not user_exists:
        print(f"User ID {user_id} does not exist in users table")
        cur.close()
        conn.close()
        return False
    
    cur.execute("SELECT id FROM virtual_reward_cards WHERE user_id = %s", (user_id,))
    card = cur.fetchone()
    if not card:
        cur.close()
        conn.close()
        return False
    card_id = card[0]
    cur.execute("""
        INSERT INTO reward_transactions (card_id, user_id, amount, transaction_type, description)
        VALUES (%s, %s, %s, %s, %s)
    """, (card_id, user_id, amount, transaction_type, description))
    cur.execute("UPDATE virtual_reward_cards SET balance = balance + %s WHERE id = %s", (amount, card_id))
    
    # Create notification for reward received
    notification_message = f"You received {amount} reward points! {description}"
    try:
        cur.execute("""
            INSERT INTO notifications (user_id, type, message, created_at)
            VALUES (%s, %s, %s, NOW())
        """, (firebase_uid, 'reward_received', notification_message))
        print(f"Notification created successfully for user {firebase_uid}")
    except Exception as e:
        print(f"Error creating notification for user {firebase_uid}: {e}")
        # Don't fail the entire transaction if notification fails
        pass
    
    conn.commit()
    cur.close()
    conn.close()
    return True

import random
import string

def generate_voucher_code():
    """Generate a unique voucher code"""
    # Generate a random 12-character alphanumeric code
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    return f"KASI-{code}"

def create_voucher(firebase_uid, voucher_type, amount):
    """Create a voucher in the database"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Generate unique voucher code
    voucher_code = generate_voucher_code()
    
    # Ensure voucher code is unique
    while True:
        cur.execute("SELECT id FROM vouchers WHERE voucher_code = %s", (voucher_code,))
        if not cur.fetchone():
            break
        voucher_code = generate_voucher_code()
    
    # Insert voucher
    cur.execute("""
        INSERT INTO vouchers (user_id, voucher_type, voucher_code, amount)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (firebase_uid, voucher_type, voucher_code, amount))
    
    voucher_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    return voucher_code

@rewards_bp.route('/api/rewards/airtime', methods=['POST'])
def purchase_airtime():
    firebase_uid = session.get('user_id')
    user_id = get_internal_user_id(firebase_uid)
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    data = request.get_json()
    amount = int(data.get('amount', 10))
    phone_number = data.get('phone_number', '')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if user has enough points
    cur.execute("SELECT id, balance FROM virtual_reward_cards WHERE user_id = %s", (user_id,))
    card = cur.fetchone()
    if not card or card[1] < amount:
        cur.close()
        conn.close()
        return jsonify({'error': 'Insufficient points'}), 400
    
    card_id = card[0]
    
    # Deduct points
    cur.execute("UPDATE virtual_reward_cards SET balance = balance - %s WHERE id = %s", (amount, card_id))
    
    # Log transaction
    cur.execute("""
        INSERT INTO reward_transactions (card_id, user_id, amount, transaction_type, description)
        VALUES (%s, %s, %s, %s, %s)
    """, (card_id, user_id, -amount, 'purchase_airtime', f'Airtime for {phone_number}'))
    
    # Create voucher
    voucher_code = create_voucher(firebase_uid, 'airtime', amount)
    
    conn.commit()
    cur.close()
    conn.close()
    
    # Create notification
    message = f"Your airtime voucher has been generated! Voucher Code: {voucher_code}"
    add_reward(firebase_uid, 0, 'airtime_voucher', message)
    
    return jsonify({
        'success': True,
        'message': 'Airtime voucher generated successfully!',
        'voucher_code': voucher_code,
        'amount': amount
    })

@rewards_bp.route('/api/rewards/electricity', methods=['POST'])
def purchase_electricity():
    firebase_uid = session.get('user_id')
    user_id = get_internal_user_id(firebase_uid)
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    data = request.get_json()
    amount = int(data.get('amount', 20))
    meter_number = data.get('meter_number', '')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if user has enough points
    cur.execute("SELECT id, balance FROM virtual_reward_cards WHERE user_id = %s", (user_id,))
    card = cur.fetchone()
    if not card or card[1] < amount:
        cur.close()
        conn.close()
        return jsonify({'error': 'Insufficient points'}), 400
    
    card_id = card[0]
    
    # Deduct points
    cur.execute("UPDATE virtual_reward_cards SET balance = balance - %s WHERE id = %s", (amount, card_id))
    
    # Log transaction
    cur.execute("""
        INSERT INTO reward_transactions (card_id, user_id, amount, transaction_type, description)
        VALUES (%s, %s, %s, %s, %s)
    """, (card_id, user_id, -amount, 'purchase_electricity', f'Electricity for {meter_number}'))
    
    # Create voucher
    voucher_code = create_voucher(firebase_uid, 'electricity', amount)
    
    conn.commit()
    cur.close()
    conn.close()
    
    # Create notification
    message = f"Your electricity voucher has been generated! Voucher Code: {voucher_code}"
    add_reward(firebase_uid, 0, 'electricity_voucher', message)
    
    return jsonify({
        'success': True,
        'message': 'Electricity voucher generated successfully!',
        'voucher_code': voucher_code,
        'amount': amount
    })

@rewards_bp.route('/api/rewards/donate', methods=['POST'])
def donate_points():
    firebase_uid = session.get('user_id')
    user_id = get_internal_user_id(firebase_uid)
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json()
    amount = int(data.get('amount'))
    cause = data.get('cause')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, balance FROM virtual_reward_cards WHERE user_id = %s", (user_id,))
    card = cur.fetchone()
    if not card:
        cur.close()
        conn.close()
        return jsonify({'error': 'No reward card found'}), 404
    card_id, balance = card

    if balance < amount:
        cur.close()
        conn.close()
        return jsonify({'error': 'Insufficient points'}), 400

    cur.execute("UPDATE virtual_reward_cards SET balance = balance - %s WHERE id = %s", (amount, card_id))
    cur.execute("""
        INSERT INTO reward_transactions (card_id, user_id, amount, transaction_type, description)
        VALUES (%s, %s, %s, %s, %s)
    """, (card_id, user_id, -amount, 'donate', f'Donation to {cause}'))
    cur.execute("""
        INSERT INTO donations (user_id, amount, cause)
        VALUES (%s, %s, %s)
    """, (user_id, amount, cause))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'success': True, 'message': 'Donation successful'})

@rewards_bp.route('/card', methods=['GET'])
def rewards_card_page():
    firebase_uid = session.get('user_id')
    user_id = get_internal_user_id(firebase_uid)
    if not user_id:
        return redirect(url_for('login'))
    # Get card info
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, card_number, balance FROM virtual_reward_cards WHERE user_id = %s", (user_id,))
    card = cur.fetchone()
    if not card:
        # Create card if not exists
        card_number = generate_card_number()
        cur.execute(
            "INSERT INTO virtual_reward_cards (user_id, card_number, balance) VALUES (%s, %s, %s) RETURNING id, card_number, balance",
            (user_id, card_number, 0)
        )
        card = cur.fetchone()
        conn.commit()
    card_id, card_number, balance = card
    
    # Calculate real-time statistics
    # Total Earned (sum of all positive transactions)
    cur.execute("""
        SELECT COALESCE(SUM(amount), 0) 
        FROM reward_transactions 
        WHERE user_id = %s AND amount > 0
    """, (user_id,))
    total_earned = cur.fetchone()[0] or 0
    
    # Total Spent (sum of all negative transactions)
    cur.execute("""
        SELECT COALESCE(ABS(SUM(amount)), 0) 
        FROM reward_transactions 
        WHERE user_id = %s AND amount < 0
    """, (user_id,))
    total_spent = cur.fetchone()[0] or 0
    
    # Active Programs (count of unique reward types earned)
    cur.execute("""
        SELECT COUNT(DISTINCT transaction_type) 
        FROM reward_transactions 
        WHERE user_id = %s AND amount > 0
    """, (user_id,))
    active_programs = cur.fetchone()[0] or 0
    
    # Get transactions
    cur.execute("""
        SELECT amount, transaction_type, description, created_at
        FROM reward_transactions
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 50
    """, (user_id,))
    transactions = [
        {'amount': row[0], 'type': row[1], 'description': row[2], 'date': row[3]}
        for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    
    return render_template('rewards_card.html', 
                         card={'card_number': card_number, 'balance': balance}, 
                         transactions=transactions,
                         total_earned=total_earned,
                         total_spent=total_spent,
                         active_programs=active_programs)

@rewards_bp.route('/spend/airtime', methods=['POST'])
def spend_airtime_form():
    firebase_uid = session.get('user_id')
    user_id = get_internal_user_id(firebase_uid)
    if not user_id:
        return redirect(url_for('login'))
    phone_number = request.form.get('phone_number')
    amount = int(request.form.get('amount'))
    # Use the same logic as purchase_airtime API
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, balance FROM virtual_reward_cards WHERE user_id = %s", (user_id,))
    card = cur.fetchone()
    if not card or card[1] < amount:
        flash('Insufficient points or no card found.', 'danger')
        return redirect(url_for('rewards.rewards_card_page'))
    card_id = card[0]
    cur.execute("UPDATE virtual_reward_cards SET balance = balance - %s WHERE id = %s", (amount, card_id))
    cur.execute("""
        INSERT INTO reward_transactions (card_id, user_id, amount, transaction_type, description)
        VALUES (%s, %s, %s, %s, %s)
    """, (card_id, user_id, -amount, 'purchase_airtime', f'Airtime for {phone_number}'))
    cur.execute("""
        INSERT INTO airtime_purchases (user_id, amount, phone_number, status)
        VALUES (%s, %s, %s, %s)
    """, (user_id, amount, phone_number, 'pending'))
    conn.commit()
    cur.close()
    conn.close()
    flash('Airtime purchase requested!', 'success')
    return redirect(url_for('rewards.rewards_card_page'))

@rewards_bp.route('/spend/electricity', methods=['POST'])
def spend_electricity_form():
    firebase_uid = session.get('user_id')
    user_id = get_internal_user_id(firebase_uid)
    if not user_id:
        return redirect(url_for('login'))
    meter_number = request.form.get('meter_number')
    amount = int(request.form.get('amount'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, balance FROM virtual_reward_cards WHERE user_id = %s", (user_id,))
    card = cur.fetchone()
    if not card or card[1] < amount:
        flash('Insufficient points or no card found.', 'danger')
        return redirect(url_for('rewards.rewards_card_page'))
    card_id = card[0]
    cur.execute("UPDATE virtual_reward_cards SET balance = balance - %s WHERE id = %s", (amount, card_id))
    cur.execute("""
        INSERT INTO reward_transactions (card_id, user_id, amount, transaction_type, description)
        VALUES (%s, %s, %s, %s, %s)
    """, (card_id, user_id, -amount, 'purchase_electricity', f'Electricity for {meter_number}'))
    cur.execute("""
        INSERT INTO electricity_purchases (user_id, amount, meter_number, status)
        VALUES (%s, %s, %s, %s)
    """, (user_id, amount, meter_number, 'pending'))
    conn.commit()
    cur.close()
    conn.close()
    flash('Electricity purchase requested!', 'success')
    return redirect(url_for('rewards.rewards_card_page'))

@rewards_bp.route('/spend/donate', methods=['POST'])
def spend_donate_form():
    firebase_uid = session.get('user_id')
    user_id = get_internal_user_id(firebase_uid)
    if not user_id:
        return redirect(url_for('login'))
    cause = request.form.get('cause')
    amount = int(request.form.get('amount'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, balance FROM virtual_reward_cards WHERE user_id = %s", (user_id,))
    card = cur.fetchone()
    if not card or card[1] < amount:
        flash('Insufficient points or no card found.', 'danger')
        return redirect(url_for('rewards.rewards_card_page'))
    card_id = card[0]
    cur.execute("UPDATE virtual_reward_cards SET balance = balance - %s WHERE id = %s", (amount, card_id))
    cur.execute("""
        INSERT INTO reward_transactions (card_id, user_id, amount, transaction_type, description)
        VALUES (%s, %s, %s, %s, %s)
    """, (card_id, user_id, -amount, 'donate', f'Donation to {cause}'))
    cur.execute("""
        INSERT INTO donations (user_id, amount, cause)
        VALUES (%s, %s, %s)
    """, (user_id, amount, cause))
    conn.commit()
    cur.close()
    conn.close()
    flash('Donation successful!', 'success')
    return redirect(url_for('rewards.rewards_card_page'))

@rewards_bp.route('/marketplace', methods=['GET'])
def marketplace():
    firebase_uid = session.get('user_id')
    user_id = get_internal_user_id(firebase_uid)
    if not user_id:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, description, price_in_points, image_url FROM marketplace_items WHERE is_active = TRUE ORDER BY created_at DESC")
    items = [
        {'id': row[0], 'name': row[1], 'description': row[2], 'price': row[3], 'image_url': row[4]} for row in cur.fetchall()
    ]
    # Get user's card balance
    cur.execute("SELECT balance FROM virtual_reward_cards WHERE user_id = %s", (user_id,))
    card = cur.fetchone()
    balance = card[0] if card else 0
    cur.close()
    conn.close()
    return render_template('marketplace.html', items=items, balance=balance)

@rewards_bp.route('/marketplace/buy/<int:item_id>', methods=['POST'])
def buy_marketplace_item(item_id):
    print(f"DEBUG: Marketplace purchase attempt for item_id: {item_id}")
    firebase_uid = session.get('user_id')
    user_id = get_internal_user_id(firebase_uid)
    if not user_id:
        print("DEBUG: User not authenticated")
        return redirect(url_for('login'))
    quantity = int(request.form.get('quantity', 1))
    print(f"DEBUG: Quantity requested: {quantity}")
    conn = get_db_connection()
    cur = conn.cursor()
    # Get item info
    cur.execute("SELECT name, price_in_points, description FROM marketplace_items WHERE id = %s AND is_active = TRUE", (item_id,))
    item = cur.fetchone()
    if not item:
        print(f"DEBUG: Item {item_id} not found or not active")
        flash('Item not found or not available.', 'danger')
        return redirect(url_for('rewards.marketplace'))
    
    item_name, price, description = item
    
    # For transport vouchers, calculate points based on custom amount
    if 'transport' in item_name.lower():
        custom_amount = int(request.form.get('custom_amount', 0))
        # Convert R amount to points (1 point = R1 for transport)
        total_points = custom_amount * quantity
    else:
        total_points = price * quantity
    
    print(f"DEBUG: Item: {item_name}, Price: {price}, Total points needed: {total_points}")
    
    # Get user card and balance
    cur.execute("SELECT id, balance FROM virtual_reward_cards WHERE user_id = %s", (user_id,))
    card = cur.fetchone()
    if not card or card[1] < total_points:
        flash('Insufficient points.', 'danger')
        return redirect(url_for('rewards.marketplace'))
    card_id = card[0]
    
    # Deduct points
    cur.execute("UPDATE virtual_reward_cards SET balance = balance - %s WHERE id = %s", (total_points, card_id))
    
    # Log transaction
    cur.execute("""
        INSERT INTO reward_transactions (card_id, user_id, amount, transaction_type, description)
        VALUES (%s, %s, %s, %s, %s)
    """, (card_id, user_id, -total_points, 'marketplace_purchase', f'Bought {item_name} x{quantity}'))
    
    # Check if this is a voucher-type item that should generate immediate vouchers
    voucher_types = ['airtime', 'electricity', 'data', 'movie', 'transport', 'clothing', 'food', 'school', 'health']
    is_voucher_item = any(voucher_type in item_name.lower() for voucher_type in voucher_types)
    
    if is_voucher_item:
        # Get network selection for airtime and data vouchers
        network = request.form.get('network', '')
        if ('airtime' in item_name.lower() or 'data' in item_name.lower()) and not network:
            flash('Please select a network for airtime and data vouchers.', 'danger')
            return redirect(url_for('rewards.marketplace'))
        
        # Get transport voucher details
        transport_company = request.form.get('transport_company', '')
        card_number = request.form.get('card_number', '')
        custom_amount = request.form.get('custom_amount', '')
        
        if 'transport' in item_name.lower():
            if not transport_company or not card_number or not custom_amount:
                flash('Please fill in all required fields for transport vouchers.', 'danger')
                return redirect(url_for('rewards.marketplace'))
            
            try:
                custom_amount = int(custom_amount)
                if custom_amount < 50:
                    flash('Transport voucher amount must be at least R50.', 'danger')
                    return redirect(url_for('rewards.marketplace'))
            except ValueError:
                flash('Please enter a valid amount for transport voucher.', 'danger')
                return redirect(url_for('rewards.marketplace'))
        
        # Generate vouchers immediately
        vouchers_created = []
        for i in range(quantity):
            # For airtime and data vouchers, include network in the voucher type
            if 'airtime' in item_name.lower():
                voucher_type = f"airtime_{network}"
                voucher_amount = price
            elif 'data' in item_name.lower():
                voucher_type = f"data_{network}"
                voucher_amount = price
            elif 'transport' in item_name.lower():
                voucher_type = f"transport_{transport_company}"
                voucher_amount = custom_amount  # Use custom amount for transport
            else:
                voucher_type = item_name.lower().replace(' voucher', '').replace(' ', '_')
                voucher_amount = price
            
            voucher_code = create_voucher(firebase_uid, voucher_type, voucher_amount)
            vouchers_created.append(voucher_code)
        
        # Create order with 'completed' status since vouchers are generated
        cur.execute("""
            INSERT INTO marketplace_orders (user_id, item_id, quantity, total_points, status)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, item_id, quantity, total_points, 'completed'))
        
        conn.commit()
        cur.close()
        conn.close()
        
        # Create notification with voucher codes
        if 'airtime' in item_name.lower():
            network_display = network.upper()
            if len(vouchers_created) == 1:
                message = f"Your {network_display} airtime voucher has been generated! Voucher Code: {vouchers_created[0]}"
            else:
                voucher_list = ', '.join(vouchers_created)
                message = f"Your {quantity} {network_display} airtime vouchers have been generated! Voucher Codes: {voucher_list}"
        elif 'data' in item_name.lower():
            network_display = network.upper()
            if len(vouchers_created) == 1:
                message = f"Your {network_display} data voucher has been generated! Voucher Code: {vouchers_created[0]}"
            else:
                voucher_list = ', '.join(vouchers_created)
                message = f"Your {quantity} {network_display} data vouchers have been generated! Voucher Codes: {voucher_list}"
        elif 'transport' in item_name.lower():
            company_display = transport_company.replace('_', ' ').title()
            if len(vouchers_created) == 1:
                message = f"Your {company_display} transport voucher (R{custom_amount}) has been generated! Voucher Code: {vouchers_created[0]}"
            else:
                voucher_list = ', '.join(vouchers_created)
                message = f"Your {quantity} {company_display} transport vouchers (R{custom_amount} each) have been generated! Voucher Codes: {voucher_list}"
        else:
            if len(vouchers_created) == 1:
                message = f"Your {item_name} voucher has been generated! Voucher Code: {vouchers_created[0]}"
            else:
                voucher_list = ', '.join(vouchers_created)
                message = f"Your {quantity} {item_name} vouchers have been generated! Voucher Codes: {voucher_list}"
        
        add_reward(firebase_uid, 0, 'voucher_generated', message)
        
        # Flash success message with voucher codes
        if 'airtime' in item_name.lower():
            network_display = network.upper()
            if len(vouchers_created) == 1:
                flash(f'Purchase successful! Your {network_display} airtime voucher code is: {vouchers_created[0]}', 'success')
            else:
                voucher_list = ', '.join(vouchers_created)
                flash(f'Purchase successful! Your {network_display} airtime voucher codes are: {voucher_list}', 'success')
        elif 'data' in item_name.lower():
            network_display = network.upper()
            if len(vouchers_created) == 1:
                flash(f'Purchase successful! Your {network_display} data voucher code is: {vouchers_created[0]}', 'success')
            else:
                voucher_list = ', '.join(vouchers_created)
                flash(f'Purchase successful! Your {network_display} data voucher codes are: {voucher_list}', 'success')
        elif 'transport' in item_name.lower():
            company_display = transport_company.replace('_', ' ').title()
            if len(vouchers_created) == 1:
                flash(f'Purchase successful! Your {company_display} transport voucher (R{custom_amount}) code is: {vouchers_created[0]}', 'success')
            else:
                voucher_list = ', '.join(vouchers_created)
                flash(f'Purchase successful! Your {company_display} transport voucher codes are: {voucher_list}', 'success')
        else:
            if len(vouchers_created) == 1:
                flash(f'Purchase successful! Your voucher code is: {vouchers_created[0]}', 'success')
            else:
                voucher_list = ', '.join(vouchers_created)
                flash(f'Purchase successful! Your voucher codes are: {voucher_list}', 'success')
        
        return redirect(url_for('rewards.marketplace'))
    else:
        # For non-voucher items, create pending order as before
        cur.execute("""
            INSERT INTO marketplace_orders (user_id, item_id, quantity, total_points, status)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, item_id, quantity, total_points, 'pending'))
        
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Purchase successful! Your order is pending.', 'success')
        return redirect(url_for('rewards.marketplace'))

@rewards_bp.route('/marketplace/orders', methods=['GET'])
def marketplace_orders():
    firebase_uid = session.get('user_id')
    user_id = get_internal_user_id(firebase_uid)
    if not user_id:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.id, i.name, o.quantity, o.total_points, o.status, o.created_at
        FROM marketplace_orders o
        JOIN marketplace_items i ON o.item_id = i.id
        WHERE o.user_id = %s
        ORDER BY o.created_at DESC
    """, (user_id,))
    orders = [
        {'id': row[0], 'item_name': row[1], 'quantity': row[2], 'total_points': row[3], 'status': row[4], 'created_at': row[5]} for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return render_template('marketplace_orders.html', orders=orders)

@rewards_bp.route('/marketplace/redeem/<item>', methods=['POST'])
def redeem_marketplace_item(item):
    firebase_uid = session.get('user_id')
    user_id = get_internal_user_id(firebase_uid)
    if not user_id:
        return redirect(url_for('login'))
    
    # Define item prices and names
    item_prices = {
        'airtime': 15,
        'electricity': 20,
        'donate': 0,  # Will be set from form
        'data': 30,
        'movie': 50,
        'transport': 25,
        'clothing': 60,
        'food': 40,
        'school': 35,
        'health': 20
    }
    item_names = {
        'airtime': 'Airtime Voucher',
        'electricity': 'Electricity Voucher',
        'donate': 'Community Donation',
        'data': 'Data Bundle',
        'movie': 'Movie Ticket',
        'transport': 'Transport Voucher',
        'clothing': 'Clothing Store Voucher',
        'food': 'Food Delivery Voucher',
        'school': 'School Supplies Pack',
        'health': 'Health & Wellness Voucher'
    }
    
    if item not in item_prices:
        flash('Invalid item.', 'danger')
        return redirect(url_for('rewards.rewards_card_page'))
    
    # For donations, get amount from form
    if item == 'donate':
        try:
            price = int(request.form.get('amount', 0))
            if price <= 0:
                flash('Please enter a valid donation amount.', 'danger')
                return redirect(url_for('rewards.rewards_card_page'))
        except (ValueError, TypeError):
            flash('Please enter a valid donation amount.', 'danger')
            return redirect(url_for('rewards.rewards_card_page'))
    else:
        price = item_prices[item]
    
    name = item_names[item]
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # First, ensure the item exists in marketplace_items table
    cur.execute("SELECT id FROM marketplace_items WHERE LOWER(name) = %s", (name.lower(),))
    item_result = cur.fetchone()
    
    if not item_result:
        # Create the item if it doesn't exist
        cur.execute("""
            INSERT INTO marketplace_items (name, description, price_in_points, is_active)
            VALUES (%s, %s, %s, TRUE)
            RETURNING id
        """, (name, f'Redeem {name} with your points', price))
        item_id = cur.fetchone()[0]
    else:
        item_id = item_result[0]
    
    # Check user's card balance
    cur.execute("SELECT id, balance FROM virtual_reward_cards WHERE user_id = %s", (user_id,))
    card = cur.fetchone()
    if not card or card[1] < price:
        flash('Insufficient points to redeem this item.', 'danger')
        cur.close()
        conn.close()
        return redirect(url_for('rewards.rewards_card_page'))
    
    card_id = card[0]
    
    # Deduct points
    cur.execute("UPDATE virtual_reward_cards SET balance = balance - %s WHERE id = %s", (price, card_id))
    
    # Log transaction
    cause = request.form.get('cause', 'Community Fund')
    
    if item == 'donate':
        # This is a donation
        cur.execute("""
            INSERT INTO reward_transactions (card_id, user_id, amount, transaction_type, description)
            VALUES (%s, %s, %s, %s, %s)
        """, (card_id, user_id, -price, 'donation', f'Donated {price} points to {cause}'))
        
        # Create notification for donation
        message = f"You successfully donated {price} points to {cause}. Thank you for your generosity!"
        add_reward(firebase_uid, 0, 'donation', message)
        
        flash(f'Successfully donated {price} points to {cause}!', 'success')
    else:
        # This is a regular marketplace purchase
        cur.execute("""
            INSERT INTO reward_transactions (card_id, user_id, amount, transaction_type, description)
            VALUES (%s, %s, %s, %s, %s)
        """, (card_id, user_id, -price, 'marketplace_purchase', f'Purchased {item} for {price} points'))
        
        # Create order with proper item_id
        cur.execute("""
            INSERT INTO marketplace_orders (user_id, item_id, quantity, total_points, status)
            VALUES (%s, %s, 1, %s, %s)
        """, (user_id, item_id, price, 'redeemed'))
        
        # Create notification for marketplace purchase
        item_name = "airtime voucher" if item == "airtime" else "electricity voucher"
        message = f"You successfully purchased a {item_name} for {price} points!"
        add_reward(firebase_uid, 0, 'marketplace_purchase', message)
        
        flash(f'Successfully purchased {item_name} for {price} points!', 'success')
    
    # Create order with proper item_id
    cur.execute("""
        INSERT INTO marketplace_orders (user_id, item_id, quantity, total_points, status)
        VALUES (%s, %s, 1, %s, %s)
    """, (user_id, item_id, price, 'redeemed'))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('rewards.rewards_card_page')) 

@rewards_bp.route('/vouchers', methods=['GET'])
def view_vouchers():
    firebase_uid = session.get('user_id')
    if not firebase_uid:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get user's vouchers
    cur.execute("""
        SELECT id, voucher_type, voucher_code, amount, status, created_at, used_at
        FROM vouchers 
        WHERE user_id = %s 
        ORDER BY created_at DESC
    """, (firebase_uid,))
    
    vouchers = []
    for row in cur.fetchall():
        vouchers.append({
            'id': row[0],
            'type': row[1],
            'code': row[2],
            'amount': row[3],
            'status': row[4],
            'created_at': row[5],
            'used_at': row[6]
        })
    
    cur.close()
    conn.close()
    
    return render_template('vouchers.html', vouchers=vouchers)

@rewards_bp.route('/vouchers/redeem/<voucher_code>', methods=['POST'])
def redeem_voucher(voucher_code):
    firebase_uid = session.get('user_id')
    if not firebase_uid:
        return jsonify({'error': 'User not authenticated'}), 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if voucher exists and belongs to user
    cur.execute("""
        SELECT id, voucher_type, amount, status 
        FROM vouchers 
        WHERE voucher_code = %s AND user_id = %s
    """, (voucher_code, firebase_uid))
    
    voucher = cur.fetchone()
    if not voucher:
        cur.close()
        conn.close()
        return jsonify({'error': 'Voucher not found'}), 404
    
    voucher_id, voucher_type, amount, status = voucher
    
    if status != 'active':
        cur.close()
        conn.close()
        return jsonify({'error': 'Voucher already used or expired'}), 400
    
    # Mark voucher as used
    cur.execute("""
        UPDATE vouchers 
        SET status = 'used', used_at = NOW() 
        WHERE id = %s
    """, (voucher_id,))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': f'{voucher_type.title()} voucher redeemed successfully!',
        'amount': amount
    }) 