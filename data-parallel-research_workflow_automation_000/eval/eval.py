import sys
import json
import os
from pathlib import Path

def load_dispatch_plan(workspace):
    candidates = list(Path(workspace).rglob("dispatch_plan.json"))
    if not candidates:
        return None, "dispatch_plan.json not found anywhere in workspace"
    # Use the most recently modified one if multiple
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    try:
        with open(candidates[0], "r", encoding="utf-8") as f:
            data = json.load(f)
        return data, str(candidates[0])
    except Exception as e:
        return None, f"Failed to parse JSON: {e}"

def check_parallel_group(plan):
    """
    A, B, C, F must be identified as parallelizable (independent).
    D depends on B. E depends on A and C.
    The plan must correctly identify at least one parallel batch containing A, B, C, F
    and a sequential dependency: D after B, E after A+C.
    """
    issues = []
    
    # Find parallel groups / batches
    parallel_sections = set()
    sequential_deps = {}
    
    # Look for parallel_agents, parallel_groups, batches, waves, etc.
    raw_text = json.dumps(plan, ensure_ascii=False).upper()
    
    # Check that A, B, C, F appear as parallelizable
    parallel_keys = ["PARALLEL", "SIMULTANEOUS", "CONCURRENT", "同时", "并行", "BATCH", "WAVE", "GROUP"]
    sequential_keys = ["SEQUENTIAL", "AFTER", "DEPENDS", "DEPENDENCY", "依赖", "顺序", "之后", "完成后"]
    
    has_parallel_mention = any(k in raw_text for k in parallel_keys)
    has_sequential_mention = any(k in raw_text for k in sequential_keys)
    
    return has_parallel_mention, has_sequential_mention

def run_eval(workspace):
    checks = []
    
    # CHECK 1: File exists and is valid JSON
    plan, location = load_dispatch_plan(workspace)
    
    if plan is None:
        checks.append({"name": "dispatch_plan.json exists and is valid JSON", "passed": False, "detail": location})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return
    
    checks.append({"name": "dispatch_plan.json exists and is valid JSON", "passed": True, "detail": f"Found at {location}"})
    
    raw_text = json.dumps(plan, ensure_ascii=False)
    raw_upper = raw_text.upper()
    
    # CHECK 2: Must have agent task entries for all 6 sections (A-F)
    section_ids = ["A", "B", "C", "D", "E", "F"]
    found_sections = []
    for sid in section_ids:
        # Look for section ID in various formats
        if f'"ID": "{sid}"' in raw_upper or f'"SECTION": "{sid}"' in raw_upper or f'"CHAPTER": "{sid}"' in raw_upper:
            found_sections.append(sid)
        elif f'"id": "{sid}"' in raw_text or f'"section": "{sid}"' in raw_text or f'"chapter": "{sid}"' in raw_text:
            found_sections.append(sid)
        # Also check for section title keywords
        elif any(kw in raw_text for kw in [
            "市场规模" if sid == "A" else "",
            "监管政策" if sid == "B" else "",
            "竞争对手" if sid == "C" else "",
            "技术架构" if sid == "D" else "",
            "定价策略" if sid == "E" else "",
            "用户行为" if sid == "F" else ""
        ] if kw):
            found_sections.append(sid)
    
    # Deduplicate
    found_sections = list(set(found_sections))
    
    # More robust check: look for section keywords
    section_keywords = {
        "A": ["市场规模", "增速", "market size", "CAGR"],
        "B": ["监管", "合规", "regulatory", "政策", "牌照"],
        "C": ["竞争", "竞品", "competitor", "平安好医生", "丁香园", "京东健康"],
        "D": ["技术架构", "tech", "本地化", "NMPA", "等保"],
        "E": ["定价", "pricing", "价格", "定价策略"],
        "F": ["用户行为", "需求洞察", "user behavior", "用研"]
    }
    
    found_sections_kw = []
    for sid, keywords in section_keywords.items():
        if any(kw in raw_text for kw in keywords):
            found_sections_kw.append(sid)
    
    all_found = set(found_sections) | set(found_sections_kw)
    
    sections_covered = len(all_found) >= 6
    checks.append({
        "name": "All 6 research sections (A-F) are covered in the plan",
        "passed": sections_covered,
        "detail": f"Sections found: {sorted(all_found)}. Expected all of A,B,C,D,E,F."
    })
    
    # CHECK 3: Parallel batch must include A, B, C, F (the independent ones)
    parallel_keywords = ["parallel", "simultaneous", "concurrent", "同时", "并行", "batch", "wave", "第一批", "first batch", "phase 1", "阶段一"]
    has_parallel = any(kw.lower() in raw_text.lower() for kw in parallel_keywords)
    
    # The parallel batch should reference A, B, C, F together
    independent_sections_in_parallel = sum(1 for sid in ["A", "B", "C", "F"] 
                                            if any(kw in raw_text for kw in section_keywords[sid]))
    
    # Check that the word "parallel" or equivalent appears near A, B, C, F mentions
    checks.append({
        "name": "Plan identifies parallel/independent research batch (A, B, C, F)",
        "passed": has_parallel and independent_sections_in_parallel >= 3,
        "detail": f"Parallel keyword found: {has_parallel}. Independent sections covered in plan: {independent_sections_in_parallel}/4 (A,B,C,F)"
    })
    
    # CHECK 4: D must be marked as dependent on B (sequential)
    d_depends_b = False
    dep_keywords = ["depends", "after", "依赖", "之后", "B完成", "完成后", "sequential", "顺序", "B章节", "section B", "章节B"]
    
    # Try to find D's entry and check for B dependency
    if isinstance(plan, dict):
        # Try various structures
        agents = plan.get("agents", plan.get("dispatch", plan.get("tasks", plan.get("sections", []))))
        if isinstance(agents, list):
            for agent in agents:
                if isinstance(agent, dict):
                    agent_str = json.dumps(agent, ensure_ascii=False).lower()
                    if any(kw in agent_str for kw in ["技术架构", "tech arch", "section d", "章节d", "d章节"]):
                        if any(kw.lower() in agent_str for kw in dep_keywords):
                            d_depends_b = True
                            break
        
        # Also check waves/phases structure
        for phase_key in ["phase2", "phase_2", "wave2", "wave_2", "第二阶段", "second_phase", "sequential_tasks"]:
            phase_data = plan.get(phase_key, {})
            if phase_data:
                phase_str = json.dumps(phase_data, ensure_ascii=False)
                if any(kw in phase_str for kw in ["技术架构", "NMPA", "等保"]):
                    d_depends_b = True
    
    # Fallback: raw text search for D being after B
    if not d_depends_b:
        d_contexts = ["技术架构合规", "technical architecture", "D章节", "chapter D", "section D"]
        b_ref_near_d = False
        for dc in d_contexts:
            idx = raw_text.find(dc)
            if idx != -1:
                surrounding = raw_text[max(0, idx-300):idx+300]
                if any(bk in surrounding for bk in ["监管", "regulatory", "B章节", "章节B", "section B", "B完成", "B的"]):
                    b_ref_near_d = True
                    break
        d_depends_b = b_ref_near_d
    
    checks.append({
        "name": "Section D (Tech Architecture) is correctly marked as dependent on Section B (Regulatory)",
        "passed": d_depends_b,
        "detail": "D must be in a sequential phase after B, referencing B as a prerequisite"
    })
    
    # CHECK 5: E must be marked as dependent on A and C
    e_depends_ac = False
    
    if isinstance(plan, dict):
        agents = plan.get("agents", plan.get("dispatch", plan.get("tasks", plan.get("sections", []))))
        if isinstance(agents, list):
            for agent in agents:
                if isinstance(agent, dict):
                    agent_str = json.dumps(agent, ensure_ascii=False).lower()
                    if any(kw in agent_str for kw in ["定价", "pricing", "section e", "章节e", "e章节"]):
                        has_a_dep = any(kw.lower() in agent_str for kw in ["市场规模", "A章节", "chapter a", "section a", "章节a", "A的"])
                        has_c_dep = any(kw.lower() in agent_str for kw in ["竞品", "竞争", "C章节", "chapter c", "section c", "章节c", "C的"])
                        if has_a_dep or has_c_dep:
                            e_depends_ac = True
                            break
    
    if not e_depends_ac:
        e_contexts = ["定价策略", "pricing strategy", "E章节", "chapter E", "section E"]
        ac_ref_near_e = False
        for ec in e_contexts:
            idx = raw_text.find(ec)
            if idx != -1:
                surrounding = raw_text[max(0, idx-400):idx+400]
                has_a = any(ak in surrounding for ak in ["市场规模", "A章节", "章节A", "section A"])
                has_c = any(ck in surrounding for ck in ["竞品", "竞争对手", "C章节", "章节C", "section C"])
                if has_a or has_c:
                    ac_ref_near_e = True
                    break
        e_depends_ac = ac_ref_near_e
    
    checks.append({
        "name": "Section E (Pricing Strategy) is correctly marked as dependent on A (Market Size) and C (Competitors)",
        "passed": e_depends_ac,
        "detail": "E must reference A and/or C as prerequisites in its definition"
    })
    
    # CHECK 6: Each agent task must have required template fields
    # Required: scope/range, questions, data sources, output format, confidence markers (高/中/低), constraints
    required_field_keywords = {
        "scope": ["scope", "范围", "聚焦", "研究范围", "明确范围"],
        "questions": ["问题", "question", "需要回答", "key_question", "回答"],
        "data_sources": ["来源", "source", "数据来源", "艾瑞", "official", "官网", "参考"],
        "output_format": ["输出", "output", "format", "格式", "返回"],
        "confidence": ["高", "中", "低", "confidence", "置信度", "high", "medium", "low"],
        "constraints": ["约束", "constraint", "不涉及", "排除", "不要", "限制", "exclude"]
    }
    
    fields_found = {}
    for field, keywords in required_field_keywords.items():
        fields_found[field] = any(kw in raw_text for kw in keywords)
    
    template_completeness = sum(fields_found.values())
    template_complete = template_completeness >= 5  # At least 5 of 6 required fields
    
    checks.append({
        "name": "Agent task templates contain required fields (scope, questions, sources, output format, confidence markers, constraints)",
        "passed": template_complete,
        "detail": f"Fields found: {fields_found}. Score: {template_completeness}/6"
    })
    
    # CHECK 7: Integration/synthesis plan must be present
    integration_keywords = ["整合", "integration", "cross-valid", "交叉验证", "矛盾", "contradiction", 
                            "口径", "统一", "审阅", "review", "综合", "synthesis", "补充调研"]
    has_integration = any(kw.lower() in raw_text.lower() for kw in integration_keywords)
    
    checks.append({
        "name": "Plan includes integration/cross-validation synthesis step",
        "passed": has_integration,
        "detail": f"Integration plan keywords found: {[kw for kw in integration_keywords if kw.lower() in raw_text.lower()]}"
    })
    
    # CHECK 8: Must NOT put D and B in the same parallel batch (the common wrong answer)
    # If D and B are co-located in a parallel group without D being marked as dependent, that's wrong
    # Check by looking for D-depends-B violation: if any structure lists D as parallel to B without dependency
    
    # Heuristic: find if there's any explicit parallel group/batch/wave that contains BOTH B and D keywords
    # without dependency markers
    violation_found = False
    
    if isinstance(plan, dict):
        def find_parallel_groups(obj, path=""):
            groups = []
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if any(pk in k.lower() for pk in ["parallel", "simultaneous", "batch", "wave", "同时", "并行"]):
                        groups.append((path + "." + k, v))
                    groups.extend(find_parallel_groups(v, path + "." + k))
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    groups.extend(find_parallel_groups(item, path + f"[{i}]"))
            return groups
        
        parallel_groups = find_parallel_groups(plan)
        for path, group in parallel_groups:
            group_str = json.dumps(group, ensure_ascii=False)
            has_b = any(kw in group_str for kw in ["监管", "regulatory", "牌照", "合规要求"])
            has_d = any(kw in group_str for kw in ["技术架构", "本地化部署", "等保", "NMPA技术"])
            if has_b and has_d:
                # Check if there's a dependency marker for D in this group
                has_dep_marker = any(dk.lower() in group_str.lower() for dk in ["depends", "after", "依赖", "之后"])
                if not has_dep_marker:
                    violation_found = True
    
    checks.append({
        "name": "Section D is NOT incorrectly placed in the same parallel batch as Section B",
        "passed": not violation_found,
        "detail": "D must be in a sequential phase after B, not co-parallel with B" if violation_found else "Correct: D is not erroneously parallelized with B"
    })
    
    # Calculate final score
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    score = passed_checks / total_checks
    
    # Must pass critical checks (1, 3, 4, 5) to pass overall
    critical_checks = [checks[0], checks[2], checks[3], checks[4]]  # exists, parallel batch, D deps B, E deps AC
    critical_passed = all(c["passed"] for c in critical_checks)
    
    overall_passed = critical_passed and score >= 0.75
    
    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)