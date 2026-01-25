import sqlite3
import uuid
import json
from config import CONFIG

DB = CONFIG["database"]["path"]


def ingest_finding(asset_id: str, scan_id: str, finding: dict):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO findings (
            finding_id,
            asset_id,
            scan_id,
            source,
            severity,
            confidence,
            title,
            description,
            cve,
            cwe,
            raw
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        asset_id,
        scan_id,
        finding["source"],
        finding["severity"],
        finding["confidence"],
        finding["title"],
        finding.get("description"),
        finding.get("cve"),
        finding.get("cwe"),
        json.dumps(finding.get("raw", {}))
    ))

    conn.commit()
    conn.close()

