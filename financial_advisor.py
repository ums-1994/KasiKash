print("financial_advisor.py loaded")
from flask import Blueprint, render_template, request, jsonify, current_app, session
from utils import login_required
import pytesseract
from PIL import Image
import io, datetime, openai, requests, os
from models import db, ChatHistory, Transaction  # adjust import path if needed
from pdf2image import convert_from_bytes
import PyPDF2
from openai import OpenAI
from support import db_connection, save_statement_analysis, get_latest_analysis, save_advisor_chat

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

    # Fetch latest analysis from database for context
    from flask import g
    with db_connection() as conn:
        analysis = get_latest_analysis(conn, user_id)
    if not analysis:
        return jsonify({'error': 'Please upload a statement first to provide context for your question.'}), 400
    analysis_id, statement_text, analysis_text = analysis

    # Build context-aware prompt
    context_prompt = (
        "You are a financial advisor. Here is the user's bank statement and previous analysis:\n\n"
        f"Statement:\n{statement_text}\n\n"
        f"Previous AI Analysis:\n{analysis_text}\n\n"
        f"User's follow-up question/request:\n{user_msg}"
    )

    # Use OpenRouter API for Google Gemma 2 9B model (same as main chatbot)
    api_key = current_app.config.get('OPENROUTER_API_KEY') or os.getenv("OPENROUTER_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "google/gemma-2-9b-it",
        "messages": [
            {"role": "user", "content": context_prompt}
        ]
    }
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        if 'choices' not in result:
            print(f"OpenRouter API error: {result}", flush=True)
            return jsonify({'error': 'AI service did not return a valid response. Please try again later.'}), 502
        assistant_msg = result['choices'][0]['message']['content']
    except requests.exceptions.HTTPError as e:
        print(f"OpenRouter API error: {e}", flush=True)
        if response.status_code == 503:
            return jsonify({'error': 'AI service is temporarily unavailable. Please try again later.'}), 503
        return jsonify({'error': f'AI service error: {str(e)}'}), 500
    except Exception as e:
        print(f"OpenRouter API error: {e}", flush=True)
        return jsonify({'error': f'AI service error: {str(e)}'}), 500

    # Save chat history to database
    with db_connection() as conn:
        save_advisor_chat(conn, user_id, analysis_id, user_msg, assistant_msg)

    return jsonify(response=assistant_msg)

@advisor_bp.route('/upload', methods=['POST'])
def upload_statement():
    user_id = request.form.get('user_id')
    file = request.files.get('file')

    # Debug prints
    print("request.form:", request.form, flush=True)
    print("request.files:", request.files, flush=True)
    print("user_id:", user_id, flush=True)
    print("file:", file, flush=True)

    if not user_id:
        print("Missing user_id in form data", flush=True)
        return jsonify({'error': 'Missing user_id'}), 400

    if not file or file.filename == '':
        print("No file uploaded or filename is empty", flush=True)
        return jsonify({'error': 'No file uploaded'}), 400

    filename = file.filename.lower()
    text = ""
    if filename.endswith('.pdf'):
        # Try to extract text directly
        try:
            file.seek(0)
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception:
            # If direct extraction fails, use OCR on images
            file.seek(0)
            images = convert_from_bytes(file.read())
            for img in images:
                text += pytesseract.image_to_string(img)
    else:
        img = Image.open(io.BytesIO(file.read()))
        text = pytesseract.image_to_string(img)

    # Prompt for Google Gemma 2 9B model
    prompt = (
        "Below is a bank statement. Please analyze the user's financial situation, "
        "summarize key spending and savings patterns, and provide professional, actionable financial advice.\n"
        "Statement:\n"
        f"{text}"
    )

    api_key = current_app.config.get('OPENROUTER_API_KEY') or os.getenv("OPENROUTER_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "google/gemma-2-9b-it",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        if 'choices' not in result:
            print(f"OpenRouter API error: {result}", flush=True)
            return jsonify({'error': 'AI service did not return a valid response. Please try again later.'}), 502
        ai_analysis = result['choices'][0]['message']['content']
        # Store context in session for follow-up questions
        session['advisor_statement_text'] = text
        session['advisor_analysis'] = ai_analysis
    except requests.exceptions.HTTPError as e:
        print(f"OpenRouter API error: {e}", flush=True)
        if response.status_code == 503:
            return jsonify({'error': 'AI service is temporarily unavailable. Please try again later.'}), 503
        return jsonify({'error': f'AI service error: {str(e)}'}), 500
    except Exception as e:
        print(f"OpenRouter API error: {e}", flush=True)
        return jsonify({'error': f'AI service error: {str(e)}'}), 500

    # Optionally, still parse transactions for your own records
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

    # Save analysis to database and store analysis_id in session
    with db_connection() as conn:
        analysis_id = save_statement_analysis(
            conn, user_id, text, ai_analysis, transactions, file.filename
        )
    session['advisor_analysis_id'] = analysis_id

    return jsonify(success=True, transactions=transactions, alerts=alerts, analysis=ai_analysis) 