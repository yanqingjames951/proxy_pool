// Background Service Worker - Proxy Pool Extension

// Extension installed
chrome.runtime.onInstalled.addListener((details) => {
    if (details.reason === 'install') {
        // Set default settings
        chrome.storage.sync.set({
            apiEndpoint: 'https://proxy_pool.feiwindevelopment.com',
            apiKey: ''
        });

        // Open settings page on first install
        chrome.tabs.create({
            url: chrome.runtime.getURL('settings/settings.html')
        });
    }
});

// Handle messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'GET_PROXY') {
        getRandomProxy().then(sendResponse);
        return true; // Keep channel open for async response
    }

    if (message.type === 'TEST_CONNECTION') {
        testConnection(message.endpoint, message.apiKey).then(sendResponse);
        return true;
    }
});

// Get random proxy from API
async function getRandomProxy() {
    try {
        const { apiEndpoint, apiKey } = await chrome.storage.sync.get(['apiEndpoint', 'apiKey']);

        if (!apiEndpoint || !apiKey) {
            return { success: false, error: 'Not configured' };
        }

        const response = await fetch(`${apiEndpoint}/get/`, {
            headers: { 'X-API-Key': apiKey }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        return { success: true, proxy: data };

    } catch (error) {
        return { success: false, error: error.message };
    }
}

// Test API connection
async function testConnection(endpoint, apiKey) {
    try {
        const response = await fetch(`${endpoint}/count/`, {
            headers: { 'X-API-Key': apiKey }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        return { success: true, count: data.count };

    } catch (error) {
        return { success: false, error: error.message };
    }
}

// Badge update (optional - shows proxy count on icon)
async function updateBadge() {
    try {
        const { apiEndpoint, apiKey } = await chrome.storage.sync.get(['apiEndpoint', 'apiKey']);

        if (!apiEndpoint || !apiKey) {
            chrome.action.setBadgeText({ text: '' });
            return;
        }

        const response = await fetch(`${apiEndpoint}/count/`, {
            headers: { 'X-API-Key': apiKey }
        });

        if (response.ok) {
            const data = await response.json();
            const count = data.count || 0;
            chrome.action.setBadgeText({ text: count > 999 ? '999+' : count.toString() });
            chrome.action.setBadgeBackgroundColor({ color: '#10b981' });
        } else {
            chrome.action.setBadgeText({ text: '!' });
            chrome.action.setBadgeBackgroundColor({ color: '#f43f5e' });
        }

    } catch (error) {
        chrome.action.setBadgeText({ text: '!' });
        chrome.action.setBadgeBackgroundColor({ color: '#f43f5e' });
    }
}

// Update badge periodically
setInterval(updateBadge, 60000); // Every minute
