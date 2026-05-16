import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def find_output_file(workspace):
    candidates = list(Path(workspace).rglob("character_psychology_brief.md"))
    if candidates:
        return candidates[0]
    return None

def evaluate(workspace):
    checks = []
    
    # 1. Find the output file
    output_file = find_output_file(workspace)
    if output_file is None:
        checks.append(check("output_file_exists", False, "character_psychology_brief.md not found anywhere in workspace"))
        return checks, 0.0
    
    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("output_file_readable", False, f"Could not read file: {e}"))
        return checks, 0.0
    
    checks.append(check("output_file_exists", True, f"Found at {output_file}"))
    
    content_lower = content.lower()
    
    # 2. Check: Both characters have psychological profiles
    has_reyes_profile = bool(re.search(r'(reyes|elena)', content, re.IGNORECASE))
    has_marco_profile = bool(re.search(r'(marco|vitelli)', content, re.IGNORECASE))
    both_characters = has_reyes_profile and has_marco_profile
    checks.append(check(
        "both_characters_covered",
        both_characters,
        f"Elena Reyes found: {has_reyes_profile}, Marco Vitelli found: {has_marco_profile}"
    ))
    
    # 3. Check: Big Five traits present with behavioral manifestations
    big_five_keywords = [
        r'开放性|openness',
        r'尽责性|conscientiousness',
        r'外向性|extraversion|extroversion',
        r'宜人性|agreeableness',
        r'神经质|neuroticism'
    ]
    big_five_count = sum(1 for kw in big_five_keywords if re.search(kw, content, re.IGNORECASE))
    big_five_ok = big_five_count >= 4
    checks.append(check(
        "big_five_traits_present",
        big_five_ok,
        f"Found {big_five_count}/5 Big Five trait dimensions. Need at least 4."
    ))
    
    # 4. Check: Attachment theory with specific types mentioned
    attachment_types = [
        r'安全型|secure attach',
        r'焦虑.迷恋|anxious.preoccupied|anxious attach',
        r'回避.疏离|dismissive.avoidant|avoidant attach',
        r'恐惧.回避|fearful.avoidant|disorganized'
    ]
    attachment_count = sum(1 for t in attachment_types if re.search(t, content, re.IGNORECASE))
    attachment_ok = attachment_count >= 2
    checks.append(check(
        "attachment_theory_specific_types",
        attachment_ok,
        f"Found {attachment_count}/4 specific attachment type references. Need at least 2 specific types named."
    ))
    
    # 5. Check: Vaillant's defense hierarchy explicitly referenced
    vaillant_patterns = [
        r'维兰特|vaillant',
        r'防御机制.*层级|defense.*hierarch|層級.*防禦',
        r'成熟.*防御|neurotic.*defense|immature.*defense|mature.*defense',
        r'理智化|intellectuali[sz]ation',
        r'投射|projection',
        r'幽默|humor.*defense|defence.*humour',
        r'区隔化|compartmentali[sz]ation|compartmentali[sz]ing',
        r'反向形成|reaction formation',
        r'压抑|repression',
        r'退行|regression'
    ]
    vaillant_hits = sum(1 for p in vaillant_patterns if re.search(p, content, re.IGNORECASE))
    vaillant_ok = vaillant_hits >= 3
    checks.append(check(
        "vaillant_defense_hierarchy",
        vaillant_ok,
        f"Found {vaillant_hits} Vaillant-related defense mechanism references. Need at least 3 (hierarchy + specific mechanisms)."
    ))
    
    # 6. Check: Unspoken contracts (无言契约) in relationship dynamics - a KEY proprietary element
    unspoken_contract_patterns = [
        r'无言契约|unspoken contract|implicit contract|无声契约',
        r'隐含期待|implicit expectation|unspoken expectation|unstated expectation',
        r'隐性协议|hidden agreement|tacit agreement'
    ]
    unspoken_ok = any(re.search(p, content, re.IGNORECASE) for p in unspoken_contract_patterns)
    checks.append(check(
        "unspoken_contracts_present",
        unspoken_ok,
        "The relationship dynamics section must include 'unspoken contracts' (无言契约) — implicit mutual expectations. " +
        ("Found." if unspoken_ok else "NOT found. This is a required schema element from the interpersonal dynamics framework.")
    ))
    
    # 7. Check: Relationship dynamics section with power dynamics AND triggers
    power_dynamics = bool(re.search(r'权力动态|power dynamic|对称|互补|complementary|symmetric|变动型|shifting', content, re.IGNORECASE))
    triggers_present = bool(re.search(r'触发[点]?|trigger[s]?|升级|escalat', content, re.IGNORECASE))
    growth_edge = bool(re.search(r'成长边缘|growth edge|更健康|healthier version|成长', content, re.IGNORECASE))
    relationship_analysis_ok = power_dynamics and triggers_present and growth_edge
    checks.append(check(
        "relationship_dynamics_complete",
        relationship_analysis_ok,
        f"Power dynamics: {power_dynamics}, Specific triggers: {triggers_present}, Growth edge: {growth_edge}. All three required."
    ))
    
    # 8. Check: Adaptive strengths present (not just pathologies)
    adaptive_patterns = [
        r'适应性|adaptive strength|strengths?|优势|积极|positive',
        r'高功能|high.function|high functioning',
        r'韧性|resilien',
        r'不适应性|maladaptive',  # Must have BOTH
    ]
    has_adaptive = any(re.search(p, content, re.IGNORECASE) for p in adaptive_patterns[:3])
    has_maladaptive = bool(re.search(adaptive_patterns[3], content, re.IGNORECASE))
    both_adaptive = has_adaptive and has_maladaptive
    checks.append(check(
        "both_adaptive_and_maladaptive_patterns",
        both_adaptive,
        f"Adaptive/strengths mentioned: {has_adaptive}, Maladaptive patterns mentioned: {has_maladaptive}. Both required per SKILL.md rules."
    ))
    
    # 9. Check: Framework limitations acknowledged (critical SKILL.md rule)
    limitation_patterns = [
        r'局限|limitation[s]?|critic|批评|locally',
        r'文化.*语境|cultural context|文化偏见|cultural bias|西方|western',
        r'集体主义|collectiv',
        r'可重复性|replication crisis|争议|controversial',
        r'不足|shortcoming|caveat',
        r'诚实承认|honest.*acknowledg|acknowledge.*limit'
    ]
    limitation_count = sum(1 for p in limitation_patterns if re.search(p, content, re.IGNORECASE))
    limitations_ok = limitation_count >= 2
    checks.append(check(
        "framework_limitations_acknowledged",
        limitations_ok,
        f"Found {limitation_count} references to framework limitations/cultural context. Need at least 2. SKILL.md mandates honest acknowledgment of limits."
    ))
    
    # 10. Check: No diagnostic labeling (characters described with traits, not as 'a narcissist', 'a borderline', etc.)
    # Check for problematic diagnostic labeling (using 'is a X' pattern rather than 'shows X traits')
    labeling_patterns = [
        r'(reyes|elena|marco|vitelli)\s+(is|是|有)\s+a[n]?\s+(narcissist|borderline|psychopath|sociopath|自恋者|边缘型人格障碍患者)',
        r'diagnosed with|诊断为.*障碍$',
    ]
    diagnostic_labels_found = any(re.search(p, content, re.IGNORECASE) for p in labeling_patterns)
    no_label_ok = not diagnostic_labels_found
    checks.append(check(
        "no_reductive_diagnostic_labeling",
        no_label_ok,
        "Characters should NOT be reduced to diagnostic labels. " +
        ("Potential labeling found — check content." if diagnostic_labels_found else "No reductive labeling detected.")
    ))
    
    # 11. Check: Marco's specific pattern (entering crises, leaving when stable) explained with named mechanism
    marco_pattern_patterns = [
        r'marco.*crisis|crisis.*marco|危机.*marco|marco.*危机',
        r'焦虑型|anxious.*attach|attachment.*anxious',
        r'讨好|fawn|caretaking|照顾者|caregiver',
        r'回避|avoidant|distanc',
        r'需要被需要|need.*to be needed|needed',
        r'stabiliz|稳定.*后|when.*stable'
    ]
    marco_explanation_count = sum(1 for p in marco_pattern_patterns if re.search(p, content, re.IGNORECASE))
    marco_ok = marco_explanation_count >= 2
    checks.append(check(
        "marco_crisis_pattern_explained",
        marco_ok,
        f"Marco's crisis-approach/stability-avoidance pattern should be explained with named psychological mechanism. Found {marco_explanation_count}/6 related references."
    ))
    
    # 12. Check: Elena's "going cold" explained as specific defense mechanism
    elena_cold_patterns = [
        r'区隔化|compartmentali[sz]',
        r'理智化|intellectuali[sz]',
        r'情感疏离|emotional detachment|detach',
        r'回避|avoidant|dismissive',
        r'冻结|freeze|shutdown|封闭|shut down',
        r'解离|dissociat',
        r'elena.*cold|cold.*elena|goes cold|going cold|shut.*down.*elena|elena.*shut'
    ]
    elena_explanation_count = sum(1 for p in elena_cold_patterns if re.search(p, content, re.IGNORECASE))
    elena_ok = elena_explanation_count >= 2
    checks.append(check(
        "elena_shutdown_mechanism_explained",
        elena_ok,
        f"Elena's 'going cold' response should be explained as a specific named defense mechanism. Found {elena_explanation_count}/7 related references."
    ))
    
    # 13. Check: Named theoretical frameworks cited (not just pop psychology)
    framework_names = [
        r'大五人格|big five|five.factor',
        r'依恋理论|attachment theory|bowlby|鲍尔比',
        r'vaillant|维兰特',
        r'beck|贝克|cognitive distortion|认知扭曲',
        r'erikson|埃里克森',
        r'karpman|卡普曼|drama triangle|戏剧三角',
        r'transactional analysis|交互分析',
        r'piaget|皮亚杰',
        r'van der kolk|范德科尔克',
        r'herman|赫尔曼',
        r'tajfel|塔吉菲尔',
        r'milgram|米尔格拉姆',
        r'porges|波杰斯|polyvagal',
        r'horney|horney',
        r'winnicott|温尼科特'
    ]
    framework_count = sum(1 for f in framework_names if re.search(f, content, re.IGNORECASE))
    frameworks_ok = framework_count >= 4
    checks.append(check(
        "named_theoretical_frameworks_cited",
        frameworks_ok,
        f"Found {framework_count}/15 named theoretical frameworks. Need at least 4 specific named frameworks (not generic terms)."
    ))
    
    # Calculate score
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    
    # Weight critical checks more heavily
    critical_checks = [
        "output_file_exists",
        "both_characters_covered", 
        "unspoken_contracts_present",
        "vaillant_defense_hierarchy",
        "framework_limitations_acknowledged",
        "named_theoretical_frameworks_cited"
    ]
    
    critical_passed = sum(1 for c in checks if c["name"] in critical_checks and c["passed"])
    non_critical_passed = passed_checks - critical_passed
    
    critical_total = len(critical_checks)
    non_critical_total = total_checks - critical_total
    
    if critical_total > 0 and non_critical_total > 0:
        score = 0.6 * (critical_passed / critical_total) + 0.4 * (non_critical_passed / non_critical_total)
    else:
        score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    overall_passed = (critical_passed >= 5) and (passed_checks >= 9)
    
    return checks, score, overall_passed

def main():
    if len(sys.argv) < 2:
        workspace = "/workspace"
    else:
        workspace = sys.argv[1]
    
    try:
        checks, score, overall_passed = evaluate(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "evaluation_error", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()