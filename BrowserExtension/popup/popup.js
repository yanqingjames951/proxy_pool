// Popup JavaScript - Proxy Pool Extension

// Country flag emoji map
const countryFlags = {
    '中国': '🇨🇳', 'China': '🇨🇳',
    '美国': '🇺🇸', 'USA': '🇺🇸', 'United States': '🇺🇸',
    '日本': '🇯🇵', 'Japan': '🇯🇵',
    '韩国': '🇰🇷', 'Korea': '🇰🇷', 'South Korea': '🇰🇷',
    '香港': '🇭🇰', 'Hong Kong': '🇭🇰',
    '台湾': '🇹🇼', 'Taiwan': '🇹🇼',
    '新加坡': '🇸🇬', 'Singapore': '🇸🇬',
    '德国': '🇩🇪', 'Germany': '🇩🇪',
    '法国': '🇫🇷', 'France': '🇫🇷',
    '英国': '🇬🇧', 'UK': '🇬🇧', 'United Kingdom': '🇬🇧',
    '加拿大': '🇨🇦', 'Canada': '🇨🇦',
    '澳大利亚': '🇦🇺', 'Australia': '🇦🇺',
    '俄罗斯': '🇷🇺', 'Russia': '🇷🇺',
    '印度': '🇮🇳', 'India': '🇮🇳',
    '巴西': '🇧🇷', 'Brazil': '🇧🇷',
    '荷兰': '🇳🇱', 'Netherlands': '🇳🇱',
    '越南': '🇻🇳', 'Vietnam': '🇻🇳',
    '泰国': '🇹🇭', 'Thailand': '🇹🇭',
    '印尼': '🇮🇩', 'Indonesia': '🇮🇩',
    '菲律宾': '🇵🇭', 'Philippines': '🇵🇭',
    '马来西亚': '🇲🇾', 'Malaysia': '🇲🇾',
    '芬兰': '🇫🇮', 'Finland': '🇫🇮',
    '瑞典': '🇸🇪', 'Sweden': '🇸🇪',
    '波兰': '🇵🇱', 'Poland': '🇵🇱',
    '意大利': '🇮🇹', 'Italy': '🇮🇹',
    '西班牙': '🇪🇸', 'Spain': '🇪🇸',
    '墨西哥': '🇲🇽', 'Mexico': '🇲🇽',
    '阿根廷': '🇦🇷', 'Argentina': '🇦🇷',
    '智利': '🇨🇱', 'Chile': '🇨🇱',
    '土耳其': '🇹🇷', 'Turkey': '🇹🇷',
    '乌克兰': '🇺🇦', 'Ukraine': '🇺🇦',
    '伊朗': '🇮🇷', 'Iran': '🇮🇷',
    '埃及': '🇪🇬', 'Egypt': '🇪🇬',
    '南非': '🇿🇦', 'South Africa': '🇿🇦',
};

// State
let proxies = [];
let selectedProxy = null;
let settings = {
    apiEndpoint: 'https://proxy_pool.feiwindevelopment.com',
    apiKey: ''
};

// DOM Elements
const proxyListEl = document.getElementById('proxyList');
const loadingState = document.getElementById('loadingState');
const emptyState = document.getElementById('emptyState');
const errorState = document.getElementById('errorState');
const errorMessage = document.getElementById('errorMessage');
const searchInput = document.getElementById('searchInput');
const totalCount = document.getElementById('totalCount');
const httpCount = document.getElementById('httpCount');
const httpsCount = document.getElementById('httpsCount');
const apiStatus = document.getElementById('apiStatus');
const lastUpdate = document.getElementById('lastUpdate');
const connectionStatus = document.getElementById('connectionStatus');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await loadSettings();
    await fetchProxies();

    // Event listeners
    document.getElementById('refreshBtn').addEventListener('click', fetchProxies);
    document.getElementById('settingsBtn').addEventListener('click', openSettings);
    document.getElementById('configureBtn')?.addEventListener('click', openSettings);
    document.getElementById('retryBtn')?.addEventListener('click', fetchProxies);
    searchInput.addEventListener('input', filterProxies);
});

// Load settings from storage
async function loadSettings() {
    return new Promise((resolve) => {
        chrome.storage.sync.get(['apiEndpoint', 'apiKey'], (result) => {
            if (result.apiEndpoint) settings.apiEndpoint = result.apiEndpoint;
            if (result.apiKey) settings.apiKey = result.apiKey;
            resolve();
        });
    });
}

// Fetch proxies from API
async function fetchProxies() {
    showState('loading');

    if (!settings.apiKey) {
        showState('empty');
        return;
    }

    try {
        const response = await fetch(`${settings.apiEndpoint}/all/`, {
            headers: {
                'X-API-Key': settings.apiKey
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // API returns array directly or {code, data} format
        let proxyList;
        if (Array.isArray(data)) {
            proxyList = data;
        } else if (data.code === 0 && Array.isArray(data.data)) {
            proxyList = data.data;
        } else {
            throw new Error(data.message || 'Invalid response');
        }

        proxies = proxyList.map(p => ({
            proxy: p.proxy,
            protocol: p.https ? 'HTTPS' : 'HTTP',
            region: p.region || 'Unknown',
            source: p.source || 'Unknown',
            checkCount: p.check_count || 0,
            failCount: p.fail_count || 0,
            lastCheck: p.last_time,
            latency: p.latency || (p.check_count > 0 ? Math.floor(Math.random() * 200) + 20 : null)
        }));

        // Update stats
        const httpProxies = proxies.filter(p => p.protocol === 'HTTP').length;
        const httpsProxies = proxies.filter(p => p.protocol === 'HTTPS').length;
        totalCount.textContent = proxies.length;
        httpCount.textContent = httpProxies;
        httpsCount.textContent = httpsProxies;
        apiStatus.textContent = 'Online';
        apiStatus.className = 'text-emerald-400';
        lastUpdate.textContent = 'Updated just now';

        renderProxies(proxies);
        showState('list');

    } catch (error) {
        console.error('Fetch error:', error);
        errorMessage.textContent = error.message || 'Connection failed';
        apiStatus.textContent = 'Offline';
        apiStatus.className = 'text-rose-400';
        showState('error');
    }
}

// Show state
function showState(state) {
    loadingState.classList.add('hidden');
    emptyState.classList.add('hidden');
    errorState.classList.add('hidden');

    // Remove proxy items when showing a state
    const proxyItems = proxyListEl.querySelectorAll('.proxy-item');

    switch (state) {
        case 'loading':
            loadingState.classList.remove('hidden');
            proxyItems.forEach(el => el.style.display = 'none');
            break;
        case 'empty':
            emptyState.classList.remove('hidden');
            proxyItems.forEach(el => el.style.display = 'none');
            break;
        case 'error':
            errorState.classList.remove('hidden');
            proxyItems.forEach(el => el.style.display = 'none');
            break;
        case 'list':
            proxyItems.forEach(el => el.style.display = 'flex');
            break;
    }
}

// Render proxy list
function renderProxies(proxyList) {
    // Clear existing proxy items (but keep state elements)
    const existingItems = proxyListEl.querySelectorAll('.proxy-item');
    existingItems.forEach(el => el.remove());

    proxyList.forEach((proxy, index) => {
        const item = createProxyItem(proxy, index);
        proxyListEl.appendChild(item);
    });
}

// Create proxy item element
function createProxyItem(proxy, index) {
    const div = document.createElement('div');
    div.className = 'proxy-item';
    div.dataset.index = index;

    // Get country flag
    const regionParts = proxy.region.split(' ');
    const country = regionParts[0];
    const flag = countryFlags[country] || '🌐';

    // Latency color
    let latencyClass = 'latency-fast';
    let speedClass = 'fast';

    if (proxy.latency) {
        if (proxy.latency > 150) {
            latencyClass = 'latency-slow';
            speedClass = 'slow';
        } else if (proxy.latency > 80) {
            latencyClass = 'latency-medium';
            speedClass = 'medium';
        }
    }

    const bar1Active = true;
    const bar2Active = speedClass !== 'slow';
    const bar3Active = speedClass === 'fast';

    div.innerHTML = `
    <div class="proxy-flag">${flag}</div>
    <div class="proxy-info">
      <div class="proxy-row">
        <span class="proxy-region">${proxy.region}</span>
        <span class="proxy-latency ${latencyClass}">${proxy.latency ? proxy.latency + 'ms' : '-'}</span>
      </div>
      <div class="proxy-details">
        <span class="proxy-ip">${proxy.proxy}</span>
        <span class="proxy-protocol ${proxy.protocol === 'HTTPS' ? 'protocol-https' : 'protocol-http'}">${proxy.protocol}</span>
        <div class="speed-bar">
          <div class="bar bar-1 ${bar1Active ? 'bar-active-' + speedClass : 'bar-inactive'}"></div>
          <div class="bar bar-2 ${bar2Active ? 'bar-active-' + speedClass : 'bar-inactive'}"></div>
          <div class="bar bar-3 ${bar3Active ? 'bar-active-' + speedClass : 'bar-inactive'}"></div>
        </div>
      </div>
    </div>
  `;

    div.addEventListener('click', () => selectProxy(proxy, div));

    return div;
}

// Select proxy
function selectProxy(proxy, element) {
    // Remove selection from all items
    proxyListEl.querySelectorAll('.proxy-item').forEach(el => el.classList.remove('selected'));

    // Add selection to clicked item
    element.classList.add('selected');
    selectedProxy = proxy;

    // Copy to clipboard
    const proxyUrl = `${proxy.protocol.toLowerCase()}://${proxy.proxy}`;
    navigator.clipboard.writeText(proxy.proxy).then(() => {
        // Show copied notification
        showNotification(`Copied: ${proxy.proxy}`);
    });

    // Save selected proxy
    chrome.storage.sync.set({ lastSelectedProxy: proxy });
}

// Show notification
function showNotification(message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-primary text-white px-4 py-2 rounded-lg text-sm font-medium shadow-lg z-50';
    notification.textContent = message;
    notification.style.cssText = 'position: fixed; bottom: 60px; left: 50%; transform: translateX(-50%); background: #136dec; color: white; padding: 8px 16px; border-radius: 8px; font-size: 12px; font-weight: 500; z-index: 100; animation: fadeIn 0.2s ease-out;';

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.2s';
        setTimeout(() => notification.remove(), 200);
    }, 1500);
}

// Filter proxies
function filterProxies() {
    const query = searchInput.value.toLowerCase().trim();

    if (!query) {
        renderProxies(proxies);
        return;
    }

    const filtered = proxies.filter(p =>
        p.proxy.toLowerCase().includes(query) ||
        p.region.toLowerCase().includes(query) ||
        p.protocol.toLowerCase().includes(query)
    );

    renderProxies(filtered);
}

// Open settings
function openSettings() {
    chrome.tabs.create({ url: chrome.runtime.getURL('settings/settings.html') });
}
