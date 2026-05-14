import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str) -> dict:
    checks = []
    workspace = Path(workspace_dir)

    # ── Locate content-calendar.md ────────────────────────────────────────────
    candidates = list(workspace.rglob("content-calendar.md"))
    # Prefer root-level
    root_calendar = workspace / "content-calendar.md"
    if root_calendar.exists():
        calendar_path = root_calendar
    elif candidates:
        # Filter out the known distractor
        real = [p for p in candidates if "drafts" not in str(p) and "archive" not in str(p)]
        calendar_path = real[0] if real else candidates[0]
    else:
        calendar_path = None

    file_exists = calendar_path is not None and calendar_path.exists()
    checks.append({
        "name": "content-calendar.md exists",
        "passed": file_exists,
        "detail": f"Found at {calendar_path}" if file_exists else "content-calendar.md not found anywhere in workspace"
    })

    if not file_exists:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    try:
        content = calendar_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Check correct topic ───────────────────────────────────────────────────
    topic_present = "health and wellness" in content.lower() or "health & wellness" in content.lower()
    checks.append({
        "name": "correct topic: 'health and wellness'",
        "passed": topic_present,
        "detail": f"Topic found in calendar: {topic_present}"
    })

    # ── Check correct target audience ─────────────────────────────────────────
    audience_present = "busy healthcare professionals" in content.lower()
    checks.append({
        "name": "correct audience: 'busy healthcare professionals'",
        "passed": audience_present,
        "detail": f"Audience found in calendar: {audience_present}"
    })

    # ── Check all 7 days present ──────────────────────────────────────────────
    required_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    days_found = [day for day in required_days if day in content]
    all_days = len(days_found) == 7
    checks.append({
        "name": "all 7 days present (Mon–Sun)",
        "passed": all_days,
        "detail": f"Days found: {days_found}"
    })

    # ── Check all 3 platforms per day ─────────────────────────────────────────
    platforms = ["Twitter", "LinkedIn", "Instagram"]
    for platform in platforms:
        count = len(re.findall(rf'###\s+{platform}', content, re.IGNORECASE))
        platform_ok = count >= 7
        checks.append({
            "name": f"{platform} sections: at least 7 (one per day)",
            "passed": platform_ok,
            "detail": f"Found {count} {platform} sections"
        })

    # ── Check correct day-theme mapping ──────────────────────────────────────
    theme_map = {
        "Monday": ["Motivational", "Week Opener"],
        "Tuesday": ["Educational", "How-to"],
        "Wednesday": ["Engagement", "Question"],
        "Thursday": ["Behind-the-scenes", "Story"],
        "Friday": ["Tip", "Quick Win"],
        "Saturday": ["Curated", "Industry News"],
        "Sunday": ["Reflection", "Community"],
    }
    for day, themes in theme_map.items():
        # Look for the day header with theme
        pattern = rf'##\s+{day}[^\n]*(?:{")|(?:".join(themes)})'
        day_theme_ok = bool(re.search(pattern, content, re.IGNORECASE))
        checks.append({
            "name": f"{day} has correct theme ({'/'.join(themes)})",
            "passed": day_theme_ok,
            "detail": f"Theme pattern found for {day}: {day_theme_ok}"
        })

    # ── Check Twitter char limit (≤280 chars) ────────────────────────────────
    # Extract all Twitter post bodies (text immediately after ### Twitter/X section header)
    twitter_sections = re.findall(
        r'###\s+Twitter(?:/X)?\s*\n(.*?)(?=\n###|\n##|\Z)',
        content, re.DOTALL | re.IGNORECASE
    )
    twitter_violations = []
    for i, section in enumerate(twitter_sections):
        # Get first non-empty, non-metadata line(s) as the post body
        lines = [l.strip() for l in section.strip().split('\n') if l.strip()]
        if not lines:
            continue
        # Collect lines until we hit metadata markers
        post_lines = []
        for line in lines:
            if line.startswith("**Best time") or line.startswith("**Hashtags"):
                break
            post_lines.append(line)
        post_body = ' '.join(post_lines)
        if len(post_body) > 280:
            twitter_violations.append(f"Section {i+1}: {len(post_body)} chars")

    twitter_char_ok = len(twitter_violations) == 0
    checks.append({
        "name": "Twitter/X posts ≤280 characters",
        "passed": twitter_char_ok,
        "detail": f"Violations: {twitter_violations}" if not twitter_char_ok else f"All {len(twitter_sections)} Twitter posts within limit"
    })

    # ── Check LinkedIn hashtag counts (3–5) ───────────────────────────────────
    linkedin_sections = re.findall(
        r'###\s+LinkedIn\s*\n(.*?)(?=\n###|\n##|\Z)',
        content, re.DOTALL | re.IGNORECASE
    )
    linkedin_hashtag_issues = []
    for i, section in enumerate(linkedin_sections):
        hashtag_lines = re.findall(r'\*\*Hashtags:\*\*\s*(.*)', section)
        if hashtag_lines:
            hashtags = re.findall(r'#\w+', hashtag_lines[0])
            count = len(hashtags)
            if not (3 <= count <= 5):
                linkedin_hashtag_issues.append(f"Section {i+1}: {count} hashtags ({hashtag_lines[0].strip()})")
    linkedin_hashtags_ok = len(linkedin_hashtag_issues) == 0
    checks.append({
        "name": "LinkedIn sections have 3–5 hashtags each",
        "passed": linkedin_hashtags_ok,
        "detail": f"Issues: {linkedin_hashtag_issues}" if not linkedin_hashtags_ok else f"All {len(linkedin_sections)} LinkedIn sections compliant"
    })

    # ── Check Instagram hashtag counts (5–10) ────────────────────────────────
    instagram_sections = re.findall(
        r'###\s+Instagram\s*\n(.*?)(?=\n###|\n##|\Z)',
        content, re.DOTALL | re.IGNORECASE
    )
    instagram_hashtag_issues = []
    for i, section in enumerate(instagram_sections):
        hashtag_lines = re.findall(r'\*\*Hashtags:\*\*\s*(.*)', section)
        if hashtag_lines:
            hashtags = re.findall(r'#\w+', hashtag_lines[0])
            count = len(hashtags)
            if not (5 <= count <= 10):
                instagram_hashtag_issues.append(f"Section {i+1}: {count} hashtags")
    instagram_hashtags_ok = len(instagram_hashtag_issues) == 0
    checks.append({
        "name": "Instagram sections have 5–10 hashtags each",
        "passed": instagram_hashtags_ok,
        "detail": f"Issues: {instagram_hashtag_issues}" if not instagram_hashtags_ok else f"All {len(instagram_sections)} Instagram sections compliant"
    })

    # ── Check best posting times present ─────────────────────────────────────
    posting_times = re.findall(r'\*\*Best time:\*\*\s*\d+:\d+\s*[AP]M', content)
    # 7 days × 3 platforms = 21 sections
    times_ok = len(posting_times) >= 18  # allow some tolerance
    checks.append({
        "name": "posting times specified (≥18 of 21 platform sections)",
        "passed": times_ok,
        "detail": f"Found {len(posting_times)} posting time entries"
    })

    # ── Check content is NOT generic / not old archive ────────────────────────
    is_not_old_draft = "2023-11-01" not in content and "DRAFT — NOT FINALIZED" not in content
    checks.append({
        "name": "output is fresh calendar, not an old draft",
        "passed": is_not_old_draft,
        "detail": "Calendar appears to be freshly generated" if is_not_old_draft else "Calendar appears to be an old draft or archive file"
    })

    # ── Check content mentions topic in actual post bodies ───────────────────
    topic_in_posts = content.lower().count("health") >= 14  # should appear in most sections
    checks.append({
        "name": "topic keyword appears throughout post bodies (≥14 occurrences)",
        "passed": topic_in_posts,
        "detail": f"'health' appears {content.lower().count('health')} times in calendar"
    })

    # ── Calculate score ───────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    overall_passed = (
        file_exists and
        topic_present and
        audience_present and
        all_days and
        twitter_char_ok and
        linkedin_hashtags_ok and
        instagram_hashtags_ok
    )

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "workspace arg", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))