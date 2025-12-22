// ADD THESE PROPERTIES TO THE ExecutiveSimulator CONSTRUCTOR:
// (Find: constructor() { ... })
this.sessionType = 'questions';
this.timeLimit = null;
this.sessionStartTime = null;
this.timerInterval = null;

// ADD THIS TO uploadReportAndSetup METHOD WHERE FormData IS CREATED:
// (Find: formData.append('question_limit', questionLimit);)
formData.append('session_type', sessionType);
formData.append('time_limit', timeLimit);

// ADD THIS AFTER SUCCESS RESPONSE IN uploadReportAndSetup:
// (Find: if (data.status === 'success') { ... })
// Store session configuration
this.sessionType = sessionType;
this.timeLimit = sessionType === 'time' ? parseInt(timeLimit) : null;
this.sessionStartTime = new Date();

this.setupSimulationPhase();
this.startPresentation(data.first_question);

// Start timer if time-based session
if (this.sessionType === 'time') {
    this.startSessionTimer();
}

// ADD THESE NEW METHODS TO THE ExecutiveSimulator CLASS:

startSessionTimer() {
    const timerElement = document.getElementById('session-timer');
    const timerDisplay = document.getElementById('timer-display');

    if (!timerElement || !this.timeLimit) return;

    timerElement.style.display = 'block';

    this.timerInterval = setInterval(() => {
        const elapsed = (new Date() - this.sessionStartTime) / 1000; // seconds
        const remaining = (this.timeLimit * 60) - elapsed; // seconds remaining

        if (remaining <= 0) {
            timerDisplay.textContent = '0:00';
            timerDisplay.parentElement.classList.remove('bg-light', 'text-dark');
            timerDisplay.parentElement.classList.add('bg-danger', 'text-white');
            this.stopSessionTimer();

            // Auto-end session when time runs out
            if (!this.sessionEnding) {
                this.showTimeExpiredMessage();
            }
            return;
        }

        const minutes = Math.floor(remaining / 60);
        const seconds = Math.floor(remaining % 60);
        timerDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;

        // Change color when less than 1 minute remains
        if (remaining <= 60) {
            timerDisplay.parentElement.classList.remove('bg-light', 'text-dark');
            timerDisplay.parentElement.classList.add('bg-warning', 'text-dark');
        } else if (remaining <= 30) {
            timerDisplay.parentElement.classList.remove('bg-warning', 'bg-light', 'text-dark');
            timerDisplay.parentElement.classList.add('bg-danger', 'text-white');
        }
    }, 1000);
}

stopSessionTimer() {
    if (this.timerInterval) {
        clearInterval(this.timerInterval);
        this.timerInterval = null;
    }
}

showTimeExpiredMessage() {
    this.sessionEnding = true;
    this.hideResponseArea();

    const conversationArea = document.getElementById('conversation-area');
    const timeExpiredElement = document.createElement('div');
    timeExpiredElement.className = 'alert alert-warning text-center mt-3';
    timeExpiredElement.innerHTML = `
        <h5><i class="fas fa-clock"></i> Time's Up!</h5>
        <p>Your ${this.timeLimit}-minute session has ended. The panel thanks you for your presentation.</p>
        <button class="btn btn-primary" onclick="simulator.endSession()">
            View Summary & Feedback
        </button>
    `;
    conversationArea.appendChild(timeExpiredElement);
    this.scrollToBottom();
}

// MODIFY THE endSession METHOD TO STOP THE TIMER:
// (Find: async endSession() { ... })
// Add this at the beginning:
this.stopSessionTimer();

// MODIFY THE newSession METHOD TO RESET TIMER:
// (Find: newSession() { ... })
// Add these properties:
this.sessionType = 'questions';
this.timeLimit = null;
this.sessionStartTime = null;

// Stop and hide timer
this.stopSessionTimer();
const timerElement = document.getElementById('session-timer');
if (timerElement) {
    timerElement.style.display = 'none';
}

// MODIFY showSessionSummary TO DISPLAY DURATION:
// (Find: showSessionSummary(summary) { ... })
// Add before the summary HTML:
const durationText = summary.session_duration
    ? `<p><strong>Duration:</strong> ${summary.session_duration} minutes</p>`
    : '';

// Then in the HTML template, add ${durationText} after the session limit line
