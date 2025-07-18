#!/usr/bin/env python3
"""
Create translation directory structure and files for South African languages.
"""

import os
import sys

# South African official languages
SA_LANGUAGES = ['af', 'en', 'nr', 'xh', 'zu', 'nso', 'st', 'tn', 'ss', 've', 'ts']

def create_translation_structure():
    """Create translation directory structure and files."""
    print("Creating translation structure for South African languages...")
    
    for locale in SA_LANGUAGES:
        # Create directory structure
        po_dir = f"translations/{locale}/LC_MESSAGES"
        os.makedirs(po_dir, exist_ok=True)
        
        # Create empty .po file
        po_file = f"{po_dir}/messages.po"
        if not os.path.exists(po_file):
            with open(po_file, 'w', encoding='utf-8') as f:
                f.write(f'''# Translation of messages for {locale}
msgid ""
msgstr ""
"Project-Id-Version: KasiKash Admin Dashboard\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2024-01-01 00:00+0000\\n"
"PO-Revision-Date: 2024-01-01 00:00+0000\\n"
"Last-Translator: \\n"
"Language: {locale}\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"

''')
            print(f"Created {po_file}")
        else:
            print(f"Already exists: {po_file}")
    
    print("Translation structure created successfully!")
    return True

def list_translations():
    """List all translation files."""
    print("Translation files:")
    for locale in SA_LANGUAGES:
        po_file = f"translations/{locale}/LC_MESSAGES/messages.po"
        mo_file = f"translations/{locale}/LC_MESSAGES/messages.mo"
        
        po_exists = os.path.exists(po_file)
        mo_exists = os.path.exists(mo_file)
        
        status = "Complete" if po_exists and mo_exists else "PO only" if po_exists else "Missing"
        print(f"  {locale}: {status}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python create_translations.py [create|list]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'create':
        create_translation_structure()
    elif command == 'list':
        list_translations()
    else:
        print("Unknown command:", command)
        sys.exit(1) 