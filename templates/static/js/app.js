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
                    title: null, // Let the backend handle the title
                    initial_message: null
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.currentSessionId = data.session.session_id;
                this.removeWelcomeMessage();
                this.clearChatArea(); // Clear previous messages
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
        // Show "Thinking..." message
        this.addMessageToChat('assistant', 'Thinking...', [], true);

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
                
                // Add AI response to UI with streaming effect
                this.streamResponse(data.message.content, data.sources);

            } else {
                const errorData = await response.json();
                this.streamResponse(`Error: ${errorData.detail}`, []);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.streamResponse('Sorry, I encountered an error. Please try again.', []);
        } finally {
            this.setLoadingState(false);
            // Update chat history after response is complete
            this.loadChatHistory();
        }
    }

    addMessageToChat(role, content, sources = [], isThinking = false) {
        const chatArea = document.getElementById('chatArea');
        if (!chatArea) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}-message`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = role === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (isThinking) {
            contentDiv.innerHTML = `<p>${this.escapeHtml(content)}</p>`;
        } else {
            contentDiv.innerHTML = `<p>${this.escapeHtml(content)}</p>`;
        }
        
        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'message-sources';
            sourcesDiv.innerHTML = '<strong>Sources:</strong><br>' + 
                sources.map(source => {
                    const pageNumber = source.page_number || 'N/A';
                    const fileName = this.escapeHtml(source.filename);
                    if (pageNumber !== 'N/A') {
                        return `<a href="/documents/${encodeURIComponent(fileName)}#page=${pageNumber}" target="_blank" class="source-item">${fileName} (Page ${pageNumber})</a>`;
                    } else {
                        return `<a href="/documents/${encodeURIComponent(fileName)}" target="_blank" class="source-item">${fileName}</a>`;
                    }
                }).join('<br>');
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
            chatItem.dataset.sessionId = session.session_id; // Use data attribute
            chatItem.onclick = () => this.loadChatSession(session.session_id);
            
            const icon = document.createElement('i');
            icon.className = 'far fa-comment-dots';
            
            const title = document.createElement('span');
            title.textContent = session.title || 'Untitled Chat';
            
            chatItem.appendChild(icon);
            chatItem.appendChild(title);
            chatList.appendChild(chatItem);
        });

        this.updateActiveChatItem();
    }

    updateActiveChatItem() {
        const chatItems = document.querySelectorAll('.chat-item');
        chatItems.forEach(item => {
            if (item.dataset.sessionId === this.currentSessionId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    async loadChatSession(sessionId) {
        try {
            const response = await fetch(`/chat/session/${sessionId}`);
            if (response.ok) {
                const session = await response.json();
                this.currentSessionId = sessionId;
                this.loadChatSessionToUI(session);
                this.updateActiveChatItem(); // Highlight the new active chat
            }
        } catch (error) {
            console.error('Error loading chat session:', error);
        }
    }

    loadChatSessionToUI(session) {
        this.removeWelcomeMessage();
        this.clearChatArea(); // Clear previous messages first
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
        // First, check if a welcome container already exists to prevent duplicates.
        if (document.getElementById('welcomeContainer')) {
            // If it exists, ensure it's visible and the chat area is hidden.
            document.getElementById('welcomeContainer').style.display = 'block';
            const chatArea = document.getElementById('chatArea');
            if (chatArea) {
                chatArea.style.display = 'none';
            }
            return; // Exit the function to prevent creating another one.
        }

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
        const docList = document.getElementById('docList');
        const docCount = document.getElementById('docCount');

        if (!docList || !docCount) return;

        try {
            const response = await fetch('/documents');
            if (!response.ok) {
                throw new Error('Failed to fetch documents');
            }
            const docs = await response.json();

            docList.innerHTML = '';
            docs.forEach(docName => {
                const docItem = document.createElement('a');
                docItem.className = 'doc-item';
                docItem.href = `/documents/${docName}`;
                docItem.target = '_blank'; // Open in new tab
                docItem.title = `Open ${docName}`;

                let iconClass = 'fas fa-file-alt'; // Default icon
                if (docName.endsWith('.pdf')) {
                    iconClass = 'fas fa-file-pdf';
                } else if (docName.endsWith('.md')) {
                    iconClass = 'fas fa-file-markdown';
                }

                docItem.innerHTML = `<i class="${iconClass}"></i><span>${docName}</span>`;
                docList.appendChild(docItem);
            });
            docCount.textContent = docs.length;
        } catch (error) {
            console.error('Error loading documents:', error);
            docList.innerHTML = '<div class="error-message">Could not load documents.</div>';
            docCount.textContent = '0';
        }
    }

    toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.classList.toggle('open');
        }
    }

    streamResponse(text, sources) {
        // Find the last assistant message (which should be the "Thinking..." message)
        const assistantMessages = document.querySelectorAll('.chat-message.assistant-message');
        const thinkingMessage = assistantMessages[assistantMessages.length - 1];
        if (!thinkingMessage) return;

        const contentDiv = thinkingMessage.querySelector('.message-content');
        contentDiv.innerHTML = '<p></p>'; // Clear the thinking message
        const p = contentDiv.querySelector('p');
        
        let i = 0;
        const speed = 20; // milliseconds per character

        function typeWriter() {
            if (i < text.length) {
                p.innerHTML += text.charAt(i);
                i++;
                setTimeout(typeWriter, speed);
            } else {
                // After typing is done, add sources
                if (sources && sources.length > 0) {
                    const sourcesDiv = document.createElement('div');
                    sourcesDiv.className = 'message-sources';
                    sourcesDiv.innerHTML = '<strong>Sources:</strong><br>' + 
                        sources.map(source => {
                            const pageNumber = source.page_number || 'N/A';
                            const fileName = this.escapeHtml(source.filename);
                            if (pageNumber !== 'N/A') {
                                return `<a href="/documents/${encodeURIComponent(fileName)}#page=${pageNumber}" target="_blank" class="source-item">${fileName} (Page ${pageNumber})</a>`;
                            } else {
                                return `<a href="/documents/${encodeURIComponent(fileName)}" target="_blank" class="source-item">${fileName}</a>`;
                            }
                        }).join('<br>');
                    contentDiv.appendChild(sourcesDiv);
                }

                // Add action buttons after typing is done
                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'message-actions';
                actionsDiv.innerHTML = `
                    <button class="action-btn copy-btn" title="Copy"><i class="fas fa-copy"></i></button>
                    <button class="action-btn redo-btn" title="Regenerate response"><i class="fas fa-redo"></i></button>
                `;
                thinkingMessage.appendChild(actionsDiv);

                // Add event listeners for new buttons
                actionsDiv.querySelector('.copy-btn').addEventListener('click', () => {
                    navigator.clipboard.writeText(text).then(() => {
                        const copyBtn = actionsDiv.querySelector('.copy-btn');
                        copyBtn.innerHTML = '<i class="fas fa-check"></i>';
                        setTimeout(() => {
                            copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
                        }, 2000);
                    });
                });

                actionsDiv.querySelector('.redo-btn').addEventListener('click', async () => {
                    const allUserMessages = Array.from(document.querySelectorAll('.chat-message.user-message .message-content p'));
                    if (allUserMessages.length === 0) return;
                    const lastQuery = allUserMessages[allUserMessages.length - 1].textContent;
                
                    thinkingMessage.remove();
                
                    this.setLoadingState(true);
                    this.addMessageToChat('assistant', 'Thinking...', [], true);

                    try {
                        const response = await fetch('/chat/send_message', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                session_id: this.currentSessionId,
                                content: lastQuery,
                            }),
                        });

                        if (response.ok) {
                            const data = await response.json();
                            this.streamResponse(data.message.content, data.sources);
                        } else {
                            const errorData = await response.json();
                            this.streamResponse(`Error: ${errorData.detail}`, []);
                        }
                    } catch (error) {
                        console.error('Error sending message:', error);
                        this.streamResponse('Sorry, I encountered an error. Please try again.', []);
                    } finally {
                        this.setLoadingState(false);
                        this.loadChatHistory();
                    }
                });
            }
        }
        typeWriter();
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => new SRMAIApp());

