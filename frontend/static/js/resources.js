async function loadResourcesData() {
    document.getElementById('personnelLoading').style.display = 'flex';
    document.getElementById('skillsLoading').style.display = 'flex';
    document.getElementById('personnelListContainer').innerHTML = '';
    document.getElementById('skillsListContainer').innerHTML = '';
    const [personnelRes, skillsRes] = await Promise.all([
        fetch(`/api/personnel?scenario_id=${currentScenarioId}`),
        fetch('/api/skills')
    ]);
    allPersonnel = await personnelRes.json();
    allSkills = await skillsRes.json();
    document.getElementById('personnelLoading').style.display = 'none';
    document.getElementById('skillsLoading').style.display = 'none';
    renderPersonnelList(allPersonnel);
    populatePersonnelSkillTiles();
    renderSkillsList(allSkills);
    populatePersonnelSkillFilter();
}

function renderPersonnelList(personnel) {
    const container = document.getElementById('personnelListContainer');
    const sorted = [...personnel].sort((a, b) => getLastName(a.name).localeCompare(getLastName(b.name)));
    const fmtDate = d => d ? new Date(d + 'T00:00:00').toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'}) : '-';
    container.innerHTML = sorted.map(person => {
        const status = person.availability_status || 'available';
        const displayName = lastFirstName(person.name);
        const currentProject = person.current_project_name
            ? `<strong>Current:</strong> ${person.current_project_name}`
            : '';
        const availDate = person.current_project_name
            ? `<strong>Available:</strong> <span class="available-date">${fmtDate(person.current_assignment_end)}</span>`
            : `<strong>Available:</strong> <span class="available-date">Now</span>`;
        return `
        <div class="card ${status}" style="position:relative;">
            <div class="card-header">
                <div style="display:flex;align-items:center;gap:6px;flex:1;min-width:0;">
                    <div class="card-title">${displayName}</div>
                    ${person.skills.split(',').map(skill =>
                        `<span class="skills-tag-light">${skill.trim()}</span>`
                    ).join('')}
                </div>
                <div class="card-status ${status}">${status}</div>
            </div>
            <div class="card-detail">${currentProject}${currentProject ? ' · ' : ''}${availDate}</div>
            <button class="card-edit-btn" onclick="editPersonnel('${person.id}')" title="Edit">✎</button>
        </div>`;
    }).join('');
}

function renderSkillsList(skills) {
    const container = document.getElementById('skillsListContainer');
    const sorted = [...skills].sort((a, b) => a.skill.localeCompare(b.skill));
    container.innerHTML = sorted.map(skill => `
        <div class="card">
            <div class="card-title">${skill.skill}</div>
        </div>
    `).join('');
}

// Populate personnel skill filter dropdown
function populatePersonnelSkillFilter() {
    const select = document.getElementById('personnelSkillFilter');
    const current = select.value;
    select.innerHTML = '<option value="">Skill</option>' +
        [...allSkills].sort((a, b) => a.skill.localeCompare(b.skill))
            .map(s => `<option value="${s.skill}">${s.skill}</option>`).join('');
    select.value = current;
}

// Filter personnel
function applyPersonnelFilters() {
    const search = (document.getElementById('personnelSearch').value || '').toLowerCase();
    const skill = document.getElementById('personnelSkillFilter').value;
    const status = document.getElementById('personnelStatusFilter').value;
    const filtered = allPersonnel.filter(p => {
        if (search && !p.name.toLowerCase().includes(search)) return false;
        if (skill && !p.skills.split(',').map(s => s.trim()).includes(skill)) return false;
        if (status && (p.availability_status || 'available') !== status) return false;
        return true;
    });
    renderPersonnelList(filtered);
}

// Populate personnel skill tiles dynamically from allSkills
function populatePersonnelSkillTiles() {
    const container = document.querySelector('#personnelModal .skill-tiles');
    const sorted = [...allSkills].sort((a, b) => a.skill.localeCompare(b.skill));
    container.innerHTML = sorted.map(s => {
        const id = 'mech-' + s.skill.toLowerCase().replace(/\s+/g, '-');
        return `
            <div class="skill-tile">
                <input type="checkbox" id="${id}" name="skills" value="${s.skill}">
                <label for="${id}">${s.skill}</label>
            </div>`;
    }).join('');
}

function openPersonnelModal() {
    document.getElementById('personnelModal').classList.add('active');
}

function closePersonnelModal() {
    document.getElementById('personnelModal').classList.remove('active');
    document.getElementById('personnelForm').reset();
    editingPersonnelId = null;
    document.querySelector('#personnelModal .modal-header h3').textContent = 'Add Personnel';
    document.querySelector('#personnelForm .submit-button').textContent = 'Add Personnel';
    document.getElementById('personnelDeleteBtn').style.display = 'none';
}

function editPersonnel(id) {
    const person = allPersonnel.find(p => p.id === id);
    if (!person) return;
    editingPersonnelId = id;
    const form = document.getElementById('personnelForm');
    form.querySelector('[name="name"]').value = person.name;
    // Check matching skill tiles
    const skills = person.skills.split(',').map(s => s.trim());
    form.querySelectorAll('[name="skills"]').forEach(cb => {
        cb.checked = skills.includes(cb.value);
    });
    document.querySelector('#personnelModal .modal-header h3').textContent = 'Edit Personnel';
    document.querySelector('#personnelForm .submit-button').textContent = 'Save Changes';
    document.getElementById('personnelDeleteBtn').style.display = 'block';
    document.getElementById('personnelModal').classList.add('active');
}

async function deletePersonnelFromModal() {
    const person = allPersonnel.find(p => p.id === editingPersonnelId);
    const name = person ? person.name : 'this person';
    if (!confirm(`Delete ${name}? This will also remove all their assignments.`)) return;
    try {
        const res = await fetch(`/api/personnel/${editingPersonnelId}`, { method: 'DELETE' });
        if (!res.ok) throw new Error(await res.text());
        closePersonnelModal();
        await loadResourcesData();
    } catch (err) {
        alert('Failed to delete: ' + err.message);
    }
}

// Close modal on outside click
document.getElementById('personnelModal').addEventListener('click', function(e) {
    if (e.target === this) closePersonnelModal();
});

// Submit personnel form (create or update)
async function submitPersonnel(event) {
    event.preventDefault();
    const formData = new FormData(event.target);

    const personnel = {
        name: formData.get('name'),
        skills: formData.getAll('skills').join(','),
    };

    try {
        const url = editingPersonnelId ? `/api/personnel/${editingPersonnelId}` : '/api/personnel';
        const method = editingPersonnelId ? 'PATCH' : 'POST';
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(personnel)
        });
        if (!response.ok) throw new Error(await response.text());
        closePersonnelModal();
        await loadResourcesData();
    } catch (err) {
        alert('Failed to save personnel: ' + err.message);
    }
}

// Delete personnel (legacy)
async function deletePersonnel(id, name) {
    if (!confirm(`Delete ${name}? This will also remove all their assignments.`)) return;
    try {
        const res = await fetch(`/api/personnel/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error(await res.text());
        await loadResourcesData();
    } catch (err) {
        alert('Failed to delete personnel: ' + err.message);
    }
}

// Skill modal functions
function openSkillModal() {
    document.getElementById('skillModal').classList.add('active');
}

function closeSkillModal() {
    document.getElementById('skillModal').classList.remove('active');
    document.getElementById('skillForm').reset();
}

document.getElementById('skillModal').addEventListener('click', function(e) {
    if (e.target === this) closeSkillModal();
});

async function submitSkill(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const skill = { skill: formData.get('skill') };

    try {
        const response = await fetch('/api/skills', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(skill)
        });
        if (!response.ok) throw new Error(await response.text());
        closeSkillModal();
        await loadResourcesData();
    } catch (err) {
        alert('Failed to add skill: ' + err.message);
    }
}

viewLoaders.resources = loadResourcesData;
