#!/usr/bin/env python3
"""
SecGuys Security Dashboard - Backend
Serves data from scan results and provides API endpoints for visualization
"""

import json
import os
import sys
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
import sqlite3

from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__)
CORS(app)

# Configuration
BASE_DIR = Path(__file__).parent.parent
SCAN_RESULTS_DIR = BASE_DIR / 'scan_results'
OUTPUT_DIR = BASE_DIR / 'output'
DB_PATH = BASE_DIR / 'security_analysis.db'

# Globals for scan state
current_scan_process = None
current_scan_output = []
scan_history = []

def load_json_file(filepath):
    """Safely load JSON file"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
    return None

def load_scan_history():
    """Load all scan results from disk"""
    history = []
    
    # Try loading final.json
    final_json = load_json_file(OUTPUT_DIR / 'final.json')
    if final_json:
        history.append({
            'id': 'final_scan',
            'timestamp': datetime.now().isoformat(),
            'target': final_json.get('target', 'Unknown'),
            'type': 'Full Scan',
            'status': 'completed',
            'findings_count': len(final_json.get('findings', [])),
            'tech_stack': final_json.get('tech_stack', [])
        })
    
    return history

@app.route('/')
def index():
    """Render main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    """Get overall dashboard statistics"""
    try:
        asset_id = request.args.get('asset_id')
        
        stats = {
            'total_assets': 0,
            'total_findings': 0,
            'critical_findings': 0,
            'high_findings': 0,
            'medium_findings': 0,
            'low_findings': 0,
            'info_findings': 0,
            'average_risk_score': 0
        }
        
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        if asset_id:
            # Get stats for specific asset
            cur.execute("""
                SELECT severity, COUNT(*) as count FROM findings 
                WHERE asset_id = ? 
                GROUP BY severity
            """, (asset_id,))
            stats['total_assets'] = 1
        else:
            # Get stats for all assets
            cur.execute("SELECT COUNT(DISTINCT asset_id) as count FROM assets")
            result = cur.fetchone()
            stats['total_assets'] = result['count'] if result else 0
            
            # Get overall finding stats
            cur.execute("""
                SELECT severity, COUNT(*) as count FROM findings 
                GROUP BY severity
            """)
        
        severity_rows = cur.fetchall()
        for row in severity_rows:
            severity = row['severity'].lower()
            count = row['count']
            
            stats['total_findings'] += count
            if severity == 'critical':
                stats['critical_findings'] = count
            elif severity == 'high':
                stats['high_findings'] = count
            elif severity == 'medium':
                stats['medium_findings'] = count
            elif severity == 'low':
                stats['low_findings'] = count
            else:
                stats['info_findings'] = count
        
        conn.close()
        
        total = sum([stats['critical_findings'], stats['high_findings'], 
                    stats['medium_findings'], stats['low_findings']])
        if total > 0:
            stats['average_risk_score'] = round(
                (stats['critical_findings'] * 10 + stats['high_findings'] * 7 + 
                 stats['medium_findings'] * 4 + stats['low_findings'] * 1) / total, 2
            )
        
        return jsonify(stats)
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/findings', methods=['GET'])
def get_findings():
    """Get all findings with optional filtering"""
    try:
        severity = request.args.get('severity', '').lower()
        asset_id = request.args.get('asset_id')
        
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        query = "SELECT * FROM findings WHERE 1=1"
        params = []
        
        if severity:
            query += " AND LOWER(severity) = ?"
            params.append(severity)
        
        if asset_id:
            query += " AND asset_id = ?"
            params.append(asset_id)
            
        scan_id = request.args.get('scan_id')
        if scan_id:
            query += " AND scan_id = ?"
            params.append(scan_id)
        
        query += " ORDER BY semantic_cvss DESC"
        
        cur.execute(query, params)
        findings_rows = cur.fetchall()
        
        findings = []
        for row in findings_rows:
            findings.append({
                'id': row['finding_id'],
                'title': row['title'],
                'severity': row['severity'],
                'cve': row['cve'],
                'description': row['description'],
                'source': row['source'],
                'semantic': {
                    'cvss_score': row['semantic_cvss'] or 0,
                    'mitre_tactic': row['mitre_tactic'] or 'Unknown',
                    'mitre_technique': row['mitre_technique'] or 'Unknown'
                }
            })
        
        conn.close()
        return jsonify({'findings': findings, 'total': len(findings)})
    except Exception as e:
        print(f"Error getting findings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/finding/<finding_id>', methods=['GET'])
def get_finding_detail(finding_id):
    """Get full details for a single finding"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM findings WHERE finding_id = ?", (finding_id,))
        row = cur.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'error': 'Finding not found'}), 404
            
        return jsonify({
            'id': row['finding_id'],
            'title': row['title'],
            'severity': row['severity'],
            'description': row['description'],
            'solution': 'No automated solution available.', # Placeholder or use a real field if DB has it
            'cve': row['cve'],
            'cvss': row['semantic_cvss'],
            'source': row['source'],
            'raw': row['raw'], # Full tool output
            'mitre': {
                'tactic': row['mitre_tactic'],
                'technique': row['mitre_technique']
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ... (Severity chart endpoint) ...

# ...

@app.route('/api/asset/<asset_id>/details', methods=['GET'])
def get_asset_details(asset_id):
    """Get detailed information about a specific asset"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Get asset info
        cur.execute("SELECT * FROM assets WHERE asset_id = ?", (asset_id,))
        asset_row = cur.fetchone()
        
        if not asset_row:
            conn.close()
            return jsonify({'error': 'Asset not found'}), 404
        
        details = {
            'target': asset_row['primary_identifier'],
            'tech_stack': [],
            'services': [],
            'findings': []
        }
        
        # Get findings for this asset
        cur.execute("""
            SELECT 
                finding_id, title, severity, cve, description, source,
                semantic_cvss as cvss_score, mitre_tactic
            FROM findings 
            WHERE asset_id = ? 
            ORDER BY semantic_cvss DESC
        """, (asset_id,))
        
        findings_rows = cur.fetchall()
        for f_row in findings_rows:
            details['findings'].append({
                'id': f_row['finding_id'],
                'title': f_row['title'],
                'severity': f_row['severity'],
                'cve': f_row['cve'],
                'description': f_row['description'],
                'source': f_row['source'],
                'semantic': {
                    'cvss_score': f_row['cvss_score'] or 0,
                    'mitre_tactic': f_row['mitre_tactic']
                }
            })
        
        # Extract unique services
        cur.execute("""
            SELECT DISTINCT source
            FROM findings 
            WHERE asset_id = ?
        """, (asset_id,))
        
        service_rows = cur.fetchall()
        for s_row in service_rows:
            details['services'].append({
                'service': s_row['source'],
                'version': 'N/A'
            })
        
        # Try to get tech stack from final.json
        final_json = load_json_file(OUTPUT_DIR / 'final.json')
        if final_json:
            details['tech_stack'] = final_json.get('tech_stack', [])
        
        conn.close()
        return jsonify(details)
    except Exception as e:
        print(f"Error getting asset details: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/findings-by-severity', methods=['GET'])
def get_findings_by_severity():
    """Get severity distribution chart data"""
    try:
        asset_id = request.args.get('asset_id')
        
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        query = "SELECT severity, COUNT(*) as count FROM findings WHERE 1=1"
        params = []
        
        if asset_id:
            query += " AND asset_id = ?"
            params.append(asset_id)
        
        query += " GROUP BY severity"
        cur.execute(query, params)
        
        severity_count = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        total = 0
        
        for row in cur.fetchall():
            severity = row['severity'].lower()
            count = row['count']
            if severity in severity_count:
                severity_count[severity] = count
            else:
                severity_count['info'] = count
            total += count
        
        conn.close()
        return jsonify({'data': severity_count, 'total': total})
    except Exception as e:
        print(f"Error getting severity distribution: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/findings-by-source', methods=['GET'])
def get_findings_by_source():
    """Get findings distribution by source (nuclei, exploits, nikto)"""
    try:
        asset_id = request.args.get('asset_id')
        
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        query = "SELECT source, COUNT(*) as count FROM findings WHERE 1=1"
        params = []
        
        if asset_id:
            query += " AND asset_id = ?"
            params.append(asset_id)
        
        query += " GROUP BY source"
        cur.execute(query, params)
        
        source_count = {}
        for row in cur.fetchall():
            source_count[row['source'] or 'unknown'] = row['count']
        
        conn.close()
        return jsonify({'data': source_count})
    except Exception as e:
        print(f"Error getting source distribution: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/top-vulnerabilities', methods=['GET'])
def get_top_vulnerabilities():
    """Get top 10 vulnerabilities by CVSS score"""
    try:
        asset_id = request.args.get('asset_id')
        
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        query = """
            SELECT title, severity, semantic_cvss, mitre_tactic 
            FROM findings 
            WHERE 1=1
        """
        params = []
        
        if asset_id:
            query += " AND asset_id = ?"
            params.append(asset_id)
        
        query += " ORDER BY semantic_cvss DESC LIMIT 10"
        cur.execute(query, params)
        
        result = []
        for row in cur.fetchall():
            result.append({
                'title': row['title'] or 'Unknown',
                'severity': row['severity'] or 'unknown',
                'cvss_score': row['semantic_cvss'] or 0,
                'mitre_tactic': row['mitre_tactic'] or 'N/A'
            })
        
        conn.close()
        return jsonify({'vulnerabilities': result})
    except Exception as e:
        print(f"Error getting top vulnerabilities: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mitre-tactics', methods=['GET'])
def get_mitre_tactics():
    """Get MITRE ATT&CK tactics distribution"""
    try:
        asset_id = request.args.get('asset_id')
        
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        query = """
            SELECT mitre_tactic, COUNT(*) as count 
            FROM findings 
            WHERE mitre_tactic IS NOT NULL AND 1=1
        """
        params = []
        
        if asset_id:
            query += " AND asset_id = ?"
            params.append(asset_id)
        
        query += " GROUP BY mitre_tactic ORDER BY count DESC"
        cur.execute(query, params)
        
        tactic_count = {}
        for row in cur.fetchall():
            tactic_count[row['mitre_tactic'] or 'Unknown'] = row['count']
        
        conn.close()
        return jsonify({'data': tactic_count})
    except Exception as e:
        print(f"Error getting MITRE tactics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/assets', methods=['GET'])
def get_assets():
    """Get all scanned assets from database"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Query assets from database
        cur.execute("""
            SELECT 
                a.asset_id,
                a.primary_identifier as target,
                COUNT(DISTINCT f.finding_id) as findings_count,
                MAX(s.completed_at) as last_scan
            FROM assets a
            LEFT JOIN findings f ON a.asset_id = f.asset_id
            LEFT JOIN scans s ON a.asset_id = s.asset_id
            GROUP BY a.asset_id
            ORDER BY s.completed_at DESC
        """)
        
        assets = []
        for row in cur.fetchall():
            # Get tech stack from final.json for additional context
            tech_stack = []
            final_json = load_json_file(OUTPUT_DIR / 'final.json')
            if final_json:
                tech_stack = final_json.get('tech_stack', [])
            
            assets.append({
                'id': row['asset_id'],
                'target': row['target'],
                'tech_stack': tech_stack,
                'findings_count': row['findings_count'] or 0,
                'last_scan': row['last_scan'] if row['last_scan'] else datetime.now().isoformat()
            })
        
        conn.close()
        return jsonify({'assets': assets})
    except Exception as e:
        print(f"Error getting assets: {e}")
        return jsonify({'error': str(e), 'assets': []}), 500




@app.route('/api/asset/<asset_id>/scans', methods=['GET'])
def get_asset_scans(asset_id):
    """Get scan history for a specific asset"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT scan_id, tool, status, started_at, completed_at
            FROM scans
            WHERE asset_id = ?
            ORDER BY started_at DESC
        """, (asset_id,))

        scans = []
        for row in cur.fetchall():
            scans.append({
                'scan_id': row['scan_id'],
                'tool': row['tool'],
                'status': row['status'],
                'started_at': row['started_at'],
                'completed_at': row['completed_at']
            })

        conn.close()
        return jsonify({'scans': scans, 'total': len(scans)})
    except Exception as e:
        print(f"Error getting asset scans: {e}")
        return jsonify({'error': str(e), 'scans': []}), 500


@app.route('/api/asset/<asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    """Delete an asset and related data (findings, scans, reports)"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Ensure asset exists
        cur.execute("SELECT asset_id, primary_identifier FROM assets WHERE asset_id = ?", (asset_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return jsonify({'error': 'Asset not found'}), 404

        target_name = row['primary_identifier']

        # Delete reports and remove files
        cur.execute("SELECT report_id, report_path FROM reports WHERE asset_id = ?", (asset_id,))
        report_rows = cur.fetchall()
        report_paths = [r['report_path'] for r in report_rows if r['report_path']]

        cur.execute("DELETE FROM reports WHERE asset_id = ?", (asset_id,))

        # Delete findings
        cur.execute("DELETE FROM findings WHERE asset_id = ?", (asset_id,))

        # Delete scans
        cur.execute("DELETE FROM scans WHERE asset_id = ?", (asset_id,))

        # Delete asset
        cur.execute("DELETE FROM assets WHERE asset_id = ?", (asset_id,))

        conn.commit()
        conn.close()

        # Remove report files from disk
        for rp in report_paths:
            try:
                p = Path(rp)
                if not p.is_absolute():
                    p = BASE_DIR / rp
                if p.exists():
                    p.unlink()
                    print(f"Deleted report file: {p}")
            except Exception as e:
                print(f"Error deleting report file {rp}: {e}")

        print(f"Deleted asset {asset_id} ({target_name}) and related data")
        return jsonify({'status': 'deleted', 'asset_id': asset_id, 'target': target_name})
    except Exception as e:
        print(f"Error deleting asset: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/report', methods=['GET'])
def get_report():
    """Get the full security assessment report"""
    try:
        report_path = BASE_DIR / 'db_report.md'
        if os.path.exists(report_path):
            with open(report_path, 'r') as f:
                report_content = f.read()
            return jsonify({'report': report_content})
        return jsonify({'error': 'Report not found'}), 404
    except Exception as e:
        print(f"Error getting report: {e}")
        return jsonify({'error': str(e)}), 500

def capture_scan_output(process):
    """Capture output from a running process"""
    global current_scan_output
    current_scan_output = []
    
    while process.poll() is None:
        output = process.stdout.readline()
        if output:
            line = output.decode('utf-8').strip()
            if line:
                current_scan_output.append({
                    'timestamp': datetime.now().isoformat(),
                    'message': line
                })
                print(line)
        time.sleep(0.1)
    
    # Capture any remaining output
    remaining = process.stdout.read().decode('utf-8')
    if remaining:
        for line in remaining.split('\n'):
            if line.strip():
                current_scan_output.append({
                    'timestamp': datetime.now().isoformat(),
                    'message': line.strip()
                })

@app.route('/api/scan/start', methods=['POST'])
def start_scan():
    """Start a new security scan"""
    global current_scan_process, current_scan_output
    
    try:
        data = request.json
        target = data.get('target')
        
        if not target:
            return jsonify({'error': 'Target is required'}), 400
        
        if current_scan_process and current_scan_process.poll() is None:
            return jsonify({'error': 'A scan is already in progress'}), 400
        
        # Start the main scanner script
        main_script = BASE_DIR / 'main.py'
        current_scan_output = []
        
        current_scan_process = subprocess.Popen(
            ['python3', str(main_script), target],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=str(BASE_DIR)
        )
        
        # Start capturing output in a separate thread
        output_thread = threading.Thread(target=capture_scan_output, args=(current_scan_process,))
        output_thread.daemon = True
        output_thread.start()
        
        return jsonify({
            'status': 'started',
            'target': target,
            'pid': current_scan_process.pid
        })
    except Exception as e:
        print(f"Error starting scan: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/scan/status', methods=['GET'])
def get_scan_status():
    """Get current scan status"""
    global current_scan_process, current_scan_output
    
    try:
        if not current_scan_process:
            return jsonify({'status': 'idle', 'output': []})
        
        poll_result = current_scan_process.poll()
        
        if poll_result is None:
            status = 'running'
        elif poll_result == 0:
            status = 'completed'
        else:
            status = 'failed'
        
        return jsonify({
            'status': status,
            'output': current_scan_output[-50:],  # Last 50 lines
            'output_count': len(current_scan_output),
            'exit_code': poll_result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scan/stop', methods=['POST'])
def stop_scan():
    """Stop the current scan"""
    global current_scan_process
    
    try:
        if current_scan_process and current_scan_process.poll() is None:
            current_scan_process.terminate()
            time.sleep(1)
            if current_scan_process.poll() is None:
                current_scan_process.kill()
            return jsonify({'status': 'stopped'})
        return jsonify({'status': 'no_scan_running'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===========================
# REPORTS API ENDPOINTS
# ===========================

@app.route('/api/reports', methods=['GET'])
def get_reports():
    """Get all generated reports with metadata"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                report_id,
                target_name,
                generated_at,
                report_path,
                report_type,
                status
            FROM reports
            ORDER BY generated_at DESC
        """)
        
        reports = []
        for row in cur.fetchall():
            reports.append({
                'id': row['report_id'],
                'target_name': row['target_name'],
                'generated_at': row['generated_at'],
                'report_path': row['report_path'],
                'report_type': row['report_type'],
                'status': row['status']
            })
        
        conn.close()
        return jsonify({'reports': reports, 'total': len(reports)})
    except Exception as e:
        print(f"Error getting reports: {e}")
        return jsonify({'error': str(e), 'reports': [], 'total': 0}), 500

@app.route('/api/reports/<int:report_id>', methods=['GET'])
def get_report_content(report_id):
    """Get specific report content"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("""
            SELECT report_path, target_name, generated_at
            FROM reports
            WHERE report_id = ?
        """, (report_id,))
        
        row = cur.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'error': 'Report not found'}), 404
        
        report_path = Path(row['report_path'])
        if not report_path.exists():
            return jsonify({'error': 'Report file not found'}), 404
        
        with open(report_path, 'r') as f:
            content = f.read()
        
        return jsonify({
            'id': report_id,
            'target_name': row['target_name'],
            'generated_at': row['generated_at'],
            'content': content
        })
    except Exception as e:
        print(f"Error getting report content: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/<int:report_id>/download', methods=['GET'])
def download_report(report_id):
    """Download report as file"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("""
            SELECT report_path, target_name, generated_at
            FROM reports
            WHERE report_id = ?
        """, (report_id,))
        
        row = cur.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'error': 'Report not found'}), 404
        
        report_path = Path(row['report_path'])
        if not report_path.exists():
            return jsonify({'error': 'Report file not found'}), 404
        
        return send_file(
            report_path,
            as_attachment=True,
            download_name=report_path.name,
            mimetype='text/markdown'
        )
    except Exception as e:
        print(f"Error downloading report: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/<int:report_id>', methods=['DELETE'])
def delete_report(report_id):
    """Delete a report"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("""
            SELECT report_path
            FROM reports
            WHERE report_id = ?
        """, (report_id,))
        
        row = cur.fetchone()
        if not row:
            conn.close()
            return jsonify({'error': 'Report not found'}), 404
        
        report_path = Path(row['report_path'])
        
        # Delete from database
        cur.execute("DELETE FROM reports WHERE report_id = ?", (report_id,))
        conn.commit()
        conn.close()
        
        # Delete file if exists
        if report_path.exists():
            report_path.unlink()
            print(f"Deleted report file: {report_path}")
        
        return jsonify({'status': 'deleted', 'message': f'Report {report_id} deleted'})
    except Exception as e:
        print(f"Error deleting report: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    print("Starting SecGuys Dashboard on http://localhost:5000")
    print("Press Ctrl+C to stop")
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
