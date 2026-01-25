import sqlite3
import uuid
from datetime import datetime
from config import CONFIG

DB = CONFIG["database"]["path"]


def start_scan(asset_id: str, tool: str) -> str:
    scan_id = str(uuid.uuid4())

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO scans (
            scan_id,
            asset_id,
            tool,
            status,
            started_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        scan_id,
        asset_id,
        tool,
        "running",
        datetime.utcnow()
    ))

    conn.commit()
    conn.close()
    return scan_id


def end_scan(scan_id: str, status: str = "completed"):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        UPDATE scans
        SET status = ?, completed_at = ?
        WHERE scan_id = ?
    """, (
        status,
        datetime.utcnow(),
        scan_id
    ))

    conn.commit()
    conn.close()

