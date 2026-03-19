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
        renderProjectStats(homeCache.project_stats);
        renderPersonnelStats(homeCache.personnel_stats);
        document.getElementById('homeAssessmentLoading').style.display = 'none';
        document.getElementById('homeAssessmentContent').innerHTML = homeCache.assessmentHtml;
        return;
    }

    const params = currentScenarioId ? `?scenario_id=${currentScenarioId}` : '';
    const res = await fetch(`/api/home/stats${params}`);
    const stats = await res.json();

    // Render stat tiles immediately
    renderProjectStats(stats.project_stats);
    renderPersonnelStats(stats.personnel_stats);

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

function renderProjectStats(stats) {
    const container = document.getElementById('homeProjectStats');
    if (!stats || !stats.total_projects) {
        container.innerHTML = '<div class="home-stat-empty">No awarded projects</div>';
        return;
    }
    container.innerHTML = `
        <div class="home-stat-pair">
            <span class="home-stat-label">Total Awarded</span>
            <span class="home-stat-value">${stats.total_projects}</span>
        </div>
        <div class="home-stat-pair">
            <span class="home-stat-label">Staffed</span>
            <span class="home-stat-value">${stats.staffed_count}</span>
        </div>
        <div class="home-stat-pair">
            <span class="home-stat-label">Unstaffed</span>
            <span class="home-stat-value">${stats.unstaffed_count}</span>
        </div>
        <div class="home-stat-pair highlight">
            <span class="home-stat-label">Staffed %</span>
            <span class="home-stat-value">${stats.staffed_pct}%</span>
        </div>
    `;
}

function renderPersonnelStats(stats) {
    const container = document.getElementById('homePersonnelStats');
    if (!stats || !stats.total_roster) {
        container.innerHTML = '<div class="home-stat-empty">No personnel</div>';
        return;
    }
    container.innerHTML = `
        <div class="home-stat-pair">
            <span class="home-stat-label">Total Roster</span>
            <span class="home-stat-value">${stats.total_roster}</span>
        </div>
        <div class="home-stat-pair">
            <span class="home-stat-label">Currently Active</span>
            <span class="home-stat-value">${stats.currently_assigned}</span>
        </div>
        <div class="home-stat-pair">
            <span class="home-stat-label">Has Future Work</span>
            <span class="home-stat-value">${stats.has_future_assignment}</span>
        </div>
        <div class="home-stat-pair highlight">
            <span class="home-stat-label">Unassigned</span>
            <span class="home-stat-value">${stats.unassigned}</span>
        </div>
    `;
}

// Register loader
viewLoaders['home'] = loadHomeData;
