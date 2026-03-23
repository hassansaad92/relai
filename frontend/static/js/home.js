// Home cache — persists across tab switches, cleared on refresh or scenario change
let homeCache = null;
let homeCacheScenarioId = null;

async function loadHomeData(forceRefresh) {
    // Set date in title
    const now = new Date();
    document.getElementById('homeDate').textContent =
        now.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

    // Serve from cache if available and same scenario
    if (!forceRefresh && homeCache && homeCacheScenarioId === currentScenarioId) {
        renderHomeStatCards(homeCache.project_stats, homeCache.personnel_stats);
        renderRecentProjects(homeCache.project_stats);
        renderMechanicRoster(homeCache.personnel_stats);
        document.getElementById('homeAssessmentLoading').style.display = 'none';
        document.getElementById('homeAssessmentContent').innerHTML = homeCache.assessmentHtml;
        return;
    }

    const params = currentScenarioId ? `?scenario_id=${currentScenarioId}` : '';
    const res = await fetch(`/api/home/stats${params}`);
    const stats = await res.json();

    // Render stat cards immediately
    renderHomeStatCards(stats.project_stats, stats.personnel_stats);
    renderRecentProjects(stats.project_stats);
    renderMechanicRoster(stats.personnel_stats);

    // Show loading state for AI assessment
    document.getElementById('homeAssessmentLoading').style.display = 'flex';
    document.getElementById('homeAssessmentContent').innerHTML = '';

    // Fetch AI assessment
    let assessmentHtml = '<p style="color:#999;">Failed to load AI assessment.</p>';
    try {
        const aiRes = await fetch('/api/home/assessment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                upcoming: stats.upcoming,
                project_stats: stats.project_stats,
                personnel_stats: stats.personnel_stats,
            }),
        });
        const aiData = await aiRes.json();
        assessmentHtml = marked.parse(aiData.assessment || 'No assessment available.');
    } catch (err) {
        // keep default error html
    } finally {
        document.getElementById('homeAssessmentLoading').style.display = 'none';
        document.getElementById('homeAssessmentContent').innerHTML = assessmentHtml;
    }

    // Store in cache
    homeCache = {
        project_stats: stats.project_stats,
        personnel_stats: stats.personnel_stats,
        assessmentHtml,
    };
    homeCacheScenarioId = currentScenarioId;
}

function clearHomeCache() {
    homeCache = null;
    homeCacheScenarioId = null;
}

function renderHomeStatCards(projectStats, personnelStats) {
    const container = document.getElementById('homeStatCards');

    const staffedPct = projectStats?.staffed_pct ?? 0;
    const totalProjects = projectStats?.total_projects ?? 0;
    const staffedCount = projectStats?.staffed_count ?? 0;

    const totalRoster = personnelStats?.total_roster ?? 0;

    const hasFuture = personnelStats?.has_future_assignment ?? 0;
    const resourcePct = totalRoster > 0 ? Math.round((hasFuture / totalRoster) * 100) : 0;

    container.innerHTML = `
        <div class="home-stat-card">
            <div class="home-stat-card-header">
                <div class="home-stat-card-icon staffing">&#128736;</div>
                <span class="home-stat-card-title">Staffing Level</span>
            </div>
            <div class="home-stat-card-value">${staffedPct}%</div>
            <div class="home-stat-card-label">${staffedCount} of ${totalProjects} projects staffed</div>
            <div class="home-stat-card-bar"><div class="home-stat-card-bar-fill staffing" style="width:${staffedPct}%"></div></div>
        </div>
        <div class="home-stat-card">
            <div class="home-stat-card-header">
                <div class="home-stat-card-icon resource">&#128101;</div>
                <span class="home-stat-card-title">Resource Allocation</span>
            </div>
            <div class="home-stat-card-value">${resourcePct}%</div>
            <div class="home-stat-card-label">${hasFuture} of ${totalRoster} have future work</div>
            <div class="home-stat-card-bar"><div class="home-stat-card-bar-fill resource" style="width:${resourcePct}%"></div></div>
        </div>
    `;
}

function renderRecentProjects(projectStats) {
    const container = document.getElementById('homeRecentProjects');
    if (!projectStats || !projectStats.recent_projects || projectStats.recent_projects.length === 0) {
        container.innerHTML = '';
        return;
    }
    const cards = projectStats.recent_projects.map(p => {
        const statusClass = p.award_status || 'awarded';
        const statusLabel = (p.award_status || 'awarded').replace('_', ' ');
        const schedClass = p.schedule_status || 'not_scheduled';
        const schedLabel = (p.schedule_status || 'not scheduled').replace('_', ' ');
        return `<div class="home-recent-card">
            <div class="home-recent-card-header">
                <span class="home-recent-card-name">${p.name}</span>
                <div class="status-badges">
                    <span class="card-status ${statusClass}">${statusLabel}</span>
                    <span class="card-status ${schedClass}">${schedLabel}</span>
                </div>
            </div>
            <div class="home-recent-card-detail">${p.duration_days || '?'}d · ${p.assignment_count || 0} assigned</div>
        </div>`;
    }).join('');
    container.innerHTML = `
        <div class="home-section-title">Recent Projects</div>
        <div class="home-recent-projects">${cards}</div>
    `;
}

function renderMechanicRoster(personnelStats) {
    const container = document.getElementById('homeMechanicRoster');
    if (!personnelStats || !personnelStats.roster || personnelStats.roster.length === 0) {
        container.innerHTML = '';
        return;
    }
    const rows = personnelStats.roster.map(p => {
        const assignment = p.current_project || '-';
        const availClass = p.is_assigned ? 'assigned' : 'available';
        const availLabel = p.is_assigned ? 'Assigned' : 'Available';
        return `<tr>
            <td style="font-weight:600;">${p.name}</td>
            <td>${assignment}</td>
            <td><span class="card-status ${availClass}">${availLabel}</span></td>
        </tr>`;
    }).join('');
    container.innerHTML = `
        <div class="home-section-title">Mechanic Roster</div>
        <table class="home-roster-table">
            <thead><tr><th>Name</th><th>Current Assignment</th><th>Availability</th></tr></thead>
            <tbody>${rows}</tbody>
        </table>
    `;
}

// Register loader
viewLoaders['home'] = loadHomeData;
