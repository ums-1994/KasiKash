#!/usr/bin/env python3
"""
Script to help set up OpenRouter API key for KasiKash chatbot
"""

import os
from dotenv import load_dotenv

def setup_openrouter():
    print("=== KasiKash OpenRouter Setup ===")
    print()
    print("To use the chatbot with Google Gemma 3n 4B model, you need an OpenRouter API key.")
    print()
    print("Steps to get your OpenRouter API key:")
    print("1. Go to https://openrouter.ai/")
    print("2. Sign up or log in to your account")
    print("3. Go to your API Keys section")
    print("4. Create a new API key")
    print("5. Copy the API key")
    print()
    
    # Check if .env file exists
    env_file = '.env'
    if not os.path.exists(env_file):
        print(f"Creating {env_file} file...")
        # Copy from template
        with open('env_template.txt', 'r') as template:
            with open(env_file, 'w') as env:
                env.write(template.read())
        print(f"{env_file} file created from template.")
    
    # Load current .env
    load_dotenv()
    
    # Check if OpenRouter API key is already set
    current_key = os.getenv('OPENROUTER_API_KEY')
    if current_key and current_key != 'your-openrouter-api-key-here':
        print(f"OpenRouter API key is already configured: {current_key[:10]}...")
        response = input("Do you want to update it? (y/n): ").lower()
        if response != 'y':
            print("Setup cancelled.")
            return
    
    # Get new API key
    print()
    api_key = input("Enter your OpenRouter API key: ").strip()
    
    if not api_key:
        print("No API key provided. Setup cancelled.")
        return
    
    # Update .env file
    try:
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Find and replace the OpenRouter API key line
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('OPENROUTER_API_KEY='):
                lines[i] = f'OPENROUTER_API_KEY={api_key}\n'
                updated = True
                break
        
        if not updated:
            # Add the line if it doesn't exist
            lines.append(f'OPENROUTER_API_KEY={api_key}\n')
        
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        print()
        print("✅ OpenRouter API key configured successfully!")
        print("You can now restart your Flask app to use the chatbot with Google Gemma 3n 4B.")
        print()
        print("Note: The chatbot will use the free Google Gemma 3n 4B model through OpenRouter.")
        
    except Exception as e:
        print(f"Error updating {env_file}: {e}")
        print("Please manually add OPENROUTER_API_KEY=your-key to your .env file")

if __name__ == "__main__":
    setup_openrouter() 