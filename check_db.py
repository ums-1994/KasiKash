#!/usr/bin/env python3
import sqlite3

def check_expense_db():
    try:
        conn = sqlite3.connect('expense.db')
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("Tables in expense.db:")
        for table in tables:
            print(f"  - {table[0]}")
            
        # Check if any of these tables have data
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} rows")
            
        conn.close()
        
    except Exception as e:
        print(f"Error checking expense.db: {e}")

if __name__ == "__main__":
    check_expense_db() 