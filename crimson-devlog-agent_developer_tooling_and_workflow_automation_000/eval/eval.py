import sys
import json
import subprocess
import re
from pathlib import Path

def run_devlog(args):
    """Run a devlog command and return stdout."""
    result = subprocess.run(
        ["devlog"] + args,
        capture_output=True, text=True,
        env={**__import__('os').environ, "PATH": "/root/.local/bin:" + __import__('os').environ.get("PATH", "")}
    )
    return result.stdout, result.stderr, result.returncode

def evaluate(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []

    # -----------------------------------------------------------------------
    # CHECK 1: sprint42_summary.json exists somewhere in workspace
    # -----------------------------------------------------------------------
    summary_files = list(workspace.rglob("sprint42_summary.json"))
    summary_exists = len(summary_files) > 0
    checks.append({
        "name": "sprint42_summary.json exists",
        "passed": summary_exists,
        "detail": f"Found at: {summary_files[0]}" if summary_exists else "File not found anywhere in workspace"
    })

    # -----------------------------------------------------------------------
    # CHECK 2: sprint42_summary.json is valid JSON with expected structure
    # -----------------------------------------------------------------------
    summary_valid = False
    summary_data = {}
    if summary_exists:
        try:
            with open(summary_files[0]) as f:
                summary_data = json.load(f)
            summary_valid = True
            checks.append({
                "name": "sprint42_summary.json is valid JSON",
                "passed": True,
                "detail": f"Keys present: {list(summary_data.keys())}"
            })
        except Exception as e:
            checks.append({
                "name": "sprint42_summary.json is valid JSON",
                "passed": False,
                "detail": f"JSON parse error: {e}"
            })
    else:
        checks.append({
            "name": "sprint42_summary.json is valid JSON",
            "passed": False,
            "detail": "File missing, cannot validate JSON"
        })

    # -----------------------------------------------------------------------
    # CHECK 3: devlog entries exist for "Infra Modernization" project
    # -----------------------------------------------------------------------
    try:
        stdout, stderr, rc = run_devlog(["list", "--project", "Infra Modernization"])
        infra_entries_found = rc == 0 and len(stdout.strip()) > 0 and "No logs" not in stdout
        # Count entries - look for lines that seem like log entries
        entry_lines = [l for l in stdout.splitlines() if l.strip() and any(kw in l.lower() for kw in ["vpc", "transit", "rds", "pipeline", "terraform", "migration", "dr", "failover", "tls", "cert", "backend", "state"])]
        checks.append({
            "name": "Infra Modernization project has log entries",
            "passed": infra_entries_found,
            "detail": f"devlog list output (first 500 chars): {stdout[:500]}"
        })
    except Exception as e:
        checks.append({
            "name": "Infra Modernization project has log entries",
            "passed": False,
            "detail": f"Error running devlog list: {e}"
        })

    # -----------------------------------------------------------------------
    # CHECK 4: devlog entries exist for "Auth Service Hardening" project
    # -----------------------------------------------------------------------
    try:
        stdout, stderr, rc = run_devlog(["list", "--project", "Auth Service Hardening"])
        auth_entries_found = rc == 0 and len(stdout.strip()) > 0 and "No logs" not in stdout
        checks.append({
            "name": "Auth Service Hardening project has log entries",
            "passed": auth_entries_found,
            "detail": f"devlog list output (first 500 chars): {stdout[:500]}"
        })
    except Exception as e:
        checks.append({
            "name": "Auth Service Hardening project has log entries",
            "passed": False,
            "detail": f"Error running devlog list: {e}"
        })

    # -----------------------------------------------------------------------
    # CHECK 5: Correct use of --status with "completed" value (not custom invented values)
    # -----------------------------------------------------------------------
    try:
        stdout_infra, _, rc_infra = run_devlog(["list", "--project", "Infra Modernization"])
        stdout_auth, _, rc_auth = run_devlog(["list", "--project", "Auth Service Hardening"])
        combined = (stdout_infra + stdout_auth).lower()
        # Check for proper status values
        has_completed = "completed" in combined
        has_blocked = "blocked" in combined
        has_in_progress = "in-progress" in combined or "in progress" in combined
        status_correct = has_completed and has_blocked and has_in_progress
        checks.append({
            "name": "Correct status values used (completed/blocked/in-progress)",
            "passed": status_correct,
            "detail": f"completed={has_completed}, blocked={has_blocked}, in-progress={has_in_progress}"
        })
    except Exception as e:
        checks.append({
            "name": "Correct status values used (completed/blocked/in-progress)",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # -----------------------------------------------------------------------
    # CHECK 6: Tags are present and comma-separated (evidence of --tags flag usage)
    # -----------------------------------------------------------------------
    try:
        stdout_search, _, rc = run_devlog(["search", "terraform"])
        tags_evidence = rc == 0 and "terraform" in stdout_search.lower()
        checks.append({
            "name": "Tags were applied (searchable via devlog search)",
            "passed": tags_evidence,
            "detail": f"Search for 'terraform' returned: {stdout_search[:300]}"
        })
    except Exception as e:
        checks.append({
            "name": "Tags were applied (searchable via devlog search)",
            "passed": False,
            "detail": f"Error running devlog search: {e}"
        })

    # -----------------------------------------------------------------------
    # CHECK 7: At least 4 entries total logged across both projects
    # -----------------------------------------------------------------------
    try:
        stdout_all, _, rc = run_devlog(["list"])
        # Rough count of entries
        lines = [l for l in stdout_all.splitlines() if l.strip()]
        # Try to count IDs or entry separators
        id_pattern = re.findall(r'\b\d+\b', stdout_all)
        num_unique_ids = len(set(id_pattern))
        # Also count lines with status indicators
        status_lines = [l for l in stdout_all.splitlines() if any(s in l.lower() for s in ["completed", "blocked", "in-progress", "in progress"])]
        enough_entries = len(status_lines) >= 4 or num_unique_ids >= 4
        checks.append({
            "name": "At least 4 log entries total across both projects",
            "passed": enough_entries,
            "detail": f"Status lines found: {len(status_lines)}, unique IDs found: {num_unique_ids}. Output (first 600 chars): {stdout_all[:600]}"
        })
    except Exception as e:
        checks.append({
            "name": "At least 4 log entries total across both projects",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # -----------------------------------------------------------------------
    # CHECK 8: stats command was used (evidence: summary JSON contains stats data)
    # -----------------------------------------------------------------------
    stats_referenced = False
    stats_detail = "No stats data found in sprint42_summary.json"
    if summary_valid and summary_data:
        # Look for stats-like fields in summary JSON
        summary_str = json.dumps(summary_data).lower()
        stats_keywords = ["total", "count", "stats", "completed", "blocked", "in-progress", "infra modernization", "auth service"]
        matches = [kw for kw in stats_keywords if kw in summary_str]
        stats_referenced = len(matches) >= 3
        stats_detail = f"Matched keywords in summary JSON: {matches}"
    checks.append({
        "name": "sprint42_summary.json contains meaningful project stats/counts",
        "passed": stats_referenced,
        "detail": stats_detail
    })

    # -----------------------------------------------------------------------
    # CHECK 9: Both project names appear in summary JSON
    # -----------------------------------------------------------------------
    both_projects_in_summary = False
    if summary_valid and summary_data:
        summary_str = json.dumps(summary_data).lower()
        has_infra = "infra" in summary_str or "modernization" in summary_str
        has_auth = "auth" in summary_str
        both_projects_in_summary = has_infra and has_auth
    checks.append({
        "name": "Both projects referenced in sprint42_summary.json",
        "passed": both_projects_in_summary,
        "detail": f"Infra project present: {has_infra if summary_valid else 'N/A'}, Auth project present: {has_auth if summary_valid else 'N/A'}"
    })

    # -----------------------------------------------------------------------
    # CHECK 10: devlog search was used for security-related entries
    # -----------------------------------------------------------------------
    try:
        stdout_search, _, rc = run_devlog(["search", "security"])
        security_searchable = rc == 0 and len(stdout_search.strip()) > 0 and "No results" not in stdout_search and "No logs" not in stdout_search
        checks.append({
            "name": "Security-tagged entries are searchable via devlog",
            "passed": security_searchable,
            "detail": f"devlog search 'security' output (first 300 chars): {stdout_search[:300]}"
        })
    except Exception as e:
        checks.append({
            "name": "Security-tagged entries are searchable via devlog",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # -----------------------------------------------------------------------
    # Final scoring
    # -----------------------------------------------------------------------
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks

    # Hard gate: must pass core checks (file exists, both projects logged, correct statuses)
    hard_gate_checks = [
        "sprint42_summary.json exists",
        "Infra Modernization project has log entries",
        "Auth Service Hardening project has log entries",
        "Correct status values used (completed/blocked/in-progress)",
    ]
    hard_gate_passed = all(c["passed"] for c in checks if c["name"] in hard_gate_checks)
    final_passed = hard_gate_passed and score >= 0.7

    result = {
        "passed": final_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace_dir)