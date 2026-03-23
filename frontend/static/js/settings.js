async function loadSettings() {
    const el = document.getElementById('licenseText');
    if (el.dataset.loaded) return;
    try {
        const res = await fetch('/api/license');
        el.textContent = await res.text();
        el.dataset.loaded = '1';
    } catch (e) {
        el.textContent = 'Failed to load license.';
    }
}

viewLoaders.settings = loadSettings;
