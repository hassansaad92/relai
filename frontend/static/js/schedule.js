async function loadScheduleData() {
    document.getElementById('scheduleLoading').style.display = 'flex';
    const [overviewRes, personnelRes, projectsRes, schedProjectsRes, assignmentsRes] = await Promise.all([
        fetch(`/api/assignments/overview?scenario_id=${currentScenarioId}`),
        fetch(`/api/personnel?scenario_id=${currentScenarioId}`),
        fetch(`/api/projects?scenario_id=${currentScenarioId}`),
        fetch(`/api/assignments/schedule-projects?scenario_id=${currentScenarioId}`),
        fetch(`/api/assignments?scenario_id=${currentScenarioId}`)
    ]);
    const overviewAssignments = await overviewRes.json();
    allPersonnel = await personnelRes.json();
    allProjects = await projectsRes.json();
    const schedProjects = await schedProjectsRes.json();
    allAssignments = await assignmentsRes.json();
    document.getElementById('scheduleLoading').style.display = 'none';
    // Use schedule-projects for the project list (has assignment_count)
    allProjects = schedProjects;
    renderGantt(overviewAssignments, allPersonnel, allProjects);
    renderAssignmentsList();
    renderScheduleProjects();
}

// Build daily allocation map: { personnelId: { 'YYYY-MM-DD': totalAllocated } }
function buildDailyAllocationMap(assignments) {
    const map = {};
    for (const a of assignments) {
        if (!map[a.personnel_id]) map[a.personnel_id] = {};
        const personMap = map[a.personnel_id];
        const start = new Date(a.start_date + 'T00:00:00');
        const end = new Date(a.end_date + 'T00:00:00');
        const alloc = parseFloat(a.allocated_days) || 1.0;
        for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
            const key = d.toISOString().split('T')[0];
            personMap[key] = (personMap[key] || 0) + alloc;
        }
    }
    return map;
}

// Render Gantt chart with Plotly
function renderGantt(assignments, personnel, projects) {
    // Detect overbooked assignments using daily allocation map
    const allocMap = buildDailyAllocationMap(assignments);
    const doubleBookedIds = new Set();
    for (let i = 0; i < assignments.length; i++) {
        const a = assignments[i];
        const personMap = allocMap[a.personnel_id] || {};
        const start = new Date(a.start_date + 'T00:00:00');
        const end = new Date(a.end_date + 'T00:00:00');
        for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
            const key = d.toISOString().split('T')[0];
            if ((personMap[key] || 0) > 1.0) {
                doubleBookedIds.add(i);
                break;
            }
        }
    }

    const traces = assignments.map((a, idx) => {
        const label = lastFirstName(a.personnel_name || 'Unknown');
        const projectName = a.project_name || 'Unknown';
        const isCurrent = a.sequence === 1 || a.sequence === '1';
        const isDoubleBooked = doubleBookedIds.has(idx);
        const exceedsCommitted = (a.committed_start_date && a.start_date > a.committed_start_date) ||
            (a.committed_end_date && a.end_date > a.committed_end_date);
        const barColor = isDoubleBooked ? '#e8890a' : (exceedsCommitted ? '#c0392b' : (isCurrent ? '#041e42' : '#6b9fd4'));
        const textColor = '#ffffff';
        const alloc = parseFloat(a.allocated_days) || 1.0;
        const barWidth = alloc < 1.0 ? 0.3 : 0.6;

        return {
            type: 'bar',
            orientation: 'h',
            y: [label],
            x: [new Date(a.end_date) - new Date(a.start_date) + 86400000],
            base: [a.start_date],
            width: [barWidth],
            name: projectName,
            text: [projectName],
            textposition: 'inside',
            insidetextanchor: 'middle',
            textfont: { color: textColor, size: 11, family: 'Montserrat, sans-serif' },
            hovertemplate: '<b>%{text}</b><br>%{y}<br>%{base|%b %d, %Y} \u2192 ' +
                new Date(a.end_date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) +
                '<extra></extra>',
            marker: {
                color: barColor,
                line: { width: 1, color: '#ffffff' }
            },
            showlegend: false,
        };
    });

    // Compute date range for x-axis with padding
    const allDates = assignments.flatMap(a => [new Date(a.start_date), new Date(a.end_date)]);
    allDates.push(currentDate);
    const minDate = new Date(Math.min(...allDates));
    const maxDate = new Date(Math.max(...allDates));
    const rangeSpanDays = (maxDate - minDate) / (1000 * 60 * 60 * 24);
    // Pad range by 10% on each side, minimum 2 days
    const padDays = Math.max(2, Math.ceil(rangeSpanDays * 0.1));
    const xStart = new Date(minDate);
    xStart.setDate(xStart.getDate() - padDays);
    const xEnd = new Date(maxDate);
    xEnd.setDate(xEnd.getDate() + padDays);

    const layout = {
        barmode: 'overlay',
        xaxis: {
            type: 'date',
            title: '',
            showline: true,
            linecolor: '#E0E2E6',
            gridcolor: getComputedStyle(document.documentElement).getPropertyValue('--surface-border').trim(),
            tickfont: { family: 'Montserrat, sans-serif', size: 11 },
            range: [xStart.toISOString().split('T')[0], xEnd.toISOString().split('T')[0]],
        },
        yaxis: {
            autorange: 'reversed',
            tickfont: { family: 'Montserrat, sans-serif', size: 11, color: '#041e42' },
            fixedrange: true,
        },
        bargap: 0.2,
        height: Math.max(250, assignments.length * 28 + 80),
        margin: { l: 130, r: 20, t: 10, b: 40 },
        font: { family: 'Montserrat, sans-serif' },
        plot_bgcolor: '#ffffff',
        paper_bgcolor: '#ffffff',
        shapes: [{
            type: 'line',
            xref: 'x',
            yref: 'paper',
            x0: currentDate.toISOString().split('T')[0],
            x1: currentDate.toISOString().split('T')[0],
            y0: 0,
            y1: 1,
            line: { color: '#000000', width: 1.5, dash: 'dash' },
            layer: 'above',
        }],
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['select2d', 'lasso2d', 'autoScale2d'],
        scrollZoom: false,
        displaylogo: false,
    };

    Plotly.newPlot('ganttChart', traces, layout, config);

    // Gantt bar click → select project in schedule panel
    const ganttEl = document.getElementById('ganttChart');
    ganttEl._projectIds = assignments.map(a => a.project_id);
    ganttEl.on('plotly_click', function(data) {
        if (data.points && data.points.length > 0) {
            const idx = data.points[0].curveNumber;
            const projectId = ganttEl._projectIds[idx];
            if (projectId) {
                selectScheduleProject(projectId);
            }
        }
    });
}

function renderAssignmentsList() {
    const container = document.getElementById('assignmentsTableContainer');
    if (!container) return;
    const fmtDate = d => d ? new Date(d + 'T00:00:00').toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'}) : '-';

    const rows = [...allPersonnel].sort((a, b) => getLastName(a.name).localeCompare(getLastName(b.name))).map(person => {
        const currentProject = person.current_project_name || '-';
        const completion = person.current_assignment_end ? fmtDate(person.current_assignment_end) : '-';
        const nextProject = person.next_project_name || '-';
        const reqStart = person.next_project_committed_start ? fmtDate(person.next_project_committed_start) : '-';

        let gapCell = '-';
        if (person.current_assignment_end && person.next_project_committed_start) {
            const endMs = new Date(person.current_assignment_end + 'T00:00:00');
            const startMs = new Date(person.next_project_committed_start + 'T00:00:00');
            const days = Math.round((endMs - startMs) / 86400000);
            if (days > 0) {
                gapCell = `<span style="color:#C20000;font-weight:600">+${days}d late</span>`;
            } else if (days < 0) {
                gapCell = `<span style="color:#27ae60">${days}d</span>`;
            } else {
                gapCell = `<span style="color:#999">0d</span>`;
            }
        }

        return `<tr>
            <td>${lastFirstName(person.name)}</td>
            <td>${currentProject}</td>
            <td>${completion}</td>
            <td>${nextProject}</td>
            <td>${reqStart}</td>
            <td>${gapCell}</td>
        </tr>`;
    });

    container.innerHTML = `
        <table class="assignments-table">
            <thead>
                <tr>
                    <th>Personnel</th>
                    <th>Current Project</th>
                    <th>Completion</th>
                    <th>Next Project</th>
                    <th>Contract Start</th>
                    <th>Gap</th>
                </tr>
            </thead>
            <tbody>${rows.join('')}</tbody>
        </table>
    `;
}

function renderScheduleProjects() {
    const container = document.getElementById('scheduleProjectsList');
    const fmtDate = d => d ? new Date(d + 'T00:00:00').toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'}) : '';
    const sorted = [...allProjects].sort((a, b) => {
        const aDate = a.committed_start_date || '9999-12-31';
        const bDate = b.committed_start_date || '9999-12-31';
        return aDate.localeCompare(bDate);
    });

    // Separate selected project (renders full-width) from the grid
    const selectedProject = selectedScheduleProjectId ? sorted.find(p => p.id === selectedScheduleProjectId) : null;

    const renderCard = (p) => {
        const schedStatus = p.schedule_status || 'not_scheduled';
        const count = p.assignment_count != null ? p.assignment_count : allAssignments.filter(a => a.project_id === p.id).length;
        const isSelected = p.id === selectedScheduleProjectId;
        const skillTags = p.required_skills ? p.required_skills.split(',').map(s =>
            `<span class="skills-tag-light">${s.trim()}</span>`
        ).join('') : '';
        const committedDates = p.committed_start_date
            ? (p.committed_start_date === p.committed_end_date
                ? fmtDate(p.committed_start_date)
                : `${fmtDate(p.committed_start_date)} – ${fmtDate(p.committed_end_date)}`)
            : 'Not set';
        const actualDates = p.actual_start_date
            ? (p.actual_start_date === p.actual_end_date
                ? fmtDate(p.actual_start_date)
                : `${fmtDate(p.actual_start_date)} – ${fmtDate(p.actual_end_date)}`)
            : '--';

        // Red highlight if scheduled dates exceed committed dates
        const isOverCommitted = p.committed_start_date && p.actual_start_date && (
            p.actual_start_date > p.committed_start_date ||
            (p.committed_end_date && p.actual_end_date && p.actual_end_date > p.committed_end_date)
        );
        const cardStyle = isOverCommitted ? 'border-left: 3px solid #c0392b;' : '';

        return `
            <div class="schedule-project-card ${isSelected ? 'selected' : ''}"
                 style="${cardStyle}"
                 onclick="selectScheduleProject('${p.id}')">
                <div class="card-header">
                    <div style="display:flex;align-items:center;gap:6px;flex:1;min-width:0;">
                        <div class="card-title">${p.name}</div>
                    </div>
                    <div class="status-badges">
                        <div class="card-status ${p.award_status}">${p.award_status.replace('_', ' ')}</div>
                        <div class="card-status ${schedStatus}">${schedStatus.replace('_', ' ')}</div>
                    </div>
                </div>
                <div class="card-detail" style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                    <span>${p.duration_days}d</span>
                    <span style="color:#ccc;">|</span>
                    <span>${count} assigned</span>
                    ${skillTags}
                </div>
                <div class="card-detail"><strong>Committed:</strong> ${committedDates} · <strong>Scheduled:</strong> ${actualDates}</div>
            </div>`;
    };

    // Render all cards in grid; selected card gets assign panel below it
    const cards = sorted.map(p => {
        let card = renderCard(p);
        if (p.id === selectedScheduleProjectId) {
            card += `<div class="schedule-assign-inline" id="scheduleAssignPanel"></div>`;
        }
        return `<div class="schedule-project-wrapper">${card}</div>`;
    }).join('');

    container.innerHTML = `<div class="schedule-projects-grid">${cards}</div>`;
    if (selectedScheduleProjectId) {
        renderScheduleAssignPanel(selectedScheduleProjectId);
    }
}

function selectScheduleProject(projectId) {
    selectedScheduleProjectId = selectedScheduleProjectId === projectId ? null : projectId;
    assignFormPersonnelId = null;
    renderScheduleProjects();
}

function renderScheduleAssignPanel(projectId) {
    const panel = document.getElementById('scheduleAssignPanel');
    const project = allProjects.find(p => p.id === projectId);
    if (!project) return;

    // Use committed dates if available, else default to today + duration
    const today = new Date().toISOString().split('T')[0];
    const projectStartStr = project.committed_start_date || today;
    const projectEndStr = project.committed_end_date || (() => {
        const d = new Date(projectStartStr + 'T00:00:00');
        d.setDate(d.getDate() + Math.ceil(parseFloat(project.duration_days) || 1) - 1);
        return d.toISOString().split('T')[0];
    })();
    const projectStart = new Date(projectStartStr + 'T00:00:00');
    const projectEnd = new Date(projectEndStr + 'T00:00:00');

    const fmtShort = d => d ? new Date(d + 'T00:00:00').toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'}) : '';
    const startFmt = fmtShort(projectStartStr);
    const endFmt = fmtShort(projectEndStr);

    const schedStatus = project.schedule_status || 'not_scheduled';
    const projectAssignments = allAssignments.filter(a => a.project_id === projectId);
    const assignedIds = new Set(projectAssignments.map(a => a.personnel_id));

    const free = [];
    const allocMap = buildDailyAllocationMap(allAssignments);
    allPersonnel.forEach(person => {
        if (assignedIds.has(person.id)) return;
        // Capacity-based: person is available only if ALL days in window have totalAllocated < 1.0
        const personMap = allocMap[person.id] || {};
        let fullyAvailable = true;
        for (let d = new Date(projectStart); d <= projectEnd; d.setDate(d.getDate() + 1)) {
            const key = d.toISOString().split('T')[0];
            if ((personMap[key] || 0) >= 1.0) {
                fullyAvailable = false;
                break;
            }
        }
        if (fullyAvailable) free.push(person);
    });
    free.sort((a, b) => a.name.localeCompare(b.name));

    const assignedHTML = projectAssignments.length === 0
        ? '<p class="no-assignments-msg">No one assigned yet.</p>'
        : projectAssignments.map(a => {
            const pName = a.personnel_name || a.personnel_id;
            const alloc = parseFloat(a.allocated_days) || 1.0;
            const allocLabel = alloc !== 1.0 ? ` [${alloc} day]` : '';
            const typeLabel = (a.assignment_type && a.assignment_type !== 'full' ? ` (${a.assignment_type})` : '') + allocLabel;
            return `<div class="schedule-person-row" style="flex-wrap:wrap;">
                <div class="schedule-person-name">${pName}</div>
                <div class="schedule-person-info">${fmtShort(a.start_date)} – ${fmtShort(a.end_date)}${typeLabel}</div>
                <button class="schedule-remove-btn" onclick="scheduleRemove('${a.id}')">×</button>
                <div class="schedule-date-edit-row" style="width:100%;margin-top:4px;margin-bottom:4px;">
                    <label>Start</label>
                    <input type="date" value="${a.start_date}" id="editAssignStart_${a.id}">
                    <label>End</label>
                    <input type="date" value="${a.end_date}" id="editAssignEnd_${a.id}">
                    <button onclick="saveAssignmentDates('${a.id}')">Update</button>
                </div>
            </div>`;
        }).join('');

    const makeAssignForm = (pid) => {
        const person = allPersonnel.find(p => p.id === pid);
        const personAvail = person?.next_available_date || '';
        const effStart = personAvail > projectStartStr ? personAvail : projectStartStr;
        const effEnd = new Date(effStart + 'T00:00:00');
        effEnd.setDate(effEnd.getDate() + project.duration_days - 1);
        const effEndStr = effEnd.toISOString().split('T')[0];
        const effStartFmt = fmtShort(effStart);
        const effEndFmt = effEnd.toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'});
        return `
        <div class="assign-date-form">
            <div class="form-group" style="margin-bottom:10px;">
                <label style="font-size:12px;font-weight:600;color:#041e42;margin-bottom:4px;display:block;">Assignment Type</label>
                <select id="assignType_${pid}" style="font-size:13px;padding:4px 6px;border:1px solid #ccc;border-radius:4px;font-family:'Montserrat',sans-serif;" onchange="updateAssignDefaults('${pid}', '${projectStartStr}', '${projectEndStr}', '${personAvail}', ${project.duration_days})">
                    <option value="full">Full alignment</option>
                    <option value="cascading">Cascading</option>
                    <option value="partial">Custom</option>
                </select>
            </div>
            <div class="assign-date-defaults" id="assignDefaults_${pid}">Default: ${effStartFmt} – ${effEndFmt}</div>
            <label class="custom-date-toggle" id="customToggleLabel_${pid}" style="display:none;">
                <input type="checkbox" id="customToggle_${pid}" onchange="toggleCustomDates('${pid}')"> Use custom dates
            </label>
            <div class="assign-custom-fields" id="customFields_${pid}">
                <input type="date" id="customStart_${pid}" value="${effStart}">
                <span style="font-size:13px;color:#666;">–</span>
                <input type="date" id="customEnd_${pid}" value="${effEndStr}">
            </div>
            <div class="assign-form-actions">
                <button class="schedule-action-btn" onclick="scheduleConfirmAssign('${pid}', '${effStart}', '${effEndStr}')">Confirm</button>
                <button class="schedule-action-btn outline" onclick="cancelAssignForm()">Cancel</button>
            </div>
        </div>`;
    };

    const freeHTML = free.length === 0
        ? '<p class="no-assignments-msg">No one available during this period.</p>'
        : free.map(p => `<div class="schedule-person-row">
            <div class="schedule-person-name">${p.name}</div>
            <div class="schedule-person-info"></div>
            <button class="schedule-action-btn" onclick="scheduleShowAssignForm('${p.id}')">+ Assign</button>
        </div>${assignFormPersonnelId === p.id ? makeAssignForm(p.id) : ''}`).join('');

    // Build "All Personnel" section (everyone not already assigned or listed as available)
    const availableIds = new Set(free.map(p => p.id));
    const allOthers = allPersonnel.filter(p => !assignedIds.has(p.id) && !availableIds.has(p.id));
    allOthers.sort((a, b) => a.name.localeCompare(b.name));

    const allPersonnelHTML = allOthers.length === 0
        ? '<p class="no-assignments-msg">No additional personnel.</p>'
        : allOthers.map(p => {
            // Find overlapping assignments to explain why they're unavailable
            const theirAssignments = allAssignments.filter(a => a.personnel_id === p.id)
                .sort((a, b) => new Date(a.start_date) - new Date(b.start_date));
            const overlapping = theirAssignments.filter(a =>
                new Date(a.start_date) <= projectEnd && new Date(a.end_date) >= projectStart
            );
            let statusText = '';
            if (overlapping.length > 0) {
                statusText = overlapping.map(a => {
                    const proj = allProjects.find(pr => pr.id === a.project_id);
                    return `${proj ? proj.name : 'project'} (${fmtShort(a.start_date)} – ${fmtShort(a.end_date)})`;
                }).join(', ');
            }
            return `<div class="schedule-person-row force-assign-row">
                <div class="schedule-person-name">${p.name}</div>
                <div class="schedule-person-info" style="color:#b35900;">${statusText}</div>
                <button class="schedule-action-btn" style="background:#b35900;" onclick="scheduleShowAssignForm('${p.id}')">+ Force Assign</button>
            </div>${assignFormPersonnelId === p.id ? makeAssignForm(p.id) : ''}`;
        }).join('');

    panel.innerHTML = `
        <div id="scheduleConflictAlerts_${projectId}"></div>
        <div class="schedule-section-label" style="margin-top:0;">Assigned</div>
        ${assignedHTML}
        <div class="schedule-section-label">Available</div>
        ${freeHTML}
        <div class="schedule-section-label">All Personnel</div>
        <input type="text" class="filter-search" id="forceAssignSearch_${projectId}" placeholder="Search personnel..." oninput="filterForceAssign('${projectId}')" style="margin-bottom:8px;">
        <div id="forceAssignList_${projectId}">${allPersonnelHTML}</div>`;
}

async function saveAssignmentDates(assignmentId) {
    const startInput = document.getElementById('editAssignStart_' + assignmentId);
    const endInput = document.getElementById('editAssignEnd_' + assignmentId);
    if (!startInput || !endInput) return;
    try {
        // Update start date via PATCH if changed
        if (startInput.value) {
            const assignment = allAssignments.find(a => a.id === assignmentId);
            if (assignment && startInput.value !== assignment.start_date) {
                const res = await fetch(`/api/assignments/${assignmentId}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ start_date: startInput.value })
                });
                if (!res.ok) throw new Error(await res.text());
            }
        }
        // Update end date via cascade endpoint (pushes subsequent assignments)
        if (endInput.value) {
            const assignment = allAssignments.find(a => a.id === assignmentId);
            if (assignment && endInput.value !== assignment.end_date) {
                const res = await fetch(`/api/assignments/${assignmentId}/cascade`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ new_end_date: endInput.value, scenario_id: currentScenarioId })
                });
                if (!res.ok) throw new Error(await res.text());
            }
        }
        await loadScheduleData();
        if (selectedScheduleProjectId) checkScheduleConflicts(selectedScheduleProjectId);
    } catch (err) {
        alert('Failed to update assignment dates: ' + err.message);
    }
}

function filterForceAssign(projectId) {
    const search = (document.getElementById('forceAssignSearch_' + projectId)?.value || '').toLowerCase();
    const container = document.getElementById('forceAssignList_' + projectId);
    if (!container) return;
    const rows = container.querySelectorAll('.force-assign-row');
    rows.forEach(row => {
        const name = row.querySelector('.schedule-person-name')?.textContent?.toLowerCase() || '';
        row.style.display = name.includes(search) ? '' : 'none';
    });
}

function checkScheduleConflicts(projectId) {
    const container = document.getElementById('scheduleConflictAlerts_' + projectId);
    if (!container) return;
    const project = allProjects.find(p => p.id === projectId);
    if (!project) return;

    const projectAssignments = allAssignments.filter(a => a.project_id === projectId);
    const fmtShort = d => d ? new Date(d + 'T00:00:00').toLocaleDateString('en-US', {month:'short', day:'numeric'}) : '';
    const conflicts = [];
    const gaps = [];

    const allocMap = buildDailyAllocationMap(allAssignments);
    projectAssignments.forEach(pa => {
        const paStart = new Date(pa.start_date);
        const paEnd = new Date(pa.end_date);
        const personName = pa.personnel_name || pa.personnel_id;

        // Check for capacity overflows (combined allocated_days > 1.0 on any day)
        const personMap = allocMap[pa.personnel_id] || {};
        const overbookedDays = [];
        for (let d = new Date(paStart); d <= paEnd; d.setDate(d.getDate() + 1)) {
            const key = d.toISOString().split('T')[0];
            if ((personMap[key] || 0) > 1.0) {
                overbookedDays.push(key);
            }
        }
        if (overbookedDays.length > 0) {
            // Find what other assignments overlap on those days
            allAssignments.forEach(other => {
                if (other.id === pa.id || other.personnel_id !== pa.personnel_id) return;
                const otherStart = new Date(other.start_date);
                const otherEnd = new Date(other.end_date);
                if (otherStart <= paEnd && otherEnd >= paStart) {
                    const otherProject = allProjects.find(p => p.id === other.project_id);
                    const otherName = otherProject ? otherProject.name : other.project_id;
                    conflicts.push(`${personName} is overbooked with ${otherName} (${overbookedDays.length} days over capacity)`);
                }
            });
        }

        // Check for gaps between this person's current assignment end and contract start
        if (project.committed_start_date) {
            const contractStart = new Date(project.committed_start_date + 'T00:00:00');
            const otherAssignments = allAssignments.filter(a =>
                a.personnel_id === pa.personnel_id && a.id !== pa.id && new Date(a.end_date) <= contractStart
            ).sort((a, b) => new Date(b.end_date) - new Date(a.end_date));

            if (otherAssignments.length > 0) {
                const prevEnd = new Date(otherAssignments[0].end_date + 'T00:00:00');
                const gapDays = Math.round((contractStart - prevEnd) / 86400000);
                if (gapDays > 14) {
                    const prevProject = allProjects.find(p => p.id === otherAssignments[0].project_id);
                    const prevName = prevProject ? prevProject.name : 'previous project';
                    gaps.push(`${personName} has a ${gapDays}-day gap between ${prevName} (ends ${fmtShort(otherAssignments[0].end_date)}) and this project (contract start ${fmtShort(project.committed_start_date)})`);
                }
            }
        }
    });

    let html = '';
    if (conflicts.length > 0) {
        html += `<div class="schedule-conflict-alert">${conflicts.map(c => `<div>&#9888; ${c}</div>`).join('')}</div>`;
    }
    if (gaps.length > 0) {
        html += `<div class="schedule-gap-alert">${gaps.map(g => `<div>&#8505; ${g}</div>`).join('')}</div>`;
    }
    container.innerHTML = html;
}

async function scheduleAssign(personnelId, startDate, endDate, assignmentType = 'full', allocatedDays = 1.0) {
    const existing = allAssignments
        .filter(a => a.personnel_id === personnelId)
        .sort((a, b) => new Date(a.start_date) - new Date(b.start_date));
    let sequence = 1;
    for (const a of existing) {
        if (new Date(a.start_date) <= new Date(startDate)) sequence++;
    }
    try {
        const res = await fetch('/api/assignments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                personnel_id: personnelId,
                project_id: selectedScheduleProjectId,
                scenario_id: currentScenarioId,
                sequence,
                start_date: startDate,
                end_date: endDate,
                allocated_days: allocatedDays,
                assignment_type: assignmentType,
            })
        });
        if (!res.ok) throw new Error(await res.text());
        await loadScheduleData();
    } catch (err) {
        alert('Failed to assign: ' + err.message);
    }
}

function scheduleShowAssignForm(personnelId) {
    assignFormPersonnelId = personnelId;
    renderScheduleAssignPanel(selectedScheduleProjectId);
}

function toggleCustomDates(personnelId) {
    const checked = document.getElementById('customToggle_' + personnelId).checked;
    document.getElementById('customFields_' + personnelId).style.display = checked ? 'flex' : 'none';
}

async function scheduleConfirmAssign(personnelId, defaultStart, defaultEnd) {
    const toggle = document.getElementById('customToggle_' + personnelId);
    const typeSelect = document.getElementById('assignType_' + personnelId);
    const assignmentType = typeSelect ? typeSelect.value : 'full';
    // Derive allocated_days from project duration: half-day projects get 0.5
    const project = allProjects.find(p => p.id === selectedScheduleProjectId);
    const projDuration = project ? parseFloat(project.duration_days) : 1;
    const allocatedDays = projDuration <= 0.5 ? 0.5 : 1.0;
    let startDate = defaultStart;
    let endDate = defaultEnd;
    if (assignmentType === 'partial' || (toggle && toggle.checked)) {
        startDate = document.getElementById('customStart_' + personnelId).value || defaultStart;
        endDate = document.getElementById('customEnd_' + personnelId).value || defaultEnd;
    }
    assignFormPersonnelId = null;
    await scheduleAssign(personnelId, startDate, endDate, assignmentType, allocatedDays);
}

function updateAssignDefaults(pid, projectStart, projectEnd, personAvail, durationDays) {
    const typeSelect = document.getElementById('assignType_' + pid);
    const type = typeSelect.value;
    const defaultsEl = document.getElementById('assignDefaults_' + pid);
    const startInput = document.getElementById('customStart_' + pid);
    const endInput = document.getElementById('customEnd_' + pid);
    const fmtD = d => new Date(d + 'T00:00:00').toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'});

    let effStart, effEndStr;
    if (type === 'full') {
        effStart = projectStart;
        const effEnd = new Date(projectStart + 'T00:00:00');
        effEnd.setDate(effEnd.getDate() + durationDays - 1);
        effEndStr = effEnd.toISOString().split('T')[0];
    } else if (type === 'cascading') {
        effStart = personAvail > projectStart ? personAvail : projectStart;
        const effEnd = new Date(effStart + 'T00:00:00');
        effEnd.setDate(effEnd.getDate() + durationDays - 1);
        effEndStr = effEnd.toISOString().split('T')[0];
    } else {
        effStart = projectStart;
        effEndStr = projectEnd;
    }
    if (defaultsEl) defaultsEl.textContent = `Default: ${fmtD(effStart)} – ${fmtD(effEndStr)}`;
    if (startInput) startInput.value = effStart;
    if (endInput) endInput.value = effEndStr;

    // For custom (partial), show date fields directly; for others, hide them
    const customFields = document.getElementById('customFields_' + pid);
    const toggleLabel = document.getElementById('customToggleLabel_' + pid);
    if (toggleLabel) toggleLabel.style.display = 'none';
    if (customFields) customFields.style.display = type === 'partial' ? 'flex' : 'none';
}

function cancelAssignForm() {
    assignFormPersonnelId = null;
    renderScheduleAssignPanel(selectedScheduleProjectId);
}

async function scheduleRemove(assignmentId) {
    try {
        const res = await fetch('/api/assignments/' + assignmentId, { method: 'DELETE' });
        if (!res.ok) throw new Error(await res.text());
        await loadScheduleData();
    } catch (err) {
        alert('Failed to remove: ' + err.message);
    }
}

function setGanttMode(mode) {
    ganttMode = mode;
    document.querySelectorAll('.gantt-toggle-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });
    document.getElementById('ganttChart').style.display = mode === 'timeline' ? 'block' : 'none';
    document.getElementById('assignmentsTableContainer').style.display = mode === 'table' ? 'block' : 'none';
    if (mode === 'timeline') {
        Plotly.Plots.resize('ganttChart');
    }
}

function toggleGanttCollapse() {
    const content = document.getElementById('ganttContent');
    const btn = document.querySelector('.gantt-collapse-btn');
    content.classList.toggle('collapsed');
    btn.classList.toggle('collapsed');
}

viewLoaders.schedule = loadScheduleData;
