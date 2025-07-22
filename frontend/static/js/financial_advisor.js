// Financial Advisor Page JS

// --- Chat Functionality ---
async function sendChat(msg) {
  try {
    const res = await fetch('/financial_advisor/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
      },
      body: JSON.stringify({ user_id: window.USER_ID || '', message: msg })
    });
    if (!res.ok) {
      let errorMsg = 'An error occurred.';
      try {
        const errData = await res.json();
        errorMsg = errData.error || errorMsg;
      } catch (e) {}
      throw new Error(errorMsg);
    }
    const data = await res.json();
    return data.response;
  } catch (err) {
    return '[Error] ' + (err.message || 'Failed to contact assistant.');
  }
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
    sendBtn.disabled = true;
    const box = document.getElementById('messages');
    const loadingEl = document.createElement('div');
    loadingEl.className = 'text-left text-gray-400';
    loadingEl.textContent = 'Advisor is typing...';
    box.appendChild(loadingEl);
    box.scrollTop = box.scrollHeight;
    const reply = await sendChat(txt);
    box.removeChild(loadingEl);
    appendMessage('Advisor', reply);
    sendBtn.disabled = false;
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
    const container = document.getElementById('upload-results');
    container.innerHTML = '<div class="text-blue-600">Analyzing your statement...</div>';
    const data = new FormData(form);
    try {
      const res = await fetch(form.action || '/financial_advisor/upload', {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCSRFToken()
        },
        body: data
      });
      const json = await res.json();
      container.innerHTML = '';
      if (json.error) {
        container.innerHTML = '<div class="text-red-600">' + json.error + '</div>';
        return;
      }
      if (json.success) {
        container.innerHTML = '<div class="text-green-600">Statement uploaded and analysis complete!</div>';
      }
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
      if (json.analysis) {
        const analysisCard = document.createElement('div');
        analysisCard.className = 'mt-6 p-4 rounded-lg border border-cyan-400 bg-blue-900 text-cyan-100 shadow-lg';
        analysisCard.innerHTML = '<h3 class="font-semibold text-cyan-300 mb-2">AI Financial Analysis & Advice</h3>' +
          '<div style="white-space: pre-line;">' + json.analysis + '</div>';
        container.appendChild(analysisCard);
      }
    } catch (err) {
      container.innerHTML = '<div class="text-red-600">An error occurred. Please try again.</div>';
    }
  };
}

// Add this function at the top
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// --- Initialization ---
window.addEventListener('DOMContentLoaded', function() {
  initChat();
  initUpload();
});