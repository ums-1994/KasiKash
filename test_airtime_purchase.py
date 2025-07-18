#!/usr/bin/env python3
"""
Test script to verify airtime purchase functionality works without database errors.
"""

import requests
import json

def test_airtime_purchase():
    """Test the airtime purchase API endpoint."""
    
    # Test data
    test_data = {
        "amount": 15,
        "phone_number": "0821234567"
    }
    
    print("Testing airtime purchase functionality...")
    print(f"Test data: {test_data}")
    
    try:
        # Test the API endpoint
        response = requests.post(
            "http://localhost:5000/rewards/api/rewards/airtime",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Response: {result}")
        else:
            print(f"Error response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the application. Make sure it's running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Error testing airtime purchase: {e}")

def test_notification_count():
    """Test the notification count endpoint."""
    
    print("\nTesting notification count endpoint...")
    
    try:
        response = requests.get("http://localhost:5000/notifications/count")
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Notification count endpoint working")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the application")
    except Exception as e:
        print(f"❌ Error testing notification count: {e}")

if __name__ == "__main__":
    test_airtime_purchase()
    test_notification_count() 