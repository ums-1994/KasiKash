#!/usr/bin/env python3
"""
Test script to verify OpenRouter connection with Google Gemma 3n 4B
"""

import os
from dotenv import load_dotenv
import requests
import json

def test_openrouter():
    print("=== Testing OpenRouter Connection ===")
    
    # Load environment variables
    load_dotenv()
    
    # Check if API key is set
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key or api_key == 'your-openrouter-api-key-here':
        print("❌ OpenRouter API key not found in .env file")
        print("Please run: python setup_openrouter.py")
        return False
    
    print(f"✅ OpenRouter API key found: {api_key[:10]}...")
    
    # Test API call using requests
    try:
        print("🔄 Testing API call with Google Gemma 3n 4B...")
        
        system_prompt = "You are a helpful assistant for a stokvel (community savings) app called KasiKash."
        user_message = "Hello! Can you explain what a stokvel is?"
        full_message = f"{system_prompt}\n\n{user_message}"
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://kasikash.com",
                "X-Title": "KasiKash",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": "google/gemma-3n-e4b-it:free",
                "messages": [
                    {
                        "role": "user",
                        "content": full_message
                    }
                ],
                "max_tokens": 200,
                "temperature": 0.7
            })
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            print("✅ API call successful!")
            print(f"Response: {ai_response}")
            return True
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

if __name__ == "__main__":
    success = test_openrouter()
    if success:
        print("\n🎉 OpenRouter is working correctly!")
        print("Your chatbot is ready to use Google Gemma 3n 4B.")
    else:
        print("\n💡 Please check your OpenRouter API key and try again.") 