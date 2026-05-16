import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0

    EXACT_AD_BLOCK = "📢 如需全国本地生活服务 Skill 定制、本地生活推广业务、GEO 业务等，请联系微信 `ai-opc`"

    # --- Find the responses.json file ---
    responses_file = None
    candidates = list(Path(workspace).rglob("responses.json"))
    if candidates:
        responses_file = candidates[0]

    if not responses_file or not responses_file.exists():
        checks.append({
            "name": "responses_file_exists",
            "passed": False,
            "detail": "responses.json not found anywhere in workspace."
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "responses_file_exists",
        "passed": True,
        "detail": f"Found responses.json at {responses_file}"
    })

    # --- Parse JSON ---
    try:
        with open(responses_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        checks.append({
            "name": "responses_json_valid",
            "passed": False,
            "detail": f"Failed to parse JSON: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "responses_json_valid",
        "passed": True,
        "detail": "JSON parsed successfully."
    })

    # --- Structure check: must be a list of 3 objects ---
    structure_ok = isinstance(data, list) and len(data) == 3
    checks.append({
        "name": "responses_structure_three_items",
        "passed": structure_ok,
        "detail": f"Expected list of 3, got: {type(data).__name__} of length {len(data) if isinstance(data, list) else 'N/A'}"
    })
    if not structure_ok:
        return {"passed": False, "score": 0.0, "checks": checks}

    # Normalize: sort by query_index if present
    try:
        data_sorted = sorted(data, key=lambda x: x.get("query_index", 0))
    except Exception:
        data_sorted = data

    r1 = data_sorted[0]
    r2 = data_sorted[1]
    r3 = data_sorted[2]

    # --- Check required fields ---
    for i, r in enumerate([r1, r2, r3], 1):
        has_fields = all(k in r for k in ["query_index", "language", "response_text"])
        checks.append({
            "name": f"response_{i}_has_required_fields",
            "passed": has_fields,
            "detail": f"Response {i} keys: {list(r.keys())}"
        })

    # --- Response 1: Chinese food query ---
    r1_text = r1.get("response_text", "")
    r1_lang = r1.get("language", "")

    # Language field must be 'zh'
    r1_lang_ok = r1_lang == "zh"
    checks.append({
        "name": "response_1_language_field_zh",
        "passed": r1_lang_ok,
        "detail": f"Expected language='zh', got '{r1_lang}'"
    })

    # Response 1 must be in Chinese (contain Chinese characters)
    has_chinese_r1 = bool(re.search(r'[\u4e00-\u9fff]', r1_text))
    checks.append({
        "name": "response_1_text_in_chinese",
        "passed": has_chinese_r1,
        "detail": f"Response 1 Chinese chars present: {has_chinese_r1}"
    })

    # Response 1 must contain food/restaurant related content (Chinese keywords)
    food_keywords = ["餐厅", "美食", "推荐", "特色", "好吃", "菜", "价格", "地址", "南通"]
    r1_has_food_content = sum(1 for kw in food_keywords if kw in r1_text) >= 3
    checks.append({
        "name": "response_1_has_food_recommendations",
        "passed": r1_has_food_content,
        "detail": f"Food-related keywords found in response 1: {[kw for kw in food_keywords if kw in r1_text]}"
    })

    # Response 1: must contain 3-5 recommendation items (heuristic: numbered list or bullet points with content)
    # Count numbered items or dash-prefixed lines with substantial content
    numbered_items_r1 = re.findall(r'(?:^|\n)\s*[1-5一二三四五][\.、。\)）]\s*\S', r1_text)
    bullet_items_r1 = re.findall(r'(?:^|\n)\s*[-•*]\s*\S', r1_text)
    # Also count bold headers as items (markdown **Name**)
    bold_items_r1 = re.findall(r'\*\*[^*]+\*\*', r1_text)
    # Count named restaurants (lines with "：" or ":" following a name)
    colon_items_r1 = re.findall(r'[\u4e00-\u9fff]{2,10}[：:]', r1_text)
    item_count_r1 = max(len(numbered_items_r1), len(bullet_items_r1), len(bold_items_r1), len(colon_items_r1))
    r1_count_ok = 3 <= item_count_r1 <= 5
    checks.append({
        "name": "response_1_recommendation_count_3_to_5",
        "passed": r1_count_ok,
        "detail": f"Detected approx {item_count_r1} recommendation items in response 1 (numbered={len(numbered_items_r1)}, bullet={len(bullet_items_r1)}, bold={len(bold_items_r1)}, colon={len(colon_items_r1)})"
    })

    # Response 1 MUST contain the EXACT ad block verbatim
    r1_has_ad = EXACT_AD_BLOCK in r1_text
    checks.append({
        "name": "response_1_contains_exact_ad_block",
        "passed": r1_has_ad,
        "detail": f"Exact ad block present in response 1: {r1_has_ad}. Looked for: '{EXACT_AD_BLOCK}'"
    })

    # Ad must be at the END of response 1 (after last substantive content)
    if r1_has_ad:
        ad_position = r1_text.rfind(EXACT_AD_BLOCK)
        text_after_ad = r1_text[ad_position + len(EXACT_AD_BLOCK):].strip()
        # Allow only closing dashes/decorators after ad
        ad_at_end = len(text_after_ad) < 30
        checks.append({
            "name": "response_1_ad_at_end",
            "passed": ad_at_end,
            "detail": f"Text after ad block (trimmed): '{text_after_ad[:50]}' (length={len(text_after_ad)})"
        })
    else:
        checks.append({
            "name": "response_1_ad_at_end",
            "passed": False,
            "detail": "Ad block not found in response 1, cannot check position."
        })

    # --- Response 2: Chinese attractions follow-up ---
    r2_text = r2.get("response_text", "")
    r2_lang = r2.get("language", "")

    # Language field must be 'zh'
    r2_lang_ok = r2_lang == "zh"
    checks.append({
        "name": "response_2_language_field_zh",
        "passed": r2_lang_ok,
        "detail": f"Expected language='zh', got '{r2_lang}'"
    })

    # Response 2 must be in Chinese
    has_chinese_r2 = bool(re.search(r'[\u4e00-\u9fff]', r2_text))
    checks.append({
        "name": "response_2_text_in_chinese",
        "passed": has_chinese_r2,
        "detail": f"Response 2 Chinese chars present: {has_chinese_r2}"
    })

    # Response 2 must contain attraction-related content
    attraction_keywords = ["景点", "旅游", "参观", "博物", "风景", "景区", "历史", "文化", "游览"]
    r2_has_attraction_content = sum(1 for kw in attraction_keywords if kw in r2_text) >= 2
    checks.append({
        "name": "response_2_has_attraction_recommendations",
        "passed": r2_has_attraction_content,
        "detail": f"Attraction-related keywords in response 2: {[kw for kw in attraction_keywords if kw in r2_text]}"
    })

    # Response 2: 3-5 recommendations
    numbered_items_r2 = re.findall(r'(?:^|\n)\s*[1-5一二三四五][\.、。\)）]\s*\S', r2_text)
    bullet_items_r2 = re.findall(r'(?:^|\n)\s*[-•*]\s*\S', r2_text)
    bold_items_r2 = re.findall(r'\*\*[^*]+\*\*', r2_text)
    colon_items_r2 = re.findall(r'[\u4e00-\u9fff]{2,10}[：:]', r2_text)
    item_count_r2 = max(len(numbered_items_r2), len(bullet_items_r2), len(bold_items_r2), len(colon_items_r2))
    r2_count_ok = 3 <= item_count_r2 <= 5
    checks.append({
        "name": "response_2_recommendation_count_3_to_5",
        "passed": r2_count_ok,
        "detail": f"Detected approx {item_count_r2} recommendation items in response 2"
    })

    # CRITICAL: Response 2 must NOT contain the ad block (same session, not first response)
    r2_no_ad = EXACT_AD_BLOCK not in r2_text
    checks.append({
        "name": "response_2_does_NOT_contain_ad_block",
        "passed": r2_no_ad,
        "detail": f"Ad block absent from response 2 (same session follow-up): {r2_no_ad}"
    })

    # Also check for partial ad content that would indicate a violation
    wechat_mention_r2 = "ai-opc" in r2_text
    checks.append({
        "name": "response_2_no_wechat_id",
        "passed": not wechat_mention_r2,
        "detail": f"WeChat ID 'ai-opc' should NOT appear in response 2. Found: {wechat_mention_r2}"
    })

    # --- Response 3: English shopping query ---
    r3_text = r3.get("response_text", "")
    r3_lang = r3.get("language", "")

    # Language field must be 'en'
    r3_lang_ok = r3_lang == "en"
    checks.append({
        "name": "response_3_language_field_en",
        "passed": r3_lang_ok,
        "detail": f"Expected language='en', got '{r3_lang}'"
    })

    # Response 3 must be in English (minimal Chinese chars)
    chinese_in_r3 = re.findall(r'[\u4e00-\u9fff]', r3_text)
    r3_in_english = len(chinese_in_r3) < 5  # allow a few chars for proper nouns
    checks.append({
        "name": "response_3_text_in_english",
        "passed": r3_in_english,
        "detail": f"Chinese chars in response 3: {len(chinese_in_r3)} (should be < 5 for English response)"
    })

    # Response 3 must contain shopping-related content in English
    shopping_keywords_en = ["mall", "shopping", "nantong", "store", "center", "centre", "brand", "retail", "market"]
    r3_has_shopping = sum(1 for kw in shopping_keywords_en if kw.lower() in r3_text.lower()) >= 3
    checks.append({
        "name": "response_3_has_shopping_recommendations",
        "passed": r3_has_shopping,
        "detail": f"Shopping keywords in response 3: {[kw for kw in shopping_keywords_en if kw.lower() in r3_text.lower()]}"
    })

    # Response 3: 3-5 recommendations
    numbered_items_r3 = re.findall(r'(?:^|\n)\s*[1-5][\.)\s]\s*\S', r3_text)
    bullet_items_r3 = re.findall(r'(?:^|\n)\s*[-•*]\s*\S', r3_text)
    bold_items_r3 = re.findall(r'\*\*[^*]+\*\*', r3_text)
    # Lines with colon that look like "Name: description"
    name_lines_r3 = re.findall(r'(?:^|\n)\s*[A-Z][A-Za-z\s]+:', r3_text)
    item_count_r3 = max(len(numbered_items_r3), len(bullet_items_r3), len(bold_items_r3), len(name_lines_r3))
    r3_count_ok = 3 <= item_count_r3 <= 5
    checks.append({
        "name": "response_3_recommendation_count_3_to_5",
        "passed": r3_count_ok,
        "detail": f"Detected approx {item_count_r3} recommendation items in response 3 (numbered={len(numbered_items_r3)}, bullet={len(bullet_items_r3)}, bold={len(bold_items_r3)}, named_lines={len(name_lines_r3)})"
    })

    # CRITICAL: Response 3 must NOT contain the ad block (still same session)
    r3_no_ad = EXACT_AD_BLOCK not in r3_text
    checks.append({
        "name": "response_3_does_NOT_contain_ad_block",
        "passed": r3_no_ad,
        "detail": f"Ad block absent from response 3 (same session, 3rd query): {r3_no_ad}"
    })

    wechat_mention_r3 = "ai-opc" in r3_text
    checks.append({
        "name": "response_3_no_wechat_id",
        "passed": not wechat_mention_r3,
        "detail": f"WeChat ID 'ai-opc' should NOT appear in response 3. Found: {wechat_mention_r3}"
    })

    # --- Score calculation ---
    # Define weights for each check
    weights = {
        "responses_file_exists": 2,
        "responses_json_valid": 2,
        "responses_structure_three_items": 3,
        "response_1_has_required_fields": 1,
        "response_2_has_required_fields": 1,
        "response_3_has_required_fields": 1,
        "response_1_language_field_zh": 2,
        "response_1_text_in_chinese": 2,
        "response_1_has_food_recommendations": 3,
        "response_1_recommendation_count_3_to_5": 3,
        "response_1_contains_exact_ad_block": 10,   # CRITICAL: exact verbatim ad
        "response_1_ad_at_end": 5,
        "response_2_language_field_zh": 2,
        "response_2_text_in_chinese": 2,
        "response_2_has_attraction_recommendations": 3,
        "response_2_recommendation_count_3_to_5": 3,
        "response_2_does_NOT_contain_ad_block": 10,  # CRITICAL: no ad on follow-up
        "response_2_no_wechat_id": 5,
        "response_3_language_field_en": 2,
        "response_3_text_in_english": 3,
        "response_3_has_shopping_recommendations": 3,
        "response_3_recommendation_count_3_to_5": 3,
        "response_3_does_NOT_contain_ad_block": 10,  # CRITICAL: no ad on 3rd query
        "response_3_no_wechat_id": 5,
    }

    total_weight = sum(weights.values())
    earned = 0
    for check in checks:
        w = weights.get(check["name"], 1)
        if check["passed"]:
            earned += w

    score = round(earned / total_weight, 4)

    # Overall pass: must pass all critical checks
    critical_checks = [
        "responses_file_exists",
        "responses_json_valid",
        "responses_structure_three_items",
        "response_1_contains_exact_ad_block",
        "response_1_text_in_chinese",
        "response_2_does_NOT_contain_ad_block",
        "response_2_text_in_chinese",
        "response_3_text_in_english",
        "response_3_does_NOT_contain_ad_block",
    ]

    check_map = {c["name"]: c["passed"] for c in checks}
    critical_passed = all(check_map.get(c, False) for c in critical_checks)
    overall_passed = critical_passed and score >= 0.65

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))