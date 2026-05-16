import sys
import json
import re
from pathlib import Path

def load_json_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_eval(workspace_dir):
    checks = []
    total_score = 0.0

    # --- Find the output file ---
    output_path = None
    candidates = list(Path(workspace_dir).rglob("audit_report.json"))
    if candidates:
        output_path = candidates[0]

    if not output_path or not output_path.exists():
        checks.append({"name": "output_file_exists", "passed": False, "detail": "audit_report.json not found anywhere in workspace."})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found at {output_path}"})

    try:
        report = load_json_file(output_path)
    except Exception as e:
        checks.append({"name": "json_parseable", "passed": False, "detail": f"Failed to parse JSON: {e}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "json_parseable", "passed": True, "detail": "JSON parsed successfully."})

    # =====================================================================
    # CHECK 1: 脑洞扩展 (Brain-Storming Expansion) using a named 脑洞法
    # The agent must use one of the four 脑洞法 from Chapter 3:
    # 强制关联法, 量级放大法, 逻辑颠倒法, 系统弹窗法
    # =====================================================================
    VALID_BRAINSTORM_METHODS = ["强制关联法", "量级放大法", "逻辑颠倒法", "系统弹窗法"]

    brainstorm_section = report.get("brainstorm_expansion", report.get("脑洞扩展", None))
    
    check_brainstorm_exists = brainstorm_section is not None
    checks.append({
        "name": "brainstorm_section_exists",
        "passed": check_brainstorm_exists,
        "detail": "brainstorm_expansion (or 脑洞扩展) key found in report." if check_brainstorm_exists else "Missing brainstorm_expansion section."
    })

    if check_brainstorm_exists:
        brainstorm_str = json.dumps(brainstorm_section, ensure_ascii=False)
        method_used = None
        for m in VALID_BRAINSTORM_METHODS:
            if m in brainstorm_str:
                method_used = m
                break
        method_named = method_used is not None
        checks.append({
            "name": "brainstorm_method_named",
            "passed": method_named,
            "detail": f"Named 脑洞法 found: '{method_used}'." if method_named else f"No valid 脑洞法 name found. Must be one of {VALID_BRAINSTORM_METHODS}."
        })
        # Check expansion has actual content (>50 chars)
        content_len = len(brainstorm_str) > 80
        checks.append({
            "name": "brainstorm_has_content",
            "passed": content_len,
            "detail": f"Brainstorm content length: {len(brainstorm_str)} chars." 
        })
        if method_named and content_len:
            total_score += 20.0
        elif content_len:
            total_score += 8.0
    
    # =====================================================================
    # CHECK 2: Titles — must have at least 3 titles, each labeled with one of the 4 proprietary formula names
    # 四大标题公式: 疯批逻辑法, 偷家战术法, 极致不对等法, 降维打击法
    # =====================================================================
    VALID_TITLE_FORMULAS = ["疯批逻辑法", "偷家战术法", "极致不对等法", "降维打击法"]

    titles_section = report.get("titles", report.get("标题", None))
    titles_section_exists = titles_section is not None
    checks.append({
        "name": "titles_section_exists",
        "passed": titles_section_exists,
        "detail": "titles (or 标题) key found." if titles_section_exists else "Missing titles section."
    })

    if titles_section_exists:
        # Find all formula names mentioned in titles section
        titles_str = json.dumps(titles_section, ensure_ascii=False)
        formulas_found = [f for f in VALID_TITLE_FORMULAS if f in titles_str]
        
        has_min_2_formulas = len(formulas_found) >= 2
        checks.append({
            "name": "titles_use_proprietary_formulas",
            "passed": has_min_2_formulas,
            "detail": f"Found formula labels: {formulas_found}. Need at least 2 distinct formulas."
        })

        # Count number of title entries
        if isinstance(titles_section, list):
            num_titles = len(titles_section)
        elif isinstance(titles_section, dict):
            num_titles = len(titles_section)
        else:
            num_titles = titles_str.count("法") 
        
        has_3_titles = num_titles >= 3
        checks.append({
            "name": "titles_count_at_least_3",
            "passed": has_3_titles,
            "detail": f"Found {num_titles} title entries (need ≥3)."
        })

        # Check 4-dimension scoring is present: 后果, 反差, 绝情, 地位
        FOUR_DIMS = ["后果", "反差", "绝情", "地位"]
        dims_found = [d for d in FOUR_DIMS if d in titles_str]
        has_4dim_scoring = len(dims_found) >= 3
        checks.append({
            "name": "titles_4dim_self_check",
            "passed": has_4dim_scoring,
            "detail": f"4-dimension scoring found: {dims_found}. Need ≥3 of {FOUR_DIMS}."
        })

        if has_min_2_formulas and has_3_titles and has_4dim_scoring:
            total_score += 30.0
        elif has_min_2_formulas and has_3_titles:
            total_score += 18.0
        elif has_min_2_formulas or has_3_titles:
            total_score += 8.0

    # =====================================================================
    # CHECK 3: Polished Passage — 三刀流 applied correctly
    # Must demonstrate:
    # a) Removal/reduction of logical connectors (因为、所以、为了、试图)
    # b) Replacement of adjective-emotion words with physiological reactions
    # c) Short paragraphs (no paragraph > ~60 Chinese characters in a single block)
    # d) Mention of the 三刀流 method or 四句顺口溜 in annotation
    # =====================================================================
    polish_section = report.get("polished_passage", report.get("润色正文", None))
    polish_section_exists = polish_section is not None
    checks.append({
        "name": "polish_section_exists",
        "passed": polish_section_exists,
        "detail": "polished_passage (or 润色正文) key found." if polish_section_exists else "Missing polished_passage section."
    })

    if polish_section_exists:
        polish_str = json.dumps(polish_section, ensure_ascii=False)

        # a) Logical connectors reduced
        # Original had: 因为(x3), 所以(x2), 为了(x1), 试图(x1)
        # After polish, total count should be ≤ 2 (significantly reduced)
        connector_count = sum(polish_str.count(c) for c in ["因为", "所以", "为了", "试图"])
        connectors_reduced = connector_count <= 3  # generous threshold
        checks.append({
            "name": "polish_connectors_reduced",
            "passed": connectors_reduced,
            "detail": f"Logical connector occurrences in polished output: {connector_count} (原文有7处, need ≤3)."
        })

        # b) Physiological reaction replacement
        # Look for physical action language — body part words or vivid physical verbs
        PHYSICAL_MARKERS = ["抓", "砸", "摔", "攥", "抖", "颤", "捏", "抬头", "咬", "握", "踢", "冲", "扑", "拍", "甩", "掐", "拽", "扯", "抹", "蹬"]
        phys_found = [p for p in PHYSICAL_MARKERS if p in polish_str]
        has_physiological = len(phys_found) >= 1
        checks.append({
            "name": "polish_physiological_reactions",
            "passed": has_physiological,
            "detail": f"Physiological action words found: {phys_found}." if has_physiological else "No physiological reaction replacement detected. Should replace 愤怒/悲伤 etc. with physical actions."
        })

        # c) Check that abstract emotion words are removed/reduced
        ABSTRACT_EMOTIONS = ["非常愤怒", "充满了复杂的情绪", "难以言说", "内心充满", "感到愤怒", "感到悲伤"]
        abstract_found = [e for e in ABSTRACT_EMOTIONS if e in polish_str]
        abstract_reduced = len(abstract_found) <= 1
        checks.append({
            "name": "polish_abstract_emotions_removed",
            "passed": abstract_reduced,
            "detail": f"Abstract emotion phrases remaining: {abstract_found}." if abstract_found else "Abstract emotion phrases successfully removed."
        })

        # d) Annotation mentions the method
        METHOD_KEYWORDS = ["三刀流", "顺口溜", "逻辑链", "形容词", "生理反应", "AI味"]
        method_mentioned = any(k in polish_str for k in METHOD_KEYWORDS)
        checks.append({
            "name": "polish_method_annotated",
            "passed": method_mentioned,
            "detail": f"Polish methodology annotation found." if method_mentioned else f"No mention of polish methodology (三刀流/顺口溜/生理反应 etc.)."
        })

        polish_score = 0
        if connectors_reduced: polish_score += 8
        if has_physiological: polish_score += 10
        if abstract_reduced: polish_score += 7
        if method_mentioned: polish_score += 5
        total_score += min(polish_score, 30.0)

    # =====================================================================
    # CHECK 4: Data Rating — report must include an S/A/B/C rating
    # =====================================================================
    report_str = json.dumps(report, ensure_ascii=False)
    has_rating = bool(re.search(r'[SABC]级|[SABC]-?级|rating.*[SABC]|[SABC].*rating|评级.*[SABC]|[SABC].*评级', report_str, re.IGNORECASE))
    # Also check for standalone S/A/B/C with context
    has_rating = has_rating or bool(re.search(r'"[SABC]"', report_str)) or any(
        f'"{g}"' in report_str or f': "{g}"' in report_str or f"'{g}'" in report_str 
        for g in ['S', 'A', 'B', 'C']
    )
    checks.append({
        "name": "data_rating_SABC_present",
        "passed": has_rating,
        "detail": "S/A/B/C data rating found in report." if has_rating else "No S/A/B/C rating system applied. Chapter 2 requires evaluating with S/A/B/C standards."
    })
    if has_rating:
        total_score += 10.0

    # =====================================================================
    # CHECK 5: Structural completeness — all 3 major sections present
    # =====================================================================
    all_sections = check_brainstorm_exists and titles_section_exists and polish_section_exists
    checks.append({
        "name": "all_three_sections_present",
        "passed": all_sections,
        "detail": "All three required sections present (brainstorm, titles, polish)." if all_sections else "One or more sections missing."
    })
    if all_sections:
        total_score += 10.0

    # --- Final ---
    final_score = min(round(total_score / 100.0, 3), 1.0)
    passed = final_score >= 0.55

    print(json.dumps({
        "passed": passed,
        "score": final_score,
        "checks": checks
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)