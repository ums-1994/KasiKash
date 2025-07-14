#!/usr/bin/env python3
"""
Test script to verify logger fix in main.py
"""

import sys
import os

def test_logger_import():
    """Test that main.py can be imported without logger errors"""
    try:
        # Add current directory to path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Test importing main.py
        import main
        print("✓ main.py imported successfully")
        
        # Test that logger is defined
        if hasattr(main, 'logger'):
            print("✓ logger is properly defined in main.py")
        else:
            print("✗ logger is not defined in main.py")
            return False
            
        # Test that logger can be used
        try:
            main.logger.info("Test log message")
            print("✓ logger can be used without errors")
        except Exception as e:
            print(f"✗ logger usage failed: {e}")
            return False
            
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_utils_import():
    """Test that utils.py functions are properly imported"""
    try:
        import utils
        
        # Test that required functions exist
        required_functions = ['get_notification_count', 'create_notification', 'login_required']
        for func_name in required_functions:
            if hasattr(utils, func_name):
                print(f"✓ {func_name} is available in utils.py")
            else:
                print(f"✗ {func_name} is missing from utils.py")
                return False
                
        return True
        
    except ImportError as e:
        print(f"✗ utils.py import error: {e}")
        return False
    except Exception as e:
        print(f"✗ utils.py unexpected error: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing KasiKash app fixes...")
    print("=" * 50)
    
    # Test logger fix
    print("\n1. Testing logger fix:")
    logger_ok = test_logger_import()
    
    # Test utils import
    print("\n2. Testing utils import:")
    utils_ok = test_utils_import()
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY:")
    if logger_ok and utils_ok:
        print("✓ All tests passed! The logger issue is fixed.")
        print("✓ The app should now run without NameError exceptions.")
        return True
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 