import json
import sys
import os
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    
    # ── Helper ──────────────────────────────────────────────────────────────
    def check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # ── 1. Find tool_audit_report.json ──────────────────────────────────────
    report_path = None
    candidates = list(Path(workspace).rglob("tool_audit_report.json"))
    # Exclude the archived/template files that are distractors
    candidates = [p for p in candidates if "archived" not in str(p) and "template" not in str(p).lower()]
    
    if not candidates:
        check("report_file_exists", False, "tool_audit_report.json not found anywhere in workspace")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    report_path = candidates[0]
    check("report_file_exists", True, f"Found at {report_path}")

    # ── 2. Parse JSON ───────────────────────────────────────────────────────
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        check("report_valid_json", True, "File parses as valid JSON")
    except Exception as e:
        check("report_valid_json", False, f"JSON parse error: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── 3. Tool Discovery List ──────────────────────────────────────────────
    # The report must contain discovered tools. We look for a list/array
    # that includes both "add" and "hello_world"
    tools_found = False
    tools_detail = "No tools list found in report"
    
    report_str = json.dumps(report).lower()
    
    # Search for tools in any reasonable structure
    def find_tools_in_obj(obj):
        """Recursively search for a list containing tool names"""
        if isinstance(obj, list):
            str_items = [str(i).lower() for i in obj]
            if any("add" in s for s in str_items) and any("hello_world" in s for s in str_items):
                return True, str(obj)
        if isinstance(obj, dict):
            for v in obj.values():
                result, detail = find_tools_in_obj(v)
                if result:
                    return True, detail
        return False, ""
    
    # Also check if both tool names appear in any list-like structure
    add_mentioned = "add" in report_str
    hello_world_mentioned = "hello_world" in report_str
    
    if add_mentioned and hello_world_mentioned:
        tools_found = True
        tools_detail = "Both 'add' and 'hello_world' tool names present in report"
    
    check("tools_discovered", tools_found, tools_detail)

    # ── 4. Add Tool Result: 47 + 38 = 85 ──────────────────────────────────
    # Expected output from the tool: "47 + 38 = 85"
    add_result_correct = False
    add_detail = "Add result not found or incorrect"
    
    report_full_str = json.dumps(report, ensure_ascii=False)
    
    # The exact format from the server is: "47 + 38 = 85"
    if "47 + 38 = 85" in report_full_str:
        add_result_correct = True
        add_detail = "Exact add result '47 + 38 = 85' found in report"
    else:
        # Check if "85" is present at minimum (partial credit check)
        if "85" in report_full_str:
            add_detail = "Number 85 present but exact format '47 + 38 = 85' not found"
        else:
            add_detail = "Result for 47+38 not found in report"
    
    check("add_tool_result_correct", add_result_correct, add_detail)

    # ── 5. Hello World Tool Result ──────────────────────────────────────────
    # Expected output: "你好，审计员！👋 欢迎使用 MCP Hello World 服务器！"
    greet_result_correct = False
    greet_detail = "Greeting result not found or incorrect"
    
    expected_greeting = "你好，审计员！👋 欢迎使用 MCP Hello World 服务器！"
    
    if expected_greeting in report_full_str:
        greet_result_correct = True
        greet_detail = f"Exact greeting '{expected_greeting}' found in report"
    else:
        # Check partial matches
        if "审计员" in report_full_str:
            greet_detail = f"Name '审计员' present but exact greeting not found. Expected: '{expected_greeting}'"
        elif "你好" in report_full_str:
            greet_detail = "Greeting starts correctly but name '审计员' not found"
        else:
            greet_detail = "No greeting output found in report"
    
    check("hello_world_tool_result_correct", greet_result_correct, greet_detail)

    # ── 6. Verify actual tool invocation (not hardcoded) ───────────────────
    # The report should NOT contain the old template content
    not_template = True
    not_template_detail = "Report appears to be freshly generated"
    
    if "OUTDATED TEMPLATE" in report_full_str or "PENDING" in report_full_str:
        not_template = False
        not_template_detail = "Report still contains template/placeholder content"
    
    check("report_not_template", not_template, not_template_detail)

    # ── 7. Bonus: Report structure quality ─────────────────────────────────
    # Check that the report has reasonable structure (not just a flat string dump)
    has_structure = isinstance(report, dict) and len(report) >= 2
    check("report_has_structure", has_structure, 
          f"Report is a dict with {len(report) if isinstance(report, dict) else 'N/A'} top-level keys" if has_structure 
          else "Report lacks expected dict structure")

    # ── Scoring ─────────────────────────────────────────────────────────────
    weights = {
        "report_file_exists": 1,
        "report_valid_json": 1,
        "tools_discovered": 2,
        "add_tool_result_correct": 3,
        "hello_world_tool_result_correct": 3,
        "report_not_template": 1,
        "report_has_structure": 1,
    }
    
    total_weight = sum(weights.values())
    earned = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    score = earned / total_weight
    
    # Must pass core checks to overall pass
    core_passed = (
        checks[0]["passed"] and  # file exists
        checks[1]["passed"] and  # valid json
        checks[3]["passed"] and  # add result
        checks[4]["passed"]      # greeting result
    )
    
    return {
        "passed": core_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))