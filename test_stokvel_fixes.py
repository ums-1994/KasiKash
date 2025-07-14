#!/usr/bin/env python3
"""
Comprehensive test script for KasiKash stokvel feature fixes
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_stokvel_database():
    """Test if stokvel tables exist and can be accessed"""
    print("🔍 Testing stokvel database setup...")
    
    try:
        import support
        
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Check if stokvels table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'stokvels'
                    );
                """)
                exists = cur.fetchone()[0]
                
                if exists:
                    print("✅ Stokvels table exists")
                    
                    # Check table structure
                    cur.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'stokvels'
                        ORDER BY ordinal_position;
                    """)
                    columns = cur.fetchall()
                    print(f"📋 Stokvels table columns: {[col[0] for col in columns]}")
                    
                    # Check if stokvel_members table exists
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'stokvel_members'
                        );
                    """)
                    members_exists = cur.fetchone()[0]
                    
                    if members_exists:
                        print("✅ Stokvel_members table exists")
                    else:
                        print("❌ Stokvel_members table missing")
                        return False
                        
                else:
                    print("❌ Stokvels table missing")
                    return False
                    
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_stokvel_routes():
    """Test stokvel routes are accessible"""
    print("\n🔍 Testing stokvel routes...")
    
    base_url = "http://localhost:8080"
    
    # Test routes that should be accessible
    routes_to_test = [
        "/stokvels",
        "/create_stokvel",
        "/contributions",
        "/make_contribution",
        "/payouts",
        "/request_payout"
    ]
    
    for route in routes_to_test:
        try:
            response = requests.get(f"{base_url}{route}", timeout=5)
            if response.status_code in [200, 302, 401]:  # 401 is expected for unauthenticated
                print(f"✅ {route} - Status: {response.status_code}")
            else:
                print(f"⚠️  {route} - Unexpected status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {route} - Connection failed (app may not be running)")
        except Exception as e:
            print(f"❌ {route} - Error: {e}")

def test_stokvel_template_fixes():
    """Test if template fixes are working"""
    print("\n🔍 Testing stokvel template fixes...")
    
    # Check if templates exist
    templates_to_check = [
        "templates/stokvels.html",
        "templates/stokvel_members.html",
        "templates/contributions.html",
        "templates/make_contribution.html"
    ]
    
    for template in templates_to_check:
        if os.path.exists(template):
            print(f"✅ {template} exists")
            
            # Check for merge conflicts
            with open(template, 'r', encoding='utf-8') as f:
                content = f.read()
                if '<<<<<<< HEAD' in content or '=======' in content or '>>>>>>>' in content:
                    print(f"❌ {template} contains merge conflicts")
                else:
                    print(f"✅ {template} is clean")
        else:
            print(f"❌ {template} missing")

def test_stokvel_form_validation():
    """Test stokvel form validation"""
    print("\n🔍 Testing stokvel form validation...")
    
    # Test create stokvel form fields
    create_stokvel_fields = [
        'name',
        'description', 
        'monthly_contribution',
        'target_amount',
        'target_date'
    ]
    
    print("📋 Create stokvel form should include:")
    for field in create_stokvel_fields:
        print(f"  - {field}")
    
    # Check if template has these fields
    try:
        with open("templates/stokvels.html", 'r', encoding='utf-8') as f:
            content = f.read()
            missing_fields = []
            for field in create_stokvel_fields:
                if field not in content:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ Missing fields in template: {missing_fields}")
            else:
                print("✅ All required fields present in template")
    except Exception as e:
        print(f"❌ Error checking template: {e}")

def test_stokvel_functionality():
    """Test core stokvel functionality"""
    print("\n🔍 Testing stokvel functionality...")
    
    try:
        import support
        
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Test creating a stokvel
                print("🧪 Testing stokvel creation...")
                
                # Check if we can insert into stokvels table
                cur.execute("""
                    INSERT INTO stokvels (name, description, created_by, monthly_contribution, target_amount, target_date)
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                """, ('Test Stokvel', 'Test Description', 'test_user_id', 100.00, 1000.00, '2025-12-31'))
                
                stokvel_id = cur.fetchone()[0]
                print(f"✅ Test stokvel created with ID: {stokvel_id}")
                
                # Test adding member
                cur.execute("""
                    INSERT INTO stokvel_members (stokvel_id, user_id, role)
                    VALUES (%s, %s, %s)
                """, (stokvel_id, 'test_user_id', 'admin'))
                print("✅ Test member added")
                
                # Clean up test data
                cur.execute("DELETE FROM stokvel_members WHERE stokvel_id = %s", (stokvel_id,))
                cur.execute("DELETE FROM stokvels WHERE id = %s", (stokvel_id,))
                conn.commit()
                print("✅ Test data cleaned up")
                
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")

def main():
    """Run all stokvel tests"""
    print("🚀 Starting KasiKash Stokvel Feature Tests\n")
    
    # Run tests
    tests = [
        ("Database Setup", test_stokvel_database),
        ("Template Fixes", test_stokvel_template_fixes),
        ("Form Validation", test_stokvel_form_validation),
        ("Core Functionality", test_stokvel_functionality),
        ("Route Accessibility", test_stokvel_routes)
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
        print("🎉 All stokvel tests passed! The feature should be working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    main() 