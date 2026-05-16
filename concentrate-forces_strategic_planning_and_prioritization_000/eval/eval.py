import json
import sys
import os
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    
    # ── helper ──────────────────────────────────────────────────────────────
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

    # ── locate output file ───────────────────────────────────────────────────
    plan_files = list(Path(workspace_dir).rglob("execution_plan.json"))
    if not plan_files:
        add_check("file_exists", False, "execution_plan.json not found anywhere in workspace")
        return {"passed": False, "score": 0.0, "checks": checks}

    plan_path = plan_files[0]
    add_check("file_exists", True, f"Found at {plan_path}")

    try:
        with open(plan_path, "r", encoding="utf-8") as f:
            plan = json.load(f)
    except Exception as e:
        add_check("json_parseable", False, f"Could not parse JSON: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}
    add_check("json_parseable", True, "Valid JSON")

    # ── CHECK 1: Problem inventory / full enumeration ────────────────────────
    # The agent must enumerate all 8 initiatives (Step 1 of skill)
    try:
        inventory_field = None
        for key in ["problem_inventory", "initiatives_inventory", "all_problems", "problems", "inventory"]:
            if key in plan:
                inventory_field = plan[key]
                break
        # Also search nested
        if inventory_field is None:
            for v in plan.values():
                if isinstance(v, list) and len(v) >= 8:
                    inventory_field = v
                    break
        
        if inventory_field and len(inventory_field) >= 8:
            add_check("full_problem_inventory", True, f"All 8 initiatives enumerated ({len(inventory_field)} items found)")
        elif inventory_field:
            add_check("full_problem_inventory", False, f"Only {len(inventory_field)} of 8 initiatives listed — must enumerate ALL problems first")
        else:
            # Check if referenced by ID anywhere in the plan text
            plan_str = json.dumps(plan)
            ids_found = sum(1 for i in range(1, 9) if f"INIT-00{i}" in plan_str)
            if ids_found >= 6:
                add_check("full_problem_inventory", True, f"All initiative IDs referenced in plan ({ids_found}/8)")
            else:
                add_check("full_problem_inventory", False, f"Full problem inventory missing or incomplete ({ids_found}/8 IDs referenced)")
    except Exception as e:
        add_check("full_problem_inventory", False, f"Error checking inventory: {e}")

    # ── CHECK 2: Primary contradiction correctly identified ──────────────────
    # Per skill Step 2: identify the PRIMARY contradiction — the one that unlocks others
    # Correct answer: INIT-003 (Auth Service Refactor) is the primary contradiction
    # because it BLOCKS both INIT-001 and INIT-006, and is also prerequisite for INIT-004
    # A secondary acceptable answer: INIT-002 (DB Optimization) blocks INIT-007, INIT-008
    # INIT-003 is the TRUE primary contradiction because it has no deps and blocks the most
    try:
        plan_str = json.dumps(plan).lower()
        
        primary_field = None
        for key in ["primary_contradiction", "main_contradiction", "primary_problem", 
                    "key_problem", "core_problem", "main_target", "primary_target"]:
            if key in plan:
                primary_field = str(plan[key])
                break
        
        # Search nested
        if primary_field is None:
            def find_primary(obj, depth=0):
                if depth > 5:
                    return None
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if any(word in k.lower() for word in ["primary", "main", "core", "key", "principal", "major"]):
                            if isinstance(v, (str, dict)):
                                return str(v)
                        result = find_primary(v, depth+1)
                        if result:
                            return result
                elif isinstance(obj, list):
                    for item in obj:
                        result = find_primary(item, depth+1)
                        if result:
                            return result
                return None
            primary_field = find_primary(plan)
        
        if primary_field and ("init-003" in primary_field.lower() or "auth" in primary_field.lower()):
            add_check("primary_contradiction_identified", True, 
                     "INIT-003 (Auth Service Refactor) correctly identified as primary contradiction — it blocks INIT-001, INIT-006, and INIT-004")
        elif primary_field and ("init-002" in primary_field.lower() or "database" in primary_field.lower() or "db" in primary_field.lower() or "query" in primary_field.lower()):
            add_check("primary_contradiction_identified", True, 
                     "INIT-002 (DB Optimization) accepted as primary contradiction — it blocks INIT-007 and INIT-008 and has no dependencies")
        else:
            # Check if plan_str mentions INIT-003 prominently near words like primary/main/focus/first
            import re
            context_match = re.search(r'(init.?003|auth).{0,200}(primary|main|first|focus|primary|主要|核心)', plan_str)
            context_match2 = re.search(r'(primary|main|first|focus|主要|核心).{0,200}(init.?003|auth)', plan_str)
            if context_match or context_match2:
                add_check("primary_contradiction_identified", True, 
                         "INIT-003 identified as primary focus in context")
            else:
                detail = f"Primary contradiction unclear or incorrect. Found: '{primary_field}'. Expected INIT-003 (Auth Refactor) or INIT-002 (DB Optimization)"
                add_check("primary_contradiction_identified", False, detail)
    except Exception as e:
        add_check("primary_contradiction_identified", False, f"Error: {e}")

    # ── CHECK 3: Breakthrough ordering follows skill's specific principles ────
    # Skill mandates: 先孤后强 (isolated/no-deps first), 先易后难, readiness check
    # Phase 1 MUST be one of the no-dependency, high-isolation, ready initiatives:
    # Best candidates: INIT-005 (CI/CD, effort=8, isolation=9, ready=True, no deps)
    #                  INIT-002 (DB Opt, effort=13, isolation=8, ready=True, no deps)
    #                  INIT-003 (Auth, effort=21, isolation=6, ready=True, no deps) - primary contradiction
    # WRONG first choice: INIT-001 (has deps), INIT-004 (not ready), INIT-006 (has deps, not ready)
    try:
        plan_str_orig = json.dumps(plan)
        plan_str_low = plan_str_orig.lower()
        
        # Find phases or sequence
        phases = None
        for key in ["phases", "execution_phases", "sequence", "plan_phases", "steps"]:
            if key in plan and isinstance(plan[key], list):
                phases = plan[key]
                break
        
        first_phase_correct = False
        first_phase_detail = "Could not determine first phase"
        
        if phases and len(phases) > 0:
            first = phases[0]
            first_str = json.dumps(first).lower()
            # Good first choices (no deps, ready, isolated)
            good_first = ["init-005", "init-002", "init-003", "ci/cd", "ci_cd", "database", "db opt", 
                         "auth", "query optim", "pipeline", "stabiliz"]
            bad_first = ["init-001", "init-004", "init-006", "init-008", "sso", "saml", 
                        "api v2", "graphql", "security audit", "multi-tenant", "dashboard"]
            
            if any(g in first_str for g in good_first):
                first_phase_correct = True
                first_phase_detail = f"First phase correctly targets an isolated, ready initiative: {first_str[:100]}"
            elif any(b in first_str for b in bad_first):
                first_phase_correct = False
                first_phase_detail = f"First phase incorrectly targets dependent/unready initiative: {first_str[:100]}"
            else:
                first_phase_correct = False
                first_phase_detail = f"First phase unclear: {first_str[:100]}"
        else:
            # No explicit phases array — look for ordering logic in text
            import re
            # Check if INIT-001/INIT-006/INIT-004 are stated as first/phase1
            wrong_first = re.search(r'(phase.?1|first.?phase|step.?1).{0,300}(init.?001|init.?004|init.?006|sso|graphql|security audit)', plan_str_low)
            good_order = re.search(r'(phase.?1|first.?phase|step.?1).{0,300}(init.?002|init.?003|init.?005|auth|database|ci.cd|pipeline)', plan_str_low)
            if good_order and not wrong_first:
                first_phase_correct = True
                first_phase_detail = "Ordering text suggests correct isolated-first principle"
            else:
                first_phase_correct = False
                first_phase_detail = "Could not confirm correct ordering — 先孤后强 principle may not be applied"
        
        add_check("breakthrough_ordering_correct", first_phase_correct, first_phase_detail)
    except Exception as e:
        add_check("breakthrough_ordering_correct", False, f"Error: {e}")

    # ── CHECK 4: "All-in" / no-parallelism principle (集中绝对优势兵力) ────────
    # Skill says: "同一时间只聚焦一个核心问题" — must commit ALL resources to ONE task
    # The plan must NOT suggest splitting the 3 engineers across multiple concurrent tasks in Phase 1
    try:
        plan_str_low = json.dumps(plan).lower()
        
        # Look for explicit single-focus commitment
        single_focus_signals = [
            "all.*engineer", "all 3", "all three", "entire team", "100%", 
            "全部", "所有工程师", "集中", "单一", "one task", "one initiative",
            "parallelism.*false", "parallel.*false", "no parallel",
            "not parallel", "not split", "do not split", "avoid split",
            "focus.*single", "single.*focus", "concentrate all",
            "full.*team.*on", "team.*on.*one"
        ]
        import re
        focus_found = any(re.search(pattern, plan_str_low) for pattern in single_focus_signals)
        
        # Also check for anti-patterns (splitting engineers in phase 1)
        split_antipatterns = [
            r'alice.*init-00[1-9].*bob.*init-00[1-9]',  # different tasks same time
            r'concurrent.*init',
            r'simultaneously.*init',
            r'parallel.*track',
            r'two.*teams.*simultaneously',
            r'split.*between',
        ]
        split_found = any(re.search(pat, plan_str_low) for pat in split_antipatterns)
        
        # Check for parallelism=false or equivalent field
        parallelism_field = None
        def find_parallelism(obj, depth=0):
            if depth > 6:
                return None
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if "parallel" in k.lower() or "concurrent" in k.lower() or "split" in k.lower():
                        return (k, v)
                    r = find_parallelism(v, depth+1)
                    if r:
                        return r
            elif isinstance(obj, list):
                for item in obj:
                    r = find_parallelism(item, depth+1)
                    if r:
                        return r
            return None
        
        parallelism_field = find_parallelism(plan)
        
        if parallelism_field:
            k, v = parallelism_field
            # False/no/0 means no parallelism → correct
            if str(v).lower() in ["false", "no", "0", "none", "禁止", "不"]:
                add_check("all_in_commitment", True, 
                         f"Explicit no-parallelism commitment found: {k}={v}")
            else:
                add_check("all_in_commitment", False if split_found else True,
                         f"Parallelism field found but value is '{v}' — ambiguous")
        elif focus_found and not split_found:
            add_check("all_in_commitment", True, 
                     "Single-focus/all-in language detected without splitting anti-pattern")
        elif split_found:
            add_check("all_in_commitment", False, 
                     "Plan appears to split engineers across multiple concurrent tasks — violates 集中绝对优势兵力")
        else:
            add_check("all_in_commitment", False, 
                     "No explicit single-focus commitment found — 集中绝对优势兵力 principle not clearly applied")
    except Exception as e:
        add_check("all_in_commitment", False, f"Error: {e}")

    # ── CHECK 5: Readiness check per target (不打无准备之仗) ─────────────────
    # Each phase/target must include a readiness assessment before committing
    try:
        plan_str_low = json.dumps(plan).lower()
        import re
        
        readiness_signals = [
            "readiness", "prepared", "preparation", "ready",
            "not.*ready", "pre.*condition", "prerequisite",
            "无准备", "有准备", "准备", "prepare",
            "spec.*complete", "expertise", "blocker",
            "before.*start", "before.*begin", "check.*before"
        ]
        readiness_found = sum(1 for sig in readiness_signals if sig in plan_str_low)
        
        # Look for explicit readiness check structure
        readiness_field_found = False
        def has_readiness_field(obj, depth=0):
            if depth > 6:
                return False
            if isinstance(obj, dict):
                for k in obj.keys():
                    if any(r in k.lower() for r in ["ready", "readiness", "prepared", "preparation", "pre_check", "prereq"]):
                        return True
                for v in obj.values():
                    if has_readiness_field(v, depth+1):
                        return True
            elif isinstance(obj, list):
                for item in obj:
                    if has_readiness_field(item, depth+1):
                        return True
            return False
        
        readiness_field_found = has_readiness_field(plan)
        
        if readiness_field_found:
            add_check("readiness_checks_present", True, 
                     "Explicit readiness check fields found in plan structure")
        elif readiness_found >= 3:
            add_check("readiness_checks_present", True, 
                     f"Readiness assessment language found ({readiness_found} signals) — 不打无准备之仗 applied")
        else:
            add_check("readiness_checks_present", False, 
                     f"Insufficient readiness checks — 不打无准备之仗 principle requires explicit go/no-go assessment per phase (found {readiness_found} signals, need >=3)")
    except Exception as e:
        add_check("readiness_checks_present", False, f"Error: {e}")

    # ── CHECK 6: Self-review/retrospective checkpoint between phases ──────────
    # Skill Step 5: "短暂总结经验 (调用 criticism-self-criticism)" between phases
    try:
        plan_str_low = json.dumps(plan).lower()
        
        retrospective_signals = [
            "retrospect", "review", "self.*critic", "self-critic", 
            "lessons.*learned", "summary", "reflect", "assess.*after",
            "after.*complet", "interval", "pause", "between.*phase",
            "总结", "复盘", "批评", "自我批评", "经验", "回顾",
            "post.*phase", "checkpoint", "debrief", "evaluate.*result"
        ]
        retro_found = sum(1 for sig in retrospective_signals if sig in plan_str_low)
        
        if retro_found >= 2:
            add_check("inter_phase_retrospective", True, 
                     f"Inter-phase retrospective/self-review checkpoint present ({retro_found} signals found)")
        else:
            add_check("inter_phase_retrospective", False, 
                     f"No inter-phase self-review checkpoint found — skill requires 短暂总结经验 between phases ({retro_found} signals, need >=2)")
    except Exception as e:
        add_check("inter_phase_retrospective", False, f"Error: {e}")

    # ── CHECK 7: Plan covers multiple sequential phases (not just 1 task) ─────
    try:
        plan_str_low = json.dumps(plan).lower()
        
        phases_list = None
        for key in ["phases", "execution_phases", "sequence", "plan_phases", "steps", "tasks"]:
            if key in plan and isinstance(plan[key], list) and len(plan[key]) >= 2:
                phases_list = plan[key]
                break
        
        if phases_list and len(phases_list) >= 3:
            add_check("sequential_multi_phase_plan", True, 
                     f"Plan has {len(phases_list)} sequential phases — covers full initiative backlog")
        elif phases_list and len(phases_list) == 2:
            add_check("sequential_multi_phase_plan", True, 
                     "Plan has 2 phases minimum — sequential structure present")
        else:
            # Check for phase mentions in text
            import re
            phase_matches = re.findall(r'phase\s*[123456]|step\s*[123456]|阶段\s*[一二三四五六1-6]', plan_str_low)
            if len(set(phase_matches)) >= 2:
                add_check("sequential_multi_phase_plan", True, 
                         f"Multiple sequential phases referenced in text: {set(phase_matches)}")
            else:
                add_check("sequential_multi_phase_plan", False, 
                         "Plan appears to address only one phase — must sequence ALL initiatives across multiple phases")
    except Exception as e:
        add_check("sequential_multi_phase_plan", False, f"Error: {e}")

    # ── SCORING ──────────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)
    overall_passed = score >= 0.75  # Must pass at least 6/8 checks

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))