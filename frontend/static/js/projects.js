async function loadProjectsData() {
    document.getElementById('projectsLoading').style.display = 'flex';
    document.getElementById('projectsListContainer').innerHTML = '';
    const [projectsRes, skillsRes] = await Promise.all([
        fetch(`/api/projects?scenario_id=${currentScenarioId}`),
        fetch('/api/skills')
    ]);
    allProjects = await projectsRes.json();
    allSkills = await skillsRes.json();
    document.getElementById('projectsLoading').style.display = 'none';
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

// Compute duration from hours and update the read-only field + end date preview
function updateHoursComputed() {
    const mh = parseFloat(document.getElementById('projectManHours').value) || 0;
    const ch = parseFloat(document.getElementById('projectCrewHours').value) || 0;
    const allowOT = document.getElementById('projectAllowOvertime').checked;
    const total = mh + ch;
    const divisor = allowOT ? 6 : 4;
    const days = total > 0 ? Math.ceil(total / divisor) * 0.5 : '';
    document.getElementById('projectDurationDays').value = days;
    if (days) updateCommittedEndPreview('duration');
}

function toggleProcurementDate() {
    const arrived = document.getElementById('projectMaterialArrived').checked;
    document.getElementById('procurementDateGroup').style.display = arrived ? 'none' : 'block';
}

function formatHours(project) {
    const mh = parseFloat(project.man_hours) || 0;
    const ch = parseFloat(project.crew_hours) || 0;
    if (mh || ch) return `${mh + ch}h`;
    return `${project.duration_days}d`;
}

// Render projects list (full page)
function renderProjectsList(projects) {
    const container = document.getElementById('projectsListContainer');
    const sorted = [...projects].sort((a, b) => a.name.localeCompare(b.name));
    const fmtDate = d => d ? new Date(d + 'T00:00:00').toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'}) : '';
    container.innerHTML = sorted.map(project => {
        const schedStatus = project.schedule_status || 'not_scheduled';
        const committedDates = project.committed_start_date
            ? `${fmtDate(project.committed_start_date)} – ${fmtDate(project.committed_end_date)}`
            : 'Not set';
        const actualDates = project.actual_start_date
            ? `${fmtDate(project.actual_start_date)} – ${fmtDate(project.actual_end_date)}`
            : '--';
        const woTag = project.work_order_number ? `<span class="card-meta" title="WO#">${project.work_order_number}</span>` : '';
        const divTag = project.division ? `<span class="skills-tag-light">${project.division}</span>` : '';
        const equipTag = project.equipment ? `<span class="card-meta" title="Equipment">${project.equipment}</span>` : '';
        return `
        <div class="card" style="position:relative;">
            <div class="card-header">
                <div style="display:flex;align-items:center;gap:6px;flex:1;min-width:0;">
                    <div class="card-title">${project.name}</div>
                    ${project.account_type === 'priority' ? '<span class="priority-badge">Priority</span>' : ''}
                    <span class="card-meta">${formatHours(project)}</span>
                    ${woTag}${divTag}${equipTag}
                    ${project.required_skills.split(',').map(skill =>
                        `<span class="skills-tag-light">${skill.trim()}</span>`
                    ).join('')}
                </div>
                <div class="status-badges">
                    <div class="card-status ${project.award_status}">${project.award_status.replace('_', ' ')}</div>
                    <div class="card-status ${schedStatus}">${schedStatus.replace('_', ' ')}</div>
                </div>
            </div>
            ${project.description ? `<div class="card-description">${project.description}</div>` : ''}
            <div class="card-detail"><strong>Committed:</strong> <span class="editable-date" onclick="editProject('${project.id}')">${committedDates}</span> · <strong>Scheduled:</strong> ${actualDates}${project.procurement_date ? ` · <strong>Material Procurement:</strong> ${fmtDate(project.procurement_date)}` : ''}</div>
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
    document.getElementById('projectAllowOvertime').checked = false;
    document.getElementById('projectCustomerId').value = '';
    document.getElementById('projectAccountType').value = 'standard';
    document.getElementById('projectManHours').value = '';
    document.getElementById('projectCrewHours').value = '';
    document.getElementById('projectDurationDays').value = '';
    document.getElementById('projectWONumber').value = '';
    document.getElementById('projectWODate').value = '';
    document.getElementById('projectEquipment').value = '';
    document.getElementById('projectMaterialStatus').value = '';
    document.getElementById('projectMaterialArrived').checked = false;
    toggleProcurementDate();
    document.getElementById('projectDivision').value = '';
    document.getElementById('projectSalesRep').value = '';
    document.getElementById('projectDescription').value = '';
    document.getElementById('projectTotalAmount').value = '';
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
    document.getElementById('projectManHours').value = project.man_hours || '';
    document.getElementById('projectCrewHours').value = project.crew_hours || '';
    document.getElementById('projectDurationDays').value = project.duration_days || '';
    form.querySelector('[name="committed_start_date"]').value = project.committed_start_date || '';
    form.querySelector('[name="committed_end_date"]').value = project.committed_end_date || '';
    form.querySelector('[name="procurement_date"]').value = project.procurement_date || '';
    form.querySelector('[name="award_status"]').value = project.award_status;
    document.getElementById('projectAllowOvertime').checked = !!project.allow_overtime;
    document.getElementById('projectCustomerId').value = project.customer_id || '';
    document.getElementById('projectAccountType').value = project.account_type || 'standard';
    // Work order details
    document.getElementById('projectWONumber').value = project.work_order_number || '';
    document.getElementById('projectWODate').value = project.work_order_date || '';
    document.getElementById('projectEquipment').value = project.equipment || '';
    document.getElementById('projectMaterialStatus').value = project.material_status || '';
    document.getElementById('projectMaterialArrived').checked = !!project.material_arrived;
    toggleProcurementDate();
    document.getElementById('projectDivision').value = project.division || '';
    document.getElementById('projectSalesRep').value = project.sales_rep || '';
    document.getElementById('projectDescription').value = project.description || '';
    document.getElementById('projectTotalAmount').value = project.total_amount || '';
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

function addBusinessDaysJS(startDate, days) {
    const d = new Date(startDate);
    let remaining = days;
    while (remaining > 0) {
        d.setDate(d.getDate() + 1);
        if (d.getDay() !== 0 && d.getDay() !== 6) remaining--;
    }
    return d;
}

function countBusinessDaysJS(start, end) {
    let count = 0;
    const d = new Date(start);
    while (d <= end) {
        if (d.getDay() !== 0 && d.getDay() !== 6) count++;
        d.setDate(d.getDate() + 1);
    }
    return count;
}

function updateCommittedEndPreview(source) {
    lastEndDateSource = source;
    const form = document.getElementById('projectForm');
    const startStr = form.querySelector('[name="committed_start_date"]').value;
    if (!startStr) return;
    const start = new Date(startStr + 'T00:00:00');
    const allowOT = document.getElementById('projectAllowOvertime').checked;

    if (source === 'duration') {
        const days = parseFloat(document.getElementById('projectDurationDays').value);
        if (!days || days < 0.5) return;
        let end;
        if (allowOT) {
            end = new Date(start);
            end.setDate(end.getDate() + Math.ceil(days) - 1);
        } else {
            end = addBusinessDaysJS(start, Math.ceil(days) - 1);
        }
        form.querySelector('[name="committed_end_date"]').value = end.toISOString().split('T')[0];
    } else if (source === 'end_date') {
        const endStr = form.querySelector('[name="committed_end_date"]').value;
        if (!endStr) return;
        const end = new Date(endStr + 'T00:00:00');
        let days;
        if (allowOT) {
            days = Math.max(1, Math.round((end - start) / (1000 * 60 * 60 * 24)) + 1);
        } else {
            days = Math.max(1, countBusinessDaysJS(start, end));
        }
        form.querySelector('[name="duration_days"]').value = days;
    }
}

async function submitProject(event) {
    event.preventDefault();
    const formData = new FormData(event.target);

    const select = document.getElementById('projectSkillsSelect');
    const mh = parseFloat(formData.get('man_hours')) || null;
    const ch = parseFloat(formData.get('crew_hours')) || null;
    const project = {
        name: formData.get('name'),
        required_skills: Array.from(select.selectedOptions).map(o => o.value).join(','),
        man_hours: mh,
        crew_hours: ch,
        award_status: formData.get('award_status'),
        allow_overtime: document.getElementById('projectAllowOvertime').checked,
        customer_id: formData.get('customer_id') || null,
        account_type: formData.get('account_type') || 'standard',
        work_order_number: formData.get('work_order_number') || null,
        work_order_date: formData.get('work_order_date') || null,
        equipment: formData.get('equipment') || null,
        material_status: formData.get('material_status') || null,
        material_arrived: document.getElementById('projectMaterialArrived').checked,
        division: formData.get('division') || null,
        sales_rep: formData.get('sales_rep') || null,
        description: formData.get('description') || null,
        total_amount: parseFloat(formData.get('total_amount')) || null,
    };
    // Include committed dates if set
    const startDate = formData.get('committed_start_date');
    if (startDate) project.committed_start_date = startDate;
    // Include procurement_date if set
    const procDate = formData.get('procurement_date');
    if (procDate) project.procurement_date = procDate;
    // If end date was explicitly changed, include it
    if (lastEndDateSource === 'end_date' && formData.get('committed_end_date')) {
        project.committed_end_date = formData.get('committed_end_date');
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

// ── Spreadsheet Upload ────────────────────────────────────────────────────────

let uploadParsedData = null;    // { headers: [], rows: [] }
let uploadMappings = null;      // [{ column, field }]
let uploadParsedProjects = null; // final project objects for import

const PROJECT_FIELDS = [
    { value: '', label: 'Skip' },
    { value: 'name', label: 'Project Name' },
    { value: 'required_skills', label: 'Required Skills' },
    { value: 'man_hours', label: 'Man Hours' },
    { value: 'crew_hours', label: 'Crew Hours' },
    { value: 'duration_days', label: 'Duration (days)' },
    { value: 'committed_start_date', label: 'Committed Start' },
    { value: 'committed_end_date', label: 'Committed End' },
    { value: 'procurement_date', label: 'Procurement Date' },
    { value: 'award_status', label: 'Award Status' },
    { value: 'allow_overtime', label: 'Allow Overtime' },
    { value: 'customer_id', label: 'Customer ID' },
    { value: 'account_type', label: 'Account Type' },
    { value: 'work_order_number', label: 'WO Number' },
    { value: 'work_order_date', label: 'WO Date' },
    { value: 'equipment', label: 'Equipment' },
    { value: 'material_status', label: 'Material Status' },
    { value: 'material_arrived', label: 'Material Arrived' },
    { value: 'division', label: 'Division' },
    { value: 'sales_rep', label: 'Sales Rep' },
    { value: 'description', label: 'Description' },
    { value: 'total_amount', label: 'Total Amount' },
];

function openUploadModal() {
    document.getElementById('uploadProjectsModal').classList.add('active');
    resetUpload();
}

function closeUploadModal() {
    document.getElementById('uploadProjectsModal').classList.remove('active');
    resetUpload();
}

function resetUpload() {
    uploadParsedData = null;
    uploadMappings = null;
    uploadParsedProjects = null;
    document.getElementById('uploadFileInput').value = '';
    showUploadStep(1);
}

function showUploadStep(step) {
    document.getElementById('uploadStep1').style.display = step === 1 ? 'block' : 'none';
    document.getElementById('uploadStep2').style.display = step === 2 ? 'block' : 'none';
    document.getElementById('uploadStep3').style.display = step === 3 ? 'block' : 'none';
    document.getElementById('uploadLoading').style.display = step === 'loading' ? 'block' : 'none';
    const titles = { 1: 'Upload Projects', 2: 'Map Columns', 3: 'Preview Import', loading: 'Upload Projects' };
    document.getElementById('uploadModalTitle').textContent = titles[step] || 'Upload Projects';
}

// File input & drag-drop setup
(function setupUploadHandlers() {
    const dropzone = document.getElementById('uploadDropzone');
    const fileInput = document.getElementById('uploadFileInput');

    dropzone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) handleFileSelect(e.target.files[0]);
    });

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length) handleFileSelect(e.dataTransfer.files[0]);
    });
})();

// Close modal on outside click
document.getElementById('uploadProjectsModal').addEventListener('click', function(e) {
    if (e.target === this) closeUploadModal();
});

function handleFileSelect(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['csv', 'xlsx', 'xls'].includes(ext)) {
        alert('Please select a CSV or Excel file (.csv, .xlsx, .xls)');
        return;
    }

    showUploadStep('loading');
    document.getElementById('uploadLoadingText').textContent = 'Parsing file...';

    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const workbook = XLSX.read(e.target.result, { type: 'array', cellDates: true });
            const sheet = workbook.Sheets[workbook.SheetNames[0]];
            const jsonData = XLSX.utils.sheet_to_json(sheet, { raw: false, defval: '' });

            if (!jsonData.length) {
                alert('The file appears to be empty.');
                showUploadStep(1);
                return;
            }

            const headers = Object.keys(jsonData[0]);
            uploadParsedData = { headers, rows: jsonData };
            requestColumnMapping(headers, jsonData.slice(0, 5));
        } catch (err) {
            alert('Failed to parse file: ' + err.message);
            showUploadStep(1);
        }
    };
    reader.readAsArrayBuffer(file);
}

async function requestColumnMapping(headers, sampleRows) {
    document.getElementById('uploadLoadingText').textContent = 'AI is analyzing columns...';
    try {
        const res = await fetch('/api/projects/map-columns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ headers, sample_rows: sampleRows })
        });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        uploadMappings = data.mappings;
        renderMappingUI(uploadMappings, sampleRows);
    } catch (err) {
        alert('Failed to analyze columns: ' + err.message);
        showUploadStep(1);
    }
}

function renderMappingUI(mappings, sampleRows) {
    const container = document.getElementById('uploadMappingTable');
    let html = '<table class="upload-mapping-table"><thead><tr><th>Spreadsheet Column</th><th>Sample Data</th><th>Maps To</th></tr></thead><tbody>';

    mappings.forEach((m, idx) => {
        const samples = sampleRows.slice(0, 3).map(r => r[m.column] || '').filter(Boolean).join(', ');
        const truncated = samples.length > 60 ? samples.slice(0, 57) + '...' : samples;
        html += `<tr>
            <td class="mapping-col-name">${escapeHtml(m.column)}</td>
            <td class="mapping-sample">${escapeHtml(truncated)}</td>
            <td><select class="mapping-select" data-idx="${idx}">
                ${PROJECT_FIELDS.map(f => `<option value="${f.value}" ${(m.field || '') === f.value ? 'selected' : ''}>${f.label}</option>`).join('')}
            </select></td>
        </tr>`;
    });

    html += '</tbody></table>';
    container.innerHTML = html;
    showUploadStep(2);
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function confirmMapping() {
    // Read current mapping selections
    const selects = document.querySelectorAll('.mapping-select');
    selects.forEach(sel => {
        const idx = parseInt(sel.dataset.idx);
        uploadMappings[idx].field = sel.value || null;
    });

    // Check that at least "name" is mapped
    const hasName = uploadMappings.some(m => m.field === 'name');
    if (!hasName) {
        alert('You must map at least one column to "Project Name".');
        return;
    }

    // Parse all rows into project objects
    const projects = [];
    for (const row of uploadParsedData.rows) {
        const proj = {};
        for (const m of uploadMappings) {
            if (m.field) {
                let val = row[m.column];
                if (val === undefined || val === null) val = '';
                val = String(val).trim();
                if (m.field === 'duration_days' || m.field === 'man_hours' || m.field === 'crew_hours' || m.field === 'total_amount') {
                    val = parseFloat(val) || 0;
                } else if (m.field === 'allow_overtime' || m.field === 'material_arrived') {
                    val = ['true', '1', 'yes'].includes(val.toLowerCase());
                } else if (m.field === 'committed_start_date' || m.field === 'committed_end_date' || m.field === 'procurement_date' || m.field === 'work_order_date') {
                    val = normalizeDate(val);
                }
                proj[m.field] = val;
            }
        }
        // Skip empty rows (no name)
        if (proj.name) projects.push(proj);
    }

    if (!projects.length) {
        alert('No valid projects found. Make sure "Project Name" column has data.');
        return;
    }

    uploadParsedProjects = projects;
    renderImportPreview(projects);
}

function normalizeDate(val) {
    if (!val) return '';
    // Try parsing various date formats
    const d = new Date(val);
    if (!isNaN(d.getTime())) {
        return d.toISOString().split('T')[0];
    }
    // Try MM/DD/YYYY
    const parts = val.split('/');
    if (parts.length === 3) {
        const [m, day, y] = parts;
        const d2 = new Date(parseInt(y), parseInt(m) - 1, parseInt(day));
        if (!isNaN(d2.getTime())) return d2.toISOString().split('T')[0];
    }
    return val;
}

function renderImportPreview(projects) {
    document.getElementById('uploadPreviewCount').textContent = `${projects.length} project${projects.length !== 1 ? 's' : ''} ready to import:`;

    const fields = uploadMappings.filter(m => m.field).map(m => m.field);
    const fieldLabels = {};
    PROJECT_FIELDS.forEach(f => fieldLabels[f.value] = f.label);

    let html = '<thead><tr>';
    fields.forEach(f => html += `<th>${fieldLabels[f] || f}</th>`);
    html += '</tr></thead><tbody>';

    projects.slice(0, 50).forEach(proj => {
        html += '<tr>';
        fields.forEach(f => {
            let val = proj[f] !== undefined ? proj[f] : '';
            html += `<td>${escapeHtml(String(val))}</td>`;
        });
        html += '</tr>';
    });

    if (projects.length > 50) {
        html += `<tr><td colspan="${fields.length}" style="text-align:center;color:#999;font-style:italic;">...and ${projects.length - 50} more</td></tr>`;
    }

    html += '</tbody>';
    document.getElementById('uploadPreviewTable').innerHTML = html;
    document.getElementById('uploadErrors').style.display = 'none';
    showUploadStep(3);
}

function backToMapping() {
    showUploadStep(2);
}

async function bulkImportProjects() {
    if (!uploadParsedProjects || !uploadParsedProjects.length) return;

    const btn = document.getElementById('uploadImportBtn');
    btn.disabled = true;
    btn.textContent = 'Importing...';

    try {
        const res = await fetch('/api/projects/bulk', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ projects: uploadParsedProjects })
        });
        if (!res.ok) throw new Error(await res.text());
        const result = await res.json();

        if (result.errors && result.errors.length) {
            const errDiv = document.getElementById('uploadErrors');
            errDiv.style.display = 'block';
            errDiv.innerHTML = `<strong>${result.imported} imported, ${result.errors.length} error(s):</strong><ul>`
                + result.errors.map(e => `<li>Row ${e.row}: ${escapeHtml(e.message)}</li>`).join('')
                + '</ul>';
            btn.disabled = false;
            btn.textContent = 'Import Projects';
        } else {
            closeUploadModal();
            await loadProjectsData();
            // Show success toast if available
            if (typeof showToast === 'function') {
                showToast(`${result.imported} project${result.imported !== 1 ? 's' : ''} imported successfully`);
            } else {
                alert(`${result.imported} project${result.imported !== 1 ? 's' : ''} imported successfully!`);
            }
        }
    } catch (err) {
        alert('Import failed: ' + err.message);
        btn.disabled = false;
        btn.textContent = 'Import Projects';
    }
}

viewLoaders.projects = loadProjectsData;
