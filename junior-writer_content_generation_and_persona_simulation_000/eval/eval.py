import sys
import json
import os
import re
from pathlib import Path

def load_json_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def main(workspace):
    checks = []
    total_score = 0.0
    max_score = 8

    # --- Find output files ---
    round1_candidates = list(Path(workspace).rglob("output_round1.json"))
    round2_candidates = list(Path(workspace).rglob("output_round2.json"))

    # CHECK 1: output_round1.json exists
    check1 = {"name": "output_round1.json exists", "passed": False, "detail": ""}
    if round1_candidates:
        check1["passed"] = True
        check1["detail"] = f"Found at {round1_candidates[0]}"
        total_score += 1
    else:
        check1["detail"] = "output_round1.json not found anywhere in workspace"
    checks.append(check1)

    # CHECK 2: output_round2.json exists
    check2 = {"name": "output_round2.json exists", "passed": False, "detail": ""}
    if round2_candidates:
        check2["passed"] = True
        check2["detail"] = f"Found at {round2_candidates[0]}"
        total_score += 1
    else:
        check2["detail"] = "output_round2.json not found anywhere in workspace"
    checks.append(check2)

    # Load files if present
    r1, r2 = None, None
    if round1_candidates:
        try:
            r1 = load_json_file(round1_candidates[0])
        except Exception as e:
            r1 = None
            checks.append({"name": "output_round1.json parseable", "passed": False, "detail": str(e)})

    if round2_candidates:
        try:
            r2 = load_json_file(round2_candidates[0])
        except Exception as e:
            r2 = None
            checks.append({"name": "output_round2.json parseable", "passed": False, "detail": str(e)})

    # CHECK 3: Round1 has all three required fields (content, style_notes, evolution_notes)
    check3 = {"name": "round1 has required fields: content, style_notes, evolution_notes", "passed": False, "detail": ""}
    if r1 is not None:
        required = ["content", "style_notes", "evolution_notes"]
        missing = [k for k in required if k not in r1]
        if not missing:
            check3["passed"] = True
            check3["detail"] = "All three fields present"
            total_score += 1
        else:
            check3["detail"] = f"Missing fields: {missing}"
    else:
        check3["detail"] = "round1 output not loadable"
    checks.append(check3)

    # CHECK 4: Round2 has all three required fields
    check4 = {"name": "round2 has required fields: content, style_notes, evolution_notes", "passed": False, "detail": ""}
    if r2 is not None:
        required = ["content", "style_notes", "evolution_notes"]
        missing = [k for k in required if k not in r2]
        if not missing:
            check4["passed"] = True
            check4["detail"] = "All three fields present"
            total_score += 1
        else:
            check4["detail"] = f"Missing fields: {missing}"
    else:
        check4["detail"] = "round2 output not loadable"
    checks.append(check4)

    # CHECK 5: Round1 evolution_notes is empty/null/blank (no feedback was given)
    check5 = {"name": "round1 evolution_notes is empty (no feedback provided)", "passed": False, "detail": ""}
    if r1 is not None and "evolution_notes" in r1:
        val = r1["evolution_notes"]
        # Should be None, empty string, or empty list
        is_empty = (
            val is None or
            val == "" or
            val == [] or
            (isinstance(val, str) and val.strip() == "") or
            (isinstance(val, str) and len(val.strip()) < 10)
        )
        if is_empty:
            check5["passed"] = True
            check5["detail"] = f"evolution_notes is appropriately empty/minimal: {repr(val)}"
            total_score += 1
        else:
            check5["detail"] = f"evolution_notes should be empty for round1 (no reader_feedback was given), but got: {repr(val)[:200]}"
    else:
        check5["detail"] = "round1 not loadable or missing evolution_notes field"
    checks.append(check5)

    # CHECK 6: Round2 evolution_notes is non-empty and references the feedback
    check6 = {"name": "round2 evolution_notes is populated and references feedback adaptation", "passed": False, "detail": ""}
    if r2 is not None and "evolution_notes" in r2:
        val = r2["evolution_notes"]
        is_nonempty = (
            val is not None and
            isinstance(val, str) and
            len(val.strip()) >= 15
        )
        if is_nonempty:
            # Check it references something about inner thoughts / clarity / 内心 / 清晰 / 直接
            text = val.lower()
            evolution_keywords = ["内心", "清晰", "直接", "明显", "调整", "反馈", "读者", "情绪", "inner", "clear", "direct", "feedback", "adjust", "explicit", "改变", "更"]
            has_keyword = any(kw in text for kw in evolution_keywords)
            if has_keyword:
                check6["passed"] = True
                check6["detail"] = f"evolution_notes populated and references adaptation. Preview: {val[:200]}"
                total_score += 1
            else:
                check6["detail"] = f"evolution_notes present but doesn't reference reader feedback adaptation. Got: {val[:200]}"
        else:
            check6["detail"] = f"evolution_notes is empty or too short in round2: {repr(val)}"
    else:
        check6["detail"] = "round2 not loadable or missing evolution_notes field"
    checks.append(check6)

    # CHECK 7: Round1 content is non-trivial Chinese prose (>=50 chars), has topic 便利店 or related
    check7 = {"name": "round1 content is non-trivial Chinese prose about the topic", "passed": False, "detail": ""}
    if r1 is not None and "content" in r1:
        content = r1["content"]
        if isinstance(content, str) and len(content.strip()) >= 50:
            # Check it's substantially Chinese text
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
            topic_hint = any(w in content for w in ["便利店", "收银", "夜", "店", "灯", "柜台", "深夜"])
            if chinese_chars >= 30 and topic_hint:
                check7["passed"] = True
                check7["detail"] = f"Round1 content is valid Chinese prose ({len(content)} chars, {chinese_chars} Chinese chars)"
                total_score += 0.5
            elif chinese_chars >= 30:
                check7["passed"] = True
                check7["detail"] = f"Round1 content is valid Chinese prose ({len(content)} chars) but topic match weak"
                total_score += 0.3
            else:
                check7["detail"] = f"Content present but lacks Chinese characters ({chinese_chars}): {content[:100]}"
        else:
            check7["detail"] = f"Round1 content too short or not string: {repr(content)[:100]}"
    else:
        check7["detail"] = "round1 not loadable or missing content"
    checks.append(check7)

    # CHECK 8: Round2 content demonstrates MORE explicit inner monologue / interiority markers
    # compared to round1 — this is the evolution check
    check8 = {"name": "round2 content shows more explicit inner thought/emotion than round1", "passed": False, "detail": ""}
    if r1 is not None and r2 is not None and "content" in r1 and "content" in r2:
        c1 = r1["content"] if isinstance(r1["content"], str) else ""
        c2 = r2["content"] if isinstance(r2["content"], str) else ""

        # Inner monologue markers in Chinese
        inner_markers = [
            "我", "他想", "她想", "想到", "想起", "心里", "心想", "觉得", "感觉", "不知道",
            "也许", "或许", "可能", "明白", "清楚", "知道", "其实", "突然", "忽然", "意识到",
            "问自己", "告诉自己", "想问", "想说"
        ]

        def count_inner(text):
            return sum(text.count(marker) for marker in inner_markers)

        inner_r1 = count_inner(c1)
        inner_r2 = count_inner(c2)

        if inner_r2 > inner_r1:
            check8["passed"] = True
            check8["detail"] = f"Round2 has more inner-thought markers ({inner_r2}) than round1 ({inner_r1}). Evolution confirmed."
            total_score += 0.5
        elif inner_r2 == inner_r1 and inner_r2 > 0:
            check8["passed"] = True
            check8["detail"] = f"Round2 has equal inner markers ({inner_r2}) — marginal pass. Round1={inner_r1}"
            total_score += 0.2
        else:
            check8["detail"] = f"Round2 inner-thought markers ({inner_r2}) not greater than round1 ({inner_r1}). Evolution not demonstrated in content."
    else:
        check8["detail"] = "Cannot compare — one or both outputs missing/invalid"
    checks.append(check8)

    # --- Final score ---
    final_score = round(total_score / max_score, 4)
    passed = final_score >= 0.6 and all(c["passed"] for c in checks[:6])

    result = {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    main(workspace_dir)