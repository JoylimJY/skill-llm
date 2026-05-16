import sys
import os
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
    
    # Find the output file
    target_files = list(Path(workspace).rglob("monthly_review.md"))
    
    if not target_files:
        add_check("file_exists", False, "monthly_review.md not found anywhere in workspace")
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    
    # Use the most recently modified one if multiple
    target_file = sorted(target_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    
    try:
        content = target_file.read_text(encoding="utf-8")
    except Exception as e:
        add_check("file_readable", False, f"Could not read file: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("file_exists", True, f"Found at {target_file}")
    
    # ── CHECK 1: Written in Chinese (majority Chinese characters) ──
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    total_alpha = len(re.findall(r'[a-zA-Z\u4e00-\u9fff]', content))
    chinese_ratio = chinese_chars / max(total_alpha, 1)
    is_chinese = chinese_ratio > 0.4
    add_check(
        "written_in_chinese",
        is_chinese,
        f"Chinese char ratio: {chinese_ratio:.2f} ({chinese_chars} Chinese / {total_alpha} total alpha-chars)"
    )
    
    # ── CHECK 2: Has required structural sections ──
    has_core_conclusion = bool(re.search(r'核心结论', content))
    has_core_workstreams = bool(re.search(r'核心主线', content))
    has_weekly = bool(re.search(r'按周回顾|第\s*[1-4１２３４]\s*周', content))
    has_one_sentence = bool(re.search(r'一句话总结', content))
    
    structure_passed = has_core_conclusion and has_core_workstreams and has_weekly and has_one_sentence
    add_check(
        "proprietary_structure_sections",
        structure_passed,
        f"核心结论={has_core_conclusion}, 核心主线={has_core_workstreams}, 按周回顾={has_weekly}, 一句话总结={has_one_sentence}"
    )
    
    # ── CHECK 3: 3-5 workstreams (not too many, not too few) ──
    # Count workstream headers: ### N. or ### 1. patterns or numbered list items under 核心主线
    workstream_matches = re.findall(r'###\s*\d+[\.、．]', content)
    num_workstreams = len(workstream_matches)
    workstreams_ok = 3 <= num_workstreams <= 5
    add_check(
        "workstream_count_3_to_5",
        workstreams_ok,
        f"Found {num_workstreams} workstream sections (### N.). Expected 3-5."
    )
    
    # ── CHECK 4: Latency optimization (user-owned) is present with strong verbs ──
    latency_present = bool(re.search(r'延迟|latency|P99|KV.{0,5}Cache|异步预加载|吞吐', content, re.IGNORECASE))
    # Strong verbs for high-confidence ownership
    strong_verbs_latency = bool(re.search(r'(主导|负责|推进|完成|实现|设计|落地).{0,60}(延迟|P99|KV|预加载|吞吐)', content) or
                                  re.search(r'(延迟|P99|KV|预加载|吞吐).{0,60}(主导|负责|推进|完成|实现|设计|落地)', content))
    add_check(
        "latency_work_with_ownership_signal",
        latency_present and strong_verbs_latency,
        f"Latency work present={latency_present}, strong ownership verb={strong_verbs_latency}"
    )
    
    # ── CHECK 5: LLM eval framework (user-owned) is present ──
    llm_eval_present = bool(re.search(r'(LLM|评测框架|评测|CI.{0,10}集成|自动化回归)', content, re.IGNORECASE))
    add_check(
        "llm_eval_framework_present",
        llm_eval_present,
        f"LLM eval framework mentioned: {llm_eval_present}"
    )
    
    # ── CHECK 6: Governance/metrics work present ──
    governance_present = bool(re.search(r'(质量治理|指标体系|漂移|KL|模型质量|指标.*设计)', content))
    add_check(
        "governance_metrics_work_present",
        governance_present,
        f"Model quality governance/metrics work mentioned: {governance_present}"
    )
    
    # ── CHECK 7: Correctly EXCLUDES or downweights meeting-only noise ──
    # The AI-generated summary falsely credited 林晓宇 for 数据管道 v3 (王芳's) and K8s (陈刚's)
    # These should NOT appear as user's owned work
    false_attribution_pipeline = bool(re.search(r'(主导|负责|完成|推进).{0,40}(数据管道.{0,20}重构|管道.*v3)', content))
    false_attribution_k8s = bool(re.search(r'(主导|负责|完成|推进).{0,40}(K8s.*扩容|节点扩容)', content))
    no_false_attribution = not false_attribution_pipeline and not false_attribution_k8s
    add_check(
        "no_false_attribution_of_others_work",
        no_false_attribution,
        f"False pipeline ownership={false_attribution_pipeline}, False k8s ownership={false_attribution_k8s}. "
        f"AI-generated summary noise must be filtered."
    )
    
    # ── CHECK 8: All-hands / standup attendance-only meetings NOT listed as user's work ──
    all_hands_as_work = bool(re.search(r'(全员大会|全体员工).{0,80}(主导|负责|完成|推进|林晓宇.*发言)', content))
    standup_noise = bool(re.search(r'(K8s.*扩容|存储迁移|监控大盘).{0,80}(林晓宇|主导|负责)', content))
    no_attendance_noise = not all_hands_as_work and not standup_noise
    add_check(
        "attendance_only_meetings_excluded",
        no_attendance_noise,
        f"All-hands as work={all_hands_as_work}, standup-only items as user work={standup_noise}"
    )
    
    # ── CHECK 9: Weekly breakdown has ≤3 lines per week (skimmable, not verbose) ──
    # Find weekly breakdown section
    weekly_section_match = re.search(r'按周回顾(.*?)(?=##|$)', content, re.DOTALL)
    weekly_ok = True
    weekly_detail = "Weekly section not found or structure unclear"
    if weekly_section_match:
        weekly_text = weekly_section_match.group(1)
        week_blocks = re.split(r'###\s*第\s*[1-4１２３４]\s*周', weekly_text)
        week_blocks = [b.strip() for b in week_blocks if b.strip()]
        violations = []
        for i, block in enumerate(week_blocks):
            # Count non-empty lines
            lines = [l for l in block.split('\n') if l.strip() and not l.strip().startswith('#')]
            if len(lines) > 3:
                violations.append(f"Week {i+1}: {len(lines)} lines (max 3)")
        weekly_ok = len(violations) == 0
        weekly_detail = f"Week blocks found: {len(week_blocks)}. Violations: {violations if violations else 'None'}"
    add_check(
        "weekly_breakdown_concise_max_3_lines",
        weekly_ok,
        weekly_detail
    )
    
    # ── CHECK 10: No "next-step suggestions" section (anti-pattern) ──
    has_next_steps_section = bool(re.search(r'(下一步建议|后续建议|建议.*下一步|next.?step)', content, re.IGNORECASE))
    add_check(
        "no_next_step_suggestions_section",
        not has_next_steps_section,
        f"'Next-step suggestions' section (anti-pattern) present: {has_next_steps_section}"
    )
    
    # ── CHECK 11: Soft verbs used for medium-confidence involvement ──
    # The cross-team coordination (data pipeline meeting where user was observer) should use soft verbs if mentioned
    # Also tech_radar discussion should use soft or be omitted
    soft_verb_check = True
    soft_verb_detail = "No problematic over-attribution found"
    # If tech radar is mentioned as user-led, that's wrong
    tech_radar_overstatement = bool(re.search(r'(主导|负责|推进).{0,40}(技术雷达|tech.?radar)', content, re.IGNORECASE))
    if tech_radar_overstatement:
        soft_verb_check = False
        soft_verb_detail = "Tech radar discussion (attendance only) overstated as user-owned work"
    add_check(
        "soft_verbs_for_uncertain_ownership",
        soft_verb_check,
        soft_verb_detail
    )
    
    # ── SCORING ──
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 3)
    
    # Must pass: file_exists + structure + no false attribution + Chinese + at least 6 total
    critical = [
        "file_exists",
        "written_in_chinese", 
        "proprietary_structure_sections",
        "no_false_attribution_of_others_work",
        "latency_work_with_ownership_signal",
    ]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical)
    overall_passed = critical_passed and passed_checks >= 8
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))