import sys
import json
import os
from pathlib import Path

def load_report(workspace):
    """Find plugin_audit_report.json anywhere in workspace."""
    candidates = list(Path(workspace).rglob("plugin_audit_report.json"))
    if not candidates:
        return None, "File 'plugin_audit_report.json' not found anywhere in workspace."
    # prefer root-level
    candidates.sort(key=lambda p: len(p.parts))
    return candidates[0], None

def run_checks(workspace):
    checks = []

    report_path, err = load_report(workspace)

    # CHECK 0: File exists
    checks.append({
        "name": "plugin_audit_report.json exists",
        "passed": report_path is not None,
        "detail": err if err else f"Found at {report_path}"
    })
    if report_path is None:
        return checks

    # Load JSON
    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "report is valid JSON", "passed": False, "detail": str(e)})
        return checks

    checks.append({"name": "report is valid JSON", "passed": True, "detail": "Parsed successfully."})

    # CHECK 1: bundled_plugin_count == 8
    try:
        count = report.get("bundled_plugin_count")
        passed = count == 8
        checks.append({
            "name": "bundled_plugin_count is 8",
            "passed": passed,
            "detail": f"Got: {count}"
        })
    except Exception as e:
        checks.append({"name": "bundled_plugin_count is 8", "passed": False, "detail": str(e)})

    # CHECK 2: disabled_plugins list contains exactly the 3 disabled plugins
    EXPECTED_DISABLED = {"cron-scheduler", "log-archiver", "metrics-exporter"}
    try:
        disabled = report.get("disabled_plugins")
        if isinstance(disabled, list):
            disabled_set = set(disabled)
            passed = disabled_set == EXPECTED_DISABLED
            checks.append({
                "name": f"disabled_plugins = {sorted(EXPECTED_DISABLED)}",
                "passed": passed,
                "detail": f"Got: {sorted(disabled_set)}"
            })
        else:
            checks.append({
                "name": f"disabled_plugins = {sorted(EXPECTED_DISABLED)}",
                "passed": False,
                "detail": f"'disabled_plugins' is not a list; got type {type(disabled).__name__}: {disabled}"
            })
    except Exception as e:
        checks.append({"name": "disabled_plugins list", "passed": False, "detail": str(e)})

    # CHECK 3: openclaw-qqbot inspect data is present
    try:
        qqbot = report.get("openclaw_qqbot_inspect") or report.get("plugin_inspect") or {}
        # Try nested
        if not qqbot and isinstance(report.get("inspected_plugins"), dict):
            qqbot = report["inspected_plugins"].get("openclaw-qqbot", {})
        if not qqbot and isinstance(report.get("inspected_plugins"), list):
            for item in report["inspected_plugins"]:
                if isinstance(item, dict) and item.get("id") == "openclaw-qqbot":
                    qqbot = item
                    break
        passed = bool(qqbot) and (
            qqbot.get("id") == "openclaw-qqbot" or
            qqbot.get("runtime", {}).get("id") == "openclaw-qqbot"
        )
        checks.append({
            "name": "openclaw-qqbot inspect data present",
            "passed": passed,
            "detail": f"qqbot section keys: {list(qqbot.keys()) if isinstance(qqbot, dict) else qqbot}"
        })
    except Exception as e:
        checks.append({"name": "openclaw-qqbot inspect data present", "passed": False, "detail": str(e)})

    # CHECK 4 (THE KEY TRAP): openclaw-qqbot status_description must be "已启用，但加载失败"
    EXPECTED_STATUS = "已启用，但加载失败"
    try:
        # Search in multiple possible locations
        def find_status_desc(d):
            if isinstance(d, dict):
                if d.get("id") == "openclaw-qqbot":
                    return d.get("status_description")
                for v in d.values():
                    r = find_status_desc(v)
                    if r is not None:
                        return r
            elif isinstance(d, list):
                for item in d:
                    r = find_status_desc(item)
                    if r is not None:
                        return r
            return None

        status_desc = find_status_desc(report)
        # Also check top-level
        if status_desc is None:
            status_desc = report.get("qqbot_status_description") or report.get("openclaw_qqbot_status")

        passed = status_desc == EXPECTED_STATUS
        checks.append({
            "name": f"openclaw-qqbot status_description = '{EXPECTED_STATUS}'",
            "passed": passed,
            "detail": f"Got: '{status_desc}'"
        })
    except Exception as e:
        checks.append({
            "name": f"openclaw-qqbot status_description = '{EXPECTED_STATUS}'",
            "passed": False,
            "detail": str(e)
        })

    # CHECK 5: qqbot runtime data has error field from CLI
    try:
        def find_error_field(d):
            if isinstance(d, dict):
                if d.get("id") == "openclaw-qqbot":
                    # check nested runtime
                    runtime = d.get("runtime", d)
                    return runtime.get("error")
                for v in d.values():
                    r = find_error_field(v)
                    if r is not None:
                        return r
            elif isinstance(d, list):
                for item in d:
                    r = find_error_field(item)
                    if r is not None:
                        return r
            return None

        error_val = find_error_field(report)
        expected_error = "WebSocket connection refused: ws://localhost:5700"
        passed = error_val is not None and expected_error in str(error_val)
        checks.append({
            "name": "openclaw-qqbot runtime error message captured",
            "passed": passed,
            "detail": f"Got error field: '{error_val}'"
        })
    except Exception as e:
        checks.append({"name": "openclaw-qqbot runtime error message captured", "passed": False, "detail": str(e)})

    # CHECK 6: all 8 bundled plugin IDs present somewhere in bundled list
    EXPECTED_IDS = {"discord","openclaw-qqbot","webhook-relay","cron-scheduler",
                    "log-archiver","alert-dispatcher","metrics-exporter","auth-bridge"}
    try:
        bundled_list = report.get("bundled_plugins") or report.get("all_plugins") or []
        if isinstance(bundled_list, list):
            found_ids = set()
            for item in bundled_list:
                if isinstance(item, dict):
                    found_ids.add(item.get("id",""))
                elif isinstance(item, str):
                    found_ids.add(item)
            passed = EXPECTED_IDS == found_ids
            checks.append({
                "name": "all 8 bundled plugin IDs present",
                "passed": passed,
                "detail": f"Found: {sorted(found_ids)}, Expected: {sorted(EXPECTED_IDS)}"
            })
        else:
            checks.append({
                "name": "all 8 bundled plugin IDs present",
                "passed": False,
                "detail": f"bundled_plugins/all_plugins is not a list: {type(bundled_list).__name__}"
            })
    except Exception as e:
        checks.append({"name": "all 8 bundled plugin IDs present", "passed": False, "detail": str(e)})

    return checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = run_checks(workspace)
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall = all(c["passed"] for c in checks)
    result = {
        "passed": overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()