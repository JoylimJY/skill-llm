import sys
import json
import os
import yaml
from pathlib import Path
import ipaddress

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    nmap_mcp_dir = workspace / "nmap-mcp"
    checks = []
    total_score = 0.0
    max_checks = 7

    def check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── CHECK 1: config.yaml has valid allowed_cidrs covering 127.x ─────────
    score = 0.0
    try:
        config_path = nmap_mcp_dir / "config.yaml"
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        cidrs = cfg.get("allowed_cidrs", [])
        loopback_covered = False
        for cidr in cidrs:
            try:
                net = ipaddress.ip_network(cidr, strict=False)
                if ipaddress.ip_address("127.0.0.1") in net:
                    loopback_covered = True
                    break
            except Exception:
                pass
        if loopback_covered and len(cidrs) >= 1:
            score += check("config_allowed_cidrs_loopback",
                           True, f"allowed_cidrs covers 127.0.0.1: {cidrs}")
        else:
            score += check("config_allowed_cidrs_loopback",
                           False, f"allowed_cidrs does not cover 127.0.0.1. Got: {cidrs}")
    except Exception as e:
        score += check("config_allowed_cidrs_loopback", False, f"Error reading config.yaml: {e}")

    # ── CHECK 2: config.yaml has valid scan_dir that actually exists ─────────
    try:
        config_path = nmap_mcp_dir / "config.yaml"
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        scan_dir_raw = cfg.get("scan_dir", "")
        # Resolve relative to nmap_mcp_dir if relative
        if scan_dir_raw.startswith("/"):
            scan_dir = Path(scan_dir_raw)
        else:
            scan_dir = (nmap_mcp_dir / scan_dir_raw).resolve()
        if scan_dir.exists() and scan_dir.is_dir():
            score += check("config_scan_dir_exists", True,
                           f"scan_dir exists: {scan_dir}")
        else:
            score += check("config_scan_dir_exists", False,
                           f"scan_dir does not exist: {scan_dir}")
    except Exception as e:
        score += check("config_scan_dir_exists", False, f"Error: {e}")

    # ── CHECK 3: config.yaml has valid audit_log path (parent dir exists) ────
    try:
        config_path = nmap_mcp_dir / "config.yaml"
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        audit_raw = cfg.get("audit_log", "")
        if audit_raw.startswith("/"):
            audit_path = Path(audit_raw)
        else:
            audit_path = (nmap_mcp_dir / audit_raw).resolve()
        # Either the file exists, or its parent dir exists
        if audit_path.exists() or audit_path.parent.exists():
            score += check("config_audit_log_valid", True,
                           f"audit_log parent exists: {audit_path}")
        else:
            score += check("config_audit_log_valid", False,
                           f"audit_log parent dir does not exist: {audit_path}")
    except Exception as e:
        score += check("config_audit_log_valid", False, f"Error: {e}")

    # ── CHECK 4: At least one scan JSON file was saved in scan_dir ───────────
    try:
        config_path = nmap_mcp_dir / "config.yaml"
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        scan_dir_raw = cfg.get("scan_dir", "")
        if scan_dir_raw.startswith("/"):
            scan_dir = Path(scan_dir_raw)
        else:
            scan_dir = (nmap_mcp_dir / scan_dir_raw).resolve()
        scan_files = list(scan_dir.glob("*.json")) if scan_dir.exists() else []
        if len(scan_files) >= 1:
            score += check("scan_file_persisted", True,
                           f"Found {len(scan_files)} scan file(s): {[f.name for f in scan_files]}")
        else:
            score += check("scan_file_persisted", False,
                           f"No JSON scan files found in scan_dir: {scan_dir}")
    except Exception as e:
        score += check("scan_file_persisted", False, f"Error: {e}")

    # ── CHECK 5: Audit log was written and contains a scan entry ────────────
    try:
        config_path = nmap_mcp_dir / "config.yaml"
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        audit_raw = cfg.get("audit_log", "")
        if audit_raw.startswith("/"):
            audit_path = Path(audit_raw)
        else:
            audit_path = (nmap_mcp_dir / audit_raw).resolve()
        if audit_path.exists() and audit_path.stat().st_size > 0:
            content = audit_path.read_text()
            # Should contain some evidence of a scan (target or tool name)
            if "127.0.0.1" in content or "nmap_tcp_scan" in content or "nmap_top_ports" in content or "nmap_service" in content or "scan" in content.lower():
                score += check("audit_log_written", True,
                               f"Audit log exists and contains scan evidence ({audit_path.stat().st_size} bytes)")
            else:
                score += check("audit_log_written", False,
                               f"Audit log exists but no scan evidence found. Content preview: {content[:200]}")
        else:
            score += check("audit_log_written", False,
                           f"Audit log not found or empty at: {audit_path}")
    except Exception as e:
        score += check("audit_log_written", False, f"Error: {e}")

    # ── CHECK 6: audit_report.json exists and has required fields ────────────
    try:
        report_files = list(workspace.rglob("audit_report.json"))
        if not report_files:
            score += check("audit_report_exists", False,
                           "audit_report.json not found anywhere in workspace")
        else:
            report_path = report_files[0]
            with open(report_path) as f:
                report = json.load(f)
            # Must contain scan_id and target fields from the retrieved scan
            required_fields = {"scan_id", "target"}
            present = required_fields.intersection(set(report.keys()))
            if len(present) == len(required_fields):
                score += check("audit_report_exists", True,
                               f"audit_report.json found at {report_path} with fields: {list(report.keys())}")
            else:
                score += check("audit_report_exists", False,
                               f"audit_report.json missing required fields. Found: {list(report.keys())}, need: {required_fields}")
    except Exception as e:
        score += check("audit_report_exists", False, f"Error reading audit_report.json: {e}")

    # ── CHECK 7: audit_report.json scan target is 127.0.0.1 (in-scope) ──────
    try:
        report_files = list(workspace.rglob("audit_report.json"))
        if not report_files:
            score += check("audit_report_target_correct", False,
                           "audit_report.json not found")
        else:
            with open(report_files[0]) as f:
                report = json.load(f)
            target = report.get("target", "")
            scan_id = report.get("scan_id", "")
            if "127.0.0.1" in str(target) and scan_id and scan_id != "stale-0000-0000":
                score += check("audit_report_target_correct", True,
                               f"target='{target}', scan_id='{scan_id}' — correct loopback scan reported")
            else:
                score += check("audit_report_target_correct", False,
                               f"target='{target}' or scan_id='{scan_id}' not correct. Expected target=127.0.0.1 and a real scan_id")
    except Exception as e:
        score += check("audit_report_target_correct", False, f"Error: {e}")

    total_score = score / max_checks
    passed = total_score >= 0.7 and all(c["passed"] for c in checks[:3])

    result = {
        "passed": passed,
        "score": round(total_score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(ws)