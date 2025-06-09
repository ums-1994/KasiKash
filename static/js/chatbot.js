document.addEventListener('DOMContentLoaded', () => {
    const chatbotContainer = document.getElementById('chatbot-container');
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatMessages = document.getElementById('chatbot-messages');
    const userInput = document.getElementById('user-message');
    const sendButton = document.getElementById('send-message');
    const quickTipsBtn = document.getElementById('quick-tips');
    const quickTipsMenu = document.getElementById('quick-tips-menu');
    
    let isMinimized = false;
    let isProcessing = false;
    
    // Toggle chat window
    chatbotToggle.addEventListener('click', () => {
        isMinimized = !isMinimized;
        chatbotToggle.textContent = isMinimized ? '+' : '−';
        chatbotContainer.classList.toggle('minimized');
        chatMessages.style.display = isMinimized ? 'none' : 'block';
        document.getElementById('chatbot-input').style.display = isMinimized ? 'none' : 'flex';
    });

    // Allow clicking the header to minimize/maximize
    document.getElementById('chatbot-header').addEventListener('click', (e) => {
        if (e.target !== chatbotToggle && e.target !== quickTipsBtn) {
            chatbotToggle.click();
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
                body: JSON.stringify({ message: message })
            });
            
            // Remove loading indicator
            loadingIndicator.remove();
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to get response from chatbot');
            }
            
            const data = await response.json();
            addMessage(data.response, 'bot');
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
        history.forEach(msg => {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message', `${msg.type}-message`);
            messageDiv.innerHTML = msg.html || msg.text;
            chatMessages.appendChild(messageDiv);
        });
    }
    
    // Load history on startup
    loadChatHistory();
    
    // Add welcome message when page loads
    window.addEventListener('load', () => {
        addMessage('Hello! I\'m KasiKash Assistant. How can I help you today?', 'bot');
    });
}); 