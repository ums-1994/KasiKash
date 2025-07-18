#!/usr/bin/env python3
"""
Script to add sample marketplace items for vouchers
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host="localhost",
        database="kasikash_db",
        user="kasikash_user",
        password="kasikash_password"
    )

def add_marketplace_items():
    """Add sample marketplace items"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Sample voucher items
    voucher_items = [
        {
            'name': 'Airtime Voucher',
            'description': 'Get R20 airtime voucher for your mobile phone',
            'price_in_points': 15,
            'is_active': True
        },
        {
            'name': 'Electricity Voucher',
            'description': 'Get R20 electricity voucher for your prepaid meter',
            'price_in_points': 20,
            'is_active': True
        },
        {
            'name': 'Data Bundle Voucher',
            'description': 'Get 1GB data bundle voucher for your mobile',
            'price_in_points': 30,
            'is_active': True
        },
        {
            'name': 'Movie Ticket Voucher',
            'description': 'Get a movie ticket voucher for local cinemas',
            'price_in_points': 50,
            'is_active': True
        },
        {
            'name': 'Transport Voucher',
            'description': 'Get R25 transport voucher for local taxi services',
            'price_in_points': 25,
            'is_active': True
        },
        {
            'name': 'Clothing Store Voucher',
            'description': 'Get R60 voucher for local clothing stores',
            'price_in_points': 60,
            'is_active': True
        },
        {
            'name': 'Food Delivery Voucher',
            'description': 'Get R40 voucher for food delivery services',
            'price_in_points': 40,
            'is_active': True
        },
        {
            'name': 'School Supplies Pack',
            'description': 'Get R35 voucher for school supplies and books',
            'price_in_points': 35,
            'is_active': True
        },
        {
            'name': 'Health & Wellness Voucher',
            'description': 'Get R20 voucher for health and wellness services',
            'price_in_points': 20,
            'is_active': True
        }
    ]
    
    # Non-voucher items
    other_items = [
        {
            'name': 'Community Donation',
            'description': 'Donate points to community development projects',
            'price_in_points': 0,  # Variable amount
            'is_active': True
        },
        {
            'name': 'Grocery Store Gift Card',
            'description': 'Get R50 gift card for local grocery stores',
            'price_in_points': 45,
            'is_active': True
        },
        {
            'name': 'Restaurant Voucher',
            'description': 'Get R80 voucher for local restaurants',
            'price_in_points': 70,
            'is_active': True
        }
    ]
    
    all_items = voucher_items + other_items
    
    try:
        # Clear existing items (optional - comment out if you want to keep existing)
        cur.execute("DELETE FROM marketplace_items")
        print("Cleared existing marketplace items")
        
        # Add new items
        for item in all_items:
            cur.execute("""
                INSERT INTO marketplace_items (name, description, price_in_points, is_active, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (item['name'], item['description'], item['price_in_points'], item['is_active']))
            print(f"Added: {item['name']} - {item['price_in_points']} points")
        
        conn.commit()
        print(f"\nSuccessfully added {len(all_items)} marketplace items!")
        
    except Exception as e:
        print(f"Error adding marketplace items: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    add_marketplace_items() 