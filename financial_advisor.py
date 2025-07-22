import os
from dotenv import load_dotenv

load_dotenv()  # Make sure this is called
print("DEBUG - OpenRouter Key:", os.getenv("OPENROUTER_API_KEY"))

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
import re

# Delete old financial advisor data on app startup
try:
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM financial_advisor_chat;")
            cur.execute("DELETE FROM financial_statement_analysis;")
        conn.commit()
    print("[INFO] Old financial advisor data deleted on startup.")
except Exception as e:
    print(f"[ERROR] Failed to delete old financial advisor data: {e}")

advisor_bp = Blueprint('advisor', __name__, url_prefix='/financial_advisor')

@advisor_bp.route('/', methods=['GET'])
@login_required
def dashboard():
    user_id = session.get('user_id')
    return render_template('financial_advisor.html', user_id=user_id)

@advisor_bp.route('/debug_session', methods=['GET'])
def debug_session():
    from flask import session
    return jsonify({
        'session_user_id': session.get('user_id'),
        'session': dict(session)
    })

@advisor_bp.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_msg = data.get('message')
    user_id = data.get('user_id')
    print(f"[DEBUG] user_id from request: {data.get('user_id')}", flush=True)
    print(f"[DEBUG] user_id from session: {session.get('user_id')}", flush=True)
    if user_id:
        user_id = user_id.strip()
    else:
        user_id = session.get('user_id', '').strip()
    print(f"[DEBUG] /chat user_id: {user_id}", flush=True)
    # Fetch latest analysis from database for context
    from flask import g
    with db_connection() as conn:
        analysis = get_latest_analysis(conn, user_id, with_budget=True)
    print(f"[DEBUG] get_latest_analysis result: {analysis}", flush=True)
    if not analysis:
        return jsonify({'error': 'No financial analysis found for your account. Please upload a statement and ensure it is processed successfully before chatting.'}), 400
    analysis_id, statement_text, analysis_text, transactions_json, ai_budget_plan = analysis
    # Build context-aware prompt
    context_prompt = (
        "You are a financial advisor. Here is the user's bank statement, previous analysis, parsed transactions, and budget plan. "
        "Use ALL the data to answer the user's question and provide actionable, detailed advice.\n\n"
        f"Statement (raw data):\n{statement_text}\n\n"
        f"Previous AI Financial Analysis & Advice:\n{analysis_text}\n\n"
        f"Parsed Transactions:\n{transactions_json}\n\n"
        f"Budget Plan:\n{ai_budget_plan}\n\n"
        f"User's follow-up question/request:\n{user_msg}"
    )
    # Restore real OpenRouter AI API call
    api_key = current_app.config.get('OPENROUTER_API_KEY') or os.getenv("OPENROUTER_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "google/gemma-2-9b-it:free",
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
    # Save chat history to database (including prompt and response)
    with db_connection() as conn:
        save_advisor_chat(conn, user_id, analysis_id, context_prompt, assistant_msg)
    return jsonify(response=assistant_msg)

@advisor_bp.route('/upload', methods=['POST'])
def upload_statement():
    user_id = request.form.get('user_id')
    if user_id:
        user_id = user_id.strip()
    else:
        user_id = ''
    file = request.files.get('file')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    if not file or file.filename == '':
        return jsonify({'error': 'No file uploaded'}), 400
    filename = file.filename.lower()
    if filename.endswith('.pdf'):
        from werkzeug.utils import secure_filename
        import os
        save_dir = os.path.join('static', 'statements')
        os.makedirs(save_dir, exist_ok=True)
        safe_name = secure_filename(file.filename)
        save_path = os.path.join(save_dir, safe_name)
        file.seek(0)
        file.save(save_path)
        pdf_url = '/static/statements/' + safe_name
        # Extract text from PDF for analysis
        import PyPDF2
        text = ""
        try:
            file_for_text = open(save_path, 'rb')
            reader = PyPDF2.PdfReader(file_for_text)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            file_for_text.close()
            print(f"[PDF Extraction] Extracted text length: {len(text)}")
            print(f"[PDF Extraction] Sample: {text[:500]}")
        except Exception as e:
            print(f"[PDF Extraction] Exception: {e}")
            text = ""
        # If text extraction is empty or too short, try OCR on each page
        if not text.strip() or len(text.strip()) < 50:
            try:
                from pdf2image import convert_from_bytes
                import pytesseract
                with open(save_path, 'rb') as f:
                    pdf_bytes = f.read()
                images = convert_from_bytes(pdf_bytes)
                ocr_text = ""
                for img in images:
                    ocr_text += pytesseract.image_to_string(img) + "\n"
                if ocr_text.strip():
                    text += "\n[OCR]\n" + ocr_text
                print(f"[OCR Extraction] Extracted OCR text length: {len(ocr_text)}")
                print(f"[OCR Extraction] Sample: {ocr_text[:500]}")
            except Exception as ocr_e:
                print(f"[OCR Extraction] Exception: {ocr_e}")
                pass
        print(f"[Final Extraction] Total text length sent to AI: {len(text)}")
        print(f"[Final Extraction] Sample: {text[:500]}")
        # Always run AI analysis on the full extracted text, even if parsing fails
        ai_analysis = None
        ai_budget_plan = None
        prompt = (
            "Below is a bank statement. Please analyze the user's financial situation, "
            "summarize key spending and savings patterns, and provide professional, actionable financial advice.\n"
            "Statement:\n"
            f"{text}"
        )
        print(f"[AI Prompt] Length: {len(prompt)}")
        print(f"[AI Prompt] Sample: {prompt[:500]}")
        api_key = current_app.config.get('OPENROUTER_API_KEY') or os.getenv("OPENROUTER_API_KEY")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={
                    "model": "google/gemma-2-9b-it:free",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            response.raise_for_status()
            result = response.json()
            print(f"[AI Response] {result}")
            if 'choices' in result and result['choices']:
                ai_analysis = result['choices'][0]['message']['content']
            else:
                print(f"[AI Error] No choices in result: {result}")
                ai_analysis = "No analysis available. (AI returned no choices)"
            # Now, request a structured budget plan
            budget_prompt = (
                "Based on the following bank statement and your previous analysis, create a structured, detailed budget plan as a clear, readable text.\n"
                f"Statement:\n{text}\n\nPrevious Analysis:\n{ai_analysis}"
            )
            budget_response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={
                    "model": "google/gemma-2-9b-it:free",
                    "messages": [
                        {"role": "user", "content": budget_prompt}
                    ]
                }
            )
            budget_response.raise_for_status()
            budget_result = budget_response.json()
            print(f"[AI Budget Response] {budget_result}")
            if 'choices' in budget_result and budget_result['choices']:
                ai_budget_plan = budget_result['choices'][0]['message']['content']
        except Exception as e:
            print(f"[AI Exception] {e}")
            ai_analysis = None
            ai_budget_plan = None
        # Save analysis to database so chat assistant can find it
        from support import db_connection, save_statement_analysis
        with db_connection() as conn:
            if not ai_analysis:
                ai_analysis = "No analysis available."
            if not ai_budget_plan:
                ai_budget_plan = ""
            analysis_id = save_statement_analysis(
                conn, user_id, text, ai_analysis, [], file.filename, ai_budget_plan
            )
        # Attempt to parse transactions, but do not block AI analysis if parsing fails
        def parse_statement(text):
            import re
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            meta = {'bank': '', 'account_holder': '', 'account': '', 'branch': '', 'period': ''}
            transactions = []
            # Extract metadata from the first 10 lines
            for i in range(min(10, len(lines))):
                l = lines[i]
                if 'statement' in l.lower() and 'account' in l.lower():
                    meta['bank'] = l
                if 'account holder' in l.lower():
                    meta['account_holder'] = l.split(':',1)[-1].strip()
                if 'account:' in l.lower() and not meta['account']:
                    meta['account'] = l.split(':',1)[-1].strip()
                if 'branch:' in l.lower():
                    meta['branch'] = l.split(':',1)[-1].strip()
                if 'statement period' in l.lower():
                    meta['period'] = l.split(':',1)[-1].strip()
            # Find table header
            header_idx = -1
            headers = []
            for i, l in enumerate(lines):
                if ('date' in l.lower() and 'description' in l.lower() and
                    ('debit' in l.lower() or 'credit' in l.lower() or 'amount' in l.lower() or 'balance' in l.lower())):
                    header_idx = i
                    if '|' in l:
                        headers = [h.strip() for h in l.split('|') if h.strip()]
                    else:
                        headers = [h.strip() for h in re.split(r'\s{2,}', l) if h.strip()]
                    break
            def is_date(s):
                return bool(re.match(r'^(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})$', s))
            if header_idx != -1 and headers:
                data_lines = lines[header_idx+1:]
                i = 0
                while i < len(data_lines):
                    l = data_lines[i]
                    if not l or set(l) <= set('-| '):
                        i += 1
                        continue
                    # Try to parse row
                    row = re.split(r'\s{2,}|\|', l)
                    row = [x.strip() for x in row if x.strip()]
                    if len(row) >= len(headers):
                        txn = dict(zip(headers, row))
                        transactions.append(txn)
                    i += 1
            return transactions
        transactions = parse_statement(text)
        def normalize_transaction_keys(txn):
            key_map = {
                'date': 'Date', 'Date': 'Date',
                'description': 'Description', 'desc': 'Description', 'Desc': 'Description',
                'amount': 'Amount', 'amt': 'Amount', 'Amount': 'Amount',
                'debit': 'Debit (R)', 'Debit': 'Debit (R)', 'Debit (R)': 'Debit (R)',
                'credit': 'Credit (R)', 'Credit': 'Credit (R)', 'Credit (R)': 'Credit (R)',
                'category': 'Category', 'Category': 'Category'
            }
            norm = {}
            for k, v in txn.items():
                std_key = key_map.get(k.strip(), k.strip())
                norm[std_key] = v
            return norm
        transactions = [normalize_transaction_keys(txn) for txn in transactions]
        if not transactions and ai_analysis:
            import re
            def extract_transactions_from_analysis(analysis):
                pattern = re.compile(r'([A-Za-z &]+):\s*R?([\d,]+(?:\.\d{1,2})?)')
                txns = []
                for match in pattern.finditer(analysis):
                    category = match.group(1).strip()
                    amount = match.group(2).replace(',', '')
                    try:
                        amount = float(amount)
                    except:
                        continue
                    txns.append({
                        'Date': '',
                        'Description': category,
                        'Amount': amount
                    })
                return txns
            transactions = extract_transactions_from_analysis(ai_analysis)
        session['advisor_transactions'] = transactions
        return jsonify(success=True, pdf_url=pdf_url, analysis=ai_analysis, budget_plan=ai_budget_plan, transactions=transactions, statement_text=text) 