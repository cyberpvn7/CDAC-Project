import json
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

# =========================
# MODEL
# =========================
MODEL_NAME = "jackaduma/SecBERT"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
model.eval()

# =========================
# SECURITY KNOWLEDGE
# =========================
SECURITY_KNOWLEDGE = {
    "Remote Code Execution": {
        "keywords": ["remote code", "command execution", "rce", "backdoor", "shell"],
        "mitre": ("Execution", "T1059")
    },
    "SQL Injection": {
        "keywords": ["sql injection", "sqli", "database", "query"],
        "mitre": ("Initial Access", "T1190")
    },
    "Authentication Weakness": {
        "keywords": ["anonymous login", "default login", "password-based"],
        "mitre": ("Credential Access", "T1110")
    },
    "Information Disclosure": {
        "keywords": ["phpinfo", "version", "banner", "headers", "enumeration"],
        "mitre": ("Discovery", "T1082")
    },
    "Directory Traversal": {
        "keywords": ["directory indexing", "file read", "path traversal"],
        "mitre": ("Discovery", "T1083")
    }
}

CAPABILITY_MAP = {
    "Remote Code Execution": "Execute arbitrary commands remotely",
    "SQL Injection": "Read or modify backend database",
    "Authentication Weakness": "Bypass authentication mechanisms",
    "Information Disclosure": "Access sensitive system information",
    "Directory Traversal": "Read arbitrary files from the system",
    "Informational": "Gather system and service information"
}

# =========================
# AI DEFINITIONS
# =========================
ATTACK_DEFINITIONS = {
    "Remote Code Execution": "Ability to execute arbitrary commands on a remote system",
    "SQL Injection": "Injection of malicious SQL queries to manipulate a database",
    "Authentication Weakness": "Ability to bypass or abuse authentication mechanisms",
    "Information Disclosure": "Exposure of sensitive system or application information",
    "Directory Traversal": "Reading files outside the intended directory"
}

# =========================
# EMBEDDINGS
# =========================
def get_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=256)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1)

ATTACK_EMBEDDINGS = {
    k: get_embedding(v) for k, v in ATTACK_DEFINITIONS.items()
}

# =========================
# CVSS AUTO ESTIMATION
# =========================
CVSS_BASE = {
    "Remote Code Execution": 9.8,
    "SQL Injection": 8.8,
    "Authentication Weakness": 7.5,
    "Directory Traversal": 6.5,
    "Information Disclosure": 5.3,
    "Informational": 3.1
}

def estimate_cvss(attack_type, source):
    score = CVSS_BASE.get(attack_type, 3.1)

    if source == "exploitdb":
        score += 0.5

    if attack_type != "Authentication Weakness":
        score += 0.3  # No auth required

    score = min(round(score, 1), 10.0)

    severity = (
        "Critical" if score >= 9.0 else
        "High" if score >= 7.0 else
        "Medium" if score >= 4.0 else
        "Low"
    )

    vector = f"CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"

    return score, severity, vector

# =========================
# RISK SCORE (YOUR LOGIC)
# =========================
def calculate_risk_score(attack_type, source):
    base = {
        "Remote Code Execution": 40,
        "SQL Injection": 30,
        "Authentication Weakness": 25,
        "Information Disclosure": 10,
        "Directory Traversal": 15,
        "Informational": 5
    }.get(attack_type, 5)

    source_weight = {
        "exploitdb": 30,
        "nuclei": 20,
        "nikto": 10
    }.get(source, 5)

    return min(base + source_weight, 100)

def risk_level(score):
    if score >= 75:
        return "Critical"
    elif score >= 50:
        return "High"
    elif score >= 25:
        return "Medium"
    return "Low"

# =========================
# CLASSIFICATION
# =========================
def rule_based(text):
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
    return None

def analyze(text):
    return rule_based(text) or semantic_classify(text) or {
        "attack_type": "Informational",
        "capability": CAPABILITY_MAP["Informational"],
        "mitre": ("Discovery", "T1082"),
        "confidence": "Low"
    }

# =========================
# DEDUP
# =========================
def deduplicate(results):
    unique = {}
    for r in results:
        key = (r["attack_type"], r.get("service", ""), r.get("port", ""))
        if key not in unique:
            r["evidence_count"] = 1
            unique[key] = r
        else:
            unique[key]["evidence_count"] += 1
    return list(unique.values())

# =========================
# PIPELINE
# =========================
def run():
    with open("final.json") as f:
        data = json.load(f)

    results = []

    for finding in data.get("nikto_findings", []):
        a = analyze(finding)
        risk = calculate_risk_score(a["attack_type"], "nikto")
        cvss, sev, vec = estimate_cvss(a["attack_type"], "nikto")

        results.append({
            "source": "nikto",
            "description": finding,
            "attack_type": a["attack_type"],
            "capability": a["capability"],
            "risk_score": risk,
            "risk_level": risk_level(risk),
            "cvss_score": cvss,
            "cvss_severity": sev,
            "cvss_vector": vec,
            "mitre": {"tactic": a["mitre"][0], "technique": a["mitre"][1]},
            "confidence": a["confidence"]
        })

    for s in data.get("findings", []):
        for n in s.get("nuclei", []):
            text = f"{s['service']} port {s['port']} {n}"
            a = analyze(text)
            risk = calculate_risk_score(a["attack_type"], "nuclei")
            cvss, sev, vec = estimate_cvss(a["attack_type"], "nuclei")

            results.append({
                "source": "nuclei",
                "service": s["service"],
                "port": s["port"],
                "description": n,
                "attack_type": a["attack_type"],
                "capability": a["capability"],
                "risk_score": risk,
                "risk_level": risk_level(risk),
                "cvss_score": cvss,
                "cvss_severity": sev,
                "cvss_vector": vec,
                "mitre": {"tactic": a["mitre"][0], "technique": a["mitre"][1]},
                "confidence": a["confidence"]
            })

        for e in s.get("exploits", []):
            cvss, sev, vec = estimate_cvss("Remote Code Execution", "exploitdb")
            risk = calculate_risk_score("Remote Code Execution", "exploitdb")

            results.append({
                "source": "exploitdb",
                "service": s["service"],
                "port": s["port"],
                "description": e,
                "attack_type": "Remote Code Execution",
                "capability": CAPABILITY_MAP["Remote Code Execution"],
                "risk_score": risk,
                "risk_level": risk_level(risk),
                "cvss_score": cvss,
                "cvss_severity": sev,
                "cvss_vector": vec,
                "mitre": {"tactic": "Execution", "technique": "T1059"},
                "confidence": "Very High (Exploit)"
            })

    with open("semantic_output.json", "w") as f:
        json.dump(deduplicate(results), f, indent=4)

    print("✅ CVSS-enriched security intelligence generated")

if __name__ == "__main__":
    run()
