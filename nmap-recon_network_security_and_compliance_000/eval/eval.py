import sys
import json
import re
import os
import glob
from pathlib import Path

def find_files_by_pattern(workspace, pattern):
    """Find files matching a glob pattern recursively."""
    return list(Path(workspace).rglob(pattern))

def check_oA_output_triple(workspace, prefix_pattern):
    """Check that all three -oA output files exist for a given prefix pattern."""
    nmap_files = find_files_by_pattern(workspace, f"{prefix_pattern}*.nmap")
    xml_files = find_files_by_pattern(workspace, f"{prefix_pattern}*.xml")
    gnmap_files = find_files_by_pattern(workspace, f"{prefix_pattern}*.gnmap")
    return nmap_files, xml_files, gnmap_files

def parse_gnmap_open_ports(gnmap_path):
    """Parse open ports from a .gnmap file using skill's logic."""
    ports = set()
    try:
        content = Path(gnmap_path).read_text()
        for line in content.splitlines():
            if "open" in line and "Ports:" in line:
                # Extract port numbers from entries like: 22/open/tcp//ssh///,
                matches = re.findall(r'(\d+)/open/', line)
                for m in matches:
                    ports.add(int(m))
    except Exception as e:
        pass
    return ports

def parse_xml_open_ports(xml_path):
    """Parse open ports from nmap XML output."""
    ports = set()
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for port_elem in root.iter('port'):
            state_elem = port_elem.find('state')
            if state_elem is not None and state_elem.get('state') == 'open':
                ports.add(int(port_elem.get('portid')))
    except Exception as e:
        pass
    return ports

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    total_score = 0.0
    max_score = 7

    # ----------------------------------------------------------------
    # CHECK 1: Service detection scan (-sC -sV or -sV) with -oA exists
    # Must have .nmap + .xml + .gnmap triple from a standard/service scan
    # ----------------------------------------------------------------
    service_scan_nmap = find_files_by_pattern(workspace, "*.nmap")
    # Filter out vuln scan files to find service scan
    service_nmap_files = [f for f in service_scan_nmap 
                          if not any(x in f.name.lower() for x in ['vuln', 'vuln_scan', 'vulnscan'])]
    
    has_service_triple = False
    service_nmap_path = None
    service_xml_path = None
    service_gnmap_path = None

    for nmap_f in service_nmap_files:
        stem = nmap_f.stem
        parent = nmap_f.parent
        xml_candidate = parent / f"{stem}.xml"
        gnmap_candidate = parent / f"{stem}.gnmap"
        if xml_candidate.exists() and gnmap_candidate.exists():
            has_service_triple = True
            service_nmap_path = nmap_f
            service_xml_path = xml_candidate
            service_gnmap_path = gnmap_candidate
            break

    checks.append({
        "name": "service_scan_oA_triple_exists",
        "passed": has_service_triple,
        "detail": f"Found service scan triple (.nmap/.xml/.gnmap): {service_nmap_path}" if has_service_triple 
                  else "No complete -oA output triple found for service detection scan"
    })
    if has_service_triple:
        total_score += 1

    # ----------------------------------------------------------------
    # CHECK 2: Service scan actually targeted 127.0.0.1 / localhost
    # ----------------------------------------------------------------
    target_correct = False
    if service_nmap_path:
        try:
            content = service_nmap_path.read_text()
            if re.search(r'(127\.0\.0\.1|localhost)', content, re.IGNORECASE):
                target_correct = True
        except Exception as e:
            pass

    checks.append({
        "name": "service_scan_targets_localhost",
        "passed": target_correct,
        "detail": "Service scan .nmap file references 127.0.0.1 or localhost as target" if target_correct
                  else "Could not confirm scan targeted 127.0.0.1/localhost"
    })
    if target_correct:
        total_score += 1

    # ----------------------------------------------------------------
    # CHECK 3: Service scan detected at least 2 open ports
    # (We know SSH:22, HTTP:80, MySQL-like:3306, App:8080 are running)
    # ----------------------------------------------------------------
    detected_ports = set()
    if service_gnmap_path:
        detected_ports = parse_gnmap_open_ports(service_gnmap_path)
    if not detected_ports and service_xml_path:
        detected_ports = parse_xml_open_ports(service_xml_path)

    enough_ports = len(detected_ports) >= 2
    checks.append({
        "name": "service_scan_found_open_ports",
        "passed": enough_ports,
        "detail": f"Detected open ports: {sorted(detected_ports)}" if detected_ports
                  else "No open ports detected in scan output"
    })
    if enough_ports:
        total_score += 1

    # ----------------------------------------------------------------
    # CHECK 4: Vulnerability scan output exists as -oA triple
    # Must have prefix containing 'vuln' and all three formats
    # ----------------------------------------------------------------
    vuln_nmap_files = [f for f in find_files_by_pattern(workspace, "*.nmap")
                       if any(x in f.name.lower() for x in ['vuln', 'vuln_scan', 'vulnscan'])]
    
    has_vuln_triple = False
    vuln_nmap_path = None

    for nmap_f in vuln_nmap_files:
        stem = nmap_f.stem
        parent = nmap_f.parent
        xml_candidate = parent / f"{stem}.xml"
        gnmap_candidate = parent / f"{stem}.gnmap"
        if xml_candidate.exists() and gnmap_candidate.exists():
            has_vuln_triple = True
            vuln_nmap_path = nmap_f
            break

    checks.append({
        "name": "vuln_scan_oA_triple_exists",
        "passed": has_vuln_triple,
        "detail": f"Found vuln scan triple: {vuln_nmap_path}" if has_vuln_triple
                  else "No vulnerability scan -oA output triple found (need vulnscan_*.nmap/xml/gnmap)"
    })
    if has_vuln_triple:
        total_score += 1

    # ----------------------------------------------------------------
    # CHECK 5: Vulnerability scan used --script vuln (check nmap file header)
    # ----------------------------------------------------------------
    vuln_script_used = False
    if vuln_nmap_path:
        try:
            content = vuln_nmap_path.read_text()
            # Nmap embeds the command line in the .nmap file
            if re.search(r'--script[= ]+(vuln|"vuln")', content, re.IGNORECASE) or \
               re.search(r'script.*vuln', content[:500], re.IGNORECASE):
                vuln_script_used = True
        except Exception:
            pass
    
    checks.append({
        "name": "vuln_scan_used_script_vuln",
        "passed": vuln_script_used,
        "detail": "Vulnerability scan .nmap header confirms --script vuln was used" if vuln_script_used
                  else "Could not confirm --script vuln was used in vulnerability scan"
    })
    if vuln_script_used:
        total_score += 1

    # ----------------------------------------------------------------
    # CHECK 6: recon_summary.json exists and has required structure
    # ----------------------------------------------------------------
    summary_files = find_files_by_pattern(workspace, "recon_summary.json")
    summary_valid = False
    summary_detail = "recon_summary.json not found"
    
    if summary_files:
        try:
            summary_path = summary_files[0]
            content = summary_path.read_text()
            data = json.loads(content)
            
            # Must contain open_ports list and target info
            has_open_ports = isinstance(data.get("open_ports"), list) and len(data.get("open_ports", [])) >= 2
            has_target = any(
                str(v) in ("127.0.0.1", "localhost") 
                for v in [data.get("target"), data.get("host"), data.get("ip")]
                if v is not None
            ) or "127.0.0.1" in content or "localhost" in content.lower()
            
            # Must have services info (at minimum some service data)
            has_services = (
                isinstance(data.get("services"), (list, dict)) or
                isinstance(data.get("open_services"), (list, dict)) or
                any("service" in str(k).lower() for k in data.keys())
            )
            
            summary_valid = has_open_ports and has_target and has_services
            summary_detail = (
                f"recon_summary.json found at {summary_path}. "
                f"open_ports: {data.get('open_ports')}, "
                f"has_target: {has_target}, "
                f"has_services: {has_services}, "
                f"keys: {list(data.keys())}"
            )
        except json.JSONDecodeError as e:
            summary_detail = f"recon_summary.json found but invalid JSON: {e}"
        except Exception as e:
            summary_detail = f"Error reading recon_summary.json: {e}"

    checks.append({
        "name": "recon_summary_json_valid",
        "passed": summary_valid,
        "detail": summary_detail
    })
    if summary_valid:
        total_score += 1

    # ----------------------------------------------------------------
    # CHECK 7: recon_summary.json open_ports are consistent with scan output
    # (ports in summary should be a subset of detected ports, at least 2 match)
    # ----------------------------------------------------------------
    ports_consistent = False
    consistency_detail = "Cannot check consistency without valid summary or scan output"

    if summary_valid and detected_ports:
        try:
            summary_path = summary_files[0]
            data = json.loads(summary_path.read_text())
            summary_ports = set()
            raw_ports = data.get("open_ports", [])
            for p in raw_ports:
                try:
                    summary_ports.add(int(p))
                except (ValueError, TypeError):
                    pass
            
            overlap = summary_ports & detected_ports
            ports_consistent = len(overlap) >= 2
            consistency_detail = (
                f"Summary ports: {sorted(summary_ports)}, "
                f"Scan detected: {sorted(detected_ports)}, "
                f"Overlap: {sorted(overlap)}"
            )
        except Exception as e:
            consistency_detail = f"Error during consistency check: {e}"

    checks.append({
        "name": "summary_ports_consistent_with_scan",
        "passed": ports_consistent,
        "detail": consistency_detail
    })
    if ports_consistent:
        total_score += 1

    # ----------------------------------------------------------------
    # Final scoring
    # ----------------------------------------------------------------
    final_score = round(total_score / max_score, 4)
    passed = total_score >= 5  # Must pass at least 5/7 checks

    result = {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()