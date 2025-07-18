#!/usr/bin/env python3
"""
Flask Language Configuration Updater
This script helps update your Flask app to support all South African languages.
"""

import os
import re

# South African languages configuration
SA_LANGUAGES = {
    'af': 'Afrikaans',
    'en': 'English', 
    'nr': 'isiNdebele',
    'xh': 'isiXhosa',
    'zu': 'isiZulu',
    'nso': 'Sepedi',
    'st': 'Sesotho',
    'tn': 'Setswana',
    'ss': 'siSwati',
    've': 'Tshivenda',
    'ts': 'Xitsonga'
}

def find_flask_app_file():
    """Find the main Flask application file"""
    possible_files = ['main.py', 'app.py', 'application.py', 'wsgi.py']
    
    for file in possible_files:
        if os.path.exists(file):
            return file
    return None

def update_flask_config():
    """Update Flask app configuration to include all SA languages"""
    app_file = find_flask_app_file()
    
    if not app_file:
        print("❌ Could not find Flask application file")
        print("Please ensure you have one of: main.py, app.py, application.py, wsgi.py")
        return False
    
    print(f"📁 Found Flask app file: {app_file}")
    
    # Read the current file
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if Babel is already configured
    if 'Babel' in content or 'babel' in content:
        print("✅ Babel appears to be already configured")
        
        # Look for LANGUAGES configuration
        languages_pattern = r'LANGUAGES\s*=\s*\{[^}]*\}'
        if re.search(languages_pattern, content):
            print("✅ LANGUAGES configuration found")
            return True
        else:
            print("⚠️  Babel configured but LANGUAGES not found")
    else:
        print("⚠️  Babel not found in Flask app")
    
    # Generate the configuration snippet
    config_snippet = f'''
# Flask-Babel Configuration for South African Languages
from flask_babel import Babel

babel = Babel(app)

# Configure supported languages
LANGUAGES = {{
    'en': 'English',
    'af': 'Afrikaans',
    'nr': 'isiNdebele', 
    'xh': 'isiXhosa',
    'zu': 'isiZulu',
    'nso': 'Sepedi',
    'st': 'Sesotho',
    'tn': 'Setswana',
    'ss': 'siSwati',
    've': 'Tshivenda',
    'ts': 'Xitsonga'
}}

# Language selector function
@babel.localeselector
def get_locale():
    # Try to get language from URL parameter
    language = request.args.get('lang')
    if language and language in LANGUAGES:
        return language
    
    # Try to get language from user preferences
    if hasattr(g, 'user') and g.user and g.user.language:
        return g.user.language
    
    # Default to English
    return 'en'

# Set the locale selector
babel.locale_selector_func = get_locale
'''
    
    print("\n📝 Here's the configuration to add to your Flask app:")
    print("=" * 60)
    print(config_snippet)
    print("=" * 60)
    
    # Also generate a language switcher template
    language_switcher_template = '''
<!-- Language Switcher Template -->
<div class="language-switcher">
    <label for="language-select">Language / Taal / Ulimi:</label>
    <select id="language-select" onchange="changeLanguage(this.value)">
        <option value="en" {% if request.args.get('lang') == 'en' %}selected{% endif %}>English</option>
        <option value="af" {% if request.args.get('lang') == 'af' %}selected{% endif %}>Afrikaans</option>
        <option value="nr" {% if request.args.get('lang') == 'nr' %}selected{% endif %}>isiNdebele</option>
        <option value="xh" {% if request.args.get('lang') == 'xh' %}selected{% endif %}>isiXhosa</option>
        <option value="zu" {% if request.args.get('lang') == 'zu' %}selected{% endif %}>isiZulu</option>
        <option value="nso" {% if request.args.get('lang') == 'nso' %}selected{% endif %}>Sepedi</option>
        <option value="st" {% if request.args.get('lang') == 'st' %}selected{% endif %}>Sesotho</option>
        <option value="tn" {% if request.args.get('lang') == 'tn' %}selected{% endif %}>Setswana</option>
        <option value="ss" {% if request.args.get('lang') == 'ss' %}selected{% endif %}>siSwati</option>
        <option value="ve" {% if request.args.get('lang') == 've' %}selected{% endif %}>Tshivenda</option>
        <option value="ts" {% if request.args.get('lang') == 'ts' %}selected{% endif %}>Xitsonga</option>
    </select>
</div>

<script>
function changeLanguage(lang) {
    const currentUrl = new URL(window.location);
    currentUrl.searchParams.set('lang', lang);
    window.location.href = currentUrl.toString();
}
</script>
'''
    
    print("\n🌐 Language Switcher Template:")
    print("=" * 60)
    print(language_switcher_template)
    print("=" * 60)
    
    return True

def create_template_markup_guide():
    """Create a guide for marking up templates"""
    guide = '''
# Template Markup Guide

## In your HTML templates, use these patterns:

### 1. Simple text translation:
{{ _('Welcome to KasiKash') }}

### 2. Plural forms:
{{ ngettext('%(num)d member', '%(num)d members', count) }}

### 3. Variables in translations:
{{ _('Hello %(name)s!', name=user.name) }}

### 4. Comments for translators:
{# Translators: This is a button label #}
{{ _('Submit') }}

## In your Python code:

### 1. Import the translation function:
from flask_babel import gettext as _

### 2. Use in your views:
@app.route('/')
def home():
    message = _('Welcome to our platform')
    return render_template('home.html', message=message)

### 3. For plural forms:
from flask_babel import ngettext
count = 5
message = ngettext('%(num)d item', '%(num)d items', count) % {'num': count}

## Common phrases to translate:
- Welcome messages
- Navigation menu items
- Form labels and buttons
- Error messages
- Success messages
- Page titles
- Help text
'''
    
    with open('template_markup_guide.md', 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print("📖 Created template_markup_guide.md")

def main():
    print("🌍 South African Languages Flask Configuration Helper")
    print("=" * 50)
    
    # Update Flask configuration
    success = update_flask_config()
    
    if success:
        print("\n✅ Configuration helper completed!")
        print("\n📋 Next steps:")
        print("1. Add the configuration snippet to your Flask app")
        print("2. Add the language switcher to your templates")
        print("3. Mark up your templates with translation functions")
        print("4. Run the PowerShell script to generate translation files")
        print("5. Edit the .po files with translations")
        print("6. Compile the translations")
    else:
        print("\n❌ Configuration helper failed")
    
    # Create template markup guide
    create_template_markup_guide()
    print("\n📖 Template markup guide created: template_markup_guide.md")

if __name__ == '__main__':
    main() 