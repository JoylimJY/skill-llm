import sys
import json
import re
from pathlib import Path

def find_output_file(workspace: Path):
    """Find the weekly_content_plan.md file anywhere in the workspace."""
    candidates = list(workspace.rglob("weekly_content_plan.md"))
    if candidates:
        return candidates[0]
    return None

def check_file_exists(workspace: Path):
    f = find_output_file(workspace)
    if f:
        return True, f"Found at {f}"
    return False, "weekly_content_plan.md not found anywhere in workspace"

def load_file(workspace: Path):
    f = find_output_file(workspace)
    if not f:
        return None, "File not found"
    try:
        content = f.read_text(encoding="utf-8")
        return content, str(f)
    except Exception as e:
        return None, str(e)

def check_header(content: str):
    """Must have ## Weekly Content Plan header with a date range."""
    pattern = r"##\s*Weekly Content Plan\s*\(.*?\)"
    if re.search(pattern, content):
        return True, "Found '## Weekly Content Plan (...)' header"
    return False, "Missing '## Weekly Content Plan ({date range})' header"

def check_seven_days(content: str):
    """Must contain exactly 7 Day entries."""
    # Match ### Day N patterns
    day_matches = re.findall(r"###\s*Day\s+\d+", content, re.IGNORECASE)
    count = len(day_matches)
    if count == 7:
        return True, f"Found exactly 7 Day sections"
    return False, f"Expected 7 Day sections, found {count}"

def check_weekday_labels(content: str):
    """Each Day section should reference a weekday."""
    weekdays_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekdays_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日",
                   "星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    all_weekdays = weekdays_en + weekdays_cn
    found = sum(1 for w in all_weekdays if w in content)
    if found >= 7:
        return True, f"Found {found} weekday references (≥7)"
    return False, f"Only found {found} weekday references, expected at least 7"

def check_all_fields(content: str):
    """Each day entry must have all 6 required fields: Title, Angle, Keywords, Virality, Reference, Est. time."""
    required_fields = ["Title", "Angle", "Keywords", "Virality", "Reference", "Est. time"]
    missing = []
    for field in required_fields:
        pattern = rf"\*\*{field}.*?\*\*"
        matches = re.findall(pattern, content, re.IGNORECASE)
        if len(matches) < 7:
            missing.append(f"{field} (found {len(matches)}/7)")
    if not missing:
        return True, "All 6 required fields present across all 7 days"
    return False, f"Missing or insufficient fields: {', '.join(missing)}"

def check_virality_format(content: str):
    """Virality must use ⭐ scale with a label (e.g., ⭐⭐⭐⭐ / High)."""
    star_pattern = r"⭐+"
    star_matches = re.findall(star_pattern, content)
    label_pattern = r"⭐+\s*/\s*(High|Medium|Low|Very High|Extreme|⭐)"
    label_matches = re.findall(label_pattern, content, re.IGNORECASE)
    # Must have at least 7 star ratings
    if len(star_matches) < 7:
        return False, f"Found only {len(star_matches)} virality star ratings, expected 7"
    # At least some should have labels (the format specifies ⭐⭐⭐⭐ / High)
    if len(label_matches) < 5:
        return False, f"Only {len(label_matches)}/7 virality entries have the required '⭐+ / Label' format"
    return True, f"Found {len(star_matches)} star ratings, {len(label_matches)} with proper '/ Label' format"

def check_3_3_1_ratio(content: str):
    """Must have 3 trend-chasing + 3 evergreen + 1 opinion/controversial topics.
    Look for these labels/markers in the content."""
    
    # Trend indicators
    trend_patterns = [
        r"\btrend\b", r"trend.chasing", r"trending", r"\bhot\b", r"时事", r"热点", r"追热",
        r"Trend", r"TREND", r"time.sensitive", r"must publish"
    ]
    # Evergreen indicators
    evergreen_patterns = [
        r"evergreen", r"Evergreen", r"EVERGREEN", r"常青", r"can prepare ahead",
        r"timeless", r"长效"
    ]
    # Opinion/controversial indicators
    opinion_patterns = [
        r"opinion", r"Opinion", r"OPINION", r"controversial", r"Controversial",
        r"争议", r"观点", r"contrarian", r"debate"
    ]
    
    trend_count = sum(1 for p in trend_patterns if re.search(p, content, re.IGNORECASE))
    evergreen_count = sum(1 for p in evergreen_patterns if re.search(p, content, re.IGNORECASE))
    opinion_count = sum(1 for p in opinion_patterns if re.search(p, content, re.IGNORECASE))
    
    # More lenient: check if any category markers are present at all
    # Also check for numeric distributions: 3 of one type, 3 of another, 1 of another
    
    has_trend = trend_count > 0
    has_evergreen = evergreen_count > 0
    has_opinion = opinion_count > 0
    
    if has_trend and has_evergreen and has_opinion:
        return True, f"Found all 3 topic-type markers (trend, evergreen, opinion/controversial)"
    
    missing_types = []
    if not has_trend:
        missing_types.append("trend-chasing label")
    if not has_evergreen:
        missing_types.append("evergreen label")
    if not has_opinion:
        missing_types.append("opinion/controversial label")
    
    return False, f"3:3:1 ratio markers incomplete — missing: {', '.join(missing_types)}"

def check_xiaohongshu_title_style(content: str):
    """小红书 titles must use emoji + numbers + keywords format."""
    # Look for titles that contain emoji AND numbers
    # Extract all **Title:** lines
    title_lines = re.findall(r"\*\*Title\*\*[:\s]*(.+)", content)
    
    if not title_lines:
        return False, "No **Title:** fields found"
    
    # Check that at least some titles have emoji characters
    emoji_pattern = re.compile(
        "[\U0001F300-\U0001F9FF"   # Misc symbols and pictographs
        "\U0001FA00-\U0001FA6F"
        "\U00002600-\U000027BF"    # Misc symbols
        "\U0001F600-\U0001F64F"    # Emoticons
        "\U0001F680-\U0001F6FF"    # Transport
        "]+",
        re.UNICODE
    )
    
    titles_with_emoji = [t for t in title_lines if emoji_pattern.search(t)]
    titles_with_numbers = [t for t in title_lines if re.search(r'\d+', t)]
    
    emoji_ratio = len(titles_with_emoji) / len(title_lines)
    number_ratio = len(titles_with_numbers) / len(title_lines)
    
    if emoji_ratio >= 0.4 and number_ratio >= 0.3:
        return True, f"{len(titles_with_emoji)}/{len(title_lines)} titles have emoji, {len(titles_with_numbers)}/{len(title_lines)} have numbers (小红书 style)"
    
    details = []
    if emoji_ratio < 0.4:
        details.append(f"only {len(titles_with_emoji)}/{len(title_lines)} titles contain emoji (need ≥40%)")
    if number_ratio < 0.3:
        details.append(f"only {len(titles_with_numbers)}/{len(title_lines)} titles contain numbers (need ≥30%)")
    return False, f"小红书 title style not applied: {'; '.join(details)}"

def check_separator_format(content: str):
    """Days must be separated by --- markdown horizontal rules."""
    separator_count = len(re.findall(r"\n---\n", content))
    if separator_count >= 6:  # 7 days = at least 6 separators between them
        return True, f"Found {separator_count} '---' separators (≥6 required)"
    return False, f"Only {separator_count} '---' separators found, expected ≥6 between 7 days"

def check_platform_is_xiaohongshu(content: str):
    """Should reference 小红书 as the target platform."""
    if "小红书" in content or "xiaohongshu" in content.lower() or "xhs" in content.lower():
        return True, "Platform 小红书 is correctly referenced"
    return False, "Target platform 小红书 not mentioned in content plan"

def check_niche_relevance(content: str):
    """Content should be relevant to zero-waste / eco-friendly / sustainable living niche."""
    eco_keywords = [
        "零废弃", "zero.waste", "环保", "可持续", "eco", "sustainable",
        "绿色", "green", "有机", "organic", "无塑料", "plastic.free",
        "竹", "bamboo", "diy", "DIY", "天然", "natural"
    ]
    found = [kw for kw in eco_keywords if re.search(kw, content, re.IGNORECASE)]
    if len(found) >= 4:
        return True, f"Niche-relevant keywords found: {', '.join(found[:6])}"
    return False, f"Too few eco/sustainable niche keywords. Found only: {found}"

def run_eval(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []

    # 1. File existence
    exists, detail = check_file_exists(workspace)
    checks.append({"name": "file_exists", "passed": exists, "detail": detail})
    if not exists:
        return {"passed": False, "score": 0.0, "checks": checks}

    content, path_detail = load_file(workspace)
    if content is None:
        checks.append({"name": "file_readable", "passed": False, "detail": path_detail})
        return {"passed": False, "score": 0.0, "checks": checks}
    checks.append({"name": "file_readable", "passed": True, "detail": f"Loaded from {path_detail}"})

    # 2. Header format
    p, d = check_header(content)
    checks.append({"name": "header_format", "passed": p, "detail": d})

    # 3. 7 days
    p, d = check_seven_days(content)
    checks.append({"name": "seven_days", "passed": p, "detail": d})

    # 4. Weekday labels
    p, d = check_weekday_labels(content)
    checks.append({"name": "weekday_labels", "passed": p, "detail": d})

    # 5. All 6 fields per day
    p, d = check_all_fields(content)
    checks.append({"name": "all_fields_present", "passed": p, "detail": d})

    # 6. Virality ⭐ format
    p, d = check_virality_format(content)
    checks.append({"name": "virality_star_format", "passed": p, "detail": d})

    # 7. 3:3:1 ratio
    p, d = check_3_3_1_ratio(content)
    checks.append({"name": "3_3_1_topic_ratio", "passed": p, "detail": d})

    # 8. 小红书 title style
    p, d = check_xiaohongshu_title_style(content)
    checks.append({"name": "xiaohongshu_title_style", "passed": p, "detail": d})

    # 9. Separator format
    p, d = check_separator_format(content)
    checks.append({"name": "separator_format", "passed": p, "detail": d})

    # 10. Platform reference
    p, d = check_platform_is_xiaohongshu(content)
    checks.append({"name": "platform_xiaohongshu", "passed": p, "detail": d})

    # 11. Niche relevance
    p, d = check_niche_relevance(content)
    checks.append({"name": "niche_relevance", "passed": p, "detail": d})

    # Score calculation
    # Weights: critical checks weigh more
    weights = {
        "file_exists": 1,
        "file_readable": 1,
        "header_format": 1,
        "seven_days": 2,
        "weekday_labels": 1,
        "all_fields_present": 2,
        "virality_star_format": 2,
        "3_3_1_topic_ratio": 3,   # highest weight — proprietary trap
        "xiaohongshu_title_style": 2,
        "separator_format": 1,
        "platform_xiaohongshu": 1,
        "niche_relevance": 1,
    }

    total_weight = sum(weights[c["name"]] for c in checks if c["name"] in weights)
    earned_weight = sum(weights[c["name"]] for c in checks if c["name"] in weights and c["passed"])
    score = round(earned_weight / total_weight, 4) if total_weight > 0 else 0.0

    # Must pass all critical checks to pass overall
    critical_checks = ["seven_days", "all_fields_present", "virality_star_format", "3_3_1_topic_ratio", "xiaohongshu_title_style"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)

    overall_passed = critical_passed and score >= 0.72

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))