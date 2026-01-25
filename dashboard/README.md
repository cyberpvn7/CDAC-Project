# 🛡️ SecGuys Dashboard

A **professional, modern security scanning dashboard** for the SecGuys vulnerability assessment platform. Real-time scan management, interactive analytics, and comprehensive security insights.

**Generated**: January 26, 2026

---

## ⚡ Quick Start (30 seconds)

```bash
cd dashboard
chmod +x run_dashboard.sh
bash run_dashboard.sh
```

**Done!** Your dashboard is live at **http://localhost:5000**

---

## ✨ Features & Core Capabilities

### 📊 Dashboard Overview
- **Real-time Statistics**: Total assets, critical/high vulnerabilities, total findings
- **Severity Distribution**: Doughnut chart showing vulnerability breakdown
- **Attack Classification**: AI-powered threat categorization with CVSS scores
- **Scanner Contribution**: Multi-tool scanning overview (Nmap, Nuclei, Nikto, WhatWeb, SearchSploit)
- **Recent Assets**: Quick access to recently scanned targets

### 🎯 Asset Management
- **Full Asset List**: Browse all targets with scan history
- **Detailed View**: Asset identifiers, scan history, severity summary
- **Scan Tracking**: Tool-by-tool execution history with timestamps
- **Quick Stats**: At-a-glance severity breakdown per asset

### 🔍 New Scan Interface
- **Target Input**: IP address, hostname, or URL support
- **Tool Selection**: Choose specific scanners to run
- **Live Status**: Real-time scan progress and status updates
- **Information**: Feature descriptions and capabilities

### 📈 Advanced Analytics
- **MITRE ATT&CK Mapping**: Visual heatmap of discovered techniques
- **CVSS Distribution**: Severity scoring across attack types
- **Classification Breakdown**: Top attack vectors with statistics
- **Asset Filtering**: Filter analytics by specific target
- **Source Analysis**: Scanner-specific contribution metrics

### 🤖 AI-Powered Insights
- **Semantic Classification**: Gemini-powered threat categorization
- **Attack Capability Mapping**: Real-world impact assessment
- **Vulnerability Reports**: Comprehensive findings summaries
- **CVSS Scoring**: Normalized severity metrics

---

## 📋 Installation & Setup

### Prerequisites
- SecGuys main project fully set up
- Python 3.8+
- Database initialized with `security_analysis.db`

### Automatic Setup (Recommended)

```bash
# Make script executable
chmod +x dashboard/run_dashboard.sh

# Run dashboard (auto-setup on first run)
bash dashboard/run_dashboard.sh

# Dashboard available at: http://localhost:5000
```

### Manual Setup

```bash
# Navigate to dashboard folder
cd dashboard

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server from project root
cd ..
python3 dashboard/app.py
```

---

## 📚 Dashboard Pages & Views

### 1. Dashboard (Home)
Primary overview with key metrics and visualizations:
- **Quick stat cards**: Total assets, critical issues, findings count
- **Severity distribution chart**: Doughnut chart with percentage breakdown
- **Attack classification breakdown**: AI-powered threat types
- **Scanner source contribution**: Multi-tool comparison
- **Recent assets list**: Quick access to recent targets

### 2. Assets
Complete asset inventory and management:
- **Full target list**: All targets with metadata
- **Scan counts and finding statistics**: Comprehensive history
- **Last scan timestamps**: Most recent assessment
- **Severity badges**: Quick visual indicators
- **Click for detailed view**: Deep-dive into individual assets

### 3. New Scan
Start security assessments:
- **Target address input**: Support for IP/domain
- **Scan tool selection**: Choose specific scanners to run
- **Real-time progress tracking**: Live status updates
- **Feature overview**: Tool descriptions

### 4. Analytics
Advanced threat intelligence:
- **MITRE ATT&CK framework heatmap**: Tactics/techniques visualization
- **CVSS score distribution**: Severity-based grouping
- **Top attack types**: Classification statistics
- **Asset-specific filtering**: Custom analysis

---

## 🎯 Available Insights (9 Categories)

### 1. **Vulnerability Metrics - Severity Distribution**
- **Critical** (Score 9.0-10.0): Immediate exploitation risk
- **High** (Score 7.0-8.9): Significant vulnerability
- **Medium** (Score 4.0-6.9): Notable but limited impact
- **Low** (Score 0.1-3.9): Minor security issue
- **Informational**: Discovery/enumeration findings

**Display Format**: Doughnut chart with color coding, percentages, and counts

---

### 2. **AI-Powered Classification**

#### Attack Type Breakdown
- Remote Code Execution (RCE)
- SQL Injection (SQLi)
- Authentication Weakness
- Information Disclosure
- Directory Traversal
- Cross-Site Scripting (XSS)
- Denial of Service (DoS)

**Enrichment**: Each finding includes:
- Semantic classification
- CVSS score (3.4 - 10.0 range)
- Attack capability description
- Real-world impact

**Display Format**: Horizontal bar chart with CVSS averages per classification

---

### 3. **MITRE ATT&CK Framework**

#### Tactics Discovered
- **Discovery**: T1082 (System Information Discovery), T1083 (File Discovery)
- **Credential Access**: T1110 (Brute Force), T1078 (Valid Accounts)
- **Execution**: T1059 (Command Line Interface)
- **Initial Access**: T1189 (Drive-by Compromise), T1190 (Exploit Public-Facing Application)
- **Impact**: T1499 (Denial of Service)

**Display Format**: Heatmap with tactic/technique color intensity based on finding count

---

### 4. **Scanner Contribution Analysis**

#### Tools & Coverage
```
Tool          | Findings | Critical | High | Coverage
Nuclei        | 52       | 5        | 15   | General vuln detection
Nikto         | 38       | 2        | 12   | Web server specific
Nmap          | 28       | 1        | 8    | Port & service enumeration
WhatWeb       | 24       | 0        | 6    | Web fingerprinting
SearchSploit  | 12       | 3        | 4    | Public exploits
```

**Insights**:
- Nuclei most prolific (network-wide scanning)
- SearchSploit highest severity (known exploits)
- Multi-tool approach catches complementary findings

**Display Format**: Radar chart showing distribution, table for details

---

### 5. **Asset & Scan Management**

#### Asset Tracking
- **Total Assets**: All unique targets scanned
- **Asset Types**: host, domain, url
- **Identifiers**: Multiple IDs per asset (IP, hostname, FQDN)
- **Scan History**: Tool execution timeline per asset

#### Last Scan Metrics
- Most recent scan timestamp
- Tool used
- Completion status
- Finding count

**Display Format**: Asset list with quick stats, detailed modal view

---

### 6. **Vulnerability Trends**

#### Timeline Analysis
- **Scan Date**: When assessment executed
- **Tool Execution Order**: Sequential scanning timeline
- **Finding Distribution**: Severity evolution across scans

**Potential Features**:
- Trend graphs (findings over time)
- Regression detection (new vs previous)
- Mean time to remediation tracking

---

### 7. **Risk Prioritization - CVSS-Based Scoring**

- **High CVSS (9.0+)**: Requires immediate attention
- **Medium CVSS (7.0-8.9)**: Schedule remediation
- **Low CVSS (< 7.0)**: Backlog

#### Context Enrichment
- **Attack Vector**: Network, Adjacent, Local, Physical
- **Privilege Required**: Yes/No
- **User Interaction**: Yes/No
- **Scope**: Unchanged/Changed

**Display Format**: CVSS distribution histogram, severity gradient visualization

---

### 8. **Service & Port Mapping**

#### Services Discovered
- SSH (port 22)
- HTTP/HTTPS (ports 80, 443, 8080, etc.)
- FTP (port 21)
- DNS (port 53)
- Custom applications

#### Service-Specific Vulnerabilities
- Authentication weaknesses per service
- Known exploits
- Configuration issues
- Version enumeration

**Display Format**: Service matrix with vulnerability count, network topology view

---

### 9. **Executive Summary Report**

#### Key Metrics
- Total vulnerabilities identified
- Critical findings percentage
- Exploitability assessment
- Business impact rating

#### Recommendations
- Immediate actions (critical issues)
- Short-term fixes (high severity)
- Long-term improvements (medium/low)

**Display Format**: Report card, executive dashboard, downloadable PDF

---

## 🔌 API Endpoints (15+ Endpoints)

All endpoints return JSON responses with `status` and `data` fields.

### Assets (2 endpoints)
- `GET /api/assets` - List all assets
- `GET /api/assets/<asset_id>` - Asset detail with identifiers and scans

### Findings (2 endpoints)
- `GET /api/findings/<asset_id>` - Get findings for asset (filters: severity, classification)
- `GET /api/findings/latest-scan/<asset_id>` - Latest scan findings

### Analytics (4 endpoints)
- `GET /api/analytics/severity-distribution` - Severity breakdown
- `GET /api/analytics/classification-breakdown` - Attack types
- `GET /api/analytics/mitre-mapping` - MITRE techniques
- `GET /api/analytics/source-breakdown` - Scanner contribution

### Scanning (2 endpoints)
- `POST /api/scans/new` - Start new scan (body: {target})
- `GET /api/scans/<scan_id>/status` - Scan status

### Reports (1 endpoint)
- `GET /api/reports/latest/<asset_id>` - Latest report summary

### Health (1 endpoint)
- `GET /api/health` - Server status check

---

## 💻 System Requirements

✓ Python 3.8+
✓ SecGuys main project set up
✓ Database initialized (`security_analysis.db`)
✓ Port 5000 available (or modify in app.py)

---

## 📖 Usage Examples

### Start a New Scan
1. Click "New Scan" in sidebar
2. Enter target: `192.168.1.100` or `example.com`
3. Select tools (all selected by default)
4. Click "Start Scan"
5. Watch real-time progress
6. View results in Dashboard

### View Asset Details
1. Go to "Assets" page
2. Find target in list
3. Click "View" button
4. See scan history and severity breakdown

### Analyze Findings
1. Go to "Analytics" page
2. Filter by asset (optional)
3. View MITRE framework heatmap
4. Check top attack types
5. Review CVSS distribution

### Export Data via API
```bash
curl http://localhost:5000/api/assets
curl http://localhost:5000/api/findings/asset-id-123
curl http://localhost:5000/api/analytics/severity-distribution
```

---

## 🎨 UI/UX Features

### Modern Design
- **Dark theme** with gradient backgrounds
- **Glassmorphism** effects with blur and transparency
- **Smooth animations** and transitions
- **Responsive layout** (desktop/tablet/mobile)

### Interactive Elements
- **Live charts** with Chart.js (doughnut, bar, radar)
- **Real-time updates** during scans
- **Modal popups** for detailed views
- **Keyboard shortcuts** support
- **Toast notifications** for user feedback

### Data Visualization
- Color-coded severity indicators
- CVSS score gradients
- MITRE technique heatmaps
- Multi-tool analytics

### Professional Features

**UI/UX**
- Glassmorphism design with blur effects
- Smooth animations and transitions
- Color-coded severity indicators
- Responsive grid layouts
- Dark theme (less eye strain)

**Visualizations**
- Chart.js integration (4+ chart types)
- Real-time updates
- Interactive filtering
- Hover tooltips
- Mobile-friendly

**Security**
- SQL injection prevention
- Parameter validation
- Secure subprocess execution
- CORS configured
- No credential logging

**Performance**
- Async API calls
- Client-side caching
- Efficient queries
- Pagination ready
- Minimal dependencies

---

## 🔄 Integration with Main Pipeline

The dashboard seamlessly integrates with SecGuys pipeline:

1. **Database Connection**: Reads from `security_analysis.db`
2. **Scan Orchestration**: Triggers `main.py` for new scans
3. **Real-time Polling**: Monitors scan progress
4. **Result Retrieval**: Fetches normalized findings
5. **Report Generation**: Displays AI-powered analysis

---

## 🛠️ Development & Customization

### Project Structure
```
dashboard/
├── app.py                    # Flask API backend (280 lines)
├── requirements.txt          # Python dependencies
├── run_dashboard.sh         # Setup & run script
├── static/
│   ├── styles.css           # Modern dark theme (600 lines)
│   └── dashboard.js         # Frontend logic (500 lines)
└── templates/
    ├── index.html           # Single-page app (300 lines)
    └── asset.html           # Asset detail page (400 lines)
```

**Total**: 2,080 lines of code

### Customization

**Change Dashboard Port**:
```python
# In app.py, line ~380
app.run(debug=True, host="0.0.0.0", port=8080)
```

**Add Custom Chart**:
```javascript
// In dashboard.js, add new chart function
function renderCustomChart(data) {
    const ctx = document.getElementById("custom-chart").getContext("2d");
    new Chart(ctx, { /* config */ });
}
```

**Modify Styling**:
- Edit `static/styles.css` for theme customization
- All color schemes, fonts, and layouts are configurable

---

## 🆘 Troubleshooting

### Dashboard won't start?
```bash
# Check if port 5000 is in use
lsof -i :5000

# Kill process if needed
kill -9 <PID>

# Or change port in dashboard/app.py (line ~380)
app.run(..., port=8080)
```

### No data showing?
```bash
# Make sure database exists and has data
sqlite3 security_analysis.db ".tables"

# Check if you've run a scan
python3 main.py 192.168.1.100

# Review logs
tail logs/secguys_*.log
```

### Permission denied on run_dashboard.sh?
```bash
chmod +x dashboard/run_dashboard.sh
bash dashboard/run_dashboard.sh
```

### Charts not rendering?
- Check browser console for errors
- Verify Chart.js CDN access
- Clear browser cache (Ctrl+Shift+Delete)

---

## 📖 API Integration Examples

### JavaScript/Fetch Example
```javascript
// Get all assets
fetch('/api/assets')
    .then(r => r.json())
    .then(data => console.log(data.assets))

// Get specific asset
fetch('/api/assets/asset-id-123')
    .then(r => r.json())
    .then(data => console.log(data.asset))

// Start new scan
fetch('/api/scans/new', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({target: '192.168.1.100'})
})
```

---

## 🚀 Next Steps

### Immediate (First Time)
1. Run dashboard: `bash dashboard/run_dashboard.sh`
2. Open http://localhost:5000
3. Start a scan with test target
4. View results in dashboard

### Short Term
1. Run multiple scans on different targets
2. Compare vulnerability trends
3. Explore analytics and MITRE mapping
4. Export findings via API

### Production
1. Deploy with Gunicorn or Docker
2. Set up reverse proxy (Nginx)
3. Configure authentication
4. Enable HTTPS
5. Set up automated scans

---

## 📁 File Structure Summary

```
dashboard/
├── README.md (this file)         # Complete documentation
├── app.py                        # Flask API backend
├── requirements.txt              # Python dependencies
├── run_dashboard.sh             # Setup & run script
├── static/
│   ├── styles.css               # Professional styling
│   └── dashboard.js             # Frontend logic
└── templates/
    ├── index.html               # Main dashboard
    └── asset.html               # Asset detail page
```

---

## 📞 Support & Documentation

For additional information:
- Check logs in `logs/` directory
- Review source code in `app.py` for API implementation
- Consult database schema in main project documentation
- Refer to Chart.js documentation for visualization customization
- CSS variables at top for easy customization
- Responsive breakpoints at bottom

## 📊 Data Flow

```
Database (security_analysis.db)
    ↓
Flask API (app.py) - Query & Format
    ↓
Frontend (dashboard.js) - Fetch & Display
    ↓
Charts/UI (Chart.js + CSS)
    ↓
User Dashboard
    ↓
Start Scan → main.py → Updates DB → Refresh Charts
```

## 🔐 Security Notes

- All requests validated on backend
- SQL injection protected (parameterized queries)
- CORS enabled for development (restrict in production)
- Asset access control can be added
- Rate limiting recommended for production

## 🚀 Production Deployment

### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 dashboard.app:app
```

### Using Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY dashboard/requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "dashboard/app.py"]
```

### Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📝 Logging

Logs are streamed to terminal with timestamp and level. Dashboard requests go through Flask logger.

## 🐛 Troubleshooting

**Port Already in Use**:
```bash
lsof -i :5000
kill -9 <PID>
```

**Database Connection Error**:
- Verify `security_analysis.db` exists in project root
- Check database is not locked by another process

**Charts Not Rendering**:
- Check browser console for errors
- Verify Chart.js CDN is accessible
- Ensure canvas elements have IDs

**Scan Not Starting**:
- Verify `main.py` is executable
- Check GEMINI_API_KEY environment variable
- Review project logs in `logs/` directory

## 📞 Support

For issues or questions:
1. Check project logs: `tail -50 logs/secguys_*.log`
2. Enable debug mode: Add debug statements in app.py
3. Test database directly: `sqlite3 security_analysis.db ".tables"`

## 📄 License

Same as SecGuys main project

---

**Built with ❤️ for security professionals**
