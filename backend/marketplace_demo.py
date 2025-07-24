import os
import psycopg2
from flask import Blueprint, request, session, redirect, url_for, flash, render_template
import random
import string
from dotenv import load_dotenv
from flask_mail import Message
from your_flask_app import mail  # Adjust import as needed for your app
import sys

load_dotenv()

# Demo Blueprint (now using real DB)
marketplace_bp = Blueprint('marketplace', __name__)

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def get_user_card(user_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            return {"balance": row[0]} if row else {"balance": 0}

def deduct_points(user_id, amount):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (amount, user_id))
            conn.commit()

def record_redemption(user_id, reward_type, amount, extra=None):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO redemptions (user_id, reward_type, amount, extra) VALUES (%s, %s, %s, %s)",
                (user_id, reward_type, amount, str(extra))
            )
            conn.commit()

def generate_voucher_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def create_notification(user_id, message):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
                (user_id, message)
            )
            conn.commit()

def send_voucher_email(user_id, code, network, reward_type):
    # Fetch user email from DB
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT email FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            if not row:
                return
            email = row[0]
    subject = f"Your {network} {reward_type.capitalize()} Voucher Code"
    body = f"Congratulations!\n\nYour {network} {reward_type} voucher code is: {code}\n\nThank you for using KasiKash!"
    msg = Message(subject, recipients=[email], body=body)
    mail.send(msg)

@marketplace_bp.route('/rewards/marketplace/voucher/<code>')
def show_voucher(code):
    return render_template('show_voucher.html', code=code)

@marketplace_bp.route('/rewards/marketplace/redeem/<reward_type>', methods=['POST'])
def redeem_reward(reward_type):
    try:
        user_id = session.get('user_id')
        print(f"[DEBUG] redeem_reward called for user_id: {user_id}")
        if not user_id:
            print("[ERROR] No user_id in session.")
            flash("Please log in.", "error")
            return redirect(url_for('login'))
        card = get_user_card(user_id)
        print(f"[DEBUG] Card before: {card}")
        reward_costs = {
            "airtime": 15,
            "electricity": 20,
            "data": 25
        }
        if reward_type in reward_costs:
            cost = reward_costs[reward_type]
            if card["balance"] < cost:
                print(f"[ERROR] Insufficient points. Balance: {card['balance']}, Cost: {cost}")
                flash("Insufficient points.", "error")
                return redirect(url_for('rewards_card'))
            network = request.form.get('network') if reward_type in ['airtime', 'data'] else None
            print(f"[DEBUG] Form network: {network}")
            deduct_points(user_id, cost)
            card_after = get_user_card(user_id)
            print(f"[DEBUG] Card after deduction: {card_after}")
            code = generate_voucher_code()
            print(f"[DEBUG] Generated voucher code: {code}")
            record_redemption(user_id, reward_type, cost, {"voucher_code": code, "network": network})
            print(f"[DEBUG] Redemption recorded in DB.")
            if network:
                create_notification(user_id, f"Your {network} {reward_type} voucher code: {code}")
                print(f"[DEBUG] Notification created for {network} {reward_type}.")
                send_voucher_email(user_id, code, network, reward_type)
                print(f"[DEBUG] Email sent for {network} {reward_type}.")
            else:
                create_notification(user_id, f"Your {reward_type} voucher code: {code}")
                print(f"[DEBUG] Notification created for {reward_type}.")
                send_voucher_email(user_id, code, '', reward_type)
                print(f"[DEBUG] Email sent for {reward_type}.")
            return redirect(url_for('marketplace.show_voucher', code=code))
        elif reward_type == "donate":
            amount = int(request.form.get('amount', 0))
            cause = request.form.get('cause', 'community')
            print(f"[DEBUG] Donation amount: {amount}, cause: {cause}")
            if card["balance"] < amount or amount <= 0:
                print(f"[ERROR] Invalid donation amount. Balance: {card['balance']}, Amount: {amount}")
                flash("Invalid donation amount.", "error")
                return redirect(url_for('rewards_card'))
            deduct_points(user_id, amount)
            card_after = get_user_card(user_id)
            print(f"[DEBUG] Card after donation deduction: {card_after}")
            record_redemption(user_id, "donation", amount, {"cause": cause})
            print(f"[DEBUG] Donation redemption recorded in DB.")
            create_notification(user_id, f"Thank you for donating {amount} points to {cause}!")
            print(f"[DEBUG] Donation notification created.")
            flash(f"Thank you for donating {amount} points to {cause}!", "success")
            return redirect(url_for('rewards_card'))
        else:
            print(f"[ERROR] Unknown reward type: {reward_type}")
            flash("Unknown reward type.", "error")
            return redirect(url_for('rewards_card'))
    except Exception as e:
        print(f"[EXCEPTION] {e}", file=sys.stderr)
        flash("An error occurred during redemption. Please contact support.", "error")
        return redirect(url_for('rewards_card')) 