// Settings JavaScript - Proxy Pool Extension

// DOM Elements
const apiEndpointInput = document.getElementById('apiEndpoint');
const apiKeyInput = document.getElementById('apiKey');
const togglePasswordBtn = document.getElementById('togglePassword');
const testBtn = document.getElementById('testBtn');
const endpointStatus = document.getElementById('endpointStatus');
const saveBtn = document.getElementById('saveBtn');
const cancelBtn = document.getElementById('cancelBtn');
const closeBtn = document.getElementById('closeBtn');

// State
let passwordVisible = false;

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await loadSettings();

    // Event listeners
    togglePasswordBtn.addEventListener('click', togglePassword);
    testBtn.addEventListener('click', testConnection);
    saveBtn.addEventListener('click', saveSettings);
    cancelBtn.addEventListener('click', closeSettings);
    closeBtn.addEventListener('click', closeSettings);

    // Input validation
    apiEndpointInput.addEventListener('input', validateEndpoint);
});

// Load settings from storage
async function loadSettings() {
    return new Promise((resolve) => {
        chrome.storage.sync.get(['apiEndpoint', 'apiKey'], (result) => {
            if (result.apiEndpoint) {
                apiEndpointInput.value = result.apiEndpoint;
            }
            if (result.apiKey) {
                apiKeyInput.value = result.apiKey;
            }
            validateEndpoint();
            resolve();
        });
    });
}

// Toggle password visibility
function togglePassword() {
    passwordVisible = !passwordVisible;
    apiKeyInput.type = passwordVisible ? 'text' : 'password';
    togglePasswordBtn.innerHTML = `<span class="material-symbols-outlined">${passwordVisible ? 'visibility_off' : 'visibility'}</span>`;
}

// Validate endpoint URL
function validateEndpoint() {
    const url = apiEndpointInput.value.trim();
    let isValid = false;

    try {
        new URL(url);
        isValid = url.startsWith('http://') || url.startsWith('https://');
    } catch {
        isValid = false;
    }

    endpointStatus.innerHTML = isValid
        ? '<span class="material-symbols-outlined" style="color: #10b981;">check_circle</span>'
        : '<span class="material-symbols-outlined" style="color: #64748b;">help</span>';

    return isValid;
}

// Test API connection
async function testConnection() {
    const endpoint = apiEndpointInput.value.trim();
    const apiKey = apiKeyInput.value.trim();

    if (!endpoint) {
        showNotification('Please enter API endpoint', 'error');
        return;
    }

    if (!apiKey) {
        showNotification('Please enter API key', 'error');
        return;
    }

    // Show loading
    testBtn.disabled = true;
    testBtn.textContent = 'Testing...';

    try {
        const response = await fetch(`${endpoint}/count/`, {
            method: 'GET',
            headers: {
                'X-API-Key': apiKey
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.count !== undefined) {
            showNotification(`Connected! ${data.count} proxies available`, 'success');
        } else {
            throw new Error('Invalid response');
        }

    } catch (error) {
        showNotification(error.message || 'Connection failed', 'error');
    } finally {
        testBtn.disabled = false;
        testBtn.textContent = 'Test';
    }
}

// Save settings
async function saveSettings() {
    const endpoint = apiEndpointInput.value.trim();
    const apiKey = apiKeyInput.value.trim();

    if (!endpoint) {
        showNotification('Please enter API endpoint', 'error');
        return;
    }

    if (!apiKey) {
        showNotification('Please enter API key', 'error');
        return;
    }

    // Remove trailing slash
    const cleanEndpoint = endpoint.replace(/\/+$/, '');

    try {
        await new Promise((resolve, reject) => {
            chrome.storage.sync.set({
                apiEndpoint: cleanEndpoint,
                apiKey: apiKey
            }, () => {
                if (chrome.runtime.lastError) {
                    reject(chrome.runtime.lastError);
                } else {
                    resolve();
                }
            });
        });

        showNotification('Settings saved!', 'success');

        // Close after short delay
        setTimeout(() => {
            window.close();
        }, 1000);

    } catch (error) {
        showNotification('Failed to save settings', 'error');
    }
}

// Close settings
function closeSettings() {
    window.close();
}

// Show notification
function showNotification(message, type = 'info') {
    // Remove any existing notifications
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}
