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

# Handle URL for nuclei
if [[ "$TARGET" =~ ^http://|^https:// ]]; then
    NUCLEI_TARGET="$TARGET"
else
    NUCLEI_TARGET="http://$TARGET"
fi

LOG_DIR="scan_results"
mkdir -p "$LOG_DIR"

# --- Fixed Animated Spinner ---
spinner() {
    local delay=0.1
    local spinstr='|/-\'
    while [ -d /proc/$PID_NMAP ] || [ -d /proc/$PID_NUCLEI ]; do
        local temp=${spinstr#?}
        printf "\r ${CYAN}[%c] Parallel Engines Running (Nmap + Nuclei)...${NC}" "$spinstr"
        spinstr=$temp${spinstr%"$temp"}
        sleep $delay
    done
    printf "\r${GREEN}[✔] Service Discovery & Vuln Scanning Complete!          ${NC}\n"
}

echo -e "${MAGENTA}======================================================${NC}"
echo -e "${CYAN}    PREDICTIVE INGESTOR v2.3 (Dynamic Target)${NC}"
echo -e "${MAGENTA}======================================================${NC}"
echo -e "${CYAN}Target Set To:${NC} ${GREEN}$TARGET${NC}"

# 1. Start background tasks
(nmap -sV -T4 -p- -oX "$LOG_DIR/nmap.xml" "$TARGET" > /dev/null 2>&1) &
PID_NMAP=$!

(nuclei -u "$NUCLEI_TARGET" -j -o "$LOG_DIR/nuclei.json" > /dev/null 2>&1) &
PID_NUCLEI=$!

spinner

# 2. Run SearchSploit
echo -e "${YELLOW}[>] Mapping Exploits...${NC}"
searchsploit --nmap "$LOG_DIR/nmap.xml" --json > "$LOG_DIR/exploits_raw.json" 2>/dev/null
echo -e "${GREEN}[✔] Exploit Mapping Complete!${NC}"

# 3. Robust Normalization
echo -e "${YELLOW}[>] Normalizing data into final.json for AI...${NC}"

python3 <<EOF
import json
import xml.etree.ElementTree as ET
import os

final = {"target": "$TARGET", "findings": []}

# --- Step 1: Nmap XML ---
if os.path.exists("$LOG_DIR/nmap.xml"):
    try:
        tree = ET.parse("$LOG_DIR/nmap.xml")
        for port in tree.findall(".//port"):
            state = port.find("state")
            if state is not None and state.get("state") == "open":
                srv = port.find("service")
                final["findings"].append({
                    "port": port.get("portid"),
                    "service": srv.get("name") if srv is not None else "unknown",
                    "version": srv.get("version", "unknown") if srv is not None else "unknown",
                    "exploits": [],
                    "nuclei": []
                })
    except Exception as e:
        print(f"Nmap Error: {e}")

# --- Step 2: Nuclei JSONL ---
if os.path.exists("$LOG_DIR/nuclei.json"):
    with open("$LOG_DIR/nuclei.json", "r") as f:
        for line in f:
            try:
                data = json.loads(line)
                for fnd in final["findings"]:
                    if str(data.get("port")) == fnd["port"]:
                        fnd["nuclei"].append(
                            data.get("info", {}).get("name", "Unknown")
                        )
            except:
                continue

# --- Step 3: SearchSploit Robust Parsing ---
if os.path.exists("$LOG_DIR/exploits_raw.json"):
    with open("$LOG_DIR/exploits_raw.json", "r") as f:
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

if [ -f "final.json" ]; then
    echo -e "${MAGENTA}======================================================${NC}"
    echo -e "${GREEN}SUCCESS: final.json created! ($(du -h final.json | cut -f1))${NC}"
    echo -e "${CYAN}Final JSON ready for AI analysis.${NC}"
else
    echo -e "${RED}FAILED to create final.json${NC}"
fi

