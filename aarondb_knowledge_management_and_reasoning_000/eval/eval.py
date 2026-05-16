import sys
import json
import os
import subprocess
from pathlib import Path

def run_checks(workspace):
    checks = []
    passed_all = True

    def add_check(name, passed, detail):
        nonlocal passed_all
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            passed_all = False

    # --- CHECK 1: Find the main JS solution script ---
    js_files = list(Path(workspace).rglob("*.js"))
    solution_js = None
    for f in js_files:
        content = f.read_text(errors="replace")
        # Must use the aarondb-edge import AND transact AND query
        if "aarondb-edge" in content and "transact" in content and "query" in content:
            solution_js = f
            break

    if solution_js is None:
        add_check("solution_script_exists", False, "No JS file found that imports aarondb-edge and uses transact+query.")
    else:
        add_check("solution_script_exists", True, f"Found solution script: {solution_js}")

    # --- CHECK 2: Correct datom structure { e, a, v } ---
    if solution_js:
        content = solution_js.read_text(errors="replace")
        import re
        # Look for datom objects with e, a, v keys
        datom_pattern = re.search(r'\{\s*e\s*:', content)
        has_ev = re.search(r'["\']?[eE]["\']?\s*:', content) and re.search(r'["\']?[aA]["\']?\s*:', content) and re.search(r'["\']?[vV]["\']?\s*:', content)
        if datom_pattern or has_ev:
            add_check("datom_structure_correct", True, "Script uses { e, a, v } datom structure.")
        else:
            add_check("datom_structure_correct", False, "Script does not appear to use correct { e, a, v } datom structure.")
    else:
        add_check("datom_structure_correct", False, "No solution script to inspect.")

    # --- CHECK 3: Query uses Datalog variable syntax "?varname" ---
    if solution_js:
        content = solution_js.read_text(errors="replace")
        var_pattern = re.search(r'"\?[a-zA-Z]', content)
        if var_pattern:
            add_check("datalog_query_syntax", True, "Script uses Datalog variable syntax '?varname'.")
        else:
            add_check("datalog_query_syntax", False, "Script does not use Datalog variable binding syntax '?varname'.")
    else:
        add_check("datalog_query_syntax", False, "No solution script to inspect.")

    # --- CHECK 4: supplier_knowledge_base.json exists ---
    kb_files = list(Path(workspace).rglob("supplier_knowledge_base.json"))
    if not kb_files:
        add_check("knowledge_base_exported", False, "supplier_knowledge_base.json not found anywhere in workspace.")
        kb_data = None
    else:
        kb_file = kb_files[0]
        try:
            kb_data = json.loads(kb_file.read_text())
            add_check("knowledge_base_exported", True, f"supplier_knowledge_base.json found at {kb_file}")
        except Exception as ex:
            add_check("knowledge_base_exported", False, f"supplier_knowledge_base.json found but invalid JSON: {ex}")
            kb_data = None

    # --- CHECK 5: query_results.json exists and has high-risk suppliers ---
    result_files = list(Path(workspace).rglob("query_results.json"))
    if not result_files:
        add_check("query_results_file_exists", False, "query_results.json not found anywhere in workspace.")
    else:
        result_file = result_files[0]
        try:
            result_data = json.loads(result_file.read_text())
            add_check("query_results_file_exists", True, f"query_results.json found at {result_file}")

            # Must contain the 3 high-risk supplier IDs: S001, S003, S007
            content_str = json.dumps(result_data)
            high_risk_ids = ["S001", "S003", "S007"]
            found_ids = [sid for sid in high_risk_ids if sid in content_str]
            if len(found_ids) == 3:
                add_check("high_risk_suppliers_identified", True, f"All 3 high-risk suppliers found in results: {found_ids}")
            elif len(found_ids) > 0:
                add_check("high_risk_suppliers_identified", False, f"Only partial high-risk suppliers found: {found_ids}, expected all of {high_risk_ids}")
            else:
                add_check("high_risk_suppliers_identified", False, f"No expected high-risk supplier IDs found in query_results.json. Content snippet: {content_str[:300]}")
        except Exception as ex:
            add_check("query_results_file_exists", False, f"query_results.json found but invalid: {ex}")
            add_check("high_risk_suppliers_identified", False, "Could not parse query_results.json.")

    # --- CHECK 6: knowledge base contains supplier facts (not empty) ---
    if kb_data is not None:
        # Should be a list/array of datom-like objects or a structured export
        is_non_empty = False
        if isinstance(kb_data, list) and len(kb_data) >= 5:
            is_non_empty = True
        elif isinstance(kb_data, dict):
            # Could be wrapped
            vals = list(kb_data.values())
            for v in vals:
                if isinstance(v, list) and len(v) >= 5:
                    is_non_empty = True
                    break
            if not is_non_empty and len(str(kb_data)) > 100:
                is_non_empty = True
        if is_non_empty:
            add_check("knowledge_base_has_facts", True, "Exported knowledge base contains sufficient facts.")
        else:
            add_check("knowledge_base_has_facts", False, f"Exported knowledge base appears too small or empty: {str(kb_data)[:200]}")
    else:
        add_check("knowledge_base_has_facts", False, "No valid knowledge base to inspect.")

    # --- CHECK 7: Script runs without error (execute it) ---
    if solution_js:
        try:
            result = subprocess.run(
                ["node", str(solution_js)],
                capture_output=True, text=True, timeout=30, cwd=workspace
            )
            if result.returncode == 0:
                add_check("script_runs_successfully", True, f"Script executed with exit code 0. stdout: {result.stdout[:200]}")
            else:
                add_check("script_runs_successfully", False, f"Script failed with exit code {result.returncode}. stderr: {result.stderr[:300]}")
        except subprocess.TimeoutExpired:
            add_check("script_runs_successfully", False, "Script timed out after 30 seconds.")
        except Exception as ex:
            add_check("script_runs_successfully", False, f"Failed to run script: {ex}")
    else:
        add_check("script_runs_successfully", False, "No solution script to run.")

    score = sum(1 for c in checks if c["passed"]) / len(checks)
    return {"passed": passed_all, "score": round(score, 3), "checks": checks}

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    output = run_checks(workspace)
    print(json.dumps(output, indent=2))