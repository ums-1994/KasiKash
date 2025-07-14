#!/usr/bin/env python3
"""
Comprehensive test script for KasiKash savings goals feature fixes
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_savings_goals_database():
    """Test if savings_goals table exists and can be accessed"""
    print("🔍 Testing savings goals database setup...")
    
    try:
        import support
        
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Check if savings_goals table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'savings_goals'
                    );
                """)
                exists = cur.fetchone()[0]
                
                if exists:
                    print("✅ Savings_goals table exists")
                    
                    # Check table structure
                    cur.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'savings_goals'
                        ORDER BY ordinal_position;
                    """)
                    columns = cur.fetchall()
                    print(f"📋 Savings_goals table columns: {[col[0] for col in columns]}")
                    
                    # Check if transactions table has savings_goal_id column
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'transactions' AND column_name = 'savings_goal_id'
                        );
                    """)
                    transactions_has_goal_id = cur.fetchone()[0]
                    
                    if transactions_has_goal_id:
                        print("✅ Transactions table has savings_goal_id column")
                    else:
                        print("❌ Transactions table missing savings_goal_id column")
                        return False
                        
                else:
                    print("❌ Savings_goals table missing")
                    return False
                    
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_savings_goals_template_fixes():
    """Test if template fixes are working"""
    print("\n🔍 Testing savings goals template fixes...")
    
    # Check if template exists
    template_path = "templates/savings_goals.html"
    
    if os.path.exists(template_path):
        print(f"✅ {template_path} exists")
        
        # Check for merge conflicts
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if '<<<<<<< HEAD' in content or '=======' in content or '>>>>>>>' in content:
                print(f"❌ {template_path} contains merge conflicts")
                return False
            else:
                print(f"✅ {template_path} is clean")
                
        # Check for required elements
        required_elements = [
            'createGoalModal',
            'contributeModal',
            'banner_stats',
            'progress-bar',
            'glass-card'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing elements in template: {missing_elements}")
            return False
        else:
            print("✅ All required elements present in template")
            
    else:
        print(f"❌ {template_path} missing")
        return False
        
    return True

def test_savings_goals_functionality():
    """Test core savings goals functionality"""
    print("\n🔍 Testing savings goals functionality...")
    
    try:
        import support
        
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Test creating a savings goal
                print("🧪 Testing savings goal creation...")
                
                # Check if we can insert into savings_goals table
                cur.execute("""
                    INSERT INTO savings_goals (user_id, name, target_amount, current_amount, target_date, status)
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                """, ('test_user_id', 'Test Goal', 1000.00, 0.00, '2025-12-31', 'active'))
                
                goal_id = cur.fetchone()[0]
                print(f"✅ Test savings goal created with ID: {goal_id}")
                
                # Test contributing to goal
                cur.execute("""
                    UPDATE savings_goals
                    SET current_amount = current_amount + %s
                    WHERE id = %s
                """, (100.00, goal_id))
                print("✅ Test contribution added")
                
                # Clean up test data
                cur.execute("DELETE FROM savings_goals WHERE id = %s", (goal_id,))
                conn.commit()
                print("✅ Test data cleaned up")
                
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False
        
    return True

def main():
    """Run all savings goals tests"""
    print("🚀 Starting KasiKash Savings Goals Feature Tests\n")
    
    # Run tests
    tests = [
        ("Database Setup", test_savings_goals_database),
        ("Template Fixes", test_savings_goals_template_fixes),
        ("Core Functionality", test_savings_goals_functionality)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All savings goals tests passed! The feature should be working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    main() 