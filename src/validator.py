#!/usr/bin/env python3
"""
Validation & Error Checking Module
Inter-phase validation to ensure data quality and prevent cascade failures
"""

import os
import json
import sqlite3
import subprocess
from pathlib import Path
from config import CONFIG


class ValidationError(Exception):
    """Custom validation exception"""
    pass


# ===========================
# FILE VALIDATION
# ===========================

def validate_final_json(filepath="final.json") -> bool:
    """Validate final.json exists and has required structure"""
    if not Path(filepath).exists():
        raise ValidationError(f"❌ {filepath} not found")
    
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
        
        # Check required fields
        if "target" not in data:
            raise ValidationError(f"❌ 'target' field missing in {filepath}")
        
        if "findings" not in data or not isinstance(data["findings"], list):
            raise ValidationError(f"❌ 'findings' field invalid in {filepath}")
        
        return True
    except json.JSONDecodeError as e:
        raise ValidationError(f"❌ Invalid JSON in {filepath}: {e}")


def validate_scan_results_exist() -> bool:
    """Validate at least one scanner output exists"""
    results_dir = Path(CONFIG["scanner"]["results_dir"])
    
    required_files = [
        "whatweb.json",
        "nikto.txt",
        "nmap.xml",
        "nuclei.json",
        "exploits_raw.json"
    ]
    
    found = 0
    for filename in required_files:
        filepath = results_dir / filename
        if filepath.exists() and filepath.stat().st_size > 0:
            found += 1
    
    if found == 0:
        raise ValidationError(f"❌ No scanner results found in {results_dir}")
    
    return True


# ===========================
# DATABASE VALIDATION
# ===========================

def validate_database_initialized() -> bool:
    """Validate database exists and has required schema"""
    db_path = CONFIG["database"]["path"]
    
    if not Path(db_path).exists():
        raise ValidationError(f"❌ Database not found: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables exist
        required_tables = ["assets", "asset_identifiers", "scans", "findings"]
        
        for table in required_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if not cursor.fetchone():
                raise ValidationError(f"❌ Table '{table}' not found in database")
        
        # Check enrichment columns exist
        cursor.execute("PRAGMA table_info(findings)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        required_enrichment_columns = {
            'semantic_classification',
            'semantic_cvss',
            'attack_capability',
            'mitre_tactic',
            'mitre_technique'
        }
        
        missing_columns = required_enrichment_columns - existing_columns
        if missing_columns:
            raise ValidationError(
                f"❌ Database schema outdated. Missing columns: {', '.join(missing_columns)}\n"
                f"   Run: python3 migrate-db.py"
            )
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        raise ValidationError(f"❌ Database error: {e}")


def validate_findings_in_db(scan_id: str) -> int:
    """Validate findings exist in database for a scan"""
    conn = sqlite3.connect(CONFIG["database"]["path"])
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM findings WHERE scan_id = ?", (scan_id,))
    count = cursor.fetchone()[0]
    
    conn.close()
    
    if count == 0:
        raise ValidationError(f"❌ No findings found in database for scan {scan_id}")
    
    return count


def validate_completed_scan_exists() -> str:
    """Validate at least one completed scan exists"""
    conn = sqlite3.connect(CONFIG["database"]["path"])
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT scan_id FROM scans
        WHERE status = 'completed'
        ORDER BY completed_at DESC
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise ValidationError(f"❌ No completed scans found in database")
    
    return result[0]


# ===========================
# TOOL VALIDATION
# ===========================

def validate_tool_available(tool: str) -> bool:
    """Check if a command-line tool is available"""
    result = subprocess.run(
        ["which", tool],
        capture_output=True
    )
    return result.returncode == 0


def validate_required_tools() -> dict:
    """Check all required security tools"""
    tools = ["nmap", "nikto", "nuclei", "whatweb", "searchsploit"]
    status = {}
    
    for tool in tools:
        status[tool] = validate_tool_available(tool)
    
    missing = [t for t, available in status.items() if not available]
    
    if missing:
        raise ValidationError(f"❌ Missing tools: {', '.join(missing)}\n   Run: bash setup.sh")
    
    return status


def validate_python_modules() -> bool:
    """Check required Python modules"""
    required_modules = [
        "google.generativeai",
        "sqlite3",
        "torch",
        "transformers"
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        raise ValidationError(f"❌ Missing Python modules: {', '.join(missing)}")
    
    return True


# ===========================
# API VALIDATION
# ===========================

def validate_gemini_api_key() -> bool:
    """Validate Gemini API key is configured"""
    api_key = CONFIG["gemini"]["api_key"]
    
    if not api_key or api_key == "":
        raise ValidationError(
            "❌ GEMINI_API_KEY not set\n"
            "   Set via environment variable or config.yaml"
        )
    
    return True


def validate_gemini_connectivity() -> bool:
    """Test basic connectivity to Gemini API"""
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=CONFIG["gemini"]["api_key"])
        model = genai.GenerativeModel(CONFIG["gemini"]["model"])
        
        # Quick test
        response = model.generate_content("test", stream=False)
        
        return True
        
    except Exception as e:
        raise ValidationError(f"❌ Gemini API connection failed: {e}")


# ===========================
# INTER-PHASE VALIDATIONS
# ===========================

def validate_setup_complete() -> bool:
    """Validate environment setup completed"""
    try:
        # Check tools
        validate_required_tools()
        
        # Check Python modules
        validate_python_modules()
        
        # Check database can be created
        if not Path(CONFIG["database"]["path"]).parent.exists():
            Path(CONFIG["database"]["path"]).parent.mkdir(parents=True, exist_ok=True)
        
        return True
    except ValidationError as e:
        raise


def validate_scan_complete() -> bool:
    """Validate scanning phase completed successfully"""
    try:
        validate_scan_results_exist()
        validate_final_json()
        return True
    except ValidationError as e:
        raise


def validate_ingest_complete() -> bool:
    """Validate ingestion phase completed"""
    try:
        validate_database_initialized()
        validate_completed_scan_exists()
        return True
    except ValidationError as e:
        raise


def validate_analyze_prerequisites() -> bool:
    """Validate prerequisites for AI analysis"""
    try:
        validate_database_initialized()
        validate_gemini_api_key()
        validate_completed_scan_exists()
        return True
    except ValidationError as e:
        raise


def validate_semantic_prerequisites() -> bool:
    """Validate prerequisites for semantic enrichment"""
    try:
        validate_database_initialized()
        validate_completed_scan_exists()
        return True
    except ValidationError as e:
        raise


# ===========================
# SUMMARY REPORTING
# ===========================

def print_validation_report(validations: dict):
    """Print validation summary"""
    print("\n" + "=" * 60)
    print("VALIDATION REPORT")
    print("=" * 60)
    
    for check_name, result in validations.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:40} {status}")
    
    all_pass = all(validations.values())
    print("=" * 60)
    
    return all_pass
