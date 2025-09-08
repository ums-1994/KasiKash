#!/usr/bin/env python3
"""
Test script for KasiKash chatbot functionality
"""
import requests
import json

def test_chatbot():
    """Test the chatbot with various queries"""
    
    base_url = "http://localhost:5000"
    
    # Test cases
    test_cases = [
        "tell me about settings",
        "how do I create a stokvel",
        "what is the financial advisor",
        "how do I add members",
        "tell me about payouts",
        "what are savings goals",
        "how do I manage my profile",
        "tell me about notifications",
        "what is KYC",
        "how do I download statements"
    ]
    
    print("🧪 Testing KasiKash Chatbot App Mode")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{test_case}'")
        
        try:
            response = requests.post(
                f"{base_url}/chat",
                json={
                    "message": test_case,
                    "mode": "rule"
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Response: {data.get('response', 'No response')[:100]}...")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Chatbot testing completed!")

if __name__ == "__main__":
    test_chatbot() 