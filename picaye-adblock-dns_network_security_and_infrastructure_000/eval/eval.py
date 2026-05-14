#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path

def load_json(path):
    with open(path) as f:
        return json.load(f)

def run_eval(workspace):
    checks = []
    total_score = 0.0

    workspace = Path(workspace)

    # ------------------------------------------------------------------ #
    # CHECK 1: config.json — upstream changed to 8.8.8.8                  #
    # ------------------------------------------------------------------ #
    try:
        config_path = workspace / "skills/adblock/data/config.json"
        config = load_json(config_path)
        upstream_ok = config.get("upstream") == "8.8.8.8"
        checks.append({
            "name": "config.json: upstream set to 8.8.8.8",
            "passed": upstream_ok,
            "detail": f"upstream = '{config.get('upstream')}'"
        })
        if upstream_ok:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": "config.json: upstream set to 8.8.8.8", "passed": False, "detail": str(e)})

    # ------------------------------------------------------------------ #
    # CHECK 2: config.json — apiPort changed to 9053                      #
    # ------------------------------------------------------------------ #
    try:
        config_path = workspace / "skills/adblock/data/config.json"
        config = load_json(config_path)
        port_ok = config.get("apiPort") == 9053
        checks.append({
            "name": "config.json: apiPort set to 9053",
            "passed": port_ok,
            "detail": f"apiPort = '{config.get('apiPort')}'"
        })
        if port_ok:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": "config.json: apiPort set to 9053", "passed": False, "detail": str(e)})

    # ------------------------------------------------------------------ #
    # CHECK 3: config.json — port 53 preserved                            #
    # ------------------------------------------------------------------ #
    try:
        config = load_json(workspace / "skills/adblock/data/config.json")
        port_ok = config.get("port") == 53
        checks.append({
            "name": "config.json: DNS port 53 preserved",
            "passed": port_ok,
            "detail": f"port = '{config.get('port')}'"
        })
        if port_ok:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "config.json: DNS port 53 preserved", "passed": False, "detail": str(e)})

    # ------------------------------------------------------------------ #
    # CHECK 4: whitelist.txt contains payroll.acmecorp.com                #
    # ------------------------------------------------------------------ #
    try:
        wl_path = workspace / "skills/adblock/data/whitelist.txt"
        with open(wl_path) as f:
            wl_domains = {line.strip().lower() for line in f if line.strip()}
        has_payroll = "payroll.acmecorp.com" in wl_domains
        checks.append({
            "name": "whitelist.txt: payroll.acmecorp.com present",
            "passed": has_payroll,
            "detail": f"whitelist entries: {sorted(wl_domains)}"
        })
        if has_payroll:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "whitelist.txt: payroll.acmecorp.com present", "passed": False, "detail": str(e)})

    # ------------------------------------------------------------------ #
    # CHECK 5: custom-blacklist.txt contains telemetry.spyware-vendor.com #
    # ------------------------------------------------------------------ #
    try:
        cb_path = workspace / "skills/adblock/data/custom-blacklist.txt"
        with open(cb_path) as f:
            cb_domains = {line.strip().lower() for line in f if line.strip()}
        has_telemetry = "telemetry.spyware-vendor.com" in cb_domains
        checks.append({
            "name": "custom-blacklist.txt: telemetry.spyware-vendor.com present",
            "passed": has_telemetry,
            "detail": f"blacklist entries: {sorted(cb_domains)}"
        })
        if has_telemetry:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "custom-blacklist.txt: telemetry.spyware-vendor.com present", "passed": False, "detail": str(e)})

    # ------------------------------------------------------------------ #
    # CHECK 6: custom-blacklist.txt contains ads.badnetwork.io            #
    # ------------------------------------------------------------------ #
    try:
        cb_path = workspace / "skills/adblock/data/custom-blacklist.txt"
        with open(cb_path) as f:
            cb_domains = {line.strip().lower() for line in f if line.strip()}
        has_bad = "ads.badnetwork.io" in cb_domains
        checks.append({
            "name": "custom-blacklist.txt: ads.badnetwork.io present",
            "passed": has_bad,
            "detail": f"blacklist entries: {sorted(cb_domains)}"
        })
        if has_bad:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "custom-blacklist.txt: ads.badnetwork.io present", "passed": False, "detail": str(e)})

    # ------------------------------------------------------------------ #
    # CHECK 7: dns_audit_report.json exists somewhere in workspace        #
    # ------------------------------------------------------------------ #
    report_path = None
    try:
        candidates = list(workspace.rglob("dns_audit_report.json"))
        # Exclude the eval script itself or mock server areas
        candidates = [c for c in candidates if "mock" not in str(c)]
        found = len(candidates) > 0
        if found:
            report_path = candidates[0]
        checks.append({
            "name": "dns_audit_report.json: file exists",
            "passed": found,
            "detail": f"Found at: {report_path}" if found else "File not found anywhere in workspace"
        })
        if found:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "dns_audit_report.json: file exists", "passed": False, "detail": str(e)})

    # ------------------------------------------------------------------ #
    # CHECK 8: report has stats section with totalQueries and             #
    #          blockedQueries                                              #
    # ------------------------------------------------------------------ #
    report = None
    if report_path:
        try:
            report = load_json(report_path)
            stats_section = report.get("stats", report)  # allow flat or nested
            has_total = "totalQueries" in stats_section or "total_queries" in stats_section
            has_blocked = "blockedQueries" in stats_section or "blocked_queries" in stats_section
            ok = has_total and has_blocked
            checks.append({
                "name": "dns_audit_report.json: contains query stats (totalQueries, blockedQueries)",
                "passed": ok,
                "detail": f"Keys found: {list(stats_section.keys()) if isinstance(stats_section, dict) else 'N/A'}"
            })
            if ok:
                total_score += 0.05
        except Exception as e:
            checks.append({"name": "dns_audit_report.json: contains query stats", "passed": False, "detail": str(e)})
    else:
        checks.append({"name": "dns_audit_report.json: contains query stats", "passed": False, "detail": "Report file not found"})

    # ------------------------------------------------------------------ #
    # CHECK 9: report shows doubleclick.net as BLOCKED                    #
    # ------------------------------------------------------------------ #
    if report is not None:
        try:
            # Accept various formats: domain_status dict, domain_checks list, etc.
            raw = json.dumps(report).lower()
            has_doubleclick_blocked = (
                "doubleclick.net" in raw and
                ("blocked" in raw or "0.0.0.0" in raw)
            )
            # More precise: look for domain_status or similar
            domain_status = report.get("domain_status", report.get("domains", report.get("checks", {})))
            
            precise_blocked = False
            if isinstance(domain_status, dict):
                for k, v in domain_status.items():
                    if "doubleclick" in k.lower():
                        v_str = json.dumps(v).lower()
                        if "block" in v_str or "0.0.0.0" in v_str or v is True:
                            precise_blocked = True
            elif isinstance(domain_status, list):
                for item in domain_status:
                    item_str = json.dumps(item).lower()
                    if "doubleclick" in item_str and ("block" in item_str or "0.0.0.0" in item_str):
                        precise_blocked = True

            passed = has_doubleclick_blocked or precise_blocked
            checks.append({
                "name": "dns_audit_report.json: doubleclick.net shown as blocked",
                "passed": passed,
                "detail": "Found doubleclick.net with blocked/0.0.0.0 status" if passed else "Not found or not marked blocked"
            })
            if passed:
                total_score += 0.075
        except Exception as e:
            checks.append({"name": "dns_audit_report.json: doubleclick.net shown as blocked", "passed": False, "detail": str(e)})
    else:
        checks.append({"name": "dns_audit_report.json: doubleclick.net shown as blocked", "passed": False, "detail": "Report not available"})

    # ------------------------------------------------------------------ #
    # CHECK 10: report shows payroll.acmecorp.com as whitelisted/allowed  #
    # ------------------------------------------------------------------ #
    if report is not None:
        try:
            raw = json.dumps(report).lower()
            has_payroll = "payroll.acmecorp.com" in raw
            is_allowed = False
            if has_payroll:
                # Find context around payroll
                idx = raw.find("payroll.acmecorp.com")
                snippet = raw[max(0, idx-50):idx+100]
                is_allowed = any(word in snippet for word in ["allow", "whitelist", "forward", "not block", "false"])
                # Also: if the value is false for "blocked"
            passed = has_payroll and is_allowed
            checks.append({
                "name": "dns_audit_report.json: payroll.acmecorp.com shown as allowed/whitelisted",
                "passed": passed,
                "detail": f"payroll.acmecorp.com present: {has_payroll}, allowed context: {is_allowed}"
            })
            if passed:
                total_score += 0.075
        except Exception as e:
            checks.append({"name": "dns_audit_report.json: payroll.acmecorp.com whitelisted", "passed": False, "detail": str(e)})
    else:
        checks.append({"name": "dns_audit_report.json: payroll.acmecorp.com whitelisted", "passed": False, "detail": "Report not available"})

    # ------------------------------------------------------------------ #
    # CHECK 11: telemetry.spyware-vendor.com shown as blocked in report   #
    # ------------------------------------------------------------------ #
    if report is not None:
        try:
            raw = json.dumps(report).lower()
            has_domain = "telemetry.spyware-vendor.com" in raw
            is_blocked = False
            if has_domain:
                idx = raw.find("telemetry.spyware-vendor.com")
                snippet = raw[max(0, idx-50):idx+120]
                is_blocked = any(word in snippet for word in ["block", "0.0.0.0", "true", "denied"])
            passed = has_domain and is_blocked
            checks.append({
                "name": "dns_audit_report.json: telemetry.spyware-vendor.com shown as blocked",
                "passed": passed,
                "detail": f"domain present: {has_domain}, blocked context: {is_blocked}"
            })
            if passed:
                total_score += 0.075
        except Exception as e:
            checks.append({"name": "dns_audit_report.json: telemetry.spyware-vendor.com blocked", "passed": False, "detail": str(e)})
    else:
        checks.append({"name": "dns_audit_report.json: telemetry.spyware-vendor.com blocked", "passed": False, "detail": "Report not available"})

    # ------------------------------------------------------------------ #
    # CHECK 12: ads.badnetwork.io shown as blocked in report              #
    # ------------------------------------------------------------------ #
    if report is not None:
        try:
            raw = json.dumps(report).lower()
            has_domain = "ads.badnetwork.io" in raw
            is_blocked = False
            if has_domain:
                idx = raw.find("ads.badnetwork.io")
                snippet = raw[max(0, idx-50):idx+120]
                is_blocked = any(word in snippet for word in ["block", "0.0.0.0", "true", "denied"])
            passed = has_domain and is_blocked
            checks.append({
                "name": "dns_audit_report.json: ads.badnetwork.io shown as blocked",
                "passed": passed,
                "detail": f"domain present: {has_domain}, blocked context: {is_blocked}"
            })
            if passed:
                total_score += 0.075
        except Exception as e:
            checks.append({"name": "dns_audit_report.json: ads.badnetwork.io blocked", "passed": False, "detail": str(e)})
    else:
        checks.append({"name": "dns_audit_report.json: ads.badnetwork.io blocked", "passed": False, "detail": "Report not available"})

    # Clamp score
    total_score = min(1.0, round(total_score, 4))
    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": total_score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))