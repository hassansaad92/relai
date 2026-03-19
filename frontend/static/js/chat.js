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

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('chatInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });
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
