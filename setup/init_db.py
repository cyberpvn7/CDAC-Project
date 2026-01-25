#!/usr/bin/env python3
"""
Database Schema Initialization
Ensures all required tables exist before running the pipeline
"""

import sqlite3
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import CONFIG


def init_database():
    """Initialize SQLite database with required schema"""
    db_path = CONFIG["database"]["path"]
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Assets Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                asset_id TEXT PRIMARY KEY,
                asset_type TEXT NOT NULL DEFAULT 'host',
                primary_identifier TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Asset Identifiers Table (IPs, domains, URLs for same asset)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asset_identifiers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                type TEXT NOT NULL,
                value TEXT NOT NULL,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id),
                UNIQUE(asset_id, value)
            )
        """)
        
        # Scans Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                scan_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                tool TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
            )
        """)
        
        # Findings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                finding_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                scan_id TEXT NOT NULL,
                source TEXT NOT NULL,
                severity TEXT,
                confidence REAL,
                title TEXT NOT NULL,
                description TEXT,
                cve TEXT,
                cwe TEXT,
                raw TEXT,
                semantic_classification TEXT,
                semantic_cvss REAL,
                attack_capability TEXT,
                mitre_tactic TEXT,
                mitre_technique TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id),
                FOREIGN KEY (scan_id) REFERENCES scans(scan_id)
            )
        """)
        
        # Create indexes for efficient querying
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scans_asset_started 
            ON scans(asset_id, started_at DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_findings_scan 
            ON findings(scan_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_findings_asset 
            ON findings(asset_id)
        """)
        
        conn.commit()
        conn.close()
        
        print(f"✅ Database initialized: {db_path}")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
