# --- Voucher Purchase Route for Member Interface ---

# --- Voucher Purchase Route for Member Interface ---



import os
import psycopg2
import random
import string
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

rewards_bp = Blueprint('rewards', __name__)

@rewards_bp.route('/purchase_voucher', methods=['POST'])
def purchase_voucher():
    firebase_uid = session.get('user_id')
    if not firebase_uid:
        flash('You must be logged in to purchase a voucher.', 'danger')
        return redirect(url_for('login'))
    voucher_type = request.form.get('voucher_type')
    amount = request.form.get('amount')
    if not voucher_type or not amount:
        flash('Please select a voucher type and amount.', 'danger')
        return redirect(url_for('rewards.rewards_card_page'))
    try:
        amount = float(amount)
        # Optionally: Check if user has enough balance, deduct, etc.
        voucher_code = create_voucher(firebase_uid, voucher_type, amount)
        flash(f'Voucher purchased! Code: {voucher_code}', 'success')
    except Exception as e:
        print('Voucher purchase error:', e)
        flash('Failed to purchase voucher. Please try again.', 'danger')
    return redirect(url_for('rewards.rewards_card_page'))
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
    
    # Get internal user ID
    user_id = get_internal_user_id(firebase_uid)
    if not user_id:
        raise ValueError("User not found")
    
    # Generate unique voucher code
    voucher_code = generate_voucher_code()
    
    # Ensure voucher code is unique
    while True:
        cur.execute("SELECT id FROM vouchers WHERE code = %s", (voucher_code,))
        if not cur.fetchone():
            break
        voucher_code = generate_voucher_code()
    
    try:
        # Insert voucher
        cur.execute("""
            INSERT INTO vouchers (user_id, voucher_type, code, amount)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (user_id, voucher_type, voucher_code, amount))
        
        result = cur.fetchone()
        if result is None:
            conn.rollback()
            raise ValueError("Failed to create voucher - no ID returned")
            
        voucher_id = result[0]
        conn.commit()
        return voucher_code
    except Exception as e:
        conn.rollback()
        raise ValueError(f"Failed to create voucher: {str(e)}")
    finally:
        cur.close()
        conn.close()

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
    try:
        firebase_uid = session.get('user_id')
        if not firebase_uid:
            flash('Please log in to access the marketplace.', 'error')
            return redirect(url_for('login'))

        # Get internal user ID
        user_id = get_internal_user_id(firebase_uid)
        if not user_id:
            flash('User account not found.', 'error')
            return redirect(url_for('login'))

        conn = get_db_connection()
        cur = conn.cursor()
        
        # First, ensure the user has a rewards card
        cur.execute("""
            SELECT balance FROM virtual_reward_cards 
            WHERE user_id = %s
        """, (user_id,))
        card = cur.fetchone()
        
        if not card:
            # Create a new card if user doesn't have one
            card_number = generate_card_number()
            cur.execute("""
                INSERT INTO virtual_reward_cards (user_id, card_number, balance) 
                VALUES (%s, %s, %s)
                RETURNING balance
            """, (user_id, card_number, 0))
            card = cur.fetchone()
            conn.commit()
            
        balance = card[0] if card else 0
        
        # Get marketplace items
        cur.execute("""
            SELECT id, name, description, price_in_points, image_url 
            FROM marketplace_items 
            WHERE is_active = TRUE 
            ORDER BY created_at DESC
        """)
        items = [
            {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'price': row[3],
                'image_url': row[4]
            } for row in cur.fetchall()
        ]
        
        return render_template('marketplace.html', items=items, balance=balance)
        
    except Exception as e:
        flash(f'Error loading marketplace: {str(e)}', 'error')
        return redirect(url_for('rewards.rewards_card_page'))
        
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@rewards_bp.route('/marketplace/buy/<int:item_id>', methods=['POST'])
def buy_marketplace_item(item_id):
    conn = None
    cur = None
    try:
        firebase_uid = session.get('user_id')
        if not firebase_uid:
            flash('Please log in to make purchases.', 'error')
            return redirect(url_for('login'))

        # Get the quantity from form data
        try:
            quantity = int(request.form.get('quantity', 1))
            if quantity < 1:
                flash('Please select a valid quantity.', 'error')
                return redirect(url_for('rewards.marketplace'))
        except ValueError:
            flash('Invalid quantity specified.', 'error')
            return redirect(url_for('rewards.marketplace'))

        conn = get_db_connection()
        cur = conn.cursor()

        # Get item info
        cur.execute("""
            SELECT name, price_in_points, description 
            FROM marketplace_items 
            WHERE id = %s AND is_active = TRUE
        """, (item_id,))
        item = cur.fetchone()

        if not item:
            flash('Item not found or not available.', 'error')
            return redirect(url_for('rewards.marketplace'))

        item_name, price, description = item

        try:
            # Process voucher purchase and get voucher codes
            vouchers, amount_per_voucher = process_voucher_purchase(
                firebase_uid, 
                item_name, 
                request.form, 
                price, 
                quantity
            )

            # Calculate total points
            total_points = amount_per_voucher * quantity
            
            # Get internal user ID for database operations
            internal_user_id = get_internal_user_id(firebase_uid)
            if not internal_user_id:
                flash('User account not found. Please contact support.', 'error')
                return redirect(url_for('rewards.marketplace'))

            # Get user's current balance
            cur.execute("""
                SELECT id, balance 
                FROM virtual_reward_cards 
                WHERE user_id = %s
            """, (internal_user_id,))
            
            card = cur.fetchone()
            if not card:
                flash('No rewards card found. Please contact support.', 'error')
                return redirect(url_for('rewards.marketplace'))
                
            card_id, current_balance = card
            
            if current_balance < total_points:
                flash(f'Insufficient points. You need {total_points} points but have {current_balance}.', 'error')
                return redirect(url_for('rewards.marketplace'))
            
            # Deduct points from card
            cur.execute("""
                UPDATE virtual_reward_cards 
                SET balance = balance - %s 
                WHERE id = %s
            """, (total_points, card_id))
            
            # Record the transaction
            cur.execute("""
                INSERT INTO reward_transactions 
                (card_id, user_id, amount, transaction_type, description)
                VALUES (%s, %s, %s, %s, %s)
            """, (card_id, internal_user_id, -total_points, 'marketplace_purchase', f'Bought {item_name} x{quantity}'))
            
            # Create order record
            cur.execute("""
                INSERT INTO marketplace_orders 
                (user_id, item_id, quantity, total_points, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (internal_user_id, item_id, quantity, total_points, 'completed'))
            
            conn.commit()
            
            # Create success message
            if len(vouchers) > 1:
                codes = ', '.join(vouchers)
                message = f'Purchase successful! Your voucher codes: {codes}'
            else:
                message = f'Purchase successful! Your voucher code: {vouchers[0]}'
                
            flash(message, 'success')
            return redirect(url_for('rewards.marketplace'))
            
        except Exception as e:
            if conn:
                conn.rollback()
            flash(f'Error processing purchase: {str(e)}', 'error')
            return redirect(url_for('rewards.marketplace'))
            
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@rewards_bp.route('/marketplace/vouchers', methods=['GET'])
def get_voucher_types():
    try:
        # Define available voucher types
        voucher_types = ['airtime', 'electricity', 'data', 'movie', 'transport', 'clothing', 'food', 'school', 'health']
        return jsonify({'voucher_types': voucher_types})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def validate_voucher_details(item_name, form_data):
    try:
        # Get network selection for airtime and data vouchers
        network = form_data.get('network', '')
        if ('airtime' in item_name.lower() or 'data' in item_name.lower()) and not network:
            return False, 'Please select a network for airtime and data vouchers.'
            
        # Get transport voucher details if needed
        if 'transport' in item_name.lower():
            transport_company = form_data.get('transport_company', '')
            card_number = form_data.get('card_number', '')
            custom_amount = form_data.get('custom_amount', '')
            
            if not transport_company:
                return False, 'Please select a transport company.'
                
            try:
                amount = int(custom_amount)
                if amount < 50:
                    return False, 'Transport voucher amount must be at least R50.'
            except ValueError:
                return False, 'Please enter a valid amount for transport voucher.'
                
        return True, None
        
    except Exception as e:
        return False, f'Error validating voucher details: {str(e)}'

def process_voucher_purchase(firebase_uid, item_name, form_data, price, quantity=1):
    try:
        # For airtime and data vouchers, get network
        network = None
        if 'airtime' in item_name.lower() or 'data' in item_name.lower():
            network = form_data.get('network')
            if not network:
                raise ValueError('Please select a network provider')

        # For transport vouchers, handle custom amount
        transport_company = None
        custom_amount = None
        if 'transport' in item_name.lower():
            transport_company = form_data.get('transport_company')
            custom_amount = form_data.get('custom_amount')
            if not transport_company:
                raise ValueError('Please select a transport company')
            try:
                custom_amount = int(custom_amount)
                if custom_amount < 50:
                    raise ValueError('Transport voucher amount must be at least R50')
            except (ValueError, TypeError):
                raise ValueError('Please enter a valid amount for transport voucher')
        
        # Create vouchers
        vouchers = []
        for _ in range(quantity):
            if 'transport' in item_name.lower():
                amount = custom_amount
                voucher_type = f"transport_{transport_company}"
            elif 'airtime' in item_name.lower():
                amount = price
                voucher_type = f"airtime_{network}"
            elif 'data' in item_name.lower():
                amount = price
                voucher_type = f"data_{network}"
            else:
                amount = price
                voucher_type = item_name.lower().replace(' voucher', '').replace(' ', '_')
            
            code = create_voucher(firebase_uid, voucher_type, amount)
            if code:
                vouchers.append(code)
            else:
                raise ValueError('Failed to create voucher')
        
        return vouchers, custom_amount if custom_amount else price
        
    except Exception as e:
        raise ValueError(str(e))

@rewards_bp.route('/marketplace/orders', methods=['GET'])
def marketplace_orders():
    firebase_uid = session.get('user_id')
    if not firebase_uid:
        return redirect(url_for('login'))
        
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT o.id, i.name, o.quantity, o.total_points, o.status, o.created_at
            FROM marketplace_orders o
            JOIN marketplace_items i ON o.item_id = i.id
            WHERE o.user_id = %s
            ORDER BY o.created_at DESC
        """, (firebase_uid,))
        orders = [
            {
                'id': row[0], 
                'item_name': row[1], 
                'quantity': row[2], 
                'total_points': row[3], 
                'status': row[4], 
                'created_at': row[5]
            } for row in cur.fetchall()
        ]
        return render_template('marketplace_orders.html', orders=orders)
    except Exception as e:
        flash(f'Error retrieving orders: {str(e)}', 'error')
        return redirect(url_for('rewards.marketplace'))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

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
        flash('Please log in to view your vouchers.', 'error')
        return redirect(url_for('login'))
    
    # Get internal user ID
    user_id = get_internal_user_id(firebase_uid)
    if not user_id:
        flash('User account not found.', 'error')
        return redirect(url_for('login'))
    
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get user's vouchers
        cur.execute("""
            SELECT id, voucher_type, code, amount, status, created_at, redeemed_at
            FROM vouchers 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (user_id,))
        
        vouchers = [
            {
                'id': row[0],
                'type': row[1],
                'code': row[2],
                'amount': row[3],
                'status': row[4],
                'created_at': row[5],
                'redeemed_at': row[6]
            }
            for row in cur.fetchall()
        ]
        
        return render_template('vouchers.html', vouchers=vouchers)
        
    except Exception as e:
        flash(f'Error retrieving vouchers: {str(e)}', 'error')
        return redirect(url_for('rewards.rewards_card_page'))
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@rewards_bp.route('/vouchers/redeem/<voucher_code>', methods=['POST'])
def redeem_voucher(voucher_code):
    firebase_uid = session.get('user_id')
    if not firebase_uid:
        return jsonify({'error': 'User not authenticated'}), 401
        
    # Get internal user ID
    user_id = get_internal_user_id(firebase_uid)
    if not user_id:
        return jsonify({'error': 'User account not found'}), 404
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if voucher exists and belongs to user
    cur.execute("""
        SELECT id, voucher_type, amount, status 
        FROM vouchers 
        WHERE code = %s AND user_id = %s
    """, (voucher_code, user_id))
    
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
        SET status = 'used', redeemed_at = NOW() 
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