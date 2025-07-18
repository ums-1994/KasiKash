#!/usr/bin/env python3
"""
Test script for language switching functionality in KasiKash admin interface
"""

import requests
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_language_switching():
    """Test language switching functionality"""
    
    # Base URL for the Flask app
    base_url = "http://localhost:5000"
    
    # Test languages
    languages = {
        'en': 'English',
        'af': 'Afrikaans', 
        'nr': 'Southern Ndebele',
        'xh': 'Xhosa',
        'zu': 'Zulu',
        'nso': 'Northern Sotho',
        'st': 'Southern Sotho',
        'tn': 'Tswana',
        'ss': 'Swati',
        've': 'Venda',
        'ts': 'Tsonga'
    }
    
    print("🌐 Testing Language Switching Functionality")
    print("=" * 50)
    
    # Test admin settings page with different languages
    for lang_code, lang_name in languages.items():
        try:
            # Test admin settings page with language parameter
            url = f"{base_url}/admin/admin/settings?lang={lang_code}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {lang_name} ({lang_code}): Admin settings page accessible")
                
                # Check if language parameter is properly handled
                if f'lang={lang_code}' in response.text or lang_code in response.text:
                    print(f"   └─ Language parameter correctly applied")
                else:
                    print(f"   ⚠─ Language parameter may not be working")
                    
            else:
                print(f"❌ {lang_name} ({lang_code}): HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {lang_name} ({lang_code}): Connection error - {e}")
        except Exception as e:
            print(f"❌ {lang_name} ({lang_code}): Error - {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Language Switching Test Summary:")
    print("• All 11 South African languages should be supported")
    print("• Language parameter should be preserved in URLs")
    print("• Admin interface should display in selected language")
    print("• Translation files should be loaded correctly")
    
    print("\n📋 Next Steps:")
    print("1. Start the Flask app: python main.py")
    print("2. Navigate to: http://localhost:5000/admin/admin/settings")
    print("3. Test language switching using the dropdown")
    print("4. Verify translations are working correctly")
    print("5. Check that language preference is saved in database")

def test_translation_files():
    """Test if translation files exist and are properly formatted"""
    
    print("\n📁 Testing Translation Files")
    print("=" * 30)
    
    languages = ['en', 'af', 'nr', 'xh', 'zu', 'nso', 'st', 'tn', 'ss', 've', 'ts']
    
    for lang in languages:
        po_file = f"translations/{lang}/LC_MESSAGES/messages.po"
        
        if os.path.exists(po_file):
            file_size = os.path.getsize(po_file)
            if file_size > 0:
                print(f"✅ {lang}: Translation file exists ({file_size} bytes)")
            else:
                print(f"⚠️  {lang}: Translation file is empty")
        else:
            print(f"❌ {lang}: Translation file missing")
    
    print("\n📊 Translation Status:")
    print("• All .po files should exist and contain translations")
    print("• Files should be compiled to .mo format for use")
    print("• Flask-Babel should load translations automatically")

if __name__ == "__main__":
    print("🚀 KasiKash Language Switching Test")
    print("=" * 40)
    
    # Test translation files first
    test_translation_files()
    
    # Test language switching
    test_language_switching()
    
    print("\n✨ Test completed!")
    print("To run the full application:")
    print("python main.py") 