document.addEventListener('DOMContentLoaded', () => {
    const chatbotContainer = document.getElementById('chatbot-container');
    const chatbotMain = document.getElementById('chatbot-main'); // The main chatbot content wrapper
    const chatbotFab = document.getElementById('chatbot-fab'); // The floating action button
    const chatbotClose = document.getElementById('chatbot-close'); // The close (X) button
    const chatMessages = document.getElementById('chatbot-messages');
    const userInput = document.getElementById('user-message');
    const sendButton = document.getElementById('send-message');
    const quickTipsBtn = document.getElementById('quick-tips');
    const quickTipsMenu = document.getElementById('quick-tips-menu');
    const aiModeToggle = document.getElementById('ai-mode-toggle');
    const appModeLabel = document.getElementById('app-mode-label');
    const aiModeLabel = document.getElementById('ai-mode-label');
    const modeSegmentBg = document.querySelector('.mode-segment-bg');
    
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
    
    // Update mode display for segmented control
    function updateModeDisplay() {
        if (isAIMode) {
            chatbotContainer.classList.remove('app-mode');
            aiModeLabel.classList.add('active-ai');
            appModeLabel.classList.remove('active-app');
            modeSegmentBg.style.left = '50%';
        } else {
            chatbotContainer.classList.add('app-mode');
            appModeLabel.classList.add('active-app');
            aiModeLabel.classList.remove('active-ai');
            modeSegmentBg.style.left = '0';
        }
    }
    
    // Click handlers for segmented control
    appModeLabel.addEventListener('click', () => {
        if (isAIMode) {
            isAIMode = false;
            aiModeToggle.checked = false;
            localStorage.setItem('kasiAIMode', 'false');
            updateModeDisplay();
            addMessage('📱 Switched to App Mode - Quick responses', 'bot');
        }
    });
    aiModeLabel.addEventListener('click', () => {
        if (!isAIMode) {
            isAIMode = true;
            aiModeToggle.checked = true;
            localStorage.setItem('kasiAIMode', 'true');
            updateModeDisplay();
            addMessage('🤖 Switched to AI Mode - Powered by Google Gemma 3n 4B', 'bot');
        }
    });
    aiModeToggle.addEventListener('change', () => {
        isAIMode = aiModeToggle.checked;
        localStorage.setItem('kasiAIMode', isAIMode.toString());
        updateModeDisplay();
        const modeMessage = isAIMode ?
            '🤖 Switched to AI Mode - Powered by Google Gemma 3n 4B' :
            '📱 Switched to App Mode - Quick responses';
        addMessage(modeMessage, 'bot');
    });
    
    // Initial state: chatbot starts minimized (class already on container)
    // No need for isMinimized flag here, controlled by classList

    // Function to set chatbot state
    function setChatbotState(minimized) {
        if (minimized) {
            chatbotContainer.classList.add('minimized');
        } else {
            chatbotContainer.classList.remove('minimized');
            chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll to bottom when opened
        }
    }

    // Close/minimize chat window from close (X) button
    chatbotClose.addEventListener('click', () => {
        setChatbotState(true);
    });

    // Open chat window from FAB
    chatbotFab.addEventListener('click', () => {
        setChatbotState(false); // Open the chatbot
    });

    // Allow clicking the header to minimize/maximize (excluding controls)
    document.getElementById('chatbot-header').addEventListener('click', (e) => {
        if (e.target !== chatbotClose && e.target !== quickTipsBtn && !e.target.closest('.chat-controls')) {
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
    
    // Send message on button click or form submit
    const chatbotInputForm = document.getElementById('chatbot-input');
    chatbotInputForm.addEventListener('submit', (e) => {
        e.preventDefault();
        sendMessage();
    });
    sendButton.addEventListener('click', (e) => {
        e.preventDefault();
        sendMessage();
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
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ message: message, mode: isAIMode ? 'ai' : 'rule' })
            });
            
            // Remove loading indicator
            loadingIndicator.remove();
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to get response from chatbot');
            }
            
            const data = await response.json();
            // Strip asterisks from bot responses before displaying
            let botResponse = data.response.replace(/\*+/g, '');
            addMessage(botResponse, 'bot');
        } catch (error) {
            console.error('Error:', error);
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

    // On load, set mode display
    updateModeDisplay();
}); 