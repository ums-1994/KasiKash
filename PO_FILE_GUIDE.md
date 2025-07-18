# Guide to Working with .po Translation Files

## What are .po files?

`.po` files are translation files used by gettext (the internationalization system). They contain:
- **msgid**: The original English text (source)
- **msgstr**: The translated text (target language)

## File Structure

Each `.po` file has:
1. **Header section** with metadata
2. **Translation entries** with msgid and msgstr pairs

## How to Edit .po Files

### 1. Basic Translation Entry
```
msgid "Welcome to KasiKash Admin"
msgstr "Welcome to KasiKash Admin"
```

### 2. For Afrikaans Translation
```
msgid "Welcome to KasiKash Admin"
msgstr "Welkom by KasiKash Admin"
```

### 3. For Xhosa Translation
```
msgid "Welcome to KasiKash Admin"
msgstr "Wamkelekile kuKasiKash Admin"
```

## Translation Process

### Step 1: Open the .po file
Open `translations/[language]/LC_MESSAGES/messages.po` in any text editor.

### Step 2: Find the text to translate
Look for `msgid` entries that contain English text.

### Step 3: Add your translation
Replace the English text in `msgstr` with your translation.

### Step 4: Save the file
Save the `.po` file with UTF-8 encoding.

## Example Translations

### English (en)
```
msgid "Dashboard"
msgstr "Dashboard"
```

### Afrikaans (af)
```
msgid "Dashboard"
msgstr "Dashboard"
```

### Xhosa (xh)
```
msgid "Dashboard"
msgstr "Ikhasi Lokubhekisa"
```

### Zulu (zu)
```
msgid "Dashboard"
msgstr "Ikhasi Lokubheka"
```

## Language Codes for South Africa

| Code | Language | Native Name |
|------|----------|-------------|
| af | Afrikaans | Afrikaans |
| en | English | English |
| nr | Southern Ndebele | isiNdebele |
| xh | Xhosa | isiXhosa |
| zu | Zulu | isiZulu |
| nso | Northern Sotho | Sepedi |
| st | Southern Sotho | Sesotho |
| tn | Tswana | Setswana |
| ss | Swati | siSwati |
| ve | Venda | Tshivenda |
| ts | Tsonga | Xitsonga |

## Tips for Translation

1. **Keep context in mind** - The same English word might have different translations depending on context
2. **Use formal language** - Admin interfaces typically use formal language
3. **Test your translations** - Make sure they make sense in the interface
4. **Be consistent** - Use the same translation for the same English term throughout
5. **Consider cultural context** - Some terms might need adaptation for local context

## Common Admin Terms

| English | Afrikaans | Xhosa | Zulu |
|---------|-----------|-------|------|
| Dashboard | Dashboard | Ikhasi Lokubhekisa | Ikhasi Lokubheka |
| Settings | Instellings | Iisethingi | Izilungiselelo |
| Users | Gebruikers | Abasebenzisi | Abasebenzisi |
| Reports | Verslae | Iingxelo | Imibiko |
| Analytics | Ontleding | Uhlalutyo | Ukuhlaziya |
| Export | Voer uit | Khuphela | Khipha |
| Import | Voer in | Ngenisa | Ngenisa |
| Save | Stoor | Gcina | Gcina |
| Cancel | Kanselleer | Rhoxisa | Khansela |
| Delete | Verwyder | Cima | Susa |

## File Locations

Your translation files are located at:
```
translations/
├── af/LC_MESSAGES/messages.po  (Afrikaans)
├── en/LC_MESSAGES/messages.po  (English)
├── nr/LC_MESSAGES/messages.po  (Southern Ndebele)
├── xh/LC_MESSAGES/messages.po  (Xhosa)
├── zu/LC_MESSAGES/messages.po  (Zulu)
├── nso/LC_MESSAGES/messages.po (Northern Sotho)
├── st/LC_MESSAGES/messages.po  (Southern Sotho)
├── tn/LC_MESSAGES/messages.po  (Tswana)
├── ss/LC_MESSAGES/messages.po  (Swati)
├── ve/LC_MESSAGES/messages.po  (Venda)
└── ts/LC_MESSAGES/messages.po  (Tsonga)
```

## Next Steps

1. **Edit each .po file** for the languages you want to support
2. **Add translations** for all the admin interface text
3. **Test the translations** in your Flask app
4. **Compile the translations** when ready

## Compiling Translations

After editing, you'll need to compile the `.po` files to `.mo` files:

```bash
# Using Babel (if available)
pybabel compile -d translations

# Or manually create .mo files
# (This will be handled by your Flask-Babel setup)
```

## Testing Translations

1. Update your Flask app's `LANGUAGES` configuration
2. Restart your Flask application
3. Test the language switching functionality
4. Verify all translations display correctly

## Need Help?

- Use online translation tools for reference
- Consult with native speakers when possible
- Test translations in context to ensure they make sense
- Keep translations consistent across the application 