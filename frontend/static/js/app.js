// View navigation
function showView(viewName, updateHistory = true) {
    // Hide all views
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });

    // Remove active from all nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });

    // Show selected view
    document.getElementById(viewName).classList.add('active');

    // Set active nav item
    document.querySelector(`[data-view="${viewName}"]`).classList.add('active');

    // Update page title
    const titles = {
        'schedule': 'Schedule',
        'resources': 'Resources',
        'projects': 'Projects',
        'history': 'History',
    };
    document.getElementById('pageTitle').textContent = titles[viewName];

    // Load data for the new view
    currentView = viewName;
    viewLoaders[viewName]().catch(err => console.error('Error loading data:', err));

    // Plotly needs a resize when the schedule view becomes visible
    if (viewName === 'schedule') {
        Plotly.Plots.resize('ganttChart');
    }

    // Update URL without page reload
    if (updateHistory) {
        const url = viewName === 'schedule' ? '/' : `/${viewName}`;
        history.pushState({ view: viewName }, '', url);
    }
}

// Handle browser back/forward buttons
window.addEventListener('popstate', (event) => {
    if (event.state && event.state.view) {
        showView(event.state.view, false);
    } else {
        showView(getViewFromURL(), false);
    }
});

// Get view name from current URL
function getViewFromURL() {
    const path = window.location.pathname;
    if (path === '/' || path === '/schedule' || path === '/overview' || path === '/assignments') return 'schedule';
    if (path === '/resources' || path === '/personnel' || path === '/skills') return 'resources';
    if (path === '/projects') return 'projects';
    if (path === '/history') return 'history';
    return 'schedule'; // default
}

// Initialize navigation
function initNavigation() {
    // Add click handlers to nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const viewName = item.getAttribute('data-view');
            showView(viewName);
        });
    });

    // Show correct view based on URL on page load
    const initialView = getViewFromURL();
    showView(initialView, false);

    // Set initial history state
    history.replaceState({ view: initialView }, '', window.location.pathname);
}

// Refresh data (current view only)
async function refreshData() {
    const button = document.getElementById('refreshButton');
    button.classList.add('loading');
    button.disabled = true;

    try {
        await viewLoaders[currentView]();
    } catch (error) {
        console.error('Error refreshing data:', error);
        alert('Failed to refresh data. Please check your connection.');
    } finally {
        button.classList.remove('loading');
        button.disabled = false;
    }
}

// Initialize app
async function init() {
    populateStatusSelects();
    await loadScenarios();
    initNavigation();
}
init();
