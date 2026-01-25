#!/usr/bin/env python3
"""
SecGuys Dashboard Server
Flask API for frontend dashboard with real-time scan management and reporting
"""

import sqlite3
import json
import os
import subprocess
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import sys

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "setup"))

from config import CONFIG

# ===========================
# FLASK APP SETUP
# ===========================

app = Flask(__name__, 
    template_folder=str(Path(__file__).parent / "templates"),
    static_folder=str(Path(__file__).parent / "static"))
CORS(app)

DB_PATH = CONFIG["database"]["path"]
PROJECT_ROOT = Path(__file__).parent.parent
SCAN_QUEUE = {}  # Track active scans

# ===========================
# DATABASE HELPERS
# ===========================

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def dict_from_row(row):
    """Convert sqlite3.Row to dict"""
    return dict(row) if row else None

# ===========================
# ASSET ENDPOINTS
# ===========================

@app.route("/api/assets", methods=["GET"])
def get_assets():
    """Fetch all assets with summary statistics"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Get all assets with latest scan info
        cur.execute("""
            SELECT DISTINCT a.asset_id, a.primary_identifier, a.asset_type, a.created_at,
                   (SELECT COUNT(*) FROM scans WHERE asset_id = a.asset_id) as total_scans,
                   (SELECT COUNT(*) FROM findings WHERE asset_id = a.asset_id) as total_findings,
                   (SELECT started_at FROM scans WHERE asset_id = a.asset_id ORDER BY started_at DESC LIMIT 1) as last_scan,
                   (SELECT GROUP_CONCAT(DISTINCT type || ':' || value) FROM asset_identifiers WHERE asset_id = a.asset_id) as identifiers
            FROM assets a
            ORDER BY a.created_at DESC
        """)
        
        assets = []
        for row in cur.fetchall():
            asset = dict(row)
            
            # Parse identifiers
            if asset['identifiers']:
                ident_list = asset['identifiers'].split(',')
                asset['identifiers'] = [{'type': x.split(':')[0], 'value': x.split(':')[1]} 
                                       for x in ident_list]
            else:
                asset['identifiers'] = []
            
            # Get severity summary
            cur.execute("""
                SELECT severity, COUNT(*) as count
                FROM findings
                WHERE asset_id = ?
                GROUP BY severity
            """, (asset['asset_id'],))
            
            severity_summary = {}
            for row2 in cur.fetchall():
                severity_summary[row2['severity']] = row2['count']
            
            asset['severity_summary'] = severity_summary
            assets.append(asset)
        
        conn.close()
        return jsonify({"status": "success", "assets": assets})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/assets/<asset_id>", methods=["GET"])
def get_asset_detail(asset_id):
    """Fetch detailed asset information"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Get asset info
        cur.execute("SELECT * FROM assets WHERE asset_id = ?", (asset_id,))
        asset = dict_from_row(cur.fetchone())
        
        if not asset:
            return jsonify({"status": "error", "message": "Asset not found"}), 404
        
        # Get identifiers
        cur.execute("""
            SELECT type, value FROM asset_identifiers WHERE asset_id = ?
        """, (asset_id,))
        asset['identifiers'] = [dict(row) for row in cur.fetchall()]
        
        # Get scan history
        cur.execute("""
            SELECT scan_id, tool, status, started_at, completed_at
            FROM scans
            WHERE asset_id = ?
            ORDER BY started_at DESC
        """, (asset_id,))
        asset['scans'] = [dict(row) for row in cur.fetchall()]
        
        # Get findings summary
        cur.execute("""
            SELECT severity, COUNT(*) as count
            FROM findings
            WHERE asset_id = ?
            GROUP BY severity
        """, (asset_id,))
        severity_summary = {}
        for row in cur.fetchall():
            severity_summary[row['severity']] = row['count']
        asset['severity_summary'] = severity_summary
        
        conn.close()
        return jsonify({"status": "success", "asset": asset})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ===========================
# FINDINGS ENDPOINTS
# ===========================

@app.route("/api/findings/<asset_id>", methods=["GET"])
def get_findings(asset_id):
    """Get findings for an asset with filters"""
    try:
        severity = request.args.get("severity", "").split(",") if request.args.get("severity") else []
        classification = request.args.get("classification")
        
        conn = get_db()
        cur = conn.cursor()
        
        query = """
            SELECT finding_id, source, severity, title, description, cve, cwe,
                   semantic_classification, semantic_cvss, attack_capability,
                   mitre_tactic, mitre_technique, created_at
            FROM findings
            WHERE asset_id = ?
        """
        params = [asset_id]
        
        if severity:
            placeholders = ",".join("?" * len(severity))
            query += f" AND severity IN ({placeholders})"
            params.extend(severity)
        
        if classification:
            query += " AND semantic_classification = ?"
            params.append(classification)
        
        query += " ORDER BY semantic_cvss DESC"
        
        cur.execute(query, params)
        findings = [dict(row) for row in cur.fetchall()]
        
        conn.close()
        return jsonify({"status": "success", "findings": findings})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/findings/latest-scan/<asset_id>", methods=["GET"])
def get_latest_findings(asset_id):
    """Get findings from latest scan for an asset"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Get latest scan
        cur.execute("""
            SELECT scan_id FROM scans
            WHERE asset_id = ? AND status = 'completed'
            ORDER BY started_at DESC
            LIMIT 1
        """, (asset_id,))
        
        scan = cur.fetchone()
        if not scan:
            return jsonify({"status": "success", "findings": []})
        
        scan_id = scan[0]
        
        # Get findings from this scan
        cur.execute("""
            SELECT finding_id, source, severity, title, description, cve, cwe,
                   semantic_classification, semantic_cvss, attack_capability,
                   mitre_tactic, mitre_technique
            FROM findings
            WHERE scan_id = ?
            ORDER BY semantic_cvss DESC
        """, (scan_id,))
        
        findings = [dict(row) for row in cur.fetchall()]
        
        conn.close()
        return jsonify({"status": "success", "findings": findings})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ===========================
# ANALYTICS ENDPOINTS
# ===========================

@app.route("/api/analytics/severity-distribution", methods=["GET"])
def get_severity_distribution():
    """Get vulnerability severity distribution"""
    try:
        asset_id = request.args.get("asset_id")
        
        conn = get_db()
        cur = conn.cursor()
        
        if asset_id:
            cur.execute("""
                SELECT severity, COUNT(*) as count
                FROM findings
                WHERE asset_id = ?
                GROUP BY severity
            """, (asset_id,))
        else:
            cur.execute("""
                SELECT severity, COUNT(*) as count
                FROM findings
                GROUP BY severity
            """)
        
        distribution = {row['severity']: row['count'] for row in cur.fetchall()}
        
        conn.close()
        return jsonify({"status": "success", "distribution": distribution})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/analytics/classification-breakdown", methods=["GET"])
def get_classification_breakdown():
    """Get findings by semantic classification"""
    try:
        asset_id = request.args.get("asset_id")
        
        conn = get_db()
        cur = conn.cursor()
        
        if asset_id:
            cur.execute("""
                SELECT semantic_classification, COUNT(*) as count, AVG(semantic_cvss) as avg_cvss
                FROM findings
                WHERE asset_id = ?
                GROUP BY semantic_classification
                ORDER BY count DESC
            """, (asset_id,))
        else:
            cur.execute("""
                SELECT semantic_classification, COUNT(*) as count, AVG(semantic_cvss) as avg_cvss
                FROM findings
                GROUP BY semantic_classification
                ORDER BY count DESC
            """)
        
        classifications = []
        for row in cur.fetchall():
            classifications.append({
                "classification": row['semantic_classification'],
                "count": row['count'],
                "avg_cvss": row['avg_cvss']
            })
        
        conn.close()
        return jsonify({"status": "success", "classifications": classifications})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/analytics/mitre-mapping", methods=["GET"])
def get_mitre_mapping():
    """Get MITRE ATT&CK techniques distribution"""
    try:
        asset_id = request.args.get("asset_id")
        
        conn = get_db()
        cur = conn.cursor()
        
        if asset_id:
            cur.execute("""
                SELECT mitre_tactic, mitre_technique, COUNT(*) as count
                FROM findings
                WHERE asset_id = ? AND mitre_tactic IS NOT NULL
                GROUP BY mitre_tactic, mitre_technique
                ORDER BY count DESC
            """, (asset_id,))
        else:
            cur.execute("""
                SELECT mitre_tactic, mitre_technique, COUNT(*) as count
                FROM findings
                WHERE mitre_tactic IS NOT NULL
                GROUP BY mitre_tactic, mitre_technique
                ORDER BY count DESC
            """)
        
        mitre_data = []
        for row in cur.fetchall():
            mitre_data.append({
                "tactic": row['mitre_tactic'],
                "technique": row['mitre_technique'],
                "count": row['count']
            })
        
        conn.close()
        return jsonify({"status": "success", "mitre": mitre_data})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/analytics/source-breakdown", methods=["GET"])
def get_source_breakdown():
    """Get findings by scanner source"""
    try:
        asset_id = request.args.get("asset_id")
        
        conn = get_db()
        cur = conn.cursor()
        
        if asset_id:
            cur.execute("""
                SELECT source, COUNT(*) as count, 
                       COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical,
                       COUNT(CASE WHEN severity = 'high' THEN 1 END) as high
                FROM findings
                WHERE asset_id = ?
                GROUP BY source
            """, (asset_id,))
        else:
            cur.execute("""
                SELECT source, COUNT(*) as count,
                       COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical,
                       COUNT(CASE WHEN severity = 'high' THEN 1 END) as high
                FROM findings
                GROUP BY source
            """)
        
        sources = []
        for row in cur.fetchall():
            sources.append({
                "source": row['source'],
                "count": row['count'],
                "critical": row['critical'],
                "high": row['high']
            })
        
        conn.close()
        return jsonify({"status": "success", "sources": sources})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ===========================
# SCAN ENDPOINTS
# ===========================

@app.route("/api/scans/new", methods=["POST"])
def start_new_scan():
    """Start a new scan on a target"""
    try:
        data = request.json
        target = data.get("target")
        
        if not target:
            return jsonify({"status": "error", "message": "Target required"}), 400
        
        # Queue scan as background job
        scan_id = str(uuid.uuid4())
        SCAN_QUEUE[scan_id] = {"status": "queued", "target": target, "created_at": datetime.now().isoformat()}
        
        # Start scan in background thread
        thread = threading.Thread(target=_run_scan, args=(target, scan_id))
        thread.daemon = True
        thread.start()
        
        return jsonify({"status": "success", "scan_id": scan_id})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/scans/<scan_id>/status", methods=["GET"])
def get_scan_status(scan_id):
    """Get scan status"""
    try:
        if scan_id in SCAN_QUEUE:
            return jsonify({"status": "success", "scan": SCAN_QUEUE[scan_id]})
        else:
            return jsonify({"status": "error", "message": "Scan not found"}), 404
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def _run_scan(target, scan_id):
    """Background task: run security scan"""
    try:
        SCAN_QUEUE[scan_id]["status"] = "running"
        SCAN_QUEUE[scan_id]["started_at"] = datetime.now().isoformat()
        
        # Run main.py scan
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "main.py"), target],
            capture_output=True,
            text=True,
            timeout=3600
        )
        
        if result.returncode == 0:
            SCAN_QUEUE[scan_id]["status"] = "completed"
        else:
            SCAN_QUEUE[scan_id]["status"] = "failed"
            SCAN_QUEUE[scan_id]["error"] = result.stderr
        
        SCAN_QUEUE[scan_id]["completed_at"] = datetime.now().isoformat()
    
    except Exception as e:
        SCAN_QUEUE[scan_id]["status"] = "failed"
        SCAN_QUEUE[scan_id]["error"] = str(e)
        SCAN_QUEUE[scan_id]["completed_at"] = datetime.now().isoformat()


# ===========================
# REPORT ENDPOINTS
# ===========================

@app.route("/api/reports/latest/<asset_id>", methods=["GET"])
def get_latest_report(asset_id):
    """Get latest AI-generated report for asset"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Get latest scan's findings for summary
        cur.execute("""
            SELECT s.scan_id, s.started_at
            FROM scans s
            WHERE s.asset_id = ? AND s.status = 'completed'
            ORDER BY s.started_at DESC
            LIMIT 1
        """, (asset_id,))
        
        scan = cur.fetchone()
        if not scan:
            return jsonify({"status": "error", "message": "No completed scans"}), 404
        
        scan_id = scan[0]
        
        # Get findings summary
        cur.execute("""
            SELECT severity, COUNT(*) as count
            FROM findings
            WHERE scan_id = ?
            GROUP BY severity
        """, (scan_id,))
        
        severity_summary = {row['severity']: row['count'] for row in cur.fetchall()}
        
        # Get top findings
        cur.execute("""
            SELECT title, description, semantic_classification, semantic_cvss, cve
            FROM findings
            WHERE scan_id = ?
            ORDER BY semantic_cvss DESC
            LIMIT 20
        """, (scan_id,))
        
        findings = [dict(row) for row in cur.fetchall()]
        
        # Get asset info
        cur.execute("""
            SELECT a.*, GROUP_CONCAT(DISTINCT ai.value) as identifiers
            FROM assets a
            LEFT JOIN asset_identifiers ai ON a.asset_id = ai.asset_id
            WHERE a.asset_id = ?
            GROUP BY a.asset_id
        """, (asset_id,))
        
        asset = dict(cur.fetchone())
        
        conn.close()
        
        # Build report
        report = {
            "asset": asset,
            "scan_date": scan[1],
            "severity_summary": severity_summary,
            "total_findings": len(findings),
            "top_findings": findings
        }
        
        return jsonify({"status": "success", "report": report})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ===========================
# STATIC PAGES
# ===========================

@app.route("/")
def index():
    """Serve dashboard index"""
    return render_template("index.html")


@app.route("/asset/<asset_id>")
def asset_detail(asset_id):
    """Serve asset detail page"""
    return render_template("asset.html", asset_id=asset_id)


# ===========================
# HEALTH CHECK
# ===========================

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db()
        conn.close()
        return jsonify({"status": "healthy"})
    except:
        return jsonify({"status": "unhealthy"}), 500


if __name__ == "__main__":
    print("🚀 SecGuys Dashboard Server Starting...")
    print(f"📊 Database: {DB_PATH}")
    print(f"📁 Project Root: {PROJECT_ROOT}")
    app.run(debug=True, host="0.0.0.0", port=5000)
