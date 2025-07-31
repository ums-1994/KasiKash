document.addEventListener('DOMContentLoaded', () => {
    const chatbotContainer = document.getElementById('chatbot-container');
    const chatbotMain = document.getElementById('chatbot-main'); // The main chatbot content wrapper
    const chatbotFab = document.getElementById('chatbot-fab'); // The floating action button
    const chatbotToggle = document.getElementById('chatbot-toggle'); // The minimize button inside the chat
    const chatMessages = document.getElementById('chatbot-messages');
    const userInput = document.getElementById('user-message');
    const sendButton = document.getElementById('send-message');
    const quickTipsBtn = document.getElementById('quick-tips');
    const quickTipsMenu = document.getElementById('quick-tips-menu');
    const aiModeToggle = document.getElementById('ai-mode-toggle');
    const currentMode = document.getElementById('current-mode');
    
    let isProcessing = false;
    let isAIMode = false; // Default to App Mode
    
    // Only clear chat history on the first load of the app (not on every page navigation)
    if (!sessionStorage.getItem('kasiChatHistoryCleared')) {
        localStorage.removeItem('kasiChatHistory');
        sessionStorage.setItem('kasiChatHistoryCleared', 'true');
    }
    
    // Load AI mode preference from localStorage
    const savedAIMode = localStorage.getItem('kasiAIMode');
    if (savedAIMode !== null) {
        isAIMode = savedAIMode === 'true';
        aiModeToggle.checked = isAIMode;
        updateModeDisplay();
    } else {
        aiModeToggle.checked = false; // Default toggle to App Mode
        updateModeDisplay();
    }
    
    // AI Mode Toggle Handler
    aiModeToggle.addEventListener('change', () => {
        isAIMode = aiModeToggle.checked;
        localStorage.setItem('kasiAIMode', isAIMode.toString());
        updateModeDisplay();
        
        // Add a mode change message
        const modeMessage = isAIMode ? 
            '🤖 Switched to AI Mode - Powered by Google Gemma 3n 4B' : 
            '📱 Switched to App Mode - Quick responses';
        addMessage(modeMessage, 'bot');
    });
    
    function updateModeDisplay() {
        if (isAIMode) {
            currentMode.textContent = '🤖 AI Mode';
            document.querySelector('.mode-label').textContent = 'AI Mode';
            chatbotContainer.classList.remove('app-mode');
        } else {
            currentMode.textContent = '📱 App Mode';
            document.querySelector('.mode-label').textContent = 'App Mode';
            chatbotContainer.classList.add('app-mode');
        }
    }

    // Initial state: chatbot starts minimized (class already on container)
    // No need for isMinimized flag here, controlled by classList

    // Function to set chatbot state
    function setChatbotState(minimized) {
        if (minimized) {
            chatbotContainer.classList.add('minimized');
            chatbotToggle.title = 'Open Chat';
            chatbotToggle.textContent = '+';
        } else {
            chatbotContainer.classList.remove('minimized');
            chatbotToggle.title = 'Minimize';
            chatbotToggle.textContent = '−';
            chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll to bottom when opened
        }
    }

    // Toggle chat window from header button
    chatbotToggle.addEventListener('click', () => {
        const currentlyMinimized = chatbotContainer.classList.contains('minimized');
        setChatbotState(!currentlyMinimized);
    });

    // Open chat window from FAB
    chatbotFab.addEventListener('click', () => {
        setChatbotState(false); // Open the chatbot
    });

    // Allow clicking the header to minimize/maximize (excluding controls)
    document.getElementById('chatbot-header').addEventListener('click', (e) => {
        if (e.target !== chatbotToggle && e.target !== quickTipsBtn && !e.target.closest('.chat-controls')) {
            const currentlyMinimized = chatbotContainer.classList.contains('minimized');
            setChatbotState(!currentlyMinimized);
        }
    });
    
    // Quick tips functionality
    quickTipsBtn.addEventListener('click', () => {
        quickTipsMenu.classList.toggle('hidden');
    });
    
    // Handle tip selection
    document.querySelectorAll('.tip').forEach(tip => {
        tip.addEventListener('click', () => {
            const question = tip.getAttribute('data-question');
            userInput.value = question;
            quickTipsMenu.classList.add('hidden');
            sendMessage();
        });
    });
    
    // Close tips when clicking outside
    document.addEventListener('click', (e) => {
        if (!quickTipsBtn.contains(e.target) && !quickTipsMenu.contains(e.target)) {
            quickTipsMenu.classList.add('hidden');
        }
    });
    
    // Send message on button click
    sendButton.addEventListener('click', sendMessage);
    
    // Send message on Enter key
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Function to show loading state
    function showLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message bot-message loading';
        loadingDiv.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return loadingDiv;
    }
    
    // --- Enhanced App Mode Fuzzy Matching Logic ---
    // Utility: basic fuzzyMatch (allows Levenshtein distance <= 1)
    function fuzzyMatch(word, token) {
      if (word === token) return true;
      if (Math.abs(word.length - token.length) > 1) return false;
      const dp = Array.from({ length: word.length + 1 }, () => []);
      for (let i = 0; i <= word.length; i++) dp[i][0] = i;
      for (let j = 0; j <= token.length; j++) dp[0][j] = j;
      for (let i = 1; i <= word.length; i++) {
        for (let j = 1; j <= token.length; j++) {
          dp[i][j] = Math.min(
            dp[i-1][j] + 1,
            dp[i][j-1] + 1,
            dp[i-1][j-1] + (word[i-1] === token[j-1] ? 0 : 1)
          );
        }
      }
      return dp[word.length][token.length] <= 1;
    }

    // Normalize input: lowercase, split, remove punctuation
    function tokenize(input) {
      return input
        .toLowerCase()
        .replace(/[.,!?]/g, "")
        .split(/\s+/)
        .filter(Boolean);
    }

    const appModeResponses = [
      // Greetings & Conversation
      { keywords: ["hi", "hello", "hey", "greetings", "howdy", "morning", "afternoon", "evening"], response: `Hi there! How can I help you with KasiKash today? 😊`, isConversational: true },
      { keywords: ["how", "are", "you"], response: `I'm great, thanks for asking! How can I help you today?`, isConversational: true },
      { keywords: ["what", "can", "you", "do"], response: `I can help you with stokvel management, savings goals, payments, rewards, and more. Just ask!` },
      { keywords: ["who", "are", "you"], response: `I'm KasiKash Assistant, your friendly financial helper!`, isConversational: true },
      { keywords: ["thank", "you"], response: `You're welcome! Let me know if you need anything else.`, isConversational: true },
      { keywords: ["thanks"], response: `Happy to help!`, isConversational: true },

      // Authentication & Profile
      { keywords: ["login", "register", "sign in", "sign up", "log in", "log out", "logout", "password", "reset"], response: `Use Login or Register on the Home screen. For password resets, tap Forgot Password.`, isConversational: true },
      { keywords: ["profile", "update", "edit", "account", "picture", "avatar", "change"], response: `Go to Profile, tap Edit, update fields or upload a picture, then hit Save.`, isConversational: true },
      { keywords: ["kyc", "verification", "verify", "identity", "documents"], response: `Under Profile, upload your KYC documents, then await admin approval.`, isConversational: true },

      // Stokvels
      { keywords: ["create", "stokvel", "group", "new stokvel", "start stokvel"], response: "__CREATE_STOKVEL__" },
      { keywords: ["join", "stokvel", "group", "participate"], response: `On Stokvels, search your group, tap Join, and wait for approval.`, isConversational: true },
      { keywords: ["leave", "stokvel", "group", "exit"], response: `Select your group, scroll to Leave Group, and confirm.`, isConversational: true },
      { keywords: ["members", "stokvel", "participants", "people", "view members", "see members"], response: `In Stokvels, open your group, then tap Members to view participants.`, isConversational: true },
      { keywords: ["delete", "stokvel", "remove group", "close stokvel"], response: `As an admin, open the group settings and choose Delete Stokvel, then confirm.`, isConversational: true },

      // Contributions & Payouts
      { keywords: ["make", "contribution", "contribute", "add money", "deposit"], response: `Open a stokvel, tap Contribute, choose amount and payment method, then confirm.`, isConversational: true },
      { keywords: ["view", "contributions", "history", "my contributions", "see contributions"], response: `In your stokvel, go to the Contributions tab to see history.`, isConversational: true },
      { keywords: ["request", "payout", "withdraw", "get money", "cash out"], response: `Navigate to Payouts, tap Request Payout, enter amount, and submit.`, isConversational: true },
      { keywords: ["view", "payouts", "withdrawals", "see payouts", "payout history"], response: `Under Payouts, see all requests and their statuses.`, isConversational: true },

      // Savings Goals
      { keywords: ["create", "goal", "savings goal", "new goal", "set goal"], response: `Go to Goals, tap + New Goal, set target and deadline, then save.`, isConversational: true },
      { keywords: ["track", "progress", "goal progress", "goal status", "goal summary"], response: `Select a goal on Goals to view its progress bar and summary.`, isConversational: true },
      { keywords: ["contribute", "goal", "add funds", "add to goal", "save to goal"], response: `Inside a goal, tap Add Funds, enter amount, and confirm.`, isConversational: true },

      // Payment Methods
      { keywords: ["add", "payment", "bank", "card", "new payment", "link account"], response: `In Settings > Payment Methods, tap Add New, enter details, and save.`, isConversational: true },
      { keywords: ["remove", "payment", "delete payment", "unlink", "remove card", "remove bank"], response: `In Payment Methods, select the method, tap Remove, then confirm.`, isConversational: true },

      // Rewards & Marketplace
      { keywords: ["view", "rewards", "rewards card", "points", "vouchers", "my rewards", "my rewards card", "voucher"], response: `Tap the Rewards icon to see your points and vouchers.`, isConversational: true },
      { keywords: ["redeem", "points", "use points", "spend points", "claim voucher"], response: `Within Rewards, select a voucher or item, tap Redeem, and confirm.`, isConversational: true },
      { keywords: ["marketplace", "shop", "buy", "store", "redeemable items"], response: `Open the Marketplace tab under Rewards to browse redeemable items.`, isConversational: true },

      // Notifications
      { keywords: ["view", "notifications", "alerts", "messages", "see notifications"], response: `Tap the bell icon to access your Notifications panel.`, isConversational: true },
      { keywords: ["clear", "notifications", "mark as read", "delete notifications"], response: `In Notifications, use Mark as Read or Clear All to manage alerts.`, isConversational: true },

      // Dashboard & Insights
      { keywords: ["dashboard", "overview", "main page", "home"], response: `The Dashboard shows your active groups, recent activity, and key metrics.`, isConversational: true },
      { keywords: ["insights", "charts", "summary", "analytics", "statistics"], response: `Go to Insights for charts and summaries of your savings and spending.`, isConversational: true },

      // Multilingual & Themes
      { keywords: ["language", "translate", "switch language", "change language"], response: `In Settings, choose Language to switch the app's language.`, isConversational: true },
      { keywords: ["dark", "mode", "theme", "light mode"], response: `Toggle Dark Mode in Settings to switch themes.`, isConversational: true },

      // Admin Functions
      { keywords: ["approve", "kyc", "admin", "kyc approval", "verify user"], response: `As an admin, visit KYC Approvals in the Admin Dashboard to review and approve.`, isConversational: true },
      { keywords: ["manage", "users", "user management", "admin users", "edit users"], response: `Under Admin > User Management, add, edit, or delete user accounts.`, isConversational: true },
      { keywords: ["generate", "report", "export", "pdf", "financial report"], response: `In Admin > Reports, select date range and click Export PDF.`, isConversational: true },

      // Financial Advisor
      { keywords: ["upload", "statement", "bank statement", "advisor", "analyze statement", "analyze", "analysis"], response: `Go to Financial Advisor, tap Upload Statement, select your PDF, and upload.`, isConversational: true },
      { keywords: ["analyze", "statement", "insights", "ai analysis", "advisor"], response: `After uploading, view AI-generated insights on the Advisor page.`, isConversational: true },
      { keywords: ["chat", "assistant", "ask", "question", "financial assistant"], response: `Use the Financial Assistant chat to ask follow-up questions.`, isConversational: true },

      // Help & Feedback
      { keywords: ["help", "guides", "faq", "support", "docs", "documentation"], response: `Tap Help or Docs in the menu to access user guides and FAQs.`, isConversational: true },
      { keywords: ["feedback", "contact", "report", "issue", "bug"], response: `Go to Contact/Feedback to send us a message or report issues.`, isConversational: true },

      // Fallback
      { keywords: [], response: `Sorry, I don't have a built-in answer for that. Switch to AI Mode for detailed help or contact support.`, isConversational: true }
    ];

    function getAppModeResponse(userInput) {
      const tokens = tokenize(userInput);
      let bestFeatureMatch = null;
      let bestFeatureScore = 0;
      let bestConversationalMatch = null;
      let bestConversationalScore = 0;

      // Feature/function rules first
      for (let entry of appModeResponses) {
        if (entry.isConversational) continue;
        let score = entry.keywords.reduce((acc, word) => acc + (tokens.some(t => fuzzyMatch(word, t)) ? 1 : 0), 0);
        if (score > bestFeatureScore) {
          bestFeatureScore = score;
          bestFeatureMatch = entry;
        }
      }
      if (bestFeatureMatch && bestFeatureScore > 0) return bestFeatureMatch.response;

      // Conversational rules second
      for (let entry of appModeResponses) {
        if (!entry.isConversational) continue;
        let score = entry.keywords.reduce((acc, word) => acc + (tokens.some(t => fuzzyMatch(word, t)) ? 1 : 0), 0);
        if (score > bestConversationalScore) {
          bestConversationalScore = score;
          bestConversationalMatch = entry;
        }
      }
      if (bestConversationalMatch && bestConversationalScore > 0) return bestConversationalMatch.response;

      // Fallback
      const fallback = appModeResponses.find(e => e.keywords.length === 0);
      return fallback ? fallback.response : "Sorry, I don't have an answer for that. Switch to AI Mode for more help.";
    }
    
    // --- Stokvel Creation Wizard State ---
    let stokvelWizardActive = false;
    let stokvelWizardStep = 0;
    let stokvelWizardData = {};

    function startStokvelCreation() {
      stokvelWizardActive = true;
      stokvelWizardStep = 1;
      stokvelWizardData = {};
      addMessage("Let's create a new stokvel! What would you like to name your stokvel?", 'bot');
    }

    function handleStokvelWizardInput(userInput) {
      if (stokvelWizardStep === 1) {
        stokvelWizardData.name = userInput;
        stokvelWizardStep = 2;
        addMessage(`Please enter a description for your stokvel (or type 'skip' to leave it blank).`, 'bot');
      } else if (stokvelWizardStep === 2) {
        stokvelWizardData.description = (userInput.trim().toLowerCase() === 'skip') ? '' : userInput;
        stokvelWizardStep = 3;
        addMessage(`What is the monthly contribution amount? (Enter a number in Rands, e.g., 100)`, 'bot');
      } else if (stokvelWizardStep === 3) {
        let amt = userInput.replace(/R|,/g, '').trim();
        if (isNaN(amt) || Number(amt) <= 0) {
          addMessage(`Please enter a valid positive number for the monthly contribution.`, 'bot');
          return;
        }
        stokvelWizardData.monthly_contribution = Number(amt);
        stokvelWizardStep = 4;
        addMessage(`What is the target amount for this stokvel? (Enter a number in Rands, or 0 if no target)`, 'bot');
      } else if (stokvelWizardStep === 4) {
        let amt = userInput.replace(/R|,/g, '').trim();
        if (isNaN(amt) || Number(amt) < 0) {
          addMessage(`Please enter a valid number for the target amount.`, 'bot');
          return;
        }
        stokvelWizardData.target_amount = Number(amt);
        stokvelWizardStep = 5;
        addMessage(`What is the target date? (Format: YYYY-MM-DD, or type 'none' for no specific date)`, 'bot');
      } else if (stokvelWizardStep === 5) {
        let date = userInput.trim();
        if (date.toLowerCase() === 'none') {
          stokvelWizardData.target_date = '';
        } else {
          // Validate date format
          if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
            addMessage(`Please enter a valid date in YYYY-MM-DD format, or type 'none'.`, 'bot');
            return;
          }
          stokvelWizardData.target_date = date;
        }
        // All data collected, submit via AJAX
        submitStokvelWizardData();
      }
    }

    async function submitStokvelWizardData() {
      addMessage('Creating your stokvel, please wait...', 'bot');
      try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        const response = await fetch('/create_stokvel', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken
          },
          body: new URLSearchParams({
            name: stokvelWizardData.name,
            description: stokvelWizardData.description,
            monthly_contribution: stokvelWizardData.monthly_contribution,
            target_amount: stokvelWizardData.target_amount,
            target_date: stokvelWizardData.target_date,
            csrf_token: csrfToken
          })
        });
        if (response.redirected) {
          // Success, reload to show new stokvel
          addMessage('Stokvel created successfully! Reloading to show your new stokvel...', 'bot');
          setTimeout(() => window.location.reload(), 2000);
          stokvelWizardActive = false;
          stokvelWizardStep = 0;
          stokvelWizardData = {};
          return;
        }
        const text = await response.text();
        if (text.includes('Stokvel created successfully')) {
          addMessage('Stokvel created successfully! Reloading to show your new stokvel...', 'bot');
          setTimeout(() => window.location.reload(), 2000);
        } else {
          addMessage('Sorry, there was a problem creating your stokvel. Please try again.', 'bot');
        }
      } catch (e) {
        addMessage('Sorry, there was a system error creating your stokvel. Please try again.', 'bot');
      }
      stokvelWizardActive = false;
      stokvelWizardStep = 0;
      stokvelWizardData = {};
    }
    
    // Function to send message to chatbot
    async function sendMessage() {
        const message = userInput.value.trim();
        
        if (!message || isProcessing) return;
        
        isProcessing = true;
        sendButton.disabled = true;
        userInput.disabled = true;
        
        // Add user message to chat
        addMessage(message, 'user');
        userInput.value = '';
        
        // Show loading indicator
        const loadingIndicator = showLoading();
        
        try {
            if (!isAIMode) {
                // --- App Mode: Use local rule-based response ---
                if (stokvelWizardActive) {
                    loadingIndicator.remove();
                    handleStokvelWizardInput(message);
                } else {
                    const reply = getAppModeResponse(message) || "Sorry, I don't have an answer for that. Switch to AI Mode for more help.";
                    loadingIndicator.remove();
                    if (reply === "__CREATE_STOKVEL__") {
                      startStokvelCreation();
                    } else {
                      addMessage(reply, 'bot');
                    }
                }
            } else {
                // --- AI Mode: Send to backend as before ---
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                    body: JSON.stringify({ message: message, mode: 'ai' })
            });
            
            loadingIndicator.remove();
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to get response from chatbot');
            }
            
            const data = await response.json();
            let botResponse = data.response.replace(/\*+/g, '');
            addMessage(botResponse, 'bot');
            }
        } catch (error) {
            loadingIndicator.remove();
            addMessage('Sorry, I encountered an error. Please try again later.', 'bot', 'error');
        } finally {
            isProcessing = false;
            sendButton.disabled = false;
            userInput.disabled = false;
            userInput.focus();
        }
    }
    
    // Function to add message to chat
    function addMessage(message, sender, type = 'normal') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        if (type === 'error') {
            messageDiv.classList.add('error-message');
        }
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Format message content
        if (message.includes('→')) {
            const parts = message.split('→');
            messageContent.innerHTML = `
                <div>${parts[0]}</div>
                <div class="calculation">${parts[1]}</div>
            `;
        } else {
            // Convert URLs to clickable links
            const urlRegex = /(https?:\/\/[^\s]+)/g;
            message = message.replace(urlRegex, url => `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`);
            
            // Convert numbers with R symbol to highlighted amounts
            message = message.replace(/R(\d+(?:\.\d{2})?)/g, '<span class="amount">R$1</span>');
            
            messageContent.innerHTML = message;
        }
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Save to chat history
        saveChatHistory();
    }
    
    // Chat history persistence
    function saveChatHistory() {
        const messages = Array.from(chatMessages.children).map(el => {
            return {
                text: el.textContent,
                type: el.classList.contains('user-message') ? 'user' : 'bot',
                html: el.innerHTML
            };
        });
        localStorage.setItem('kasiChatHistory', JSON.stringify(messages));
    }
    
    function loadChatHistory() {
        const history = JSON.parse(localStorage.getItem('kasiChatHistory') || '[]');
        if (history.length > 0) {
            history.forEach(msg => {
                const messageDiv = document.createElement('div');
                messageDiv.classList.add('message', `${msg.type}-message`);
                messageDiv.innerHTML = msg.html || msg.text;
                chatMessages.appendChild(messageDiv);
            });
            chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll to bottom after loading
            return true; // History was loaded
        }
        return false; // No history
    }
    
    // Load history on startup, add welcome message only if no history
    const historyLoaded = loadChatHistory();
    if (!historyLoaded) {
        addMessage('Hello! I\'m KasiKash Assistant. How can I help you today?', 'bot');
    }

    // Initial state check for FAB display (since it's minimized by default in HTML)
    setChatbotState(true); 
}); 