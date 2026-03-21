async function loadProjectsData() {
    const [projectsRes, skillsRes] = await Promise.all([
        fetch(`/api/projects?scenario_id=${currentScenarioId}`),
        fetch('/api/skills')
    ]);
    allProjects = await projectsRes.json();
    allSkills = await skillsRes.json();
    renderProjectsList(allProjects);
    populateSkillsDropdown();
}

// Populate skills dropdown
function populateSkillsDropdown() {
    const select = document.getElementById('projectSkillsSelect');
    select.innerHTML = allSkills.map(skill =>
        `<option value="${skill.skill}">${skill.skill}</option>`
    ).join('');
}

// Render projects list (full page)
function renderProjectsList(projects) {
    const container = document.getElementById('projectsListContainer');
    const sorted = [...projects].sort((a, b) => a.name.localeCompare(b.name));
    const fmtDate = d => d ? new Date(d + 'T00:00:00').toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'}) : '';
    container.innerHTML = sorted.map(project => {
        const schedStatus = project.schedule_status || 'not_scheduled';
        const contractDates = `${fmtDate(project.contract_start_date)} – ${fmtDate(project.contract_end_date)}`;
        const actualDates = project.actual_start_date
            ? `${fmtDate(project.actual_start_date)} – ${fmtDate(project.actual_end_date)}`
            : '--';
        return `
        <div class="card" style="position:relative;">
            <div class="card-header">
                <div style="display:flex;align-items:center;gap:6px;flex:1;min-width:0;">
                    <div class="card-title">${project.name}</div>
                    <span class="card-meta">${project.duration_days}d</span>
                    ${project.required_skills.split(',').map(skill =>
                        `<span class="skills-tag-light">${skill.trim()}</span>`
                    ).join('')}
                </div>
                <div class="status-badges">
                    <div class="card-status ${project.award_status}">${project.award_status.replace('_', ' ')}</div>
                    <div class="card-status ${schedStatus}">${schedStatus.replace('_', ' ')}</div>
                </div>
            </div>
            <div class="card-detail"><strong>Contract:</strong> <span class="editable-date" onclick="editProject('${project.id}')">${contractDates}</span> · <strong>Scheduled:</strong> ${actualDates}${project.procurement_date ? ` · <strong>Procurement:</strong> ${fmtDate(project.procurement_date)}` : ''}</div>
            <button class="card-edit-btn" onclick="editProject('${project.id}')" title="Edit">✎</button>
        </div>`;
    }).join('');
}

// Filter projects
function applyProjectFilters() {
    const search = (document.getElementById('projectsSearch').value || '').toLowerCase();
    const award = document.getElementById('projectsAwardFilter').value;
    const sched = document.getElementById('projectsScheduleFilter').value;
    const filtered = allProjects.filter(p => {
        if (search && !p.name.toLowerCase().includes(search)) return false;
        if (award && p.award_status !== award) return false;
        if (sched && (p.schedule_status || 'not_scheduled') !== sched) return false;
        return true;
    });
    renderProjectsList(filtered);
}

function openProjectModal() {
    document.getElementById('projectModal').classList.add('active');
}

function closeProjectModal() {
    document.getElementById('projectModal').classList.remove('active');
    document.getElementById('projectForm').reset();
    editingProjectId = null;
    lastEndDateSource = null;
    document.querySelector('#projectModal .modal-header h3').textContent = 'Add Project';
    document.querySelector('#projectForm .submit-button').textContent = 'Add Project';
    document.getElementById('projectDeleteBtn').style.display = 'none';
}

function editProject(id) {
    const project = allProjects.find(p => p.id === id);
    if (!project) return;
    editingProjectId = id;
    const form = document.getElementById('projectForm');
    form.querySelector('[name="name"]').value = project.name;
    form.querySelector('[name="contract_start_date"]').value = project.contract_start_date;
    form.querySelector('[name="duration_days"]').value = project.duration_days;
    form.querySelector('[name="contract_end_date"]').value = project.contract_end_date || '';
    form.querySelector('[name="procurement_date"]').value = project.procurement_date || '';
    form.querySelector('[name="award_status"]').value = project.award_status;
    lastEndDateSource = null;
    // Select matching skills in dropdown
    const skills = project.required_skills.split(',').map(s => s.trim());
    const select = document.getElementById('projectSkillsSelect');
    Array.from(select.options).forEach(opt => {
        opt.selected = skills.includes(opt.value);
    });
    document.querySelector('#projectModal .modal-header h3').textContent = 'Edit Project';
    document.querySelector('#projectForm .submit-button').textContent = 'Save Changes';
    document.getElementById('projectDeleteBtn').style.display = 'block';
    document.getElementById('projectModal').classList.add('active');
}

async function deleteProjectFromModal() {
    const project = allProjects.find(p => p.id === editingProjectId);
    const name = project ? project.name : 'this project';
    if (!confirm(`Delete ${name}? This will also remove all assignments for this project.`)) return;
    try {
        const res = await fetch(`/api/projects/${editingProjectId}`, { method: 'DELETE' });
        if (!res.ok) throw new Error(await res.text());
        closeProjectModal();
        await loadProjectsData();
    } catch (err) {
        alert('Failed to delete: ' + err.message);
    }
}

// Close modal on outside click
document.getElementById('projectModal').addEventListener('click', function(e) {
    if (e.target === this) closeProjectModal();
});

function updateContractEndPreview(source) {
    lastEndDateSource = source;
    const form = document.getElementById('projectForm');
    const startStr = form.querySelector('[name="contract_start_date"]').value;
    if (!startStr) return;
    const start = new Date(startStr + 'T00:00:00');

    if (source === 'duration') {
        const days = parseFloat(form.querySelector('[name="duration_days"]').value);
        if (!days || days < 0.5) return;
        const end = new Date(start);
        end.setDate(end.getDate() + Math.ceil(days));
        form.querySelector('[name="contract_end_date"]').value = end.toISOString().split('T')[0];
    } else if (source === 'end_date') {
        const endStr = form.querySelector('[name="contract_end_date"]').value;
        if (!endStr) return;
        const end = new Date(endStr + 'T00:00:00');
        const days = Math.max(1, Math.round((end - start) / (1000 * 60 * 60 * 24)));
        form.querySelector('[name="duration_days"]').value = days;
    }
}

async function submitProject(event) {
    event.preventDefault();
    const formData = new FormData(event.target);

    const select = document.getElementById('projectSkillsSelect');
    const project = {
        name: formData.get('name'),
        required_skills: Array.from(select.selectedOptions).map(o => o.value).join(','),
        contract_start_date: formData.get('contract_start_date'),
        duration_days: parseFloat(formData.get('duration_days')),
        award_status: formData.get('award_status'),
    };
    // Include procurement_date if set
    const procDate = formData.get('procurement_date');
    if (procDate) project.procurement_date = procDate;
    // If end date was explicitly changed, include it
    if (lastEndDateSource === 'end_date' && formData.get('contract_end_date')) {
        project.contract_end_date = formData.get('contract_end_date');
    }

    try {
        const url = editingProjectId ? `/api/projects/${editingProjectId}` : '/api/projects';
        const method = editingProjectId ? 'PATCH' : 'POST';
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(project)
        });
        if (!response.ok) throw new Error(await response.text());
        closeProjectModal();
        await loadProjectsData();
    } catch (err) {
        alert('Failed to save project: ' + err.message);
    }
}

// Delete project (legacy)
async function deleteProject(id, name) {
    if (!confirm(`Delete ${name}? This will also remove all assignments for this project.`)) return;
    try {
        const res = await fetch(`/api/projects/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error(await res.text());
        await loadProjectsData();
    } catch (err) {
        alert('Failed to delete project: ' + err.message);
    }
}

viewLoaders.projects = loadProjectsData;
