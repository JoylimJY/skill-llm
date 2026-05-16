import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    score = 0.0
    total_checks = 10

    def add_check(name: str, passed: bool, detail: str):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # --- Find the output file ---
    workspace = Path(workspace_dir)
    found_files = list(workspace.rglob("wok_seasoning_outline.json"))

    if not found_files:
        add_check("file_exists", False, "wok_seasoning_outline.json not found anywhere in the workspace.")
        return {"passed": False, "score": 0.0, "checks": checks}

    output_file = found_files[0]
    add_check("file_exists", True, f"Found file at: {output_file}")

    # --- Parse JSON ---
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        add_check("json_parseable", False, f"Failed to parse JSON: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}

    add_check("json_parseable", True, "JSON parsed successfully.")

    # --- Check 1: Content type identification (教程类 / How-to) ---
    content_type_raw = str(data.get("content_type", "") or data.get("type", "") or data.get("内容类型", "")).lower()
    # Accept various representations of tutorial/how-to
    type_keywords = ["教程", "how-to", "howto", "how_to", "tutorial", "教程类"]
    type_correct = any(kw in content_type_raw for kw in type_keywords)
    add_check(
        "content_type_is_tutorial",
        type_correct,
        f"content_type value: '{content_type_raw}'. Expected 教程类/How-to/tutorial."
    )

    # --- Check 2: Template selection (standard tutorial - 标准教程结构) ---
    template_raw = str(data.get("template", "") or data.get("模板", "") or data.get("structure_template", "")).lower()
    # Should be template 1 (standard), not template 2 (quick-start) — standard has FAQ in closing
    template_keywords = ["标准", "standard", "模板1", "template_1", "template 1", "模板 1"]
    template_correct = any(kw in template_raw for kw in template_keywords)
    # If template field is absent, check if the structure has FAQ section (which only standard template has)
    if not template_correct:
        # Check if FAQ is present in closing section as fallback signal
        full_text = json.dumps(data, ensure_ascii=False).lower()
        if "faq" in full_text or "常见问题" in full_text:
            template_correct = True
    add_check(
        "template_is_standard_tutorial",
        template_correct,
        f"template value: '{template_raw}'. Expected 标准教程结构 (Template 1), which includes FAQ in closing."
    )

    # --- Check 3: Opening section exists with required sub-elements ---
    # Required: 痛点描述, 价值承诺, 适用人群, 内容预告
    full_text = json.dumps(data, ensure_ascii=False)
    full_text_lower = full_text.lower()

    opening_section = None
    for key in ["opening", "开头", "intro", "introduction", "开篇"]:
        if key in data:
            opening_section = data[key]
            break

    # If structured as sections list
    if opening_section is None and "sections" in data:
        for sec in data.get("sections", []):
            sec_name = str(sec.get("name", "") or sec.get("title", "") or sec.get("section", "")).lower()
            if any(k in sec_name for k in ["开头", "opening", "intro"]):
                opening_section = sec
                break

    opening_text = json.dumps(opening_section, ensure_ascii=False).lower() if opening_section else full_text_lower

    pain_point = any(k in opening_text for k in ["痛点", "pain", "problem", "问题", "困境", "苦恼", "困惑", "sticks", "粘锅", "rust", "锈", "开锅"])
    value_promise = any(k in opening_text for k in ["价值", "value", "承诺", "得到", "学会", "能", "benefit", "learn", "master"])
    target_audience = any(k in opening_text for k in ["适用", "人群", "audience", "适合", "谁", "who", "目标", "新手", "beginner"])
    content_preview = any(k in opening_text for k in ["预告", "preview", "会讲", "内容", "include", "cover", "步骤", "方法"])

    opening_elements_count = sum([pain_point, value_promise, target_audience, content_preview])
    opening_passed = opening_elements_count >= 3

    add_check(
        "opening_has_required_subelements",
        opening_passed,
        f"Opening sub-elements found: pain_point={pain_point}, value_promise={value_promise}, "
        f"target_audience={target_audience}, content_preview={content_preview}. "
        f"Need at least 3/4. Found {opening_elements_count}/4."
    )

    # --- Check 4: Opening percentage ~10% ---
    opening_pct = None
    if isinstance(opening_section, dict):
        for k in ["percentage", "percent", "比例", "占比", "weight", "proportion"]:
            if k in opening_section:
                try:
                    val = str(opening_section[k]).replace("%", "").strip()
                    opening_pct = float(val)
                except:
                    pass
    if opening_pct is None:
        # Try to find "10%" or "10" near opening in full text
        opening_area = full_text[:500] + full_text_lower[:500]
        pct_match = re.search(r'(?:开头|opening|intro)[^}]{0,200}?(\d+)\s*%', full_text_lower[:1000])
        if pct_match:
            opening_pct = float(pct_match.group(1))

    if opening_pct is not None:
        pct_correct = abs(opening_pct - 10.0) <= 3.0
        add_check(
            "opening_percentage_10pct",
            pct_correct,
            f"Opening percentage: {opening_pct}%. Expected ~10%."
        )
    else:
        add_check(
            "opening_percentage_10pct",
            False,
            "Could not find a percentage value for the opening section. Expected ~10%."
        )

    # --- Check 5: Body/正文 section exists and has steps ---
    body_section = None
    for key in ["body", "正文", "main_content", "main", "content", "正文内容"]:
        if key in data:
            body_section = data[key]
            break

    if body_section is None and "sections" in data:
        for sec in data.get("sections", []):
            sec_name = str(sec.get("name", "") or sec.get("title", "") or sec.get("section", "")).lower()
            if any(k in sec_name for k in ["正文", "body", "main", "步骤", "方法"]):
                body_section = sec
                break

    body_text = json.dumps(body_section, ensure_ascii=False).lower() if body_section else full_text_lower

    # Check for preparation step + numbered steps
    has_prep = any(k in body_text for k in ["准备", "preparation", "工具", "tool", "需要什么", "materials", "所需"])
    has_steps = len(re.findall(r'步骤\s*[1-9]|step\s*[1-9]|第[一二三四五六七八九]\s*步', body_text)) >= 3
    has_case = any(k in body_text for k in ["案例", "case", "实战", "演示", "example", "actual"])
    has_advanced = any(k in body_text for k in ["进阶", "advanced", "技巧", "tips", "提高", "improve", "更好"])

    body_elements_count = sum([has_prep, has_steps, has_case, has_advanced])
    body_passed = body_elements_count >= 3

    add_check(
        "body_has_required_subelements",
        body_passed,
        f"Body sub-elements: prep={has_prep}, steps>=3={has_steps}, case={has_case}, advanced={has_advanced}. "
        f"Need 3/4. Found {body_elements_count}/4."
    )

    # --- Check 6: Body percentage ~70% ---
    body_pct = None
    if isinstance(body_section, dict):
        for k in ["percentage", "percent", "比例", "占比", "weight", "proportion"]:
            if k in body_section:
                try:
                    val = str(body_section[k]).replace("%", "").strip()
                    body_pct = float(val)
                except:
                    pass
    if body_pct is None:
        pct_match = re.search(r'(?:正文|body|main)[^}]{0,300}?(\d+)\s*%', full_text_lower)
        if pct_match:
            body_pct = float(pct_match.group(1))

    if body_pct is not None:
        body_pct_correct = abs(body_pct - 70.0) <= 5.0
        add_check(
            "body_percentage_70pct",
            body_pct_correct,
            f"Body percentage: {body_pct}%. Expected ~70%."
        )
    else:
        add_check(
            "body_percentage_70pct",
            False,
            "Could not find a percentage value for the body section. Expected ~70%."
        )

    # --- Check 7: Closing/结尾 section with all 4 required sub-elements ---
    # Required for 标准教程结构: 总结回顾, 常见问题FAQ, 行动建议, 互动引导
    closing_section = None
    for key in ["closing", "结尾", "conclusion", "ending", "outro"]:
        if key in data:
            closing_section = data[key]
            break

    if closing_section is None and "sections" in data:
        for sec in data.get("sections", []):
            sec_name = str(sec.get("name", "") or sec.get("title", "") or sec.get("section", "")).lower()
            if any(k in sec_name for k in ["结尾", "closing", "conclusion", "ending"]):
                closing_section = sec
                break

    closing_text = json.dumps(closing_section, ensure_ascii=False).lower() if closing_section else full_text_lower

    has_summary = any(k in closing_text for k in ["总结", "summary", "回顾", "review", "recap", "要点", "核心"])
    has_faq = any(k in closing_text for k in ["faq", "常见问题", "q&a", "q&a", "faqs", "问答", "疑问"])
    has_action = any(k in closing_text for k in ["行动", "action", "建议", "suggestion", "下一步", "next step", "开始", "start"])
    has_interaction = any(k in closing_text for k in ["互动", "interaction", "引导", "评论", "comment", "点赞", "like", "收藏", "share", "分享"])

    closing_elements_count = sum([has_summary, has_faq, has_action, has_interaction])
    closing_passed = closing_elements_count >= 3

    add_check(
        "closing_has_required_subelements",
        closing_passed,
        f"Closing sub-elements: summary={has_summary}, faq={has_faq}, action={has_action}, interaction={has_interaction}. "
        f"Need 3/4. Found {closing_elements_count}/4."
    )

    # --- Check 8: Closing percentage ~20% ---
    closing_pct = None
    if isinstance(closing_section, dict):
        for k in ["percentage", "percent", "比例", "占比", "weight", "proportion"]:
            if k in closing_section:
                try:
                    val = str(closing_section[k]).replace("%", "").strip()
                    closing_pct = float(val)
                except:
                    pass
    if closing_pct is None:
        pct_match = re.search(r'(?:结尾|closing|conclusion)[^}]{0,300}?(\d+)\s*%', full_text_lower)
        if pct_match:
            closing_pct = float(pct_match.group(1))

    if closing_pct is not None:
        closing_pct_correct = abs(closing_pct - 20.0) <= 4.0
        add_check(
            "closing_percentage_20pct",
            closing_pct_correct,
            f"Closing percentage: {closing_pct}%. Expected ~20%."
        )
    else:
        add_check(
            "closing_percentage_20pct",
            False,
            "Could not find a percentage value for the closing section. Expected ~20%."
        )

    # --- Check 9: Content filling - domain-specific content from notes is incorporated ---
    # The outline must reference wok-specific content from the raw notes
    wok_keywords = ["wok", "炒锅", "开锅", "seasoning", "carbon steel", "铁锅", "碳钢", "oil", "油", "rust", "锈", "smoke", "烟", "patina", "步骤", "soap", "肥皂", "dry", "干", "heat", "加热"]
    wok_refs = sum(1 for kw in wok_keywords if kw.lower() in full_text_lower)
    wok_content_present = wok_refs >= 5

    add_check(
        "wok_domain_content_incorporated",
        wok_content_present,
        f"Domain-specific wok content references found: {wok_refs}/10+ expected keywords. "
        f"The outline must incorporate content from the raw notes."
    )

    # --- Check 10: Common mistakes section present (required by 标准教程结构: 注意事项/常见错误 in each step) ---
    mistake_keywords = ["常见错误", "注意事项", "common mistake", "错误", "mistake", "warning", "avoid", "不要", "caution", "wrong", "误区"]
    has_mistakes = any(kw in full_text_lower for kw in mistake_keywords)

    add_check(
        "common_mistakes_documented",
        has_mistakes,
        f"Common mistakes/注意事项 section: {'found' if has_mistakes else 'NOT FOUND'}. "
        f"标准教程结构 requires 注意事项/常见错误 within each step."
    )

    # --- Compute final score ---
    passed_checks = sum(1 for c in checks if c["passed"])
    score = round(passed_checks / total_checks, 2)
    overall_passed = passed_checks >= 7  # Must pass at least 7/10 checks

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: eval_script.py <workspace_dir>"}))
        sys.exit(1)

    workspace_dir = sys.argv[1]
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))