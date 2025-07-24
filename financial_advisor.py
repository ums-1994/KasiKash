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

def add_paragraphs(text):
    import re
    # Split into blocks separated by two or more newlines
    blocks = re.split(r'\n{2,}', text)
    html = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # If block looks like a table or list, don't wrap in <p>
        if (block.startswith('<ul>') or block.startswith('<table') or
            block.startswith('<ol>') or block.startswith('<tr>') or
            block.startswith('<th>') or block.startswith('<td>')):
            html.append(block)
        else:
            html.append(f'<p>{block}</p>')
    return '\n'.join(html)

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
    # Fetch latest analysis for this user
    from support import db_connection, get_latest_analysis
    advisor_analysis = None
    with db_connection() as conn:
        analysis = get_latest_analysis(conn, user_id, with_budget=True)
        if analysis:
            _, _, analysis_text, _, _ = analysis
            advisor_analysis = analysis_text
    return render_template('financial_advisor.html', user_id=user_id, advisor_analysis=advisor_analysis)

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
    # Build a shorter, context-aware prompt
    context_prompt = (
        "You are a financial advisor. Here is the user's previous financial analysis and their follow-up question. "
        "Use the analysis to provide actionable, detailed advice.\n\n"
        f"Previous AI Financial Analysis & Advice:\n{analysis_text}\n\n"
        f"User's follow-up question/request:\n{user_msg}"
    )
    api_key = current_app.config.get('OPENROUTER_API_KEY') or os.getenv("OPENROUTER_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "qwen/qwen3-30b-a3b:free",
        "messages": [
            {"role": "user", "content": context_prompt}
        ]
    }
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        if 'choices' not in result:
            print(f"OpenRouter API error: {result}", flush=True)
            return jsonify({'error': 'AI service did not return a valid response. Please try again later.'}), 502
        assistant_msg = result['choices'][0]['message']['content']
        # Remove markdown asterisks and headers, and convert dashes to bullets for a cleaner look
        import re
        assistant_msg = re.sub(r'\*{3,}', '', assistant_msg)  # Remove ***
        assistant_msg = re.sub(r'\*{2}', '', assistant_msg)   # Remove **
        assistant_msg = re.sub(r'\*', '', assistant_msg)      # Remove *
        assistant_msg = re.sub(r'#+', '', assistant_msg)       # Remove markdown headers (#)
        assistant_msg = re.sub(r'^\s*- ', '• ', assistant_msg, flags=re.MULTILINE)  # Replace dash lists with bullets
    except requests.exceptions.Timeout:
        print("[AI Exception] Request timed out.")
        return jsonify({'error': 'AI service timed out. Please try again later.'}), 504
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
        from pdf2image import convert_from_bytes
        import pytesseract
        text = ""
        try:
            with open(save_path, 'rb') as file_for_text:
                pdf_bytes = file_for_text.read()
                file_for_text.seek(0)
                reader = PyPDF2.PdfReader(file_for_text)
                images = convert_from_bytes(pdf_bytes)
                for i, page in enumerate(reader.pages):
                    # Extract text from PDF page
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n[PDF Page {i+1} Text]\n" + page_text + "\n"
                    # Extract OCR from image of the page
                    if i < len(images):
                        ocr_text = pytesseract.image_to_string(images[i])
                        if ocr_text.strip():
                            text += f"\n[PDF Page {i+1} OCR]\n" + ocr_text + "\n"
            print(f"[PDF+OCR Extraction] Extracted text length: {len(text)}")
            print(f"[PDF+OCR Extraction] Sample: {text[:500]}")
        except Exception as e:
            print(f"[PDF+OCR Extraction] Exception: {e}")
            text = ""
        print(f"[Final Extraction] Total text length sent to AI: {len(text)}")
        print(f"[Final Extraction] Sample: {text[:500]}")
        # Limit the input to the first 4000 characters to fit the model's context window
        max_chars = 4000
        short_text = text[:max_chars]

        prompt = f"""
Give financial advice based on this bank statement:
{short_text}
"""

        print(f"[AI Prompt] {prompt[:500]}")
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
                    "model": "qwen/qwen3-30b-a3b:free",
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
                import re
                # Convert markdown headers to <b> tags
                ai_analysis = re.sub(r'^\s*#+\s*(.*)', r'<b>\1</b>', ai_analysis, flags=re.MULTILINE)
                # Convert double asterisks to <b>
                ai_analysis = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', ai_analysis)
                # Remove single asterisks
                ai_analysis = re.sub(r'\*', '', ai_analysis)
                # Replace dash-based lists with <ul><li>...</li></ul>
                def dash_to_ul(text):
                    lines = text.split('\n')
                    in_ul = False
                    new_lines = []
                    for line in lines:
                        if re.match(r'^\s*- ', line):
                            if not in_ul:
                                new_lines.append('<ul>')
                                in_ul = True
                            new_lines.append('<li>' + line.lstrip('- ').strip() + '</li>')
                        else:
                            if in_ul:
                                new_lines.append('</ul>')
                                in_ul = False
                            new_lines.append(line)
                    if in_ul:
                        new_lines.append('</ul>')
                    return '\n'.join(new_lines)
                ai_analysis = dash_to_ul(ai_analysis)
                # Convert markdown tables to HTML tables
                def md_table_to_html(text):
                    lines = text.split('\n')
                    html = []
                    in_table = False
                    for i, line in enumerate(lines):
                        if re.match(r'^\s*\|', line):
                            cells = [c.strip() for c in line.strip().split('|')[1:-1]]
                            if not in_table:
                                html.append('<table class="advisor-table">')
                                in_table = True
                            if i+1 < len(lines) and re.match(r'^\s*\|[\s:-]+\|$', lines[i+1]):
                                html.append('<tr>' + ''.join(f'<th>{c}</th>' for c in cells) + '</tr>')
                            else:
                                html.append('<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>')
                        else:
                            if in_table:
                                html.append('</table>')
                                in_table = False
                            html.append(line)
                    if in_table:
                        html.append('</table>')
                    return '\n'.join(html)
                ai_analysis = md_table_to_html(ai_analysis)
                # Wrap in a div for styling
                ai_analysis = add_paragraphs(ai_analysis)
                ai_analysis = f'<div class="advisor-analysis-html">{ai_analysis}</div>'
            else:
                print(f"[AI Error] No choices in result: {result}")
                ai_analysis = "No analysis available. (AI returned no choices)"
        except Exception as e:
            print(f"[AI Exception] {e}")
            ai_analysis = None
        # Save analysis to database so chat assistant can find it
        from support import db_connection, save_statement_analysis
        with db_connection() as conn:
            if not ai_analysis:
                ai_analysis = "No analysis available."
            analysis_id = save_statement_analysis(
                conn, user_id, text, ai_analysis, [], file.filename, None
            )
        # --- Extract transactions from statement text ---
        def parse_transactions(text):
            import re
            txs = []
            # Example regex for lines like: 01/04/2025 Rent - Diepsloot Prop 6,500.00-2,000.00
            pattern = re.compile(r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d,]+\.\d{2})-([\d,]+\.\d{2})$', re.MULTILINE)
            for match in pattern.finditer(text):
                date, desc, debit, credit = match.groups()
                debit = float(debit.replace(",", "")) if debit else 0.0
                credit = float(credit.replace(",", "")) if credit else 0.0
                amount = credit - debit  # Net effect
                txs.append({
                    'date': date,
                    'description': desc.strip(),
                    'amount': amount,
                    'debit': debit,
                    'credit': credit,
                    'category': None  # Could add simple rules later
                    })
            return txs
        transactions = parse_transactions(text)
        session['advisor_transactions'] = transactions
        return jsonify(success=True, pdf_url=pdf_url, analysis=ai_analysis, statement_text=text, transactions=transactions) 
