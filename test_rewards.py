#!/usr/bin/env python3
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def test_reward_system():
    """Test the reward system to see if it's working properly."""
    
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', 5432)
        )
        cur = conn.cursor()
        
        # Check if there are any users with firebase_uid
        cur.execute("SELECT firebase_uid, username, email FROM users WHERE firebase_uid IS NOT NULL LIMIT 5")
        users = cur.fetchall()
        
        print("Users with firebase_uid:")
        for user in users:
            print(f"  {user[0]} - {user[1]} ({user[2]})")
        
        if not users:
            print("No users found with firebase_uid!")
            return
        
        # Test with the first user
        test_user_firebase_uid = users[0][0]
        print(f"\nTesting with user: {test_user_firebase_uid}")
        
        # Check if user has a virtual reward card
        cur.execute("SELECT id, card_number, balance FROM virtual_reward_cards WHERE user_id = (SELECT id FROM users WHERE firebase_uid = %s)", (test_user_firebase_uid,))
        card = cur.fetchone()
        
        if card:
            print(f"User has reward card: {card[1]} with balance: {card[2]}")
        else:
            print("User does not have a reward card yet")
        
        # Check notifications for this user
        cur.execute("SELECT id, message, type, is_read, created_at FROM notifications WHERE user_id = %s ORDER BY created_at DESC LIMIT 5", (test_user_firebase_uid,))
        notifications = cur.fetchall()
        
        print(f"\nRecent notifications for user:")
        if notifications:
            for notif in notifications:
                print(f"  {notif[4]}: {notif[2]} - {notif[1]} (read: {notif[3]})")
        else:
            print("  No notifications found")
        
        # Check reward transactions
        cur.execute("""
            SELECT rt.amount, rt.transaction_type, rt.description, rt.created_at
            FROM reward_transactions rt
            JOIN users u ON rt.user_id = u.id
            WHERE u.firebase_uid = %s
            ORDER BY rt.created_at DESC LIMIT 5
        """, (test_user_firebase_uid,))
        transactions = cur.fetchall()
        
        print(f"\nRecent reward transactions:")
        if transactions:
            for trans in transactions:
                print(f"  {trans[3]}: {trans[0]} points - {trans[1]} ({trans[2]})")
        else:
            print("  No reward transactions found")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error testing reward system: {e}")

if __name__ == "__main__":
    test_reward_system() 