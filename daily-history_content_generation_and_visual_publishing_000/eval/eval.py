import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace_dir):
    checks = []
    
    # --- 1. Find the output file ---
    target = Path("/mnt/user-data/outputs/daily-history.html")
    fallback_matches = list(Path(workspace_dir).rglob("daily-history.html"))
    
    html_content = None
    try:
        if target.exists():
            html_content = target.read_text(encoding="utf-8", errors="replace")
            checks.append(check("output_file_exists_at_correct_path", True, f"Found at {target}"))
        elif fallback_matches:
            html_content = fallback_matches[0].read_text(encoding="utf-8", errors="replace")
            checks.append(check("output_file_exists_at_correct_path", False,
                f"File found at {fallback_matches[0]} but NOT at required path {target}"))
        else:
            checks.append(check("output_file_exists_at_correct_path", False,
                "daily-history.html not found anywhere"))
            return {"passed": False, "score": 0.0, "checks": checks}
    except Exception as e:
        checks.append(check("output_file_exists_at_correct_path", False, f"Read error: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}

    content_lower = html_content.lower()

    # --- 2. Check it's a valid HTML file ---
    is_html = "<!doctype html" in content_lower or "<html" in content_lower
    checks.append(check("valid_html_structure", is_html,
        "Contains <!DOCTYPE html> or <html> tag" if is_html else "Does not appear to be valid HTML"))

    # --- 3. Ad slot: id="ad-slot-middle" exists ---
    has_ad_middle = 'id="ad-slot-middle"' in html_content or "id='ad-slot-middle'" in html_content
    checks.append(check("ad_slot_middle_div_present",
        has_ad_middle,
        'Found <div id="ad-slot-middle">' if has_ad_middle else 'Missing <div id="ad-slot-middle">'))

    # --- 4. Ad slot: id="ad-slot-bottom" exists ---
    has_ad_bottom = 'id="ad-slot-bottom"' in html_content or "id='ad-slot-bottom'" in html_content
    checks.append(check("ad_slot_bottom_div_present",
        has_ad_bottom,
        'Found <div id="ad-slot-bottom">' if has_ad_bottom else 'Missing <div id="ad-slot-bottom">'))

    # --- 5. ad-slot-middle appears between 3rd and 4th event card ---
    # Strategy: find positions of event cards and ad-slot-middle
    try:
        # Look for year markers or event card divs; count them relative to ad-slot-middle
        # We look for year numbers (4-digit) appearing as prominent text blocks
        # More robust: look for the ad-slot-middle position relative to event-like sections
        ad_middle_pos = html_content.find('id="ad-slot-middle"')
        if ad_middle_pos == -1:
            ad_middle_pos = html_content.find("id='ad-slot-middle'")
        
        if ad_middle_pos != -1:
            # Count "event card" patterns before and after ad-slot-middle
            # We'll look for common card class patterns or year + description blocks
            # Count distinct year patterns (4-digit years like 1xxx or 2xxx) before and after
            before_ad = html_content[:ad_middle_pos]
            after_ad = html_content[ad_middle_pos:]
            
            # Count event cards by looking for category emojis (strong signal)
            emojis = ["🔬", "🏛️", "🎨", "⚽", "👤"]
            emojis_before = sum(before_ad.count(e) for e in emojis)
            emojis_after = sum(after_ad.count(e) for e in emojis)
            
            # Should have at least 3 event indicators before and at least 1 after
            ad_placement_ok = emojis_before >= 3 and emojis_after >= 1
            checks.append(check("ad_slot_middle_correct_placement",
                ad_placement_ok,
                f"Category emojis before ad-slot-middle: {emojis_before}, after: {emojis_after}. Expected >=3 before, >=1 after."))
        else:
            checks.append(check("ad_slot_middle_correct_placement", False,
                "Cannot check placement: ad-slot-middle not found"))
    except Exception as e:
        checks.append(check("ad_slot_middle_correct_placement", False, f"Error checking placement: {e}"))

    # --- 6. ad-slot-middle has min-height 90px (in style or CSS) ---
    try:
        # Check inline style on the div or in a nearby/global style block
        # Look for min-height: 90px anywhere in the document (could be in <style> block referencing id)
        mh_pattern = re.search(r'min-height\s*:\s*90px', html_content, re.IGNORECASE)
        # Also check for min-height on the ad-slot-middle div specifically
        ad_div_match = re.search(
            r'id=["\']ad-slot-middle["\'][^>]*style=["\'][^"\']*min-height\s*:\s*90px',
            html_content, re.IGNORECASE)
        ad_div_match2 = re.search(
            r'style=["\'][^"\']*min-height\s*:\s*90px[^"\']*["\'][^>]*id=["\']ad-slot-middle["\']',
            html_content, re.IGNORECASE)
        has_min_height = bool(mh_pattern or ad_div_match or ad_div_match2)
        checks.append(check("ad_slot_middle_min_height_90px",
            has_min_height,
            "Found min-height: 90px in document" if has_min_height else "Missing min-height: 90px for ad slot"))
    except Exception as e:
        checks.append(check("ad_slot_middle_min_height_90px", False, f"Error: {e}"))

    # --- 7. Footer: "Powered by ClawCode" ---
    has_footer = "powered by clawcode" in content_lower
    checks.append(check("footer_powered_by_clawcode",
        has_footer,
        'Found "Powered by ClawCode"' if has_footer else 'Missing "Powered by ClawCode" footer'))

    # --- 8. Bilingual header: 历史上的今天 / Today in History ---
    has_cn_title = "历史上的今天" in html_content
    has_en_title = "today in history" in content_lower
    bilingual_header = has_cn_title and has_en_title
    checks.append(check("bilingual_header_present",
        bilingual_header,
        f"CN title: {has_cn_title}, EN title: {has_en_title}"))

    # --- 9. Date in header (month/day format) ---
    try:
        # Look for a date pattern like "April 2" or "4月2日" or "January 15" etc.
        date_en_pattern = re.search(
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\b',
            html_content, re.IGNORECASE)
        date_cn_pattern = re.search(r'\d{1,2}月\d{1,2}日', html_content)
        has_date = bool(date_en_pattern or date_cn_pattern)
        checks.append(check("date_displayed_in_header",
            has_date,
            f"EN date: {date_en_pattern.group() if date_en_pattern else 'not found'}, "
            f"CN date: {date_cn_pattern.group() if date_cn_pattern else 'not found'}"))
    except Exception as e:
        checks.append(check("date_displayed_in_header", False, f"Error: {e}"))

    # --- 10. Category emojis present (at least 3 distinct ones) ---
    try:
        emojis_found = [e for e in ["🔬", "🏛️", "🎨", "⚽", "👤"] if e in html_content]
        enough_emojis = len(emojis_found) >= 3
        checks.append(check("category_emojis_present",
            enough_emojis,
            f"Found category emojis: {emojis_found} ({len(emojis_found)}/5, need >=3)"))
    except Exception as e:
        checks.append(check("category_emojis_present", False, f"Error: {e}"))

    # --- 11. Chinese language content in descriptions ---
    try:
        # Look for Chinese characters in event description areas
        cn_chars = re.findall(r'[\u4e00-\u9fff]', html_content)
        has_chinese = len(cn_chars) > 30  # substantial Chinese content expected
        checks.append(check("chinese_descriptions_present",
            has_chinese,
            f"Found {len(cn_chars)} Chinese characters (need >30 for bilingual content)"))
    except Exception as e:
        checks.append(check("chinese_descriptions_present", False, f"Error: {e}"))

    # --- 12. Animation: fade/slide in CSS or JS ---
    try:
        anim_keywords = ["fadeIn", "fade-in", "slideIn", "slide-in", "animation", "@keyframes",
                         "opacity", "transform", "transition"]
        anim_found = [kw for kw in anim_keywords if kw.lower() in content_lower]
        has_animation = len(anim_found) >= 2
        checks.append(check("animation_present",
            has_animation,
            f"Animation keywords found: {anim_found[:5]}"))
    except Exception as e:
        checks.append(check("animation_present", False, f"Error: {e}"))

    # --- 13. Staggered delays for cards ---
    try:
        stagger_patterns = [
            re.search(r'animation-delay\s*:\s*[\d.]+s', html_content),
            re.search(r'delay\s*:\s*\d+', html_content),
            re.search(r'setInterval|setTimeout.*\d{3}', html_content),
            re.search(r'delay.*\d+ms', html_content, re.IGNORECASE),
        ]
        has_stagger = any(bool(p) for p in stagger_patterns)
        checks.append(check("staggered_animation_delays",
            has_stagger,
            "Found staggered delay pattern" if has_stagger else "No staggered delay pattern detected"))
    except Exception as e:
        checks.append(check("staggered_animation_delays", False, f"Error: {e}"))

    # --- 14. Display font for years (Oswald or Bebas Neue) ---
    try:
        has_display_font = (
            "oswald" in content_lower or
            "bebas" in content_lower or
            "bebas neue" in content_lower
        )
        checks.append(check("display_font_for_years",
            has_display_font,
            "Found Oswald or Bebas Neue font reference" if has_display_font
            else "Missing required display font (Oswald or Bebas Neue)"))
    except Exception as e:
        checks.append(check("display_font_for_years", False, f"Error: {e}"))

    # --- 15. Body font (Source Serif Pro or Lora) ---
    try:
        has_body_font = (
            "source serif" in content_lower or
            "lora" in content_lower or
            "source+serif" in content_lower
        )
        checks.append(check("elegant_body_font",
            has_body_font,
            "Found Source Serif Pro or Lora font reference" if has_body_font
            else "Missing required body font (Source Serif Pro or Lora)"))
    except Exception as e:
        checks.append(check("elegant_body_font", False, f"Error: {e}"))

    # --- 16. Timeline center line present ---
    try:
        # Look for a vertical line element
        centerline_patterns = [
            "timeline-line" in content_lower,
            "center-line" in content_lower,
            bool(re.search(r'height\s*:\s*100%.*width\s*:\s*[24]px', html_content)),
            bool(re.search(r'width\s*:\s*[24]px.*height\s*:\s*100%', html_content)),
            bool(re.search(r'\.line|#line|timeline.*line', content_lower)),
        ]
        has_centerline = any(centerline_patterns)
        checks.append(check("timeline_center_line",
            has_centerline,
            "Found timeline center line element" if has_centerline
            else "No timeline center line detected"))
    except Exception as e:
        checks.append(check("timeline_center_line", False, f"Error: {e}"))

    # --- 17. Alternating left-right layout ---
    try:
        alt_patterns = [
            "alternating" in content_lower,
            "nth-child" in content_lower,
            bool(re.search(r'left.*right|right.*left', content_lower)),
            bool(re.search(r'nth-child\(even\)|nth-child\(odd\)', html_content)),
            "flex-direction: row-reverse" in content_lower,
            "flex-direction:row-reverse" in content_lower,
        ]
        has_alternating = any(alt_patterns)
        checks.append(check("alternating_left_right_cards",
            has_alternating,
            "Found alternating layout pattern" if has_alternating
            else "No alternating left-right card layout detected"))
    except Exception as e:
        checks.append(check("alternating_left_right_cards", False, f"Error: {e}"))

    # --- 18. At least 5 distinct year markers (4-digit years) ---
    try:
        years = re.findall(r'\b(1[0-9]{3}|2[0-9]{3})\b', html_content)
        distinct_years = set(years)
        # Filter to plausible historical years
        hist_years = {y for y in distinct_years if 1000 <= int(y) <= 2100}
        enough_years = len(hist_years) >= 5
        checks.append(check("five_or_more_distinct_historical_years",
            enough_years,
            f"Found {len(hist_years)} distinct historical year markers: {sorted(hist_years)[:10]}"))
    except Exception as e:
        checks.append(check("five_or_more_distinct_historical_years", False, f"Error: {e}"))

    # --- 19. Ad-slot-bottom at bottom of page (appears after ad-slot-middle) ---
    try:
        if has_ad_middle and has_ad_bottom:
            mid_pos = html_content.find('id="ad-slot-middle"')
            if mid_pos == -1:
                mid_pos = html_content.find("id='ad-slot-middle'")
            bot_pos = html_content.find('id="ad-slot-bottom"')
            if bot_pos == -1:
                bot_pos = html_content.find("id='ad-slot-bottom'")
            bottom_after_middle = bot_pos > mid_pos
            checks.append(check("ad_slot_bottom_after_middle",
                bottom_after_middle,
                f"ad-slot-bottom pos:{bot_pos} > ad-slot-middle pos:{mid_pos}: {bottom_after_middle}"))
        else:
            checks.append(check("ad_slot_bottom_after_middle", False,
                "Cannot verify order: one or both ad slots missing"))
    except Exception as e:
        checks.append(check("ad_slot_bottom_after_middle", False, f"Error: {e}"))

    # --- Calculate final score ---
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)

    # Critical checks that must pass for overall pass
    critical = [
        "output_file_exists_at_correct_path",
        "ad_slot_middle_div_present",
        "ad_slot_bottom_div_present",
        "footer_powered_by_clawcode",
        "bilingual_header_present",
        "chinese_descriptions_present",
        "five_or_more_distinct_historical_years",
        "ad_slot_middle_correct_placement",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical
    )
    overall_passed = critical_passed and score >= 0.70

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))