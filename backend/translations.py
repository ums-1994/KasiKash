"""
Translations for KasiKash app in South African languages
"""

# REMOVE ALL TRANSLATION LOGIC AND DICTIONARIES
# The app will now use plain English text only, no translation or language switching.

# Dummy get_text and t functions for compatibility

def get_text(key, lang='en'):
    return key  # Just return the key, no translation

t = get_text

TRANSLATIONS = {}

__all__ = ['get_text', 't', 'TRANSLATIONS']