import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)

    # --- Find the output HTML file ---
    html_files = list(workspace.rglob("presentation.html"))
    
    if not html_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "presentation.html not found anywhere in workspace"}]
        }
    
    html_path = html_files[0]
    
    try:
        html_content = html_path.read_text(encoding='utf-8')
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False, "detail": f"Could not read file: {e}"}]
        }

    html_lower = html_content.lower()

    # ---- Check 1: File is a single HTML file ----
    check_html = html_content.strip().startswith("<!") or html_content.strip().lower().startswith("<html")
    checks.append({
        "name": "single_html_file",
        "passed": check_html,
        "detail": "File must be a valid HTML document starting with <!DOCTYPE html> or <html>"
    })

    # ---- Check 2: Dark background - #000000 or #0a0a0a ----
    has_dark_bg = (
        "#000000" in html_content or 
        "#0a0a0a" in html_content or
        "background.*#000" in html_lower or
        "bg-black" in html_lower or
        "background-color.*rgb(0,0,0)" in html_lower.replace(" ", "") or
        "background.*000000" in html_lower
    )
    checks.append({
        "name": "dark_background_color",
        "passed": has_dark_bg,
        "detail": f"Must use #000000 or #0a0a0a background. Found dark bg: {has_dark_bg}"
    })

    # ---- Check 3: White main text color #ffffff ----
    has_white_text = (
        "#ffffff" in html_lower or
        "color.*#fff" in html_lower or
        "text-white" in html_lower
    )
    checks.append({
        "name": "white_main_text",
        "passed": has_white_text,
        "detail": f"Must use #ffffff for main text. Found: {has_white_text}"
    })

    # ---- Check 4: 9:16 vertical aspect ratio (portrait) ----
    # Look for explicit 9:16 ratio or portrait dimensions like width:9, height:16 style
    has_916_ratio = (
        "9/16" in html_content or
        "9:16" in html_content or
        "aspect-ratio.*9.*16" in html_lower.replace(" ", "") or
        "aspect-[9/16]" in html_lower or
        # Check for explicit portrait dimensions like width:360px height:640px or similar 9:16 ratios
        re.search(r'width\s*:\s*(\d+).*?height\s*:\s*(\d+)', html_content) is not None
    )
    # More specific check for 9:16 portrait aspect
    ratio_check = False
    ratio_patterns = [
        r'aspect-\[9/16\]',
        r'9\s*/\s*16',
        r'aspect.{0,10}9.{0,5}16',
        r'width.{0,10}360.{0,50}height.{0,10}640',
        r'width.{0,10}390.{0,50}height.{0,10}693',
        r'width.{0,10}414.{0,50}height.{0,10}736',
        r'width.{0,10}9.{0,3}%;.{0,30}height.{0,10}16',
    ]
    for pat in ratio_patterns:
        if re.search(pat, html_lower):
            ratio_check = True
            break
    # Also accept if "9/16" or "portrait" is mentioned
    if "9/16" in html_content or "portrait" in html_lower:
        ratio_check = True
        
    checks.append({
        "name": "portrait_9_16_ratio",
        "passed": ratio_check,
        "detail": f"Must use 9:16 vertical/portrait aspect ratio. Pattern found: {ratio_check}"
    })

    # ---- Check 5: TailwindCSS CDN ----
    has_tailwind = (
        "tailwindcss" in html_lower or
        "tailwind" in html_lower and "cdn" in html_lower or
        "cdn.tailwindcss" in html_lower or
        "unpkg.com/tailwindcss" in html_lower or
        "jsdelivr" in html_lower and "tailwind" in html_lower or
        # Chinese CDN variants
        "bootcdn" in html_lower and "tailwind" in html_lower or
        "jsd.onmicrosoft.cn" in html_lower
    )
    checks.append({
        "name": "tailwindcss_cdn",
        "passed": has_tailwind,
        "detail": f"Must use TailwindCSS via CDN. Found: {has_tailwind}"
    })

    # ---- Check 6: Keyboard navigation (arrow keys ← →) ----
    has_keyboard_nav = (
        "keydown" in html_lower or
        "keyup" in html_lower or
        "arrowleft" in html_lower or
        "arrowright" in html_lower or
        "key.*left" in html_lower or
        "key.*right" in html_lower or
        "37" in html_content and "39" in html_content  # key codes for left/right arrows
    )
    # More refined check
    keyboard_patterns = [
        r'arrowleft',
        r'arrowright', 
        r'keydown',
        r'keycode.*37',
        r'keycode.*39',
        r'key\s*===\s*[\'"]ArrowLeft',
        r'key\s*===\s*[\'"]ArrowRight',
    ]
    keyboard_check = any(re.search(p, html_lower) for p in keyboard_patterns)
    checks.append({
        "name": "keyboard_navigation",
        "passed": keyboard_check,
        "detail": f"Must support keyboard ← → navigation. Found: {keyboard_check}"
    })

    # ---- Check 7: Bottom progress bar / navigation ----
    progress_patterns = [
        r'progress',
        r'nav.*bottom',
        r'bottom.*nav',
        r'fixed.*bottom',
        r'position.*fixed',
        r'indicator',
        r'pagination',
        r'slide.*dot',
        r'dot.*slide',
    ]
    has_progress = any(re.search(p, html_lower) for p in progress_patterns)
    checks.append({
        "name": "bottom_progress_navigation",
        "passed": has_progress,
        "detail": f"Must have bottom progress navigation bar. Found: {has_progress}"
    })

    # ---- Check 8: Multiple slides (at least 5, one topic per slide philosophy) ----
    # Count slide-like divs
    slide_count_patterns = [
        len(re.findall(r'class=["\'][^"\']*slide[^"\']*["\']', html_lower)),
        len(re.findall(r'<section', html_lower)),
        len(re.findall(r'data-slide', html_lower)),
        len(re.findall(r'slide-\d+', html_lower)),
        len(re.findall(r'page-\d+', html_lower)),
    ]
    max_slides = max(slide_count_patterns)
    
    # Alternative: count distinct slide containers via id patterns
    slide_ids = re.findall(r'id=["\'](?:slide|page|screen)[-_]?(\d+)["\']', html_lower)
    num_slides_by_id = len(set(slide_ids))
    
    effective_slides = max(max_slides, num_slides_by_id)
    has_enough_slides = effective_slides >= 5
    
    checks.append({
        "name": "multiple_slides_min_5",
        "passed": has_enough_slides,
        "detail": f"Must have at least 5 slides (one-topic-per-slide). Detected ~{effective_slides} slides."
    })

    # ---- Check 9: Titles ≤ 12 Chinese characters ----
    # Extract h1/h2 text content
    h1_h2_texts = re.findall(r'<h[12][^>]*>(.*?)</h[12]>', html_content, re.DOTALL)
    
    title_violations = []
    for title_raw in h1_h2_texts:
        # Strip HTML tags from title
        title_clean = re.sub(r'<[^>]+>', '', title_raw).strip()
        # Count only Chinese + common Chinese punctuation characters
        chinese_chars = re.findall(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', title_clean)
        char_count = len(title_clean.replace(' ', ''))  # total non-space chars
        if char_count > 12 and len(chinese_chars) > 0:
            title_violations.append(f"'{title_clean[:30]}' ({char_count} chars)")
    
    titles_ok = len(title_violations) == 0 or len(h1_h2_texts) == 0
    checks.append({
        "name": "titles_max_12_chars",
        "passed": titles_ok,
        "detail": f"All slide titles must be ≤12 chars. Violations: {title_violations[:3] if title_violations else 'none'}"
    })

    # ---- Check 10: Content covers lecture themes (AI, programmers, LLM) ----
    key_themes = ["程序员", "大模型", "ai", "代码", "工程师", "llm", "效率", "替代"]
    theme_hits = sum(1 for theme in key_themes if theme in html_lower or theme in html_content.lower())
    covers_content = theme_hits >= 3
    checks.append({
        "name": "content_covers_lecture_themes",
        "passed": covers_content,
        "detail": f"Presentation must cover content from lecture script. Theme hits: {theme_hits}/8 (need ≥3)"
    })

    # ---- Check 11: No horizontal 16:9 ratio (must not use 16:9 landscape) ----
    has_wrong_ratio = bool(re.search(r'16\s*/\s*9|16:9|1920.*1080|1280.*720|aspect-\[16/9\]', html_lower))
    no_landscape = not has_wrong_ratio
    checks.append({
        "name": "no_landscape_16_9_ratio",
        "passed": no_landscape,
        "detail": f"Must NOT use 16:9 landscape ratio. Found 16:9: {has_wrong_ratio}"
    })

    # ---- Check 12: Smooth transition / animation ----
    animation_patterns = [
        r'transition',
        r'animation',
        r'transform',
        r'ease',
        r'duration',
        r'slide-in',
        r'fade',
    ]
    has_animation = any(re.search(p, html_lower) for p in animation_patterns)
    checks.append({
        "name": "smooth_transition_animation",
        "passed": has_animation,
        "detail": f"Must have smooth slide transition animation. Found: {has_animation}"
    })

    # ---- Compute score ----
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 3)
    
    # Must pass critical checks to overall pass
    critical_checks = [
        "single_html_file",
        "dark_background_color", 
        "keyboard_navigation",
        "portrait_9_16_ratio",
        "multiple_slides_min_5",
        "content_covers_lecture_themes",
        "no_landscape_16_9_ratio",
    ]
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.70

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))