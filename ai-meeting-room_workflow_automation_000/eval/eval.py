import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def find_report(workspace):
    """Find meeting_report.md anywhere in workspace."""
    results = list(Path(workspace).rglob("meeting_report.md"))
    return results[0] if results else None

def load_text(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None

def run_eval(workspace):
    checks = []

    # ── 1. File existence ────────────────────────────────────────────────────
    report_path = find_report(workspace)
    if report_path is None:
        checks.append(check("file_exists", False, "meeting_report.md not found anywhere in workspace"))
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    text = load_text(report_path)
    if text is None or len(text.strip()) < 200:
        checks.append(check("file_exists", False, f"File found at {report_path} but is empty or too short"))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(check("file_exists", True, f"Found meeting_report.md at {report_path}, length={len(text)}"))

    text_lower = text.lower()

    # ── 2. Full Mode output structure (풀 모드) ──────────────────────────────
    # Must have the mandatory sections from 풀 모드 template
    required_sections = [
        ("30초 요약", r"30초\s*요약|30-second summary", "30초 요약 section"),
        ("사전 리서치", r"사전\s*리서치|pre.?research|리서치\s*브리핑", "사전 리서치 브리핑 section"),
        ("토론 전문", r"토론\s*전문|토론", "토론 전문 section"),
        ("핵심 논점", r"핵심\s*논점|핵심논점|논점.*합의|합의.*논점", "핵심 논점 & 합의 table"),
        ("데빌의 최종", r"데빌의\s*최종|데빌.*최종|최종.*데빌|😈.*최종|최종.*😈", "데빌의 최종 section"),
        ("액션 아이템", r"액션\s*아이템|액션아이템|action\s*item", "액션 아이템 section"),
        ("미합의", r"미합의|unresolved|리스크", "미합의 & 리스크 section"),
    ]

    section_passed = 0
    for sec_key, sec_pattern, sec_label in required_sections:
        found = bool(re.search(sec_pattern, text, re.IGNORECASE))
        checks.append(check(f"section_{sec_key}", found, f"{sec_label} {'found' if found else 'MISSING'}"))
        if found:
            section_passed += 1

    # ── 3. Correct meeting type: 사업성 검토 ─────────────────────────────────
    biz_review = bool(re.search(r"사업성\s*검토|사업성검토|business\s*review|feasibility", text, re.IGNORECASE))
    checks.append(check("meeting_type_biz_review", biz_review,
                         "Meeting correctly identified as 사업성 검토" if biz_review else "Meeting type 사업성 검토 not identified"))

    # ── 4. Mandatory agents present ─────────────────────────────────────────
    # 리오(의장) and 데빌 always required
    has_leo = bool(re.search(r"🦁|리오|의장", text))
    has_devil = bool(re.search(r"😈|데빌", text))
    checks.append(check("agent_leo_present", has_leo, "🦁 리오(의장) present" if has_leo else "🦁 리오 MISSING"))
    checks.append(check("agent_devil_present", has_devil, "😈 데빌 present" if has_devil else "😈 데빌 MISSING"))

    # At least 3 expert agents from the pool (for F&B: scout, analyst, copy, legal, growth)
    expert_agents = {
        "스카우트": r"🦊|스카우트",
        "애널": r"📊|애널",
        "카피": r"🐝|카피",
        "리걸": r"⚖️|리걸",
        "그로스": r"🎯|그로스",
        "투자자": r"💰|투자자",
    }
    found_experts = []
    for name, pattern in expert_agents.items():
        if re.search(pattern, text):
            found_experts.append(name)
    expert_count_ok = len(found_experts) >= 3
    checks.append(check("expert_agents_min3", expert_count_ok,
                         f"Found {len(found_experts)} expert agents: {found_experts}. Need >= 3"))

    # ── 5. Dialogue format: ping-pong (not monologue) ────────────────────────
    # The debate section should show rapid back-and-forth
    # Evidence: agent emoji/name appears many times, no single block > ~300 chars between agent markers
    agent_marker_pattern = r"(🦁|😈|🦊|📊|🐝|⚖️|🎯|💰|🌍|🔧|🎨|🧠|👥)"
    agent_markers = re.findall(agent_marker_pattern, text)
    many_turns = len(agent_markers) >= 15  # at least 15 agent speaking turns = ping-pong
    checks.append(check("dialogue_pingpong_turns", many_turns,
                         f"Found {len(agent_markers)} agent speaking turns (need >=15 for ping-pong format)"))

    # ── 6. Direct name-calling rebuttals ─────────────────────────────────────
    # Pattern: agent calls another agent by name while disagreeing
    name_call_patterns = [
        r"(스카우트|애널|카피|리걸|데빌|그로스|투자자|리오).{0,20}(틀렸|아니야|잠깐|잠시|그건|맞아\?|어디서|출처|그 숫자|그게|그건)",
        r"(잠깐|아니|그건|틀렸).{0,30}(스카우트|애널|카피|리걸|데빌|그로스|투자자)",
    ]
    direct_rebuttals = 0
    for pat in name_call_patterns:
        matches = re.findall(pat, text, re.IGNORECASE)
        direct_rebuttals += len(matches)
    rebuttals_ok = direct_rebuttals >= 2
    checks.append(check("direct_rebuttals_min2", rebuttals_ok,
                         f"Found ~{direct_rebuttals} direct name-calling rebuttals (need >=2)"))

    # ── 7. Opinion change present ────────────────────────────────────────────
    opinion_change = bool(re.search(
        r"아까.{0,30}틀렸|내가\s*틀렸|처음엔.{0,50}인데.{0,50}(지금|이제|보니|알고보니)|설득.{0,20}됐|맞네|그말이\s*맞|맞는\s*것\s*같|인정",
        text, re.IGNORECASE
    ))
    checks.append(check("opinion_change_present", opinion_change,
                         "Opinion change found (agent admits error or is persuaded)" if opinion_change
                         else "No opinion change found — required by SKILL.md"))

    # ── 8. Devil's extreme questions (min 2) ─────────────────────────────────
    # Devil should have strong, extreme statements — look for Devil speaking multiple times with strong language
    devil_speech_blocks = re.findall(r"😈[^😈🦁🦊📊🐝⚖️🎯💰🌍🔧🎨🧠👥]{20,}", text)
    devil_turns = len(devil_speech_blocks)
    devil_extreme = bool(re.search(
        r"(망해|폐업|실패|0원|없어|안\s*돼|불가능|위험|죽어|버텨|버틸|살아남|30초|설명해봐|투자\s*안|이유\s*3|3가지\s*이유)",
        text, re.IGNORECASE
    ))
    devil_ok = devil_turns >= 2 and devil_extreme
    checks.append(check("devil_extreme_min2", devil_ok,
                         f"Devil has {devil_turns} speech blocks and extreme language={'yes' if devil_extreme else 'no'}"))

    # ── 9. Quality gate: concrete numbers with sources ────────────────────────
    # Numbers with units and source citations
    numbers_with_source = re.findall(
        r"\d[\d,]*\s*(조원|억원|만원|원|%|명|개|회|배|위|만\s*명|억\s*명).{0,100}(통계청|공정위|닐슨|유로모니터|출처|리포트|기준|자료|IRI|식약처|aT|한국농수산)",
        text, re.IGNORECASE
    )
    has_numbers_sources = len(numbers_with_source) >= 2
    checks.append(check("quality_numbers_with_sources", has_numbers_sources,
                         f"Found {len(numbers_with_source)} number+source pairs (need >=2)"))

    # ── 10. Real failure case cited ──────────────────────────────────────────
    failure_case = bool(re.search(
        r"(실패|망한|폐업|철수|단종|중단).{0,50}(사례|경우|예|예시|회사|브랜드|제품|서비스)",
        text, re.IGNORECASE
    ))
    checks.append(check("failure_case_cited", failure_case,
                         "Failure case cited" if failure_case else "No failure case found — required by SKILL.md"))

    # ── 11. Action items as decision tree (if X → A, else B) ─────────────────
    decision_tree = bool(re.search(
        r"(이상|초과|달성|성공|성과).{0,40}(→|->|이면|면\s*A|면\s*확장|면\s*진행).{0,80}(미달|미만|실패|부족).{0,40}(→|->|이면|피벗|B로|중단)",
        text, re.IGNORECASE
    ))
    # Also check table format with 성공 시 → and 실패 시 →
    decision_tree2 = bool(re.search(r"성공\s*(시|하면|이면).{0,30}(→|이후|다음).{0,100}실패\s*(시|하면|이면)", text, re.IGNORECASE))
    decision_tree3 = bool(re.search(r"(A로\s*확장|B로\s*피벗|피벗\s*방향|다음\s*단계)", text, re.IGNORECASE))
    dt_ok = decision_tree or decision_tree2 or decision_tree3
    checks.append(check("action_decision_tree", dt_ok,
                         "Decision tree action items found (if X → A, else → B)" if dt_ok
                         else "Action items not in decision tree format — '마케팅 강화' style is banned"))

    # ── 12. No forbidden phrases (quality gate) ──────────────────────────────
    forbidden = [
        r"시장\s*조사를\s*하세요",
        r"타겟을\s*정하세요",
        r"차별화하세요(?!\s*[.。]?.{0,5}(방법|전략|구체|어떻게))",
        r"검토가\s*필요합니다",
        r"리스크가\s*있을\s*수\s*있습니다(?!\s*[.。]?.{0,20}(왜냐|구체|얼마|어떤))",
    ]
    forbidden_found = []
    for pat in forbidden:
        if re.search(pat, text, re.IGNORECASE):
            forbidden_found.append(pat)
    no_forbidden = len(forbidden_found) == 0
    checks.append(check("no_forbidden_phrases", no_forbidden,
                         f"No forbidden phrases found" if no_forbidden
                         else f"Forbidden phrases found: {forbidden_found}"))

    # ── 13. Go / No-Go conclusion present ───────────────────────────────────
    conclusion = bool(re.search(r"(Go|No-Go|조건부\s*Go|No\s*Go|노고|고\b)", text, re.IGNORECASE))
    checks.append(check("conclusion_go_nogo", conclusion,
                         "Go/No-Go conclusion present" if conclusion else "No Go/No-Go conclusion found"))

    # ── 14. Thought process exposed ─────────────────────────────────────────
    thought_process = bool(re.search(
        r"(처음엔|처음에는|초반에).{0,60}(봤는데|생각했는데|봤지만).{0,60}(이제|지금|보니|알고보니|데이터|수치)",
        text, re.IGNORECASE
    ))
    checks.append(check("thought_process_exposed", thought_process,
                         "Thought process exposed (처음엔 A → 데이터 보니 B)" if thought_process
                         else "No thought process exposure found — required by SKILL.md"))

    # ── 15. Consensus table present ─────────────────────────────────────────
    table_markers = text.count("|")
    has_table = table_markers >= 10  # markdown table needs many pipes
    checks.append(check("consensus_table_present", has_table,
                         f"Table structure found ({table_markers} pipe chars)" if has_table
                         else "No markdown table found for 핵심 논점 & 합의"))

    # ── Final scoring ────────────────────────────────────────────────────────
    # Weights
    weighted = [
        ("file_exists", 1.0),
        ("section_30초 요약", 0.5),
        ("section_사전 리서치", 0.5),
        ("section_토론 전문", 0.5),
        ("section_핵심 논점", 0.5),
        ("section_데빌의 최종", 0.5),
        ("section_액션 아이템", 0.5),
        ("section_미합의", 0.3),
        ("meeting_type_biz_review", 0.5),
        ("agent_leo_present", 0.5),
        ("agent_devil_present", 0.8),
        ("expert_agents_min3", 0.5),
        ("dialogue_pingpong_turns", 1.0),
        ("direct_rebuttals_min2", 1.0),
        ("opinion_change_present", 0.8),
        ("devil_extreme_min2", 0.8),
        ("quality_numbers_with_sources", 0.8),
        ("failure_case_cited", 0.7),
        ("action_decision_tree", 1.0),
        ("no_forbidden_phrases", 0.5),
        ("conclusion_go_nogo", 0.5),
        ("thought_process_exposed", 0.7),
        ("consensus_table_present", 0.5),
    ]

    check_map = {c["name"]: c["passed"] for c in checks}
    total_weight = sum(w for _, w in weighted)
    earned = sum(w for name, w in weighted if check_map.get(name, False))
    score = round(earned / total_weight, 3)

    # Must pass critical checks to overall pass
    critical = ["file_exists", "agent_devil_present", "dialogue_pingpong_turns",
                "direct_rebuttals_min2", "action_decision_tree", "section_액션 아이템",
                "section_데빌의 최종", "section_토론 전문"]
    critical_passed = all(check_map.get(c, False) for c in critical)

    overall_passed = critical_passed and score >= 0.65

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        result = run_eval(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": f"Evaluator crashed: {e}"}]
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))