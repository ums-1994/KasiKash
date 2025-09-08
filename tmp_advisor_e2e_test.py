import re
import requests

BASE = 'http://127.0.0.1:5000'
EMAIL = 'dzunisanimabunda85@gmail.com'

sess = requests.Session()

def get_csrf_from_html(html: str) -> str:
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    return m.group(1) if m else ''

def get_meta_csrf(html: str) -> str:
    m = re.search(r'<meta name="csrf-token" content="([^"]+)"', html)
    return m.group(1) if m else ''

print('[STEP] GET /login')
r = sess.get(f'{BASE}/login')
r.raise_for_status()
csrf_login = get_csrf_from_html(r.text)
print('[INFO] login csrf len:', len(csrf_login))

print('[STEP] POST /login_validation')
payload = {
    'csrf_token': csrf_login,
    'email': EMAIL,
    'password': 'dummy',
    'remember': 'y'
}
r = sess.post(f'{BASE}/login_validation', data=payload, allow_redirects=False)
print('[INFO] login status:', r.status_code, 'location:', r.headers.get('Location'))
if r.status_code in (301, 302):
    sess.get(BASE + r.headers['Location'])

print('[STEP] GET /financial_advisor/')
r = sess.get(f'{BASE}/financial_advisor/')
r.raise_for_status()
csrf_meta = get_meta_csrf(r.text)
print('[INFO] advisor meta csrf len:', len(csrf_meta))

# Try to parse user_id from the hidden input in the upload form
m_uid = re.search(r'name="user_id"\s+value="([^"]+)"', r.text)
user_id = m_uid.group(1) if m_uid else ''
print('[INFO] user_id:', user_id)

print('[STEP] POST /financial_advisor/upload')
files = {
    'file': ('mechanic_bank_statement.pdf', open('mechanic_bank_statement.pdf', 'rb'), 'application/pdf')
}
data = {
    'csrf_token': csrf_meta or csrf_login,
    'user_id': user_id
}
headers = {'X-CSRFToken': csrf_meta} if csrf_meta else {}
r = sess.post(f'{BASE}/financial_advisor/upload', data=data, files=files, headers=headers)
print('[RESULT]', r.status_code)
print(r.text[:2000])


