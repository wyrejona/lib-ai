// Chat page JavaScript

// Initialize with current time
document.addEventListener('DOMContentLoaded', function() {
    // Initialize current time
    document.getElementById('currentTime').textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    // Auto-resize textarea
    const inputField = document.getElementById('userInput');
    if (inputField) {
        inputField.addEventListener('input', function() {
            autoResize(this);
        });
        
        // Handle textarea enter key
        inputField.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Focus input field
        inputField.focus();
    }
    
    // Scroll to bottom functionality
    const chatMessages = document.getElementById('chatMessages');
    const scrollToBottomBtn = document.getElementById('scrollToBottom');
    
    if (chatMessages && scrollToBottomBtn) {
        // Monitor scroll position
        chatMessages.addEventListener('scroll', checkScrollPosition);
        
        // Initialize
        setTimeout(() => {
            scrollToBottom();
            checkScrollPosition();
        }, 100);
        
        // Scroll to bottom on button click
        scrollToBottomBtn.addEventListener('click', scrollToBottom);
    }
    
    // Fetch AI Engine status
    fetchAIEngineStatus();
    
    // Refresh status every 30 seconds
    setInterval(fetchAIEngineStatus, 30000);
});

// Auto-resize textarea
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

// Scroll to bottom
function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }
}

// Check scroll position
function checkScrollPosition() {
    const chatMessages = document.getElementById('chatMessages');
    const scrollToBottomBtn = document.getElementById('scrollToBottom');
    
    if (!chatMessages || !scrollToBottomBtn) return;
    
    const scrollHeight = chatMessages.scrollHeight;
    const scrollTop = chatMessages.scrollTop;
    const clientHeight = chatMessages.clientHeight;
    
    // Show scroll-to-bottom button if not at bottom
    if (scrollHeight - scrollTop - clientHeight > 100) {
        scrollToBottomBtn.classList.add('visible');
    } else {
        scrollToBottomBtn.classList.remove('visible');
    }
}

// Send message
async function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message
    addMessage(message, 'user');
    input.value = '';
    autoResize(input);
    
    try {
        // Show typing indicator
        const typingIndicator = addTypingIndicator();
        
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        });
        
        // Remove typing indicator
        if (typingIndicator) {
            typingIndicator.remove();
        }
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Add bot response
        if (data.response) {
            addMessage(data.response, 'bot');
        } else if (data.error) {
            addMessage(`Error: ${data.error}`, 'bot');
        } else {
            addMessage('Sorry, I could not generate a response.', 'bot');
        }
        
        // Scroll to bottom after adding message
        setTimeout(scrollToBottom, 100);
        
    } catch (error) {
        // Remove typing indicator if it exists
        document.querySelectorAll('.typing-indicator').forEach(el => el.remove());
        
        addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        console.error('Chat error:', error);
        showNotification('Error sending message. Please try again.', 'error');
    }
}

// Add message to chat
function addMessage(text, type) {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    messageDiv.className = `message ${type}-message`;
    messageDiv.innerHTML = `
        <div class="message-header">
            <i class="fas fa-${type === 'user' ? 'user' : 'robot'}"></i>
            ${type === 'user' ? 'You' : 'Library AI'}
            <span class="message-time">${time}</span>
        </div>
        <div class="message-content">${escapeHtml(text)}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    checkScrollPosition();
}

// Add typing indicator
function addTypingIndicator() {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return null;
    
    const typingDiv = document.createElement('div');
    
    typingDiv.className = 'typing-indicator';
    typingDiv.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;
    
    messagesContainer.appendChild(typingDiv);
    scrollToBottom();
    
    return typingDiv;
}

// Clear chat
async function clearChat() {
    const confirmed = await confirmDialog('Are you sure you want to clear the chat history?');
    if (!confirmed) return;
    
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;
    
    messagesContainer.innerHTML = `
        <div class="message bot-message">
            <div class="message-header">
                <i class="fas fa-robot"></i> Library AI
                <span class="message-time" id="currentTime">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
            </div>
            <div class="message-content">
                Chat cleared. How can I help you today?
            </div>
        </div>
    `;
    
    scrollToBottom();
    showNotification('Chat cleared successfully', 'success');
}

// Fetch AI Engine status
async function fetchAIEngineStatus() {
    try {
        const response = await fetch('/api/engine-status');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        
        // Update status values
        const updateElement = (id, value) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value || 'Not Available';
        };
        
        updateElement('currentChatModel', data.chatModel);
        updateElement('currentEmbeddingModel', data.embeddingModel);
        updateElement('vectorStoreStatus', data.vectorStore);
        updateElement('ollamaStatus', data.ollamaStatus);
        
        // Color code the status
        colorCodeStatus('vectorStoreStatus', data.vectorStore);
        colorCodeStatus('ollamaStatus', data.ollamaStatus);
        
    } catch (error) {
        console.error('Failed to fetch AI engine status:', error);
        
        const updateElement = (id, value) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        };
        
        updateElement('currentChatModel', 'Error');
        updateElement('currentEmbeddingModel', 'Error');
        updateElement('vectorStoreStatus', 'Connection Failed');
        updateElement('ollamaStatus', 'Connection Failed');
        
        // Set error colors
        const elements = ['vectorStoreStatus', 'ollamaStatus'];
        elements.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.style.color = 'var(--danger)';
        });
    }
}

// Color code status values
function colorCodeStatus(elementId, status) {
    const element = document.getElementById(elementId);
    if (!element || !status) return;
    
    const statusLower = status.toLowerCase();
    if (statusLower.includes('ready') || statusLower.includes('active') || statusLower.includes('connected')) {
        element.style.color = 'var(--success)';
    } else if (statusLower.includes('error') || statusLower.includes('failed') || statusLower.includes('disconnected')) {
        element.style.color = 'var(--danger)';
    } else if (statusLower.includes('loading') || statusLower.includes('checking')) {
        element.style.color = 'var(--warning)';
    } else {
        element.style.color = 'var(--secondary)';
    }
}

// Helper: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Helper: Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) notification.remove();
    }, 5000);
}

// Helper: Confirm dialog
async function confirmDialog(message) {
    return new Promise((resolve) => {
        const dialog = document.createElement('div');
        dialog.className = 'confirm-dialog-overlay';
        dialog.innerHTML = `
            <div class="confirm-dialog">
                <div class="confirm-dialog-content">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h4>Confirm Action</h4>
                    <p>${message}</p>
                </div>
                <div class="confirm-dialog-actions">
                    <button class="btn btn-secondary" onclick="this.closest('.confirm-dialog-overlay').remove(); resolve(false)">
                        Cancel
                    </button>
                    <button class="btn btn-danger" onclick="this.closest('.confirm-dialog-overlay').remove(); resolve(true)">
                        Confirm
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(dialog);
    });
}

// Export functions for global access
window.chatFunctions = {
    sendMessage,
    clearChat,
    scrollToBottom,
    fetchAIEngineStatus
};

// Add notification styles if not present
if (!document.getElementById('notification-styles')) {
    const styles = document.createElement('style');
    styles.id = 'notification-styles';
    styles.textContent = `
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            display: flex;
            align-items: center;
            justify-content: space-between;
            min-width: 300px;
            max-width: 400px;
            z-index: 1000;
            animation: slideIn 0.3s ease;
            border-left: 4px solid #4f46e5;
        }
        
        .notification-success {
            border-left-color: #10b981;
        }
        
        .notification-error {
            border-left-color: #ef4444;
        }
        
        .notification-warning {
            border-left-color: #f59e0b;
        }
        
        .notification-content {
            display: flex;
            align-items: center;
            gap: 12px;
            flex: 1;
        }
        
        .notification-content i {
            font-size: 20px;
        }
        
        .notification-success .notification-content i {
            color: #10b981;
        }
        
        .notification-error .notification-content i {
            color: #ef4444;
        }
        
        .notification-warning .notification-content i {
            color: #f59e0b;
        }
        
        .notification-content span {
            color: #1f2937;
            font-size: 14px;
            line-height: 1.4;
        }
        
        .notification-close {
            background: none;
            border: none;
            color: #9ca3af;
            cursor: pointer;
            padding: 4px;
            margin-left: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .notification-close:hover {
            color: #6b7280;
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        .confirm-dialog-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        
        .confirm-dialog {
            background: white;
            border-radius: 8px;
            padding: 24px;
            max-width: 400px;
            width: 90%;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        }
        
        .confirm-dialog-content {
            text-align: center;
            margin-bottom: 20px;
        }
        
        .confirm-dialog-content i {
            font-size: 48px;
            color: #f59e0b;
            margin-bottom: 16px;
        }
        
        .confirm-dialog-content h4 {
            margin: 0 0 8px 0;
            color: #1f2937;
        }
        
        .confirm-dialog-content p {
            margin: 0;
            color: #6b7280;
        }
        
        .confirm-dialog-actions {
            display: flex;
            gap: 12px;
            justify-content: center;
        }
    `;
    document.head.appendChild(styles);
}
