import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)

    # --- Check 1: content-calendar.md exists in workspace root ---
    try:
        calendar_files = list(workspace.rglob("content-calendar.md"))
        # Prefer root-level file
        root_calendar = workspace / "content-calendar.md"
        if root_calendar.exists():
            calendar_path = root_calendar
        elif calendar_files:
            calendar_path = calendar_files[0]
        else:
            calendar_path = None

        if calendar_path and calendar_path.exists():
            checks.append({"name": "content-calendar.md exists", "passed": True, "detail": f"Found at {calendar_path}"})
            content = calendar_path.read_text(encoding="utf-8", errors="replace")
        else:
            checks.append({"name": "content-calendar.md exists", "passed": False, "detail": "content-calendar.md not found in workspace"})
            content = ""
    except Exception as e:
        checks.append({"name": "content-calendar.md exists", "passed": False, "detail": f"Exception: {e}"})
        content = ""

    if not content:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "further checks skipped", "passed": False, "detail": "No content to evaluate"}]
        }
        print(json.dumps(result))
        return

    # --- Check 2: Correct topic "plant-based nutrition" is in the file ---
    try:
        topic_present = "plant-based nutrition" in content.lower() or "plant based nutrition" in content.lower() or "plantbasednutrition" in content.lower()
        checks.append({
            "name": "Topic 'plant-based nutrition' present",
            "passed": topic_present,
            "detail": "Found topic reference in content" if topic_present else "Topic 'plant-based nutrition' not found in calendar"
        })
    except Exception as e:
        checks.append({"name": "Topic 'plant-based nutrition' present", "passed": False, "detail": f"Exception: {e}"})

    # --- Check 3: Target audience "health-conscious gen z" is in the file ---
    try:
        audience_keywords = ["gen z", "genz", "health-conscious", "health conscious"]
        audience_present = any(kw in content.lower() for kw in audience_keywords)
        checks.append({
            "name": "Target audience 'health-conscious Gen Z' present",
            "passed": audience_present,
            "detail": "Found audience reference in content" if audience_present else "Audience 'health-conscious Gen Z' not found — was the second argument passed to generate.sh?"
        })
    except Exception as e:
        checks.append({"name": "Target audience present", "passed": False, "detail": f"Exception: {e}"})

    # --- Check 4: All 7 days present ---
    try:
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        content_lower = content.lower()
        days_found = [day for day in days if day in content_lower]
        all_days_present = len(days_found) == 7
        checks.append({
            "name": "All 7 days (Mon–Sun) present",
            "passed": all_days_present,
            "detail": f"Found days: {days_found}" if all_days_present else f"Missing days. Found: {days_found}"
        })
    except Exception as e:
        checks.append({"name": "All 7 days present", "passed": False, "detail": f"Exception: {e}"})

    # --- Check 5: All 3 platforms present ---
    try:
        platforms = ["twitter", "linkedin", "instagram"]
        platforms_found = [p for p in platforms if p in content.lower()]
        all_platforms = len(platforms_found) == 3
        checks.append({
            "name": "All 3 platforms (Twitter, LinkedIn, Instagram) present",
            "passed": all_platforms,
            "detail": f"Found platforms: {platforms_found}" if all_platforms else f"Missing platforms. Found: {platforms_found}"
        })
    except Exception as e:
        checks.append({"name": "All 3 platforms present", "passed": False, "detail": f"Exception: {e}"})

    # --- Check 6: Correct day themes present ---
    try:
        theme_map = {
            "monday": ["motivational", "week opener", "motivation"],
            "tuesday": ["educational", "how-to", "howto", "how to"],
            "wednesday": ["engagement", "question"],
            "thursday": ["behind-the-scenes", "behind the scenes", "story"],
            "friday": ["tip", "quick win"],
            "saturday": ["curated", "industry news", "roundup"],
            "sunday": ["reflection", "community"],
        }
        themes_correct = 0
        theme_details = []
        for day, keywords in theme_map.items():
            # Find content around the day heading
            day_pattern = re.compile(rf'##\s*{day}[^\n]*\n(.*?)(?=##\s*\w|\Z)', re.IGNORECASE | re.DOTALL)
            day_match = day_pattern.search(content)
            if day_match:
                day_content = day_match.group(0).lower()
                found = any(kw in day_content for kw in keywords)
            else:
                # Fallback: search broader context
                idx = content_lower.find(day)
                if idx >= 0:
                    day_section = content_lower[idx:idx+500]
                    found = any(kw in day_section for kw in keywords)
                else:
                    found = False
            if found:
                themes_correct += 1
                theme_details.append(f"{day}: ✓")
            else:
                theme_details.append(f"{day}: ✗ (expected one of {keywords})")

        themes_passed = themes_correct >= 6  # Allow 1 miss for flexibility
        checks.append({
            "name": "Day themes follow the prescribed content mix",
            "passed": themes_passed,
            "detail": f"{themes_correct}/7 themes correct. Details: {'; '.join(theme_details)}"
        })
    except Exception as e:
        checks.append({"name": "Day themes correct", "passed": False, "detail": f"Exception: {e}"})

    # --- Check 7: Twitter posts ≤280 characters ---
    try:
        # Extract Twitter/X post bodies
        # Pattern: after "### 🐦 Twitter/X" or "### Twitter", grab the next non-empty line(s) up to blank line or next heading
        twitter_sections = re.findall(
            r'###\s*(?:🐦\s*)?Twitter(?:/X)?\s*\n+(.*?)(?=\n###|\n##|\n---|\Z)',
            content, re.DOTALL | re.IGNORECASE
        )
        
        over_limit = []
        twitter_post_count = 0
        for section in twitter_sections:
            # Get the main post text (first paragraph, before "Best time:" or "**Best time**")
            post_text = re.split(r'\n\*\*Best time', section, maxsplit=1)[0].strip()
            post_text = re.split(r'\nBest time', post_text, maxsplit=1)[0].strip()
            # Remove markdown formatting for char count
            clean_text = re.sub(r'\*\*.*?\*\*', '', post_text).strip()
            if clean_text:
                twitter_post_count += 1
                if len(clean_text) > 280:
                    over_limit.append(f"Post #{twitter_post_count}: {len(clean_text)} chars")

        if twitter_post_count == 0:
            checks.append({
                "name": "Twitter posts ≤280 characters",
                "passed": False,
                "detail": "No Twitter posts found to evaluate"
            })
        else:
            twitter_ok = len(over_limit) == 0
            checks.append({
                "name": "Twitter posts ≤280 characters",
                "passed": twitter_ok,
                "detail": f"Checked {twitter_post_count} Twitter posts. Over limit: {over_limit if over_limit else 'none'}"
            })
    except Exception as e:
        checks.append({"name": "Twitter posts ≤280 characters", "passed": False, "detail": f"Exception: {e}"})

    # --- Check 8: Instagram posts have 5-10 hashtags ---
    try:
        instagram_sections = re.findall(
            r'###\s*(?:📸\s*)?Instagram\s*\n+(.*?)(?=\n###|\n##|\n---|\Z)',
            content, re.DOTALL | re.IGNORECASE
        )
        
        hashtag_violations = []
        ig_count = 0
        for section in instagram_sections:
            # Find the hashtags line(s) - look for lines with # tags
            hashtag_lines = re.findall(r'#\w+', section)
            # Filter out section headers
            hashtag_count = len(hashtag_lines)
            ig_count += 1
            if hashtag_count < 5 or hashtag_count > 10:
                hashtag_violations.append(f"Post #{ig_count}: {hashtag_count} hashtags (need 5-10)")

        if ig_count == 0:
            checks.append({
                "name": "Instagram posts have 5-10 hashtags",
                "passed": False,
                "detail": "No Instagram sections found"
            })
        else:
            ig_hashtag_ok = len(hashtag_violations) == 0
            checks.append({
                "name": "Instagram posts have 5-10 hashtags",
                "passed": ig_hashtag_ok,
                "detail": f"Checked {ig_count} Instagram posts. Violations: {hashtag_violations if hashtag_violations else 'none'}"
            })
    except Exception as e:
        checks.append({"name": "Instagram hashtags 5-10", "passed": False, "detail": f"Exception: {e}"})

    # --- Check 9: LinkedIn posts have 3-5 hashtags ---
    try:
        linkedin_sections = re.findall(
            r'###\s*(?:💼\s*)?LinkedIn\s*\n+(.*?)(?=\n###|\n##|\n---|\Z)',
            content, re.DOTALL | re.IGNORECASE
        )
        
        linkedin_violations = []
        li_count = 0
        for section in linkedin_sections:
            hashtag_count = len(re.findall(r'#\w+', section))
            li_count += 1
            if hashtag_count < 3 or hashtag_count > 5:
                linkedin_violations.append(f"Post #{li_count}: {hashtag_count} hashtags (need 3-5)")

        if li_count == 0:
            checks.append({
                "name": "LinkedIn posts have 3-5 hashtags",
                "passed": False,
                "detail": "No LinkedIn sections found"
            })
        else:
            li_hashtag_ok = len(linkedin_violations) == 0
            checks.append({
                "name": "LinkedIn posts have 3-5 hashtags",
                "passed": li_hashtag_ok,
                "detail": f"Checked {li_count} LinkedIn posts. Violations: {linkedin_violations if linkedin_violations else 'none'}"
            })
    except Exception as e:
        checks.append({"name": "LinkedIn hashtags 3-5", "passed": False, "detail": f"Exception: {e}"})

    # --- Check 10: Posting times included ---
    try:
        time_pattern = re.compile(r'\d{1,2}:\d{2}\s*(?:AM|PM)', re.IGNORECASE)
        time_matches = time_pattern.findall(content)
        times_present = len(time_matches) >= 14  # At least 2 times per day (14 minimum)
        checks.append({
            "name": "Best posting times included (≥14 time references)",
            "passed": times_present,
            "detail": f"Found {len(time_matches)} posting time references"
        })
    except Exception as e:
        checks.append({"name": "Posting times included", "passed": False, "detail": f"Exception: {e}"})

    # --- Scoring ---
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0

    # Critical checks that must pass for overall pass
    critical_names = [
        "content-calendar.md exists",
        "Topic 'plant-based nutrition' present",
        "Target audience 'health-conscious Gen Z' present",
        "All 7 days (Mon–Sun) present",
        "All 3 platforms (Twitter, LinkedIn, Instagram) present",
        "Twitter posts ≤280 characters",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_names
    )

    overall_passed = critical_passed and score >= 0.75

    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace_dir)