// Financial Advisor Page JS

// --- Chat Functionality ---
async function sendChat(msg) {
  const res = await fetch('/financial_advisor/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ user_id: window.USER_ID || '', message: msg })
  });
  const data = await res.json();
  return data.response;
}

function appendMessage(who, text) {
  const box = document.getElementById('messages');
  const el = document.createElement('div');
  el.className = (who === 'You') ? 'text-right text-green-600' : 'text-left text-gray-800';
  el.textContent = who + ': ' + text;
  box.appendChild(el);
  box.scrollTop = box.scrollHeight;
}

function initChat() {
  const sendBtn = document.getElementById('chat-send');
  const input = document.getElementById('chat-input');
  if (!sendBtn || !input) return;
  sendBtn.onclick = async function() {
    const txt = input.value.trim();
    if (!txt) return;
    appendMessage('You', txt);
    input.value = '';
    const reply = await sendChat(txt);
    appendMessage('Advisor', reply);
  };
  input.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') sendBtn.click();
  });
}

// --- Upload Functionality ---
function initUpload() {
  const form = document.getElementById('upload-form');
  if (!form) return;
  form.onsubmit = async function(e) {
    e.preventDefault();
    const data = new FormData(form);
    const res = await fetch(form.action || '/financial_advisor/upload', { method: 'POST', body: data });
    const json = await res.json();
    const container = document.getElementById('upload-results');
    container.innerHTML = '';
    if (json.alerts) {
      json.alerts.forEach(function(a) {
        const div = document.createElement('div');
        div.className = 'text-red-600';
        div.textContent = a;
        container.appendChild(div);
      });
    }
    if (json.transactions) {
      // Simple table of txns
      const tbl = document.createElement('table');
      tbl.className = 'min-w-full text-left mt-2';
      tbl.innerHTML = '<thead><tr><th>Date</th><th>Description</th><th>Amount</th></tr></thead>';
      const body = document.createElement('tbody');
      json.transactions.forEach(function(t) {
        const row = document.createElement('tr');
        row.innerHTML = '<td>' + t.date + '</td><td>' + t.description + '</td><td>R' + Number(t.amount).toFixed(2) + '</td>';
        body.appendChild(row);
      });
      tbl.appendChild(body);
      container.appendChild(tbl);
    }
  };
}

// --- Initialization ---
window.addEventListener('DOMContentLoaded', function() {
  initChat();
  initUpload();
}); 