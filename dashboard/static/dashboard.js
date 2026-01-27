// SecGuys Dashboard Logic
// =========================

// Global state
let currentAsset = null;
let currentAssetId = null;
let charts = {};
let scanPollingInterval = null;

// Theme Colors (Matching CSS)
const theme = {
    critical: '#ef4444',
    high: '#f97316',
    medium: '#eab308',
    low: '#22c55e',
    info: '#06b6d4',
    text: '#f8fafc',
    textMuted: '#94a3b8',
    border: '#334155',
    grid: 'rgba(255, 255, 255, 0.05)'
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    loadAssetSelector();
    loadDashboardData();
    setupFilters();

    // Auto-refresh last updated
    updateLastUpdated();
    setInterval(updateLastUpdated, 60000); // Every minute
});

function updateLastUpdated() {
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    const el = document.getElementById('last-updated');
    if (el) el.textContent = timeString;
}

// Navigation Logic
function initNavigation() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = link.dataset.section;
            switchSection(section);

            // UI Updates
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            // Update Header Title
            const titles = {
                'overview': 'Dashboard Overview',
                'findings': 'Vulnerability Findings',
                'scan': 'Scan Operations',
                'assets': 'Asset Management',
                'reports': 'Reports Archive'
            };
            document.getElementById('page-title').textContent = titles[section] || 'Dashboard';

            // specific loaders
            if (section === 'assets') loadAssets();
            if (section === 'reports') loadReportsHistory();
            if (section === 'findings') loadFindingsTable();
        });
    });
}

function switchSection(sectionId) {
    document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
    const target = document.getElementById(sectionId);
    if (target) target.classList.add('active');
}

// Asset Context
function loadAssetSelector() {
    fetch('/api/assets')
        .then(res => res.json())
        .then(data => {
            const selectors = [document.getElementById('sidebar-asset-selector'), document.getElementById('asset-selector')];

            selectors.forEach(sel => {
                if (!sel) return;
                sel.innerHTML = '<option value="">All Assets</option>';
                data.assets.forEach(asset => {
                    const opt = document.createElement('option');
                    opt.value = asset.id;
                    opt.textContent = asset.target;
                    sel.appendChild(opt);
                });

                // Event Listener
                sel.addEventListener('change', (e) => {
                    currentAssetId = e.target.value;
                    // Sync other selectors
                    selectors.forEach(s => { if (s && s !== sel) s.value = currentAssetId; });
                    refreshAllData();
                });
            });
        });
}

function refreshAllData() {
    loadDashboardData();
    if (document.getElementById('findings').classList.contains('active')) loadFindingsTable();
}

// Dashboard Data
function loadDashboardData() {
    const params = currentAssetId ? `?asset_id=${currentAssetId}` : '';

    // Stats
    fetch(`/api/dashboard-stats${params}`)
        .then(res => res.json())
        .then(data => {
            animateValue('stat-critical', data.critical_findings);
            animateValue('stat-high', data.high_findings);
            animateValue('stat-medium', data.medium_findings);
            animateValue('stat-low', data.info_findings + data.low_findings);

            loadCharts(params);
        });
}

function animateValue(id, value) {
    const obj = document.getElementById(id);
    if (!obj) return;
    obj.textContent = value;
    // We could add a counting animation here if we wanted extra flair
}

// Charts & Visuals
function loadCharts(params) {
    // 1. Severity Distribution
    fetch(`/api/findings-by-severity${params}`)
        .then(res => res.json())
        .then(data => {
            renderChart('severityChart', 'doughnut', {
                labels: ['Critical', 'High', 'Medium', 'Low', 'Info'],
                datasets: [{
                    data: [data.data.critical, data.data.high, data.data.medium, data.data.low, data.data.info],
                    backgroundColor: [theme.critical, theme.high, theme.medium, theme.low, theme.info],
                    borderWidth: 0
                }]
            });

            renderChart('riskChart', 'line', {
                labels: ['Scan 1', 'Scan 2', 'Scan 3', 'Current'],
                datasets: [{
                    label: 'Critical/High Issues',
                    data: [12, 10, 8, data.data.critical + data.data.high],
                    borderColor: theme.primary,
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            });
        });

    // 2. Source Distribution
    fetch(`/api/findings-by-source${params}`)
        .then(res => res.json())
        .then(data => {
            renderChart('sourceChart', 'bar', {
                labels: Object.keys(data.data),
                datasets: [{
                    label: 'Findings',
                    data: Object.values(data.data),
                    backgroundColor: theme.info,
                    borderRadius: 4
                }]
            }, { indexAxis: 'y' });
        });

    // 3. MITRE TACTICS MATRIX (New Implementation)
    fetch(`/api/findings${params}`)
        .then(res => res.json())
        .then(data => {
            renderMitreMatrix(data.findings);
        });

    // 4. Top Vulns
    fetch(`/api/top-vulnerabilities${params}`)
        .then(res => res.json())
        .then(data => {
            renderChart('topVulnsChart', 'bar', {
                labels: data.vulnerabilities.map(v => v.title.substring(0, 20) + '...'),
                datasets: [{
                    label: 'CVSS Score',
                    data: data.vulnerabilities.map(v => v.cvss_score),
                    backgroundColor: data.vulnerabilities.map(v => getSeverityColor(v.severity)),
                    borderRadius: 4
                }]
            }, { indexAxis: 'y' });
        });

    // 5. Tech Stack (New)
    loadTechStack(params);
}

// Tech Stack Visualization
function loadTechStack(params) {
    // Ideally we get this from a specific endpoint, but we can reuse asset detail logic or findings sources
    const container = document.getElementById('tech-stack-container');
    if (!container) return;

    // Mocking some detection logic based on what we see in findings + assets
    // In a real app, this comes from the scanner output (e.g., Wappalyzer)

    // Let's try to fetch asset details if we have an asset selected, else guess from findings source
    let technologies = new Set(['linux', 'python', 'flask']); // Default guesses

    if (currentAssetId) {
        fetch(`/api/asset/${currentAssetId}/details`)
            .then(res => res.json())
            .then(data => {
                if (data.tech_stack) data.tech_stack.forEach(t => technologies.add(t.toLowerCase()));
                renderTechGrid(Array.from(technologies));
            });
    } else {
        // Fallback for overview
        renderTechGrid(Array.from(technologies));
    }
}

function renderTechGrid(techList) {
    const container = document.getElementById('tech-stack-container');
    container.innerHTML = '';

    // Map common names to DevIcons classes
    const iconMap = {
        'python': 'devicon-python-plain',
        'javascript': 'devicon-javascript-plain',
        'react': 'devicon-react-original',
        'nginx': 'devicon-nginx-original',
        'apache': 'devicon-apache-plain',
        'linux': 'devicon-linux-plain',
        'ubuntu': 'devicon-ubuntu-plain',
        'docker': 'devicon-docker-plain',
        'mysql': 'devicon-mysql-plain',
        'postgresql': 'devicon-postgresql-plain',
        'flask': 'devicon-flask-original',
        'php': 'devicon-php-plain',
        'wordpress': 'devicon-wordpress-plain'
    };

    techList.forEach(tech => {
        const iconClass = iconMap[tech] || 'fa-solid fa-server'; // Fallback
        const isFontAwesome = iconClass.startsWith('fa-');

        const item = document.createElement('div');
        item.className = 'tech-item';
        item.innerHTML = `
            <i class="${iconClass} tech-icon" style="${!isFontAwesome ? 'color: inherit' : 'color: var(--primary)'}"></i>
            <span class="tech-name">${tech.toUpperCase()}</span>
        `;
        container.appendChild(item);
    });

    if (techList.length === 0) container.innerHTML = '<div style="font-size:12px; color:var(--text-muted)">No specific technologies detected</div>';
}

// MITRE Matrix Rendering
function renderMitreMatrix(findings) {
    const container = document.getElementById('mitre-matrix');
    if (!container) return;
    container.innerHTML = '';

    // Define standard tactics order
    const tactics = [
        'Initial Access', 'Execution', 'Persistence',
        'Privilege Escalation', 'Defense Evasion', 'Credential Access',
        'Discovery', 'Lateral Movement', 'Collection', 'Exfiltration'
    ];

    // Group findings by Tactic -> Technique
    const coverage = {};
    findings.forEach(f => {
        const t = f.semantic.mitre_tactic;
        // Normalize tactic name if needed (simple check)
        if (t && t !== 'Unknown') {
            if (!coverage[t]) coverage[t] = new Set();
            coverage[t].add(f.semantic.mitre_technique || 'Generic');
        }
    });

    tactics.forEach(tactic => {
        const col = document.createElement('div');
        col.className = 'mitre-column';

        const header = document.createElement('div');
        header.className = 'mitre-header';
        header.textContent = tactic;
        col.appendChild(header);

        // Mock techniques for visual structure, creating a "Matrix" look
        // In reality, we'd list ALL potential techniques, but for this UI we'll list a few common ones
        // and highlight the ones we have findings for.
        const commonTechniques = [
            'Exploit Public App', 'Command Scripting', 'Account Manipulation',
            'Valid Accounts', 'OS Credential Dumping', 'Process Injection',
            'Network Sniffing', 'Remote Services', 'Data Staged', 'Encrypted Channel'
        ];

        // Add active techniques from findings first
        if (coverage[tactic]) {
            coverage[tactic].forEach(tech => {
                const cell = document.createElement('div');
                cell.className = 'mitre-cell active';
                cell.textContent = tech;
                cell.title = `Findings Detected in ${tactic}`;
                col.appendChild(cell);
            });
        }

        // Fill with some "inactive" placeholders to make the grid look consistent
        const fillCount = 5 - (coverage[tactic] ? coverage[tactic].size : 0);
        for (let i = 0; i < Math.max(0, fillCount); i++) {
            const cell = document.createElement('div');
            cell.className = 'mitre-cell';
            cell.textContent = '-';
            col.appendChild(cell);
        }

        container.appendChild(col);
    });
}

function renderChart(id, type, data, extraOptions = {}) {
    const ctx = document.getElementById(id);
    if (!ctx) return;

    if (charts[id]) charts[id].destroy();

    charts[id] = new Chart(ctx, {
        type: type,
        data: data,
        options: {
            ...extraOptions,
            responsive: true,
            maintainAspectRatio: false, // Important for CSS grid
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: theme.textMuted }
                }
            },
            scales: type !== 'doughnut' ? {
                x: {
                    grid: { color: theme.border },
                    ticks: { color: theme.textMuted }
                },
                y: {
                    grid: { color: theme.border },
                    ticks: { color: theme.textMuted }
                }
            } : {}
        }
    });
}

// Findings Table
let findingsParams = {
    sort: 'severity', // or 'cvss'
    order: 'desc'
};

function loadFindingsTable(specificAssetId = null) {
    const tbody = document.getElementById('findings-table-body');
    const filter = document.getElementById('findings-severity-filter').value;

    // Determine context (Overview vs Asset Detail)
    const assetIdObj = specificAssetId || currentAssetId;

    // Check if we have a specific scan filter selected
    let scanId = null;
    const scanFilter = document.getElementById('scan-filter-select');
    if (scanFilter && document.getElementById('asset-detail').classList.contains('active')) {
        scanId = scanFilter.value;
    }

    // Build URL
    let url = '/api/findings?';
    if (assetIdObj) url += `asset_id=${assetIdObj}&`;
    if (scanId) url += `scan_id=${scanId}&`;
    if (filter !== 'all') url += `severity=${filter}`;

    if (tbody) tbody.innerHTML = '<tr><td colspan="5" style="text-align:center">Loading...</td></tr>';

    fetch(url)
        .then(res => res.json())
        .then(data => {
            if (!tbody) return;
            tbody.innerHTML = '';

            if (data.findings.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center">No findings found</td></tr>';
                return;
            }

            // Client-side Sort
            sortFindings(data.findings);

            data.findings.forEach(f => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><span class="badge badge-${f.severity}">${f.severity}</span></td>
                    <td>
                        <div style="font-weight:600">${escapeHtml(f.title)}</div>
                        <div style="font-size:11px; color:${theme.textMuted}">${f.semantic.mitre_tactic}</div>
                    </td>
                    <td>${f.source}</td>
                    <td>
                        <div style="font-weight:700; color:${getSeverityColor(f.severity)}">${f.semantic.cvss_score}</div>
                    </td>
                    <td>
                        <button class="btn btn-secondary btn-sm" onclick="viewFinding('${f.id}')">Details</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        });
}

function sortFindings(findings) {
    findings.sort((a, b) => {
        let valA, valB;
        if (findingsParams.sort === 'severity' || findingsParams.sort === 'cvss') {
            valA = a.semantic.cvss_score || 0;
            valB = b.semantic.cvss_score || 0;
        } else {
            valA = a[findingsParams.sort];
            valB = b[findingsParams.sort];
        }

        if (findingsParams.order === 'desc') {
            return valA < valB ? 1 : -1;
        } else {
            return valA > valB ? 1 : -1;
        }
    });
}

function setupFilters() {
    const f = document.getElementById('findings-severity-filter');
    if (f) f.addEventListener('change', () => loadFindingsTable());

    // Setup Header Sorters
    document.querySelectorAll('th[data-sort]').forEach(th => {
        th.style.cursor = 'pointer';
        th.addEventListener('click', () => {
            const key = th.dataset.sort;
            if (findingsParams.sort === key) {
                findingsParams.order = findingsParams.order === 'desc' ? 'asc' : 'desc';
            } else {
                findingsParams.sort = key;
                findingsParams.order = 'desc';
            }
            // Trigger reload (efficiently would just re-render, but reload is fine for now)
            loadFindingsTable();
        });
    });
}

// Findings Detail View
window.viewFinding = function (id) {
    document.getElementById('finding-detail-modal').classList.remove('hidden');
    const content = document.getElementById('finding-detail-content');
    content.innerHTML = '<div class="loading">Loading details...</div>';

    fetch(`/api/finding/${id}`).then(res => res.json()).then(data => {
        if (data.error) {
            content.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            return;
        }

        const cveBadge = data.cve ? `<span class="badge badge-info">${data.cve}</span>` : '';
        const rawOutput = data.raw ? `<pre>${escapeHtml(data.raw)}</pre>` : 'No raw output available';

        content.innerHTML = `
            <div style="margin-bottom:20px; border-bottom:1px solid var(--border); padding-bottom:10px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h2 style="margin:0; font-size:18px;">${escapeHtml(data.title)}</h2>
                    <span class="badge badge-${data.severity}">${data.severity}</span>
                </div>
                <div style="margin-top:10px; font-size:12px; color:${theme.textMuted}">
                    Source: ${data.source} ${cveBadge}
                </div>
            </div>
            
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px; margin-bottom:20px;">
                <div>
                    <h4 style="font-size:14px; margin-bottom:5px">Description</h4>
                    <p style="font-size:13px; color:${theme.textMuted}">${escapeHtml(data.description || 'No description provided.')}</p>
                </div>
                <div>
                     <h4 style="font-size:14px; margin-bottom:5px">Metrics</h4>
                     <div class="stat-card p-0" style="padding:15px; background:var(--bg-app)">
                        <div class="stat-info">
                            <div class="stat-value" style="font-size:20px">${data.cvss}</div>
                            <div class="stat-label">CVSS Score</div>
                        </div>
                     </div>
                </div>
            </div>
            
            <div style="margin-bottom:20px;">
                <h4 style="font-size:14px; margin-bottom:5px">Remediation / Solution</h4>
                <p style="font-size:13px; color:${theme.textMuted}">${escapeHtml(data.solution || 'No specific solution available.')}</p>
            </div>
            
            <div>
                <h4 style="font-size:14px; margin-bottom:5px">Raw Output / Proof</h4>
                ${rawOutput}
            </div>
        `;
    });
};

document.getElementById('close-finding-btn').addEventListener('click', () => {
    document.getElementById('finding-detail-modal').classList.add('hidden');
});

// Scans
document.getElementById('start-scan-btn').addEventListener('click', startScan);
document.getElementById('stop-scan-btn').addEventListener('click', stopScan);

function startScan() {
    const target = document.getElementById('target-input').value;
    if (!target) return alert('Please enter a target');

    fetch('/api/scan/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target })
    }).then(res => res.json())
        .then(data => {
            if (data.error) return alert(data.error);

            document.getElementById('scan-status-card').classList.remove('hidden');
            document.getElementById('start-scan-btn').disabled = true;
            document.getElementById('stop-scan-btn').disabled = false;

            scanPollingInterval = setInterval(pollScan, 1000);
        });
}

function pollScan() {
    fetch('/api/scan/status')
        .then(res => res.json())
        .then(data => {
            const log = document.getElementById('output-log');
            if (data.output) log.textContent = data.output.map(l => l.message).join('\n');
            log.scrollTop = log.scrollHeight;

            if (data.status === 'completed' || data.status === 'failed') {
                clearInterval(scanPollingInterval);
                document.getElementById('start-scan-btn').disabled = false;
                document.getElementById('stop-scan-btn').disabled = true;
                refreshAllData();
            }
        });
}

function stopScan() {
    fetch('/api/scan/stop', { method: 'POST' });
}

// Assets (Keep generic logic)
function loadAssets() {
    const container = document.getElementById('assets-list');
    container.innerHTML = '<div class="loading">Loading...</div>';

    fetch('/api/assets').then(res => res.json()).then(data => {
        if (!data.assets.length) {
            container.innerHTML = 'No assets';
            return;
        }

        container.innerHTML = data.assets.map(a => `
            <div class="card p-0">
                <div class="card-header">
                    <h3>${escapeHtml(a.target)}</h3>
                    <span class="badge badge-info">${a.findings_count} Issues</span>
                </div>
                <div class="card-body">
                    <div style="font-size:12px; color:${theme.textMuted}; margin-bottom:10px;">
                        Last Scan: ${new Date(a.last_scan).toLocaleDateString()}
                    </div>
                    <div class="actions-cell">
                        <button class="btn btn-secondary btn-sm" onclick="viewAsset('${a.id}')">View</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteAsset('${a.id}')">Delete</button>
                    </div>
                </div>
            </div>
        `).join('');
    });
}

function deleteAsset(id) {
    if (confirm('Delete asset?')) {
        fetch(`/api/asset/${id}`, { method: 'DELETE' }).then(() => loadAssets());
    }
}

// Reports
function loadReportsHistory() {
    const list = document.getElementById('reports-list');
    list.innerHTML = '<div class="loading">Loading...</div>';

    fetch('/api/reports').then(res => res.json()).then(data => {
        if (!data.reports.length) {
            list.innerHTML = 'No reports';
            return;
        }

        let html = `<table class="data-table"><thead><tr><th>Target</th><th>Generated</th><th>Actions</th></tr></thead><tbody>`;
        data.reports.forEach(r => {
            html += `
                <tr>
                    <td>${escapeHtml(r.target_name)}</td>
                    <td>${new Date(r.generated_at).toLocaleString()}</td>
                    <td>
                        <button class="btn btn-secondary btn-sm" onclick="viewReport(${r.id})">View</button>
                        <button class="btn btn-secondary btn-sm" onclick="downloadReportRaw(${r.id})">Raw</button>
                    </td>
                </tr>
             `;
        });
        html += `</tbody></table>`;
        list.innerHTML = html;
    });
}

function viewReport(id) {
    const viewer = document.getElementById('report-viewer');
    const content = document.getElementById('report-viewer-content');
    const title = document.getElementById('report-modal-title');
    const downloadBtn = document.getElementById('download-report-btn');

    viewer.classList.remove('hidden');
    content.innerHTML = '<div class="loading">Loading report...</div>';

    fetch(`/api/reports/${id}`).then(res => res.json()).then(data => {
        if (data.error) {
            content.innerHTML = 'Error loading report';
            return;
        }

        // Set Metadata
        if (title) title.textContent = `Report: ${data.target_name}`;

        // Attach Download action
        if (downloadBtn) {
            downloadBtn.onclick = () => window.location.href = `/api/reports/${id}/download`;
        }

        const md = window.markdownit({
            html: true,
            linkify: true,
            typographer: true
        });

        // Simple render
        content.innerHTML = md.render(data.content);
    });
}

// PDF Generation removed as per user request for simplicity

document.getElementById('close-viewer-btn').addEventListener('click', () => {
    document.getElementById('report-viewer').classList.add('hidden');
});

// Utils
function getSeverityColor(sev) {
    return theme[sev.toLowerCase()] || theme.info;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Asset Details Implementation
window.viewAsset = function (id) {
    // Hide list, Show detail
    document.getElementById('assets-list').classList.add('hidden');
    document.getElementById('asset-detail').classList.remove('hidden');
    document.getElementById('asset-detail-content').innerHTML = '<div class="loading">Loading asset details...</div>';

    // Fetch Details & Scans
    Promise.all([
        fetch(`/api/asset/${id}/details`).then(r => r.json()),
        fetch(`/api/asset/${id}/scans`).then(r => r.json())
    ]).then(([details, scansData]) => {
        renderAssetDetail(details, scansData, id);
    });
}

function renderAssetDetail(details, scansData, id) {
    const container = document.getElementById('asset-detail-content');

    // Scans Dropdown Options
    let scanOptions = '<option value="">All Scan Results</option>';
    scansData.scans.forEach(s => {
        const date = new Date(s.completed_at || s.starts_at).toLocaleString();
        scanOptions += `<option value="${s.scan_id}">[${s.tool}] ${date} (${s.status})</option>`;
    });

    // Tech Stack Badges
    const techBadges = Array.from(new Set(details.tech_stack || [])).map(t =>
        `<span class="badge badge-info" style="margin-right:5px">${t}</span>`
    ).join('');

    container.innerHTML = `
        <div class="card mb-4">
            <div class="card-header">
                <div style="display:flex; justify-content:space-between; width:100%; align-items:center">
                    <div>
                        <h2 style="margin:0">${escapeHtml(details.target)}</h2>
                        <div style="color:${theme.textMuted}; font-size:12px; margin-top:5px">ID: ${id}</div>
                    </div>
                </div>
            </div>
            <div class="card-body">
                <div class="grid-2-col" style="margin-bottom:0">
                    <div>
                        <h4 style="color:${theme.textMuted}; margin-bottom:10px">Tech Stack</h4>
                        <div style="display:flex; flex-wrap:wrap; gap:5px">${techBadges || 'No tech detected'}</div>
                    </div>
                    <div class="text-right">
                        <div class="stat-value">${details.findings.length}</div>
                        <div class="stat-label">Total Findings</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-header flex-between">
                <h3>Findings Explorer</h3>
                <div style="display:flex; gap:10px; align-items:center">
                    <label style="font-size:12px; color:${theme.textMuted}">Filter Source:</label>
                    <select id="scan-filter-select" class="table-filter" style="width:250px">
                        ${scanOptions}
                    </select>
                </div>
            </div>
            <div class="card-body p-0">
                 <!-- Reusing the findings table structure -->
                 <div class="table-responsive">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Severity</th>
                                <th>Title</th>
                                <th>Source</th>
                                <th>CVSS</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody id="findings-table-body-detail">
                            <!-- Populated by JS -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;

    // Bind Event Listener for Scan Filter
    document.getElementById('scan-filter-select').addEventListener('change', (e) => {
        loadFindingsTableForDetail(id, e.target.value);
    });

    // Initial Load of Findings
    loadFindingsTableForDetail(id, null);
}

// Specialized loader for the detail view table
function loadFindingsTableForDetail(assetId, scanId) {
    const tbody = document.getElementById('findings-table-body-detail');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center">Loading...</td></tr>';

    let url = `/api/findings?asset_id=${assetId}`;
    if (scanId) url += `&scan_id=${scanId}`;

    fetch(url).then(res => res.json()).then(data => {
        tbody.innerHTML = '';
        if (data.findings.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center">No findings for this selection</td></tr>';
            return;
        }

        data.findings.forEach(f => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                    <td><span class="badge badge-${f.severity}">${f.severity}</span></td>
                    <td>
                        <div style="font-weight:600">${escapeHtml(f.title)}</div>
                    </td>
                    <td>${f.source}</td>
                    <td>
                        <div style="font-weight:700; color:${getSeverityColor(f.severity)}">${f.semantic.cvss_score}</div>
                    </td>
                    <td>
                        <button class="btn btn-secondary btn-sm">Details</button>
                    </td>
                `;
            tbody.appendChild(tr);
        });
    });
}

// Back button logic needs to reset the view
document.getElementById('back-to-assets').addEventListener('click', () => {
    document.getElementById('asset-detail').classList.add('hidden');
    document.getElementById('assets-list').classList.remove('hidden');
    loadAssets(); // Refresh list
});

window.downloadReportRaw = function (id) {
    window.location.href = `/api/reports/${id}/download`;
}
