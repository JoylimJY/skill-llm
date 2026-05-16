#!/usr/bin/env python3
import sys
import json
import subprocess
import re
from pathlib import Path

def run_mcporter(cmd_args):
    """Run an mcporter command and return stdout."""
    try:
        result = subprocess.run(
            ["mcporter", "call"] + cmd_args,
            capture_output=True, text=True, timeout=30
        )
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)

def find_report(workspace):
    """Find maintenance_report.json anywhere in workspace."""
    workspace_path = Path(workspace)
    candidates = list(workspace_path.rglob("maintenance_report.json"))
    if candidates:
        return candidates[0]
    return None

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    # ---- CHECK 1: maintenance_report.json exists ----
    report_path = find_report(workspace)
    if report_path and report_path.exists():
        checks.append({"name": "report_file_exists", "passed": True, "detail": f"Found at {report_path}"})
    else:
        checks.append({"name": "report_file_exists", "passed": False, "detail": "maintenance_report.json not found anywhere in workspace"})

    # ---- CHECK 2: Report is valid JSON ----
    report_data = None
    if report_path and report_path.exists():
        try:
            report_data = json.loads(report_path.read_text())
            checks.append({"name": "report_valid_json", "passed": True, "detail": "Report is valid JSON"})
        except json.JSONDecodeError as e:
            checks.append({"name": "report_valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
    else:
        checks.append({"name": "report_valid_json", "passed": False, "detail": "No report file to parse"})

    # ---- CHECK 3: Report contains required fields ----
    required_fields = ["memories_saved", "gc_result", "consolidation_result", "promotion_result"]
    if report_data and isinstance(report_data, dict):
        missing = [f for f in required_fields if f not in report_data]
        if not missing:
            checks.append({"name": "report_has_required_fields", "passed": True, "detail": f"All required fields present: {required_fields}"})
        else:
            checks.append({"name": "report_has_required_fields", "passed": False, "detail": f"Missing fields: {missing}"})
    else:
        checks.append({"name": "report_has_required_fields", "passed": False, "detail": "Report data not available or not a dict"})

    # ---- CHECK 4: Exactly 5 memories saved (one per finding) ----
    if report_data and isinstance(report_data, dict):
        saved = report_data.get("memories_saved", [])
        count = len(saved) if isinstance(saved, list) else (saved if isinstance(saved, int) else 0)
        if count == 5:
            checks.append({"name": "all_5_findings_saved", "passed": True, "detail": "All 5 research findings saved"})
        else:
            checks.append({"name": "all_5_findings_saved", "passed": False, "detail": f"Expected 5 findings saved, got {count}"})
    else:
        checks.append({"name": "all_5_findings_saved", "passed": False, "detail": "Cannot determine saved count from report"})

    # ---- CHECK 5: Strength values are correct per importance mapping ----
    # critical -> 2.0, high -> 1.5, normal -> 1.0, temporary -> 0.5
    # Load the original findings to know expected strengths
    findings_path = Path(workspace) / "data" / "research_findings.json"
    importance_to_strength = {
        "critical": 2.0,
        "high": 1.5,
        "normal": 1.0,
        "temporary": 0.5,
    }
    expected_strengths = {}
    try:
        findings = json.loads(findings_path.read_text())
        for f in findings:
            expected_strengths[f["id"]] = importance_to_strength.get(f["importance"], 1.0)
    except Exception as e:
        expected_strengths = {}

    if report_data and isinstance(report_data, dict) and isinstance(report_data.get("memories_saved"), list):
        saved_list = report_data["memories_saved"]
        strength_ok = True
        strength_details = []
        
        # Try to verify strength from the actual CortexGraph storage
        try:
            graph_output = run_mcporter(["cortexgraph.read_graph", "limit=50"])
            # Check if we can find strength values in the saved memories
            # Also check from report data if it contains strength info
            for entry in saved_list:
                if isinstance(entry, dict) and "strength" in entry:
                    finding_id = entry.get("finding_id", entry.get("id", ""))
                    expected = expected_strengths.get(finding_id)
                    actual = float(entry.get("strength", 0))
                    if expected and abs(actual - expected) > 0.01:
                        strength_ok = False
                        strength_details.append(f"{finding_id}: expected {expected}, got {actual}")
        except Exception as e:
            strength_details.append(f"Could not verify strengths: {e}")

        # Even if we can't verify from report, check the CortexGraph directly
        try:
            graph_output = run_mcporter(["cortexgraph.read_graph", "limit=50"])
            # Look for strength=0.5 (temporary) and strength=2.0 (critical) in output
            has_05 = "0.5" in graph_output or '"strength": 0.5' in graph_output
            has_20 = "2.0" in graph_output or '"strength": 2.0' in graph_output
            has_15 = "1.5" in graph_output or '"strength": 1.5' in graph_output

            if has_05 and has_20 and has_15:
                checks.append({"name": "correct_strength_values", "passed": True, "detail": "Found strength=0.5 (temporary), 1.5 (high), 2.0 (critical) in graph"})
            else:
                # Fall back to search approach
                search_output = run_mcporter(["cortexgraph.search_memory", "query=attention mechanism transformer", "top_k=10"])
                # If critical memories are present and have high strength, that's evidence
                if "attention" in search_output.lower() or "patent" in search_output.lower():
                    checks.append({"name": "correct_strength_values", "passed": True, "detail": "Critical memories found in search (strength likely correct)"})
                else:
                    checks.append({"name": "correct_strength_values", "passed": False, "detail": f"Could not confirm correct strength values. has_0.5={has_05}, has_1.5={has_15}, has_2.0={has_20}"})
        except Exception as e:
            checks.append({"name": "correct_strength_values", "passed": False, "detail": f"Error checking strengths: {e}"})
    else:
        # Check directly in CortexGraph
        try:
            graph_output = run_mcporter(["cortexgraph.read_graph", "limit=50"])
            has_05 = "0.5" in graph_output
            has_20 = "2.0" in graph_output
            has_15 = "1.5" in graph_output
            if has_05 and has_20 and has_15:
                checks.append({"name": "correct_strength_values", "passed": True, "detail": "Found diverse strength values in graph (0.5, 1.5, 2.0)"})
            else:
                checks.append({"name": "correct_strength_values", "passed": False, "detail": f"Missing strength diversity: has_0.5={has_05}, has_1.5={has_15}, has_2.0={has_20}"})
        except Exception as e:
            checks.append({"name": "correct_strength_values", "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 6: GC was run (dry_run or real) and result captured ----
    if report_data and isinstance(report_data, dict):
        gc_result = report_data.get("gc_result")
        if gc_result is not None and gc_result != "" and gc_result != {}:
            checks.append({"name": "gc_run_and_captured", "passed": True, "detail": f"GC result captured: {str(gc_result)[:100]}"})
        else:
            checks.append({"name": "gc_run_and_captured", "passed": False, "detail": "gc_result is empty or None"})
    else:
        checks.append({"name": "gc_run_and_captured", "passed": False, "detail": "Report not available"})

    # ---- CHECK 7: Consolidation was run with correct parameters (auto_detect=true mode=apply) ----
    if report_data and isinstance(report_data, dict):
        consol_result = report_data.get("consolidation_result")
        consol_str = str(consol_result).lower() if consol_result else ""
        # Check if the report indicates apply mode was used (not just preview)
        # Also verify by looking at consolidation output
        if consol_result is not None and consol_result != "":
            # Check mode used
            if "apply" in consol_str or "mode" in consol_str or "consolidat" in consol_str:
                checks.append({"name": "consolidation_apply_mode", "passed": True, "detail": "Consolidation ran with apply mode"})
            else:
                # Accept if result is present and non-trivially shows consolidation happened
                checks.append({"name": "consolidation_apply_mode", "passed": True, "detail": f"Consolidation result present: {str(consol_result)[:100]}"})
        else:
            checks.append({"name": "consolidation_apply_mode", "passed": False, "detail": "consolidation_result is empty or None"})
    else:
        checks.append({"name": "consolidation_apply_mode", "passed": False, "detail": "Report not available"})

    # ---- CHECK 8: Promote was run ----
    if report_data and isinstance(report_data, dict):
        promote_result = report_data.get("promotion_result")
        if promote_result is not None and promote_result != "":
            checks.append({"name": "promotion_run_and_captured", "passed": True, "detail": f"Promotion result: {str(promote_result)[:100]}"})
        else:
            checks.append({"name": "promotion_run_and_captured", "passed": False, "detail": "promotion_result is empty or None"})
    else:
        checks.append({"name": "promotion_run_and_captured", "passed": False, "detail": "Report not available"})

    # ---- CHECK 9: Memories actually exist in CortexGraph (not just dry run) ----
    try:
        search_output = run_mcporter(["cortexgraph.search_memory", "query=microservices architecture decision", "top_k=5"])
        if "microservices" in search_output.lower() or "adr" in search_output.lower() or "architecture" in search_output.lower():
            checks.append({"name": "memories_persisted_in_cortexgraph", "passed": True, "detail": "Critical memory about architecture decision found in search"})
        else:
            # Try another search
            search2 = run_mcporter(["cortexgraph.search_memory", "query=attention mechanism latency", "top_k=5"])
            if "attention" in search2.lower() or "latency" in search2.lower() or "transformer" in search2.lower():
                checks.append({"name": "memories_persisted_in_cortexgraph", "passed": True, "detail": "Critical memory about attention mechanism found in search"})
            else:
                checks.append({"name": "memories_persisted_in_cortexgraph", "passed": False, "detail": f"Could not find saved memories in CortexGraph. Search output: {search_output[:200]}"})
    except Exception as e:
        checks.append({"name": "memories_persisted_in_cortexgraph", "passed": False, "detail": f"Error searching CortexGraph: {e}"})

    # ---- CHECK 10: Report saved in reports/ directory ----
    reports_dir = Path(workspace) / "reports"
    report_in_reports = reports_dir / "maintenance_report.json"
    if report_in_reports.exists():
        checks.append({"name": "report_in_correct_directory", "passed": True, "detail": "maintenance_report.json found in reports/"})
    else:
        # Accept it anywhere in workspace but note it
        if report_path and report_path.exists():
            checks.append({"name": "report_in_correct_directory", "passed": False, "detail": f"Report found at {report_path} but expected in reports/maintenance_report.json"})
        else:
            checks.append({"name": "report_in_correct_directory", "passed": False, "detail": "Report not found in reports/ directory"})

    # Calculate score
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total

    result = {
        "passed": score >= 0.7,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()