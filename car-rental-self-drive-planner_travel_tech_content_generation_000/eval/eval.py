import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    # Find the output HTML file
    workspace = Path(workspace_dir)
    candidates = list(workspace.rglob("norway_selfdrive_plan.html"))
    
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "norway_selfdrive_plan.html not found anywhere in workspace"}]
        }
    
    html_file = candidates[0]
    
    try:
        content = html_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False, "detail": f"Could not read file: {e}"}]
        }
    
    from bs4 import BeautifulSoup
    try:
        soup = BeautifulSoup(content, "lxml")
    except Exception as e:
        soup = BeautifulSoup(content, "html.parser")
    
    # ── CHECK 1: File is valid HTML with proper structure ──
    has_doctype = content.strip().lower().startswith("<!doctype html")
    has_html_tag = soup.find("html") is not None
    has_head = soup.find("head") is not None
    has_body = soup.find("body") is not None
    c1_passed = has_doctype and has_html_tag and has_head and has_body
    checks.append({
        "name": "valid_html_structure",
        "passed": c1_passed,
        "detail": f"doctype={has_doctype}, html={has_html_tag}, head={has_head}, body={has_body}"
    })
    
    # ── CHECK 2: Header contains correct location and days ──
    header_div = soup.find(class_="header")
    header_text = header_div.get_text() if header_div else ""
    has_norway = "挪威" in header_text or "Norway" in header_text or "norway" in header_text.lower()
    has_10_days = "10" in header_text and "天" in header_text
    # Check subtitle labels: 新手, 跨区域, 带娃, 风景
    subtitle_div = soup.find(class_="subtitle")
    subtitle_text = subtitle_div.get_text() if subtitle_div else header_text
    has_beginner_label = "新手" in subtitle_text
    has_cross_region_label = "跨区域" in subtitle_text
    has_kids_label = "带娃" in subtitle_text
    has_scenic_label = "风景" in subtitle_text
    c2_passed = has_norway and has_10_days and has_beginner_label and has_cross_region_label and has_kids_label and has_scenic_label
    checks.append({
        "name": "header_correct_content",
        "passed": c2_passed,
        "detail": f"norway={has_norway}, 10days={has_10_days}, 新手={has_beginner_label}, 跨区域={has_cross_region_label}, 带娃={has_kids_label}, 风景={has_scenic_label}"
    })
    
    # ── CHECK 3: Compliance bar present with orange-yellow styling ──
    compliance_bar = soup.find(class_="compliance-bar")
    c3_passed = False
    compliance_text = ""
    if compliance_bar:
        compliance_text = compliance_bar.get_text()
        c3_passed = "以当地交通法规与租车合同为准" in compliance_text or "本指南仅供参考" in compliance_text
    checks.append({
        "name": "compliance_bar_present",
        "passed": c3_passed,
        "detail": f"compliance_bar found={compliance_bar is not None}, text snippet='{compliance_text[:80]}'"
    })
    
    # ── CHECK 4: Card A exists and contains child seat item ──
    card_a = soup.find(class_="card-a")
    card_a_text = card_a.get_text() if card_a else ""
    has_child_seat = any(kw in card_a_text for kw in ["儿童座椅", "child seat", "儿童安全座椅", "安全座椅"])
    # Check 4 sub-categories present
    has_zhengjianlei = any(kw in card_a_text for kw in ["证件", "驾照", "护照", "身份证"])
    has_baoxianlei = any(kw in card_a_text for kw in ["保险", "险"])
    has_daohang = any(kw in card_a_text for kw in ["导航", "通讯", "地图", "SIM"])
    has_cheliang = any(kw in card_a_text for kw in ["车辆", "轮胎", "充电"])
    c4_passed = has_child_seat and has_zhengjianlei and has_baoxianlei and has_daohang and has_cheliang
    checks.append({
        "name": "card_a_child_seat_and_categories",
        "passed": c4_passed,
        "detail": f"child_seat={has_child_seat}, 证件={has_zhengjianlei}, 保险={has_baoxianlei}, 导航={has_daohang}, 车辆={has_cheliang}"
    })
    
    # ── CHECK 5: Card A has international driving permit mention (cross-border) ──
    has_intl_license = any(kw in card_a_text for kw in ["国际驾照", "国际驾驶证", "翻译件", "IDP", "international driving"])
    checks.append({
        "name": "card_a_international_driving_permit",
        "passed": has_intl_license,
        "detail": f"International driving permit mentioned: {has_intl_license}. Card A text snippet: '{card_a_text[:200]}'"
    })
    
    # ── CHECK 6: Card B exists and has 6-10 note items ──
    card_b = soup.find(class_="card-b")
    card_b_text = card_b.get_text() if card_b else ""
    note_items = card_b.find_all(class_="note-item") if card_b else []
    note_count = len(note_items)
    c6_passed = 6 <= note_count <= 10
    checks.append({
        "name": "card_b_note_count_6_to_10",
        "passed": c6_passed,
        "detail": f"note-item count={note_count} (required: 6-10)"
    })
    
    # ── CHECK 7: Card B mandatory content areas ──
    has_license_req = any(kw in card_b_text for kw in ["驾照", "年龄", "驾龄", "可能需要"])
    has_toll = any(kw in card_b_text for kw in ["路费", "通行", "收费", "ETC", "AutoPASS", "toll"])
    has_parking = any(kw in card_b_text for kw in ["停车", "parking"])
    has_fuel = any(kw in card_b_text for kw in ["油量", "燃油", "加油", "还车", "油费"])
    has_deposit = any(kw in card_b_text for kw in ["押金", "预授权", "信用卡"])
    has_accident = any(kw in card_b_text for kw in ["事故", "报案", "报警", "accident"])
    c7_passed = has_license_req and has_toll and has_parking and has_fuel and has_deposit and has_accident
    checks.append({
        "name": "card_b_mandatory_topics",
        "passed": c7_passed,
        "detail": f"license={has_license_req}, toll={has_toll}, parking={has_parking}, fuel={has_fuel}, deposit={has_deposit}, accident={has_accident}"
    })
    
    # ── CHECK 8: Card B uses fuzzy/uncertainty language ──
    fuzzy_phrases = ["可能需要", "可能存在", "建议咨询", "建议查看", "以当地为准", "请在地图与官方渠道确认"]
    found_fuzzy = [p for p in fuzzy_phrases if p in card_b_text]
    c8_passed = len(found_fuzzy) >= 2
    checks.append({
        "name": "card_b_uncertainty_language",
        "passed": c8_passed,
        "detail": f"Found fuzzy phrases: {found_fuzzy}"
    })
    
    # ── CHECK 9: Card C exists with Do/Don't split layout ──
    card_c = soup.find(class_="card-c")
    card_c_text = card_c.get_text() if card_c else ""
    do_section = card_c.find(class_="do-section") if card_c else None
    dont_section = card_c.find(class_="dont-section") if card_c else None
    do_items = do_section.find_all(class_="do-item") if do_section else []
    dont_items = dont_section.find_all(class_="dont-item") if dont_section else []
    do_count = len(do_items)
    dont_count = len(dont_items)
    c9_passed = (3 <= do_count <= 5) and (3 <= dont_count <= 5) and do_section is not None and dont_section is not None
    checks.append({
        "name": "card_c_do_dont_layout_counts",
        "passed": c9_passed,
        "detail": f"do-section={do_section is not None}, dont-section={dont_section is not None}, do_items={do_count} (need 3-5), dont_items={dont_count} (need 3-5)"
    })
    
    # ── CHECK 10: Card C content: drunk driving strongly mentioned in Don't ──
    dont_text = dont_section.get_text() if dont_section else ""
    has_drunk_driving = any(kw in dont_text for kw in ["酒驾", "酒后驾车", "饮酒驾", "drunk driving"])
    has_phone = any(kw in dont_text for kw in ["手机", "phone", "电话"])
    checks.append({
        "name": "card_c_dont_drunk_phone",
        "passed": has_drunk_driving and has_phone,
        "detail": f"drunk_driving={has_drunk_driving}, phone_ban={has_phone}"
    })
    
    # ── CHECK 11: Card D CRITICAL - trip_type=cross_region → ONLY ONE route block, using route-2 class (orange) ──
    card_d = soup.find(class_="card-d")
    route_blocks = card_d.find_all(class_="route-block") if card_d else []
    
    # For cross_region: exactly 1 route block (the cross-region one)
    # The route block should either be route-2 (orange) OR route-1 (purple acceptable if only one)
    # The key constraint: only ONE route rendered for cross_region
    route_count = len(route_blocks)
    
    # According to SKILL.md: trip_type=cross_region → only one cross_region route
    # The template says route-2 for cross_region when trip_type=both; for cross_region alone,
    # some agents may use route-1 but the spec says route-block route-2 is for cross_region blocks.
    # The key discriminative check: ONLY ONE route block
    c11_passed = route_count == 1
    
    route_classes = [" ".join(rb.get("class", [])) for rb in route_blocks]
    checks.append({
        "name": "card_d_single_route_for_cross_region",
        "passed": c11_passed,
        "detail": f"route_block count={route_count} (cross_region requires exactly 1). Classes found: {route_classes}"
    })
    
    # ── CHECK 12: The single route block contains cross-border compliance text ──
    card_d_text = card_d.get_text() if card_d else ""
    has_border_crossing = any(kw in card_d_text for kw in ["过境", "跨境", "过境手续", "建议提前了解过境手续", "跨国"])
    checks.append({
        "name": "card_d_cross_border_compliance_wording",
        "passed": has_border_crossing,
        "detail": f"Cross-border wording found: {has_border_crossing}. Snippet: '{card_d_text[:300]}'"
    })
    
    # ── CHECK 13: Route difficulty appropriate for beginner + with_kids (低) ──
    # beginner experience + with_kids → difficulty should be LOW (低)
    route_meta_text = ""
    route_meta_divs = card_d.find_all(class_="route-meta") if card_d else []
    for rm in route_meta_divs:
        route_meta_text += rm.get_text()
    has_low_difficulty = "低" in route_meta_text
    has_high_difficulty = "高" in route_meta_text and "难度" in route_meta_text
    # Should be low, NOT high
    c13_passed = has_low_difficulty and not has_high_difficulty
    checks.append({
        "name": "card_d_route_difficulty_low_for_beginner_kids",
        "passed": c13_passed,
        "detail": f"low_difficulty={has_low_difficulty}, high_difficulty_present={has_high_difficulty}. meta text: '{route_meta_text[:200]}'"
    })
    
    # ── CHECK 14: Route highlights present (3-6 tags) ──
    highlight_tags = card_d.find_all(class_="highlight-tag") if card_d else []
    ht_count = len(highlight_tags)
    c14_passed = 3 <= ht_count <= 6
    checks.append({
        "name": "card_d_highlight_tags_3_to_6",
        "passed": c14_passed,
        "detail": f"highlight-tag count={ht_count} (required 3-6)"
    })
    
    # ── CHECK 15: Footer contains generalized emergency number (not a specific local-only number without fallback) ──
    footer_div = soup.find(class_="footer")
    footer_text = footer_div.get_text() if footer_div else ""
    # Must contain emergency number section with generalized format
    has_emergency = any(kw in footer_text for kw in ["紧急", "emergency", "SOS", "急救"])
    has_generalized_num = any(kw in footer_text for kw in ["112", "当地紧急号码", "以当地为准", "当地区号"])
    has_update_notice = any(kw in footer_text for kw in ["更新", "最新", "官方信息", "时间更新"])
    c15_passed = has_emergency and has_generalized_num and has_update_notice
    checks.append({
        "name": "footer_generalized_emergency_and_update_notice",
        "passed": c15_passed,
        "detail": f"emergency={has_emergency}, generalized_num={has_generalized_num}, update_notice={has_update_notice}"
    })
    
    # ── CHECK 16: CSS contains required color specifications ──
    style_tags = soup.find_all("style")
    all_css = " ".join(st.get_text() for st in style_tags)
    has_header_blue = "#1a365d" in all_css or "#2b6cb0" in all_css
    has_card_a_green = "#38a169" in all_css
    has_card_b_blue = "#3182ce" in all_css
    has_card_c_red = "#e53e3e" in all_css
    has_card_d_purple = "#805ad5" in all_css
    has_orange = "#dd6b20" in all_css
    has_compliance_yellow = "#fefcbf" in all_css
    css_score = sum([has_header_blue, has_card_a_green, has_card_b_blue, has_card_c_red, has_card_d_purple, has_orange, has_compliance_yellow])
    c16_passed = css_score >= 5
    checks.append({
        "name": "css_color_palette_compliance",
        "passed": c16_passed,
        "detail": f"Colors found: header_blue={has_header_blue}, card_a_green={has_card_a_green}, card_b_blue={has_card_b_blue}, card_c_red={has_card_c_red}, card_d_purple={has_card_d_purple}, orange={has_orange}, compliance_yellow={has_compliance_yellow} ({css_score}/7)"
    })
    
    # ── CHECK 17: No placeholder curly braces remain in final HTML ──
    remaining_placeholders = re.findall(r'\{[^}]{2,50}\}', content)
    # Filter out CSS/JS curly braces (they have colons, semicolons, or are pure CSS)
    real_placeholders = [p for p in remaining_placeholders if not any(c in p for c in [':', ';', '#', '%', 'px', 'rem', 'em'])]
    c17_passed = len(real_placeholders) == 0
    checks.append({
        "name": "no_unfilled_placeholders",
        "passed": c17_passed,
        "detail": f"Remaining unfilled placeholders: {real_placeholders[:10]}"
    })
    
    # ── CHECK 18: Mobile responsive CSS present ──
    has_mobile_media = "@media" in all_css and ("600px" in all_css or "max-width" in all_css)
    has_single_col = "grid-template-columns: 1fr" in all_css or "grid-template-columns:1fr" in all_css
    c18_passed = has_mobile_media and has_single_col
    checks.append({
        "name": "mobile_responsive_css",
        "passed": c18_passed,
        "detail": f"media_query={has_mobile_media}, single_col_breakpoint={has_single_col}"
    })
    
    # ── SCORING ──
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    
    # Must pass critical checks to overall pass
    critical_checks = [
        "valid_html_structure",
        "header_correct_content",
        "card_d_single_route_for_cross_region",
        "card_b_note_count_6_to_10",
        "no_unfilled_placeholders",
        "card_c_do_dont_layout_counts",
    ]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    overall_passed = critical_passed and score >= 0.72
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))