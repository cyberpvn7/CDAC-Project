#!/bin/bash

# --- Styling ---
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
MAGENTA='\033[0;35m'
RED='\033[0;31m'
NC='\033[0m'

# --- User Input ---
echo -e "${YELLOW}Enter Target (IP or Domain): ${NC}"
read TARGET

if [ -z "$TARGET" ]; then
    echo -e "${RED}[!] No target provided. Exiting.${NC}"
    exit 1
fi

# Handle URL for web tools
if [[ "$TARGET" =~ ^http://|^https:// ]]; then
    WEB_TARGET="$TARGET"
else
    WEB_TARGET="http://$TARGET"
fi

LOG_DIR="scan_results"
mkdir -p "$LOG_DIR"

# --- Banner ---
echo -e "${MAGENTA}======================================================${NC}"
echo -e "${CYAN}        CENTRALIZED VULN SCANNER ${NC}"
echo -e "${CYAN}  (WhatWeb | Nikto | Nmap | Nuclei)${NC}"
echo -e "${MAGENTA}======================================================${NC}"
echo -e "${CYAN}Target:${NC} ${GREEN}$TARGET${NC}"
echo

# 1️⃣ WhatWeb
echo -e "${YELLOW}[+] WhatWeb running (Technology Detection)...${NC}"
whatweb "$WEB_TARGET" --log-json="$LOG_DIR/whatweb.json" > /dev/null 2>&1
if [ -f "$LOG_DIR/whatweb.json" ]; then
    echo -e "${GREEN}[✔] WhatWeb completed${NC}"
else
    echo -e "${RED}[!] WhatWeb failed or no web service${NC}"
fi
echo

# 2️⃣ Nikto
echo -e "${YELLOW}[+] Nikto running (Web Server Misconfiguration Scan)...${NC}"
nikto -h "$WEB_TARGET" -o "$LOG_DIR/nikto.txt" > /dev/null 2>&1
if [ -f "$LOG_DIR/nikto.txt" ]; then
    echo -e "${GREEN}[✔] Nikto completed${NC}"
else
    echo -e "${RED}[!] Nikto failed${NC}"
fi
echo

# 3️⃣ Nmap
echo -e "${YELLOW}[+] Nmap running (Port & Service Scan)...${NC}"
nmap -sV -T4 -p- -oX "$LOG_DIR/nmap.xml" "$TARGET" > /dev/null 2>&1
echo -e "${GREEN}[✔] Nmap completed${NC}"
echo

# 4️⃣ Nuclei
echo -e "${YELLOW}[+] Nuclei running (Vulnerability Scan)...${NC}"
nuclei -u "$WEB_TARGET" -j -o "$LOG_DIR/nuclei.json" > /dev/null 2>&1
echo -e "${GREEN}[✔] Nuclei completed${NC}"
echo

# 5️⃣ SearchSploit
echo -e "${YELLOW}[+] SearchSploit running (Exploit Mapping)...${NC}"
searchsploit --nmap "$LOG_DIR/nmap.xml" --json > "$LOG_DIR/exploits_raw.json" 2>/dev/null
echo -e "${GREEN}[✔] SearchSploit completed${NC}"
echo

# 6️⃣ Normalization → final.json
echo -e "${YELLOW}[+] Normalizing all results into final.json...${NC}"

python3 <<EOF
import json
import xml.etree.ElementTree as ET
import os

final = {
    "target": "$TARGET",
    "tech_stack": [],
    "nikto_findings": [],
    "findings": []
}

# --- WhatWeb ---
if os.path.exists("$LOG_DIR/whatweb.json"):
    try:
        with open("$LOG_DIR/whatweb.json") as f:
            for line in f:
                data = json.loads(line)
                final["tech_stack"] = list(data.get("plugins", {}).keys())
    except:
        pass

# --- Nikto ---
if os.path.exists("$LOG_DIR/nikto.txt"):
    try:
        with open("$LOG_DIR/nikto.txt") as f:
            for line in f:
                if line.startswith("+"):
                    final["nikto_findings"].append(line.strip())
    except:
        pass

# --- Nmap ---
if os.path.exists("$LOG_DIR/nmap.xml"):
    tree = ET.parse("$LOG_DIR/nmap.xml")
    for port in tree.findall(".//port"):
        state = port.find("state")
        if state is not None and state.get("state") == "open":
            srv = port.find("service")
            final["findings"].append({
                "port": port.get("portid"),
                "service": srv.get("name") if srv is not None else "unknown",
                "version": srv.get("version", "unknown") if srv is not None else "unknown",
                "nuclei": [],
                "exploits": []
            })

# --- Nuclei ---
if os.path.exists("$LOG_DIR/nuclei.json"):
    with open("$LOG_DIR/nuclei.json") as f:
        for line in f:
            try:
                data = json.loads(line)
                for fnd in final["findings"]:
                    if str(data.get("port")) == fnd["port"]:
                        fnd["nuclei"].append(
                            data.get("info", {}).get("name", "Unknown")
                        )
            except:
                pass

# --- SearchSploit ---
if os.path.exists("$LOG_DIR/exploits_raw.json"):
    with open("$LOG_DIR/exploits_raw.json") as f:
        content = f.read()

    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(content):
        try:
            obj, end = decoder.raw_decode(content, idx)
            for ex in obj.get("RESULTS_EXPLOIT", []):
                for fnd in final["findings"]:
                    if fnd["service"] != "unknown" and fnd["service"].lower() in ex["Title"].lower():
                        if ex["Title"] not in fnd["exploits"]:
                            fnd["exploits"].append(ex["Title"])
            idx = end
        except:
            break

with open("final.json", "w") as f:
    json.dump(final, f, indent=2)
EOF

# 7️⃣ Final message
if [ -f "final.json" ]; then
    echo
    echo -e "${MAGENTA}======================================================${NC}"
    echo -e "${GREEN}[✔] final.json created successfully${NC}"
    echo -e "${CYAN}Centralized vulnerability scanning complete.${NC}"
    echo
    echo -e "${YELLOW}👉 NEXT STEP:${NC}"
    echo -e "${GREEN}Run predictive / AI analysis:${NC}"
    echo -e "${CYAN}    python3 analyze.py${NC}"
    echo -e "${MAGENTA}======================================================${NC}"
else
    echo -e "${RED}[!] Failed to generate final.json${NC}"
fi

