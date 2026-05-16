import sys
import json
import re
from pathlib import Path
from datetime import datetime

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    max_checks = 10

    def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # --- CHECK 1: Report file exists in data/ directory ---
    report_files = list(workspace.glob("data/trend-report-*.json"))
    # Also check nested
    if not report_files:
        report_files = list(workspace.rglob("trend-report-*.json"))

    file_found = len(report_files) > 0
    score = add_check(
        "report_file_exists",
        file_found,
        f"Found {len(report_files)} trend-report file(s): {[str(f) for f in report_files]}"
    )
    total_score += score

    if not file_found:
        output = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(output))
        return

    # Use the most recently modified report file
    report_path = sorted(report_files, key=lambda f: f.stat().st_mtime, reverse=True)[0]

    # --- CHECK 2: File is valid JSON ---
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        total_score += add_check("valid_json", True, f"File {report_path.name} is valid JSON")
    except Exception as e:
        total_score += add_check("valid_json", False, f"JSON parse error: {e}")
        output = {"passed": False, "score": round(total_score / max_checks, 3), "checks": checks}
        print(json.dumps(output))
        return

    # --- CHECK 3: Correct filename format (trend-report-YYYY-MM-DD.json) ---
    fname = report_path.name
    date_pattern = re.compile(r'^trend-report-(\d{4}-\d{2}-\d{2})\.json$')
    date_match = date_pattern.match(fname)
    has_correct_filename = date_match is not None
    total_score += add_check(
        "correct_filename_format",
        has_correct_filename,
        f"Filename '{fname}' {'matches' if has_correct_filename else 'does NOT match'} pattern trend-report-YYYY-MM-DD.json"
    )

    # --- CHECK 4: Top-level required keys ---
    required_top_keys = {"date", "trending_topics", "content_ideas", "viral_formats"}
    present_keys = set(report.keys())
    missing_keys = required_top_keys - present_keys
    has_all_keys = len(missing_keys) == 0
    total_score += add_check(
        "top_level_schema_keys",
        has_all_keys,
        f"Missing top-level keys: {missing_keys}" if not has_all_keys else "All required top-level keys present"
    )

    # --- CHECK 5: date field format ---
    try:
        date_val = report.get("date", "")
        datetime.strptime(date_val, "%Y-%m-%d")
        total_score += add_check("date_field_valid", True, f"date field '{date_val}' is valid YYYY-MM-DD format")
    except Exception as e:
        total_score += add_check("date_field_valid", False, f"date field invalid: {report.get('date')} — {e}")

    # --- CHECK 6: trending_topics schema and engagement filter applied ---
    trending_topics = report.get("trending_topics", [])
    required_topic_fields = {"topic", "source", "engagement", "angle", "evidence"}
    valid_sources = {"twitter", "reddit", "rss", "youtube"}
    valid_engagement = {"high", "medium", "low"}

    topic_schema_ok = True
    topic_detail_parts = []

    if not isinstance(trending_topics, list) or len(trending_topics) == 0:
        topic_schema_ok = False
        topic_detail_parts.append("trending_topics is empty or not a list")
    else:
        for i, t in enumerate(trending_topics):
            missing = required_topic_fields - set(t.keys())
            if missing:
                topic_schema_ok = False
                topic_detail_parts.append(f"topic[{i}] missing fields: {missing}")
            if t.get("source") not in valid_sources:
                topic_schema_ok = False
                topic_detail_parts.append(f"topic[{i}] invalid source: '{t.get('source')}' (must be one of {valid_sources})")
            if t.get("engagement") not in valid_engagement:
                topic_schema_ok = False
                topic_detail_parts.append(f"topic[{i}] invalid engagement: '{t.get('engagement')}' (must be one of {valid_engagement})")

    total_score += add_check(
        "trending_topics_schema",
        topic_schema_ok,
        "; ".join(topic_detail_parts) if topic_detail_parts else f"All {len(trending_topics)} trending_topics have correct schema"
    )

    # --- CHECK 7: Engagement filter respected — low-engagement items excluded ---
    # Twitter: tweets with likes<=100 OR retweets<=20 should NOT appear
    # The tweet with id 1003 (likes=67, retweets=8) and id 1005 (likes=88, retweets=12) should be excluded
    # Check that low-engagement twitter content is not in trending topics
    all_evidence = [str(t.get("evidence", "")).lower() for t in trending_topics]
    all_angles = [str(t.get("angle", "")).lower() for t in trending_topics]
    all_text = " ".join(all_evidence + all_angles + [str(t.get("topic", "")).lower() for t in trending_topics])

    # Low-engagement tweet IDs that should be excluded
    low_engagement_markers = ["status/1003", "status/1005"]
    leaked_low_engagement = [m for m in low_engagement_markers if m in all_text]

    engagement_filter_ok = len(leaked_low_engagement) == 0
    total_score += add_check(
        "engagement_filter_applied",
        engagement_filter_ok,
        f"Low-engagement tweet URLs found in report: {leaked_low_engagement}" if leaked_low_engagement else "No low-engagement twitter items leaked into report"
    )

    # --- CHECK 8: content_ideas schema ---
    content_ideas = report.get("content_ideas", [])
    required_idea_fields = {"title", "format", "hook", "key_points", "cta"}
    valid_formats = {"thread", "article", "newsletter", "video-script"}

    idea_schema_ok = True
    idea_detail_parts = []

    if not isinstance(content_ideas, list) or len(content_ideas) == 0:
        idea_schema_ok = False
        idea_detail_parts.append("content_ideas is empty or not a list")
    else:
        for i, idea in enumerate(content_ideas):
            missing = required_idea_fields - set(idea.keys())
            if missing:
                idea_schema_ok = False
                idea_detail_parts.append(f"idea[{i}] missing fields: {missing}")
            fmt = idea.get("format", "")
            if fmt not in valid_formats:
                idea_schema_ok = False
                idea_detail_parts.append(f"idea[{i}] invalid format: '{fmt}' (must be one of {valid_formats})")
            kp = idea.get("key_points", [])
            if not isinstance(kp, list) or len(kp) < 1:
                idea_schema_ok = False
                idea_detail_parts.append(f"idea[{i}] key_points must be a non-empty list")

    total_score += add_check(
        "content_ideas_schema",
        idea_schema_ok,
        "; ".join(idea_detail_parts) if idea_detail_parts else f"All {len(content_ideas)} content_ideas have correct schema"
    )

    # --- CHECK 9: viral_formats schema ---
    viral_formats = report.get("viral_formats", [])
    required_viral_fields = {"format", "example", "why_it_works"}

    viral_schema_ok = True
    viral_detail_parts = []

    if not isinstance(viral_formats, list) or len(viral_formats) == 0:
        viral_schema_ok = False
        viral_detail_parts.append("viral_formats is empty or not a list")
    else:
        for i, vf in enumerate(viral_formats):
            missing = required_viral_fields - set(vf.keys())
            if missing:
                viral_schema_ok = False
                viral_detail_parts.append(f"viral_formats[{i}] missing fields: {missing}")

    total_score += add_check(
        "viral_formats_schema",
        viral_schema_ok,
        "; ".join(viral_detail_parts) if viral_detail_parts else f"All {len(viral_formats)} viral_formats have correct schema"
    )

    # --- CHECK 10: Multi-source coverage (at least 3 distinct sources represented) ---
    sources_present = set()
    for t in trending_topics:
        src = t.get("source", "").lower()
        if src in valid_sources:
            sources_present.add(src)

    multi_source_ok = len(sources_present) >= 3
    total_score += add_check(
        "multi_source_coverage",
        multi_source_ok,
        f"Sources represented: {sources_present} ({'OK' if multi_source_ok else 'need at least 3 distinct sources'})"
    )

    # --- Final scoring ---
    final_score = round(total_score / max_checks, 3)
    passed = final_score >= 0.75 and all(
        c["passed"] for c in checks
        if c["name"] in {
            "report_file_exists",
            "valid_json",
            "top_level_schema_keys",
            "trending_topics_schema",
            "content_ideas_schema",
            "viral_formats_schema"
        }
    )

    output = {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace_dir)