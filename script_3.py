# Create JavaScript file
js_content = '''// AI Executive Panel Simulator - JavaScript

class ExecutiveSimulator {
    constructor() {
        this.currentPhase = 'setup';
        this.selectedExecutives = [];
        this.conversationHistory = [];
        this.awaitingResponse = false;
        this.currentExecutive = null;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.showPhase('setup');
    }
    
    bindEvents() {
        // Setup form submission
        document.getElementById('setup-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.startSession();
        });
        
        // Response submission
        document.getElementById('send-response-btn').addEventListener('click', () => {
            this.sendResponse();
        });
        
        // Enter key in response textarea
        document.getElementById('student-response').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendResponse();
            }
        });
        
        // End session
        document.getElementById('end-session-btn').addEventListener('click', () => {
            this.endSession();
        });
        
        // New session
        document.getElementById('new-session-btn').addEventListener('click', () => {
            this.newSession();
        });
        
        // Executive selection
        document.querySelectorAll('.executive-card input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                this.updateSelectedExecutives();
            });
        });
    }
    
    updateSelectedExecutives() {
        this.selectedExecutives = [];
        document.querySelectorAll('.executive-card input[type="checkbox"]:checked').forEach(checkbox => {
            this.selectedExecutives.push(checkbox.value);
        });
    }
    
    showPhase(phaseName) {
        // Hide all phases
        document.querySelectorAll('.phase').forEach(phase => {
            phase.classList.remove('active');
        });
        
        // Show target phase
        document.getElementById(`${phaseName}-phase`).classList.add('active');
        this.currentPhase = phaseName;
    }
    
    async startSession() {
        if (this.selectedExecutives.length === 0) {
            alert('Please select at least one executive for the panel.');
            return;
        }
        
        const companyName = document.getElementById('company-name').value;
        const industry = document.getElementById('industry').value;
        const presentationTopic = document.getElementById('presentation-topic').value;
        
        if (!companyName || !industry || !presentationTopic) {
            alert('Please fill in all required fields.');
            return;
        }
        
        // Show loading
        this.showLoadingModal('Setting up your executive panel...');
        
        try {
            const response = await fetch('/setup_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    company_name: companyName,
                    industry: industry,
                    presentation_topic: presentationTopic,
                    selected_executives: this.selectedExecutives
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.hideLoadingModal();
                this.setupSimulationPhase();
                this.startPresentation();
            } else {
                throw new Error(data.error || 'Failed to setup session');
            }
        } catch (error) {
            this.hideLoadingModal();
            alert('Error starting session: ' + error.message);
        }
    }
    
    setupSimulationPhase() {
        const executiveList = document.getElementById('executive-list');
        executiveList.innerHTML = '';
        
        const executives = {
            'CEO': { name: 'Sarah Chen', icon: 'fa-crown' },
            'CFO': { name: 'Michael Rodriguez', icon: 'fa-chart-line' },
            'CTO': { name: 'Dr. Lisa Wang', icon: 'fa-microchip' },
            'CMO': { name: 'James Thompson', icon: 'fa-bullhorn' },
            'COO': { name: 'Rebecca Johnson', icon: 'fa-cogs' }
        };
        
        this.selectedExecutives.forEach(role => {
            const exec = executives[role];
            const execElement = document.createElement('div');
            execElement.className = 'executive-member';
            execElement.innerHTML = `
                <div class="avatar avatar-${role}">
                    <i class="fas ${exec.icon}"></i>
                </div>
                <div class="info">
                    <div class="name">${exec.name}</div>
                    <div class="title">${role}</div>
                </div>
            `;
            executiveList.appendChild(execElement);
        });
        
        this.showPhase('simulation');
    }
    
    async startPresentation() {
        this.showLoadingModal('AI executives are preparing their questions...');
        
        try {
            const response = await fetch('/start_presentation', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.hideLoadingModal();
                this.displayInitialQuestions(data.initial_questions);
            } else {
                throw new Error(data.error || 'Failed to start presentation');
            }
        } catch (error) {
            this.hideLoadingModal();
            alert('Error starting presentation: ' + error.message);
        }
    }
    
    displayInitialQuestions(questions) {
        const conversationArea = document.getElementById('conversation-area');
        conversationArea.innerHTML = '';
        
        // Add welcome message
        this.addMessage({
            type: 'system',
            message: 'Welcome to your executive presentation! The panel is ready to hear your proposal.',
            timestamp: new Date().toISOString()
        });
        
        // Add first executive question
        if (questions.length > 0) {
            const firstQuestion = questions[0];
            this.addExecutiveMessage(firstQuestion);
            this.currentExecutive = firstQuestion.executive;
            this.showResponseArea(firstQuestion.executive);
        }
    }
    
    addMessage(messageData) {
        const conversationArea = document.getElementById('conversation-area');
        const messageElement = document.createElement('div');
        
        if (messageData.type === 'system') {
            messageElement.className = 'message system text-center';
            messageElement.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    ${messageData.message}
                </div>
            `;
        }
        
        conversationArea.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    addExecutiveMessage(questionData) {
        const conversationArea = document.getElementById('conversation-area');
        const messageElement = document.createElement('div');
        messageElement.className = 'message executive';
        
        const time = new Date(questionData.timestamp).toLocaleTimeString();
        
        messageElement.innerHTML = `
            <div class="message-header">
                <div class="executive-avatar avatar-${questionData.executive}">
                    ${this.getExecutiveIcon(questionData.executive)}
                </div>
                <div>
                    <strong>${questionData.name}</strong>
                    <small class="text-muted">${questionData.title}</small>
                </div>
            </div>
            <div class="message-bubble">
                <p class="mb-0">${questionData.question}</p>
                <div class="message-time">${time}</div>
            </div>
        `;
        
        conversationArea.appendChild(messageElement);
        this.scrollToBottom();
        
        // Highlight active executive
        this.setActiveExecutive(questionData.executive);
    }
    
    addStudentMessage(response, executive) {
        const conversationArea = document.getElementById('conversation-area');
        const messageElement = document.createElement('div');
        messageElement.className = 'message student';
        
        const time = new Date().toLocaleTimeString();
        
        messageElement.innerHTML = `
            <div class="message-header">
                <div>
                    <strong>You</strong>
                    <small class="text-muted">Student Response</small>
                </div>
                <div class="student-avatar">
                    <i class="fas fa-user"></i>
                </div>
            </div>
            <div class="message-bubble">
                <p class="mb-0">${response}</p>
                <div class="message-time">${time}</div>
            </div>
        `;
        
        conversationArea.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    getExecutiveIcon(role) {
        const icons = {
            'CEO': '<i class="fas fa-crown"></i>',
            'CFO': '<i class="fas fa-chart-line"></i>',
            'CTO': '<i class="fas fa-microchip"></i>',
            'CMO': '<i class="fas fa-bullhorn"></i>',
            'COO': '<i class="fas fa-cogs"></i>'
        };
        return icons[role] || '<i class="fas fa-user"></i>';
    }
    
    setActiveExecutive(role) {
        document.querySelectorAll('.executive-member').forEach(member => {
            member.classList.remove('active');
        });
        
        // Find and activate the correct executive
        document.querySelectorAll('.executive-member').forEach(member => {
            const titleElement = member.querySelector('.title');
            if (titleElement && titleElement.textContent === role) {
                member.classList.add('active');
            }
        });
    }
    
    showResponseArea(executive) {
        const responseArea = document.getElementById('response-area');
        responseArea.style.display = 'block';
        
        const textarea = document.getElementById('student-response');
        textarea.placeholder = `Respond to the ${executive}...`;
        textarea.focus();
        
        this.awaitingResponse = true;
    }
    
    hideResponseArea() {
        document.getElementById('response-area').style.display = 'none';
        this.awaitingResponse = false;
    }
    
    async sendResponse() {
        const responseText = document.getElementById('student-response').value.trim();
        
        if (!responseText) {
            alert('Please enter a response.');
            return;
        }
        
        if (!this.awaitingResponse || !this.currentExecutive) {
            alert('No active question to respond to.');
            return;
        }
        
        // Add student response to conversation
        this.addStudentMessage(responseText, this.currentExecutive);
        
        // Clear response area
        document.getElementById('student-response').value = '';
        this.hideResponseArea();
        
        // Show loading
        this.addLoadingMessage('Executive is considering your response...');
        
        try {
            const response = await fetch('/respond_to_executive', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    response: responseText,
                    executive_role: this.currentExecutive
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.removeLoadingMessage();
                
                // Add follow-up question
                if (data.follow_up) {
                    setTimeout(() => {
                        this.addExecutiveMessage(data.follow_up);
                        this.currentExecutive = data.follow_up.executive;
                        this.showResponseArea(data.follow_up.executive);
                    }, 1000);
                }
            } else {
                throw new Error(data.error || 'Failed to get response');
            }
        } catch (error) {
            this.removeLoadingMessage();
            alert('Error getting executive response: ' + error.message);
            this.showResponseArea(this.currentExecutive);
        }
    }
    
    addLoadingMessage(text) {
        const conversationArea = document.getElementById('conversation-area');
        const loadingElement = document.createElement('div');
        loadingElement.className = 'loading-message';
        loadingElement.id = 'loading-message';
        loadingElement.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p>${text}</p>
        `;
        conversationArea.appendChild(loadingElement);
        this.scrollToBottom();
    }
    
    removeLoadingMessage() {
        const loadingMessage = document.getElementById('loading-message');
        if (loadingMessage) {
            loadingMessage.remove();
        }
    }
    
    async endSession() {
        if (confirm('Are you sure you want to end this session?')) {
            try {
                const response = await fetch('/end_session', {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    this.showSessionSummary(data.summary);
                } else {
                    throw new Error(data.error || 'Failed to end session');
                }
            } catch (error) {
                alert('Error ending session: ' + error.message);
            }
        }
    }
    
    showSessionSummary(summary) {
        const summaryContainer = document.getElementById('session-summary');
        
        summaryContainer.innerHTML = `
            <div class="summary-grid">
                <div class="summary-card">
                    <h6><i class="fas fa-info-circle"></i> Session Details</h6>
                    <p><strong>Company:</strong> ${summary.company_name}</p>
                    <p><strong>Topic:</strong> ${summary.presentation_topic}</p>
                    <p><strong>Executives:</strong> ${summary.executives_involved.join(', ')}</p>
                    <p><strong>Total Interactions:</strong> ${summary.total_interactions}</p>
                </div>
                
                <div class="summary-card">
                    <h6><i class="fas fa-thumbs-up"></i> Strengths</h6>
                    ${summary.feedback.strengths.map(strength => 
                        `<div class="feedback-item strength">${strength}</div>`
                    ).join('')}
                </div>
                
                <div class="summary-card">
                    <h6><i class="fas fa-lightbulb"></i> Areas for Improvement</h6>
                    ${summary.feedback.areas_for_improvement.map(improvement => 
                        `<div class="feedback-item improvement">${improvement}</div>`
                    ).join('')}
                </div>
            </div>
            
            <div class="row">
                <div class="col-12">
                    <div class="summary-card">
                        <h6><i class="fas fa-users"></i> Executive Feedback</h6>
                        ${Object.entries(summary.feedback.executive_feedback).map(([role, feedback]) => `
                            <div class="mb-3">
                                <h6 class="text-primary">${feedback.name} (${role})</h6>
                                <p><strong>Focus Areas:</strong> ${feedback.focus_areas_addressed.join(', ')}</p>
                                <p><strong>Suggestion:</strong> ${feedback.suggestions}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        
        this.showPhase('summary');
    }
    
    newSession() {
        // Reset all data
        this.currentPhase = 'setup';
        this.selectedExecutives = [];
        this.conversationHistory = [];
        this.awaitingResponse = false;
        this.currentExecutive = null;
        
        // Clear form
        document.getElementById('setup-form').reset();
        document.querySelectorAll('.executive-card input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        // Show setup phase
        this.showPhase('setup');
    }
    
    scrollToBottom() {
        const conversationArea = document.getElementById('conversation-area');
        conversationArea.scrollTop = conversationArea.scrollHeight;
    }
    
    showLoadingModal(message = 'Loading...') {
        const modal = document.getElementById('loadingModal');
        modal.querySelector('p').textContent = message;
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }
    
    hideLoadingModal() {
        const modal = document.getElementById('loadingModal');
        const bootstrapModal = bootstrap.Modal.getInstance(modal);
        if (bootstrapModal) {
            bootstrapModal.hide();
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ExecutiveSimulator();
});

// Additional utility functions
function formatTime(timestamp) {
    return new Date(timestamp).toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit'
    });
}

function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden - could pause timers or save state
    } else {
        // Page is visible - could resume or refresh
    }
});
'''

# Save JavaScript file
with open('static/js/app.js', 'w') as f:
    f.write(js_content)

print("Created static/js/app.js")