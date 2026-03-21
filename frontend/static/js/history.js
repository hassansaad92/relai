async function loadHistoryData() {
    document.getElementById('historyLoading').style.display = 'flex';
    document.getElementById('historyListContainer').innerHTML = '';
    const res = await fetch('/api/archive/scenarios');
    const scenarios = await res.json();
    document.getElementById('historyLoading').style.display = 'none';
    const container = document.getElementById('historyListContainer');
    if (!scenarios.length) {
        container.innerHTML = '<p style="padding:16px;color:#666;">No archived schedules yet. Promote a draft to archive the previous master.</p>';
        return;
    }
    const fmtDate = d => d ? new Date(d).toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'}) : '-';
    container.innerHTML = scenarios.map(s => `
        <div class="card" style="cursor:pointer;" onclick="toggleArchiveDetail('${s.scenario_id}', this)">
            <div class="card-header">
                <span class="card-title">${s.scenario_name}</span>
                <span class="card-status" style="background:#e0e2e6;color:#041e42;">${s.assignment_count} assignments</span>
            </div>
            <div style="font-size:12px;color:#666;">Archived ${fmtDate(s.archived_at)}</div>
            <div class="archive-detail" style="display:none;margin-top:10px;"></div>
        </div>
    `).join('');
}

async function toggleArchiveDetail(scenarioId, card) {
    const detail = card.querySelector('.archive-detail');
    if (detail.style.display !== 'none') {
        detail.style.display = 'none';
        return;
    }
    detail.innerHTML = '<span style="color:#999;">Loading...</span>';
    detail.style.display = 'block';
    try {
        const res = await fetch(`/api/archive/assignments?scenario_id=${scenarioId}`);
        const assignments = await res.json();
        const fmtDate = d => d ? new Date(d + 'T00:00:00').toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'}) : '-';
        detail.innerHTML = assignments.map(a =>
            `<div style="font-size:13px;padding:4px 0;border-bottom:1px solid #f0f0f0;">${a.personnel_name || 'Unknown'} &rarr; ${a.project_name || 'Unknown'} (${fmtDate(a.start_date)} &ndash; ${fmtDate(a.end_date)})</div>`
        ).join('');
        if (!assignments.length) detail.innerHTML = '<span style="color:#999;">No assignments found.</span>';
    } catch (err) {
        detail.innerHTML = '<span style="color:red;">Failed to load assignments.</span>';
    }
}

viewLoaders.history = loadHistoryData;
