#!/usr/bin/env python3
"""
Translation Helper Script for KasiKash Admin Dashboard
Helps you translate admin interface text to South African languages.
"""

import os
import sys

# South African languages
SA_LANGUAGES = {
    'af': 'Afrikaans',
    'en': 'English', 
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

def show_translation_status():
    """Show the status of all translation files."""
    print("=== Translation Status ===")
    for code, name in SA_LANGUAGES.items():
        po_file = f"translations/{code}/LC_MESSAGES/messages.po"
        if os.path.exists(po_file):
            size = os.path.getsize(po_file)
            status = "Ready" if size > 500 else "Empty"
            print(f"{code:2} - {name:15} : {status} ({size} bytes)")
        else:
            print(f"{code:2} - {name:15} : Missing")

def show_sample_translations():
    """Show sample translations for common admin terms."""
    print("\n=== Sample Translations ===")
    
    samples = {
        'Dashboard': {
            'af': 'Dashboard',
            'xh': 'Ikhasi Lokubhekisa',
            'zu': 'Ikhasi Lokubheka'
        },
        'Settings': {
            'af': 'Instellings',
            'xh': 'Iisethingi',
            'zu': 'Izilungiselelo'
        },
        'Users': {
            'af': 'Gebruikers',
            'xh': 'Abasebenzisi',
            'zu': 'Abasebenzisi'
        },
        'Reports': {
            'af': 'Verslae',
            'xh': 'Iingxelo',
            'zu': 'Imibiko'
        }
    }
    
    for english, translations in samples.items():
        print(f"\n{english}:")
        for code, translation in translations.items():
            print(f"  {code}: {translation}")

def edit_translation_file(language_code):
    """Open a translation file for editing."""
    po_file = f"translations/{language_code}/LC_MESSAGES/messages.po"
    
    if not os.path.exists(po_file):
        print(f"Translation file for {language_code} not found!")
        return
    
    print(f"\n=== Editing {SA_LANGUAGES.get(language_code, language_code)} ===")
    print(f"File: {po_file}")
    print("\nTo edit this file:")
    print("1. Open the file in any text editor (Notepad, VS Code, etc.)")
    print("2. Find the English text in 'msgid' lines")
    print("3. Add your translation in the 'msgstr' line below it")
    print("4. Save the file with UTF-8 encoding")
    print("\nExample:")
    print('msgid "Dashboard"')
    print('msgstr "Ikhasi Lokubhekisa"  # Xhosa translation')
    
    # Show the file location
    abs_path = os.path.abspath(po_file)
    print(f"\nFull path: {abs_path}")

def show_common_terms():
    """Show common admin terms that need translation."""
    print("\n=== Common Admin Terms to Translate ===")
    
    terms = [
        "Dashboard", "Settings", "Users", "Reports", "Analytics",
        "Export", "Import", "Save", "Cancel", "Delete", "Edit",
        "Add", "Search", "Filter", "Status", "Date", "Amount",
        "Actions", "Overview", "Details", "History", "Approval",
        "Pending", "Completed", "Active", "Inactive", "Total",
        "Monthly", "Weekly", "Daily", "From", "To", "Type",
        "Name", "Email", "Phone", "Address", "Role", "Created",
        "Updated", "Description", "Comment", "Note", "Warning",
        "Error", "Success", "Info", "Loading", "Processing"
    ]
    
    for i, term in enumerate(terms, 1):
        print(f"{i:2}. {term}")
        if i % 10 == 0:
            print()

def main():
    """Main function."""
    print("=== KasiKash Translation Helper ===\n")
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python translate_helper.py status     - Show translation status")
        print("  python translate_helper.py samples    - Show sample translations")
        print("  python translate_helper.py terms      - Show common terms")
        print("  python translate_helper.py edit [lang] - Edit translation file")
        print("\nLanguage codes:")
        for code, name in SA_LANGUAGES.items():
            print(f"  {code} - {name}")
        return
    
    command = sys.argv[1]
    
    if command == "status":
        show_translation_status()
    elif command == "samples":
        show_sample_translations()
    elif command == "terms":
        show_common_terms()
    elif command == "edit":
        if len(sys.argv) < 3:
            print("Please specify a language code (e.g., 'python translate_helper.py edit xh')")
            return
        language_code = sys.argv[2]
        if language_code not in SA_LANGUAGES:
            print(f"Unknown language code: {language_code}")
            print("Available codes:", list(SA_LANGUAGES.keys()))
            return
        edit_translation_file(language_code)
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main() 