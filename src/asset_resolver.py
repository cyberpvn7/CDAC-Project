import sqlite3
import uuid
import socket
from config import CONFIG

DB = CONFIG["database"]["path"]


def resolve_domain(domain: str) -> list:
    try:
        return list(set(socket.gethostbyname_ex(domain)[2]))
    except Exception:
        return []


def reverse_ip(ip: str):
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return None


def get_existing_asset(cur, identifier: str):
    """
    Check if asset already exists using any known identifier
    (domain, subdomain, ip, url)
    """
    cur.execute("""
        SELECT asset_id
        FROM asset_identifiers
        WHERE value = ?
        LIMIT 1
    """, (identifier,))
    row = cur.fetchone()
    return row[0] if row else None


def create_asset(target: str) -> str:
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # 1️⃣ Check if asset already exists
    existing_asset_id = get_existing_asset(cur, target)
    if existing_asset_id:
        conn.close()
        return existing_asset_id

    # 2️⃣ Create new asset
    asset_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO assets (asset_id, asset_type, primary_identifier)
        VALUES (?, ?, ?)
    """, (asset_id, "host", target))

    identifiers = []

    # 3️⃣ Resolve identifiers
    if target.replace(".", "").isdigit():
        identifiers.append(("ip", target))
        rdns = reverse_ip(target)
        if rdns:
            identifiers.append(("domain", rdns))
    else:
        identifiers.append(("domain", target))
        ips = resolve_domain(target)
        for ip in ips:
            identifiers.append(("ip", ip))

    # 4️⃣ Insert identifiers
    for identifier_type, value in identifiers:
        cur.execute("""
            INSERT OR IGNORE INTO asset_identifiers (asset_id, type, value)
            VALUES (?, ?, ?)
        """, (asset_id, identifier_type, value))

    conn.commit()
    conn.close()
    return asset_id

