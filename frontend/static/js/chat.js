function appendChatMessage(role, text) {
    const container = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = `chat-msg ${role}`;
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    if (role === 'assistant') {
        bubble.innerHTML = marked.parse(text);
    } else {
        bubble.textContent = text;
    }
    div.appendChild(bubble);
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
}

function showTyping() {
    const container = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = 'chat-msg assistant chat-typing';
    div.innerHTML = '<div class="chat-bubble">Thinking...</div>';
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const sendBtn = document.getElementById('chatSendBtn');
    const message = input.value.trim();
    if (!message) return;

    input.value = '';
    sendBtn.disabled = true;

    appendChatMessage('user', message);
    chatHistory.push({ role: 'user', content: message });

    const typingEl = showTyping();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages: chatHistory })
        });
        if (!response.ok) throw new Error('Request failed');
        const data = await response.json();
        typingEl.remove();
        appendChatMessage('assistant', data.response);
        chatHistory.push({ role: 'assistant', content: data.response });

        // Auto-switch to new draft if schedule was created
        if (data.schedule_created && data.scenario_id) {
            await loadScenarios();
            await switchScenario(data.scenario_id);
            // Switch to Schedule view if not already there
            if (currentView !== 'schedule') {
                document.querySelector(`.tab-btn[data-view="schedule"]`).click();
            }
            showScheduleNotification(`AI draft '${data.scenario_name}' created. Viewing now.`);
        }
    } catch (err) {
        typingEl.remove();
        appendChatMessage('assistant', 'Sorry, I encountered an error. Please try again.');
        chatHistory.pop();
    } finally {
        sendBtn.disabled = false;
        input.focus();
    }
}

// ── Voice Input ──────────────────────────────────────────────────────────────
let _recognition = null;
let _isRecording = false;

function initVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const micBtn = document.getElementById('chatMicBtn');
    micBtn.style.display = 'flex';

    _recognition = new SpeechRecognition();
    _recognition.continuous = true;
    _recognition.interimResults = true;
    _recognition.lang = 'en-US';

    _recognition.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';
        for (let i = 0; i < event.results.length; i++) {
            const result = event.results[i];
            if (result.isFinal) {
                finalTranscript += result[0].transcript;
            } else {
                interimTranscript += result[0].transcript;
            }
        }
        document.getElementById('chatInput').value = finalTranscript + interimTranscript;
    };

    _recognition.onend = () => {
        // Auto-restart if still in recording mode (browser stops after silence)
        if (_isRecording) {
            try { _recognition.start(); } catch (e) { stopVoiceInput(); }
        }
    };

    _recognition.onerror = () => {
        stopVoiceInput();
    };
}

function toggleVoiceInput() {
    if (_isRecording) {
        stopVoiceInput();
    } else {
        startVoiceInput();
    }
}

function startVoiceInput() {
    if (!_recognition) return;
    _isRecording = true;
    document.getElementById('chatMicBtn').classList.add('recording');
    document.getElementById('chatInput').value = '';
    try { _recognition.start(); } catch (e) { /* already started */ }
}

function stopVoiceInput() {
    _isRecording = false;
    document.getElementById('chatMicBtn').classList.remove('recording');
    if (_recognition) {
        try { _recognition.stop(); } catch (e) { /* not started */ }
    }
    document.getElementById('chatInput').focus();
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('chatInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });
    initVoiceInput();
});

// Chat panel toggle
function toggleChatPanel() {
    const panel = document.getElementById('chatPanel');
    panel.classList.toggle('collapsed');
    document.body.classList.toggle('chat-collapsed');
    // Resize Plotly chart after panel transition
    setTimeout(() => {
        const gantt = document.getElementById('ganttChart');
        if (gantt && gantt.data) Plotly.Plots.resize('ganttChart');
    }, 300);
}
