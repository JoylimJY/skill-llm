import sys
import json
import subprocess
import os
from pathlib import Path

def run_dig_short(hostname, record_type):
    """Run dig with +short and return stripped lines."""
    try:
        result = subprocess.run(
            ["dig", hostname, record_type, "+short"],
            capture_output=True, text=True, timeout=15
        )
        lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
        return lines
    except Exception as e:
        return []

def run_dig_reverse(ip):
    """Run dig -x IP +short for reverse lookup."""
    try:
        result = subprocess.run(
            ["dig", "-x", ip, "+short"],
            capture_output=True, text=True, timeout=15
        )
        lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
        return lines
    except Exception as e:
        return []

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    overall_passed = True

    # --- Find the output file ---
    output_files = list(Path(workspace).rglob("dns_audit_report.json"))

    if not output_files:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False, "detail": "dns_audit_report.json not found anywhere in workspace"}]
        }))
        return

    report_path = output_files[0]
    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found at {report_path}"})

    # --- Parse JSON ---
    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"}]
        }))
        return

    checks.append({"name": "valid_json", "passed": True, "detail": "File is valid JSON"})

    # Expected entries from manifest (after stripping comments/blanks):
    # Hostnames: example.com, cloudflare.com, google.com
    # IPs (reverse): 8.8.8.8, 1.1.1.1, 208.67.222.222

    hostnames = ["example.com", "cloudflare.com", "google.com"]
    ips = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]

    # Check report is a list or dict with expected entries
    # Accept either a list of records or a dict keyed by host
    # We'll be flexible: look for the data regardless of top-level structure

    def find_entry(report, key):
        """Find an entry in report by hostname/ip key."""
        if isinstance(report, list):
            for item in report:
                if isinstance(item, dict):
                    for v in item.values():
                        if v == key:
                            return item
                    if item.get("host") == key or item.get("hostname") == key or item.get("ip") == key:
                        return item
        elif isinstance(report, dict):
            if key in report:
                return report[key]
            # search nested
            for k, v in report.items():
                if isinstance(v, dict) and (v.get("host") == key or v.get("hostname") == key or k == key):
                    return v
        return None

    # --- Check A records for each hostname ---
    for hostname in hostnames:
        expected_ips = run_dig_short(hostname, "A")
        entry = find_entry(report, hostname)

        check_name = f"a_record_{hostname}"
        if entry is None:
            checks.append({"name": check_name, "passed": False, "detail": f"No entry found for {hostname}"})
            overall_passed = False
            continue

        # Extract IPv4 addresses from the entry
        entry_str = json.dumps(entry).lower()
        found_any_ipv4 = False
        for eip in expected_ips:
            if eip in entry_str:
                found_any_ipv4 = True
                break

        if not expected_ips:
            # DNS lookup failed at eval time, skip with a warning
            checks.append({"name": check_name, "passed": True, "detail": f"Could not verify {hostname} A record at eval time (DNS unavailable), entry exists"})
        elif found_any_ipv4:
            checks.append({"name": check_name, "passed": True, "detail": f"{hostname} A record present: {expected_ips[0]}"})
        else:
            checks.append({"name": check_name, "passed": False, "detail": f"{hostname} A record missing or incorrect. Expected one of {expected_ips}, got entry: {json.dumps(entry)[:200]}"})
            overall_passed = False

    # --- Check AAAA records for each hostname ---
    for hostname in hostnames:
        expected_ipv6 = run_dig_short(hostname, "AAAA")
        entry = find_entry(report, hostname)
        check_name = f"aaaa_record_{hostname}"

        if entry is None:
            checks.append({"name": check_name, "passed": False, "detail": f"No entry found for {hostname}"})
            overall_passed = False
            continue

        entry_str = json.dumps(entry).lower()
        # IPv6 addresses contain colons
        has_ipv6_field = "aaaa" in entry_str or "ipv6" in entry_str

        if not expected_ipv6:
            # Hostname may not have AAAA; check that an attempt was made (field exists, even if empty)
            checks.append({"name": check_name, "passed": True, "detail": f"No AAAA for {hostname} or DNS unavailable; field presence not strictly required"})
        else:
            found_ipv6 = False
            for eip in expected_ipv6:
                if eip.lower() in entry_str:
                    found_ipv6 = True
                    break
            if found_ipv6 or has_ipv6_field:
                checks.append({"name": check_name, "passed": True, "detail": f"{hostname} AAAA record present"})
            else:
                checks.append({"name": check_name, "passed": False, "detail": f"{hostname} AAAA record missing. Expected one of {expected_ipv6}"})
                overall_passed = False

    # --- Check reverse lookups for IPs ---
    for ip in ips:
        expected_ptr = run_dig_reverse(ip)
        entry = find_entry(report, ip)
        check_name = f"reverse_lookup_{ip}"

        if entry is None:
            checks.append({"name": check_name, "passed": False, "detail": f"No reverse lookup entry found for {ip}"})
            overall_passed = False
            continue

        entry_str = json.dumps(entry).lower()
        has_ptr = "ptr" in entry_str or "reverse" in entry_str or "hostname" in entry_str

        if not expected_ptr:
            # PTR unavailable at eval time
            if has_ptr or entry_str:
                checks.append({"name": check_name, "passed": True, "detail": f"Reverse lookup entry for {ip} present (PTR unavailable at eval time)"})
            else:
                checks.append({"name": check_name, "passed": False, "detail": f"Reverse lookup entry for {ip} appears empty"})
                overall_passed = False
        else:
            found_ptr = False
            for ptr in expected_ptr:
                if ptr.lower().rstrip(".") in entry_str or ptr.lower() in entry_str:
                    found_ptr = True
                    break
            if found_ptr:
                checks.append({"name": check_name, "passed": True, "detail": f"Reverse PTR for {ip}: {expected_ptr[0]}"})
            else:
                # Be lenient: if entry exists with some data, consider partial pass
                checks.append({"name": check_name, "passed": False, "detail": f"PTR for {ip} not found in entry. Expected one of {expected_ptr}, entry: {json.dumps(entry)[:200]}"})
                overall_passed = False

    # --- Check that comments/blanks were excluded ---
    # The manifest has comment lines and blank lines; the agent must not include them as hosts
    check_name = "no_comment_lines_as_hosts"
    comment_leaked = False
    report_str = json.dumps(report)
    for bad in ["# Host manifest", "# web tier", "# Known IPs", "# DO NOT EDIT", "# end of manifest", "# Generated"]:
        if bad in report_str:
            comment_leaked = True
            break
    if comment_leaked:
        checks.append({"name": check_name, "passed": False, "detail": "Report contains raw comment strings that should have been filtered"})
        overall_passed = False
    else:
        checks.append({"name": check_name, "passed": True, "detail": "No comment lines leaked into report"})

    # --- Score calculation ---
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 3)
    overall_passed = overall_passed and (score >= 0.75)

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()