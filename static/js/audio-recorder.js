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

                // Show transcription as student message
                if (window.simulator && window.simulator.addStudentMessage) {
                    window.simulator.addStudentMessage(result.transcription + ' [Audio]');
                }

                // Wait a moment before showing next question
                setTimeout(() => {
                    // ✅ FIXED: Check for session ending or closing message
                    if (result.session_ending || (result.follow_up && result.follow_up.is_closing)) {
                        console.log('✅ Session ending, displaying closing message');
                        this.displayClosingMessage(result.follow_up);
                    } else if (result.follow_up) {
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
                <div class="alert alert-info">
                    <strong>Your response:</strong> ${text}
                </div>
            `;
            transcriptionDiv.style.display = 'block';
        }
    }

    displayNextQuestion(followUp) {
        console.log('Displaying next question:', followUp);
    
        // ✅ RESET RECORDING UI BEFORE SHOWING NEXT QUESTION
        this.updateRecordingUI(false);  // Hide Stop button, show Record button
        this.hideProcessingIndicator();
    
        // ✅ CLEAR TRANSCRIPTION PREVIEW
        const transcriptionDiv = document.getElementById('transcriptionPreview');
        if (transcriptionDiv) {
            transcriptionDiv.innerHTML = '';
            transcriptionDiv.style.display = 'none';
        }

        // Add to main simulator: presentQuestion reveals the text in sync
        // with the audio starting, then the response area opens
        if (window.simulator) {
            window.simulator.currentExecutive = followUp.executive;
            window.simulator.presentQuestion(followUp).then(() => {
                window.simulator.showResponseArea(followUp.executive);
            });
        }
    }

    // ✅ ADD THIS NEW METHOD:
    displayClosingMessage(followUp) {
        console.log('✅ Displaying closing message:', followUp);
    
        // ✅ RESET RECORDING UI
        this.updateRecordingUI(false);
        this.hideProcessingIndicator();
    
        // ✅ CLEAR TRANSCRIPTION PREVIEW
        const transcriptionDiv = document.getElementById('transcriptionPreview');
        if (transcriptionDiv) {
            transcriptionDiv.innerHTML = '';
            transcriptionDiv.style.display = 'none';
        }

        // Add closing message to chat, revealed in sync with its audio,
        // then move to the summary once the audio finishes
        if (window.simulator && followUp) {
            window.simulator.sessionEnding = true;
            window.simulator.presentQuestion(followUp).then(() => {
                window.simulator.showSessionEndedMessage();
                window.simulator.endSessionWhenAudioFinishes();
            });
        }
    }

    showProcessingIndicator() {
        const indicator = document.getElementById('processingIndicator');
        if (indicator) {
            indicator.style.display = 'block';
        }
        
        const recordBtn = document.getElementById('recordBtn');
        if (recordBtn) {
            recordBtn.disabled = true;
        }
    }

    hideProcessingIndicator() {
        const indicator = document.getElementById('processingIndicator');
        if (indicator) {
            indicator.style.display = 'none';
        }

        const recordBtn = document.getElementById('recordBtn');
        if (recordBtn) {
            recordBtn.disabled = false;
        }
    }

    updateRecordingUI(isRecording) {
        const recordBtn = document.getElementById('recordBtn');
        const stopBtn = document.getElementById('stopRecordBtn');
        
        if (recordBtn && stopBtn) {
            if (isRecording) {
                recordBtn.style.display = 'none';
                stopBtn.style.display = 'inline-block';
            } else {
                recordBtn.style.display = 'inline-block';
                stopBtn.style.display = 'none';
            }
        }
    }

    startTimer() {
        const timerDisplay = document.getElementById('recordingTimer');
        if (!timerDisplay) return;

        timerDisplay.style.display = 'block';
        
        this.timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.recordingStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            timerDisplay.textContent = `Recording: ${minutes}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }

        const timerDisplay = document.getElementById('recordingTimer');
        if (timerDisplay) {
            timerDisplay.style.display = 'none';
        }
    }

    setCurrentExecutive(executive) {
        this.currentExecutive = executive;
    }
}

// Initialize audio recorder when page loads
window.addEventListener('DOMContentLoaded', () => {
    window.audioRecorder = new AudioRecorder();
    console.log('✅ Audio recorder initialized');
});
