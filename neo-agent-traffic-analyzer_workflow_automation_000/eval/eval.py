import json
import sys
import os
from pathlib import Path

def run_checks(workspace):
    checks = []
    passed_all = True

    # ── CHECK 1: Full report JSON file exists ──────────────────────────────────
    report_files = list(Path(workspace).rglob("full_analysis_report.json"))
    report_found = len(report_files) > 0
    checks.append({
        "name": "full_analysis_report.json exists",
        "passed": report_found,
        "detail": f"Found at: {report_files[0]}" if report_found else "File not found anywhere in workspace"
    })
    if not report_found:
        passed_all = False

    # ── CHECK 2: Report is valid JSON with non-trivial content ─────────────────
    report_data = None
    if report_found:
        try:
            with open(report_files[0], "r") as f:
                report_data = json.load(f)
            is_dict_or_list = isinstance(report_data, (dict, list))
            has_content = len(json.dumps(report_data)) > 100
            check_passed = is_dict_or_list and has_content
            checks.append({
                "name": "Report contains valid non-trivial JSON structure",
                "passed": check_passed,
                "detail": f"Type: {type(report_data).__name__}, size: {len(json.dumps(report_data))} chars" if check_passed else "Report is empty or malformed"
            })
            if not check_passed:
                passed_all = False
        except Exception as e:
            checks.append({
                "name": "Report contains valid non-trivial JSON structure",
                "passed": False,
                "detail": f"Exception reading report: {e}"
            })
            passed_all = False

    # ── CHECK 3: Report references agent-gamma as a bottleneck ────────────────
    if report_data is not None:
        try:
            report_str = json.dumps(report_data).lower()
            mentions_gamma = "agent-gamma" in report_str or "gamma" in report_str
            checks.append({
                "name": "Report identifies agent-gamma (the bottleneck agent)",
                "passed": mentions_gamma,
                "detail": "Found 'gamma' reference in report" if mentions_gamma else "No reference to agent-gamma in report"
            })
            if not mentions_gamma:
                passed_all = False
        except Exception as e:
            checks.append({
                "name": "Report identifies agent-gamma (the bottleneck agent)",
                "passed": False,
                "detail": f"Exception: {e}"
            })
            passed_all = False

    # ── CHECK 4: DOT visualization file exists ─────────────────────────────────
    dot_files = list(Path(workspace).rglob("*.dot"))
    dot_found = len(dot_files) > 0
    checks.append({
        "name": "DOT network visualization file exists",
        "passed": dot_found,
        "detail": f"Found: {[str(f) for f in dot_files]}" if dot_found else "No .dot file found in workspace"
    })
    if not dot_found:
        passed_all = False

    # ── CHECK 5: DOT file contains valid Graphviz syntax ──────────────────────
    if dot_found:
        try:
            dot_content = dot_files[0].read_text()
            has_digraph = "digraph" in dot_content.lower() or "graph" in dot_content.lower()
            has_arrow = "->" in dot_content or "--" in dot_content
            has_agents = "agent" in dot_content.lower() or "alpha" in dot_content.lower()
            dot_valid = has_digraph and (has_arrow or has_agents)
            checks.append({
                "name": "DOT file contains valid Graphviz network graph syntax",
                "passed": dot_valid,
                "detail": f"has_digraph={has_digraph}, has_arrow={has_arrow}, has_agents={has_agents}" if dot_valid
                          else f"DOT content appears invalid. First 200 chars: {dot_content[:200]}"
            })
            if not dot_valid:
                passed_all = False
        except Exception as e:
            checks.append({
                "name": "DOT file contains valid Graphviz network graph syntax",
                "passed": False,
                "detail": f"Exception reading DOT file: {e}"
            })
            passed_all = False

    # ── CHECK 6: DOT file references multiple agents ──────────────────────────
    if dot_found:
        try:
            dot_content = dot_files[0].read_text().lower()
            agent_names = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]
            found_agents = [a for a in agent_names if a in dot_content]
            enough_agents = len(found_agents) >= 4
            checks.append({
                "name": "DOT graph includes at least 4 of the 6 agents",
                "passed": enough_agents,
                "detail": f"Found agents in DOT: {found_agents} ({len(found_agents)}/6)"
            })
            if not enough_agents:
                passed_all = False
        except Exception as e:
            checks.append({
                "name": "DOT graph includes at least 4 of the 6 agents",
                "passed": False,
                "detail": f"Exception: {e}"
            })
            passed_all = False

    # ── CHECK 7: Bottleneck analysis output was produced ──────────────────────
    # Check that either the report contains bottleneck data OR a separate bottleneck file exists
    bottleneck_evidence = False
    detail_msg = ""
    try:
        if report_data is not None:
            report_str = json.dumps(report_data).lower()
            if any(kw in report_str for kw in ["bottleneck", "latency", "timeout", "slow", "high_latency"]):
                bottleneck_evidence = True
                detail_msg = "Report contains bottleneck/latency analysis keywords"

        if not bottleneck_evidence:
            # Look for a separate bottleneck output file
            bn_files = list(Path(workspace).rglob("*bottleneck*"))
            if bn_files:
                bottleneck_evidence = True
                detail_msg = f"Found bottleneck file: {bn_files[0]}"

        checks.append({
            "name": "Bottleneck analysis evidence found in outputs",
            "passed": bottleneck_evidence,
            "detail": detail_msg if bottleneck_evidence else "No bottleneck analysis keywords in report and no bottleneck-named files found"
        })
        if not bottleneck_evidence:
            passed_all = False
    except Exception as e:
        checks.append({
            "name": "Bottleneck analysis evidence found in outputs",
            "passed": False,
            "detail": f"Exception: {e}"
        })
        passed_all = False

    # ── SCORE ──────────────────────────────────────────────────────────────────
    num_passed = sum(1 for c in checks if c["passed"])
    score = round(num_passed / len(checks), 3)

    return {
        "passed": passed_all,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))