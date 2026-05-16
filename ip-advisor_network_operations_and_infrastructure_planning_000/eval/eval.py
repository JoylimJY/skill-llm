import sys
import json
import re
from pathlib import Path

def find_report(workspace):
    """Search for network_audit.json anywhere in the workspace."""
    results = list(Path(workspace).rglob("network_audit.json"))
    return results[0] if results else None

def run_checks(workspace):
    checks = []
    overall_passed = True

    # --- Check 1: File exists ---
    report_path = find_report(workspace)
    file_exists = report_path is not None
    checks.append({
        "name": "network_audit.json exists",
        "passed": file_exists,
        "detail": f"Found at {report_path}" if file_exists else "File network_audit.json not found anywhere in workspace"
    })
    if not file_exists:
        overall_passed = False
        return checks, overall_passed

    # --- Parse JSON ---
    try:
        with open(report_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        checks.append({"name": "JSON parseable", "passed": False, "detail": str(e)})
        overall_passed = False
        return checks, overall_passed

    checks.append({"name": "JSON parseable", "passed": True, "detail": "File is valid JSON"})

    # --- Check 2: Valid IPs section ---
    # Expected valid IPs from the candidate list (must have run `validate` on each):
    # Valid: 10.0.1.5, 10.0.1.6, 10.0.1.15, 10.0.1.16, 10.0.1.20, 10.0.1.1, 10.0.1.50, 10.0.1.55, 10.0.1.88, 10.0.1.89, 10.0.1.100
    # Invalid: 10.0.1.300, 999.1.1.1, 10.0.1.abc, 10.0.1.-1
    EXPECTED_VALID = {
        "10.0.1.5", "10.0.1.6", "10.0.1.15", "10.0.1.16", "10.0.1.20",
        "10.0.1.1", "10.0.1.50", "10.0.1.55", "10.0.1.88", "10.0.1.89", "10.0.1.100"
    }
    EXPECTED_INVALID = {"10.0.1.300", "999.1.1.1", "10.0.1.abc", "10.0.1.-1"}

    # Find all IPs in the data structure (searching recursively)
    data_str = json.dumps(data)

    # Try to find valid_ips key or similar
    valid_ips_found = set()
    invalid_ips_found = set()

    def collect_ips_from_obj(obj, key_hint=""):
        nonlocal valid_ips_found, invalid_ips_found
        if isinstance(obj, dict):
            for k, v in obj.items():
                k_lower = k.lower()
                if "valid" in k_lower and "invalid" not in k_lower:
                    if isinstance(v, list):
                        for item in v:
                            if isinstance(item, str) and re.match(r'^\d+\.\d+\.\d+\.\d+$', item.strip()):
                                valid_ips_found.add(item.strip())
                            elif isinstance(item, dict):
                                ip_val = item.get("ip") or item.get("address") or item.get("candidate_ip")
                                if ip_val and re.match(r'^\S+$', str(ip_val)):
                                    valid_ips_found.add(str(ip_val).strip())
                elif "invalid" in k_lower:
                    if isinstance(v, list):
                        for item in v:
                            if isinstance(item, str):
                                invalid_ips_found.add(item.strip())
                            elif isinstance(item, dict):
                                ip_val = item.get("ip") or item.get("address") or item.get("candidate_ip")
                                if ip_val:
                                    invalid_ips_found.add(str(ip_val).strip())
                collect_ips_from_obj(v, k)
        elif isinstance(obj, list):
            for item in obj:
                collect_ips_from_obj(item, key_hint)

    collect_ips_from_obj(data)

    # Check valid IPs correctness
    correct_valid = EXPECTED_VALID.issubset(valid_ips_found)
    no_invalid_in_valid = len(EXPECTED_INVALID.intersection(valid_ips_found)) == 0

    checks.append({
        "name": "Valid IPs correctly identified (11 IPs)",
        "passed": correct_valid,
        "detail": f"Expected {sorted(EXPECTED_VALID)}, found {sorted(valid_ips_found)}. Missing: {sorted(EXPECTED_VALID - valid_ips_found)}"
    })
    if not correct_valid:
        overall_passed = False

    checks.append({
        "name": "Invalid IPs not included in valid list",
        "passed": no_invalid_in_valid,
        "detail": f"Invalid IPs that should be excluded from valid list: {sorted(EXPECTED_INVALID.intersection(valid_ips_found))}"
    })
    if not no_invalid_in_valid:
        overall_passed = False

    # --- Check 3: Subnet info for 10.0.1.0/24 ---
    # Expected subnet details:
    EXPECTED_SUBNET = {
        "network": "10.0.1.0",
        "broadcast": "10.0.1.255",
        "netmask": "255.255.255.0",
        "prefix": 24,
        "total_hosts": 256,
        "usable_hosts": 254,
        "first_host": "10.0.1.1",
        "last_host": "10.0.1.254",
    }

    subnet_checks_passed = []
    for key, expected_val in EXPECTED_SUBNET.items():
        found = re.search(re.escape(str(expected_val)), data_str)
        subnet_checks_passed.append((key, found is not None, str(expected_val)))

    subnet_ok = all(ok for _, ok, _ in subnet_checks_passed)
    missing_fields = [k for k, ok, _ in subnet_checks_passed if not ok]
    checks.append({
        "name": "Subnet details for 10.0.1.0/24 present",
        "passed": subnet_ok,
        "detail": f"All subnet fields correct" if subnet_ok else f"Missing/incorrect fields: {missing_fields}"
    })
    if not subnet_ok:
        overall_passed = False

    # --- Check 4: Range enumeration (10.0.1.1 to 10.0.1.100) ---
    # Must contain 100 IPs from 10.0.1.1 to 10.0.1.100 (inclusive = 100 IPs)
    range_ips_found = set()

    def collect_range_ips(obj):
        if isinstance(obj, dict):
            # Check if this dict looks like range output
            if "ips" in obj and isinstance(obj["ips"], list):
                for ip in obj["ips"]:
                    if isinstance(ip, str):
                        range_ips_found.add(ip.strip())
            if "range" in str(obj.keys()).lower() or "start" in obj or "end" in obj:
                for v in obj.values():
                    collect_range_ips(v)
            else:
                for v in obj.values():
                    collect_range_ips(v)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, str) and re.match(r'^10\.0\.1\.\d+$', item.strip()):
                    range_ips_found.add(item.strip())
                elif isinstance(item, dict):
                    collect_range_ips(item)

    collect_range_ips(data)

    # Expected: 10.0.1.1 through 10.0.1.100 = 100 IPs
    EXPECTED_RANGE = {f"10.0.1.{i}" for i in range(1, 101)}

    range_correct = EXPECTED_RANGE.issubset(range_ips_found)
    range_count_ok = len(range_ips_found) >= 100

    checks.append({
        "name": "Range 10.0.1.1 to 10.0.1.100 enumerated (100 IPs)",
        "passed": range_correct,
        "detail": f"Expected 100 IPs in range. Found {len(range_ips_found & EXPECTED_RANGE)} matching IPs. Missing: {sorted(EXPECTED_RANGE - range_ips_found)[:5]}..." if not range_correct else "All 100 range IPs present"
    })
    if not range_correct:
        overall_passed = False

    # --- Check 5: Report uses data from all three commands ---
    # Heuristic: must have subnet key, validation keys, and range keys
    has_subnet_key = any(k in data_str.lower() for k in ["subnet", "network", "netmask", "cidr"])
    has_validation_key = any(k in data_str.lower() for k in ["valid", "validation", "validated"])
    has_range_key = any(k in data_str.lower() for k in ["range", "ips", "enumerat"])

    multi_cmd_check = has_subnet_key and has_validation_key and has_range_key
    checks.append({
        "name": "Report consolidates subnet, validation, and range data",
        "passed": multi_cmd_check,
        "detail": f"subnet={has_subnet_key}, validation={has_validation_key}, range={has_range_key}"
    })
    if not multi_cmd_check:
        overall_passed = False

    return checks, overall_passed


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks, passed = run_checks(workspace)
    except Exception as e:
        checks = [{"name": "eval_crash", "passed": False, "detail": str(e)}]
        passed = False

    score = sum(1 for c in checks if c["passed"]) / len(checks) if checks else 0.0

    result = {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()