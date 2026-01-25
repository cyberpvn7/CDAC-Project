import google.generativeai as genai
import sqlite3
import json
import time
from datetime import datetime
from config import CONFIG

# =========================
# CONFIG
# =========================

DB_PATH = CONFIG["database"]["path"]
API_KEY = CONFIG["gemini"]["api_key"]
MODEL_NAME = CONFIG["gemini"]["model"]
OUTPUT_FILE = "db_report.md"

# =========================
# DB HELPERS
# =========================

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_latest_completed_scan():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT scan_id, asset_id, started_at
        FROM scans
        WHERE status = 'completed'
        ORDER BY started_at DESC
        LIMIT 1
    """)

    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def fetch_asset(asset_id):
    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM assets WHERE asset_id = ?", (asset_id,))
    asset = dict(cur.fetchone())

    cur.execute("""
        SELECT type, value
        FROM asset_identifiers
        WHERE asset_id = ?
    """, (asset_id,))
    identifiers = [dict(r) for r in cur.fetchall()]

    conn.close()
    return asset, identifiers


def fetch_findings(scan_id):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT source, severity, title, description, cve, cwe, raw
        FROM findings
        WHERE scan_id = ?
        ORDER BY severity DESC
    """, (scan_id,))

    rows = []
    for r in cur.fetchall():
        row = dict(r)
        try:
            row["raw"] = json.loads(row["raw"]) if row["raw"] else {}
        except Exception:
            row["raw"] = {}
        rows.append(row)

    conn.close()
    return rows


# =========================
# EVIDENCE PREPARATION
# =========================

def build_evidence():
    scan = fetch_latest_completed_scan()
    if not scan:
        raise RuntimeError("No completed scans found")

    asset, identifiers = fetch_asset(scan["asset_id"])
    findings = fetch_findings(scan["scan_id"])

    # Severity summary
    severity_summary = {}
    for f in findings:
        severity_summary[f["severity"]] = severity_summary.get(f["severity"], 0) + 1

    # Group findings by source
    by_source = {}
    for f in findings:
        by_source.setdefault(f["source"], []).append(f)

    # Extract service/port context
    services = {}
    for f in findings:
        raw = f.get("raw", {})
        port = raw.get("port")
        service = raw.get("service")
        if port or service:
            key = f"{service}:{port}"
            services.setdefault(key, []).append(f["title"])

    return {
        "scan": scan,
        "asset": asset,
        "identifiers": identifiers,
        "severity_summary": severity_summary,
        "findings_by_source": {
            k: v[:10]  # cap to avoid token explosion
            for k, v in by_source.items()
        },
        "service_exposure": services,
        "total_findings": len(findings)
    }


# =========================
# GEMINI PROMPT
# =========================

def build_prompt(evidence):
    return f"""
You are a senior offensive security analyst.

You are given **structured, verified vulnerability data from a security database**.
This data represents a **single completed scan snapshot**.
All findings are factual. Do NOT invent anything.

====================
TARGET
====================
{json.dumps(evidence["asset"], indent=2)}

Identifiers:
{json.dumps(evidence["identifiers"], indent=2)}

====================
SCAN SUMMARY
====================
Scan ID: {evidence["scan"]["scan_id"]}
Scan Time: {evidence["scan"]["started_at"]}

Total Findings: {evidence["total_findings"]}
Severity Breakdown:
{json.dumps(evidence["severity_summary"], indent=2)}

====================
FINDINGS BY TOOL
====================
{json.dumps(evidence["findings_by_source"], indent=2)}

====================
SERVICE EXPOSURE
====================
{json.dumps(evidence["service_exposure"], indent=2)}

====================
TASKS
====================

1. EXECUTIVE SUMMARY
   - Overall security posture
   - Key risks driving exposure

2. CRITICAL & HIGH-RISK FINDINGS
   - Focus on exploitability and impact
   - Reference services, ports, and versions

3. ATTACK CHAINS
   - 2–3 realistic attack paths
   - Initial access → escalation → impact
   - Justify each step using evidence

4. RISK ASSESSMENT
   - Overall risk level (Low / Medium / High / Critical)
   - Explain reasoning

5. REMEDIATION
   - Prioritized, actionable fixes
   - Configuration & defensive controls
   - Avoid generic advice

====================
RULES
====================
- Do NOT hallucinate
- Base everything strictly on evidence
- Be concise and professional
- Use Markdown headings
"""

# =========================
# MAIN
# =========================

def generate_report():
    print("🤖 Generating AI Security Report (NEW DB Schema)")

    evidence = build_evidence()

    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)

    prompt = build_prompt(evidence)

    print("🛰 Sending structured evidence to Gemini...")
    time.sleep(2)

    response = model.generate_content(prompt)
    report = response.text

    header = f"""# AI Security Assessment Report
Generated: {datetime.utcnow().isoformat()} UTC

---

"""

    with open(OUTPUT_FILE, "w") as f:
        f.write(header + report)

    print(f"✅ Report written to {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_report()

