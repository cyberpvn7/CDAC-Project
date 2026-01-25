#!/usr/bin/env python3
"""
Semantic Analyzer with Database Integration
Enriches findings with semantic classification, CVSS scoring, and MITRE mapping
Integrates directly with SQLite database for seamless pipeline integration
"""

import json
import sqlite3
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from pathlib import Path
import sys
import shutil
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CONFIG

# =========================
# MODEL INITIALIZATION
# =========================
MODEL_NAME = CONFIG["semantic"]["model"]
print(f"📦 Loading {MODEL_NAME}...")

try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME)
    model.eval()
    print("✅ Model loaded")
except Exception as e:
    print(f"⚠️  Model loading failed: {e}. Falling back to rule-based classification.")
    tokenizer = None
    model = None

# =========================
# SECURITY KNOWLEDGE BASE
# =========================

SECURITY_KNOWLEDGE = {
    "Remote Code Execution": {
        "keywords": ["remote code", "command execution", "rce", "backdoor", "shell", "execute"],
        "mitre": ("Execution", "T1059")
    },
    "SQL Injection": {
        "keywords": ["sql injection", "sqli", "database", "query", "mysql", "postgresql"],
        "mitre": ("Initial Access", "T1190")
    },
    "Authentication Weakness": {
        "keywords": ["anonymous login", "default login", "password", "auth", "credential"],
        "mitre": ("Credential Access", "T1110")
    },
    "Information Disclosure": {
        "keywords": ["phpinfo", "version", "banner", "headers", "enumeration", "leak"],
        "mitre": ("Discovery", "T1082")
    },
    "Directory Traversal": {
        "keywords": ["directory indexing", "file read", "path traversal", "directory listing"],
        "mitre": ("Discovery", "T1083")
    },
    "Cross-Site Scripting": {
        "keywords": ["xss", "javascript", "script injection", "dom"],
        "mitre": ("Initial Access", "T1189")
    },
    "Denial of Service": {
        "keywords": ["dos", "ddos", "overflow", "crash", "resource"],
        "mitre": ("Impact", "T1499")
    }
}

CAPABILITY_MAP = {
    "Remote Code Execution": "Execute arbitrary commands remotely",
    "SQL Injection": "Read or modify backend database",
    "Authentication Weakness": "Bypass authentication mechanisms",
    "Information Disclosure": "Access sensitive system information",
    "Directory Traversal": "Read arbitrary files from the system",
    "Cross-Site Scripting": "Execute arbitrary JavaScript in user browser",
    "Denial of Service": "Disrupt service availability",
    "Informational": "Gather system and service information"
}

ATTACK_DEFINITIONS = {
    "Remote Code Execution": "Ability to execute arbitrary commands on a remote system",
    "SQL Injection": "Injection of malicious SQL queries to manipulate a database",
    "Authentication Weakness": "Ability to bypass or abuse authentication mechanisms",
    "Information Disclosure": "Exposure of sensitive system or application information",
    "Directory Traversal": "Reading files outside the intended directory",
    "Cross-Site Scripting": "Injection of malicious JavaScript into web pages",
    "Denial of Service": "Ability to make a system unavailable to legitimate users"
}

# =========================
# EMBEDDINGS (if model available)
# =========================

ATTACK_EMBEDDINGS = {}
if model is not None and tokenizer is not None:
    def get_embedding(text):
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=256)
        with torch.no_grad():
            outputs = model(**inputs)
        return outputs.last_hidden_state.mean(dim=1)
    
    ATTACK_EMBEDDINGS = {
        k: get_embedding(v) for k, v in ATTACK_DEFINITIONS.items()
    }

# =========================
# CVSS SCORING
# =========================

CVSS_BASE = {
    "Remote Code Execution": 9.8,
    "SQL Injection": 8.8,
    "Authentication Weakness": 7.5,
    "Directory Traversal": 6.5,
    "Information Disclosure": 5.3,
    "Cross-Site Scripting": 6.1,
    "Denial of Service": 7.5,
    "Informational": 3.1
}

def estimate_cvss(attack_type, source):
    """Estimate CVSS score based on attack type and source"""
    score = CVSS_BASE.get(attack_type, 3.1)

    # Boost for known exploits
    if source == "exploitdb":
        score += 0.5

    # Boost if no auth required
    if attack_type != "Authentication Weakness":
        score += 0.3

    score = min(round(score, 1), 10.0)

    severity = (
        "Critical" if score >= 9.0 else
        "High" if score >= 7.0 else
        "Medium" if score >= 4.0 else
        "Low"
    )

    vector = f"CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"

    return score, severity, vector


def calculate_risk_score(attack_type, source):
    """Calculate internal risk score (0-100)"""
    base = {
        "Remote Code Execution": 40,
        "SQL Injection": 30,
        "Authentication Weakness": 25,
        "Information Disclosure": 10,
        "Directory Traversal": 15,
        "Cross-Site Scripting": 20,
        "Denial of Service": 25,
        "Informational": 5
    }.get(attack_type, 5)

    source_weight = {
        "exploitdb": 30,
        "nuclei": 20,
        "nikto": 10,
        "whatweb": 5
    }.get(source, 5)

    return min(base + source_weight, 100)


def risk_level(score):
    """Convert risk score to text level"""
    if score >= 75:
        return "Critical"
    elif score >= 50:
        return "High"
    elif score >= 25:
        return "Medium"
    return "Low"

# =========================
# CLASSIFICATION LOGIC
# =========================

def rule_based(text):
    """Rule-based classification using keywords"""
    t = text.lower()
    for attack, data in SECURITY_KNOWLEDGE.items():
        if any(k in t for k in data["keywords"]):
            return {
                "attack_type": attack,
                "capability": CAPABILITY_MAP[attack],
                "mitre": data["mitre"],
                "confidence": "Very High (Rule)"
            }
    return None


def semantic_classify(text, threshold=0.65):
    """AI-based semantic classification using embeddings"""
    if model is None or tokenizer is None:
        return None
    
    try:
        emb = get_embedding(text)
        best, score = None, 0.0

        for attack, ref in ATTACK_EMBEDDINGS.items():
            s = F.cosine_similarity(emb, ref).item()
            if s > score:
                best, score = attack, s

        if score >= threshold:
            return {
                "attack_type": best,
                "capability": CAPABILITY_MAP[best],
                "mitre": SECURITY_KNOWLEDGE[best]["mitre"],
                "confidence": f"AI ({round(score, 2)})"
            }
    except Exception as e:
        print(f"⚠️  Semantic classification failed: {e}")
    
    return None


def analyze(text):
    """Classify finding text into attack type"""
    result = rule_based(text)
    
    if result is None:
        result = semantic_classify(text)
    
    if result is None:
        result = {
            "attack_type": "Informational",
            "capability": CAPABILITY_MAP["Informational"],
            "mitre": ("Discovery", "T1082"),
            "confidence": "Low"
        }
    
    return result

# =========================
# DATABASE INTEGRATION
# =========================

def fetch_latest_scan():
    """Get the most recent completed scan"""
    conn = sqlite3.connect(CONFIG["database"]["path"])
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT scan_id, asset_id
        FROM scans
        WHERE status = 'completed'
        ORDER BY completed_at DESC
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    conn.close()
    return result


def fetch_findings(scan_id):
    """Get all findings for a scan"""
    conn = sqlite3.connect(CONFIG["database"]["path"])
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT finding_id, source, severity, title, description, raw
        FROM findings
        WHERE scan_id = ?
    """, (scan_id,))
    
    rows = cursor.fetchall()
    conn.close()
    return rows


def update_finding_semantic(finding_id, classification, cvss_score, cvss_severity, mitre_tactic, mitre_technique):
    """Update finding with semantic analysis results"""
    conn = sqlite3.connect(CONFIG["database"]["path"])
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE findings
            SET semantic_classification = ?,
                semantic_cvss = ?,
                attack_capability = ?,
                mitre_tactic = ?,
                mitre_technique = ?
            WHERE finding_id = ?
        """, (
            classification,
            cvss_score,
            CAPABILITY_MAP.get(classification, ""),
            mitre_tactic,
            mitre_technique,
            finding_id
        ))
        
        conn.commit()
    except sqlite3.OperationalError as e:
        if "no such column" in str(e):
            print(f"\n⚠️  Database schema is outdated. Missing enrichment columns.")
            print(f"   Run: python3 migrate-db.py")
            conn.close()
            raise RuntimeError("Database migration required")
        else:
            raise
    finally:
        conn.close()


# =========================
# EXPORT & BACKUP FUNCTIONS
# =========================

def backup_previous_analysis():
    """Backup the current semantic_analysis.json to a timestamped version"""
    analysis_file = Path(CONFIG["scanner"]["results_dir"]) / "semantic_analysis.json"
    
    if analysis_file.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = analysis_file.parent / f"semantic_analysis.backup_{timestamp}.json"
        
        try:
            shutil.copy2(analysis_file, backup_file)
            print(f"💾 Backed up previous analysis to: {backup_file.name}")
            return backup_file
        except Exception as e:
            print(f"⚠️  Failed to backup previous analysis: {e}")
            return None
    
    return None


def export_semantic_analysis(scan_id, findings):
    """Export semantic analysis results to JSON file"""
    conn = sqlite3.connect(CONFIG["database"]["path"])
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    exported_findings = []
    
    for finding_id, source, severity, title, description, raw in findings:
        # Fetch enriched data
        cursor.execute("""
            SELECT semantic_classification, semantic_cvss, attack_capability, 
                   mitre_tactic, mitre_technique
            FROM findings
            WHERE finding_id = ?
        """, (finding_id,))
        
        enriched = cursor.fetchone()
        
        exported_findings.append({
            "finding_id": finding_id,
            "source": source,
            "severity": severity,
            "title": title,
            "description": description,
            "semantic": {
                "classification": enriched[0] if enriched else "Unknown",
                "cvss_score": enriched[1] if enriched else None,
                "attack_capability": enriched[2] if enriched else None,
                "mitre_tactic": enriched[3] if enriched else None,
                "mitre_technique": enriched[4] if enriched else None
            }
        })
    
    conn.close()
    
    # Backup previous version if exists
    backup_previous_analysis()
    
    # Export current analysis
    export_data = {
        "export_timestamp": datetime.utcnow().isoformat(),
        "scan_id": scan_id,
        "total_findings": len(exported_findings),
        "findings": exported_findings
    }
    
    analysis_file = Path(CONFIG["scanner"]["results_dir"]) / "semantic_analysis.json"
    analysis_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(analysis_file, "w") as f:
            json.dump(export_data, f, indent=2)
        
        print(f"📄 Semantic analysis exported to: {analysis_file}")
        return True
    except Exception as e:
        print(f"⚠️  Failed to export semantic analysis: {e}")
        return False


# =========================
# MAIN PIPELINE
# =========================

def run_semantic_enrichment():
    """Main semantic enrichment pipeline"""
    print("=" * 60)
    print("SEMANTIC ENRICHMENT & CVSS SCORING")
    print("=" * 60)
    
    # Fetch latest scan
    try:
        result = fetch_latest_scan()
    except RuntimeError as e:
        if "migration" in str(e).lower():
            print(f"❌ {e}")
            return False
        raise
    
    if not result:
        print("❌ No completed scans found in database")
        return False
    
    scan_id, asset_id = result
    print(f"📊 Enriching scan: {scan_id}")
    
    # Fetch findings
    findings = fetch_findings(scan_id)
    if not findings:
        print("⚠️  No findings to enrich")
        return True
    
    enriched_count = 0
    failed_count = 0
    
    # Process each finding
    for finding_id, source, severity, title, description, raw in findings:
        try:
            # Classify
            classification = analyze(title or description or "")
            
            # CVSS
            cvss_score, cvss_severity, cvss_vector = estimate_cvss(
                classification["attack_type"],
                source
            )
            
            mitre_tactic, mitre_technique = classification["mitre"]
            
            # Update DB
            update_finding_semantic(
                finding_id,
                classification["attack_type"],
                cvss_score,
                cvss_severity,
                mitre_tactic,
                mitre_technique
            )
            
            enriched_count += 1
            
        except RuntimeError as e:
            if "migration" in str(e).lower():
                print(f"\n❌ {e}")
                return False
            failed_count += 1
        except Exception as e:
            failed_count += 1
    
    if enriched_count > 0:
        print(f"✅ Enriched {enriched_count}/{len(findings)} findings")
        print(f"📊 All semantic analysis stored in database (scan_id: {scan_id})")
        
        # Export to JSON with backup
        export_semantic_analysis(scan_id, findings)
    
    if failed_count > 0:
        print(f"⚠️  Failed to enrich {failed_count} findings")
    
    return enriched_count > 0 or len(findings) == 0  # Success if we enriched something or no findings


if __name__ == "__main__":
    success = run_semantic_enrichment()
    sys.exit(0 if success else 1)
