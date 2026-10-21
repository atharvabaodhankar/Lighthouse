/**
 * Lighthouse — Production Client Logic
 * Streamlined Navigation, Responsive Mobile Drawer, Multi-Platform Setup Guide,
 * and Live Query Log Flush Functionality.
 */

let currentTab = 'overview';
let currentTheme = localStorage.getItem('lighthouse_theme') || 'resend';
let refreshInterval = 5000;
let refreshTimer = null;
let trafficChart = null;
let queryTypeChart = null;

document.addEventListener('DOMContentLoaded', () => {
    applyTheme(currentTheme);
    initNavigation();
    initCharts();
    loadAllData();
    startPolling();
    initSearchAndFilters();
    initKeyboardShortcuts();
});

// -----------------------------------------------------------------------------
// Theme Management
// -----------------------------------------------------------------------------

function applyTheme(theme) {
    currentTheme = theme;
    localStorage.setItem('lighthouse_theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
    
    const icon = document.getElementById('themeToggleIcon');
    if (icon) {
        // In dark mode (resend), show sun (click to toggle light); in light mode (notion), show moon
        icon.setAttribute('data-lucide', theme === 'resend' ? 'sun' : 'moon');
    }

    if (trafficChart) {
        updateChartTheme();
    }

    if (window.lucide) {
        window.lucide.createIcons();
    }
}

function toggleTheme() {
    const nextTheme = currentTheme === 'resend' ? 'notion' : 'resend';
    applyTheme(nextTheme);
    showToast(`Switched to ${nextTheme === 'resend' ? 'Obsidian Dark' : 'Notion Warm Light'}`);
}

function updateChartTheme() {
    const isDark = currentTheme === 'resend';
    if (!trafficChart) return;

    trafficChart.data.datasets[0].borderColor = isDark ? '#52525b' : '#9b9a97';
    trafficChart.data.datasets[0].backgroundColor = isDark ? 'rgba(82, 82, 91, 0.12)' : 'rgba(155, 154, 151, 0.08)';
    trafficChart.data.datasets[1].borderColor = isDark ? '#3b82f6' : '#0075de';
    trafficChart.data.datasets[1].backgroundColor = isDark ? 'rgba(59, 130, 246, 0.14)' : 'rgba(0, 117, 222, 0.10)';

    trafficChart.options.scales.x.grid.color = isDark ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.05)';
    trafficChart.options.scales.y.grid.color = isDark ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.05)';
    trafficChart.options.plugins.tooltip.backgroundColor = isDark ? '#18191e' : '#ffffff';
    trafficChart.options.plugins.tooltip.titleColor = isDark ? '#f4f4f5' : '#191817';
    trafficChart.options.plugins.tooltip.bodyColor = isDark ? '#a1a1aa' : '#5f5e5b';
    trafficChart.options.plugins.tooltip.borderColor = isDark ? 'rgba(255, 255, 255, 0.14)' : 'rgba(0, 0, 0, 0.12)';
    trafficChart.update('none');

    if (queryTypeChart) {
        queryTypeChart.data.datasets[0].borderColor = isDark ? '#111215' : '#ffffff';
        queryTypeChart.data.datasets[0].backgroundColor = isDark 
            ? ['#3b82f6', '#f97316', '#10b981', '#f59e0b', '#8b5cf6', '#52525b']
            : ['#0075de', '#c2410c', '#15803d', '#d97706', '#7c3aed', '#9b9a97'];
        queryTypeChart.update('none');
    }
}

// -----------------------------------------------------------------------------
// Navigation & Mobile Drawer
// -----------------------------------------------------------------------------

function initNavigation() {
    document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tab = item.getAttribute('data-tab');
            switchTab(tab);
        });
    });

    const rateSelect = document.getElementById('refreshRateSelect');
    if (rateSelect) {
        rateSelect.addEventListener('change', (e) => {
            const val = parseInt(e.target.value);
            refreshInterval = val;
            startPolling();
            showToast(`Auto-refresh set to ${val === 0 ? 'paused' : (val/1000) + 's'}`);
        });
    }
}

function toggleMobileMenu() {
    const sidebar = document.getElementById('notionSidebar');
    const backdrop = document.getElementById('sidebarBackdrop');
    if (!sidebar) return;

    const isOpen = sidebar.classList.contains('open');
    if (isOpen) {
        closeMobileMenu();
    } else {
        sidebar.classList.add('open');
        backdrop?.classList.add('open');
    }
}

function closeMobileMenu() {
    const sidebar = document.getElementById('notionSidebar');
    const backdrop = document.getElementById('sidebarBackdrop');
    sidebar?.classList.remove('open');
    backdrop?.classList.remove('open');
}

function switchTab(tabId) {
    currentTab = tabId;
    closeMobileMenu();

    document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => {
        item.classList.toggle('active', item.getAttribute('data-tab') === tabId);
    });

    document.querySelectorAll('.view-panel').forEach(panel => {
        panel.style.display = panel.id === `view-${tabId}` ? 'block' : 'none';
    });

    const bcElem = document.getElementById('currentBreadcrumb');
    if (bcElem) {
        const labels = {
            'overview': 'Traffic & analytics',
            'queries': 'Query log',
            'devices': 'Guarded devices',
            'setup': 'Connect & setup guide',
            'rules': 'Filtering rules',
            'telegram': 'Daily briefing',
            'settings': 'Cloud infrastructure'
        };
        bcElem.textContent = labels[tabId] || tabId;
    }

    if (window.lucide) {
        window.lucide.createIcons();
    }

    if (tabId === 'overview') {
        setTimeout(() => {
            if (trafficChart) trafficChart.resize();
        }, 80);
    }
}

function switchSetupPlatform(platformId) {
    document.querySelectorAll('.setup-tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-platform') === platformId);
    });

    document.querySelectorAll('.platform-guide').forEach(guide => {
        guide.classList.toggle('active', guide.id === `guide-${platformId}`);
    });

    if (window.lucide) {
        window.lucide.createIcons();
    }
}

function copyToClipboard(text, btnElement) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
            handleCopiedState(btnElement);
        }).catch(() => fallbackCopy(text, btnElement));
    } else {
        fallbackCopy(text, btnElement);
    }
}

function fallbackCopy(text, btnElement) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
        document.execCommand('copy');
        handleCopiedState(btnElement);
    } catch (err) {
        showToast('Failed to copy');
    }
    document.body.removeChild(textArea);
}

function handleCopiedState(btnElement) {
    if (btnElement) {
        btnElement.classList.add('copied');
        const originalText = btnElement.innerHTML;
        btnElement.innerHTML = `<i data-lucide="check" style="width:12px; height:12px;"></i><span>Copied!</span>`;
        if (window.lucide) window.lucide.createIcons();
        setTimeout(() => {
            btnElement.classList.remove('copied');
            btnElement.innerHTML = originalText;
            if (window.lucide) window.lucide.createIcons();
        }, 2000);
    }
    showToast('Copied to clipboard');
}

// -----------------------------------------------------------------------------
// Flush Logs Feature
// -----------------------------------------------------------------------------

function openFlushModal() {
    openModal('flushModal');
}

function closeFlushModal() {
    closeModal('flushModal');
}

async function confirmFlushLogs() {
    const btn = document.getElementById('confirmFlushBtn');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<i data-lucide="loader-2" style="width:14px; height:14px; animation:spin 1s linear infinite;"></i><span>Flushing...</span>`;
    }

    try {
        const res = await fetch('/api/logs/flush', { method: 'POST' });
        const data = await res.json();
        
        closeFlushModal();
        showToast('DNS query logs flushed successfully');
        
        // Reload all data to reflect flushed logs
        await loadAllData();
    } catch (e) {
        console.error('Failed to flush logs', e);
        showToast('Failed to flush logs');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<i data-lucide="trash-2" style="width:14px; height:14px;"></i><span>Flush all logs</span>`;
            if (window.lucide) window.lucide.createIcons();
        }
    }
}

// -----------------------------------------------------------------------------
// Polling & Data Loading
// -----------------------------------------------------------------------------

function startPolling() {
    if (refreshTimer) clearInterval(refreshTimer);
    if (refreshInterval > 0) {
        refreshTimer = setInterval(() => {
            loadSummary();
            if (currentTab === 'queries') loadQueries();
            if (currentTab === 'overview') loadChart();
        }, refreshInterval);
    }
}

async function loadAllData() {
    await Promise.all([
        loadSummary(),
        loadChart(),
        loadTopItems(),
        loadQueries(),
        loadClients(),
        loadRules()
    ]);
    if (window.lucide) {
        window.lucide.createIcons();
    }
}

// -----------------------------------------------------------------------------
// Data Fetching & Rendering
// -----------------------------------------------------------------------------

async function loadSummary() {
    try {
        const res = await fetch('/api/summary');
        const data = await res.json();

        const isEnabled = data.status === 'enabled';
        const dot = document.getElementById('statusDot');
        if (dot) dot.className = `status-dot ${isEnabled ? '' : 'disabled'}`;
        
        const statusText = document.getElementById('statusText');
        if (statusText) statusText.textContent = isEnabled ? 'Shield active' : 'Shield paused';
        
        const clientCount = data.unique_clients !== undefined ? data.unique_clients : (data.clients_ever_seen || 0);
        const heroStatus = document.getElementById('heroStatusText');
        if (heroStatus) {
            heroStatus.textContent = isEnabled 
                ? `Guarding ${clientCount} active client${clientCount === 1 ? '' : 's'} · Live Pi-hole v6 engine`
                : 'Protection temporarily paused';
        }

        const heroToggleBtn = document.getElementById('heroToggleBtn');
        if (heroToggleBtn) {
            heroToggleBtn.innerHTML = isEnabled 
                ? `<i data-lucide="pause-circle" style="width:14px; height:14px;"></i><span>Pause protection</span>` 
                : `<i data-lucide="play-circle" style="width:14px; height:14px;"></i><span>Resume protection</span>`;
            if (window.lucide) window.lucide.createIcons();
        }

        document.getElementById('metricTotalQueries').textContent = (data.dns_queries_today || 0).toLocaleString();
        document.getElementById('metricBlockedQueries').textContent = (data.ads_blocked_today || 0).toLocaleString();
        document.getElementById('metricBlockPercentage').textContent = `${data.ads_percentage_today || 0}%`;
        document.getElementById('metricGravitySize').textContent = (data.domains_being_blocked || 0).toLocaleString();
        document.getElementById('metricClientsCount').textContent = clientCount;
        document.getElementById('metricLatency').textContent = `${data.avg_latency_ms || 11.4} ms`;

        const badge = document.getElementById('sidebarDevicesBadge');
        if (badge) badge.textContent = clientCount;

    } catch (e) {
        console.error('Failed to load summary', e);
    }
}

function initCharts() {
    const isDark = currentTheme === 'resend';
    
    // Area Traffic Chart
    const trafficCtx = document.getElementById('trafficChartCanvas')?.getContext('2d');
    if (trafficCtx) {
        trafficChart = new Chart(trafficCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Total queries',
                        data: [],
                        borderColor: isDark ? '#52525b' : '#9b9a97',
                        backgroundColor: isDark ? 'rgba(82, 82, 91, 0.12)' : 'rgba(155, 154, 151, 0.08)',
                        fill: true,
                        tension: 0.35,
                        borderWidth: 1.5,
                        pointRadius: 0,
                        pointHoverRadius: 4
                    },
                    {
                        label: 'Blocked trackers',
                        data: [],
                        borderColor: isDark ? '#3b82f6' : '#0075de',
                        backgroundColor: isDark ? 'rgba(59, 130, 246, 0.14)' : 'rgba(0, 117, 222, 0.10)',
                        fill: true,
                        tension: 0.35,
                        borderWidth: 1.5,
                        pointRadius: 0,
                        pointHoverRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: isDark ? '#18191e' : '#ffffff',
                        titleColor: isDark ? '#f4f4f5' : '#191817',
                        bodyColor: isDark ? '#a1a1aa' : '#5f5e5b',
                        borderColor: isDark ? 'rgba(255, 255, 255, 0.14)' : 'rgba(0, 0, 0, 0.12)',
                        borderWidth: 1,
                        padding: 10,
                        cornerRadius: 6,
                        displayColors: true,
                        boxPadding: 4,
                        callbacks: {
                            label: (ctx) => ` ${ctx.dataset.label}: ${ctx.raw.toLocaleString()}`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: isDark ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.05)' },
                        ticks: { color: isDark ? '#71717a' : '#787774', font: { family: 'JetBrains Mono', size: 10.5 } }
                    },
                    y: {
                        grid: { color: isDark ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.05)' },
                        ticks: { color: isDark ? '#71717a' : '#787774', font: { family: 'JetBrains Mono', size: 10.5 } },
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Doughnut Query Types Chart
    const typeCtx = document.getElementById('queryTypeChartCanvas')?.getContext('2d');
    if (typeCtx) {
        queryTypeChart = new Chart(typeCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: isDark 
                        ? ['#3b82f6', '#f97316', '#10b981', '#f59e0b', '#8b5cf6', '#52525b']
                        : ['#0075de', '#c2410c', '#15803d', '#d97706', '#7c3aed', '#9b9a97'],
                    borderColor: isDark ? '#111215' : '#ffffff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: isDark ? '#a1a1aa' : '#5f5e5b',
                            font: { family: 'Inter', size: 11.5 },
                            padding: 12,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` ${ctx.label}: ${ctx.raw}%`
                        }
                    }
                },
                cutout: '72%'
            }
        });
    }
}

async function loadChart() {
    try {
        const res = await fetch('/api/chart');
        const data = await res.json();

        if (trafficChart && data.labels) {
            trafficChart.data.labels = data.labels;
            trafficChart.data.datasets[0].data = data.total_queries;
            trafficChart.data.datasets[1].data = data.blocked_queries;
            trafficChart.update('none');
        }
    } catch (e) {
        console.error('Failed to load chart', e);
    }
}

async function loadTopItems() {
    try {
        const res = await fetch('/api/top-items');
        const data = await res.json();

        const permittedList = document.getElementById('topPermittedList');
        if (permittedList && data.top_queries) {
            permittedList.innerHTML = data.top_queries.slice(0, 6).map(q => `
                <div class="domain-ranking-row">
                    <span class="domain-name" title="${q.domain}">${q.domain}</span>
                    <span class="domain-count">${q.count.toLocaleString()}</span>
                </div>
            `).join('') || `<div class="domain-ranking-row"><span class="domain-name">No queries recorded yet</span></div>`;
        }

        const blockedList = document.getElementById('topBlockedList');
        if (blockedList && data.top_ads) {
            blockedList.innerHTML = data.top_ads.slice(0, 6).map(q => `
                <div class="domain-ranking-row">
                    <span class="domain-name text-blocked" title="${q.domain}">${q.domain}</span>
                    <span class="domain-count">${q.count.toLocaleString()}</span>
                </div>
            `).join('') || `<div class="domain-ranking-row"><span class="domain-name">No threats sinkholed today</span></div>`;
        }

        if (queryTypeChart && data.query_types) {
            queryTypeChart.data.labels = Object.keys(data.query_types);
            queryTypeChart.data.datasets[0].data = Object.values(data.query_types);
            queryTypeChart.update('none');
        }
    } catch (e) {
        console.error('Failed to load top items', e);
    }
}

async function loadQueries() {
    try {
        const filterType = document.querySelector('input[name="queryFilter"]:checked')?.value || 'all';
        const search = document.getElementById('querySearchInput')?.value || '';
        const res = await fetch(`/api/queries?limit=50&filter_type=${filterType}&search=${encodeURIComponent(search)}`);
        const data = await res.json();

        const tbody = document.getElementById('queriesTableBody');
        const counter = document.getElementById('queryCountBadge');
        if (!tbody) return;

        const queries = data.queries || [];
        if (counter) counter.textContent = `${queries.length} items`;

        if (queries.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:32px; color:var(--color-mute);">No DNS queries found matching your search</td></tr>`;
            return;
        }

        tbody.innerHTML = queries.map(q => {
            const isBlocked = q.status === 'Blocked';
            return `
                <tr>
                    <td class="font-mono" style="color:var(--color-mute); font-size:11.5px;">${q.timestamp}</td>
                    <td>
                        <span class="status-indicator-tag ${isBlocked ? 'blocked' : 'permitted'}">
                            ${isBlocked ? 'Blocked' : 'Permitted'}
                        </span>
                    </td>
                    <td>
                        <div class="font-mono" style="font-size:12.5px; font-weight:500; ${isBlocked ? 'color:var(--color-accent-red);' : ''}">
                            ${q.domain}
                        </div>
                    </td>
                    <td>
                        <span class="font-mono" style="font-size:11.5px; color:var(--color-mute);">${q.query_type}</span>
                    </td>
                    <td>
                        <div style="font-size:12.5px; font-weight:500;">${q.client_name}</div>
                        <div class="font-mono" style="font-size:11px; color:var(--color-mute);">${q.client_ip}</div>
                    </td>
                    <td style="text-align:right;">
                        <button class="btn-ghost" onclick="quickToggleRule('${q.domain}', '${isBlocked ? 'allowed' : 'blocked'}')" title="${isBlocked ? 'Whitelist domain' : 'Block domain'}">
                            <span>${isBlocked ? 'Allow' : 'Block'}</span>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

    } catch (e) {
        console.error('Failed to load queries', e);
    }
}

async function loadClients() {
    try {
        const res = await fetch('/api/clients');
        const data = await res.json();
        const container = document.getElementById('devicesContainer');
        if (!container) return;

        const clients = data.clients || [];
        const badge = document.getElementById('sidebarDevicesBadge');
        if (badge) badge.textContent = clients.length;

        const iconMap = {
            'laptop': 'laptop',
            'mobile': 'smartphone',
            'tv': 'tv',
            'iot': 'cpu'
        };

        container.innerHTML = clients.map(c => `
            <div class="device-card">
                <div class="device-card-header">
                    <div class="device-icon-box">
                        <i data-lucide="${iconMap[c.type] || 'laptop'}" style="width:16px; height:16px;"></i>
                    </div>
                    <div>
                        <div class="device-name">${c.name}</div>
                        <div class="device-ip font-mono">${c.ip} · ${c.mac}</div>
                    </div>
                    <span class="status-indicator-tag permitted" style="margin-left:auto;">Online</span>
                </div>
                <div class="device-stats">
                    <div class="device-stat-item">
                        <div class="stat-label">Queries (24h)</div>
                        <div class="stat-value tabular font-mono">${c.total_queries.toLocaleString()}</div>
                    </div>
                    <div class="device-stat-item">
                        <div class="stat-label">Sinkholed trackers</div>
                        <div class="stat-value tabular font-mono text-blocked">${c.blocked_queries.toLocaleString()} (${c.block_rate}%)</div>
                    </div>
                </div>
            </div>
        `).join('');

        if (window.lucide) {
            window.lucide.createIcons();
        }

    } catch (e) {
        console.error('Failed to load clients', e);
    }
}

async function loadRules() {
    try {
        const res = await fetch('/api/rules');
        const data = await res.json();

        const blockedBody = document.getElementById('blockedRulesBody');
        if (blockedBody && data.blocked) {
            blockedBody.innerHTML = data.blocked.map(r => `
                <tr>
                    <td class="font-mono" style="color:var(--color-accent-red); font-weight:500;">${r.domain}</td>
                    <td><span class="meta-tag">${r.type}</span></td>
                    <td style="color:var(--color-charcoal);">${r.comment || '—'}</td>
                    <td class="font-mono" style="font-size:11.5px; color:var(--color-mute);">${r.added_at}</td>
                    <td style="text-align:right;">
                        <button class="btn-ghost" style="color:var(--color-accent-red);" onclick="deleteRule('${r.domain}', 'blocked')">
                            <i data-lucide="trash-2" style="width:13px; height:13px;"></i>
                        </button>
                    </td>
                </tr>
            `).join('') || `<tr><td colspan="5" style="text-align:center; padding:18px; color:var(--color-mute);">No custom blocked domains</td></tr>`;
        }

        const allowedBody = document.getElementById('allowedRulesBody');
        if (allowedBody && data.allowed) {
            allowedBody.innerHTML = data.allowed.map(r => `
                <tr>
                    <td class="font-mono" style="color:var(--color-accent-green); font-weight:500;">${r.domain}</td>
                    <td><span class="meta-tag">${r.type}</span></td>
                    <td style="color:var(--color-charcoal);">${r.comment || '—'}</td>
                    <td class="font-mono" style="font-size:11.5px; color:var(--color-mute);">${r.added_at}</td>
                    <td style="text-align:right;">
                        <button class="btn-ghost" style="color:var(--color-accent-red);" onclick="deleteRule('${r.domain}', 'allowed')">
                            <i data-lucide="trash-2" style="width:13px; height:13px;"></i>
                        </button>
                    </td>
                </tr>
            `).join('') || `<tr><td colspan="5" style="text-align:center; padding:18px; color:var(--color-mute);">No custom whitelisted domains</td></tr>`;
        }

        if (window.lucide) {
            window.lucide.createIcons();
        }

    } catch (e) {
        console.error('Failed to load rules', e);
    }
}

// -----------------------------------------------------------------------------
// Protection Toggling & Rules Management
// -----------------------------------------------------------------------------

function handleToggleProtection() {
    const statusText = document.getElementById('statusText')?.textContent;
    if (statusText && statusText.includes('paused')) {
        applyProtectionToggle(true, 0);
    } else {
        openModal('pauseModal');
    }
}

async function applyProtectionToggle(enable, duration) {
    closeModal('pauseModal');
    try {
        const res = await fetch('/api/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enable, duration })
        });
        const data = await res.json();
        if (data.success) {
            showToast(enable ? 'DNS protection resumed' : `DNS protection paused for ${duration === 0 ? 'indefinitely' : (duration/60) + ' min'}`);
            loadSummary();
        }
    } catch (e) {
        showToast('Failed to toggle protection');
    }
}

async function quickToggleRule(domain, listType) {
    try {
        const res = await fetch('/api/rules', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                domain,
                list_type: listType,
                rule_type: 'exact',
                comment: 'Added from live query log'
            })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Added ${domain} to ${listType}`);
            loadRules();
            loadQueries();
        }
    } catch (e) {
        showToast('Failed to update rule');
    }
}

async function handleAddRuleSubmit(e) {
    e.preventDefault();
    const domain = document.getElementById('newRuleDomain').value.trim();
    const listType = document.getElementById('newRuleListType').value;
    const ruleType = document.getElementById('newRuleType').value;
    const comment = document.getElementById('newRuleComment').value.trim();

    if (!domain) return;

    try {
        const res = await fetch('/api/rules', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ domain, list_type: listType, rule_type: ruleType, comment })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Rule added: ${domain}`);
            closeModal('addRuleModal');
            document.getElementById('addRuleForm').reset();
            loadRules();
        } else {
            showToast(data.error || 'Failed to add rule');
        }
    } catch (e) {
        showToast('Failed to add rule');
    }
}

async function deleteRule(domain, listType) {
    if (!confirm(`Remove rule for ${domain}?`)) return;

    try {
        const res = await fetch('/api/rules', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ domain, list_type: listType })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Rule removed: ${domain}`);
            loadRules();
        }
    } catch (e) {
        showToast('Failed to delete rule');
    }
}

async function handleTelegramPreview() {
    try {
        const res = await fetch('/api/telegram/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ preview_only: true })
        });
        const data = await res.json();
        if (data.preview) {
            document.getElementById('telegramPreviewText').textContent = data.preview;
            openModal('telegramModal');
        }
    } catch (e) {
        showToast('Failed to generate Telegram preview');
    }
}

async function handleSendTelegramTest() {
    try {
        const res = await fetch('/api/telegram/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ preview_only: false })
        });
        const data = await res.json();
        if (data.success) {
            showToast('Telegram briefing dispatched');
            closeModal('telegramModal');
        } else {
            showToast(data.error || 'Could not send Telegram message');
        }
    } catch (e) {
        showToast('Failed to dispatch alert');
    }
}

// -----------------------------------------------------------------------------
// UI Utilities
// -----------------------------------------------------------------------------

function openModal(id) {
    document.getElementById(id)?.classList.add('open');
    if (window.lucide) window.lucide.createIcons();
}

function closeModal(id) {
    document.getElementById(id)?.classList.remove('open');
}

function showToast(message) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'notion-toast';
    toast.innerHTML = `<i data-lucide="check-circle" style="width:14px; height:14px; color:var(--color-accent-green);"></i><span>${message}</span>`;
    container.appendChild(toast);
    if (window.lucide) window.lucide.createIcons();

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(6px)';
        toast.style.transition = 'all 140ms cubic-bezier(0.22, 1, 0.36, 1)';
        setTimeout(() => toast.remove(), 140);
    }, 2800);
}

function initSearchAndFilters() {
    const searchInput = document.getElementById('querySearchInput');
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                loadQueries();
            }, 200);
        });
    }

    document.querySelectorAll('input[name="queryFilter"]').forEach(radio => {
        radio.addEventListener('change', () => {
            loadQueries();
        });
    });
}

function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            switchTab('queries');
            const search = document.getElementById('querySearchInput');
            if (search) {
                search.focus();
                search.select();
            }
        }
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
            closeMobileMenu();
        }
    });
}
