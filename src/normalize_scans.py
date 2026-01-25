#!/usr/bin/env python3
"""
Scanner Output Normalization
Extracts and consolidates findings from multiple scanner tools
"""

import json
import xml.etree.ElementTree as ET
import os
import re
from pathlib import Path
from config import CONFIG


def normalize_whatweb(scan_results_dir):
    """Extract technology stack from WhatWeb JSON output"""
    tech_stack = []
    whatweb_file = Path(scan_results_dir) / "whatweb.json"
    
    if not whatweb_file.exists():
        return tech_stack
    
    try:
        with open(whatweb_file, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    tech_stack.extend(list(data.get("plugins", {}).keys()))
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"⚠️  WhatWeb parsing error: {e}")
    
    return list(set(tech_stack))  # deduplicate


def normalize_nikto(scan_results_dir):
    """Extract findings from Nikto text output"""
    findings = []
    nikto_file = Path(scan_results_dir) / "nikto.txt"
    
    if not nikto_file.exists():
        return findings
    
    try:
        with open(nikto_file, "r") as f:
            content = f.read()
            # Parse Nikto findings (pattern: + description)
            for match in re.finditer(r"^\+\s+(.+)$", content, re.MULTILINE):
                finding = match.group(1).strip()
                if finding:
                    findings.append(finding)
    except Exception as e:
        print(f"⚠️  Nikto parsing error: {e}")
    
    return findings


def normalize_nmap(scan_results_dir):
    """Extract ports and services from Nmap XML output"""
    services = []
    nmap_file = Path(scan_results_dir) / "nmap.xml"
    
    if not nmap_file.exists():
        return services
    
    try:
        tree = ET.parse(nmap_file)
        root = tree.getroot()
        
        for host in root.findall(".//host"):
            for port in host.findall(".//port"):
                port_num = port.get("portid")
                protocol = port.get("protocol")
                
                service_elem = port.find("service")
                service_name = ""
                version = ""
                
                if service_elem is not None:
                    service_name = service_elem.get("name", "")
                    version = service_elem.get("product", "")
                
                state = port.find("state").get("state")
                
                if state == "open":
                    services.append({
                        "port": port_num,
                        "protocol": protocol,
                        "service": service_name,
                        "version": version,
                        "state": state
                    })
    except Exception as e:
        print(f"⚠️  Nmap parsing error: {e}")
    
    return services


def normalize_nuclei(scan_results_dir):
    """Extract vulnerabilities from Nuclei JSON output"""
    vulnerabilities = []
    nuclei_file = Path(scan_results_dir) / "nuclei.json"
    
    if not nuclei_file.exists():
        return vulnerabilities
    
    try:
        with open(nuclei_file, "r") as f:
            for line in f:
                try:
                    finding = json.loads(line)
                    info = finding.get("info", {})
                    # Safely handle info field (could be dict or string)
                    if isinstance(info, dict):
                        severity = info.get("severity", "info").lower()
                        title = info.get("name", "")
                        description = info.get("description", "")
                    else:
                        severity = "info"
                        title = ""
                        description = ""
                    
                    vulnerabilities.append({
                        "template": finding.get("template", ""),
                        "type": finding.get("type", ""),
                        "severity": severity,
                        "title": title,
                        "description": description,
                        "url": finding.get("matched_at", ""),
                        "raw": finding
                    })
                except (json.JSONDecodeError, AttributeError):
                    continue
    except Exception as e:
        print(f"⚠️  Nuclei parsing error: {e}")
    
    return vulnerabilities


def normalize_searchsploit(scan_results_dir):
    """Extract exploits from SearchSploit JSON output (JSONL format)"""
    exploits = []
    exploits_file = Path(scan_results_dir) / "exploits_raw.json"
    
    if not exploits_file.exists():
        return exploits
    
    try:
        with open(exploits_file, "r") as f:
            for line in f:
                try:
                    # Handle both JSON objects and JSON arrays in the file
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    
                    # Extract from different possible structures
                    results = data.get("RESULTS_EXPLOIT", []) or data.get("RESULTS", [])
                    
                    for result in results:
                        exploits.append({
                            "title": result.get("Title", ""),
                            "path": result.get("Path", ""),
                            "type": result.get("Type", ""),
                            "exploit_code": result.get("Exploit Code", ""),
                            "cve": result.get("CVE", result.get("Codes", ""))
                        })
                except (json.JSONDecodeError, AttributeError, TypeError):
                    continue
    except Exception as e:
        print(f"⚠️  SearchSploit parsing error: {e}")
    
    return exploits


def merge_findings(services, nuclei_findings, exploits):
    """Merge Nmap services with Nuclei and SearchSploit findings"""
    merged = []
    
    for service in services:
        port = service.get("port")
        service_name = service.get("service")
        version = service.get("version")
        
        # Find relevant Nuclei findings
        nuclei_for_service = [
            n for n in nuclei_findings
            if str(port) in n.get("url", "") or service_name.lower() in n.get("template", "").lower()
        ]
        
        # Find relevant exploits
        exploits_for_service = [
            e for e in exploits
            if version and version.lower() in e.get("title", "").lower()
        ]
        
        merged.append({
            "port": port,
            "service": service_name,
            "version": version,
            "nuclei": [n["title"] for n in nuclei_for_service],
            "exploits": [e["title"] for e in exploits_for_service],
            "raw_nuclei": nuclei_for_service,
            "raw_exploits": exploits_for_service
        })
    
    return merged


def normalize_scans(target, scan_results_dir=None):
    """Main normalization function"""
    
    if scan_results_dir is None:
        scan_results_dir = CONFIG["scanner"]["results_dir"]
    
    print(f"📊 Normalizing scan results from {scan_results_dir}...")
    
    try:
        tech_stack = normalize_whatweb(scan_results_dir)
        nikto_findings = normalize_nikto(scan_results_dir)
        services = normalize_nmap(scan_results_dir)
        nuclei_findings = normalize_nuclei(scan_results_dir)
        exploits = normalize_searchsploit(scan_results_dir)
        
        findings = merge_findings(services, nuclei_findings, exploits)
        
        final_output = {
            "target": target,
            "tech_stack": tech_stack,
            "nikto_findings": nikto_findings,
            "findings": findings,
            "summary": {
                "total_services": len(services),
                "total_vulnerabilities": len(nuclei_findings),
                "total_exploits": len(exploits)
            }
        }
        
        return final_output
        
    except Exception as e:
        print(f"❌ Normalization failed: {e}")
        raise


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 normalize_scans.py <target>")
        sys.exit(1)
    
    target = sys.argv[1]
    result = normalize_scans(target)
    
    output_path = Path(CONFIG["scanner"]["results_dir"]) / "final.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"✅ Normalized output: {output_path}")
