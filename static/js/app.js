/**
 * Subconscious Voice Agent - Frontend Application
 * ================================================
 * Handles voice interaction using MediaRecorder + Server-side transcription,
 * business selection, and conversation management.
 */

// =============================================================================
// State Management
// =============================================================================

const state = {
    currentBusiness: null,
    sessionId: generateSessionId(),
    isInCall: false,
    isListening: false,
    isRecording: false,
    isSpeaking: false,
    isMuted: false,
    speakerOn: true,
    mediaRecorder: null,
    audioStream: null,
    audioChunks: [],
    synthesis: window.speechSynthesis,
    businesses: {},
    silenceTimer: null,
    recordingStartTime: null,
};

function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// =============================================================================
// DOM Elements
// =============================================================================

const elements = {
    // Panels
    businessPanel: document.getElementById('businessPanel'),
    businessGrid: document.getElementById('businessGrid'),
    callInterface: document.getElementById('callInterface'),
    
    // Call Header
    backButton: document.getElementById('backButton'),
    currentBusinessIcon: document.getElementById('currentBusinessIcon'),
    currentBusinessName: document.getElementById('currentBusinessName'),
    callStatus: document.getElementById('callStatus'),
    
    // Conversation
    conversationContainer: document.getElementById('conversationContainer'),
    conversation: document.getElementById('conversation'),
    welcomeMessage: document.getElementById('welcomeMessage'),
    
    // Visualizer
    visualizerContainer: document.getElementById('visualizerContainer'),
    visualizerLabel: document.getElementById('visualizerLabel'),
    
    // Sample Queries
    sampleQueries: document.getElementById('sampleQueries'),
    queryChips: document.getElementById('queryChips'),
    
    // Controls
    muteButton: document.getElementById('muteButton'),
    callButton: document.getElementById('callButton'),
    speakerButton: document.getElementById('speakerButton'),
    
    // Text Input
    textInput: document.getElementById('textInput'),
    sendButton: document.getElementById('sendButton'),
    
    // Footer
    apiStatus: document.getElementById('apiStatus'),
    
    // Toast
    toast: document.getElementById('toast'),
    toastMessage: document.getElementById('toastMessage'),
};

// =============================================================================
// Microphone & Recording Setup (MediaRecorder API)
// =============================================================================

async function initMicrophone() {
    try {
        // Request microphone permission
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                channelCount: 1,
                sampleRate: 16000,
                echoCancellation: true,
                noiseSuppression: true,
            }
        });
        
        state.audioStream = stream;
        console.log('✅ Microphone access granted');
        showToast('Microphone ready', 'success');
        return true;
        
    } catch (error) {
        console.error('Microphone access error:', error);
        
        if (error.name === 'NotAllowedError') {
            showToast('Please allow microphone access to use voice', 'error');
        } else if (error.name === 'NotFoundError') {
            showToast('No microphone found', 'error');
        } else {
            showToast('Microphone error: ' + error.message, 'error');
        }
        return false;
    }
}

function startRecording() {
    if (!state.audioStream || state.isMuted || state.isSpeaking) {
        return;
    }
    
    state.audioChunks = [];
    state.isRecording = true;
    state.isListening = true;
    state.recordingStartTime = Date.now();
    
    // Determine supported MIME type
    let mimeType = 'audio/webm';
    if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        mimeType = 'audio/webm;codecs=opus';
    } else if (MediaRecorder.isTypeSupported('audio/webm')) {
        mimeType = 'audio/webm';
    } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        mimeType = 'audio/mp4';
    } else if (MediaRecorder.isTypeSupported('audio/ogg')) {
        mimeType = 'audio/ogg';
    }
    
    try {
        state.mediaRecorder = new MediaRecorder(state.audioStream, { mimeType });
    } catch (e) {
        // Fallback without specifying mimeType
        state.mediaRecorder = new MediaRecorder(state.audioStream);
    }
    
    state.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
            state.audioChunks.push(event.data);
        }
    };
    
    state.mediaRecorder.onstop = async () => {
        state.isRecording = false;
        
        // Only process if we have audio data and recording was long enough
        const recordingDuration = Date.now() - state.recordingStartTime;
        
        if (state.audioChunks.length > 0 && recordingDuration > 500) {
            const audioBlob = new Blob(state.audioChunks, { type: state.mediaRecorder.mimeType });
            
            // Only transcribe if blob has content
            if (audioBlob.size > 1000) {
                updateUI();
                await transcribeAndProcess(audioBlob);
            }
        }
        
        // Restart listening if still in call
        if (state.isInCall && !state.isMuted && !state.isSpeaking) {
            setTimeout(() => startRecording(), 500);
        }
    };
    
    state.mediaRecorder.start();
    updateUI();
    
    // Show recording indicator
    elements.visualizerLabel.textContent = 'Listening... (speak now)';
    
    // Auto-stop recording after silence or max duration
    // For demo: record for 4 seconds then stop to process
    state.silenceTimer = setTimeout(() => {
        stopRecording();
    }, 4000);
    
    console.log('🎙️ Recording started');
}

function stopRecording() {
    if (state.silenceTimer) {
        clearTimeout(state.silenceTimer);
        state.silenceTimer = null;
    }
    
    if (state.mediaRecorder && state.mediaRecorder.state === 'recording') {
        state.mediaRecorder.stop();
        console.log('🛑 Recording stopped');
    }
    
    state.isRecording = false;
    state.isListening = false;
}

async function transcribeAndProcess(audioBlob) {
    elements.visualizerLabel.textContent = 'Processing...';
    
    try {
        // Create form data with audio file
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        
        // Send to server for transcription
        const response = await fetch('/api/transcribe', {
            method: 'POST',
            body: formData,
        });
        
        const data = await response.json();
        
        if (data.success && data.text && data.text.trim()) {
            console.log('📝 Transcription:', data.text);
            handleUserMessage(data.text);
        } else if (data.error) {
            console.log('Transcription note:', data.error);
            // Don't show error for "couldn't understand" - just keep listening
            if (!data.error.includes('Could not understand')) {
                showToast(data.error, 'error');
            }
        }
        
    } catch (error) {
        console.error('Transcription error:', error);
    }
    
    updateUI();
}

// =============================================================================
// Text-to-Speech (Web Speech API)
// =============================================================================

function speak(text, callback) {
    if (!state.speakerOn || !text) {
        if (callback) callback();
        return;
    }
    
    // Stop recording while speaking
    stopRecording();
    
    // Cancel any ongoing speech
    state.synthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    
    // Try to use a nice voice
    const voices = state.synthesis.getVoices();
    const preferredVoices = voices.filter(v => 
        v.lang.startsWith('en') && 
        (v.name.includes('Samantha') || 
         v.name.includes('Alex') || 
         v.name.includes('Google') ||
         v.name.includes('Microsoft') ||
         v.name.includes('Natural'))
    );
    
    if (preferredVoices.length > 0) {
        utterance.voice = preferredVoices[0];
    }
    
    utterance.onstart = () => {
        state.isSpeaking = true;
        updateUI();
    };
    
    utterance.onend = () => {
        state.isSpeaking = false;
        updateUI();
        if (callback) callback();
        
        // Resume recording after speaking
        if (state.isInCall && !state.isMuted) {
            setTimeout(() => startRecording(), 500);
        }
    };
    
    utterance.onerror = (event) => {
        console.error('TTS error:', event);
        state.isSpeaking = false;
        updateUI();
        if (callback) callback();
        
        // Resume recording even if TTS fails
        if (state.isInCall && !state.isMuted) {
            setTimeout(() => startRecording(), 500);
        }
    };
    
    state.synthesis.speak(utterance);
}

// =============================================================================
// API Communication
// =============================================================================

async function sendMessage(message) {
    if (!message.trim()) return;
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                business_id: state.currentBusiness?.id || 'hotel',
                session_id: state.sessionId,
            }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            return data.response;
        } else {
            console.error('API error:', data.error);
            return data.response || "I'm sorry, I couldn't process that request.";
        }
    } catch (error) {
        console.error('Network error:', error);
        return "I'm sorry, I'm having trouble connecting. Please try again.";
    }
}

async function checkApiHealth() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        
        if (data.api_configured) {
            elements.apiStatus.textContent = '● API Connected';
            elements.apiStatus.className = 'api-status connected';
        } else {
            elements.apiStatus.textContent = '○ API Key Missing';
            elements.apiStatus.className = 'api-status disconnected';
        }
    } catch (error) {
        elements.apiStatus.textContent = '○ Connection Error';
        elements.apiStatus.className = 'api-status disconnected';
    }
}

async function resetConversation() {
    try {
        await fetch('/api/reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: state.sessionId }),
        });
    } catch (e) {
        console.error('Reset error:', e);
    }
}

// =============================================================================
// Message Handling
// =============================================================================

async function handleUserMessage(text) {
    if (!text.trim()) return;
    
    // Stop recording while processing
    stopRecording();
    
    // Add user message to conversation
    addMessage(text, 'user');
    
    // Show typing indicator
    const typingId = showTypingIndicator();
    
    // Send to API
    const response = await sendMessage(text);
    
    // Remove typing indicator
    removeTypingIndicator(typingId);
    
    // Add agent response
    addMessage(response, 'agent');
    
    // Speak the response
    speak(response);
}

function addMessage(text, role) {
    // Hide welcome message
    if (elements.welcomeMessage) {
        elements.welcomeMessage.style.display = 'none';
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = text;
    
    const time = document.createElement('div');
    time.className = 'message-time';
    time.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    messageDiv.appendChild(bubble);
    messageDiv.appendChild(time);
    elements.conversation.appendChild(messageDiv);
    
    // Scroll to bottom
    elements.conversation.scrollTop = elements.conversation.scrollHeight;
}

function showTypingIndicator() {
    const id = 'typing_' + Date.now();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message agent';
    messageDiv.id = id;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble typing-indicator';
    bubble.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
    
    messageDiv.appendChild(bubble);
    elements.conversation.appendChild(messageDiv);
    elements.conversation.scrollTop = elements.conversation.scrollHeight;
    
    return id;
}

function removeTypingIndicator(id) {
    const typing = document.getElementById(id);
    if (typing) typing.remove();
}

// =============================================================================
// Business Selection
// =============================================================================

async function loadBusinesses() {
    try {
        const response = await fetch('/api/businesses');
        state.businesses = await response.json();
        renderBusinessCards();
    } catch (error) {
        console.error('Failed to load businesses:', error);
        showToast('Failed to load businesses', 'error');
    }
}

function renderBusinessCards() {
    elements.businessGrid.innerHTML = '';
    
    const descriptions = {
        hotel: 'Book rooms, check amenities, and get concierge assistance',
        restaurant: 'Make reservations, explore the menu, and plan your dining',
        clinic: 'Schedule appointments and get medical information',
        salon: 'Book haircuts, coloring, and beauty treatments',
        realestate: 'Find properties, schedule viewings, and get market insights',
        gym: 'Learn about memberships, classes, and fitness programs',
    };
    
    for (const [id, business] of Object.entries(state.businesses)) {
        const card = document.createElement('div');
        card.className = 'business-card';
        card.style.setProperty('--card-color', business.color);
        card.onclick = () => selectBusiness(id);
        
        card.innerHTML = `
            <span class="business-card-icon">${business.icon}</span>
            <h3 class="business-card-name">${business.name}</h3>
            <p class="business-card-description">${descriptions[id] || 'Call and interact with this business'}</p>
            <div class="business-card-cta">
                <span>Start Call</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
            </div>
        `;
        
        elements.businessGrid.appendChild(card);
    }
}

function selectBusiness(businessId) {
    state.currentBusiness = state.businesses[businessId];
    state.currentBusiness.id = businessId;
    
    // Update UI
    elements.currentBusinessIcon.textContent = state.currentBusiness.icon;
    elements.currentBusinessName.textContent = state.currentBusiness.name;
    
    // Update sample queries
    renderSampleQueries();
    
    // Show call interface
    elements.businessPanel.style.display = 'none';
    elements.callInterface.classList.add('active');
    
    // Generate new session
    state.sessionId = generateSessionId();
    
    // Clear conversation
    elements.conversation.innerHTML = '';
    if (elements.welcomeMessage) {
        elements.welcomeMessage.style.display = 'flex';
        elements.conversation.appendChild(elements.welcomeMessage);
    }
}

function renderSampleQueries() {
    elements.queryChips.innerHTML = '';
    
    if (state.currentBusiness?.sample_queries) {
        state.currentBusiness.sample_queries.forEach(query => {
            const chip = document.createElement('button');
            chip.className = 'query-chip';
            chip.textContent = query;
            chip.onclick = () => {
                elements.textInput.value = query;
                handleSendText();
            };
            elements.queryChips.appendChild(chip);
        });
    }
}

function goBack() {
    // End call if active
    if (state.isInCall) {
        endCall();
    }
    
    // Reset conversation
    resetConversation();
    
    // Show business panel
    elements.callInterface.classList.remove('active');
    elements.businessPanel.style.display = 'block';
    
    state.currentBusiness = null;
}

// =============================================================================
// Call Control
// =============================================================================

async function startCall() {
    // Request microphone access if not already granted
    if (!state.audioStream) {
        const granted = await initMicrophone();
        if (!granted) {
            showToast('Cannot start call without microphone', 'error');
            return;
        }
    }
    
    state.isInCall = true;
    elements.callButton.classList.add('active');
    elements.callButton.querySelector('.phone-icon').style.display = 'none';
    elements.callButton.querySelector('.hangup-icon').style.display = 'block';
    elements.muteButton.disabled = false;
    
    elements.callStatus.textContent = 'Connected';
    elements.callStatus.classList.add('active');
    
    // Hide sample queries during call
    elements.sampleQueries.classList.add('hidden');
    
    updateUI();
    
    // Play greeting
    if (state.currentBusiness?.greeting) {
        addMessage(state.currentBusiness.greeting, 'agent');
        speak(state.currentBusiness.greeting, () => {
            // Start listening after greeting
            if (!state.isMuted) {
                startRecording();
            }
        });
    } else {
        startRecording();
    }
}

function endCall() {
    state.isInCall = false;
    state.isListening = false;
    state.isSpeaking = false;
    
    stopRecording();
    state.synthesis.cancel();
    
    elements.callButton.classList.remove('active');
    elements.callButton.querySelector('.phone-icon').style.display = 'block';
    elements.callButton.querySelector('.hangup-icon').style.display = 'none';
    elements.muteButton.disabled = true;
    
    elements.callStatus.textContent = 'Call ended';
    elements.callStatus.classList.remove('active');
    
    // Show sample queries
    elements.sampleQueries.classList.remove('hidden');
    
    updateUI();
}

function toggleMute() {
    state.isMuted = !state.isMuted;
    
    const mutedIcon = elements.muteButton.querySelector('.muted-icon');
    const unmutedIcon = elements.muteButton.querySelector('.unmuted-icon');
    
    if (state.isMuted) {
        elements.muteButton.classList.add('active');
        mutedIcon.style.display = 'block';
        unmutedIcon.style.display = 'none';
        stopRecording();
    } else {
        elements.muteButton.classList.remove('active');
        mutedIcon.style.display = 'none';
        unmutedIcon.style.display = 'block';
        if (state.isInCall && !state.isSpeaking) {
            startRecording();
        }
    }
}

function toggleSpeaker() {
    state.speakerOn = !state.speakerOn;
    
    const onIcon = elements.speakerButton.querySelector('.speaker-on-icon');
    const offIcon = elements.speakerButton.querySelector('.speaker-off-icon');
    
    if (state.speakerOn) {
        elements.speakerButton.classList.remove('active');
        onIcon.style.display = 'block';
        offIcon.style.display = 'none';
    } else {
        elements.speakerButton.classList.add('active');
        onIcon.style.display = 'none';
        offIcon.style.display = 'block';
        state.synthesis.cancel();
    }
}

// =============================================================================
// Text Input Handling
// =============================================================================

function handleSendText() {
    const text = elements.textInput.value.trim();
    if (!text) return;
    
    elements.textInput.value = '';
    handleUserMessage(text);
}

// =============================================================================
// UI Updates
// =============================================================================

function updateUI() {
    // Update visualizer
    if (state.isInCall) {
        if (state.isSpeaking) {
            elements.visualizerContainer.classList.add('active', 'speaking');
            elements.visualizerLabel.textContent = 'Speaking...';
        } else if (state.isRecording || state.isListening) {
            elements.visualizerContainer.classList.add('active');
            elements.visualizerContainer.classList.remove('speaking');
            elements.visualizerLabel.textContent = 'Listening...';
        } else if (state.isMuted) {
            elements.visualizerContainer.classList.remove('active');
        } else {
            elements.visualizerContainer.classList.remove('active');
        }
    } else {
        elements.visualizerContainer.classList.remove('active', 'speaking');
    }
}

function showToast(message, type = 'info') {
    elements.toastMessage.textContent = message;
    elements.toast.className = `toast ${type} visible`;
    
    setTimeout(() => {
        elements.toast.classList.remove('visible');
    }, 3000);
}

// =============================================================================
// Event Listeners
// =============================================================================

function setupEventListeners() {
    // Back button
    elements.backButton.addEventListener('click', goBack);
    
    // Call button
    elements.callButton.addEventListener('click', () => {
        if (state.isInCall) {
            endCall();
        } else {
            startCall();
        }
    });
    
    // Mute button
    elements.muteButton.addEventListener('click', toggleMute);
    
    // Speaker button
    elements.speakerButton.addEventListener('click', toggleSpeaker);
    
    // Text input
    elements.textInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSendText();
        }
    });
    
    elements.sendButton.addEventListener('click', handleSendText);
    
    // Load voices when available
    if (state.synthesis.onvoiceschanged !== undefined) {
        state.synthesis.onvoiceschanged = () => {
            console.log('Voices loaded:', state.synthesis.getVoices().length);
        };
    }
}

// =============================================================================
// Initialization
// =============================================================================

async function init() {
    console.log('🎙️ Subconscious Voice Agent initializing...');
    
    // Setup event listeners
    setupEventListeners();
    
    // Load businesses
    await loadBusinesses();
    
    // Check API health
    await checkApiHealth();
    
    // Load voices
    state.synthesis.getVoices();
    
    console.log('✅ Voice Agent ready');
    console.log('💡 Microphone access will be requested when you start a call');
}

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', init);
