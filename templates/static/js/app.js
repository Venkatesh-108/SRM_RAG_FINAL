// AI Doc Assist - Main Application JavaScript

class SRMAIApp {
    constructor() {
        this.isLoading = false;
        this.currentSessionId = null;
        this.currentAutocompleteIndex = -1;
        this.isStreaming = false;
        this.streamingTimeoutId = null;
        this.currentAbortController = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadChatHistory();
        this.loadDocuments();
        this.initializeDocumentsSection();
        this.updateCharCounter();
        this.showWelcomeMessage(); // Show welcome message on app start
    }

    bindEvents() {
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (this.handleAutocompleteNavigation(e)) {
                        return;
                    }
                    this.sendMessage();
                } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                    if (this.handleAutocompleteNavigation(e)) {
                        e.preventDefault();
                    }
                } else if (e.key === 'Escape') {
                    this.hideAutocomplete();
                }
            });
            chatInput.addEventListener('input', () => {
                this.updateSendButton();
                this.updateCharCounter();
                this.handleAutocomplete();
            });
        }

        const sendBtn = document.getElementById('sendBtn');
        if (sendBtn) {
            sendBtn.addEventListener('click', () => {
                if (this.isStreaming) {
                    this.stopStreaming();
                } else {
                    this.sendMessage();
                }
            });
        }

        const newChatBtn = document.querySelector('.new-chat-btn');
        if (newChatBtn) {
            newChatBtn.addEventListener('click', () => this.startNewChat());
        }

        const mobileMenuBtn = document.getElementById('mobileMenuBtn');
        if (mobileMenuBtn) {
            mobileMenuBtn.addEventListener('click', () => this.toggleSidebar());
        }

        const hamburgerBtn = document.getElementById('hamburgerBtn');
        if (hamburgerBtn) {
            hamburgerBtn.addEventListener('click', () => this.toggleSidebar());
        }

        // Mobile backdrop click to close sidebar
        const mobileBackdrop = document.getElementById('mobileBackdrop');
        if (mobileBackdrop) {
            mobileBackdrop.addEventListener('click', () => {
                this.toggleSidebar(); // Close sidebar when backdrop is clicked
            });
        }

        // Collapsed icon buttons expand sidebar
        document.querySelectorAll('.collapsed-icon-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const sidebar = document.querySelector('.sidebar');
                if (sidebar && sidebar.classList.contains('collapsed')) {
                    sidebar.classList.remove('collapsed');
                }
            });
        });

        // Window resize handler for desktop/mobile transitions
        window.addEventListener('resize', () => {
            const sidebar = document.querySelector('.sidebar');
            const backdrop = document.getElementById('mobileBackdrop');
            const body = document.body;

            if (window.innerWidth >= 1024) {
                // Desktop mode: clean up mobile classes
                if (sidebar) {
                    sidebar.classList.remove('active');
                }
                if (backdrop) {
                    backdrop.classList.remove('active');
                }
                body.classList.remove('sidebar-open');
            } else {
                // Mobile mode: clean up desktop classes
                if (sidebar) {
                    sidebar.classList.remove('collapsed');
                }
            }
        });

        const clearChatsBtn = document.querySelector('.clear-chats-btn');
        if (clearChatsBtn) {
            clearChatsBtn.addEventListener('click', () => this.clearAllChats());
        }

        // Documents expand/collapse functionality
        const documentsHeader = document.getElementById('documentsHeader');
        if (documentsHeader) {
            documentsHeader.addEventListener('click', () => this.toggleDocumentsSection());
        }

        const uploadBtn = document.getElementById('uploadBtn');
        const pdfUploadInput = document.getElementById('pdfUploadInput');

        if (uploadBtn) {
            uploadBtn.addEventListener('click', () => pdfUploadInput.click());
        }

        if (pdfUploadInput) {
            pdfUploadInput.addEventListener('change', (event) => this.uploadFile(event.target.files[0]));
        }

        // Hide autocomplete when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.input-wrapper')) {
                this.hideAutocomplete();
            }
        });

        // Modal events
        const modal = document.getElementById('confirmationModal');
        if (modal) {
            document.getElementById('modalCancelBtn').addEventListener('click', () => this.hideModal());
            modal.addEventListener('click', (e) => {
                if (e.target.id === 'confirmationModal') {
                    this.hideModal();
                }
            });
        }
    }

    showModal(title, message, onConfirm) {
        document.getElementById('modalTitle').textContent = title;
        document.getElementById('modalMessage').textContent = message;
        
        const confirmBtn = document.getElementById('modalConfirmBtn');
        const newConfirmBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
        
        newConfirmBtn.addEventListener('click', () => {
            onConfirm();
            this.hideModal();
        });
        
        document.getElementById('confirmationModal').style.display = 'flex';
        setTimeout(() => document.getElementById('confirmationModal').classList.add('show'), 10);
    }

    hideModal() {
        const modal = document.getElementById('confirmationModal');
        modal.classList.remove('show');
        setTimeout(() => modal.style.display = 'none', 300);
    }

    async uploadFile(file) {
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        const uploadBtn = document.getElementById('uploadBtn');
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';

        try {
            const response = await fetch('/upload_pdf/', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                const result = await response.json();
                console.log(result.message);
                this.loadDocuments(); // Refresh the document list
                alert('File uploaded and indexed successfully!');
            } else {
                const error = await response.json();
                console.error('Upload failed:', error.detail);
                alert(`Upload failed: ${error.detail}`);
            }
        } catch (error) {
            console.error('An error occurred during upload:', error);
            alert('An error occurred during upload. Please try again.');
        } finally {
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = '<i class="fas fa-upload"></i> Upload PDF';
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
                this.clearChatArea(); // Clear previous messages
                this.showWelcomeMessage(); // Show welcome message instead of empty chat
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

        // Create abort controller for this request
        this.currentAbortController = new AbortController();

        try {
            const response = await fetch('/chat/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.currentSessionId,
                    content: message
                }),
                signal: this.currentAbortController.signal
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
            if (error.name === 'AbortError') {
                console.log('Request was aborted');
                this.handleStreamStop();
            } else {
                console.error('Error sending message:', error);
                this.streamResponse('Sorry, I encountered an error. Please try again.', []);
            }
        } finally {
            this.setLoadingState(false);
            this.currentAbortController = null;
            // Update chat history after response is complete
            this.loadChatHistory();
        }
    }

    addMessageToChat(role, content, sources = [], isThinking = false) {
        const chatArea = document.getElementById('chatArea');
        if (!chatArea) return;

        // Show chat area and hide welcome message when first message is added
        this.showChatArea();

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
            // Use formatted rendering for AI responses, plain text for user messages
            if (role === 'assistant') {
                contentDiv.innerHTML = this.renderFormattedText(content);
            } else {
                contentDiv.innerHTML = `<p>${this.escapeHtml(content)}</p>`;
            }
        }

        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'message-sources';
            sourcesDiv.innerHTML = '<strong>Sources:</strong><br>' +
                sources.map(source => {
                    // Handle both old string format and new object format
                    if (typeof source === 'string') {
                        return `<span class="source-item">${this.escapeHtml(source)}</span>`;
                    } else {
                        const pageNumber = source.page_number || 'N/A';
                        const fileName = this.escapeHtml(source.filename || source.text || 'Unknown');
                        if (pageNumber !== 'N/A') {
                            return `<a href="/documents/${encodeURIComponent(fileName)}#page=${pageNumber}" target="_blank" class="source-item">${fileName} (Page ${pageNumber})</a>`;
                        } else {
                            return `<a href="/documents/${encodeURIComponent(fileName)}" target="_blank" class="source-item">${fileName}</a>`;
                        }
                    }
                }).join('<br>');
            contentDiv.appendChild(sourcesDiv);
        }

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        chatArea.appendChild(messageDiv);

        // Add action buttons for assistant messages (but not thinking messages)
        if (role === 'assistant' && !isThinking) {
            this.addActionButtons(messageDiv, content);
        }

        // Enhanced auto-scroll with smooth behavior
        this.scrollToBottom();
    }

    addActionButtons(messageDiv, content) {
        // Add action buttons
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'message-actions';
        actionsDiv.innerHTML = `
            <button class="action-btn copy-btn" title="Copy"><i class="fas fa-copy"></i></button>
            <button class="action-btn redo-btn" title="Regenerate response"><i class="fas fa-redo"></i></button>
        `;
        messageDiv.appendChild(actionsDiv);

        const self = this; // Store reference to 'this'

        // Add event listeners for new buttons
        actionsDiv.querySelector('.copy-btn').addEventListener('click', () => {
            navigator.clipboard.writeText(content).then(() => {
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
        
            messageDiv.remove();
        
            self.setLoadingState(true);
            self.addMessageToChat('assistant', 'Thinking...', [], true);

            try {
                const response = await fetch('/chat/send_message', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: self.currentSessionId,
                        content: lastQuery,
                    }),
                });

                if (response.ok) {
                    const data = await response.json();
                    self.streamResponse(data.message.content, data.sources);
                } else {
                    const errorData = await response.json();
                    self.streamResponse(`Error: ${errorData.detail}`, []);
                }
            } catch (error) {
                console.error('Error sending message:', error);
                self.streamResponse('Sorry, I encountered an error. Please try again.', []);
            } finally {
                self.setLoadingState(false);
                self.loadChatHistory();
            }
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    applySyntaxHighlighting(code, language = '') {
        // Since we want all text to be black anyway, just escape HTML and return
        let highlighted = this.escapeHtml(code);

        // Split very long lines at appropriate points before highlighting
        highlighted = this.handleLongLines(highlighted);

        // No syntax highlighting - just return the properly escaped text
        return highlighted;
    }

    handleLongLines(text) {
        // Split lines that are longer than 80 characters at logical break points
        return text.split('\n').map(line => {
            if (line.length <= 80) return line;

            // For command lines, try to break at logical points
            if (line.includes('./') || line.includes(' -c ') || line.includes(' --')) {
                // Break at parameter boundaries
                return line.replace(/(\s+--?\w+)/g, '\n    $1');
            }

            // For very long paths, allow natural breaking
            return line;
        }).join('\n');
    }

    renderFormattedText(text) {
        // Convert common formatting patterns to HTML
        let formattedText = text;

        // Simplified code blocks - just escape HTML properly
        formattedText = formattedText.replace(/```[\s\S]*?```/g, (match) => {
            // Extract the code content (remove the ``` markers)
            const code = match.replace(/^```(\w+)?\n?/, '').replace(/```$/, '');

            // Properly escape HTML entities and tags
            const escapedCode = this.escapeHtml(code);

            return `<pre><code>${escapedCode}</code></pre>`;
        });

        // Handle markdown headings (# ## ### #### ##### ######)
        formattedText = formattedText.replace(/^######\s+(.+)$/gm, '<h6>$1</h6>');
        formattedText = formattedText.replace(/^#####\s+(.+)$/gm, '<h5>$1</h5>');
        formattedText = formattedText.replace(/^####\s+(.+)$/gm, '<h4>$1</h4>');
        formattedText = formattedText.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>');
        formattedText = formattedText.replace(/^##\s+(.+)$/gm, '<h2>$1</h2>');
        formattedText = formattedText.replace(/^#\s+(.+)$/gm, '<h1>$1</h1>');
        
        // Handle section headers with equals signs (====)
        formattedText = formattedText.replace(/^(.+)\n=+$/gm, '<h3>$1</h3>');
        
        // Handle section headers with dashes (----)
        formattedText = formattedText.replace(/^(.+)\n-+$/gm, '<h4>$1</h4>');
        
        // Handle section headers (lines ending with :)
        formattedText = formattedText.replace(/^([^:\n]+):$/gm, '<strong>$1:</strong>');
        
        // Handle NOTEs specifically (they are NOT list items) - remove number
        formattedText = formattedText.replace(/^(\d+\.)\s+(NOTE:.*?)$/gm, '<div class="note-item"><strong class="note-content">$2</strong></div>');

        // Handle numbered lists (1. 2. 3. etc.) - but exclude NOTEs
        formattedText = formattedText.replace(/^(\d+\.)\s+(?!NOTE:)(.+)$/gm, '<strong>$1</strong> $2');
        
        // Handle bullet points (- or •)
        formattedText = formattedText.replace(/^[-•]\s+(.+)$/gm, '• $1');
        
        // Handle emphasis (text between ** or __)
        formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        formattedText = formattedText.replace(/__(.*?)__/g, '<em>$1</em>');
        
        // Handle inline code snippets (text between `)
        formattedText = formattedText.replace(/`([^`\n]+)`/g, '<code>$1</code>');
        
        // Handle line breaks for better readability
        formattedText = formattedText.replace(/\n\n+/g, '<br><br>');
        formattedText = formattedText.replace(/\n/g, '<br>');
        
        // Remove extra br tags after headings
        formattedText = formattedText.replace(/(<\/h[1-6]>)(<br>)+/g, '$1');
        
        // Remove extra br tags before and after code blocks
        formattedText = formattedText.replace(/(<br>)+(<pre><code>)/g, '$2');
        formattedText = formattedText.replace(/(<\/code><\/pre>)(<br>)+/g, '$1');
        
        // Remove extra br tags before and after inline code
        formattedText = formattedText.replace(/(<br>)+(<code>)/g, '<br>$2');
        formattedText = formattedText.replace(/(<\/code>)(<br>)+/g, '$1<br>');
        
        // Wrap in div instead of paragraph to allow block elements
        formattedText = `<div>${formattedText}</div>`;
        
        return formattedText;
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
            
            // Create chat content wrapper for icon and title
            const chatContent = document.createElement('div');
            chatContent.className = 'chat-content';
            chatContent.onclick = () => this.loadChatSession(session.session_id);
            
            const icon = document.createElement('i');
            icon.className = 'far fa-comment-dots';
            
            const title = document.createElement('span');
            title.className = 'chat-title';
            title.textContent = session.title || 'Untitled Chat';
            
            chatContent.appendChild(icon);
            chatContent.appendChild(title);
            
            // Create delete button
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'chat-delete-btn';
            deleteBtn.title = 'Delete chat';
            deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
            deleteBtn.onclick = (e) => {
                e.stopPropagation(); // Prevent chat from being selected
                this.deleteIndividualChat(session.session_id, session.title || 'Untitled Chat');
            };
            
            chatItem.appendChild(chatContent);
            chatItem.appendChild(deleteBtn);
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
        this.clearChatArea(); // Clear previous messages first
        this.showChatArea();

        const chatArea = document.getElementById('chatArea');
        if (!chatArea) return;

        session.messages.forEach(msg => {
            this.addMessageToChat(msg.role, msg.content, msg.sources);
        });

        // Scroll to bottom after loading all messages with a small delay
        setTimeout(() => {
            this.scrollToBottom();
        }, 100);
    }

    async clearAllChats() {
        this.showModal(
            'Clear All Chats',
            'Are you sure you want to clear all chat sessions? This action cannot be undone.',
            async () => {
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
        );
    }

    async deleteIndividualChat(sessionId, chatTitle) {
        this.showModal(
            `Delete "${chatTitle}"`,
            'Are you sure you want to delete this chat? This action cannot be undone.',
            async () => {
                try {
                    const response = await fetch(`/chat/session/${sessionId}`, {
                        method: 'DELETE'
                    });
        
                    if (response.ok) {
                        if (this.currentSessionId === sessionId) {
                            this.currentSessionId = null;
                            this.clearChatArea();
                            this.showWelcomeMessage();
                        }
                        
                        this.loadChatHistory();
                        console.log(`Chat "${chatTitle}" deleted successfully`);
                    } else {
                        const errorData = await response.json();
                        console.error('Failed to delete chat:', errorData.detail);
                        alert(`Failed to delete chat: ${errorData.detail}`);
                    }
                } catch (error) {
                    console.error('Error deleting chat:', error);
                    alert('An error occurred while deleting the chat. Please try again.');
                }
            }
        );
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
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="welcome-content">
                        <h3 align="center">Welcome to AI Doc Assist</h3>

                        <div class="phi3-attribution" style="text-align: center; margin: 20px 0; padding: 10px; background: linear-gradient(135deg, #0d6efd 0%, #4a90e2 100%); color: white; border-radius: 8px; font-weight: 600;">
                            Built with Microsoft Phi-3
                        </div>

                        <div class="quick-start">
                            <p class="section-title">How to get started:</p>
                            <ul class="start-steps">
                                    <li>💬 Ask questions about your SRM documentation</li>
                                <li>Example: "How to uninstall a SolutionPack?"</li>
                               
                            </ul>
                        </div>
                    </div>
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

    stopStreaming() {
        this.isStreaming = false;
        if (this.streamingTimeoutId) {
            clearTimeout(this.streamingTimeoutId);
            this.streamingTimeoutId = null;
        }
        if (this.currentAbortController) {
            this.currentAbortController.abort();
        }
        this.updateSendButtonForStreaming();
    }

    handleStreamStop() {
        // Find the last assistant message and add a "stopped" indicator
        const assistantMessages = document.querySelectorAll('.chat-message.assistant-message');
        const lastMessage = assistantMessages[assistantMessages.length - 1];
        if (lastMessage) {
            const contentDiv = lastMessage.querySelector('.message-content');
            if (contentDiv) {
                const stoppedIndicator = document.createElement('div');
                stoppedIndicator.className = 'stream-stopped-indicator';
                stoppedIndicator.innerHTML = '<em style="color: #6c5ce7; font-size: 12px;">Response stopped by user</em>';
                contentDiv.appendChild(stoppedIndicator);
            }
        }
    }

    updateSendButtonForStreaming() {
        const sendBtn = document.getElementById('sendBtn');
        if (sendBtn) {
            if (this.isStreaming) {
                sendBtn.innerHTML = '<i class="fas fa-stop"></i>';
                sendBtn.title = 'Stop';
                sendBtn.disabled = false;
                sendBtn.classList.add('stop-mode');
            } else {
                sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
                sendBtn.title = 'Send';
                sendBtn.disabled = false;
                sendBtn.classList.remove('stop-mode');
                this.updateSendButton(); // Check if input is empty to disable if needed
            }
        }
    }

    setLoadingState(loading) {
        this.isLoading = loading;
        const sendBtn = document.getElementById('sendBtn');
        if (sendBtn && !this.isStreaming) {
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
                docItem.target = '_blank'; // Open in new window
                docItem.rel = 'noopener noreferrer'; // Security best practice
                docItem.title = `Open ${docName} in new window`;

                let iconClass = 'fas fa-file-alt'; // Default icon
                if (docName.endsWith('.pdf')) {
                    iconClass = 'fas fa-file-pdf';
                } else if (docName.endsWith('.md')) {
                    iconClass = 'fas fa-file-markdown';
                }

                docItem.innerHTML = `<i class="${iconClass}"></i><span>${docName}</span>`;
                docList.appendChild(docItem);
            });

            // Show all documents without truncation
            docList.classList.remove('auto-collapsible', 'expanded');

            docCount.textContent = docs.length;
        } catch (error) {
            console.error('Error loading documents:', error);
            docList.innerHTML = '<div class="error-message">Could not load documents.</div>';
            docCount.textContent = '0';
        }
    }

    toggleDocumentsSection() {
        const docList = document.getElementById('docList');
        const expandIcon = document.getElementById('documentsExpandIcon');

        if (!docList || !expandIcon) return;

        docList.classList.toggle('collapsed');
        expandIcon.classList.toggle('expanded');

        // Store the state in localStorage
        const isCollapsed = docList.classList.contains('collapsed');
        localStorage.setItem('documentsCollapsed', isCollapsed.toString());
    }

    // Initialize documents section state from localStorage
    initializeDocumentsSection() {
        const docList = document.getElementById('docList');
        const expandIcon = document.getElementById('documentsExpandIcon');

        if (!docList || !expandIcon) return;

        const isCollapsed = localStorage.getItem('documentsCollapsed') === 'true';
        if (isCollapsed) {
            docList.classList.add('collapsed');
            expandIcon.classList.add('expanded');
        }
    }

    toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        const backdrop = document.getElementById('mobileBackdrop');
        const body = document.body;

        if (sidebar) {
            // Check if we're in mobile view (window width < 1024px)
            const isMobile = window.innerWidth < 1024;

            if (isMobile) {
                // Mobile behavior: toggle active class and backdrop
                const isActive = sidebar.classList.contains('active');

                if (isActive) {
                    // Close sidebar
                    sidebar.classList.remove('active');
                    if (backdrop) backdrop.classList.remove('active');
                    body.classList.remove('sidebar-open');
                } else {
                    // Open sidebar
                    sidebar.classList.add('active');
                    if (backdrop) backdrop.classList.add('active');
                    body.classList.add('sidebar-open');
                }
            } else {
                // Desktop behavior: toggle collapsed class
                sidebar.classList.toggle('collapsed');
            }
        }
    }

    scrollToBottom(smooth = true) {
        const chatArea = document.getElementById('chatArea');
        if (!chatArea) return;

        if (smooth) {
            chatArea.scrollTo({
                top: chatArea.scrollHeight,
                behavior: 'smooth'
            });
        } else {
            chatArea.scrollTop = chatArea.scrollHeight;
        }
    }

    shouldAutoScroll() {
        const chatArea = document.getElementById('chatArea');
        if (!chatArea) return true;

        // Auto-scroll if user is near the bottom (within 100px of bottom)
        const scrollPosition = chatArea.scrollTop + chatArea.clientHeight;
        const scrollHeight = chatArea.scrollHeight;
        return scrollHeight - scrollPosition <= 100;
    }

    streamResponse(text, sources) {
        // Find the last assistant message (which should be the "Thinking..." message)
        const assistantMessages = document.querySelectorAll('.chat-message.assistant-message');
        const thinkingMessage = assistantMessages[assistantMessages.length - 1];
        if (!thinkingMessage) return;

        const contentDiv = thinkingMessage.querySelector('.message-content');
        contentDiv.innerHTML = ''; // Clear the thinking message
        
        let i = 0;
        const speed = 5; // milliseconds per character (faster typing)
        let currentText = '';
        const self = this; // Store reference to 'this'
        
        // Set streaming state
        this.isStreaming = true;
        this.updateSendButtonForStreaming();

        function typeWriter() {
            if (i < text.length && self.isStreaming) {
                currentText += text.charAt(i);
                // Apply formatting to the current text
                contentDiv.innerHTML = self.renderFormattedText(currentText);
                i++;

                // Auto-scroll during streaming if user is near bottom
                if (self.shouldAutoScroll()) {
                    self.scrollToBottom(false); // Use instant scroll for smooth typing
                }

                self.streamingTimeoutId = setTimeout(typeWriter, speed);
            } else {
                // Streaming completed or stopped
                self.isStreaming = false;
                self.updateSendButtonForStreaming();

                // After typing is done, add sources (only if completed, not stopped)
                if (i >= text.length && sources && sources.length > 0) {
                    const sourcesDiv = document.createElement('div');
                    sourcesDiv.className = 'message-sources';
                    sourcesDiv.innerHTML = '<strong>Sources:</strong><br>' +
                        sources.map(source => {
                            // Handle both old string format and new object format
                            if (typeof source === 'string') {
                                return `<span class="source-item">${self.escapeHtml(source)}</span>`;
                            } else {
                                const pageNumber = source.page_number || 'N/A';
                                const fileName = self.escapeHtml(source.filename || source.text || 'Unknown');
                                if (pageNumber !== 'N/A') {
                                    return `<a href="/documents/${encodeURIComponent(fileName)}#page=${pageNumber}" target="_blank" class="source-item">${fileName} (Page ${pageNumber})</a>`;
                                } else {
                                    return `<a href="/documents/${encodeURIComponent(fileName)}" target="_blank" class="source-item">${fileName}</a>`;
                                }
                            }
                        }).join('<br>');
                    contentDiv.appendChild(sourcesDiv);

                    // Smooth scroll after adding sources
                    if (self.shouldAutoScroll()) {
                        self.scrollToBottom();
                    }
                }

                // Add action buttons after typing is done (only if completed)
                if (i >= text.length) {
                    self.addActionButtons(thinkingMessage, text);

                    // Final smooth scroll after everything is complete
                    if (self.shouldAutoScroll()) {
                        self.scrollToBottom();
                    }
                }
            }
        }
        typeWriter();
    }

    // Autocomplete functionality
    async handleAutocomplete() {
        const chatInput = document.getElementById('chatInput');
        const query = chatInput.value.trim();

        // Hide autocomplete if query is too short
        if (query.length < 2) {
            this.hideAutocomplete();
            return;
        }

        try {
            console.log('Fetching autocomplete for:', query);
            const response = await fetch(`/autocomplete?query=${encodeURIComponent(query)}`);
            const data = await response.json();
            console.log('Autocomplete data:', data);
            this.showAutocomplete(data.suggestions, query);
        } catch (error) {
            console.error('Autocomplete error:', error);
            this.hideAutocomplete();
        }
    }

    showAutocomplete(suggestions, query) {
        const dropdown = document.getElementById('autocompleteDropdown');
        console.log('Dropdown element:', dropdown);
        
        if (!suggestions || suggestions.length === 0) {
            console.log('No suggestions to show');
            this.hideAutocomplete();
            return;
        }

        console.log('Showing', suggestions.length, 'suggestions');
        dropdown.innerHTML = '';
        this.currentAutocompleteIndex = -1;

        suggestions.forEach((suggestionData, index) => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            item.dataset.index = index;
            
            // Handle both old string format and new object format
            const suggestion = typeof suggestionData === 'string' ? suggestionData : suggestionData.title;
            const subtitle = typeof suggestionData === 'object' ? suggestionData.subtitle : '';
            const matchType = typeof suggestionData === 'object' ? suggestionData.match_type : 'partial';
            const isExactMatch = typeof suggestionData === 'object' ? suggestionData.is_exact_match : false;
            const documentName = typeof suggestionData === 'object' ? suggestionData.document : null;
            
            // Add match type indicator
            if (isExactMatch) {
                item.classList.add('exact-match');
            } else if (matchType === 'related') {
                item.classList.add('related-match');
            }
            
            // Highlight matching text
            const highlightedText = this.highlightMatch(suggestion, query);
            
            // Create document source indicator
            let documentIndicator = '';
            if (documentName) {
                // Show full document name without truncation
                documentIndicator = `<span class="document-indicator" title="${this.escapeHtml(documentName)}">${this.escapeHtml(documentName)}</span>`;
            }
            
            // Add match type indicator (small icon only)
            let matchIcon = '';
            if (isExactMatch) {
                matchIcon = '<span class="match-icon exact" title="Exact match">✓</span>';
            } else if (matchType === 'related') {
                matchIcon = '<span class="match-icon related" title="Related suggestion">~</span>';
            }
            
            // Create subtitle display if available
            let subtitleHtml = '';
            if (subtitle && subtitle.trim()) {
                subtitleHtml = `<div class="suggestion-subtitle">${this.escapeHtml(subtitle)}</div>`;
            }

            // Multi-line layout with subtitle support
            item.innerHTML = `
                <div class="suggestion-content">
                    <div class="suggestion-main">
                        <div class="suggestion-title">${highlightedText}</div>
                        ${subtitleHtml}
                    </div>
                    <div class="suggestion-right">
                        ${documentIndicator}
                        ${matchIcon}
                    </div>
                </div>
            `;
            
            item.addEventListener('click', () => {
                this.selectAutocompleteItem(suggestion);
            });
            
            dropdown.appendChild(item);
        });

        dropdown.classList.add('show');
        console.log('Dropdown classes:', dropdown.className);
        console.log('Dropdown computed style:', window.getComputedStyle(dropdown).display);
        console.log('Dropdown visible:', dropdown.offsetHeight > 0);
    }

    hideAutocomplete() {
        const dropdown = document.getElementById('autocompleteDropdown');
        dropdown.classList.remove('show');
        this.currentAutocompleteIndex = -1;
    }

    highlightMatch(text, query) {
        const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
        return text.replace(regex, '<span class="highlight">$1</span>');
    }

    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    selectAutocompleteItem(suggestion) {
        const chatInput = document.getElementById('chatInput');
        chatInput.value = suggestion;
        this.hideAutocomplete();
        chatInput.focus();
        this.updateSendButton();
        this.updateCharCounter();
    }

    handleAutocompleteNavigation(e) {
        const dropdown = document.getElementById('autocompleteDropdown');
        if (!dropdown.classList.contains('show')) {
            return false;
        }

        const items = dropdown.querySelectorAll('.autocomplete-item');
        if (items.length === 0) {
            return false;
        }

        if (e.key === 'ArrowDown') {
            this.currentAutocompleteIndex = Math.min(this.currentAutocompleteIndex + 1, items.length - 1);
            this.updateAutocompleteSelection(items);
            return true;
        } else if (e.key === 'ArrowUp') {
            this.currentAutocompleteIndex = Math.max(this.currentAutocompleteIndex - 1, -1);
            this.updateAutocompleteSelection(items);
            return true;
        } else if (e.key === 'Enter' && this.currentAutocompleteIndex >= 0) {
            const selectedItem = items[this.currentAutocompleteIndex];
            const suggestion = selectedItem.textContent;
            this.selectAutocompleteItem(suggestion);
            return true;
        }

        return false;
    }

    updateAutocompleteSelection(items) {
        items.forEach((item, index) => {
            item.classList.toggle('active', index === this.currentAutocompleteIndex);
        });
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => new SRMAIApp());

