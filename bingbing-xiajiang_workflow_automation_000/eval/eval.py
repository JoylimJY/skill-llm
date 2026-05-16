import sys
import json
import os
from pathlib import Path

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def evaluate(workspace_dir):
    checks = []
    total_score = 0.0
    max_score = 10.0

    # Find the target file
    target_path = Path(workspace_dir) / "retail_project" / "reports" / "final" / "final_session_report.json"
    
    # Also search recursively in case agent put it somewhere else
    if not target_path.exists():
        candidates = list(Path(workspace_dir).rglob("final_session_report.json"))
        if candidates:
            target_path = candidates[0]

    if not target_path.exists():
        checks.append({"name": "file_exists", "passed": False, "detail": "final_session_report.json not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {target_path}"})

    try:
        report = load_json(target_path)
    except Exception as e:
        checks.append({"name": "json_valid", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "json_valid", "passed": True, "detail": "File is valid JSON"})

    # ---- CHECK 1: Correct Execution Path (Module1 → Module3 → Module4, NO Module2) ----
    # The user explicitly said no content creation → Module2 should be absent
    exec_path_str = ""
    try:
        # Accept various forms: list, string, nested dict
        ep = report.get("execution_path") or report.get("session_info", {}).get("execution_path", "")
        if isinstance(ep, list):
            exec_path_str = " -> ".join(str(x) for x in ep).lower()
        else:
            exec_path_str = str(ep).lower()
        
        has_module1 = "module_1" in exec_path_str or "module1" in exec_path_str or "模块1" in exec_path_str or "信息守护者" in exec_path_str
        has_module3 = "module_3" in exec_path_str or "module3" in exec_path_str or "模块3" in exec_path_str or "状态洞察" in exec_path_str
        has_module4 = "module_4" in exec_path_str or "module4" in exec_path_str or "模块4" in exec_path_str or "工作流" in exec_path_str
        has_module2 = "module_2" in exec_path_str or "module2" in exec_path_str or "模块2" in exec_path_str or "内容趋势" in exec_path_str or "content" in exec_path_str.lower()
        
        path_correct = has_module1 and has_module3 and has_module4 and not has_module2
        checks.append({
            "name": "correct_execution_path",
            "passed": path_correct,
            "detail": f"Execution path string: '{exec_path_str}'. Has M1:{has_module1}, M3:{has_module3}, M4:{has_module4}, Has M2(SHOULD BE FALSE):{has_module2}"
        })
        if path_correct:
            total_score += 2.0
    except Exception as e:
        checks.append({"name": "correct_execution_path", "passed": False, "detail": f"Error checking execution path: {e}"})

    # ---- CHECK 2: Adaptive Decisions correctly applied ----
    # skip_rate=0.72 > 0.60 → reduce_confirmations=True
    # preferred_style='concise' → output concise
    # acceptance_rate=0.82 > 0.70 → more_recommendations=True  
    # preferred_mode='parallel' → parallel execution
    try:
        adapt = report.get("adaptive_decisions") or report.get("user_adaptation") or report.get("adaptive_strategy") or {}
        
        # Check reduce confirmations
        reduce_confirm = adapt.get("reduce_confirmations") or adapt.get("skip_confirmations") or adapt.get("simplified_confirmation")
        if isinstance(reduce_confirm, bool):
            confirm_correct = reduce_confirm == True
        elif isinstance(reduce_confirm, str):
            confirm_correct = reduce_confirm.lower() in ("true", "yes", "enabled", "reduced", "简化确认")
        else:
            # Search in string representation
            adapt_str = json.dumps(adapt, ensure_ascii=False).lower()
            confirm_correct = any(kw in adapt_str for kw in ["reduce", "skip", "简化", "减少确认"])
        
        checks.append({
            "name": "adaptive_reduce_confirmation",
            "passed": confirm_correct,
            "detail": f"skip_rate=0.72 > 0.60 should trigger reduce_confirmations=True. Found: {adapt}"
        })
        if confirm_correct:
            total_score += 1.0

        # Check output style = concise
        style_val = adapt.get("output_style") or adapt.get("preferred_style") or adapt.get("output_preference") or ""
        if isinstance(style_val, str):
            style_correct = "concise" in style_val.lower() or "精简" in style_val or "简洁" in style_val
        else:
            adapt_str = json.dumps(adapt, ensure_ascii=False).lower()
            style_correct = "concise" in adapt_str or "精简" in adapt_str
        
        checks.append({
            "name": "adaptive_concise_output",
            "passed": style_correct,
            "detail": f"preferred_style='concise' should be reflected. Found style: {style_val}"
        })
        if style_correct:
            total_score += 1.0

        # Check more recommendations
        more_recs = adapt.get("more_recommendations") or adapt.get("increase_recommendations") or adapt.get("recommendation_mode")
        adapt_str = json.dumps(adapt, ensure_ascii=False).lower()
        if isinstance(more_recs, bool):
            recs_correct = more_recs == True
        elif isinstance(more_recs, str):
            recs_correct = more_recs.lower() in ("true", "yes", "more", "high", "多推荐")
        else:
            recs_correct = any(kw in adapt_str for kw in ["多推荐", "more_rec", "more rec", "increased", "acceptance_rate"])
        
        checks.append({
            "name": "adaptive_more_recommendations",
            "passed": recs_correct,
            "detail": f"acceptance_rate=0.82 > 0.70 should trigger more recommendations. adapt dict: {adapt}"
        })
        if recs_correct:
            total_score += 0.5

        # Check parallel execution
        exec_mode = adapt.get("execution_mode") or adapt.get("preferred_execution") or adapt.get("parallel_execution") or ""
        if isinstance(exec_mode, str):
            parallel_correct = "parallel" in exec_mode.lower() or "并行" in exec_mode
        elif isinstance(exec_mode, bool):
            parallel_correct = exec_mode == True
        else:
            parallel_correct = "parallel" in adapt_str or "并行" in adapt_str
        
        checks.append({
            "name": "adaptive_parallel_execution",
            "passed": parallel_correct,
            "detail": f"preferred_mode='parallel' should be reflected. Found: {exec_mode}"
        })
        if parallel_correct:
            total_score += 0.5

    except Exception as e:
        checks.append({"name": "adaptive_decisions_check", "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 3: Memory Layer Assignments ----
    # Module1: L0 primary, compress to L2
    # Module3: L3 → L4
    # Module4: L3 permanent (ttl_days: null)
    try:
        report_str = json.dumps(report, ensure_ascii=False).lower()
        
        # Module1 memory
        m1_l0 = ("l0" in report_str and ("module_1" in report_str or "module1" in report_str or "信息守护者" in report_str))
        m1_l2_compress = ("l2" in report_str and ("compress" in report_str or "l2" in report_str))
        
        # Module3 memory layers L3 and L4
        m3_l3 = "l3" in report_str
        m3_l4 = "l4" in report_str
        
        # Module4 permanent
        m4_permanent = ("null" in report_str or "permanent" in report_str or "永久" in report_str or "none" in report_str)
        
        memory_layers_ok = m1_l0 and m3_l3 and m3_l4 and m4_permanent
        checks.append({
            "name": "memory_layer_assignments",
            "passed": memory_layers_ok,
            "detail": f"M1→L0:{m1_l0}, M3→L3:{m3_l3}/L4:{m3_l4}, M4→permanent:{m4_permanent}"
        })
        if memory_layers_ok:
            total_score += 2.0
    except Exception as e:
        checks.append({"name": "memory_layer_assignments", "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 4: Reflection Mechanism present for each executed module ----
    # Each executed module should have reflection scores: completeness, quality, usability
    try:
        reflection_found = False
        # Look for reflection data in various possible locations
        def find_reflection(obj, depth=0):
            if depth > 5:
                return False
            if isinstance(obj, dict):
                keys_lower = {k.lower() for k in obj.keys()}
                if any(k in keys_lower for k in ["completeness", "完整性", "quality", "质量", "usability", "可用性"]):
                    return True
                for v in obj.values():
                    if find_reflection(v, depth+1):
                        return True
            elif isinstance(obj, list):
                for item in obj:
                    if find_reflection(item, depth+1):
                        return True
            return False
        
        reflection_found = find_reflection(report)
        
        # Also check string-based
        if not reflection_found:
            report_str_raw = json.dumps(report, ensure_ascii=False)
            reflection_found = any(kw in report_str_raw for kw in [
                "completeness", "完整性", "quality", "质量", "usability", "可用性", "reflection", "反思"
            ])
        
        checks.append({
            "name": "reflection_mechanism_present",
            "passed": reflection_found,
            "detail": "Reflection scores (completeness/quality/usability) should be present for each executed module"
        })
        if reflection_found:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "reflection_mechanism_present", "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 5: Memory Summary with correct layer counts ----
    # Executed: Module1 (L0+L2), Module3 (L3+L4), Module4 (L3 permanent)
    # So: stored_L0 >= 1, stored_L2 >= 1, stored_L3 >= 2 (M3+M4), stored_L4 >= 1
    try:
        mem_summary = report.get("memory_summary") or {}
        
        # Try to find memory summary nested
        if not mem_summary:
            for key in ["final_report", "session_summary", "summary"]:
                if key in report and isinstance(report[key], dict):
                    mem_summary = report[key].get("memory_summary", {})
                    if mem_summary:
                        break
        
        l0_count = mem_summary.get("stored_L0", mem_summary.get("L0", 0))
        l2_count = mem_summary.get("stored_L2", mem_summary.get("L2", 0))
        l3_count = mem_summary.get("stored_L3", mem_summary.get("L3", 0))
        l4_count = mem_summary.get("stored_L4", mem_summary.get("L4", 0))
        
        # Validate: L0 ≥ 1 (M1), L2 ≥ 1 (M1 compress), L3 ≥ 1 (M3 or M4), L4 ≥ 1 (M3)
        mem_correct = (
            isinstance(l0_count, (int, float)) and l0_count >= 1 and
            isinstance(l2_count, (int, float)) and l2_count >= 1 and
            isinstance(l3_count, (int, float)) and l3_count >= 1 and
            isinstance(l4_count, (int, float)) and l4_count >= 1
        )
        
        checks.append({
            "name": "memory_summary_counts",
            "passed": mem_correct,
            "detail": f"L0={l0_count}, L2={l2_count}, L3={l3_count}, L4={l4_count}. All should be ≥1 for M1+M3+M4 path."
        })
        if mem_correct:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "memory_summary_counts", "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 6: Session ID and User ID preserved from input ----
    try:
        session_id = str(report.get("session_id") or report.get("session_info", {}).get("session_id", ""))
        user_id = str(report.get("user_id") or report.get("session_info", {}).get("user_id", ""))
        
        sid_correct = "session_20260225_retail_007" in session_id
        uid_correct = "user_retail_007" in user_id
        
        checks.append({
            "name": "session_and_user_id_correct",
            "passed": sid_correct and uid_correct,
            "detail": f"session_id='{session_id}' (expected contains 'session_20260225_retail_007'), user_id='{user_id}' (expected 'user_retail_007')"
        })
        if sid_correct and uid_correct:
            total_score += 0.5
    except Exception as e:
        checks.append({"name": "session_and_user_id_correct", "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 7: Module1 output data preserved/referenced ----
    try:
        report_str_raw = json.dumps(report, ensure_ascii=False)
        m1_data_preserved = (
            "蜜雪冰城" in report_str_raw or
            "新茶饮" in report_str_raw or
            "36kr" in report_str_raw or
            "A_grade" in report_str_raw or
            "A级" in report_str_raw or
            "industry_trend" in report_str_raw
        )
        checks.append({
            "name": "module1_output_preserved",
            "passed": m1_data_preserved,
            "detail": "Module1's output data (industry info, grades) should be referenced in the final report"
        })
        if m1_data_preserved:
            total_score += 0.5
    except Exception as e:
        checks.append({"name": "module1_output_preserved", "passed": False, "detail": f"Error: {e}"})

    # Final pass/fail
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    final_passed = total_score >= 6.0  # Need at least 60% of max score

    return {
        "passed": final_passed,
        "score": round(total_score / max_score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))