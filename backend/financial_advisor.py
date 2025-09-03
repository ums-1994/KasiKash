import os
from dotenv import load_dotenv

load_dotenv()  # Make sure this is called
# Avoid printing the raw API key
print("DEBUG - OpenRouter Key set:", "YES" if os.getenv("OPENROUTER_API_KEY") else "NO")

print("financial_advisor.py loaded")
from flask import Blueprint, render_template, request, jsonify, current_app, session, url_for
from .utils import login_required
import pytesseract
from PIL import Image
import io, datetime, openai, requests, os
from .models import db, ChatHistory, Transaction  # adjust import path if needed
from pdf2image import convert_from_bytes
import PyPDF2
from openai import OpenAI
from .support import db_connection, save_statement_analysis, get_latest_analysis, save_advisor_chat
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

# Note: Removed startup data deletion to preserve user financial data
# Users' financial analysis and chat history will be preserved between sessions
print("[INFO] Financial advisor module loaded - user data preserved.")

advisor_bp = Blueprint('advisor', __name__, url_prefix='/financial_advisor')

@advisor_bp.route('/page', methods=['GET'])
@login_required
def dashboard():
    # Render the blank financial advisor page
    return render_template('financial_advisor.html')

@advisor_bp.route('/', methods=['GET'])
@login_required
def dashboard_api():
    """
    API endpoint to get the latest financial analysis for the logged-in user.
    Returns JSON with the latest analysis or a message if none exists.
    """
    user_id = session.get('user_id')
    from .support import db_connection, get_latest_analysis
    with db_connection() as conn:
        analysis = get_latest_analysis(conn, user_id, with_budget=True)
    if analysis:
        _, _, analysis_text, _, _ = analysis
        return jsonify({
            'user_id': user_id,
            'analysis': analysis_text
        })
    else:
        return jsonify({
            'user_id': user_id,
            'analysis': None,
            'message': 'No analysis found. Please upload a statement.'
        })

@advisor_bp.route('/debug_session', methods=['GET'])
def debug_session():
    from flask import session
    return jsonify({
        'session_user_id': session.get('user_id'),
        'session': dict(session)
    })

@advisor_bp.route('/chat', methods=['POST'])
def chat_api():
    """
    API endpoint for chat with the financial advisor. Expects JSON with 'message' and 'user_id'.
    Returns JSON with the AI response or error.
    """
    data = request.json
    user_msg = data.get('message')
    user_id = data.get('user_id')
    if user_id:
        user_id = user_id.strip()
    else:
        user_id = session.get('user_id', '').strip()
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    if not user_msg or not user_msg.strip():
        return jsonify({'error': 'Message is required'}), 400
    # Fetch latest analysis from database for context
    with db_connection() as conn:
        analysis = get_latest_analysis(conn, user_id, with_budget=True)
    if not analysis:
        return jsonify({'error': 'No financial analysis found for your account. Please upload a statement and ensure it is processed successfully before chatting.'}), 400
    analysis_id, statement_text, analysis_text, transactions_json, ai_budget_plan = analysis
    # Build a context-aware prompt
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
        "model": "google/gemma-2-9b-it",
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
            return jsonify({'error': 'AI service did not return a valid response. Please try again later.'}), 502
        assistant_msg = result['choices'][0]['message']['content']
        import re
        assistant_msg = re.sub(r'\*{3,}', '', assistant_msg)
        assistant_msg = re.sub(r'\*{2}', '', assistant_msg)
        assistant_msg = re.sub(r'\*', '', assistant_msg)
        assistant_msg = re.sub(r'#+', '', assistant_msg)
        assistant_msg = re.sub(r'^\s*- ', '• ', assistant_msg, flags=re.MULTILINE)
    except requests.exceptions.Timeout:
        return jsonify({'error': 'AI service timed out. Please try again later.'}), 504
    except Exception as e:
        return jsonify({'error': f'AI service error: {str(e)}'}), 500
    # Save chat history to database
    with db_connection() as conn:
        save_advisor_chat(conn, user_id, analysis_id, context_prompt, assistant_msg)
    return jsonify({'response': assistant_msg})

@advisor_bp.route('/upload', methods=['POST'])
def upload_statement_api():
    """
    API endpoint for uploading a financial statement. Expects multipart/form-data with 'file' and 'user_id'.
    Returns JSON with analysis and file info, or error.
    """
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
        save_dir = os.path.join(current_app.static_folder, 'statements')
        os.makedirs(save_dir, exist_ok=True)
        safe_name = secure_filename(file.filename)
        save_path = os.path.join(save_dir, safe_name)
        file.seek(0)
        file.save(save_path)
        pdf_url = url_for('static', filename=f'statements/{safe_name}')
        # Extract text from PDF for analysis (robust: native text first, OCR as best-effort)
        import PyPDF2
        from pdf2image import convert_from_bytes
        import pytesseract
        text = ""

        # 1) Extract native PDF text (PyPDF2)
        try:
            with open(save_path, 'rb') as f_pdf:
                reader = PyPDF2.PdfReader(f_pdf)
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        text += f"\n[PDF Page {i+1} Text]\n" + page_text + "\n"
        except Exception as e:
            print(f"[PDF Text Extraction] Exception: {e}")

        # 2) Best-effort OCR (do not fail overall if OCR not available)
        try:
            with open(save_path, 'rb') as f_bytes:
                pdf_bytes = f_bytes.read()
            images = convert_from_bytes(pdf_bytes)
            for i, img in enumerate(images):
                try:
                    ocr_text = pytesseract.image_to_string(img)
                    if ocr_text.strip():
                        text += f"\n[PDF Page {i+1} OCR]\n" + ocr_text + "\n"
                except Exception as e:
                    print(f"[OCR] Page {i+1} failed: {e}")
        except Exception as e:
            print(f"[OCR Pipeline] Skipping OCR due to error: {e}")

        print(f"[Final Extraction] Total text length sent to AI: {len(text)}")
        print(f"[Final Extraction] Sample: {text[:500]}")
        if not text.strip():
            return jsonify({'error': 'Could not extract any text from the statement. Ensure Poppler/Tesseract are installed or upload a text-based PDF.'}), 400
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
                    "model": "google/gemma-2-9b-it",
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
        from .support import db_connection, save_statement_analysis
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
            # Handle patterns like: 01/04/2025 Desc 6,500.00 - 2,000.00
            pattern1 = re.compile(r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d,]+\.\d{2})\s*-\s*([\d,]+\.\d{2})$', re.MULTILINE)
            for match in pattern1.finditer(text):
                date, desc, debit, credit = match.groups()
                debit = float(debit.replace(",", "")) if debit else 0.0
                credit = float(credit.replace(",", "")) if credit else 0.0
                amount = credit - debit
                txs.append({
                    'date': date,
                    'description': desc.strip(),
                    'amount': amount,
                    'debit': debit,
                    'credit': credit,
                    'category': None
                })
            # Fallback: single signed amount (e.g., -1,200.00)
            pattern2 = re.compile(r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(-?[\d,]+\.\d{2})$', re.MULTILINE)
            for match in pattern2.finditer(text):
                date, desc, amt = match.groups()
                if any(t['date'] == date and t['description'] == desc.strip() for t in txs):
                    continue
                amount = float(amt.replace(",", ""))
                debit = abs(amount) if amount < 0 else 0.0
                credit = amount if amount > 0 else 0.0
                txs.append({
                    'date': date,
                    'description': desc.strip(),
                    'amount': amount,
                    'debit': debit,
                    'credit': credit,
                    'category': None
                })
            return txs
        transactions = parse_transactions(text)
        session['advisor_transactions'] = transactions
        from datetime import datetime
        print(f"[UPLOAD] Returning analysis for {file.filename}: {ai_analysis[:100]}...")
        return jsonify(
            success=True,
            pdf_url=pdf_url,
            file_name=file.filename,
            uploaded_at=datetime.utcnow().isoformat() + 'Z',
            analysis=ai_analysis,
            statement_text=text,
            transactions=transactions
        )