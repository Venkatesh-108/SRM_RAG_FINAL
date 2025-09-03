// SRM AI Doc Assist - Main Application JavaScript

class SRMAIApp {
    constructor() {
        this.isLoading = false;
        this.currentSessionId = null;
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

        const clearChatsBtn = document.querySelector('.clear-chats-btn');
        if (clearChatsBtn) {
            clearChatsBtn.addEventListener('click', () => this.clearAllChats());
        }
    }

    async startNewChat() {
        try {
            const response = await fetch('/chat/create_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title: 'New Chat',
                    initial_message: null
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.currentSessionId = data.session.session_id;
                this.removeWelcomeMessage();
                this.showChatArea();
                this.loadChatHistory();
                console.log('New chat session created:', this.currentSessionId);
            } else {
                console.error('Failed to create new chat session');
            }
        } catch (error) {
            console.error('Error creating new chat session:', error);
        }
    }

    async sendMessage() {
        const chatInput = document.getElementById('chatInput');
        const message = chatInput.value.trim();
        
        if (!message || this.isLoading) return;
        
        if (!this.currentSessionId) {
            // Create new session if none exists
            await this.startNewChat();
        }

        // Add user message to UI
        this.addMessageToChat('user', message);
        chatInput.value = '';
        this.updateCharCounter();
        this.updateSendButton();

        // Show loading state
        this.setLoadingState(true);

        try {
            const response = await fetch('/chat/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.currentSessionId,
                    content: message
                })
            });

            if (response.ok) {
                const data = await response.json();
                
                // Add AI response to UI
                this.addMessageToChat('assistant', data.message.content, data.sources);
                
                // Update chat history
                this.loadChatHistory();
            } else {
                const errorData = await response.json();
                this.addMessageToChat('assistant', `Error: ${errorData.detail}`, []);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessageToChat('assistant', 'Sorry, I encountered an error. Please try again.', []);
        } finally {
            this.setLoadingState(false);
        }
    }

    addMessageToChat(role, content, sources = []) {
        const chatArea = document.getElementById('chatArea');
        if (!chatArea) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}-message`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = role === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = `<p>${this.escapeHtml(content)}</p>`;
        
        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'message-sources';
            sourcesDiv.innerHTML = '<strong>Sources:</strong><br>' + 
                sources.map(source => 
                    `<span class="source-item">${source.filename} (Page ${source.page_number || 'N/A'})</span>`
                ).join('<br>');
            contentDiv.appendChild(sourcesDiv);
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        chatArea.appendChild(messageDiv);
        
        // Scroll to bottom
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async loadChatHistory() {
        try {
            const response = await fetch('/chat/sessions');
            if (response.ok) {
                const data = await response.json();
                this.updateChatList(data.sessions);
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
        }
    }

    updateChatList(sessions) {
        const chatList = document.getElementById('chatList');
        if (!chatList) return;

        chatList.innerHTML = '';
        
        if (sessions.length === 0) {
            chatList.innerHTML = '<div class="no-chats">No chats yet</div>';
            return;
        }

        sessions.forEach(session => {
            const chatItem = document.createElement('div');
            chatItem.className = 'chat-item';
            chatItem.onclick = () => this.loadChatSession(session.session_id);
            
            const icon = document.createElement('i');
            icon.className = 'far fa-comment-dots';
            
            const title = document.createElement('span');
            title.textContent = session.title || 'Untitled Chat';
            
            chatItem.appendChild(icon);
            chatItem.appendChild(title);
            chatList.appendChild(chatItem);
        });
    }

    async loadChatSession(sessionId) {
        try {
            const response = await fetch(`/chat/session/${sessionId}`);
            if (response.ok) {
                const session = await response.json();
                this.currentSessionId = sessionId;
                this.loadChatSessionToUI(session);
            }
        } catch (error) {
            console.error('Error loading chat session:', error);
        }
    }

    loadChatSessionToUI(session) {
        this.removeWelcomeMessage();
        this.showChatArea();
        
        const chatArea = document.getElementById('chatArea');
        if (!chatArea) return;

        session.messages.forEach(msg => {
            this.addMessageToChat(msg.role, msg.content, msg.sources);
        });
    }

    async clearAllChats() {
        if (!confirm('Are you sure you want to clear all chat sessions? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch('/chat/sessions/clear', {
                method: 'DELETE'
            });

            if (response.ok) {
                this.currentSessionId = null;
                this.clearChatArea();
                this.loadChatHistory();
                this.showWelcomeMessage();
            } else {
                console.error('Failed to clear all chats');
            }
        } catch (error) {
            console.error('Error clearing all chats:', error);
        }
    }

    clearChatArea() {
        const chatArea = document.getElementById('chatArea');
        if (chatArea) {
            chatArea.innerHTML = '';
        }
    }

    showChatArea() {
        const chatArea = document.getElementById('chatArea');
        const welcomeContainer = document.getElementById('welcomeContainer');
        
        if (chatArea) {
            chatArea.style.display = 'flex';
        }
        
        if (welcomeContainer) {
            welcomeContainer.style.display = 'none';
        }
    }

    showWelcomeMessage() {
        const contentArea = document.getElementById('contentArea');
        const chatArea = document.getElementById('chatArea');
        
        if (contentArea) {
            const welcomeContainer = document.createElement('div');
            welcomeContainer.className = 'welcome-container';
            welcomeContainer.id = 'welcomeContainer';
            welcomeContainer.innerHTML = `
                <div class="welcome-message">
                    <div class="welcome-icon">
                        <i class="fas fa-brain"></i>
                    </div>
                    <h2>Welcome to AI Doc Assist!</h2>
                    <p>Your intelligent companion for document analysis, insights extraction, and knowledge discovery.</p>
                </div>
            `;
            contentArea.appendChild(welcomeContainer);
        }
        
        if (chatArea) {
            chatArea.style.display = 'none';
        }
    }

    removeWelcomeMessage() {
        const welcomeContainer = document.getElementById('welcomeContainer');
        if (welcomeContainer) {
            welcomeContainer.remove();
        }
    }

    setLoadingState(loading) {
        this.isLoading = loading;
        const sendBtn = document.getElementById('sendBtn');
        if (sendBtn) {
            sendBtn.disabled = loading;
            sendBtn.innerHTML = loading ? '<i class="fas fa-spinner fa-spin"></i>' : '<i class="fas fa-paper-plane"></i>';
        }
    }

    updateCharCounter() {
        const chatInput = document.getElementById('chatInput');
        const charCounter = document.getElementById('charCounter');
        if (chatInput && charCounter) {
            const maxLength = 1000;
            charCounter.textContent = `${chatInput.value.length}/${maxLength}`;
        }
    }

    updateSendButton() {
        const chatInput = document.getElementById('chatInput');
        const sendBtn = document.getElementById('sendBtn');
        if (chatInput && sendBtn) {
            sendBtn.disabled = chatInput.value.trim().length === 0;
        }
    }

    async loadDocuments() {
        // This is a placeholder. In a real app, you'd fetch this from an endpoint.
        const docs = ["SRM Installation and Configuration...", "SRM Upgrade Guide.pdf"];
        const docList = document.getElementById('docList');
        const docCount = document.getElementById('docCount');

        if (docList && docCount) {
            docList.innerHTML = '';
            docs.forEach(docName => {
                const docItem = document.createElement('div');
                docItem.className = 'doc-item';
                docItem.innerHTML = `<i class="fas fa-file-pdf"></i><span>${docName}</span>`;
                docList.appendChild(docItem);
            });
            docCount.textContent = docs.length;
        }
    }

    toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.classList.toggle('open');
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => new SRMAIApp());

