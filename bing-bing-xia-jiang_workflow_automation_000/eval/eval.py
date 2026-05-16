import sys
import json
import math
from pathlib import Path

def find_session_plan(workspace):
    """Find session_plan.json anywhere in workspace."""
    candidates = list(Path(workspace).rglob("session_plan.json"))
    return candidates[0] if candidates else None

def evaluate(workspace):
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, max_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        max_score += weight
        if passed:
            total_score += weight

    # Find the output file
    plan_path = find_session_plan(workspace)
    if plan_path is None:
        add_check("session_plan.json exists", False, "File session_plan.json not found anywhere in workspace.", weight=2.0)
        return checks, 0.0, max_score

    add_check("session_plan.json exists", True, f"Found at {plan_path}", weight=2.0)

    # Load the file
    try:
        with open(plan_path, 'r', encoding='utf-8') as f:
            plan = json.load(f)
    except Exception as e:
        add_check("session_plan.json is valid JSON", False, f"JSON parse error: {e}", weight=2.0)
        return checks, 0.0, max_score

    add_check("session_plan.json is valid JSON", True, "Parsed successfully.", weight=2.0)

    # ── CHECK 1: UserProfile normalization ─────────────────────────────────
    # Expected derived values from raw data:
    # skip_rate = 28/40 = 0.70
    # preferred_style = 'detailed' (31 vs 9)
    # acceptance_rate = 20/25 = 0.80
    # preferred_mode = 'parallel' (33 vs 7)

    profile = plan.get("user_profile", plan.get("normalized_profile", plan.get("profile", {})))

    # skip_rate
    try:
        ch = profile.get("confirmation_habit", {})
        skip_rate = ch.get("skip_rate", None)
        if skip_rate is not None and abs(float(skip_rate) - 0.70) < 0.02:
            add_check("UserProfile: skip_rate computed correctly (28/40=0.70)", True,
                      f"Got {skip_rate}", weight=1.5)
        else:
            add_check("UserProfile: skip_rate computed correctly (28/40=0.70)", False,
                      f"Expected ~0.70, got {skip_rate}", weight=1.5)
    except Exception as e:
        add_check("UserProfile: skip_rate computed correctly (28/40=0.70)", False, str(e), weight=1.5)

    # preferred_style
    try:
        op = profile.get("output_preference", {})
        pref_style = op.get("preferred_style", None)
        if pref_style == "detailed":
            add_check("UserProfile: preferred_style='detailed'", True, f"Got '{pref_style}'", weight=1.5)
        else:
            add_check("UserProfile: preferred_style='detailed'", False,
                      f"Expected 'detailed', got '{pref_style}'", weight=1.5)
    except Exception as e:
        add_check("UserProfile: preferred_style='detailed'", False, str(e), weight=1.5)

    # acceptance_rate
    try:
        rec = profile.get("recommendation", {})
        acc_rate = rec.get("acceptance_rate", None)
        if acc_rate is not None and abs(float(acc_rate) - 0.80) < 0.02:
            add_check("UserProfile: acceptance_rate computed correctly (20/25=0.80)", True,
                      f"Got {acc_rate}", weight=1.5)
        else:
            add_check("UserProfile: acceptance_rate computed correctly (20/25=0.80)", False,
                      f"Expected ~0.80, got {acc_rate}", weight=1.5)
    except Exception as e:
        add_check("UserProfile: acceptance_rate computed correctly (20/25=0.80)", False, str(e), weight=1.5)

    # preferred_mode
    try:
        exe = profile.get("execution", {})
        pref_mode = exe.get("preferred_mode", None)
        if pref_mode == "parallel":
            add_check("UserProfile: preferred_mode='parallel'", True, f"Got '{pref_mode}'", weight=1.5)
        else:
            add_check("UserProfile: preferred_mode='parallel'", False,
                      f"Expected 'parallel', got '{pref_mode}'", weight=1.5)
    except Exception as e:
        add_check("UserProfile: preferred_mode='parallel'", False, str(e), weight=1.5)

    # user_id preserved
    try:
        uid = profile.get("user_id", None)
        if uid == "user_med_007":
            add_check("UserProfile: user_id='user_med_007'", True, "Correct.", weight=0.5)
        else:
            add_check("UserProfile: user_id='user_med_007'", False, f"Got '{uid}'", weight=0.5)
    except Exception as e:
        add_check("UserProfile: user_id='user_med_007'", False, str(e), weight=0.5)

    # ── CHECK 2: Adaptive Strategy Decisions ───────────────────────────────
    # skip_rate = 0.70 > 0.60 → reduce confirmation steps
    # preferred_style = 'detailed' → output detailed reports
    # acceptance_rate = 0.80 > 0.70 → more recommendations
    # preferred_mode = 'parallel' → prefer parallel execution

    decisions_raw = plan.get("adaptive_decisions", plan.get("adaptive_strategy", plan.get("decisions", [])))
    decisions_str = json.dumps(decisions_raw, ensure_ascii=False).lower()

    # reduce confirmation
    reduce_confirm_keywords = ["减少确认", "reduce confirm", "skip confirmation", "简化确认", "减少确认步骤", "fewer confirm"]
    reduce_confirm_found = any(k in decisions_str for k in reduce_confirm_keywords)
    add_check("Adaptive: skip_rate>60% → reduce confirmation steps", reduce_confirm_found,
              f"Expected mention of reduced/simplified confirmation. decisions_str snippet: {decisions_str[:300]}", weight=2.0)

    # detailed output
    detailed_keywords = ["详细", "detailed", "more detail", "完整报告"]
    detailed_found = any(k in decisions_str for k in detailed_keywords)
    add_check("Adaptive: preferred_style=detailed → detailed output", detailed_found,
              f"Expected mention of detailed output. decisions_str snippet: {decisions_str[:300]}", weight=1.5)

    # more recommendations
    more_rec_keywords = ["多推荐", "more recommend", "增加推荐", "推荐接受", "higher recommend"]
    more_rec_found = any(k in decisions_str for k in more_rec_keywords)
    add_check("Adaptive: acceptance_rate>70% → more recommendations", more_rec_found,
              f"Expected mention of more recommendations. decisions_str snippet: {decisions_str[:300]}", weight=1.5)

    # parallel execution
    parallel_keywords = ["并行", "parallel"]
    parallel_found = any(k in decisions_str for k in parallel_keywords)
    add_check("Adaptive: preferred_mode=parallel → parallel execution", parallel_found,
              f"Expected mention of parallel execution. decisions_str snippet: {decisions_str[:300]}", weight=1.5)

    # ── CHECK 3: Execution Path ────────────────────────────────────────────
    # User intent: monitor medical device industry trends (Module 1) + create content for education (Module 2)
    # Correct execution path: Module1 → Module2
    # Module 3 (personal status) and Module 4 (workflow) are NOT mentioned in the request

    exec_path_raw = plan.get("execution_path", plan.get("module_sequence", plan.get("workflow_path", [])))

    exec_path_str = ""
    if isinstance(exec_path_raw, list):
        exec_path_str = json.dumps(exec_path_raw, ensure_ascii=False).lower()
    else:
        exec_path_str = str(exec_path_raw).lower()

    # Module 1 must be present and first
    module1_keywords = ["module_1", "module1", "模块1", "信息守护者", "ai信息守护者", "ai-information-guardian"]
    module1_found = any(k in exec_path_str for k in module1_keywords)
    add_check("Execution path: Module 1 included (must be first)", module1_found,
              f"Module 1 must be in path. Got: {exec_path_str[:200]}", weight=2.0)

    # Module 2 must be present
    module2_keywords = ["module_2", "module2", "模块2", "内容趋势", "content-trend", "内容军师"]
    module2_found = any(k in exec_path_str for k in module2_keywords)
    add_check("Execution path: Module 2 included (content creation intent)", module2_found,
              f"Module 2 must be in path for content creation. Got: {exec_path_str[:200]}", weight=2.0)

    # Module 3 should NOT be in the execution path (user didn't mention personal status analysis)
    module3_keywords = ["module_3", "module3", "模块3", "状态洞察", "status-insight"]
    module3_found = any(k in exec_path_str for k in module3_keywords)
    add_check("Execution path: Module 3 NOT included (not in user intent)", not module3_found,
              f"Module 3 should not be in path. Got: {exec_path_str[:200]}", weight=1.5)

    # Module 4 should NOT be in the execution path
    module4_keywords = ["module_4", "module4", "模块4", "工作流沉淀", "workflow-publisher"]
    module4_found = any(k in exec_path_str for k in module4_keywords)
    add_check("Execution path: Module 4 NOT included (not in user intent)", not module4_found,
              f"Module 4 should not be in path. Got: {exec_path_str[:200]}", weight=1.5)

    # ── CHECK 4: Context object with memory layer assignments ──────────────
    # Per data-flow.md:
    # Module1: memory_layer=L0, compress_target=L2, retention=1小时 (1 hour)
    # Module2: memory_layer=L2, compress_target=L3, retention=7天 (7 days)

    ctx = plan.get("context", plan.get("session_context", {}))
    mod_outputs = ctx.get("module_outputs", plan.get("module_outputs", {}))

    # Try to find module 1 output info
    m1_data = None
    for key in ["module_1", "module1", "1"]:
        if key in mod_outputs:
            m1_data = mod_outputs[key]
            break

    if m1_data:
        # memory_layer should be L0
        ml1 = str(m1_data.get("memory_layer", "")).upper()
        add_check("Context: Module1 memory_layer=L0", "L0" in ml1,
                  f"Expected L0, got '{ml1}'", weight=2.0)
        # retention should indicate 1 hour
        ret1 = str(m1_data.get("retention", ""))
        ret1_ok = "1" in ret1 and ("小时" in ret1 or "hour" in ret1.lower() or "hr" in ret1.lower())
        add_check("Context: Module1 retention=1小时", ret1_ok,
                  f"Expected '1小时' or '1 hour', got '{ret1}'", weight=1.5)
        # compress_target should be L2
        ct1 = str(m1_data.get("compress_target", "")).upper()
        add_check("Context: Module1 compress_target=L2", "L2" in ct1,
                  f"Expected L2, got '{ct1}'", weight=1.5)
    else:
        add_check("Context: Module1 output entry present", False,
                  f"No module_1 entry found in module_outputs. Keys: {list(mod_outputs.keys())}", weight=5.0)

    # Try to find module 2 output info
    m2_data = None
    for key in ["module_2", "module2", "2"]:
        if key in mod_outputs:
            m2_data = mod_outputs[key]
            break

    if m2_data:
        # memory_layer should be L2
        ml2 = str(m2_data.get("memory_layer", "")).upper()
        add_check("Context: Module2 memory_layer=L2", "L2" in ml2,
                  f"Expected L2, got '{ml2}'", weight=2.0)
        # retention should indicate 7 days
        ret2 = str(m2_data.get("retention", ""))
        ret2_ok = "7" in ret2 and ("天" in ret2 or "day" in ret2.lower())
        add_check("Context: Module2 retention=7天", ret2_ok,
                  f"Expected '7天' or '7 days', got '{ret2}'", weight=1.5)
    else:
        add_check("Context: Module2 output entry present", False,
                  f"No module_2 entry found in module_outputs. Keys: {list(mod_outputs.keys())}", weight=3.5)

    # ── CHECK 5: Session/user metadata ─────────────────────────────────────
    session_id_present = bool(
        ctx.get("session_id") or
        plan.get("session_id") or
        plan.get("session_info", {}).get("session_id")
    )
    add_check("Context: session_id present", session_id_present,
              "session_id should be present in context or plan root.", weight=0.5)

    user_id_in_ctx = (
        ctx.get("user_id") == "user_med_007" or
        plan.get("user_id") == "user_med_007"
    )
    add_check("Context: user_id='user_med_007' in context", user_id_in_ctx,
              f"user_id should be 'user_med_007' in context.", weight=0.5)

    # ── Final scoring ──────────────────────────────────────────────────────
    score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    overall_passed = score >= 0.75

    return checks, score, overall_passed

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks, score, overall_passed = evaluate(workspace)
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()