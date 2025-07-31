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
      if (json.pdf_url) {
        // Display the PDF in an iframe
        const pdfFrame = document.createElement('iframe');
        pdfFrame.src = json.pdf_url;
        pdfFrame.width = '100%';
        pdfFrame.height = '600px';
        pdfFrame.style.border = '1px solid #ccc';
        pdfFrame.title = 'Uploaded Statement';
        container.appendChild(pdfFrame);
      }
      // Transaction table rendering removed as per user request
      if (json.analysis) {
        const analysisCard = document.createElement('div');
        analysisCard.className = 'mt-6 p-4 rounded-lg border border-cyan-400 bg-blue-900 text-cyan-100 shadow-lg';
        analysisCard.innerHTML = '<h3 class="font-semibold text-cyan-300 mb-2">AI Financial Analysis & Advice</h3>' +
          '<div style="white-space: pre-line;">' + json.analysis + '</div>';
        container.appendChild(analysisCard);
      }
      // --- Trigger chart update after upload ---
      if (json.transactions && Array.isArray(json.transactions) && json.transactions.length > 0) {
        window.ADVISOR_TRANSACTIONS = json.transactions;
        renderAdvisorCharts(json.transactions);
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

// --- Parse metrics, recent activity, and chart data from AI analysis/advice text ---
function parseAdvisorAnalysis(analysisHtml) {
  // This is a simple parser for the specific AI output format you provided.
  // It extracts numbers and categories from the advice text for metrics and charts.
  if (!analysisHtml) return { metrics: {}, recent: [], chart: { categories: {}, timeline: [] } };
  const text = analysisHtml.replace(/<[^>]+>/g, ''); // Strip HTML tags
  // Extract key metrics
  const incomeMatch = text.match(/ZAR\s*([\d,]+)\s*on the 25th of each month/);
  const rentMatch = text.match(/Rent: ZAR\s*([\d,]+)/);
  const utilitiesMatch = text.match(/Utilities: ZAR\s*([\d,]+)/);
  const groceriesMatch = text.match(/Groceries: ZAR\s*([\d,]+)/);
  const closingMatch = text.match(/closing balance.*?ZAR\s*([\d,]+)/i);
  const netSavingsMatch = text.match(/Leaves ZAR\s*([\d,]+) from the ZAR/);
  // Extract recent activity (use the sample monthly cash flow plan table)
  const recent = [];
  const tableRegex = /\|\s*([A-Za-z\/ ]+)\s*\|\s*ZAR ([\d,]+)\s*\|/g;
  let m;
  while ((m = tableRegex.exec(text)) !== null) {
    recent.push({
      description: m[1].trim(),
      amount: parseFloat(m[2].replace(/,/g, '')),
      date: '',
      category: m[1].trim()
    });
  }
  // For charts, aggregate by category
  const categories = {};
  recent.forEach(tx => {
    if (!categories[tx.category]) categories[tx.category] = 0;
    categories[tx.category] += tx.amount;
  });
  // Timeline: just use the order in the table
  const timeline = recent.map((tx, i) => ({ date: `Step ${i+1}`, amount: tx.amount }));
  // Metrics
  const metrics = {
    income: incomeMatch ? parseFloat(incomeMatch[1].replace(/,/g, '')) : null,
    rent: rentMatch ? parseFloat(rentMatch[1].replace(/,/g, '')) : null,
    utilities: utilitiesMatch ? parseFloat(utilitiesMatch[1].replace(/,/g, '')) : null,
    groceries: groceriesMatch ? parseFloat(groceriesMatch[1].replace(/,/g, '')) : null,
    closing: closingMatch ? parseFloat(closingMatch[1].replace(/,/g, '')) : null,
    netSavings: netSavingsMatch ? parseFloat(netSavingsMatch[1].replace(/,/g, '')) : null
  };
  return { metrics, recent, chart: { categories, timeline } };
}

// --- Render Overview from AI analysis ---
function renderOverviewFromAnalysis(analysisHtml) {
  const parsed = parseAdvisorAnalysis(analysisHtml);
  // Metrics
  const bar = document.getElementById('advisor-metrics-bar');
  if (bar) {
    bar.innerHTML = `
      <div class="metric-card bg-blue-900 text-cyan-200 rounded-lg p-4 min-w-[180px]">
        <div class="text-xs uppercase mb-1">Income</div>
        <div class="text-2xl font-bold">R${parsed.metrics.income?.toLocaleString() || '-'}</div>
      </div>
      <div class="metric-card bg-blue-900 text-cyan-200 rounded-lg p-4 min-w-[180px]">
        <div class="text-xs uppercase mb-1">Rent</div>
        <div class="text-2xl font-bold">R${parsed.metrics.rent?.toLocaleString() || '-'}</div>
      </div>
      <div class="metric-card bg-blue-900 text-cyan-200 rounded-lg p-4 min-w-[180px]">
        <div class="text-xs uppercase mb-1">Utilities</div>
        <div class="text-2xl font-bold">R${parsed.metrics.utilities?.toLocaleString() || '-'}</div>
      </div>
      <div class="metric-card bg-blue-900 text-cyan-200 rounded-lg p-4 min-w-[180px]">
        <div class="text-xs uppercase mb-1">Groceries</div>
        <div class="text-2xl font-bold">R${parsed.metrics.groceries?.toLocaleString() || '-'}</div>
      </div>
      <div class="metric-card bg-blue-900 text-cyan-200 rounded-lg p-4 min-w-[180px]">
        <div class="text-xs uppercase mb-1">Net Savings</div>
        <div class="text-2xl font-bold">R${parsed.metrics.netSavings?.toLocaleString() || '-'}</div>
      </div>
    `;
  }
  // Recent Activity
  const container = document.getElementById('advisor-recent-activity');
  if (container) {
    container.innerHTML = `<h3 class="text-lg font-semibold text-cyan-200 mb-2">Sample Monthly Cash Flow Plan</h3>
      <div class="space-y-2">
        ${parsed.recent.map(tx => `
          <div class="flex justify-between items-center bg-blue-950 bg-opacity-60 rounded p-2">
            <div>
              <div class="font-bold text-cyan-100">${tx.description}</div>
            </div>
            <div class="text-right">
              <div class="font-bold text-cyan-100">
                R${tx.amount.toLocaleString()}
              </div>
            </div>
          </div>
        `).join('')}
      </div>`;
  }
  // Charts
  // Pie: by category
  const pieCtx = document.getElementById('advisor-pie-chart')?.getContext('2d');
  if (pieCtx) {
    if (window.advisorPieChartInstance) window.advisorPieChartInstance.destroy();
    window.advisorPieChartInstance = new Chart(pieCtx, {
      type: 'pie',
      data: {
        labels: Object.keys(parsed.chart.categories),
        datasets: [{
          data: Object.values(parsed.chart.categories),
          backgroundColor: [
            '#60efff', '#38bdf8', '#7B61FF', '#34d399', '#fbbf24', '#f87171', '#a78bfa', '#f472b6', '#facc15', '#818cf8'
          ],
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            display: true,
            position: 'bottom',
            labels: {
              color: '#c0eaff',
              font: { family: 'Inter, Montserrat, sans-serif', size: 16 }
            }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const label = context.label || '';
                const value = context.parsed || 0;
                return `${label}: R${value.toLocaleString()}`;
              }
            },
            backgroundColor: '#222e3a',
            titleColor: '#60efff',
            bodyColor: '#fff',
            borderColor: '#60efff',
            borderWidth: 1,
            padding: 12
          },
        },
        animation: {
          animateScale: true,
          animateRotate: true
        }
      }
    });
  }
  // Line: timeline
  const lineCtx = document.getElementById('advisor-bar-chart')?.getContext('2d');
  if (lineCtx) {
    if (window.advisorLineChartInstance) window.advisorLineChartInstance.destroy();
    window.advisorLineChartInstance = new Chart(lineCtx, {
      type: 'line',
      data: {
        labels: parsed.chart.timeline.map(t => t.date),
        datasets: [{
          label: 'Cash Flow Steps',
          data: parsed.chart.timeline.map(t => t.amount),
          borderColor: '#60efff',
          backgroundColor: 'rgba(96,239,255,0.1)',
          tension: 0.4,
          fill: true,
          pointBackgroundColor: '#7B61FF',
          pointBorderColor: '#fff',
          pointRadius: 5,
          pointHoverRadius: 8,
          pointBorderWidth: 2
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            display: true,
            position: 'top',
            align: 'end',
            labels: {
              color: '#c0eaff',
              font: { family: 'Inter, Montserrat, sans-serif', size: 16 }
            }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return `R${context.parsed.y.toLocaleString()}`;
              }
            },
            backgroundColor: '#222e3a',
            titleColor: '#60efff',
            bodyColor: '#fff',
            borderColor: '#60efff',
            borderWidth: 1,
            padding: 12
          },
        },
        animation: {
          duration: 1200,
          easing: 'easeOutQuart'
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              color: '#c0eaff',
              font: { family: 'Inter, Montserrat, sans-serif', size: 14 },
              callback: function(value) { return 'R' + value; }
            },
            grid: { color: 'rgba(96,239,255,0.08)' }
          },
          x: {
            ticks: {
              color: '#c0eaff',
              font: { family: 'Inter, Montserrat, sans-serif', size: 14 }
            },
            grid: { color: 'rgba(96,239,255,0.04)' }
          }
        }
      }
    });
  }
}

// --- Hook into upload and tab switching ---
function showOverviewFromAnalysis() {
  // Find the analysis HTML in the Overview tab
  const analysisDiv = document.querySelector('#overview-advice-analysis .advisor-analysis-html');
  if (analysisDiv) {
    renderOverviewFromAnalysis(analysisDiv.innerHTML);
  }
}
// On tab switch
const tabBtns = document.querySelectorAll('.tab-btn');
tabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    const tab = btn.getAttribute('data-tab');
    if (tab === 'overview') {
      showOverviewFromAnalysis();
    }
  });
});
// On upload success
window.addEventListener('DOMContentLoaded', function() {
  initChat();
  initUpload();
  if (window.ADVISOR_TRANSACTIONS && window.ADVISOR_TRANSACTIONS.length > 0) {
    renderAdvisorCharts(window.ADVISOR_TRANSACTIONS);
  }
  showOverviewFromAnalysis();
});

// --- Tab switching logic (fix) ---
document.addEventListener('DOMContentLoaded', function() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('bg-blue-900'));
      btn.classList.add('bg-blue-900');
      const tab = btn.getAttribute('data-tab');
      tabContents.forEach(tc => tc.classList.add('hidden'));
      document.getElementById('tab-' + tab).classList.remove('hidden');
      // Also update overview if needed
      if (tab === 'overview') {
        showOverviewFromAnalysis();
      }
    });
  });
  // Set default tab (Upload) on load
  tabBtns[0].classList.add('bg-blue-900');
  tabContents.forEach((tc, i) => {
    if (i === 0) tc.classList.remove('hidden');
    else tc.classList.add('hidden');
  });
});