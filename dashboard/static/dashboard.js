/* ========================================
   SECGUYS DASHBOARD - FRONTEND LOGIC
   ======================================== */

// API Base URL
const API_BASE = "/api";

// Global state
const state = {
    assets: [],
    currentAssetId: null,
    charts: {}
};

// ===========================
// INITIALIZATION
// ===========================

document.addEventListener("DOMContentLoaded", async () => {
    console.log("🚀 SecGuys Dashboard initialized");
    
    // Setup event listeners
    setupNavigation();
    setupFormHandlers();
    setupModalHandlers();
    
    // Load initial data
    await loadDashboard();
    await populateAssetFilters();
});

// ===========================
// NAVIGATION
// ===========================

function setupNavigation() {
    document.querySelectorAll(".nav-item").forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const section = item.getAttribute("data-section");
            switchSection(section);
        });
    });
}

function switchSection(sectionName) {
    // Hide all sections
    document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
    
    // Remove active from nav
    document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));
    
    // Show target section
    const section = document.getElementById(`${sectionName}-section`);
    if (section) {
        section.classList.add("active");
        
        // Mark nav item active
        document.querySelector(`[data-section="${sectionName}"]`).classList.add("active");
        
        // Trigger section-specific actions
        if (sectionName === "dashboard") {
            loadDashboard();
        } else if (sectionName === "assets") {
            loadAssets();
        } else if (sectionName === "analytics") {
            loadAnalytics();
        }
    }
}

// ===========================
// DASHBOARD
// ===========================

async function loadDashboard() {
    try {
        const [assetsRes, severityRes, classRes, sourceRes] = await Promise.all([
            axios.get(`${API_BASE}/assets`),
            axios.get(`${API_BASE}/analytics/severity-distribution`),
            axios.get(`${API_BASE}/analytics/classification-breakdown`),
            axios.get(`${API_BASE}/analytics/source-breakdown`)
        ]);

        const assets = assetsRes.data.assets;
        state.assets = assets;

        // Update stats
        updateStats(assets, severityRes.data.distribution);

        // Render charts
        renderSeverityChart(severityRes.data.distribution);
        renderClassificationChart(classRes.data.classifications);
        renderSourceChart(sourceRes.data.sources);

        // Render recent assets
        renderRecentAssets(assets.slice(0, 5));

    } catch (error) {
        console.error("Dashboard load error:", error);
        showNotification("Failed to load dashboard", "error");
    }
}

function updateStats(assets, severity) {
    document.getElementById("total-assets").textContent = assets.length;
    document.getElementById("critical-count").textContent = severity.critical || 0;
    document.getElementById("high-count").textContent = severity.high || 0;
    
    const total = Object.values(severity).reduce((a, b) => a + b, 0);
    document.getElementById("total-findings").textContent = total;
}

function renderRecentAssets(assets) {
    const container = document.getElementById("recent-assets-list");
    
    if (assets.length === 0) {
        container.innerHTML = '<div class="loading">No assets yet</div>';
        return;
    }

    container.innerHTML = assets.map(asset => `
        <div class="asset-item" onclick="viewAssetDetail('${asset.asset_id}')">
            <div class="asset-info">
                <div class="asset-name">${asset.primary_identifier}</div>
                <div class="asset-meta">${asset.total_findings} findings • ${asset.total_scans} scans</div>
            </div>
            <div style="color: var(--text-light);">
                ${renderSeverityBadges(asset.severity_summary)}
            </div>
        </div>
    `).join("");
}

function renderSeverityBadges(summary) {
    return Object.entries(summary || {})
        .map(([severity, count]) => `<span class="severity-badge severity-${severity}">${count}</span>`)
        .join("");
}

// ===========================
// CHARTS
// ===========================

function renderSeverityChart(distribution) {
    const ctx = document.getElementById("severity-chart").getContext("2d");
    
    destroyChart("severity");
    
    state.charts.severity = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: Object.keys(distribution),
            datasets: [{
                data: Object.values(distribution),
                backgroundColor: [
                    "rgba(220, 38, 38, 0.8)",   // critical
                    "rgba(249, 115, 22, 0.8)",  // high
                    "rgba(234, 179, 8, 0.8)",   // medium
                    "rgba(59, 130, 246, 0.8)",  // low
                    "rgba(14, 165, 233, 0.8)"   // info
                ],
                borderColor: "rgba(255, 255, 255, 0.1)",
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        color: "rgba(255, 255, 255, 0.7)",
                        font: { size: 12 }
                    }
                }
            }
        }
    });
}

function renderClassificationChart(classifications) {
    const ctx = document.getElementById("classification-chart").getContext("2d");
    
    destroyChart("classification");
    
    state.charts.classification = new Chart(ctx, {
        type: "bar",
        data: {
            labels: classifications.map(c => c.classification),
            datasets: [{
                label: "Count",
                data: classifications.map(c => c.count),
                backgroundColor: "rgba(99, 102, 241, 0.6)",
                borderColor: "rgba(99, 102, 241, 1)",
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        color: "rgba(255, 255, 255, 0.7)"
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color: "rgba(255, 255, 255, 0.5)" },
                    grid: { color: "rgba(255, 255, 255, 0.1)" }
                },
                y: {
                    ticks: { color: "rgba(255, 255, 255, 0.7)" },
                    grid: { color: "rgba(255, 255, 255, 0.1)" }
                }
            }
        }
    });
}

function renderSourceChart(sources) {
    const ctx = document.getElementById("source-chart").getContext("2d");
    
    destroyChart("source");
    
    state.charts.source = new Chart(ctx, {
        type: "radar",
        data: {
            labels: sources.map(s => s.source),
            datasets: [{
                label: "Findings",
                data: sources.map(s => s.count),
                borderColor: "rgba(99, 102, 241, 1)",
                backgroundColor: "rgba(99, 102, 241, 0.2)",
                borderWidth: 2,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        color: "rgba(255, 255, 255, 0.7)"
                    }
                }
            },
            scales: {
                r: {
                    ticks: {
                        color: "rgba(255, 255, 255, 0.5)",
                        backdropColor: "transparent"
                    },
                    grid: { color: "rgba(255, 255, 255, 0.1)" }
                }
            }
        }
    });
}

function destroyChart(key) {
    if (state.charts[key]) {
        state.charts[key].destroy();
        delete state.charts[key];
    }
}

// ===========================
// ASSETS PAGE
// ===========================

async function loadAssets() {
    try {
        const response = await axios.get(`${API_BASE}/assets`);
        const assets = response.data.assets;

        const table = document.getElementById("assets-table");
        
        if (assets.length === 0) {
            table.innerHTML = '<div class="loading">No assets found. Start a scan to add assets.</div>';
            return;
        }

        table.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Target</th>
                        <th>Type</th>
                        <th>Scans</th>
                        <th>Findings</th>
                        <th>Severity</th>
                        <th>Last Scan</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    ${assets.map(asset => `
                        <tr>
                            <td>${asset.primary_identifier}</td>
                            <td>${asset.asset_type}</td>
                            <td>${asset.total_scans}</td>
                            <td>${asset.total_findings}</td>
                            <td>${renderSeverityBadges(asset.severity_summary)}</td>
                            <td>${formatDate(asset.last_scan)}</td>
                            <td><button class="btn btn-primary" onclick="viewAssetDetail('${asset.asset_id}')">View</button></td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        `;

    } catch (error) {
        console.error("Assets load error:", error);
        document.getElementById("assets-table").innerHTML = '<div class="loading">Failed to load assets</div>';
    }
}

async function viewAssetDetail(assetId) {
    try {
        const response = await axios.get(`${API_BASE}/assets/${assetId}`);
        const asset = response.data.asset;

        const modal = document.getElementById("asset-modal");
        const body = document.getElementById("modal-body");

        body.innerHTML = `
            <div style="color: white;">
                <h2>${asset.primary_identifier}</h2>
                <p style="color: #9ca3af; margin-bottom: 1.5rem;">Type: ${asset.asset_type}</p>
                
                <h3 style="margin-top: 1.5rem; margin-bottom: 1rem;">Identifiers</h3>
                <div style="background: rgba(99, 102, 241, 0.1); padding: 1rem; border-radius: 6px;">
                    ${asset.identifiers.map(id => `
                        <div style="margin: 0.5rem 0;">
                            <strong>${id.type}</strong>: ${id.value}
                        </div>
                    `).join("")}
                </div>

                <h3 style="margin-top: 1.5rem; margin-bottom: 1rem;">Severity Summary</h3>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
                    ${Object.entries(asset.severity_summary || {}).map(([severity, count]) => `
                        <div style="background: rgba(99, 102, 241, 0.1); padding: 1rem; border-radius: 6px; text-align: center;">
                            <div style="font-size: 2rem; font-weight: 700; color: var(--primary);">${count}</div>
                            <div style="color: #9ca3af; font-size: 0.9rem;">${severity}</div>
                        </div>
                    `).join("")}
                </div>

                <h3 style="margin-top: 1.5rem; margin-bottom: 1rem;">Recent Scans</h3>
                <div style="max-height: 300px; overflow-y: auto;">
                    ${asset.scans.map(scan => `
                        <div style="background: rgba(99, 102, 241, 0.1); padding: 1rem; margin-bottom: 0.5rem; border-radius: 6px;">
                            <div><strong>${scan.tool}</strong> <span class="severity-badge" style="margin-left: 1rem;">${scan.status}</span></div>
                            <div style="color: #9ca3af; font-size: 0.9rem;">${formatDate(scan.started_at)}</div>
                        </div>
                    `).join("")}
                </div>
            </div>
        `;

        modal.classList.remove("hidden");

    } catch (error) {
        console.error("Asset detail error:", error);
    }
}

// ===========================
// ANALYTICS PAGE
// ===========================

async function loadAnalytics() {
    try {
        const assetFilter = document.getElementById("analytics-asset-filter").value;
        
        const [classRes, mitreRes] = await Promise.all([
            axios.get(`${API_BASE}/analytics/classification-breakdown`, { 
                params: { asset_id: assetFilter || undefined }
            }),
            axios.get(`${API_BASE}/analytics/mitre-mapping`, {
                params: { asset_id: assetFilter || undefined }
            })
        ]);

        renderTopClassifications(classRes.data.classifications);
        renderMitreHeatmap(mitreRes.data.mitre);
        renderCVSSChart(classRes.data.classifications);

    } catch (error) {
        console.error("Analytics load error:", error);
    }
}

function renderTopClassifications(classifications) {
    const container = document.getElementById("top-classifications");
    
    container.innerHTML = classifications.slice(0, 8).map(c => `
        <div class="stat-item">
            <div class="stat-item-name">${c.classification}</div>
            <div style="display: flex; gap: 1rem; align-items: center;">
                <div class="stat-item-count">${c.count}</div>
                <div style="color: #9ca3af;">CVSS: ${(c.avg_cvss || 0).toFixed(1)}</div>
            </div>
        </div>
    `).join("");
}

function renderMitreHeatmap(mitreData) {
    const container = document.getElementById("mitre-heatmap");
    
    if (mitreData.length === 0) {
        container.innerHTML = '<div style="grid-column: 1/-1; padding: 2rem; text-align: center; color: #9ca3af;">No MITRE data available</div>';
        return;
    }

    // Group by tactic
    const tactics = {};
    mitreData.forEach(item => {
        if (!tactics[item.tactic]) {
            tactics[item.tactic] = [];
        }
        tactics[item.tactic].push(item);
    });

    let html = "";
    Object.entries(tactics).forEach(([tactic, techniques]) => {
        techniques.forEach(technique => {
            const intensity = Math.min(technique.count / 5, 1);
            html += `
                <div class="mitre-cell" style="background: rgba(99, 102, 241, ${0.1 + intensity * 0.3});">
                    <div class="mitre-tactic">${tactic}</div>
                    <div class="mitre-technique">${technique.technique}</div>
                    <div class="mitre-count">${technique.count}</div>
                </div>
            `;
        });
    });

    container.innerHTML = html;
}

function renderCVSSChart(classifications) {
    const ctx = document.getElementById("cvss-chart");
    if (!ctx) return;

    const cvssData = classifications.filter(c => c.avg_cvss).slice(0, 10);

    destroyChart("cvss");

    state.charts.cvss = new Chart(ctx.getContext("2d"), {
        type: "bar",
        data: {
            labels: cvssData.map(c => c.classification),
            datasets: [{
                label: "Average CVSS",
                data: cvssData.map(c => c.avg_cvss),
                backgroundColor: cvssData.map(c => {
                    if (c.avg_cvss >= 9) return "rgba(220, 38, 38, 0.8)";
                    if (c.avg_cvss >= 7) return "rgba(249, 115, 22, 0.8)";
                    if (c.avg_cvss >= 4) return "rgba(234, 179, 8, 0.8)";
                    return "rgba(59, 130, 246, 0.8)";
                }),
                borderColor: "rgba(255, 255, 255, 0.1)",
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                x: {
                    min: 0,
                    max: 10,
                    ticks: { color: "rgba(255, 255, 255, 0.5)" },
                    grid: { color: "rgba(255, 255, 255, 0.1)" }
                },
                y: {
                    ticks: { color: "rgba(255, 255, 255, 0.7)" },
                    grid: { color: "rgba(255, 255, 255, 0.1)" }
                }
            },
            plugins: {
                legend: {
                    labels: { color: "rgba(255, 255, 255, 0.7)" }
                }
            }
        }
    });
}

async function populateAssetFilters() {
    try {
        const response = await axios.get(`${API_BASE}/assets`);
        const assets = response.data.assets;

        const select = document.getElementById("analytics-asset-filter");
        
        assets.forEach(asset => {
            const option = document.createElement("option");
            option.value = asset.asset_id;
            option.textContent = asset.primary_identifier;
            select.appendChild(option);
        });

        select.addEventListener("change", loadAnalytics);

    } catch (error) {
        console.error("Filter populate error:", error);
    }
}

// ===========================
// SCAN FORM
// ===========================

function setupFormHandlers() {
    const scanForm = document.getElementById("scan-form");
    
    scanForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const target = document.getElementById("target").value;
        
        if (!target) {
            showNotification("Please enter a target", "error");
            return;
        }

        try {
            // Disable form
            scanForm.style.opacity = "0.5";
            scanForm.style.pointerEvents = "none";

            // Show status
            document.getElementById("scan-status").classList.remove("hidden");

            // Start scan
            const response = await axios.post(`${API_BASE}/scans/new`, { target });
            const scanId = response.data.scan_id;

            // Poll for status
            await pollScanStatus(scanId);

            // Re-enable form
            scanForm.style.opacity = "1";
            scanForm.style.pointerEvents = "auto";

            // Clear form
            scanForm.reset();
            document.getElementById("scan-status").classList.add("hidden");

            // Reload dashboard
            showNotification("Scan completed successfully!", "success");
            switchSection("dashboard");
            loadDashboard();

        } catch (error) {
            console.error("Scan error:", error);
            showNotification("Scan failed: " + (error.response?.data?.message || error.message), "error");
            scanForm.style.opacity = "1";
            scanForm.style.pointerEvents = "auto";
        }
    });
}

async function pollScanStatus(scanId, maxAttempts = 300) {
    for (let i = 0; i < maxAttempts; i++) {
        try {
            const response = await axios.get(`${API_BASE}/scans/${scanId}/status`);
            const scan = response.data.scan;

            document.querySelector(".status-message").textContent = 
                `Status: ${scan.status} | Created: ${new Date(scan.created_at).toLocaleString()}`;

            if (scan.status === "completed") {
                return true;
            }
            if (scan.status === "failed") {
                throw new Error(scan.error || "Scan failed");
            }

            // Wait before next poll
            await new Promise(resolve => setTimeout(resolve, 2000));

        } catch (error) {
            console.error("Poll error:", error);
            throw error;
        }
    }

    throw new Error("Scan timeout");
}

// ===========================
// MODAL HANDLERS
// ===========================

function setupModalHandlers() {
    const modal = document.getElementById("asset-modal");
    const closeBtn = document.querySelector(".modal-close");

    closeBtn.addEventListener("click", () => {
        modal.classList.add("hidden");
    });

    modal.addEventListener("click", (e) => {
        if (e.target === modal) {
            modal.classList.add("hidden");
        }
    });
}

// ===========================
// UTILITIES
// ===========================

function formatDate(dateString) {
    if (!dateString) return "Never";
    const date = new Date(dateString);
    return date.toLocaleString();
}

function showNotification(message, type = "info") {
    // Create notification element
    const notification = document.createElement("div");
    notification.style.cssText = `
        position: fixed;
        top: 2rem;
        right: 2rem;
        background: ${type === "success" ? "rgba(16, 185, 129, 0.9)" : "rgba(239, 68, 68, 0.9)"};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        z-index: 10000;
        font-weight: 600;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Auto remove
    setTimeout(() => {
        notification.style.animation = "slideOut 0.3s ease-out";
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

// Add slide animations
const style = document.createElement("style");
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
