import sys
import json
import os
from pathlib import Path

def load_json_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def check_text_contains_any(text, keywords):
    """Return True if text contains any of the keywords (case-insensitive Chinese-friendly)."""
    if not isinstance(text, str):
        text = json.dumps(text, ensure_ascii=False)
    return any(kw in text for kw in keywords)

def entry_to_full_text(entry):
    """Flatten an entry dict to a single string for keyword scanning."""
    return json.dumps(entry, ensure_ascii=False)

def evaluate(workspace):
    checks = []
    score_parts = []

    # ── Locate coaching_responses.json ───────────────────────────────────────
    candidates = list(Path(workspace).rglob("coaching_responses.json"))
    file_found = len(candidates) > 0

    checks.append({
        "name": "coaching_responses.json exists",
        "passed": file_found,
        "detail": f"Found at: {candidates[0]}" if file_found else "File not found anywhere in workspace."
    })
    score_parts.append(1.0 if file_found else 0.0)

    if not file_found:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    # ── Parse JSON ────────────────────────────────────────────────────────────
    try:
        data = load_json_file(candidates[0])
    except Exception as e:
        checks.append({"name": "JSON parseable", "passed": False, "detail": str(e)})
        score_parts.append(0.0)
        return {"passed": False, "score": round(sum(score_parts)/len(score_parts), 3), "checks": checks}

    checks.append({"name": "JSON parseable", "passed": True, "detail": "OK"})
    score_parts.append(1.0)

    # ── Must have 3 entries ───────────────────────────────────────────────────
    # Accept either a list of 3, or a dict with 3 top-level keys
    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        entries = list(data.values())
    else:
        entries = []

    has_three = len(entries) == 3
    checks.append({
        "name": "Contains exactly 3 case entries",
        "passed": has_three,
        "detail": f"Found {len(entries)} entries."
    })
    score_parts.append(1.0 if has_three else 0.0)

    full_text = json.dumps(data, ensure_ascii=False)

    # ══════════════════════════════════════════════════════════════════════════
    # CASE 1 — 分手/挽回 checks (scenario_1: 小明/小美)
    # ══════════════════════════════════════════════════════════════════════════

    # 1a. Stage correctly identified as 分手/挽回
    stage_breakup_keywords = ["分手", "挽回", "分手/挽回", "breakup"]
    stage1_ok = check_text_contains_any(full_text, stage_breakup_keywords)
    checks.append({
        "name": "Case1: 关系阶段 = 分手/挽回",
        "passed": stage1_ok,
        "detail": "Expected 分手/挽回 stage to be identified and referenced." if not stage1_ok else "OK"
    })
    score_parts.append(1.0 if stage1_ok else 0.0)

    # 1b. All 4 required sub-sections for 分手挽回 type are present
    breakup_subsections = ["分手原因分析", "断联策略", "重建吸引", "挽回话术"]
    subsection_results = []
    for sub in breakup_subsections:
        present = sub in full_text
        subsection_results.append(present)
        checks.append({
            "name": f"Case1: 分手挽回子项 — {sub}",
            "passed": present,
            "detail": "Present in output." if present else f"Missing required sub-section: {sub}"
        })
        score_parts.append(1.0 if present else 0.0)

    # 1c. Personality strategy for 外向 user + 感性 target
    # 外向 → 直接幽默，带动气氛; 感性 → 情感共鸣，表达真心
    personality_keywords_1 = ["情感共鸣", "表达真心", "感性", "真心", "真诚", "直接", "幽默"]
    p1_ok = check_text_contains_any(full_text, personality_keywords_1)
    checks.append({
        "name": "Case1: 性格策略匹配 (外向用户/感性对象)",
        "passed": p1_ok,
        "detail": "Expected personality-matched strategy." if not p1_ok else "OK"
    })
    score_parts.append(1.0 if p1_ok else 0.0)

    # 1d. Strategy for 分手/挽回 core (分析问题, 重建吸引)
    strategy_keywords_1 = ["重建吸引", "断联", "冷静", "分析"]
    s1_ok = check_text_contains_any(full_text, strategy_keywords_1)
    checks.append({
        "name": "Case1: 核心策略 (分析问题/重建吸引/断联)",
        "passed": s1_ok,
        "detail": "Expected 分手/挽回 core strategy keywords." if not s1_ok else "OK"
    })
    score_parts.append(1.0 if s1_ok else 0.0)

    # ══════════════════════════════════════════════════════════════════════════
    # CASE 2 — 暧昧期 checks (scenario_2: James/晓雯)
    # ══════════════════════════════════════════════════════════════════════════

    # 2a. Stage correctly identified as 暧昧期
    stage_ambiguous_keywords = ["暧昧期", "暧昧", "没挑明"]
    stage2_ok = check_text_contains_any(full_text, stage_ambiguous_keywords)
    checks.append({
        "name": "Case2: 关系阶段 = 暧昧期",
        "passed": stage2_ok,
        "detail": "Expected 暧昧期 to be identified." if not stage2_ok else "OK"
    })
    score_parts.append(1.0 if stage2_ok else 0.0)

    # 2b. Core strategy for 暧昧期 (推拉互动, 制造心动, 升级关系)
    ambiguous_strategy_kw = ["推拉", "制造心动", "升级关系", "推拉互动", "心动"]
    s2_ok = check_text_contains_any(full_text, ambiguous_strategy_kw)
    checks.append({
        "name": "Case2: 核心策略 (推拉互动/制造心动/升级关系)",
        "passed": s2_ok,
        "detail": "Expected 暧昧期 strategy keywords." if not s2_ok else "OK"
    })
    score_parts.append(1.0 if s2_ok else 0.0)

    # 2c. User personality = 理性 → 逻辑沟通，展示上进心
    rational_kw = ["逻辑", "上进心", "理性", "条理", "逻辑沟通"]
    r2_ok = check_text_contains_any(full_text, rational_kw)
    checks.append({
        "name": "Case2: 理性用户性格策略 (逻辑沟通/展示上进心)",
        "passed": r2_ok,
        "detail": "Expected 理性 personality strategy." if not r2_ok else "OK"
    })
    score_parts.append(1.0 if r2_ok else 0.0)

    # 2d. Target is 内向 → 循序渐进，用真诚打动
    introverted_kw = ["内向", "循序渐进", "真诚", "慢慢"]
    i2_ok = check_text_contains_any(full_text, introverted_kw)
    checks.append({
        "name": "Case2: 内向对象策略 (循序渐进/真诚打动)",
        "passed": i2_ok,
        "detail": "Expected 内向 target strategy." if not i2_ok else "OK"
    })
    score_parts.append(1.0 if i2_ok else 0.0)

    # 2e. Talk-track type includes 聊天话术 or 约会安排 sub-elements
    case2_talk_kw = ["约会选址", "约会流程", "推拉技巧", "欲擒故纵", "框架设置", "约会安排", "聊天话术", "带领节奏"]
    t2_ok = check_text_contains_any(full_text, case2_talk_kw)
    checks.append({
        "name": "Case2: 话术类型包含聊天话术或约会安排子项",
        "passed": t2_ok,
        "detail": "Expected chat/date talk-track sub-elements." if not t2_ok else "OK"
    })
    score_parts.append(1.0 if t2_ok else 0.0)

    # ══════════════════════════════════════════════════════════════════════════
    # CASE 3 — 搭讪/认识期 checks (scenario_3: 阿杰/图书馆女生)
    # ══════════════════════════════════════════════════════════════════════════

    # 3a. Stage correctly identified as 认识期 or related to 搭讪
    stage_pickup_keywords = ["认识期", "搭讪", "刚认识", "建立安全感", "展示价值", "引起兴趣"]
    stage3_ok = check_text_contains_any(full_text, stage_pickup_keywords)
    checks.append({
        "name": "Case3: 关系阶段 = 认识期/搭讪",
        "passed": stage3_ok,
        "detail": "Expected 认识期 or 搭讪 stage." if not stage3_ok else "OK"
    })
    score_parts.append(1.0 if stage3_ok else 0.0)

    # 3b. Required 搭讪开场 sub-elements present
    pickup_subsections = ["自然开场白", "制造话题", "展示价值", "合理收号"]
    pickup_any = [s for s in pickup_subsections if s in full_text]
    pickup_ok = len(pickup_any) >= 2  # at least 2 of 4 sub-sections
    checks.append({
        "name": "Case3: 搭讪开场子项 (至少2个: 自然开场白/制造话题/展示价值/合理收号)",
        "passed": pickup_ok,
        "detail": f"Found sub-sections: {pickup_any}" if pickup_ok else f"Only found: {pickup_any}. Need ≥2."
    })
    score_parts.append(1.0 if pickup_ok else 0.0)

    # 3c. Strategy aligned with 认识期 core (建立安全感/展示价值/引起兴趣)
    core_pickup_kw = ["建立安全感", "展示价值", "引起兴趣", "安全感"]
    cp3_ok = check_text_contains_any(full_text, core_pickup_kw)
    checks.append({
        "name": "Case3: 认识期核心策略 (建立安全感/展示价值/引起兴趣)",
        "passed": cp3_ok,
        "detail": "Expected 认识期 core strategy." if not cp3_ok else "OK"
    })
    score_parts.append(1.0 if cp3_ok else 0.0)

    # 3d. User is 内向 → 循序渐进，用真诚打动
    introverted3_kw = ["内向", "循序渐进", "真诚打动", "真诚", "慢慢来"]
    i3_ok = check_text_contains_any(full_text, introverted3_kw)
    checks.append({
        "name": "Case3: 内向用户性格策略",
        "passed": i3_ok,
        "detail": "Expected 内向 personality strategy for user." if not i3_ok else "OK"
    })
    score_parts.append(1.0 if i3_ok else 0.0)

    # ══════════════════════════════════════════════════════════════════════════
    # GLOBAL FORMAT CHECKS
    # ══════════════════════════════════════════════════════════════════════════

    # Output format types — at least 2 of the 4 must appear
    output_format_types = ["话术生成", "策略分析", "技巧讲解", "案例分析"]
    found_formats = [f for f in output_format_types if f in full_text]
    fmt_ok = len(found_formats) >= 2
    checks.append({
        "name": "全局: 输出格式类型标记 (至少2种: 话术生成/策略分析/技巧讲解/案例分析)",
        "passed": fmt_ok,
        "detail": f"Found format types: {found_formats}" if fmt_ok else f"Only found: {found_formats}. Need ≥2."
    })
    score_parts.append(1.0 if fmt_ok else 0.0)

    # Safety check: no harmful/vulgar content markers
    banned_terms = ["骚扰", "低俗", "违法"]
    safety_ok = not any(term in full_text for term in ["我要强迫", "骚扰她", "违法手段"])
    checks.append({
        "name": "全局: 内容合规 (无违法/骚扰内容)",
        "passed": safety_ok,
        "detail": "Content appears compliant." if safety_ok else "Potentially non-compliant content detected."
    })
    score_parts.append(1.0 if safety_ok else 0.0)

    # ── Final score ───────────────────────────────────────────────────────────
    total = len(score_parts)
    passed_count = sum(score_parts)
    final_score = round(passed_count / total, 3)
    overall_passed = final_score >= 0.70

    return {
        "passed": overall_passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        result = evaluate(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": str(e)}]
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))