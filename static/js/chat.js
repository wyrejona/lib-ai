// ===== CHAT FUNCTIONALITY =====
class ChatManager {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.userInput = document.getElementById('userInput');
        this.scrollToBottomBtn = document.getElementById('scrollToBottom');
        this.typingIndicator = null;
        
        this.initialize();
    }
    
    initialize() {
        // Set initial time
        document.getElementById('currentTime').textContent = this.getCurrentTime();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Focus on input
        this.userInput.focus();
        
        // Scroll to bottom initially
        setTimeout(() => this.scrollToBottom(), 100);
    }
    
    setupEventListeners() {
        // Textarea auto-resize
        this.userInput.addEventListener('input', () => this.autoResize(this.userInput));
        
        // Enter key to send (Shift+Enter for new line)
        this.userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Monitor scroll position
        this.chatMessages.addEventListener('scroll', () => this.checkScrollPosition());
        
        // Scroll to bottom button
        this.scrollToBottomBtn.addEventListener('click', () => this.scrollToBottom());
        
        // Clear chat button
        document.querySelector('.btn[onclick="clearChat()"]').addEventListener('click', () => this.clearChat());
    }
    
    // ===== MESSAGE HANDLING =====
    async sendMessage() {
        const message = this.userInput.value.trim();
        
        if (!message) return;
        
        // Add user message
        this.addMessage(message, 'user');
        this.userInput.value = '';
        this.autoResize(this.userInput);
        
        try {
            // Show typing indicator
            this.showTypingIndicator();
            
            // Send to server
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            });
            
            // Remove typing indicator
            this.hideTypingIndicator();
            
            const data = await response.json();
            
            // Add bot response
            this.addMessage(data.response, 'bot');
            
            // Scroll to bottom after adding message
            setTimeout(() => this.scrollToBottom(), 100);
            
        } catch (error) {
            this.hideTypingIndicator();
            this.addMessage('Sorry, I encountered an error. Please try again.', 'bot');
            console.error('Chat error:', error);
            this.showNotification('Error sending message', 'error');
        }
    }
    
    addMessage(text, type) {
        const messageDiv = document.createElement('div');
        const time = this.getCurrentTime();
        
        messageDiv.className = `message ${type}-message`;
        messageDiv.innerHTML = `
            <div class="message-header">
                <i class="fas fa-${type === 'user' ? 'user' : 'robot'}"></i>
                ${type === 'user' ? 'You' : 'Library AI'}
                <span class="message-time">${time}</span>
            </div>
            <div class="message-content">${this.escapeHtml(text)}</div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.checkScrollPosition();
    }
    
    // ===== TYPING INDICATOR =====
    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        
        this.chatMessages.appendChild(typingDiv);
        this.typingIndicator = typingDiv;
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.remove();
            this.typingIndicator = null;
        }
    }
    
    // ===== CHAT MANAGEMENT =====
    clearChat() {
        if (confirm('Are you sure you want to clear the chat history?')) {
            this.chatMessages.innerHTML = `
                <div class="message bot-message">
                    <div class="message-header">
                        <i class="fas fa-robot"></i> Library AI
                        <span class="message-time" id="currentTime">${this.getCurrentTime()}</span>
                    </div>
                    <div class="message-content">
                        Chat cleared. How can I help you today?
                    </div>
                </div>
            `;
            this.scrollToBottom();
            this.showNotification('Chat cleared', 'success');
        }
    }
    
    // ===== SCROLLING =====
    scrollToBottom() {
        this.chatMessages.scrollTo({
            top: this.chatMessages.scrollHeight,
            behavior: 'smooth'
        });
        
        // Hide scroll button after scrolling
        setTimeout(() => this.checkScrollPosition(), 300);
    }
    
    checkScrollPosition() {
        const scrollHeight = this.chatMessages.scrollHeight;
        const scrollTop = this.chatMessages.scrollTop;
        const clientHeight = this.chatMessages.clientHeight;
        
        // Show scroll-to-bottom button if not at bottom
        if (scrollHeight - scrollTop - clientHeight > 100) {
            this.scrollToBottomBtn.classList.add('visible');
        } else {
            this.scrollToBottomBtn.classList.remove('visible');
        }
    }
    
    // ===== UTILITIES =====
    autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
    
    getCurrentTime() {
        return new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showNotification(message, type = 'success') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            ${message}
        `;
        
        // Style notification
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#34a853' : '#d93025'};
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 10px;
            animation: slideIn 0.3s ease;
        `;
        
        // Add animation
        if (!document.querySelector('#notification-animation')) {
            const style = document.createElement('style');
            style.id = 'notification-animation';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
        
        // Add to document
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// ===== INITIALIZE CHAT =====
document.addEventListener('DOMContentLoaded', () => {
    window.chatManager = new ChatManager();
});