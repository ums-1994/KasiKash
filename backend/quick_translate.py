#!/usr/bin/env python3
"""
Quick Translation Helper for KasiKash Admin Dashboard
Helps translate specific terms to South African languages.
"""

# Common admin terms and their translations
TRANSLATIONS = {
    "Welcome, Admin 👋": {
        "af": "Welkom, Admin 👋",
        "xh": "Wamkelekile, Admin 👋",
        "zu": "Sawubona, Admin 👋",
        "st": "Rea u amohela, Admin 👋",
        "tn": "Re a go amogela, Admin 👋",
        "nso": "Re a go amogela, Admin 👋",
        "ss": "Sawubona, Admin 👋",
        "nr": "Sawubona, Admin 👋",
        "ve": "Ndi khou ni lumelisa, Admin 👋",
        "ts": "Avuxeni, Admin 👋"
    },
    "Dashboard": {
        "af": "Dashboard",
        "xh": "Ikhasi Lokubhekisa",
        "zu": "Ikhasi Lokubheka",
        "st": "Dashboard",
        "tn": "Dashboard",
        "nso": "Dashboard",
        "ss": "Dashboard",
        "nr": "Dashboard",
        "ve": "Dashboard",
        "ts": "Dashboard"
    },
    "Manage Users": {
        "af": "Bestuur Gebruikers",
        "xh": "Lawula Abasebenzisi",
        "zu": "Lawula Abasebenzisi",
        "st": "Laola Basebedisi",
        "tn": "Laola Basebedisi",
        "nso": "Laola Basebedisi",
        "ss": "Lawula Basebenti",
        "nr": "Lawula Abasebenzisi",
        "ve": "Vhulunzhei Vhashumeli",
        "ts": "Lawula Vatirhi"
    },
    "Settings": {
        "af": "Instellings",
        "xh": "Iisethingi",
        "zu": "Izilungiselelo",
        "st": "Litlhophiso",
        "tn": "Dikgololesego",
        "nso": "Dikgololesego",
        "ss": "Litlhophiso",
        "nr": "Izilungiselelo",
        "ve": "Dzikhinaho",
        "ts": "Vutshila"
    },
    "Reports": {
        "af": "Verslae",
        "xh": "Iingxelo",
        "zu": "Imibiko",
        "st": "Lipokello",
        "tn": "Dipokelo",
        "nso": "Dipokelo",
        "ss": "Lipokello",
        "nr": "Imibiko",
        "ve": "Dzivhudzulo",
        "ts": "Mibiko"
    },
    "Search": {
        "af": "Soek",
        "xh": "Khanqa",
        "zu": "Sesha",
        "st": "Batla",
        "tn": "Batla",
        "nso": "Batla",
        "ss": "Batla",
        "nr": "Sesha",
        "ve": "Sengulusa",
        "ts": "Tluka"
    },
    "Save": {
        "af": "Stoor",
        "xh": "Gcina",
        "zu": "Gcina",
        "st": "Boloka",
        "tn": "Boloka",
        "nso": "Boloka",
        "ss": "Boloka",
        "nr": "Gcina",
        "ve": "Vhulunga",
        "ts": "Hlayisa"
    },
    "Cancel": {
        "af": "Kanselleer",
        "xh": "Rhoxisa",
        "zu": "Khansela",
        "st": "Khansela",
        "tn": "Khansela",
        "nso": "Khansela",
        "ss": "Khansela",
        "nr": "Khansela",
        "ve": "Khansela",
        "ts": "Khansela"
    },
    "Delete": {
        "af": "Verwyder",
        "xh": "Cima",
        "zu": "Susa",
        "st": "Hlakola",
        "tn": "Phumola",
        "nso": "Phumola",
        "ss": "Hlakola",
        "nr": "Susa",
        "ve": "Dzula",
        "ts": "Susa"
    },
    "Edit": {
        "af": "Redigeer",
        "xh": "Hlela",
        "zu": "Hlela",
        "st": "Fetola",
        "tn": "Fetola",
        "nso": "Fetola",
        "ss": "Fetola",
        "nr": "Hlela",
        "ve": "Sedzulusa",
        "ts": "Lungisa"
    },
    "Add": {
        "af": "Voeg by",
        "xh": "Yongeza",
        "zu": "Engeza",
        "st": "Eketsa",
        "tn": "Eketsa",
        "nso": "Eketsa",
        "ss": "Eketsa",
        "nr": "Engeza",
        "ve": "Dzhenisa",
        "ts": "Engeza"
    }
}

def show_translations(term):
    """Show translations for a specific term."""
    if term in TRANSLATIONS:
        print(f"\nTranslations for '{term}':")
        print("-" * 50)
        for lang, translation in TRANSLATIONS[term].items():
            print(f"{lang:2} : {translation}")
    else:
        print(f"\nNo translations found for '{term}'")
        print("Available terms:")
        for term in TRANSLATIONS.keys():
            print(f"  - {term}")

def show_all_terms():
    """Show all available terms."""
    print("\nAvailable terms for translation:")
    print("-" * 40)
    for i, term in enumerate(TRANSLATIONS.keys(), 1):
        print(f"{i:2}. {term}")

def interactive_translate():
    """Interactive translation mode."""
    print("=== Quick Translation Helper ===")
    print("Type a term to see translations, or 'list' to see all terms, or 'quit' to exit")
    
    while True:
        term = input("\nEnter term to translate: ").strip()
        
        if term.lower() == 'quit':
            break
        elif term.lower() == 'list':
            show_all_terms()
        else:
            show_translations(term)

def main():
    """Main function."""
    if len(sys.argv) < 2:
        interactive_translate()
        return
    
    command = sys.argv[1]
    
    if command == "list":
        show_all_terms()
    elif command == "interactive":
        interactive_translate()
    else:
        # Treat as a term to translate
        show_translations(command)

if __name__ == "__main__":
    import sys
    main() 