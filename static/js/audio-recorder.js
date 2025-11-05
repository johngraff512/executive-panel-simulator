// Audio Recording Manager for AI Executive Panel Simulator
class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.recordingStartTime = null;
        this.timerInterval = null;
        this.currentExecutive = null;
    }

    async startRecording() {
        try {
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 44100
                } 
            });

            // Create MediaRecorder with webm format
            const options = { mimeType: 'audio/webm' };
            this.mediaRecorder = new MediaRecorder(stream, options);

            // Handle data availability
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            // Handle recording stop
            this.mediaRecorder.onstop = async () => {
                await this.handleRecordingComplete();
            };

            // Start recording
            this.audioChunks = [];
            this.mediaRecorder.start();
            this.isRecording = true;
            this.recordingStartTime = Date.now();

            // Update UI
            this.updateRecordingUI(true);
            this.startTimer();

            console.log('🎤 Recording started');

        } catch (error) {
            console.error('Error accessing microphone:', error);
            
            if (error.name === 'NotAllowedError') {
                alert('Microphone access denied. Please allow microphone access in your browser settings and try again.');
            } else if (error.name === 'NotFoundError') {
                alert('No microphone found. Please connect a microphone and try again.');
            } else {
                alert('Error accessing microphone: ' + error.message);
            }
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            
            // Stop all audio tracks
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
            
            this.isRecording = false;
            this.stopTimer();

            console.log('⏹️ Recording stopped');
        }
    }

    async handleRecordingComplete() {
        // Create audio blob from chunks
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        
        console.log(`📦 Audio blob created: ${audioBlob.size} bytes`);

        // Upload and process
        await this.uploadAudioResponse(audioBlob);

        // Clear chunks for next recording
        this.audioChunks = [];
    }

    async uploadAudioResponse(audioBlob) {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'response.webm');
        formData.append('executive_role', this.currentExecutive || '');

        // Show processing indicator
        this.showProcessingIndicator();

        try {
            const response = await fetch('/respond_to_executive_audio', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.status === 'success') {
                // Display transcription
                this.displayTranscription(result.transcription);
    
                // ✅ ADD: Show transcription as student message in chat
                if (window.simulator && window.simulator.addStudentMessage) {
                    window.simulator.addStudentMessage(result.transcription + ' [Audio]');
                }
    
                // ✅ ADD: Wait a moment before showing next question
                setTimeout(() => {
                    // Display next question or closing
                    if (result.session_ending) {
                        this.displayClosingMessage(result.follow_up);
                    } else {
                        this.displayNextQuestion(result.follow_up);
                    }
                }, 1000);
            } else {
                alert('Error processing audio: ' + result.error);
                this.hideProcessingIndicator();
            }

        } catch (error) {
            console.error('Error uploading audio:', error);
            alert('Error uploading audio response. Please try again or use text input.');
            this.hideProcessingIndicator();
        }
    }

    displayTranscription(text) {
        const transcriptionDiv = document.getElementById('transcriptionPreview');
        if (transcriptionDiv) {
            transcriptionDiv.innerHTML = `
                <div class="transcription-box">
                    <strong>Your Response (transcribed):</strong>
                    <p>${text}</p>
                </div>
            `;
            transcriptionDiv.style.display = 'block';
        }
    }

    displayNextQuestion(followUp) {
        this.hideProcessingIndicator();
    
        // Store current executive
        this.currentExecutive = followUp.executive;
    
        // ✅ USE the simulator's addExecutiveMessage function instead
        if (window.simulator && window.simulator.addExecutiveMessage) {
            window.simulator.addExecutiveMessage(followUp);
        
            // Show response area for next answer
            if (window.simulator.showResponseArea) {
                window.simulator.showResponseArea(followUp.executive);
            }
        } else {
            // Fallback: manually display question (old way)
            const questionHTML = `
                <div class="card border-primary mb-3">
                    <div class="card-header bg-primary text-white">
                        <strong>${followUp.name}</strong> (${followUp.title})
                    </div>
                    <div class="card-body">
                        <p class="mb-0">${followUp.question}</p>
                    </div>
                </div>
            `;
        
            const questionContainer = document.getElementById('questionContainer');
            if (questionContainer) {
                questionContainer.innerHTML = questionHTML;
            }
        }
    
        // Reset recording UI
        this.updateRecordingUI(false);
    
        // Clear transcription preview after delay
        setTimeout(() => {
            const preview = document.getElementById('transcriptionPreview');
            if (preview) {
                preview.style.display = 'none';
            }
        }, 3000);
    }

    displayClosingMessage(followUp) {
        this.hideProcessingIndicator();
        
        const closingHTML = `
            <div class="session-complete">
                <h2>Session Complete!</h2>
                <div class="closing-message">
                    <p>${followUp.question}</p>
                </div>
                <button onclick="window.location.href='/download_transcript'" class="btn-download">
                    📄 Download Transcript
                </button>
            </div>
        `;

        const questionContainer = document.getElementById('questionContainer');
        if (questionContainer) {
            questionContainer.innerHTML = closingHTML;
        }

        // Hide response controls
        document.getElementById('responseSection').style.display = 'none';
    }

    updateRecordingUI(recording) {
        const recordBtn = document.getElementById('recordButton');
        const recordingIndicator = document.getElementById('recordingIndicator');
        const stopBtn = document.getElementById('stopButton');

        if (recording) {
            recordBtn.style.display = 'none';
            stopBtn.style.display = 'inline-block';
            recordingIndicator.style.display = 'flex';
        } else {
            recordBtn.style.display = 'inline-block';
            stopBtn.style.display = 'none';
            recordingIndicator.style.display = 'none';
        }
    }

    startTimer() {
        const timerDisplay = document.getElementById('recordingTimer');
        
        this.timerInterval = setInterval(() => {
            const elapsed = Date.now() - this.recordingStartTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            
            timerDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    showProcessingIndicator() {
        const indicator = document.getElementById('processingIndicator');
        if (indicator) {
            indicator.style.display = 'flex';
        }
    }

    hideProcessingIndicator() {
        const indicator = document.getElementById('processingIndicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }
}

// Initialize global recorder instance
const audioRecorder = new AudioRecorder();

// Global functions for button clicks
function startRecording() {
    audioRecorder.startRecording();
}

function stopRecording() {
    audioRecorder.stopRecording();
}

function toggleRecordingMode() {
    const textMode = document.getElementById('textResponseSection');
    const audioMode = document.getElementById('audioResponseSection');
    const textBtn = document.getElementById('textModeBtn');
    const audioBtn = document.getElementById('audioModeBtn');

    if (textMode.style.display === 'none') {
        // Switch to text mode
        textMode.style.display = 'block';
        audioMode.style.display = 'none';
        textBtn.classList.add('active');
        audioBtn.classList.remove('active');
    } else {
        // Switch to audio mode
        textMode.style.display = 'none';
        audioMode.style.display = 'block';
        textBtn.classList.remove('active');
        audioBtn.classList.add('active');
    }
}
