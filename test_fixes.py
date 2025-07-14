#!/usr/bin/env python3
"""
Test script to verify KasiKash app fixes
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all required modules can be imported"""
    logger.info("Testing imports...")
    
    try:
        import flask
        logger.info("✓ Flask imported successfully")
    except ImportError as e:
        logger.error(f"✗ Flask import failed: {e}")
        return False
    
    try:
        import psycopg2
        logger.info("✓ psycopg2 imported successfully")
    except ImportError as e:
        logger.error(f"✗ psycopg2 import failed: {e}")
        return False
    
    try:
        import firebase_admin
        logger.info("✓ firebase_admin imported successfully")
    except ImportError as e:
        logger.error(f"✗ firebase_admin import failed: {e}")
        return False
    
    try:
        import pandas
        logger.info("✓ pandas imported successfully")
    except ImportError as e:
        logger.error(f"✗ pandas import failed: {e}")
        return False
    
    try:
        import plotly
        logger.info("✓ plotly imported successfully")
    except ImportError as e:
        logger.error(f"✗ plotly import failed: {e}")
        return False
    
    try:
        from flask_session import Session
        logger.info("✓ Flask-Session imported successfully")
    except ImportError as e:
        logger.error(f"✗ Flask-Session import failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration loading"""
    logger.info("Testing configuration...")
    
    try:
        from config import Config
        logger.info("✓ Configuration module imported successfully")
        
        # Test required environment variables
        required_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']
        missing_vars = []
        
        for var in required_vars:
            if not getattr(Config, var, None):
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"⚠ Missing environment variables: {missing_vars}")
        else:
            logger.info("✓ All required environment variables are set")
            
    except ImportError as e:
        logger.error(f"✗ Configuration import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database connection"""
    logger.info("Testing database connection...")
    
    try:
        from database import verify_database_connection
        if verify_database_connection():
            logger.info("✓ Database connection successful")
            return True
        else:
            logger.error("✗ Database connection failed")
            return False
    except Exception as e:
        logger.error(f"✗ Database test failed: {e}")
        return False

def test_firebase():
    """Test Firebase configuration"""
    logger.info("Testing Firebase configuration...")
    
    try:
        import firebase_admin
        from firebase_admin import credentials
        
        # Check if Firebase is initialized
        if not firebase_admin._apps:
            logger.warning("⚠ Firebase not initialized - this is normal if no service account key is provided")
        else:
            logger.info("✓ Firebase initialized successfully")
        
        return True
    except Exception as e:
        logger.error(f"✗ Firebase test failed: {e}")
        return False

def test_file_structure():
    """Test required file structure"""
    logger.info("Testing file structure...")
    
    required_dirs = [
        'static/profile_pics',
        'static/kyc_docs',
        'flask_session_data'
    ]
    
    missing_dirs = []
    for directory in required_dirs:
        if not os.path.exists(directory):
            missing_dirs.append(directory)
    
    if missing_dirs:
        logger.warning(f"⚠ Missing directories: {missing_dirs}")
        logger.info("Creating missing directories...")
        for directory in missing_dirs:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"✓ Created directory: {directory}")
    else:
        logger.info("✓ All required directories exist")
    
    return True

def test_main_app():
    """Test main application import"""
    logger.info("Testing main application...")
    
    try:
        # Test importing main app components
        from main import app
        logger.info("✓ Main application imported successfully")
        
        # Test basic app configuration
        if hasattr(app, 'config'):
            logger.info("✓ App configuration exists")
        else:
            logger.error("✗ App configuration missing")
            return False
        
        return True
    except Exception as e:
        logger.error(f"✗ Main application test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting KasiKash app fix verification...")
    logger.info("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_config),
        ("File Structure Test", test_file_structure),
        ("Database Test", test_database),
        ("Firebase Test", test_firebase),
        ("Main App Test", test_main_app),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! The app should work correctly.")
        return 0
    else:
        logger.warning("⚠ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 