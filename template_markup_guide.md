
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
