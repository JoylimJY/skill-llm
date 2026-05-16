import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    # ── 1. Find network_report.md ──────────────────────────────────────────
    candidates = list(workspace.rglob("network_report.md"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "network_report.md exists",
        "passed": file_found,
        "detail": f"Found at {candidates[0]}" if file_found else "File not found anywhere in workspace"
    })
    if not file_found:
        return {"passed": False, "score": 0.0, "checks": checks}

    try:
        content = candidates[0].read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── 2. Markdown table structure ────────────────────────────────────────
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    table_lines = [l for l in lines if l.startswith("|")]

    has_header = any(
        re.search(r'IP\s*(地址)?', l, re.IGNORECASE) and
        re.search(r'MAC', l, re.IGNORECASE) and
        re.search(r'(开放)?端口|port', l, re.IGNORECASE) and
        re.search(r'设备类型|device', l, re.IGNORECASE)
        for l in table_lines
    )
    checks.append({
        "name": "table_header_correct",
        "passed": has_header,
        "detail": f"Header row with IP/MAC/Port/Device columns {'found' if has_header else 'NOT found'}. Table lines: {table_lines[:3]}"
    })

    separator_lines = [l for l in table_lines if re.match(r'^\|[-| :]+\|$', l)]
    has_separator = len(separator_lines) >= 1
    checks.append({
        "name": "table_has_separator_row",
        "passed": has_separator,
        "detail": f"Separator row {'found' if has_separator else 'NOT found'}"
    })

    data_rows = [l for l in table_lines if l not in [table_lines[0]] and not re.match(r'^\|[-| :]+\|$', l)]

    has_five_rows = len(data_rows) >= 5
    checks.append({
        "name": "table_has_5_data_rows",
        "passed": has_five_rows,
        "detail": f"Found {len(data_rows)} data rows (expected 5)"
    })

    # ── 3. All 5 IPs present ──────────────────────────────────────────────
    expected_ips = ["192.168.1.1", "192.168.1.42", "192.168.1.77", "192.168.1.112", "192.168.1.200"]
    ips_found = []
    for ip in expected_ips:
        found = ip in content
        ips_found.append(found)
    all_ips_present = all(ips_found)
    checks.append({
        "name": "all_5_ips_present",
        "passed": all_ips_present,
        "detail": f"IPs found: {[ip for ip, ok in zip(expected_ips, ips_found) if ok]}, missing: {[ip for ip, ok in zip(expected_ips, ips_found) if not ok]}"
    })

    # ── 4. MAC addresses present (normalized with dashes or colons) ────────
    expected_macs_raw = [
        "e4:68:a3:11:22:33",
        "94:e6:f7:aa:bb:cc",
        "40:31:3c:de:ad:01",
        "30:9c:23:ff:ee:dd",
        "b8:27:eb:55:44:33"
    ]
    def normalize_mac(mac):
        return mac.lower().replace(":", "-").replace(" ", "")

    content_lower = content.lower()
    macs_found = []
    for mac in expected_macs_raw:
        colon_form = mac.lower()
        dash_form = normalize_mac(mac)
        found = colon_form in content_lower or dash_form in content_lower
        macs_found.append(found)
    all_macs_present = all(macs_found)
    checks.append({
        "name": "all_5_macs_present",
        "passed": all_macs_present,
        "detail": f"MACs found: {sum(macs_found)}/5. Missing: {[m for m, ok in zip(expected_macs_raw, macs_found) if not ok]}"
    })

    # ── 5. Proprietary device type: 小米路由器 for e4:68:a3 MAC ──────────
    # Row for 192.168.1.1 must contain 小米路由器
    row_gateway = [r for r in table_lines if "192.168.1.1" in r and "192.168.1.112" not in r]
    gateway_correct = False
    if row_gateway:
        row_text = row_gateway[0]
        # Must have 小米路由器 label (Xiaomi router)
        gateway_correct = "小米路由器" in row_text or ("xiaomi" in row_text.lower() and "路由" in row_text)
    checks.append({
        "name": "device_type_xiaomi_router_192.168.1.1",
        "passed": gateway_correct,
        "detail": f"192.168.1.1 row: {'小米路由器 found' if gateway_correct else 'missing 小米路由器 label'}. Row: {row_gateway[0] if row_gateway else 'NOT FOUND'}"
    })

    # ── 6. Proprietary: 小米设备 for 40:31:3c MAC (192.168.1.77) ─────────
    row_77 = [r for r in table_lines if "192.168.1.77" in r]
    xiaomi_iot_correct = False
    if row_77:
        row_text = row_77[0]
        xiaomi_iot_correct = "小米设备" in row_text or ("xiaomi" in row_text.lower() and ("iot" in row_text.lower() or "设备" in row_text))
    checks.append({
        "name": "device_type_xiaomi_iot_192.168.1.77",
        "passed": xiaomi_iot_correct,
        "detail": f"192.168.1.77 row: {'小米设备 found' if xiaomi_iot_correct else 'missing 小米设备 label'}. Row: {row_77[0] if row_77 else 'NOT FOUND'}"
    })

    # ── 7. Proprietary: Windows电脑 for ports 135,139,445 (192.168.1.112) ─
    row_112 = [r for r in table_lines if "192.168.1.112" in r]
    windows_correct = False
    if row_112:
        row_text = row_112[0]
        windows_correct = "Windows" in row_text and ("电脑" in row_text or "SMB" in row_text)
    checks.append({
        "name": "device_type_windows_192.168.1.112",
        "passed": windows_correct,
        "detail": f"192.168.1.112 row: {'Windows电脑 found' if windows_correct else 'missing Windows电脑 label'}. Row: {row_112[0] if row_112 else 'NOT FOUND'}"
    })

    # ── 8. Linux server for 22+80 ports (192.168.1.42 and/or 192.168.1.200) 
    row_42 = [r for r in table_lines if "192.168.1.42" in r]
    linux_correct = False
    if row_42:
        row_text = row_42[0]
        linux_correct = "Linux" in row_text or "linux" in row_text.lower()
    checks.append({
        "name": "device_type_linux_server_192.168.1.42",
        "passed": linux_correct,
        "detail": f"192.168.1.42 row: {'Linux found' if linux_correct else 'missing Linux label'}. Row: {row_42[0] if row_42 else 'NOT FOUND'}"
    })

    # ── 9. Ports present in rows ──────────────────────────────────────────
    port_checks = [
        ("192.168.1.1", ["80", "443", "23"]),
        ("192.168.1.112", ["135", "139", "445"]),
        ("192.168.1.77", ["8080", "8443"]),
    ]
    ports_correct = True
    port_details = []
    for ip, ports in port_checks:
        row = [r for r in table_lines if ip in r and "192.168.1.112" not in r or (ip == "192.168.1.112" and ip in r)]
        # Simplified: just search in entire content
        for port in ports:
            # Find the row for this IP and check the port is there
            ip_rows = [r for r in table_lines if ip in r]
            if ip_rows:
                port_in_row = port in ip_rows[0]
                if not port_in_row:
                    ports_correct = False
                port_details.append(f"{ip}:{port}={'OK' if port_in_row else 'MISSING'}")
    checks.append({
        "name": "open_ports_correct_in_rows",
        "passed": ports_correct,
        "detail": "; ".join(port_details) if port_details else "No port rows checked"
    })

    # ── Final score ────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)

    # Must pass critical checks to be "passed"
    critical = [
        "network_report.md exists",
        "table_header_correct",
        "all_5_ips_present",
        "device_type_xiaomi_router_192.168.1.1",
        "device_type_xiaomi_iot_192.168.1.77",
        "device_type_windows_192.168.1.112",
        "device_type_linux_server_192.168.1.42",
    ]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical)
    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))