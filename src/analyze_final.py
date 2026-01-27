import google.generativeai as genai
import sqlite3
import json
import time
from datetime import datetime, timezone
from config import CONFIG
import random
from pathlib import Path

# =========================
# CONFIG
# =========================

DB_PATH = CONFIG["database"]["path"]
API_KEY = CONFIG["gemini"]["api_key"]
MODEL_NAME = CONFIG["gemini"]["model"]
OUTPUT_FILE = "db_report.md"
REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# =========================
# RATE LIMIT HANDLER
# =========================

def call_gemini_with_retry(model, prompt, max_retries=5):
    """Call Gemini API with exponential backoff for rate limits"""
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_msg = str(e)
            # Check for rate limit error
            if "429" in error_msg or "quota" in error_msg.lower():
                if attempt < max_retries - 1:
                    # Exponential backoff: 35s, 70s, 140s, 280s, etc.
                    wait_time = 35 * (2 ** attempt) + random.uniform(0, 5)
                    print(f"     ⏳ Rate limit hit. Waiting {wait_time:.0f}s before retry {attempt+1}/{max_retries-1}...")
                    time.sleep(wait_time)
                else:
                    print(f"     ⚠️  Could not generate this section after {max_retries} attempts")
                    return f"*Note: This section could not be generated due to API rate limiting. Please try again later.*"
            else:
                raise Exception(f"API Error: {error_msg}")

# =========================
# DB HELPERS
# =========================

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def save_report_metadata(asset_id, scan_id, target_name, report_path):
    """Save report metadata to database"""
    try:
        conn = db()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO reports (asset_id, scan_id, target_name, report_path, generated_at, report_type, status)
            VALUES (?, ?, ?, ?, datetime('now'), 'security_assessment', 'completed')
        """, (asset_id, scan_id, target_name, str(report_path)))
        
        conn.commit()
        report_id = cur.lastrowid
        conn.close()
        
        print(f"✅ Report metadata saved (ID: {report_id})")
        return report_id
    except Exception as e:
        print(f"⚠️  Error saving report metadata: {e}")
        return None


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


def fetch_semantic_analysis():
    """Fetch semantic analysis data from JSON file"""
    try:
        with open("scan_results/semantic_analysis.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Warning: Could not load semantic analysis: {str(e)}")
        return {"findings": [], "total_findings": 0}


# =========================
# EVIDENCE PREPARATION
# =========================

def build_evidence():
    scan = fetch_latest_completed_scan()
    if not scan:
        raise RuntimeError("No completed scans found")

    asset, identifiers = fetch_asset(scan["asset_id"])
    findings = fetch_findings(scan["scan_id"])
    semantic_analysis = fetch_semantic_analysis()

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
        "findings": findings,
        "severity_summary": severity_summary,
        "findings_by_source": {
            k: v[:10]  # cap to avoid token explosion
            for k, v in by_source.items()
        },
        "service_exposure": services,
        "total_findings": len(findings),
        "semantic_analysis": semantic_analysis
    }


# =========================
# GEMINI PROMPTS (MULTI-SECTION)
# =========================

def build_evidence_context(evidence):
    """Build the common evidence context for all prompts"""
    return f"""
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
"""


def build_prompt_executive_summary(evidence):
    """Section 1: Executive Summary"""
    return f"""
You are a senior offensive security analyst.

You are given **structured, verified vulnerability data from a security database**.
All findings are factual. Do NOT invent anything.

{build_evidence_context(evidence)}

====================
TASK: EXECUTIVE SUMMARY
====================

Provide a concise executive summary covering:
1. Overall security posture of the target
2. Key risks and exposure drivers
3. Severity distribution impact
4. Initial assessment of threat level

**IMPORTANT FORMATTING RULES:**
- DO NOT include a section title/heading in your response
- Start directly with the content (e.g., "This report details...")
- Use bold text for key findings
- Use bullet points for lists
- Be professional and concise
- Do NOT hallucinate. Base everything strictly on the evidence provided.
"""


def build_prompt_critical_findings(evidence):
    """Section 2: Critical & High-Risk Findings"""
    return f"""
You are a senior offensive security analyst.

You are given **structured, verified vulnerability data from a security database**.
All findings are factual. Do NOT invent anything.

{build_evidence_context(evidence)}

====================
TASK: CRITICAL & HIGH-RISK FINDINGS
====================

Analyze and prioritize the most critical vulnerabilities:
1. List critical and high-severity findings with context
2. Focus on exploitability and real-world impact
3. Reference specific services, ports, and versions
4. Explain why each finding is a security concern
5. Highlight any zero-days or known active exploits

**IMPORTANT FORMATTING RULES:**
- DO NOT include a section title/heading in your response
- Start directly with the analysis
- Use ### for subsections (e.g., ### High-Severity Findings)
- Use bullet points for vulnerability lists
- Use bold for service names and severity levels
- Be professional and detailed
- Do NOT hallucinate. Base everything strictly on evidence.
"""


def build_prompt_attack_chains(evidence):
    """Section 3: Attack Chains"""
    return f"""
You are a senior offensive security analyst.

You are given **structured, verified vulnerability data from a security database**.
All findings are factual. Do NOT invent anything.

{build_evidence_context(evidence)}

====================
TASK: ATTACK CHAINS
====================

Construct 2-3 realistic attack paths an adversary could take:
1. For each chain, describe:
   - Initial access vector (how to get in)
   - Escalation path (lateral movement, privilege escalation)
   - Final impact (what can be achieved)
2. Justify each step using evidence from the findings
3. Explain the likelihood and severity of each chain

**IMPORTANT FORMATTING RULES:**
- DO NOT include a section title/heading in your response
- Start directly with the attack chains
- Use ### for each attack chain (e.g., ### Attack Chain 1: SSH Exploitation)
- Use bold for impact levels (High, Critical, etc.)
- Be professional and detailed
- Do NOT hallucinate. Base everything strictly on evidence.
"""


def build_prompt_risk_assessment(evidence):
    """Section 4: Risk Assessment"""
    return f"""
You are a senior offensive security analyst.

You are given **structured, verified vulnerability data from a security database**.
All findings are factual. Do NOT invent anything.

{build_evidence_context(evidence)}

====================
TASK: RISK ASSESSMENT
====================

Provide an overall risk assessment:
1. Rate the overall risk level: Low / Medium / High / Critical
2. Explain the reasoning behind this rating
3. Identify the primary risk vectors
4. Assess exploitability and business impact
5. Comment on urgency of remediation

**IMPORTANT FORMATTING RULES:**
- DO NOT include a section title/heading in your response
- Start directly with the assessment
- Use bold for the overall risk level (e.g., **Overall Risk Level: Critical**)
- Use numbered sections for structure (1., 2., 3., etc.)
- Use bullet points for risk vectors
- Be professional and justified
- Do NOT hallucinate. Base everything strictly on evidence.
"""


def build_prompt_remediation(evidence):
    """Section 5: Remediation Strategy"""
    return f"""
You are a senior offensive security analyst.

You are given **structured, verified vulnerability data from a security database**.
All findings are factual. Do NOT invent anything.

{build_evidence_context(evidence)}

====================
TASK: REMEDIATION & DEFENSIVE CONTROLS
====================

Provide prioritized remediation recommendations:
1. List fixes in order of criticality and impact
2. For each major issue:
   - Describe the specific fix (configuration, patch, deployment)
   - Estimate effort (low/medium/high)
   - Expected risk reduction
3. Include defensive controls and hardening measures
4. Suggest monitoring and detection strategies

**IMPORTANT FORMATTING RULES:**
- DO NOT include a section title/heading in your response
- Start directly with the recommendations
- Use ### for each remediation priority (e.g., ### 1. Address SSH Vulnerabilities)
- Use bold for effort levels and risk reduction
- Use bullet points for defensive controls and monitoring
- Be professional and actionable
- Avoid generic advice. Focus on practical, implementable solutions.
- Do NOT hallucinate. Base everything strictly on evidence.
"""


def build_prompt_mitre_framework(evidence):
    """Section 6: MITRE Attack Framework Analysis"""
    semantic_data = evidence.get("semantic_analysis", {})
    findings = semantic_data.get("findings", [])
    
    # Aggregate MITRE tactics and techniques
    mitre_tactics = {}
    mitre_techniques = {}
    attack_capabilities = {}
    classifications = {}
    
    for finding in findings:
        semantic = finding.get("semantic", {})
        
        tactic = semantic.get("mitre_tactic")
        technique = semantic.get("mitre_technique")
        capability = semantic.get("attack_capability")
        classification = semantic.get("classification")
        
        if tactic:
            mitre_tactics[tactic] = mitre_tactics.get(tactic, 0) + 1
        if technique:
            mitre_techniques[technique] = mitre_techniques.get(technique, 0) + 1
        if capability:
            attack_capabilities[capability] = attack_capabilities.get(capability, 0) + 1
        if classification:
            classifications[classification] = classifications.get(classification, 0) + 1
    
    # Create sample findings with safe serialization
    sample_findings = []
    for f in findings[:15]:
        sample_findings.append({
            "title": f.get("title"),
            "mitre_tactic": f.get("semantic", {}).get("mitre_tactic"),
            "mitre_technique": f.get("semantic", {}).get("mitre_technique"),
            "severity": f.get("severity")
        })
    
    mitre_context = f"""
====================
SEMANTIC ANALYSIS DATA
====================

MITRE Tactics Distribution:
{json.dumps(mitre_tactics, indent=2)}

MITRE Techniques Distribution:
{json.dumps(mitre_techniques, indent=2)}

Attack Capabilities:
{json.dumps(attack_capabilities, indent=2)}

Finding Classifications:
{json.dumps(classifications, indent=2)}

Sample Semantic Findings (First 15):
{json.dumps(sample_findings, indent=2)}

====================
EVIDENCE CONTEXT
====================
{build_evidence_context(evidence)}
"""
    
    return f"""
You are a senior offensive security analyst with MITRE ATT&CK framework expertise.

You are given **structured, verified vulnerability data with semantic analysis** including MITRE tactics and techniques mapped to each finding.
All findings are factual. Do NOT invent anything.

{mitre_context}

====================
TASK: MITRE ATTACK FRAMEWORK & ATTACK TECHNIQUE ANALYSIS
====================

Provide a comprehensive analysis covering:

1. **MITRE Tactics Summary**
   - List the primary attack tactics identified (Discovery, Credential Access, Execution, Impact, etc.)
   - For each tactic, explain how it manifests in the target's vulnerabilities
   - Provide count of findings per tactic

2. **MITRE Techniques Breakdown**
   - Map specific MITRE techniques (T1082, T1110, T1059, etc.) to findings
   - Explain the real-world attack impact for each technique
   - Highlight techniques most relevant to the target

3. **Attack Capability Assessment**
   - Summarize the attack capabilities enabled by these vulnerabilities
   - Group capabilities by attacker objectives (reconnaissance, access, persistence, etc.)
   - Assess the progression of attack capabilities

4. **Threat Actor Perspective**
   - Describe attack chains from a threat actor's viewpoint
   - What techniques would be chained together?
   - What prerequisites exist for each stage?

5. **Defensive Gaps and Detection Opportunities**
   - Identify which MITRE techniques are most likely to succeed due to defensive gaps
   - Suggest detection strategies aligned with MITRE ATT&CK mitigations

**IMPORTANT FORMATTING RULES:**
- DO NOT include a section title/heading in your response
- Start directly with section 1 (MITRE Tactics Summary)
- Use ### for main sections (e.g., ### MITRE Tactics Summary)
- Use #### for subsections
- Use bold for tactic and technique names (e.g., **T1082: System Information Discovery**)
- Use bullet points for details
- Be professional and detailed
- Ground everything in the semantic analysis provided
- Do NOT hallucinate or invent MITRE mappings.
"""

# =========================
# REPORT GENERATION (MULTI-SECTION)
# =========================

def generate_section(model, section_name, prompt_builder, evidence):
    """Generate a single report section with retry logic"""
    print(f"  📝 Generating {section_name}...")
    prompt = prompt_builder(evidence)
    try:
        content = call_gemini_with_retry(model, prompt, max_retries=5)
        return content
    except Exception as e:
        return f"*Error generating this section: {str(e)}*"


def generate_report():
    print("🤖 Generating AI Security Report (Multi-Section with Rate Limit Handling)")

    evidence = build_evidence()
    print(f"✅ Evidence prepared for asset {evidence['asset']['asset_id']}")

    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)

    # Define sections in order
    sections = [
        ("Executive Summary", build_prompt_executive_summary),
        ("Critical & High-Risk Findings", build_prompt_critical_findings),
        ("Attack Chains", build_prompt_attack_chains),
        ("Risk Assessment", build_prompt_risk_assessment),
        ("Remediation & Defensive Controls", build_prompt_remediation),
        ("MITRE Attack Framework Analysis", build_prompt_mitre_framework),
    ]

    print("🛰 Sending multi-section requests to Gemini...\n")

    # Generate each section with spacing to avoid rate limits
    report_sections = {}
    for idx, (section_name, prompt_builder) in enumerate(sections):
        try:
            section_content = generate_section(model, section_name, prompt_builder, evidence)
            report_sections[section_name] = section_content
            print(f"     ✅ {section_name} completed\n")
            
            # Add delay between requests (except after last request)
            if idx < len(sections) - 1:
                delay = 8 + random.uniform(0, 3)  # 8-11 seconds between requests
                print(f"  ⏸️  Spacing requests ({delay:.0f}s)...\n")
                time.sleep(delay)
                
        except Exception as e:
            print(f"     ❌ Error generating {section_name}: {str(e)}\n")
            report_sections[section_name] = f"*Could not generate this section: {str(e)}*"

    # Build final report with improved formatting
    header = f"""# AI Security Assessment Report

**Generated:** {datetime.now(timezone.utc).isoformat()} UTC  
**Target Asset:** {evidence["asset"]["asset_id"]}  
**Scan ID:** {evidence["scan"]["scan_id"]}  
**Scan Time:** {evidence["scan"]["started_at"]}

---

"""

    report = header
    for idx, (section_name, content) in enumerate(report_sections.items(), 1):
        report += f"## {idx}. {section_name}\n\n{content}\n\n"
        if idx < len(report_sections):
            report += "---\n\n"
    
    report += "\n---\n*End of Report*"

    # Generate timestamped filename
    target_name = evidence["asset"]["primary_identifier"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"{target_name}_{timestamp}.md"
    report_path = REPORTS_DIR / report_filename
    
    # Write to timestamped file
    with open(report_path, "w") as f:
        f.write(report)

    print(f"✅ Report written to {report_path}")
    
    # Also write to legacy location for backward compatibility
    with open(OUTPUT_FILE, "w") as f:
        f.write(report)
    print(f"✅ Legacy report also written to {OUTPUT_FILE}")
    
    # Save metadata to database
    asset_id = evidence["asset"]["asset_id"]
    scan_id = evidence["scan"]["scan_id"]
    save_report_metadata(asset_id, scan_id, target_name, report_path)


if __name__ == "__main__":
    generate_report()

