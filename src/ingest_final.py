import json
import os

from config import CONFIG
from asset_resolver import create_asset
from scan_manager import start_scan, end_scan
from ingest_findings import ingest_finding

FINAL_JSON = "final.json"


def severity_to_confidence(sev: str) -> float:
    return {
        "critical": 0.95,
        "high": 0.90,
        "medium": 0.75,
        "low": 0.60,
        "info": 0.40
    }.get(sev, 0.50)


def ingest_final_json():
    if not os.path.exists(FINAL_JSON):
        print("❌ final.json not found")
        return

    with open(FINAL_JSON, "r") as f:
        data = json.load(f)

    # 1️⃣ Extract target
    target = data.get("target")
    if not target:
        print("❌ target missing in final.json")
        return

    # 2️⃣ Create/reuse asset
    asset_id = create_asset(target)

    # 3️⃣ Create NEW scan (history preserved)
    scan_id = start_scan(asset_id, "aggregated_scan")

    inserted = 0

    try:
        # 4️⃣ Ingest service / nuclei / exploit findings
        for item in data.get("findings", []):
            port = item.get("port")
            service = item.get("service")
            version = item.get("version")

            context = {
                "port": port,
                "service": service,
                "version": version
            }

            # Nuclei findings
            for n in item.get("nuclei", []):
                ingest_finding(asset_id, scan_id, {
                    "source": "nuclei",
                    "severity": "medium",
                    "confidence": severity_to_confidence("medium"),
                    "title": n,
                    "description": f"{service} service on port {port}",
                    "cve": None,
                    "cwe": None,
                    "raw": context
                })
                inserted += 1

            # Exploit hints
            for e in item.get("exploits", []):
                ingest_finding(asset_id, scan_id, {
                    "source": "searchsploit",
                    "severity": "high",
                    "confidence": severity_to_confidence("high"),
                    "title": e,
                    "description": f"Exploit related to {service} on port {port}",
                    "cve": None,
                    "cwe": None,
                    "raw": context
                })
                inserted += 1

        # 5️⃣ Ingest Nikto findings
        for n in data.get("nikto_findings", []):
            ingest_finding(asset_id, scan_id, {
                "source": "nikto",
                "severity": "low",
                "confidence": severity_to_confidence("low"),
                "title": n[:120],
                "description": n,
                "cve": None,
                "cwe": None,
                "raw": {"tool": "nikto"}
            })
            inserted += 1

        end_scan(scan_id, "completed")

    except Exception as e:
        end_scan(scan_id, "failed")
        print("❌ Ingestion failed:", e)
        return

    print("✅ final.json ingested successfully")
    print("Asset ID:", asset_id)
    print("Scan ID :", scan_id)
    print("Findings:", inserted)


if __name__ == "__main__":
    ingest_final_json()

