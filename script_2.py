# Create static files directory structure
import os

os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)

# Create CSS styles
css_content = '''/* AI Executive Panel Simulator Styles */

:root {
    --primary-color: #0d6efd;
    --secondary-color: #6c757d;
    --success-color: #198754;
    --info-color: #0dcaf0;
    --warning-color: #ffc107;
    --danger-color: #dc3545;
    --executive-ceo: #8b5a3c;
    --executive-cfo: #2e8b57;
    --executive-cto: #4169e1;
    --executive-cmo: #ff6347;
    --executive-coo: #9370db;
}

body {
    background-color: #f8f9fa;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.navbar-brand {
    font-weight: 600;
}

.phase {
    display: none;
    animation: fadeIn 0.5s ease-in;
}

.phase.active {
    display: block;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Executive Selection Cards */
.executive-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-top: 0.5rem;
}

.executive-card {
    position: relative;
    border: 2px solid #e9ecef;
    border-radius: 8px;
    transition: all 0.3s ease;
    background: white;
}

.executive-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.executive-card input[type="checkbox"] {
    display: none;
}

.executive-card label {
    display: flex;
    align-items: center;
    padding: 1rem;
    cursor: pointer;
    margin-bottom: 0;
    width: 100%;
    height: 100%;
}

.executive-card input[type="checkbox"]:checked + label {
    background: linear-gradient(135deg, var(--primary-color), #4dabf7);
    color: white;
    border-radius: 6px;
}

.exec-icon {
    font-size: 2rem;
    margin-right: 1rem;
    min-width: 3rem;
    text-align: center;
}

.exec-info strong {
    display: block;
    font-size: 1.1rem;
    margin-bottom: 0.25rem;
}

.exec-info small {
    opacity: 0.8;
    font-size: 0.875rem;
}

/* Executive colors */
.executive-card[data-role="CEO"] input[type="checkbox"]:checked + label {
    background: linear-gradient(135deg, var(--executive-ceo), #cd853f);
}

.executive-card[data-role="CFO"] input[type="checkbox"]:checked + label {
    background: linear-gradient(135deg, var(--executive-cfo), #3cb371);
}

.executive-card[data-role="CTO"] input[type="checkbox"]:checked + label {
    background: linear-gradient(135deg, var(--executive-cto), #6495ed);
}

.executive-card[data-role="CMO"] input[type="checkbox"]:checked + label {
    background: linear-gradient(135deg, var(--executive-cmo), #ff7f50);
}

.executive-card[data-role="COO"] input[type="checkbox"]:checked + label {
    background: linear-gradient(135deg, var(--executive-coo), #ba55d3);
}

/* Conversation Styles */
.conversation-container {
    height: 400px;
    overflow-y: auto;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 1rem;
    background: white;
}

.message {
    margin-bottom: 1.5rem;
    opacity: 0;
    animation: slideInMessage 0.5s ease-out forwards;
}

@keyframes slideInMessage {
    from {
        opacity: 0;
        transform: translateX(-20px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

.message.executive {
    text-align: left;
}

.message.student {
    text-align: right;
}

.message-header {
    display: flex;
    align-items: center;
    margin-bottom: 0.5rem;
    font-weight: 600;
}

.message.student .message-header {
    justify-content: flex-end;
}

.executive-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 1.2rem;
    margin-right: 0.75rem;
}

.student-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: var(--success-color);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 1.2rem;
    margin-left: 0.75rem;
}

.message-bubble {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 12px;
    padding: 1rem;
    max-width: 80%;
    position: relative;
}

.message.executive .message-bubble {
    margin-left: 0;
    border-left: 4px solid var(--primary-color);
}

.message.student .message-bubble {
    margin-left: auto;
    background: var(--success-color);
    color: white;
    border-left: none;
    border-right: 4px solid #0d5128;
}

.message-time {
    font-size: 0.75rem;
    color: #6c757d;
    margin-top: 0.5rem;
}

.message.student .message-time {
    color: rgba(255,255,255,0.8);
}

/* Executive role colors for avatars */
.avatar-CEO { background: var(--executive-ceo); }
.avatar-CFO { background: var(--executive-cfo); }
.avatar-CTO { background: var(--executive-cto); }
.avatar-CMO { background: var(--executive-cmo); }
.avatar-COO { background: var(--executive-coo); }

/* Executive Panel Sidebar */
.executive-member {
    display: flex;
    align-items: center;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    background: #f8f9fa;
    border-radius: 8px;
    border-left: 4px solid transparent;
}

.executive-member.active {
    background: #e3f2fd;
    border-left-color: var(--primary-color);
}

.executive-member .avatar {
    width: 35px;
    height: 35px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 0.9rem;
    margin-right: 0.75rem;
}

.executive-member .info {
    flex: 1;
}

.executive-member .info .name {
    font-weight: 600;
    font-size: 0.9rem;
    margin-bottom: 0.25rem;
}

.executive-member .info .title {
    font-size: 0.75rem;
    color: #6c757d;
}

/* Response Area */
#response-area {
    border-top: 1px solid #dee2e6;
    padding-top: 1rem;
}

#student-response {
    border-radius: 8px;
    resize: vertical;
    min-height: 80px;
}

#send-response-btn {
    border-radius: 0 8px 8px 0;
}

/* Loading States */
.loading-message {
    text-align: center;
    padding: 2rem;
    color: #6c757d;
}

.loading-message .spinner-border {
    width: 2rem;
    height: 2rem;
    margin-bottom: 1rem;
}

/* Summary Styles */
.summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.summary-card {
    background: white;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 1.5rem;
}

.summary-card h6 {
    color: var(--primary-color);
    margin-bottom: 1rem;
    font-weight: 600;
}

.feedback-item {
    background: #f8f9fa;
    border-left: 4px solid var(--success-color);
    padding: 1rem;
    margin-bottom: 0.75rem;
    border-radius: 4px;
}

.feedback-item.improvement {
    border-left-color: var(--warning-color);
}

.feedback-item.strength {
    border-left-color: var(--success-color);
}

/* Responsive Design */
@media (max-width: 768px) {
    .executive-grid {
        grid-template-columns: 1fr 1fr;
    }
    
    .message-bubble {
        max-width: 90%;
    }
    
    .conversation-container {
        height: 300px;
    }
}

/* Utility Classes */
.sticky-top {
    top: 20px;
}

.shadow {
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075) !important;
}

.shadow-sm {
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075) !important;
}

.shadow-lg {
    box-shadow: 0 1rem 3rem rgba(0, 0, 0, 0.175) !important;
}

/* Animation for buttons */
.btn {
    transition: all 0.2s ease;
}

.btn:hover {
    transform: translateY(-1px);
}

/* Custom scrollbar */
.conversation-container::-webkit-scrollbar {
    width: 6px;
}

.conversation-container::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
}

.conversation-container::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 3px;
}

.conversation-container::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
}
'''

# Save CSS file
with open('static/css/style.css', 'w') as f:
    f.write(css_content)

print("Created static/css/style.css")