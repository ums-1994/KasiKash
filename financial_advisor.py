print("financial_advisor.py loaded")
from flask import Blueprint, render_template, request, jsonify, current_app, session
from utils import login_required
import pytesseract
from PIL import Image
import io, datetime, openai
from models import db, ChatHistory, Transaction  # adjust import path if needed

advisor_bp = Blueprint('advisor', __name__, url_prefix='/financial_advisor')

@advisor_bp.route('/', methods=['GET'])
@login_required
def dashboard():
    user_id = session.get('user_id')
    return render_template('financial_advisor.html', user_id=user_id)

@advisor_bp.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_msg = data.get('message')
    user_id = data.get('user_id')

    openai.api_key = current_app.config['OPENAI_API_KEY']
    resp = openai.ChatCompletion.create(
      model='gpt-3.5-turbo',
      messages=[{'role':'user','content':user_msg}]
    )
    assistant_msg = resp.choices[0].message.content

    # Save chat history
    entry = ChatHistory(user_id=user_id, user_message=user_msg, assistant_response=assistant_msg)
    db.session.add(entry)
    db.session.commit()

    return jsonify(response=assistant_msg)

@advisor_bp.route('/upload', methods=['POST'])
def upload_statement():
    user_id = request.form.get('user_id')
    file = request.files.get('file')
    img = Image.open(io.BytesIO(file.read()))
    text = pytesseract.image_to_string(img)

    transactions = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 3: continue
        date_str, *desc_parts, amt_str = parts
        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            amount = float(amt_str.replace('R','').replace(',',''))
        except: continue
        desc = ' '.join(desc_parts)
        tx = Transaction(user_id=user_id, date=date, description=desc, amount=amount, category='Uncategorized')
        db.session.add(tx)
        transactions.append({'date': date_str, 'description': desc, 'amount': amount})
    db.session.commit()

    alerts = []
    alerts.append("⚠️ You've exceeded your food budget this month.")

    return jsonify(transactions=transactions, alerts=alerts) 