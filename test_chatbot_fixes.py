#!/usr/bin/env python3
"""
Comprehensive test script for KasiKash chatbot fixes
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_chatbot_database():
    """Test if chat_history table exists and can be created"""
    print("🔍 Testing chatbot database setup...")
    
    try:
        import support
        
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Check if table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'chat_history'
                    );
                """)
                exists = cur.fetchone()[0]
                
                if exists:
                    print("✅ chat_history table exists")
                    
                    # Test inserting a record
                    cur.execute("""
                        INSERT INTO chat_history (user_id, message, response, mode)
                        VALUES (%s, %s, %s, %s)
                    """, ('test_user', 'test message', 'test response', 'ai'))
                    conn.commit()
                    print("✅ chat_history table is writable")
                    
                    # Clean up test data
                    cur.execute("DELETE FROM chat_history WHERE user_id = 'test_user'")
                    conn.commit()
                    print("✅ chat_history table cleanup successful")
                    
                else:
                    print("❌ chat_history table does not exist")
                    print("   Run: python create_chat_history_table.py")
                    return False
                    
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    
    return True

def test_chatbot_files():
    """Test if all required chatbot files exist"""
    print("\n🔍 Testing chatbot files...")
    
    required_files = [
        'templates/chatbot.html',
        'static/css/chatbot.css',
        'static/js/chatbot.js',
        'templates/base.html'
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing!")
            all_exist = False
    
    return all_exist

def test_base_template():
    """Test if base template has correct chatbot includes"""
    print("\n🔍 Testing base template...")
    
    try:
        with open('templates/base.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ('CSRF token meta tag', 'meta name="csrf-token"'),
            ('Chatbot CSS include', 'chatbot.css'),
            ('Chatbot HTML include', "{% include 'chatbot.html' %}"),
            ('Chatbot JS include', 'chatbot.js'),
            ('No merge conflicts', '<<<<<<< HEAD'),
            ('No merge conflicts', '======='),
            ('No merge conflicts', '>>>>>>>')
        ]
        
        all_good = True
        for check_name, search_term in checks:
            if search_term in content:
                if 'merge conflicts' in check_name:
                    print(f"❌ {check_name} - Found merge conflict markers!")
                    all_good = False
                else:
                    print(f"✅ {check_name}")
            else:
                if 'merge conflicts' in check_name:
                    print(f"✅ {check_name} - No merge conflicts found")
                else:
                    print(f"❌ {check_name} - Missing!")
                    all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ Base template test failed: {e}")
        return False

def test_chatbot_html():
    """Test if chatbot HTML has required elements"""
    print("\n🔍 Testing chatbot HTML structure...")
    
    try:
        with open('templates/chatbot.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_elements = [
            'chatbot-container',
            'chatbot-main',
            'chatbot-header',
            'chatbot-messages',
            'chatbot-input',
            'chatbot-fab',
            'user-message',
            'send-message',
            'quick-tips'
        ]
        
        all_found = True
        for element in required_elements:
            if element in content:
                print(f"✅ {element}")
            else:
                print(f"❌ {element} - Missing!")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"❌ Chatbot HTML test failed: {e}")
        return False

def test_chatbot_css():
    """Test if chatbot CSS has required styles"""
    print("\n🔍 Testing chatbot CSS...")
    
    try:
        with open('static/css/chatbot.css', 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_styles = [
            '#chatbot-container',
            '#chatbot-main',
            '.message',
            '.user-message',
            '.bot-message',
            '#chatbot-fab',
            '.typing-indicator'
        ]
        
        all_found = True
        for style in required_styles:
            if style in content:
                print(f"✅ {style}")
            else:
                print(f"❌ {style} - Missing!")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"❌ Chatbot CSS test failed: {e}")
        return False

def test_chatbot_js():
    """Test if chatbot JavaScript has required functions"""
    print("\n🔍 Testing chatbot JavaScript...")
    
    try:
        with open('static/js/chatbot.js', 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_functions = [
            'sendMessage',
            'addMessage',
            'showLoading',
            'updateModeDisplay',
            'setChatbotState'
        ]
        
        all_found = True
        for func in required_functions:
            if func in content:
                print(f"✅ {func}")
            else:
                print(f"❌ {func} - Missing!")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"❌ Chatbot JavaScript test failed: {e}")
        return False

def test_dependencies():
    """Test if required Python dependencies are available"""
    print("\n🔍 Testing Python dependencies...")
    
    required_packages = [
        'requests',
        'flask',
        'firebase_admin',
        'psycopg2'
    ]
    
    all_available = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Not available!")
            all_available = False
    
    return all_available

def main():
    """Run all chatbot tests"""
    print("🚀 Starting KasiKash Chatbot Fixes Test Suite")
    print("=" * 50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Files", test_chatbot_files),
        ("Base Template", test_base_template),
        ("Chatbot HTML", test_chatbot_html),
        ("Chatbot CSS", test_chatbot_css),
        ("Chatbot JavaScript", test_chatbot_js),
        ("Database", test_chatbot_database)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Chatbot should be working properly.")
        print("\nNext steps:")
        print("1. Start the Flask app: python main.py")
        print("2. Log in to the application")
        print("3. Test the chatbot by clicking the 💬 button")
        print("4. Try both App Mode and AI Mode")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Run: python create_chat_history_table.py")
        print("- Check that all files exist in the correct locations")
        print("- Ensure all dependencies are installed: pip install -r requirements.txt")

if __name__ == "__main__":
    main() 