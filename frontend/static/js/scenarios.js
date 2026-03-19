async function loadScenarios() {
    const res = await fetch('/api/scenarios');
    allScenarios = await res.json();
    if (!currentScenarioId) {
        const master = allScenarios.find(s => s.status === 'master');
        if (master) currentScenarioId = master.id;
    }
    updateScenarioIndicator();
    renderScenarioPanel();
}

function updateScenarioIndicator() {
    const current = allScenarios.find(s => s.id === currentScenarioId);
    if (!current) return;
    document.getElementById('scenarioDot').className = `scenario-dot ${current.status}`;
    document.getElementById('scenarioIndicatorName').textContent = current.name;
}

function renderScenarioPanel() {
    const drafts = allScenarios.filter(s => s.status === 'draft');
    document.getElementById('scenarioList').innerHTML = allScenarios.map(s => `
        <div class="scenario-item ${s.id === currentScenarioId ? 'active-view' : ''}">
            <span class="scenario-dot ${s.status}"></span>
            <span class="scenario-item-name" onclick="switchScenario('${s.id}')">${s.name}</span>
            <span class="scenario-item-badge ${s.status}">${s.status}</span>
            ${s.status === 'draft' ? `
                <div class="scenario-item-actions">
                    <button class="scenario-action-btn" onclick="promoteScenario('${s.id}')">Promote</button>
                    <button class="scenario-action-btn danger" onclick="deleteScenario('${s.id}')">×</button>
                </div>` : ''}
        </div>
    `).join('');
    // Hide New Draft button when a draft already exists
    document.getElementById('newDraftBtn').style.display = drafts.length > 0 ? 'none' : '';
}

function toggleScenarioPanel() {
    document.getElementById('scenarioPanel').classList.toggle('active');
}

document.addEventListener('click', (e) => {
    const panel = document.getElementById('scenarioPanel');
    const indicator = document.getElementById('scenarioIndicator');
    if (panel.classList.contains('active') && !panel.contains(e.target) && !indicator.contains(e.target)) {
        panel.classList.remove('active');
    }
});

async function switchScenario(id) {
    currentScenarioId = id;
    clearHomeCache();
    updateScenarioIndicator();
    renderScenarioPanel();
    document.getElementById('scenarioPanel').classList.remove('active');
    await viewLoaders[currentView]();
}

async function createDraft() {
    const name = window.prompt('Draft name:', `Draft – ${new Date().toLocaleDateString('en-US', {month: 'short', day: 'numeric', year: 'numeric'})}`);
    if (!name) return;
    try {
        const res = await fetch('/api/scenarios', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        if (!res.ok) { alert((await res.json()).detail); return; }
        await loadScenarios();
    } catch (err) {
        alert('Failed to create draft: ' + err.message);
    }
}

async function promoteScenario(id) {
    if (!confirm('Promote this draft to master? The current master will be archived to History.')) return;
    try {
        const res = await fetch(`/api/scenarios/${id}/promote`, { method: 'POST' });
        if (!res.ok) throw new Error(await res.text());
        currentScenarioId = id;
        await loadScenarios();
        await viewLoaders[currentView]();
    } catch (err) {
        alert('Failed to promote: ' + err.message);
    }
}

async function deleteScenario(id) {
    if (!confirm('Delete this draft? This cannot be undone.')) return;
    try {
        const res = await fetch(`/api/scenarios/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error(await res.text());
        if (currentScenarioId === id) {
            const master = allScenarios.find(s => s.status === 'master');
            if (master) currentScenarioId = master.id;
        }
        await loadScenarios();
        await viewLoaders[currentView]();
    } catch (err) {
        alert('Failed to delete: ' + err.message);
    }
}
