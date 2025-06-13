#!/usr/bin/env python3
import sqlite3

def check_tables():
    try:
        conn = sqlite3.connect('kasikash.db')
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("Tables in kasikash.db:")
        for table in tables:
            print(f"  - {table[0]}")
            
        # Check if critical tables exist
        critical_tables = ['users', 'stokvels', 'transactions', 'savings_goals', 'payment_methods']
        missing_tables = []
        
        for table in critical_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                missing_tables.append(table)
        
        if missing_tables:
            print(f"\nMissing critical tables: {missing_tables}")
        else:
            print("\nAll critical tables exist!")
            
        conn.close()
        
    except Exception as e:
        print(f"Error checking tables: {e}")

if __name__ == "__main__":
    check_tables() 