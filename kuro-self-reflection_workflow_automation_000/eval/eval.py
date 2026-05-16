import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def find_file(workspace, filename):
    matches = list(Path(workspace).rglob(filename))
    return matches[0] if matches else None

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return None

def main():
    workspace = sys.argv[1]
    checks = []
    
    # ===== CHECK 1: Reflection Report Exists =====
    reflection_file = find_file(workspace, "reflection_report.md")
    if reflection_file is None:
        # Try alternate common names
        for name in ["*反思报告*", "*retro*report*", "*reflection*"]:
            matches = list(Path(workspace).rglob(name))
            if matches:
                reflection_file = matches[0]
                break
    
    if reflection_file is None:
        checks.append(check("reflection_report_exists", False, "No reflection_report.md found anywhere in workspace"))
        reflection_content = ""
    else:
        reflection_content = read_file(reflection_file) or ""
        checks.append(check("reflection_report_exists", True, f"Found at {reflection_file}"))
    
    # ===== CHECK 2: Optimization Plan Exists =====
    plan_file = find_file(workspace, "optimization_plan.md")
    if plan_file is None:
        for name in ["*优化计划*", "*improvement*plan*", "*action*plan*", "*plan*"]:
            matches = [m for m in Path(workspace).rglob(name) if m.is_file() and m.suffix == ".md"]
            if matches:
                plan_file = matches[0]
                break
    
    if plan_file is None:
        checks.append(check("optimization_plan_exists", False, "No optimization_plan.md found anywhere in workspace"))
        plan_content = ""
    else:
        plan_content = read_file(plan_file) or ""
        checks.append(check("optimization_plan_exists", True, f"Found at {plan_file}"))
    
    # ===== CHECK 3: Checklist file exists =====
    checklist_file = find_file(workspace, "checklist.md")
    if checklist_file is None:
        for name in ["*checklist*", "*check_list*", "*检查清单*"]:
            matches = [m for m in Path(workspace).rglob(name) if m.is_file() and m.suffix == ".md"]
            if matches:
                checklist_file = matches[0]
                break
    
    if checklist_file is None:
        checks.append(check("checklist_exists", False, "No checklist.md found (Stage 5 Solidify requirement)"))
        checklist_content = ""
    else:
        checklist_content = read_file(checklist_file) or ""
        checks.append(check("checklist_exists", True, f"Found at {checklist_file}"))
    
    # ===== CHECK 4: Three-Layer Structure in Reflection =====
    # Must have all three layers in correct order
    combined = reflection_content.lower()
    
    has_layer1 = bool(re.search(r'(第一层|layer.1|问题审视|problem|直面问题)', combined))
    has_layer2 = bool(re.search(r'(第二层|layer.2|系统审视|system|系统)', combined))
    has_layer3 = bool(re.search(r'(第三层|layer.3|角色审视|role|角色)', combined))
    
    all_three_layers = has_layer1 and has_layer2 and has_layer3
    checks.append(check(
        "reflection_three_layers",
        all_three_layers,
        f"Layer1(问题)={has_layer1}, Layer2(系统)={has_layer2}, Layer3(角色)={has_layer3}"
    ))
    
    # ===== CHECK 5: Layer ordering - Layer 1 must appear before Layer 2, Layer 2 before Layer 3 =====
    if all_three_layers:
        try:
            # Find positions of each layer heading
            layer1_patterns = [r'第一层', r'layer.?1', r'问题审视', r'## .{0,10}问题']
            layer2_patterns = [r'第二层', r'layer.?2', r'系统审视', r'## .{0,10}系统']
            layer3_patterns = [r'第三层', r'layer.?3', r'角色审视', r'## .{0,10}角色']
            
            def find_pos(content, patterns):
                positions = []
                for p in patterns:
                    for m in re.finditer(p, content, re.IGNORECASE):
                        positions.append(m.start())
                return min(positions) if positions else float('inf')
            
            pos1 = find_pos(reflection_content, layer1_patterns)
            pos2 = find_pos(reflection_content, layer2_patterns)
            pos3 = find_pos(reflection_content, layer3_patterns)
            
            correct_order = pos1 < pos2 < pos3
            checks.append(check(
                "reflection_layer_order",
                correct_order,
                f"Layer order positions: L1={pos1}, L2={pos2}, L3={pos3}. Must be L1<L2<L3 (ascending depth)"
            ))
        except Exception as e:
            checks.append(check("reflection_layer_order", False, f"Error checking layer order: {e}"))
    else:
        checks.append(check("reflection_layer_order", False, "Cannot check order - not all layers present"))
    
    # ===== CHECK 6: Evidence-based problem identification (must reference actual bugs from logs) =====
    # The actual problems from the scenario: timeout, refund, auth token
    reflection_lower = reflection_content.lower()
    has_timeout = bool(re.search(r'timeout|超时', reflection_lower))
    has_refund = bool(re.search(r'refund|退款', reflection_lower))
    has_auth = bool(re.search(r'auth|token|认证|鉴权', reflection_lower))
    has_evidence = bool(re.search(r'(evidence|证据|log|日志|5.{0,10}(error|bug)|data|数据)', reflection_lower))
    
    evidence_score = sum([has_timeout, has_refund, has_auth])
    checks.append(check(
        "reflection_evidence_based",
        evidence_score >= 2 and has_evidence,
        f"Bug references: timeout={has_timeout}, refund={has_refund}, auth={has_auth}, evidence_present={has_evidence}"
    ))
    
    # ===== CHECK 7: Role self-examination (角色审视) with self-critique =====
    # Must contain self-examination elements: role identification + self-critique
    has_role_identification = bool(re.search(r'(执行者|审查者|质检|reviewer|executor|coordinator|协调者)', combined))
    has_self_critique = bool(re.search(r'(我.{0,20}(没有|未|缺乏|问题)|i (didn|failed|neglected)|self.critique|自我)', combined))
    has_mindset_behavior_ability = bool(re.search(r'(心态|行为|能力|mindset|behavior|skill|attitude)', combined))
    
    role_quality = has_role_identification and (has_self_critique or has_mindset_behavior_ability)
    checks.append(check(
        "reflection_role_self_examination",
        role_quality,
        f"role_id={has_role_identification}, self_critique={has_self_critique}, mindset/behavior/ability={has_mindset_behavior_ability}"
    ))
    
    # ===== CHECK 8: Repeat pattern identified (Sprint 41 = same issues) =====
    # Skill says: "重复错误: 同类问题出现 2 次以上" is an activation condition
    # Agent must notice this is a repeat from Sprint 41
    has_repeat_pattern = bool(re.search(r'(sprint.41|上次|previous|repeat|重复|模式|pattern|again)', combined))
    checks.append(check(
        "reflection_identifies_repeat_pattern",
        has_repeat_pattern,
        "Must identify that this is a recurring pattern (Sprint 41 had same issues)"
    ))
    
    # ===== CHECK 9: Plan has all three solution layers =====
    plan_lower = plan_content.lower()
    plan_has_direct_fix = bool(re.search(r'(第一层|直接修复|direct.fix|immediate|layer.?1)', plan_lower))
    plan_has_system = bool(re.search(r'(第二层|系统改进|system.impr|layer.?2)', plan_lower))
    plan_has_self_change = bool(re.search(r'(第三层|自我改变|self.change|layer.?3)', plan_lower))
    
    plan_three_layers = plan_has_direct_fix and plan_has_system and plan_has_self_change
    checks.append(check(
        "plan_three_layers",
        plan_three_layers,
        f"Plan: direct_fix={plan_has_direct_fix}, system={plan_has_system}, self_change={plan_has_self_change}"
    ))
    
    # ===== CHECK 10: Plan has P0/P1/P2/P3 priority classification =====
    has_priority_system = bool(re.search(r'(p0|p1|p2|p3|优先级|priority)', plan_lower))
    has_p0 = bool(re.search(r'(p0|立即|immediate|urgent)', plan_lower))
    
    checks.append(check(
        "plan_priority_classification",
        has_priority_system and has_p0,
        f"priority_system={has_priority_system}, has_P0_immediate={has_p0}"
    ))
    
    # ===== CHECK 11: Plan has success metrics / success indicators =====
    has_success_metrics = bool(re.search(r'(成功指标|success.metric|验收标准|acceptance|目标|goal|measure)', plan_lower))
    checks.append(check(
        "plan_success_metrics",
        has_success_metrics,
        f"Plan must include success metrics table (成功指标)"
    ))
    
    # ===== CHECK 12: Self-change plan has mindset/behavior/ability breakdown =====
    self_change_section = ""
    # Try to extract the self-change section from plan
    sc_match = re.search(r'(第三层|自我改变|self.change)(.*?)(?=##|\Z)', plan_content, re.DOTALL | re.IGNORECASE)
    if sc_match:
        self_change_section = sc_match.group(2).lower()
    else:
        self_change_section = plan_lower
    
    has_mindset = bool(re.search(r'(心态|mindset|attitude|认知)', self_change_section))
    has_behavior = bool(re.search(r'(行为|behavior|action|实践|practice)', self_change_section))
    has_ability = bool(re.search(r'(能力|skill|ability|技能|capability)', self_change_section))
    
    mba_breakdown = has_mindset and has_behavior and has_ability
    checks.append(check(
        "plan_self_change_mba_breakdown",
        mba_breakdown,
        f"Self-change must categorize into 心态/行为/能力: mindset={has_mindset}, behavior={has_behavior}, ability={has_ability}"
    ))
    
    # ===== CHECK 13: Checklist has mandatory items (必查项) =====
    checklist_lower = checklist_content.lower()
    has_mandatory_section = bool(re.search(r'(必查项|mandatory|required|必须)', checklist_lower))
    has_checkbox_items = bool(re.search(r'\[.?\]', checklist_content))
    has_checklist_items = bool(re.search(r'(test|edge.case|timeout|refund|review|测试|超时|退款|代码审查)', checklist_lower))
    
    checklist_quality = has_checkbox_items and has_checklist_items
    checks.append(check(
        "checklist_quality",
        checklist_quality,
        f"mandatory_section={has_mandatory_section}, checkboxes={has_checkbox_items}, relevant_items={has_checklist_items}"
    ))
    
    # ===== CHECK 14: Meta-information in reflection (反思时间, 触发原因, 范围) =====
    has_meta = bool(re.search(r'(元信息|meta|反思时间|触发|trigger|scope|范围|时间)', combined))
    checks.append(check(
        "reflection_meta_info",
        has_meta,
        "Reflection report must contain meta-information section (元信息: time, scope, trigger)"
    ))
    
    # ===== CHECK 15: System analysis includes input/process/output/feedback examination =====
    system_section = ""
    sys_match = re.search(r'(第二层|系统审视|system)(.*?)(?=第三层|角色|layer.?3|##|\Z)', reflection_content, re.DOTALL | re.IGNORECASE)
    if sys_match:
        system_section = sys_match.group(2).lower()
    else:
        system_section = combined
    
    has_input = bool(re.search(r'(输入|input)', system_section))
    has_process = bool(re.search(r'(处理|流程|process|procedure|mechanism|机制)', system_section))
    has_feedback = bool(re.search(r'(反馈|feedback)', system_section))
    has_mechanism = bool(re.search(r'(机制|mechanism|流程|process|规范|standard)', system_section))
    
    system_depth = sum([has_input, has_process, has_feedback, has_mechanism])
    checks.append(check(
        "reflection_system_analysis_depth",
        system_depth >= 2,
        f"System analysis elements: input={has_input}, process={has_process}, feedback={has_feedback}, mechanism={has_mechanism} (need >= 2)"
    ))
    
    # Calculate score
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    overall_passed = passed_count >= int(total * 0.75)
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()