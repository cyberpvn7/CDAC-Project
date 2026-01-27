# SecGuys Security Dashboard

A comprehensive security dashboard for visualizing and managing security scan results, vulnerabilities, and assets.

## Features

### 📊 Dashboard Overview
- **Real-time Statistics**: Critical, High, Medium, and Low severity findings at a glance
- **Severity Distribution Chart**: Doughnut chart showing vulnerability distribution
- **Source Analysis**: Bar chart showing findings by source (nuclei, exploits, nikto)
- **MITRE ATT&CK Integration**: Radar chart displaying tactics distribution
- **Top Vulnerabilities**: Bar chart highlighting the riskiest vulnerabilities by CVSS score
- **Risk Score Distribution**: Line chart showing risk progression

### 🔍 New Scan Functionality
- **Initiate Scans**: Start new security scans with custom targets
- **Real-time Output**: View scan progress in real-time terminal output
- **Scan Control**: Start and stop scans as needed
- **Status Monitoring**: Track scan completion and results

### 🎯 Findings Management
- **Comprehensive Listing**: View all identified security findings
- **Filter by Severity**: Quick filter by Critical, High, Medium, Low
- **Detailed Information**: 
  - Finding title and description
  - CVSS scores
  - MITRE techniques and tactics
  - Source (nuclei, exploits, nikto)

### 💾 Asset Management
- **Asset Inventory**: View all scanned assets/targets
- **Service Discovery**: See discovered services and versions
- **Technology Stack**: Identify technologies in use
- **Asset Details**: Deep dive into individual assets with findings

### 📋 Security Report
- **Full Assessment Report**: Complete markdown report with:
  - Executive summary
  - Critical & high-risk findings analysis
  - Vulnerability details
  - Remediation recommendations
  - Risk assessment

## Setup & Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Quick Start

1. **Make the run script executable**:
```bash
chmod +x /path/to/dashboard/run_dashboard.sh
```

2. **Run the dashboard**:
```bash
./run_dashboard.sh
```

The dashboard will:
- Create a virtual environment (if needed)
- Install dependencies
- Start the Flask server on `http://localhost:5000`

3. **Open in browser**:
```
http://localhost:5000
```

### Manual Setup (Alternative)

```bash
cd dashboard

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python3 app.py
```

## Project Structure

```
dashboard/
├── app.py                      # Flask backend application
├── requirements.txt            # Python dependencies
├── run_dashboard.sh           # Startup script
├── README.md                  # This file
├── templates/
│   └── dashboard.html         # Main HTML template
└── static/
    ├── dashboard.js           # Frontend JavaScript logic
    └── styles.css             # Dashboard styling
```

## API Endpoints

### Dashboard Statistics
- `GET /api/dashboard-stats` - Get overall security statistics

### Findings
- `GET /api/findings` - Get all findings (with optional severity filter)
- `GET /api/findings-by-severity` - Get severity distribution
- `GET /api/findings-by-source` - Get findings by source
- `GET /api/top-vulnerabilities` - Get top 10 vulnerabilities by CVSS

### Analysis
- `GET /api/mitre-tactics` - Get MITRE ATT&CK tactics distribution

### Assets
- `GET /api/assets` - Get all scanned assets
- `GET /api/asset/<asset_id>/details` - Get detailed asset information

### Reports
- `GET /api/report` - Get security assessment report

### Scans
- `POST /api/scan/start` - Start a new security scan
- `GET /api/scan/status` - Get current scan status
- `POST /api/scan/stop` - Stop running scan

## Data Sources

The dashboard reads from:
- **final.json** - Complete scan results with findings
- **semantic_analysis.json** - Analyzed findings with MITRE mappings and CVSS scores
- **db_report.md** - Detailed security assessment report

## Navigation

### Overview Tab
Main dashboard with statistics and charts

### New Scan Tab
Initiate new security scans with real-time output monitoring

### Findings Tab
Browse and filter all security findings

### Assets Tab
View scanned assets and their discovered services

### Report Tab
Read the full security assessment report

## Features Explained

### Severity Levels
- 🔴 **Critical** - Immediate action required
- 🟠 **High** - Address soon
- 🟡 **Medium** - Plan remediation
- 🔵 **Low/Info** - Monitor

### CVSS Score
- 0.0 - 3.9: Low
- 4.0 - 6.9: Medium
- 7.0 - 8.9: High
- 9.0 - 10.0: Critical

### Sources
- **nuclei** - Template-based vulnerability detection
- **exploits** - Known public exploits
- **nikto** - Web server scanning

## Customization

### Theme
Edit CSS variables in `static/styles.css`:
```css
:root {
    --primary: #2563eb;
    --critical: #dc2626;
    --high: #ea580c;
    /* ... more colors ... */
}
```

### Port
Change the port in `app.py`:
```python
app.run(host='0.0.0.0', port=5000)
```

### Timeout
Adjust scan timeout in `app.py` (currently runs main.py without timeout)

## Troubleshooting

### Port Already in Use
```bash
# Find and kill process on port 5000
lsof -i :5000
kill -9 <PID>
```

### Module Not Found Errors
```bash
# Ensure you're in the virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

### Dashboard Not Loading Data
- Check if `final.json` and `semantic_analysis.json` exist in output/scan_results directories
- Verify database file exists at `security_analysis.db`
- Check browser console for JavaScript errors

## Performance Notes

- Charts automatically load on section switch
- Scans run asynchronously without blocking UI
- Output logs limited to last 50 lines for performance
- Data is cached in browser memory

## Security Considerations

- Dashboard runs on localhost by default
- Remove `debug=True` for production
- Consider adding authentication for remote access
- Use HTTPS when accessing remotely

## Future Enhancements

- [ ] Export findings to PDF/Excel
- [ ] Scheduled automated scans
- [ ] Historical trend analysis
- [ ] Custom remediation workflows
- [ ] Multi-asset comparison
- [ ] Integration with threat intelligence feeds

## Support

For issues or questions, check:
1. Browser console (F12) for JavaScript errors
2. Terminal output for Flask errors
3. File permissions for output/scan_results directories

## License

Part of the SecGuys Security Suite
