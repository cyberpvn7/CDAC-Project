# SecGuys - Automated Security Scanning & AI-Driven Risk Assessment

**A unified, automated vulnerability scanning and AI-driven risk assessment framework.**

> **Status:** ✅ Complete & Production Ready | **Last Updated:** January 26, 2026

---

## 📖 Table of Contents

1. [Quick Start](#quick-start)
2. [Overview](#overview)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Configuration](#configuration)
6. [Architecture](#architecture)
7. [Database Schema](#database-schema)
8. [Commands Reference](#commands-reference)
9. [Advanced Usage](#advanced-usage)
10. [Troubleshooting](#troubleshooting)
11. [Security Considerations](#security-considerations)
12. [Development & Customization](#development--customization)

---

## Quick Start

### ⚡ Get Running in 3 Steps

```bash
# 1. Set your Gemini API key
export GEMINI_API_KEY="your-api-key-here"

# 2. Run setup (one-time)
bash setup_integration.sh

# 3. Scan a target
python3 main.py 192.168.1.100
```

That's it! The pipeline will:
- ✅ Scan with 5 security tools (Nmap, Nuclei, Nikto, WhatWeb, SearchSploit)
- ✅ Normalize findings into a unified format
- ✅ Store results in SQLite database
- ✅ Generate an AI-powered security report
- ✅ Enrich findings with CVSS scores and MITRE mappings

### 📊 View Results

```bash
# AI-generated report
cat db_report.md

# Query database
sqlite3 security_analysis.db "SELECT severity, COUNT(*) FROM findings GROUP BY severity;"

# Check logs
tail -50 logs/secguys_*.log
```

---

## Overview

### 🎯 What SecGuys Does

SecGuys (codenamed HITMAN) orchestrates a complete security assessment workflow in six phases:

```
1. Environment Setup   → Install tools & initialize database
2. Vulnerability Scan → Run Nmap, Nuclei, Nikto, WhatWeb, SearchSploit
3. Normalization      → Consolidate findings into unified schema
4. Database Ingestion → Store assets, scans, and findings in SQLite
5. AI Analysis        → Generate strategic report via Gemini API
6. Semantic Enrichment → Classify findings, calculate CVSS scores, map MITRE
```

### 🏗️ Architecture at a Glance

```
Your Target(s)
    ↓
1. Environment Setup
   └─ Validates tools, initializes database
    ↓
2. Vulnerability Scanning
   └─ Runs: Nmap, Nuclei, Nikto, WhatWeb, SearchSploit
    ↓
3. Normalization
   └─ Consolidates findings into unified format
    ↓
4. Database Ingestion
   └─ Stores in SQLite with asset tracking
    ↓
5. AI Analysis
   └─ Generates strategic report via Gemini
    ↓
6. Semantic Enrichment
   └─ Classifies attacks, calculates CVSS, maps MITRE
    ↓
Results:
├─ db_report.md (AI-generated report)
├─ security_analysis.db (queryable database)
└─ logs/ (detailed execution logs)
```

---

## Installation

### Prerequisites

- Linux (Kali Linux recommended)
- Python 3.7+
- pip package manager
- Git

### Step-by-Step Setup

#### 1. Clone the Project

```bash
git clone https://github.com/VedantKCSE/SecGuys.git
cd SecGuys
```

#### 2. Grant Execute Permissions

```bash
chmod +x setup_integration.sh
chmod +x setup.sh
chmod +x scanner.sh
```

#### 3. Get API Key

Visit: https://aistudio.google.com/app/apikey

Generate a free API key for Gemini (note: free tier may have rate limits).

#### 4. Set Environment Variable

```bash
export GEMINI_API_KEY="your-api-key-here"
```

#### 5. Run Setup

```bash
bash setup_integration.sh
```

This script will:
- Verify Python installation
- Install system dependencies
- Install Python packages
- Initialize the database
- Verify everything works

---

## Usage

### Single Target Scan

```bash
python3 main.py 192.168.1.100
```

### Multiple Targets

**Command Line:**
```bash
python3 main.py 192.168.1.1 192.168.1.2 192.168.1.3
```

**From File:**
Create `targets.txt` with one target per line, then:
```bash
python3 main.py targets.txt
```

### Phase Skipping

```bash
# Skip initial setup (already done before)
python3 main.py 192.168.1.100 --skip-setup

# Skip scanning (use existing scan results)
python3 main.py 192.168.1.100 --skip-scan --skip-setup

# Skip semantic enrichment
python3 main.py 192.168.1.100 --skip-semantic

# Skip tool availability check
python3 main.py 192.168.1.100 --no-tool-check
```

### Debug Mode

```bash
LOG_LEVEL=DEBUG python3 main.py 192.168.1.100
```

---

## Configuration

### Environment Variables

```bash
# Gemini AI Configuration (REQUIRED)
export GEMINI_API_KEY="AIzaSy..."

# Gemini AI Configuration (Optional)
export GEMINI_MODEL="gemini-2.5-flash-lite"

# Database Configuration
export SECGUYS_DB_PATH="security_analysis.db"

# Scanner Configuration
export SECGUYS_SCAN_RESULTS="scan_results"
export SECGUYS_SCAN_TIMEOUT="3600"
export SECGUYS_PARALLEL_SCANNERS="false"

# Semantic Analysis Configuration
export SEMANTIC_MODEL="jackaduma/SecBERT"
export SEMANTIC_ENABLED="true"

# Logging Configuration
export LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
export LOG_DIR="logs"
```

### Configuration File (config.yaml)

```yaml
database:
  path: security_analysis.db

scanner:
  results_dir: scan_results
  timeout: 3600
  parallel: false

gemini:
  api_key: ""              # Set via GEMINI_API_KEY environment variable
  model: gemini-2.5-flash-lite

semantic:
  model: jackaduma/SecBERT
  enabled: true

logging:
  level: INFO
  dir: logs
```

> **Priority:** Environment variables override config.yaml values.

---

## Architecture

### Data Flow Diagram

```
┌─────────────┐
│ Target(s)   │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────┐
│ 1. ENVIRONMENT SETUP             │
│ ├─ Init database schema          │
│ ├─ Validate tools (nmap, etc.)   │
│ └─ Check Python modules          │
└──────────────────┬───────────────┘
                   │
       ┌───────────┘
       │
       ▼
┌──────────────────────────────────┐
│ 2. VULNERABILITY SCANNING        │
│ ├─ WhatWeb (tech stack)          │
│ ├─ Nikto (web misconfig)         │
│ ├─ Nmap (port discovery)         │
│ ├─ Nuclei (CVE scanning)         │
│ └─ SearchSploit (exploits)       │
└──────────────────┬───────────────┘
                   │
       ┌───────────┘
       │
       ▼
┌──────────────────────────────────┐
│ 3. NORMALIZATION                 │
│ └─ Consolidate → final.json      │
└──────────────────┬───────────────┘
                   │
       ┌───────────┘
       │
       ▼
┌──────────────────────────────────┐
│ 4. DATABASE INGESTION            │
│ ├─ Create asset record           │
│ ├─ Start scan session            │
│ ├─ Ingest findings               │
│ └─ Mark scan complete            │
└──────────────────┬───────────────┘
                   │
       ┌───────────┘
       │
       ▼
┌──────────────────────────────────┐
│ 5. AI ANALYSIS (Gemini)          │
│ ├─ Query findings from DB        │
│ ├─ Send structured evidence      │
│ └─ Generate → db_report.md       │
└──────────────────┬───────────────┘
                   │
       ┌───────────┘
       │
       ▼
┌──────────────────────────────────┐
│ 6. SEMANTIC ENRICHMENT           │
│ ├─ Classify attack types         │
│ ├─ Calculate CVSS scores         │
│ ├─ Map MITRE tactics             │
│ └─ Update DB + JSON output       │
└──────────────────────────────────┘
```

### Component Architecture

```
main.py (orchestrator)
├── config.py (configuration)
├── validator.py (validation)
├── init-db.py (database)
├── normalize_scans.py (normalization)
└── Phase executors call:
    ├── scanner.sh (existing)
    ├── ingest_final.py (updated)
    ├── analyze_final.py (updated)
    └── transformer/semantic_analyzer.py (updated)
```

---

## Database Schema

### assets Table
```sql
CREATE TABLE assets (
  asset_id TEXT PRIMARY KEY,           -- UUID
  asset_type TEXT,                     -- "host"
  primary_identifier TEXT UNIQUE,      -- IP or domain
  created_at TIMESTAMP
);
```

### asset_identifiers Table
```sql
CREATE TABLE asset_identifiers (
  identifier_id TEXT PRIMARY KEY,      -- UUID
  asset_id TEXT NOT NULL,              -- FK to assets
  type TEXT,                           -- "ip", "domain", "url"
  value TEXT,                          -- IP address, domain name, etc.
  created_at TIMESTAMP,
  FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);
```

### scans Table
```sql
CREATE TABLE scans (
  scan_id TEXT PRIMARY KEY,            -- UUID
  asset_id TEXT NOT NULL,              -- FK to assets
  tool TEXT,                           -- "aggregated_scan"
  status TEXT,                         -- "running", "completed", "failed"
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);
```

### findings Table
```sql
CREATE TABLE findings (
  finding_id TEXT PRIMARY KEY,         -- UUID
  asset_id TEXT NOT NULL,              -- FK to assets
  scan_id TEXT NOT NULL,               -- FK to scans
  source TEXT,                         -- "nuclei", "nikto", "searchsploit", "whatweb"
  severity TEXT,                       -- "critical", "high", "medium", "low", "info"
  confidence REAL,                     -- 0.0-1.0
  title TEXT,
  description TEXT,
  cve TEXT,                            -- CVE ID (if applicable)
  cwe TEXT,                            -- CWE ID (if applicable)
  raw TEXT,                            -- JSON blob
  semantic_classification TEXT,        -- Attack type (enriched)
  semantic_cvss REAL,                  -- CVSS score (enriched)
  attack_capability TEXT,              -- Capability description (enriched)
  mitre_tactic TEXT,                   -- MITRE tactic (enriched)
  mitre_technique TEXT,                -- MITRE technique ID (enriched)
  created_at TIMESTAMP,
  FOREIGN KEY (asset_id) REFERENCES assets(asset_id),
  FOREIGN KEY (scan_id) REFERENCES scans(scan_id)
);
```

### Indexes for Performance

```sql
CREATE INDEX idx_scans_asset_started ON scans(asset_id, started_at DESC);
CREATE INDEX idx_findings_scan ON findings(scan_id);
CREATE INDEX idx_findings_asset ON findings(asset_id);
CREATE INDEX idx_findings_severity ON findings(severity);
```

---

## Commands Reference

### Essential Commands

| Task | Command |
|------|---------|
| Scan single target | `python3 main.py 192.168.1.100` |
| Scan multiple targets | `python3 main.py 192.168.1.1 192.168.1.2` |
| Scan from file | `python3 main.py targets.txt` |
| Setup (one-time) | `bash setup_integration.sh` |
| View AI report | `cat db_report.md \| less` |
| Debug mode | `LOG_LEVEL=DEBUG python3 main.py 192.168.1.100` |
| View logs | `tail -f logs/secguys_*.log` |
| Query database | `sqlite3 security_analysis.db "SELECT * FROM findings LIMIT 5;"` |

### Database Queries

```sql
-- Total findings count
sqlite3 security_analysis.db "SELECT COUNT(*) FROM findings;"

-- Findings by severity
sqlite3 security_analysis.db \
  "SELECT severity, COUNT(*) FROM findings GROUP BY severity;"

-- Critical findings with CVSS scores
sqlite3 security_analysis.db \
  "SELECT title, severity, semantic_cvss FROM findings WHERE semantic_cvss > 8.0;"

-- All scanned assets
sqlite3 security_analysis.db "SELECT * FROM assets;"

-- Scan history for asset
sqlite3 security_analysis.db \
  "SELECT scan_id, started_at, COUNT(finding_id) as finding_count FROM scans s LEFT JOIN findings f ON s.scan_id = f.scan_id WHERE s.asset_id = 'asset_id' GROUP BY s.scan_id ORDER BY s.started_at DESC;"

-- Export findings to CSV
sqlite3 security_analysis.db \
  ".mode csv" \
  ".output findings.csv" \
  "SELECT title, severity, source, semantic_cvss FROM findings;"
```

---

## Advanced Usage

### Batch Scanning with Results Analysis

```bash
# Scan all targets
for target in 192.168.1.{1..10}; do
  echo "Scanning $target..."
  python3 main.py $target --skip-setup
done

# Analyze all results
sqlite3 security_analysis.db \
  "SELECT asset_id, severity, COUNT(*) as count FROM findings GROUP BY asset_id, severity ORDER BY asset_id, COUNT(*) DESC;"
```

### Real-Time Monitoring

```bash
# Terminal 1: Watch logs
tail -f logs/secguys_*.log

# Terminal 2: Monitor database
watch -n 1 'sqlite3 security_analysis.db "SELECT COUNT(*) FROM findings WHERE semantic_classification IS NOT NULL;"'
```

### Compare Scans Over Time

```bash
# Get vulnerability trends
sqlite3 security_analysis.db \
  "SELECT severity, COUNT(*) as count, STRFTIME('%Y-%m-%d', started_at) as scan_date \
   FROM findings f JOIN scans s ON f.scan_id = s.scan_id \
   WHERE asset_id = 'target_id' \
   GROUP BY severity, scan_date \
   ORDER BY scan_date DESC;"
```

### Track Vulnerability Patches

```bash
# Find fixed vulnerabilities between two scans
sqlite3 security_analysis.db \
  "SELECT DISTINCT new.title FROM findings new \
   WHERE new.scan_id = 'latest_scan_id' \
   AND new.finding_id NOT IN (
     SELECT finding_id FROM findings WHERE scan_id = 'previous_scan_id'
   );"
```

---

## Troubleshooting

### Common Issues & Solutions

#### "GEMINI_API_KEY not set"

```bash
export GEMINI_API_KEY="your-actual-key"
python3 main.py 192.168.1.100
```

Get API key at: https://aistudio.google.com/app/apikey

#### "Missing tools: nmap, nuclei, etc."

```bash
bash setup.sh
```

Or install manually:
```bash
apt update && apt install nmap
```

#### "Database is locked"

```bash
# Wait for previous scan to complete
# Or use different database path:
export SECGUYS_DB_PATH="my_custom.db"
python3 main.py 192.168.1.100
```

#### "no such column: semantic_classification"

Database schema is outdated.

```bash
python3 migrate-db.py
```

#### "Failed to ingest findings"

Complete recovery:
```bash
python3 init-db.py
python3 migrate-db.py
python3 main.py 192.168.1.100
```

#### "Gemini API connection failed"

Check API key and network connectivity:

```bash
# Verify API key
echo $GEMINI_API_KEY

# Check network
curl -I https://aistudio.google.com

# Debug
LOG_LEVEL=DEBUG python3 main.py 192.168.1.100
```

#### "Out of memory"

Reduce scan scope or skip semantic enrichment:

```bash
python3 main.py 192.168.1.100 --skip-semantic
```

### Database Health Check

```bash
# Verify schema completeness
python3 -c "
import sqlite3
conn = sqlite3.connect('security_analysis.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(findings)')
cols = {row[1] for row in cursor.fetchall()}
required = {'semantic_classification', 'semantic_cvss', 'attack_capability', 'mitre_tactic', 'mitre_technique'}
if required.issubset(cols):
    print('✅ All enrichment columns present')
else:
    print('❌ Missing columns:', required - cols)
"
```

### Check Pipeline Status

```bash
# List all tables
sqlite3 security_analysis.db "SELECT name FROM sqlite_master WHERE type='table';"

# Count records
sqlite3 security_analysis.db "SELECT COUNT(*) FROM findings;"

# Check enrichment status
sqlite3 security_analysis.db "SELECT COUNT(*) FROM findings WHERE semantic_classification IS NOT NULL;"
```

---

## Security Considerations

### 🔐 API Key Protection

**✅ Recommended:**
```bash
export GEMINI_API_KEY="your-key"
python3 main.py 192.168.1.100
```

**❌ NOT Recommended:**
```python
# Don't do this!
API_KEY = "AIza..."  # Hardcoded in source
```

### 🔐 Database Security

Restrict database file permissions:
```bash
chmod 600 security_analysis.db
```

Keep database in secure location, don't commit to version control.

### 🔐 Log Security

Restrict log directory:
```bash
chmod 700 logs/
```

### 🔐 Environment Files

For CI/CD, use `.env` files:
```bash
cat > .env
GEMINI_API_KEY=AIzaSy...
SECGUYS_DB_PATH=security_analysis.db
^D
chmod 600 .env
source .env
```

### 🔐 Network Scanning

Always get permission before scanning targets:
- **Own networks:** ✅ Safe
- **Client networks:** Requires written authorization
- **Public networks:** May violate laws

---

## Development & Customization

### Adding a New Scanner

1. Update `scanner.sh` to run your tool
2. Modify `normalize_scans.py` to parse output
3. Run: `python3 main.py <target>`

### Customizing AI Prompts

Edit prompts in [analyze_final.py](analyze_final.py):

```python
def build_prompt(evidence):
    return f"""
You are a senior security analyst...
[Customize tasks, format, etc.]
"""
```

### Adding Custom Validation

Add checks to [validator.py](validator.py):

```python
def validate_custom():
    # Your validation logic
    if error:
        raise ValidationError("Custom error message")
```

Then call in [main.py](main.py) phase functions.

### Database Queries

Query findings directly:

```bash
sqlite3 security_analysis.db
SELECT severity, COUNT(*) FROM findings GROUP BY severity;
SELECT * FROM findings WHERE semantic_cvss > 8.0;
.quit
```

### Project Structure

```
SecGuys/
├── main.py                         # Master orchestrator
├── config.py                       # Configuration manager
├── config.yaml                     # Configuration file
├── validator.py                    # Validation module
├── init-db.py                      # Database initialization
├── normalize_scans.py              # Normalization module
├── setup_integration.sh            # Quick-start setup
├── scanner.sh                      # Scanner orchestrator
├── setup.sh                        # Tool installation
│
├── src/
│   ├── analyze_final.py            # Gemini analysis
│   ├── asset_resolver.py           # Asset management
│   ├── ingest_final.py             # Database ingestion
│   ├── ingest_findings.py          # Finding ingestion
│   ├── scan_manager.py             # Scan management
│   └── transformer/
│       └── semantic_analyzer.py    # Semantic enrichment
│
├── scan_results/                   # Scanner outputs
├── logs/                           # Pipeline logs
├── security_analysis.db            # SQLite database
├── db_report.md                    # AI-generated report
└── README.md                       # This file
```

---

## Output Files

| File | Purpose |
|------|---------|
| `db_report.md` | AI-generated security report (markdown) |
| `security_analysis.db` | SQLite database with all findings and metadata |
| `scan_results/final.json` | Normalized scan findings (JSON) |
| `scan_results/whatweb.json` | Web technology stack detection |
| `scan_results/nikto.txt` | Web server misconfigurations |
| `scan_results/nmap.xml` | Port and service discovery |
| `scan_results/nuclei.json` | CVE and vulnerability detections |
| `scan_results/exploits_raw.json` | Correlated public exploits |
| `transformer/semantic_analysis.json` | Enriched findings with CVSS/MITRE |
| `transformer/semantic_analysis.backup_*.json` | Timestamped backups of analyses |
| `logs/secguys_*.log` | Pipeline execution logs |

---

## Performance Tips

- **Faster scans:** Reduce timeout or skip unnecessary tools
- **Smaller database:** Remove old scans: `DELETE FROM scans WHERE completed_at < datetime("now", "-30 days");`
- **Batch targets:** Use file input instead of CLI loop
- **Skip unnecessary phases:** Use `--skip-*` flags

---

## Semantic Analysis & Enrichment

### Features

1. **Automatic Classification** - Attacks classified as RCE, SQLi, XSS, etc.
2. **CVSS Calculation** - Severity automatically scored 0.0-10.0
3. **MITRE Mapping** - Findings mapped to MITRE ATT&CK framework
4. **Database Storage** - All enrichment stored in database columns
5. **Timestamped Backups** - Previous analyses preserved for comparison

### Semantic Data Columns

```sql
semantic_classification  -- Attack category (e.g., "Remote Code Execution")
semantic_cvss           -- Computed CVSS score (0.0-10.0)
attack_capability       -- Capability description
mitre_tactic            -- MITRE tactic (e.g., "Initial Access")
mitre_technique         -- MITRE technique ID (e.g., "T1190")
```

---

## Scan Versioning

### How Multiple Scans Work

When you scan the same target multiple times:

```
192.168.100.136 (Target)
    ↓
    Asset (ID: unique per target) [Created once]
    ├── Scan 1 (started_at: 2026-01-25 19:54:44) → 126 findings
    ├── Scan 2 (started_at: 2026-01-25 19:57:48) → 133 findings  
    └── Scan 3 (started_at: 2026-01-25 20:00:53) → 140 findings
```

- **assets** table: ONE record per unique target
- **scans** table: MULTIPLE records with timestamps
- **findings** table: ALL findings linked to their scan_id

### Query Historical Data

```sql
-- All scans for asset (sorted by time)
SELECT s.scan_id, s.started_at, COUNT(f.finding_id) as finding_count
FROM scans s
LEFT JOIN findings f ON f.scan_id = s.scan_id
WHERE s.asset_id = 'target_asset_id'
GROUP BY s.scan_id
ORDER BY s.started_at DESC;
```

---

## Example Output

### Console Output

```
╔══════════════════════════════════════════════════════════╗
║          SECGUYS - Automated Scanning Pipeline           ║
║            Started: 2026-01-25 14:32:00                  ║
╚══════════════════════════════════════════════════════════╝

════════════════════════════════════════════════════════════
PHASE 1: Environment Setup
════════════════════════════════════════════════════════════
Checking required tools...
✅ All tools available
Initializing database...
✅ Database initialized: security_analysis.db
✅ Environment setup completed

════════════════════════════════════════════════════════════
PHASE 2: Vulnerability Scanning
════════════════════════════════════════════════════════════
🎯 Scanning target: 192.168.1.100
[+] WhatWeb running...
[✔] WhatWeb completed
[+] Nikto running...
[✔] Nikto completed
[+] Nmap running...
[✔] Nmap completed
[+] Nuclei running...
[✔] Nuclei completed
[+] SearchSploit running...
[✔] SearchSploit completed
✅ Scan completed for 192.168.1.100

════════════════════════════════════════════════════════════
PHASE 3: Normalization
════════════════════════════════════════════════════════════
📊 Normalizing scan results...
✅ Normalized: scan_results/final.json (47 findings)

════════════════════════════════════════════════════════════
PHASE 4: Database Ingestion
════════════════════════════════════════════════════════════
✅ 47 findings ingested into database

════════════════════════════════════════════════════════════
PHASE 5: AI Analysis (Gemini)
════════════════════════════════════════════════════════════
🤖 Generating AI Security Report...
✅ Report written to db_report.md

════════════════════════════════════════════════════════════
PHASE 6: Semantic Enrichment
════════════════════════════════════════════════════════════
📊 Enriching scan: abc-123-def
✅ Enriched 47/47 findings
✅ Semantic output exported

╔══════════════════════════════════════════════════════════╗
║                  PIPELINE SUMMARY                        ║
╠══════════════════════════════════════════════════════════╣
║ Setup         ✅ PASSED                                 ║
║ Scan          ✅ PASSED                                 ║
║ Normalize     ✅ PASSED                                 ║
║ Ingest        ✅ PASSED                                 ║
║ Analyze       ✅ PASSED                                 ║
║ Semantic      ✅ PASSED                                 ║
╚══════════════════════════════════════════════════════════╝

📊 Final Report: db_report.md
🗄️  Database: security_analysis.db
```

### Report Fragment (db_report.md)

```markdown
# AI Security Assessment Report
Generated: 2026-01-25T14:35:00 UTC

## EXECUTIVE SUMMARY
Target 192.168.1.100 presents **CRITICAL** risk due to:
- Publicly exploitable OpenSSH vulnerability
- Multiple information disclosure vectors
- Weak authentication mechanisms

## CRITICAL & HIGH-RISK FINDINGS

### OpenSSH 8.4p1 Debian 5 - Authentication Bypass (Critical)
**Source:** SearchSploit  
**Port:** 22  
**Impact:** Remote unauthenticated code execution  
**Evidence:** 20+ public exploits available

...
```

---

## Help & Support

### Get Help

```bash
# Show available options
python3 main.py --help

# Check setup status
python3 init-db.py

# Validate configuration
python3 -c "from config import CONFIG; print(CONFIG)"

# Test database
python3 -c "import sqlite3; sqlite3.connect('security_analysis.db').execute('SELECT 1').fetchone()"
```

### Debug Mode

```bash
export LOG_LEVEL=DEBUG
python3 main.py 192.168.1.100
```

Check logs:
```bash
cat logs/secguys_*.log | tail -100
```

---

## What Changed (Integration Summary)

### Before vs After

**Before:**
- 5 manual commands to run
- Hardcoded configuration scattered across files
- API key exposed in source code
- Silent failures between phases
- Manual database setup required
- File-based data exchange

**After:**
- ✅ Single command pipeline
- ✅ Centralized configuration (config.py + config.yaml + env vars)
- ✅ API key from environment (never hardcoded)
- ✅ Validation at every phase
- ✅ Automatic database initialization
- ✅ Database-integrated workflow

---

## Maintenance

### Database Cleanup

```bash
# Remove scans older than 30 days
sqlite3 security_analysis.db "DELETE FROM scans WHERE completed_at < datetime('now', '-30 days');"
```

### Migration

If you get schema errors:

```bash
python3 migrate-db.py
```

This adds any missing columns safely and is idempotent.

---

## License & Attribution

Built on Kali Linux security tools. Requires valid API key for Gemini API.

---

## 🚀 Next Steps

1. **Get API Key:** https://aistudio.google.com/app/apikey
2. **Set Environment:** `export GEMINI_API_KEY="your-key"`
3. **Run Setup:** `bash setup_integration.sh`
4. **First Scan:** `python3 main.py 192.168.1.100`
5. **Review Results:** `cat db_report.md`

---

## Questions?

- Check logs for detailed output: `tail -f logs/secguys_*.log`
- Run with debug mode: `LOG_LEVEL=DEBUG python3 main.py <target>`
- Query database: `sqlite3 security_analysis.db`

**Happy scanning! 🔒🛡️**
