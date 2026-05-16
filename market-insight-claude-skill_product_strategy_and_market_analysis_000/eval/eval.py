import sys
import json
import re
from pathlib import Path

def find_report(workspace):
    """Find the insight report file."""
    ws = Path(workspace)
    # Search for the specific filename requested in the prompt
    candidates = list(ws.rglob("insight_report.md"))
    if not candidates:
        # Also accept insight_report.txt as fallback
        candidates = list(ws.rglob("insight_report.txt"))
    return candidates[0] if candidates else None

def check_text(content, patterns, require_all=True):
    """Check if content matches patterns."""
    if require_all:
        return all(re.search(p, content, re.IGNORECASE | re.DOTALL) for p in patterns)
    return any(re.search(p, content, re.IGNORECASE | re.DOTALL) for p in patterns)

def run_eval(workspace):
    checks = []
    score = 0.0

    # --- CHECK 0: File exists ---
    report_path = find_report(workspace)
    file_exists = report_path is not None
    checks.append({
        "name": "report_file_exists",
        "passed": file_exists,
        "detail": f"Found at: {report_path}" if file_exists else "insight_report.md not found in workspace tree"
    })
    if not file_exists:
        return {"passed": False, "score": 0.0, "checks": checks}

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # --- CHECK 1: Has exactly 4 distinct user persona sections (A/B/C/D class or equivalent) ---
    try:
        # Look for 4 distinct persona sections - could be A类/B类/C类/D类 or numbered
        persona_patterns = [
            r'[A-D]类|类型\s*[A-D]|画像\s*[1-4]|第[一二三四]类|用户[1-4]',
        ]
        # Count persona headers
        persona_matches_abcd = re.findall(r'[A-D]类[：:：]', content)
        persona_matches_numbered = re.findall(r'画像\s*[1-4]|类型\s*[1-4]', content)
        persona_section_count = len(persona_matches_abcd) + len(persona_matches_numbered)

        # Alternative: count section headers that look like distinct personas
        section_headers = re.findall(r'#{1,3}\s*[A-D]类|#{1,3}\s*.*?(?:派|族|人|者|型)\b', content)

        passed_4_personas = persona_section_count >= 4 or len(section_headers) >= 4

        checks.append({
            "name": "four_user_personas",
            "passed": passed_4_personas,
            "detail": f"Found {persona_section_count} A/B/C/D类 markers, {len(section_headers)} persona section headers. Need 4 distinct personas."
        })
    except Exception as e:
        checks.append({"name": "four_user_personas", "passed": False, "detail": str(e)})

    # --- CHECK 2: Behavior-driven naming (具象化命名 - evocative names, NOT just age/gender demographics) ---
    try:
        # Good: names ending in 派/族/者/人 with descriptive adjectives
        evocative_names = re.findall(r'[^\s，,。.]{2,12}(?:派|族|人|者|型|控|党)', content)
        # Bad: pure demographic labels
        demographic_only = re.findall(r'(?:25-35岁|男性用户|女性用户|学生群体|上班族$)', content)

        passed_naming = len(evocative_names) >= 3
        checks.append({
            "name": "behavior_driven_naming",
            "passed": passed_naming,
            "detail": f"Found {len(evocative_names)} evocative persona names (e.g., '焦虑释放派'): {evocative_names[:5]}. Need ≥3 behavior-driven names."
        })
    except Exception as e:
        checks.append({"name": "behavior_driven_naming", "passed": False, "detail": str(e)})

    # --- CHECK 3: Core user marked (⭐ or explicit 核心用户 designation) ---
    try:
        core_user_marked = bool(re.search(r'⭐|核心用户|★|【核心】|核心群体', content))
        checks.append({
            "name": "core_user_marked",
            "passed": core_user_marked,
            "detail": "⭐ or 核心用户 marker found in content." if core_user_marked else "No core user marking (⭐ or 核心用户) found."
        })
    except Exception as e:
        checks.append({"name": "core_user_marked", "passed": False, "detail": str(e)})

    # --- CHECK 4: Core user justification uses the THREE proprietary criteria ---
    try:
        has_repurchase = bool(re.search(r'复购|复购频次|复购率|高频', content))
        has_anticyclical = bool(re.search(r'抗周期|抗周期性|不受.*周期|穿越.*周期', content))
        has_addiction = bool(re.search(r'成瘾|成瘾性|上瘾|依赖性', content))

        criteria_count = sum([has_repurchase, has_anticyclical, has_addiction])
        passed_criteria = criteria_count >= 2  # require at least 2 of 3

        checks.append({
            "name": "core_user_justification_criteria",
            "passed": passed_criteria,
            "detail": f"Proprietary criteria found: 复购频次={has_repurchase}, 抗周期性={has_anticyclical}, 成瘾性={has_addiction}. Found {criteria_count}/3 criteria."
        })
    except Exception as e:
        checks.append({"name": "core_user_justification_criteria", "passed": False, "detail": str(e)})

    # --- CHECK 5: Emotional analysis has all THREE dimensions (痛点/痒点/爽点) ---
    try:
        has_pain = bool(re.search(r'痛点', content))
        has_itch = bool(re.search(r'痒点', content))
        has_joy = bool(re.search(r'爽点', content))
        all_three = has_pain and has_itch and has_joy

        checks.append({
            "name": "three_emotional_dimensions",
            "passed": all_three,
            "detail": f"痛点={has_pain}, 痒点={has_itch}, 爽点={has_joy}. All three emotional dimensions required."
        })
    except Exception as e:
        checks.append({"name": "three_emotional_dimensions", "passed": False, "detail": str(e)})

    # --- CHECK 6: Each emotional dimension has 文案表达 (copywriting expressions) ---
    try:
        # Look for quoted copywriting expressions or 文案 labels
        copywriting_markers = re.findall(r'文案[表达]*[：:：]|"[^"]{10,}"|"[^"]{10,}"', content)
        has_copywriting = len(copywriting_markers) >= 2

        checks.append({
            "name": "copywriting_expressions_present",
            "passed": has_copywriting,
            "detail": f"Found {len(copywriting_markers)} copywriting expression markers. Need ≥2 文案表达 entries."
        })
    except Exception as e:
        checks.append({"name": "copywriting_expressions_present", "passed": False, "detail": str(e)})

    # --- CHECK 7: 爽点 includes physical/sensory details (生理细节) ---
    try:
        # The 爽点 section should have sensory/physical details - look near 爽点 for sensory words
        joy_section = re.search(r'爽点.{0,800}', content, re.DOTALL)
        sensory_words = ['℃|度|分钟|秒|呼吸|心跳|身体|肌肉|大脑|生理|感官|触觉|听觉|视觉|温度|节奏', ]
        has_sensory = False
        if joy_section:
            joy_text = joy_section.group(0)
            has_sensory = bool(re.search(sensory_words[0], joy_text))

        checks.append({
            "name": "joy_point_sensory_details",
            "passed": has_sensory,
            "detail": "Sensory/physical detail found in 爽点 section." if has_sensory else "Missing sensory/physical details in 爽点 section (e.g., temperature, duration, breathing, body sensation)."
        })
    except Exception as e:
        checks.append({"name": "joy_point_sensory_details", "passed": False, "detail": str(e)})

    # --- CHECK 8: P0/P1/P2 priority tiers all present ---
    try:
        has_p0 = bool(re.search(r'P0', content))
        has_p1 = bool(re.search(r'P1', content))
        has_p2 = bool(re.search(r'P2', content))
        all_tiers = has_p0 and has_p1 and has_p2

        checks.append({
            "name": "p0_p1_p2_tiers_present",
            "passed": all_tiers,
            "detail": f"P0={has_p0}, P1={has_p1}, P2={has_p2}. All three priority tiers required."
        })
    except Exception as e:
        checks.append({"name": "p0_p1_p2_tiers_present", "passed": False, "detail": str(e)})

    # --- CHECK 9: Each product opportunity has cost and difficulty fields ---
    try:
        has_cost = bool(re.search(r'成本[：:：\s]*(?:低|中|高)', content))
        has_difficulty = bool(re.search(r'(?:执行难度|难度)[：:：\s]*(?:易|中|难)', content))

        passed_fields = has_cost and has_difficulty
        checks.append({
            "name": "product_opportunity_structured_fields",
            "passed": passed_fields,
            "detail": f"成本(低/中/高)={has_cost}, 难度(易/中/难)={has_difficulty}. Both cost and difficulty fields with proper values required."
        })
    except Exception as e:
        checks.append({"name": "product_opportunity_structured_fields", "passed": False, "detail": str(e)})

    # --- CHECK 10: Product opportunities map back to specific emotional drivers ---
    try:
        # Each P-tier item should reference which emotional type it addresses
        emotional_reference = re.findall(r'(?:对应情绪|对应.*?(?:痛点|痒点|爽点)|基于.*?(?:痛点|痒点|爽点))', content)
        has_emotional_mapping = len(emotional_reference) >= 2

        checks.append({
            "name": "opportunity_to_emotion_mapping",
            "passed": has_emotional_mapping,
            "detail": f"Found {len(emotional_reference)} emotional driver mappings in product opportunities. Need ≥2."
        })
    except Exception as e:
        checks.append({"name": "opportunity_to_emotion_mapping", "passed": False, "detail": str(e)})

    # --- CHECK 11: Report covers MindWave app (not generic / copy-pasted from 胡辣汤 example) ---
    try:
        is_mindwave = bool(re.search(r'MindWave|正念|冥想|mindwave', content, re.IGNORECASE))
        is_not_hotpot = not bool(re.search(r'胡辣汤|水煎包', content))

        passed_domain = is_mindwave and is_not_hotpot
        checks.append({
            "name": "correct_domain_mindwave",
            "passed": passed_domain,
            "detail": f"Contains MindWave/冥想 content={is_mindwave}, avoids 胡辣汤 example content={is_not_hotpot}."
        })
    except Exception as e:
        checks.append({"name": "correct_domain_mindwave", "passed": False, "detail": str(e)})

    # --- CHECK 12: Persona sections contain 行为特征 and 消费场景 fields ---
    try:
        has_behavior = bool(re.search(r'行为特征|行为描述|真实行为', content))
        has_scene = bool(re.search(r'消费场景|使用场景|典型场景', content))
        has_value_judgment = bool(re.search(r'价值判断|复购潜力|价值评估', content))

        persona_structure = sum([has_behavior, has_scene, has_value_judgment])
        passed_persona_structure = persona_structure >= 2

        checks.append({
            "name": "persona_required_fields",
            "passed": passed_persona_structure,
            "detail": f"行为特征={has_behavior}, 消费场景={has_scene}, 价值判断={has_value_judgment}. Found {persona_structure}/3 required persona fields."
        })
    except Exception as e:
        checks.append({"name": "persona_required_fields", "passed": False, "detail": str(e)})

    # --- Calculate Score ---
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = len(passed_checks) / total

    # Must pass critical checks to be considered overall passed
    critical_checks = [
        "report_file_exists",
        "four_user_personas",
        "three_emotional_dimensions",
        "p0_p1_p2_tiers_present",
        "core_user_marked",
        "correct_domain_mindwave",
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