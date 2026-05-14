import sys
import json
import subprocess
from pathlib import Path

def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    overall_passed = True

    # ── Helper ────────────────────────────────────────────────────────────────
    def add_check(name, passed, detail):
        nonlocal overall_passed
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            overall_passed = False

    # ── Check 1: Find the report JSON file ───────────────────────────────────
    report_file = None
    candidates = list(workspace.rglob("report.json"))
    if not candidates:
        # Accept any *report*.json not in the 'reports/drafts' or 'reports/old' dirs
        candidates = [
            f for f in workspace.rglob("*.json")
            if "report" in f.name.lower()
            and "draft" not in f.name.lower()
            and "schema" not in f.name.lower()
            and "archive" not in str(f)
            and "2024" not in str(f)
        ]

    if candidates:
        # Prefer one named exactly 'report.json' or closest match
        exact = [f for f in candidates if f.name == "report.json"]
        report_file = exact[0] if exact else candidates[0]
        add_check(
            "report_file_exists",
            True,
            f"Found report file at: {report_file}"
        )
    else:
        add_check(
            "report_file_exists",
            False,
            "No report JSON file found in workspace. Expected a file named 'report.json'."
        )
        # Can't proceed without the file
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    # ── Check 2: Report file is valid JSON ────────────────────────────────────
    try:
        report_data = json.loads(report_file.read_text())
        add_check(
            "report_is_valid_json",
            True,
            f"Report file is valid JSON with top-level type: {type(report_data).__name__}"
        )
    except (json.JSONDecodeError, IOError) as e:
        add_check("report_is_valid_json", False, f"Failed to parse report JSON: {e}")
        score = 1.0 / 6.0
        return {"passed": False, "score": score, "checks": checks}

    # ── Check 3: Report contains meaningful analysis data ─────────────────────
    # The tool should produce a structured object, not an empty dict/list
    report_str = json.dumps(report_data).lower()
    
    has_content = False
    if isinstance(report_data, dict) and len(report_data) >= 2:
        has_content = True
    elif isinstance(report_data, list) and len(report_data) >= 1:
        has_content = True
    
    add_check(
        "report_has_meaningful_content",
        has_content,
        f"Report has {len(report_data) if isinstance(report_data, (dict, list)) else 0} top-level keys/items"
    )

    # ── Check 4: Report references the logistics agents ───────────────────────
    logistics_agents = ["payment-proc", "inventory-check", "order-intake", "shipping-coord", "fraud-detector", "notifier"]
    agents_found = [a for a in logistics_agents if a in report_str]
    
    add_check(
        "report_references_pipeline_agents",
        len(agents_found) >= 3,
        f"Report references these known agents: {agents_found}"
    )

    # ── Check 5: Report contains latency/bottleneck information ───────────────
    bottleneck_keywords = ["bottleneck", "latency", "latency_ms", "payload", "message", "traffic", "flow", "delivered", "timeout"]
    keywords_found = [kw for kw in bottleneck_keywords if kw in report_str]
    
    add_check(
        "report_contains_traffic_analysis_data",
        len(keywords_found) >= 3,
        f"Report contains traffic analysis keywords: {keywords_found}"
    )

    # ── Check 6: The correct input log was used (message IDs present) ─────────
    # Our generated messages have IDs like msg-0001 through msg-0200
    has_msg_ids = "msg-" in report_str or "order-intake" in report_str
    
    # Also check: if the tool ran on the correct log, it should reflect ~200 messages
    msg_count_hint = False
    if isinstance(report_data, dict):
        for v in report_data.values():
            if isinstance(v, (int, float)) and 150 <= v <= 250:
                msg_count_hint = True
                break
            if isinstance(v, dict):
                for vv in v.values():
                    if isinstance(vv, (int, float)) and 150 <= vv <= 250:
                        msg_count_hint = True
                        break
    
    add_check(
        "report_derived_from_correct_log",
        has_msg_ids or msg_count_hint,
        f"Report appears to be derived from the correct pipeline log (msg IDs or ~200 count found: {has_msg_ids or msg_count_hint})"
    )

    # ── Score calculation ─────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 3)
    overall_passed = all(c["passed"] for c in checks)

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace_dir)
    print(json.dumps(result, indent=2))