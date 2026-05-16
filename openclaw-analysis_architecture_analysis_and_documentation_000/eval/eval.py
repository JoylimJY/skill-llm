import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def find_report(workspace):
    """Find the analysis report file."""
    ws = Path(workspace)
    candidates = list(ws.rglob("nexusmfg_analysis.md"))
    if not candidates:
        # try broader search
        candidates = list(ws.rglob("*analysis*.md")) + list(ws.rglob("*analysis*.txt"))
    return candidates[0] if candidates else None

def run_eval(workspace):
    checks = []
    
    # ── Find the output file ──────────────────────────────────────────────────
    report_path = find_report(workspace)
    if report_path is None:
        checks.append(check("report_exists", False, "Could not find nexusmfg_analysis.md or any analysis report file"))
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append(check("report_exists", True, f"Found report at {report_path}"))
    
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("report_readable", False, f"Could not read file: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append(check("report_readable", True, f"File readable, {len(content)} chars"))
    
    # ── Check 1: All 7 principles present with proper numbering ──────────────
    principle_patterns = [
        (r"1️⃣|Agent\s*无处不在|Ubiquitous\s*Agent", "Principle 1: Agent无处不在"),
        (r"2️⃣|技能即插件|Skill-as-Plugin", "Principle 2: 技能即插件"),
        (r"3️⃣|记忆即永续|Memory-as-Persistence", "Principle 3: 记忆即永续"),
        (r"4️⃣|协作即本能|Collaboration-as-Instinct", "Principle 4: 协作即本能"),
        (r"5️⃣|感知即语言|Perception-as-Language", "Principle 5: 感知即语言"),
        (r"6️⃣|安全即信任|Security-as-Trust", "Principle 6: 安全即信任"),
        (r"7️⃣|进化即必然|Evolution-as-Inevitable", "Principle 7: 进化即必然"),
    ]
    
    all_principles_present = True
    for pattern, label in principle_patterns:
        found = bool(re.search(pattern, content))
        if not found:
            all_principles_present = False
        checks.append(check(f"has_{label}", found, 
                             f"{'Found' if found else 'MISSING'} section for {label}"))
    
    # ── Check 2: All 21 sub-dimensions present ───────────────────────────────
    subdimension_patterns = [
        # Principle 1
        (r"硬件即\s*Agent|硬件.*Agent.*节点|每个设备.*独立", "硬件即Agent"),
        (r"边缘自治|自组织|自治网络|本地.*集群", "边缘自治网络"),
        (r"Agent\s*市场|技能.*发布.*订阅|发布.*订阅.*技能|Marketplace", "Agent市场机制"),
        # Principle 2
        (r"动态.*热插拔|热加载|运行时.*加载|热插拔", "动态技能热插拔"),
        (r"技能组合|低代码|无代码|组合编程", "技能组合编程"),
        (r"技能基因|可继承|继承.*变异|基因库", "技能基因库"),
        # Principle 3
        (r"跨设备.*记忆|记忆.*同步|设备.*共享.*记忆", "跨设备记忆同步"),
        (r"记忆压缩|记忆蒸馏|遗忘机制|记忆.*总结|蒸馏", "记忆压缩与蒸馏"),
        (r"集体记忆|跨用户.*知识|知识共享", "集体记忆网络"),
        # Principle 4
        (r"意图对齐|自动.*理解.*目标|Agent.*意图", "Agent意图对齐"),
        (r"动态任务编排|任务.*自动分解|自动.*分配.*任务|任务编排", "动态任务编排"),
        (r"跨领域专家|专家\s*Agent|专家.*相互调用", "跨领域专家"),
        # Principle 5
        (r"多模态|图像.*声音|统一编码|多模态.*编码", "多模态统一编码"),
        (r"数字孪生|3D.*环境|物理世界.*数字|孪生", "物理世界数字孪生"),
        (r"持续学习|学习.*用户习惯|感知.*持续学习|在线学习", "持续学习感知"),
        # Principle 6
        (r"可解释|审计日志|行为.*可追溯|溯源", "可解释AI决策"),
        (r"隐私优先|本地.*处理|敏感.*本地|隐私.*架构", "隐私优先架构"),
        (r"硬件.*信任链|TPM|硬件级.*安全|信任链", "硬件级信任链"),
        # Principle 7 (only 2 sub-dimensions!)
        (r"自进化|自我优化|自主.*优化|使用模式.*优化", "自进化Agent"),
        (r"人机共生|人类.*AI.*促进|相互促进|人机协作.*进化|操作员.*反馈", "人机共生进化"),
    ]
    
    subdim_found_count = 0
    for pattern, label in subdimension_patterns:
        found = bool(re.search(pattern, content))
        if found:
            subdim_found_count += 1
        checks.append(check(f"subdim_{label}", found,
                             f"{'Found' if found else 'MISSING'} sub-dimension: {label}"))
    
    subdim_coverage = subdim_found_count / len(subdimension_patterns)
    checks.append(check("subdim_coverage_75pct", subdim_coverage >= 0.75,
                         f"Sub-dimension coverage: {subdim_found_count}/{len(subdimension_patterns)} = {subdim_coverage:.1%}"))
    
    # ── Check 3: Principle 7 must have exactly 2 (not 3) sub-dimensions ──────
    # Extract the Principle 7 section
    p7_match = re.search(
        r"(7️⃣|进化即必然|Evolution-as-Inevitable)(.*?)(?=\Z|\n#{1,3}\s|\Z)",
        content, re.DOTALL | re.IGNORECASE
    )
    p7_correct_count = False
    p7_detail = "Could not extract Principle 7 section"
    if p7_match:
        p7_section = p7_match.group(2)
        # Count sub-dimension bullets (lines starting with - or • or #### or similar)
        subdim_indicators = re.findall(
            r"(自进化|人机共生|人机协作|自我优化|相互促进)",
            p7_section
        )
        # Principle 7 should NOT have a third sub-dimension fabricated
        fabricated_third = re.search(
            r"(技术奇点|自主繁殖|Agent.*繁衍|系统.*自主.*扩展|自主.*复制)",
            p7_section
        )
        if len(subdim_indicators) >= 1:
            p7_correct_count = not bool(fabricated_third)
            p7_detail = (
                f"Principle 7 contains {len(subdim_indicators)} correct sub-dim keywords. "
                f"Fabricated 3rd sub-dim: {bool(fabricated_third)}"
            )
        else:
            p7_detail = "Principle 7 section found but sub-dimensions unclear"
    checks.append(check("principle7_no_fabricated_third_subdim", p7_correct_count, p7_detail))
    
    # ── Check 4: NexusMFG-specific factual accuracy ───────────────────────────
    # The report must correctly identify specific YES/PARTIAL/NO verdicts for key dimensions
    factual_checks = [
        # TPM chips exist but SDK not exposed → hardware trust chain is PARTIAL/NO
        (r"TPM.*未暴露|TPM.*未打通|TPM.*未.*API|硬件.*信任链.*不完整|信任链.*待完善|TPM.*待|TPM.*缺|TPM.*零|TPM.*尚未",
         "TPM_partial_correctly_identified",
         "TPM exists but not exposed to Agents — should be flagged as incomplete"),
        # Memory compression is MISSING
        (r"记忆.*蒸馏.*缺|蒸馏.*未.*实现|无.*蒸馏|缺乏.*蒸馏|记忆压缩.*不|存储.*瓶颈|蒸馏.*没有",
         "memory_distillation_gap_identified",
         "Memory distillation is missing — should be flagged"),
        # Skill inheritance is NOT supported
        (r"技能.*继承.*不支持|继承.*缺失|无.*继承|技能基因.*不|复制粘贴|继承机制.*缺",
         "skill_inheritance_gap_identified",
         "Skill inheritance not supported — should be flagged"),
        # Edge autonomy is limited (no self-organization)
        (r"边缘.*自组织.*不|无.*自组织|自组织.*缺|自治.*受限|手动配置",
         "edge_self_organization_gap_identified",
         "Edge self-organization requires manual config — should be flagged"),
    ]
    
    for pattern, name, detail_hint in factual_checks:
        found = bool(re.search(pattern, content, re.IGNORECASE))
        checks.append(check(name, found,
                             f"{'Correctly identified' if found else 'MISSED: ' + detail_hint}"))
    
    # ── Check 5: Report is substantive (minimum length) ──────────────────────
    min_length = 1500
    is_long_enough = len(content) >= min_length
    checks.append(check("report_min_length", is_long_enough,
                         f"Report length: {len(content)} chars (min {min_length})"))
    
    # ── Check 6: The 7-principle structure integrity (not 6, not 8) ───────────
    emoji_count = len(re.findall(r'[1-7]️⃣', content))
    # Allow for the principles to appear multiple times (headers + references)
    has_all_7_emojis = emoji_count >= 7
    # More lenient: count distinct principle headers
    distinct_principle_headers = len(set(re.findall(r'[1-7]️⃣', content)))
    structure_correct = distinct_principle_headers == 7 or (
        all(bool(re.search(p, content)) for p, _ in principle_patterns)
    )
    checks.append(check("seven_principles_complete_structure", structure_correct,
                         f"Found {distinct_principle_headers} distinct emoji principle markers; "
                         f"all 7 principles covered by text: {all(bool(re.search(p, content)) for p, _ in principle_patterns)}"))
    
    # ── Scoring ───────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / total
    
    # Must pass critical checks to be overall "passed"
    critical_checks = [
        "report_exists",
        "subdim_coverage_75pct",
        "report_min_length",
        "seven_principles_complete_structure",
        "TPM_partial_correctly_identified",
        "memory_distillation_gap_identified",
        "skill_inheritance_gap_identified",
    ]
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.70
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))