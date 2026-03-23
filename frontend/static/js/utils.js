// Set current date
document.getElementById('currentDate').textContent = currentDate.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
});

function populateStatusSelects() {
    const awardOpts = AWARD_STATUSES.map(s => `<option value="${s.value}">${s.label}</option>`).join('');
    document.getElementById('projectsAwardFilter').innerHTML = '<option value="">Award Status</option>' + awardOpts;
    document.getElementById('projectFormAwardStatus').innerHTML = awardOpts;
    const schedOpts = SCHEDULE_STATUSES.map(s => `<option value="${s.value}">${s.label}</option>`).join('');
    document.getElementById('projectsScheduleFilter').innerHTML = '<option value="">Schedule Status</option>' + schedOpts;
}

// Filter dropdown helpers
function onFilterChange(select) {
    const clearBtn = select.parentElement.querySelector('.filter-clear');
    if (select.value) {
        clearBtn.style.display = 'block';
        select.classList.remove('placeholder');
    } else {
        clearBtn.style.display = 'none';
        select.classList.add('placeholder');
    }
    if (select.id.startsWith('personnel')) applyPersonnelFilters();
    else applyProjectFilters();
}

function clearFilter(btn) {
    const select = btn.parentElement.querySelector('.filter-select');
    select.value = '';
    select.classList.add('placeholder');
    btn.style.display = 'none';
    if (select.id.startsWith('personnel')) applyPersonnelFilters();
    else applyProjectFilters();
}

// Parse CSV
function parseCSV(text) {
    const lines = text.trim().split('\n');
    const headers = lines[0].split(',');
    return lines.slice(1).map(line => {
        const values = [];
        let current = '';
        let inQuotes = false;

        for (let char of line) {
            if (char === '"') {
                inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
                values.push(current.trim());
                current = '';
            } else {
                current += char;
            }
        }
        values.push(current.trim());

        const obj = {};
        headers.forEach((header, i) => {
            obj[header.trim()] = values[i]?.replace(/^"|"$/g, '') || '';
        });
        return obj;
    });
}

// Calculate days until project starts
function calculateTMinus(startDate) {
    const start = new Date(startDate + 'T00:00:00');
    const diffTime = start - currentDate;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
        return 'STARTED';
    } else if (diffDays === 0) {
        return 'Starts in: T-0 (TODAY)';
    } else {
        return `Starts in: T-${diffDays} days`;
    }
}

function lastFirstName(name) {
    const parts = name.trim().split(/\s+/);
    if (parts.length < 2) return name;
    const last = parts.pop();
    return `${last}, ${parts.join(' ')}`;
}

function getLastName(name) {
    const parts = name.trim().split(/\s+/);
    return parts.length < 2 ? name : parts[parts.length - 1];
}

function showScheduleNotification(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.textContent = message;
    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
