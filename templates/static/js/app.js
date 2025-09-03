// SRM AI Doc Assist - Main Application JavaScript

class SRMAIApp {
    constructor() {
        this.isLoading = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadChatHistory();
        this.loadDocuments();
        this.updateCharCounter();
    }

    bindEvents() {
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            chatInput.addEventListener('input', () => {
                this.updateSendButton();
                this.updateCharCounter();
            });
        }

        const sendBtn = document.getElementById('sendBtn');
        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendMessage());
        }

        const newChatBtn = document.querySelector('.new-chat-btn');
        if (newChatBtn) {
            newChatBtn.addEventListener('click', () => this.startNewChat());
        }
        
        const mobileMenuBtn = document.getElementById('mobileMenuBtn');
        if (mobileMenuBtn) {
            mobileMenuBtn.addEventListener('click', () => this.toggleSidebar());
        }

        const suggestedPrompt = document.querySelector('.suggested-prompt');
        if (suggestedPrompt) {
            suggestedPrompt.addEventListener('click', () => {
                const promptText = suggestedPrompt.innerText.replace(/"/g, '');
                chatInput.value = promptText;
                chatInput.focus();
                this.updateSendButton();
                this.updateCharCounter();
            });
        }
    }

    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        sidebar.classList.toggle('active');
    }

    async sendMessage() {
        const chatInput = document.getElementById('chatInput');
        const message = chatInput.value.trim();
        
        if (!message || this.isLoading) return;

        this.removeWelcomeMessage();
        this.addMessageToChat('user', message);
        
        chatInput.value = '';
        this.updateSendButton();
        this.updateCharCounter();

        this.showLoading(true);

        try {
            const response = await this.sendToAPI(message);
            this.addMessageToChat('ai', response.answer, response.sources);
            this.saveToChatHistory(message, response);
        } catch (error) {
            console.error('Error:', error);
            this.addMessageToChat('ai', 'Sorry, an error occurred. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }

    removeWelcomeMessage() {
        const welcomeContainer = document.getElementById('welcomeContainer');
        if (welcomeContainer) {
            welcomeContainer.remove();
        }
    }

    addMessageToChat(sender, content, sources = []) {
        this.removeWelcomeMessage();
        const contentArea = document.getElementById('contentArea');
        
        // This is a simplified message display. You can enhance this with avatars, etc.
        const messageWrapper = document.createElement('div');
        messageWrapper.className = `chat-message-wrapper ${sender}-message`;
        
        let html = `<div class="message-content">${content}</div>`;
        if (sources && sources.length > 0) {
            html += '<div class="message-sources"><strong>Sources:</strong><ul>';
            sources.forEach(source => {
                html += `<li>${source}</li>`;
            });
            html += '</ul></div>';
        }
        
        messageWrapper.innerHTML = html;
        contentArea.appendChild(messageWrapper);
        contentArea.scrollTop = contentArea.scrollHeight;
    }

    showLoading(isLoading) {
        this.isLoading = isLoading;
        // You can implement a loading indicator if you wish
        const sendBtn = document.getElementById('sendBtn');
        sendBtn.disabled = isLoading;
    }
    
    updateSendButton() {
        const chatInput = document.getElementById('chatInput');
        const sendBtn = document.getElementById('sendBtn');
        sendBtn.disabled = chatInput.value.trim().length === 0;
    }

    updateCharCounter() {
        const chatInput = document.getElementById('chatInput');
        const charCounter = document.getElementById('charCounter');
        const maxLength = 1000;
        charCounter.textContent = `${chatInput.value.length}/${maxLength}`;
    }

    async loadDocuments() {
        // This is a placeholder. In a real app, you'd fetch this from an endpoint.
        const docs = ["SRM Installation and Configuration...", "SRM Upgrade Guide.pdf"];
        const docList = document.getElementById('docList');
        const docCount = document.getElementById('docCount');

        docList.innerHTML = '';
        docs.forEach(docName => {
            const docItem = document.createElement('div');
            docItem.className = 'doc-item';
            docItem.innerHTML = `<i class="fas fa-file-pdf"></i><span>${docName}</span>`;
            docList.appendChild(docItem);
        });
        docCount.textContent = docs.length;
    }

    startNewChat() {
        // Implement new chat logic
    }

    loadChatHistory() {
        // Implement loading chat history
    }

    saveToChatHistory(userMessage, aiResponse) {
        // Implement saving chat history
    }
}

document.addEventListener('DOMContentLoaded', () => new SRMAIApp());

