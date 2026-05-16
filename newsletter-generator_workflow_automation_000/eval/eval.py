#!/usr/bin/env python3
"""Evaluation script for the fintech newsletter automation task."""
import sys
import json
import re
from pathlib import Path

def load_json_file(path):
    with open(path) as f:
        return json.load(f)

def find_file(workspace, filename):
    matches = list(Path(workspace).rglob(filename))
    return matches[0] if matches else None

def run_eval(workspace):
    workspace = Path(workspace)
    checks = []

    # ── CHECK 1: curated_content.json exists and is valid ────────────────────
    curated_path = find_file(workspace, "curated_content.json")
    curated_ok = False
    curated_data = {}
    try:
        assert curated_path is not None, "curated_content.json not found"
        curated_data = load_json_file(curated_path)
        assert "articles" in curated_data, "Missing 'articles' key"
        assert "keywords" in curated_data, "Missing 'keywords' key"
        curated_ok = True
        detail = f"Found {curated_data.get('articles_found',0)} articles, keywords: {curated_data.get('keywords')}"
    except Exception as e:
        detail = str(e)
    checks.append({"name": "curated_content.json exists and is valid JSON", "passed": curated_ok, "detail": detail})

    # ── CHECK 2: curated content has fintech/relevant keywords ────────────────
    kw_ok = False
    try:
        keywords = curated_data.get("keywords", [])
        assert len(keywords) >= 2, f"Expected ≥2 keywords, got {keywords}"
        # Accept any fintech-adjacent keywords
        joined = " ".join(k.lower() for k in keywords)
        fintech_terms = ["fintech", "finance", "investing", "crypto", "banking", "defi",
                         "personal finance", "money", "trading", "blockchain", "stock",
                         "wealth", "budget", "savings", "payments"]
        matched = [t for t in fintech_terms if t in joined]
        assert len(matched) >= 1, f"No fintech keywords detected in: {keywords}"
        kw_ok = True
        detail = f"Keywords: {keywords}, fintech matches: {matched}"
    except Exception as e:
        detail = str(e)
    checks.append({"name": "Curation uses fintech-relevant keywords", "passed": kw_ok, "detail": detail})

    # ── CHECK 3: min-relevance was set (non-zero, bespoke parameter) ──────────
    relevance_ok = False
    try:
        min_rel = curated_data.get("min_relevance", 0.0)
        assert min_rel > 0.0, f"min_relevance should be > 0, got {min_rel}"
        assert min_rel <= 1.0, f"min_relevance must be ≤ 1.0, got {min_rel}"
        relevance_ok = True
        detail = f"min_relevance={min_rel} (valid range 0-1)"
    except Exception as e:
        detail = str(e)
    checks.append({"name": "curate_content --min-relevance was used (proprietary param, 0-1)", "passed": relevance_ok, "detail": detail})

    # ── CHECK 4: Weekly newsletter .md exists ─────────────────────────────────
    newsletter_path = find_file(workspace, "fintech_weekly.md")
    # Also accept common variants
    if newsletter_path is None:
        for candidate in ["weekly_newsletter.md", "newsletter.md", "fintech-weekly.md", "weekly.md"]:
            newsletter_path = find_file(workspace, candidate)
            if newsletter_path:
                break
    newsletter_ok = False
    newsletter_content = ""
    try:
        assert newsletter_path is not None, "No weekly newsletter .md file found"
        newsletter_content = newsletter_path.read_text()
        assert len(newsletter_content) > 100, "Newsletter file is suspiciously short"
        newsletter_ok = True
        detail = f"Found {newsletter_path.name}, {len(newsletter_content)} chars"
    except Exception as e:
        detail = str(e)
    checks.append({"name": "Weekly newsletter .md file created", "passed": newsletter_ok, "detail": detail})

    # ── CHECK 5: Newsletter type is weekly (proprietary --type flag) ──────────
    type_ok = False
    try:
        assert newsletter_content, "No newsletter content"
        meta_match = re.search(r'<!-- META:(.*?) -->', newsletter_content)
        assert meta_match, "Missing META comment in newsletter (was generate_newsletter.py used?)"
        meta = json.loads(meta_match.group(1))
        assert meta.get("type") == "weekly", f"type should be 'weekly', got '{meta.get('type')}'"
        type_ok = True
        detail = f"type='{meta.get('type')}'"
    except Exception as e:
        detail = str(e)
    checks.append({"name": "Newsletter --type is 'weekly' (not daily/monthly)", "passed": type_ok, "detail": detail})

    # ── CHECK 6: Article count ≥ 15 (weekly standard) ────────────────────────
    articles_ok = False
    try:
        meta_match = re.search(r'<!-- META:(.*?) -->', newsletter_content)
        assert meta_match, "No META in newsletter"
        meta = json.loads(meta_match.group(1))
        n = meta.get("articles", 0)
        assert n >= 15, f"Weekly newsletter should have ≥15 articles, got {n}"
        articles_ok = True
        detail = f"articles={n}"
    except Exception as e:
        detail = str(e)
    checks.append({"name": "Newsletter has ≥15 articles (weekly roundup standard)", "passed": articles_ok, "detail": detail})

    # ── CHECK 7: Affiliate links added via add_affiliate_links.py ────────────
    affiliate_ok = False
    try:
        affiliate_match = re.search(r'<!-- AFFILIATE_META:(.*?) -->', newsletter_content)
        assert affiliate_match, "No AFFILIATE_META in newsletter (was add_affiliate_links.py run?)"
        ameta = json.loads(affiliate_match.group(1))
        network = ameta.get("network", "")
        assert network in ["amazon", "shareasale", "cj", "impact"], \
            f"network must be amazon/shareasale/cj/impact, got '{network}'"
        affiliate_ok = True
        detail = f"network={network}, links={ameta.get('links_added')}"
    except Exception as e:
        detail = str(e)
    checks.append({"name": "Affiliate links added via recognized network (amazon/shareasale/cj/impact)", "passed": affiliate_ok, "detail": detail})

    # ── CHECK 8: FTC disclosure at TOP (bespoke --disclosure-position constraint) ──
    disclosure_top_ok = False
    try:
        affiliate_match = re.search(r'<!-- AFFILIATE_META:(.*?) -->', newsletter_content)
        assert affiliate_match, "No AFFILIATE_META"
        ameta = json.loads(affiliate_match.group(1))
        pos = ameta.get("disclosure_position", "")
        assert pos == "top", f"disclosure_position must be 'top', got '{pos}'"
        # Also verify disclosure actually appears before content body
        ftc_idx = newsletter_content.find("FTC DISCLOSURE")
        subject_idx = newsletter_content.find("Subject:")
        assert ftc_idx != -1, "FTC DISCLOSURE text not found in newsletter"
        assert ftc_idx < subject_idx, "FTC disclosure should appear before newsletter body (disclosure at top)"
        disclosure_top_ok = True
        detail = f"disclosure_position='{pos}', FTC at char {ftc_idx}, Subject at char {subject_idx}"
    except Exception as e:
        detail = str(e)
    checks.append({"name": "FTC disclosure position is 'top' (proprietary constraint)", "passed": disclosure_top_ok, "detail": detail})

    # ── CHECK 9: schedule.json exists and is valid ────────────────────────────
    schedule_path = find_file(workspace, "schedule.json")
    if schedule_path is None:
        for candidate in ["send_schedule.json", "newsletter_schedule.json", "fintech_schedule.json"]:
            schedule_path = find_file(workspace, candidate)
            if schedule_path:
                break
    schedule_ok = False
    schedule_data = {}
    try:
        assert schedule_path is not None, "No schedule .json file found"
        schedule_data = load_json_file(schedule_path)
        assert "send_time" in schedule_data, "Missing 'send_time'"
        assert "timezone" in schedule_data, "Missing 'timezone'"
        assert "segments" in schedule_data, "Missing 'segments'"
        schedule_ok = True
        detail = f"Found {schedule_path.name}: time={schedule_data.get('send_time')}, tz={schedule_data.get('timezone')}"
    except Exception as e:
        detail = str(e)
    checks.append({"name": "Schedule JSON created with required fields", "passed": schedule_ok, "detail": detail})

    # ── CHECK 10: Schedule timezone is valid and B2B-appropriate send time ────
    schedule_detail_ok = False
    try:
        import pytz
        tz_str = schedule_data.get("timezone", "")
        tz = pytz.timezone(tz_str)  # raises if invalid
        assert schedule_data.get("timezone_valid", False), "timezone_valid=False in schedule"

        send_time = schedule_data.get("send_time", "")
        # B2B newsletters: Tue-Thu, 8-11 AM per SKILL.md
        # We accept any time string HH:MM between 07:00 and 12:00 as "morning"
        hour = int(send_time.split(":")[0]) if ":" in send_time else -1
        assert 7 <= hour <= 12, f"Send time {send_time} is not in morning window (07-12)"

        segments = schedule_data.get("segments", [])
        assert len(segments) >= 1, "No subscriber segments specified"

        schedule_detail_ok = True
        detail = f"timezone={tz_str}, send_time={send_time}, segments={segments}"
    except Exception as e:
        detail = str(e)
    checks.append({"name": "Schedule has valid timezone and morning send time", "passed": schedule_detail_ok, "detail": detail})

    # ── CHECK 11: Newsletter tone is professional or conversational ───────────
    tone_ok = False
    try:
        meta_match = re.search(r'<!-- META:(.*?) -->', newsletter_content)
        assert meta_match, "No META"
        meta = json.loads(meta_match.group(1))
        tone = meta.get("tone", "")
        assert tone in ["professional", "conversational", "casual"], \
            f"Tone '{tone}' is not a recognized value"
        # For a fintech professional audience, professional or conversational is correct
        assert tone != "playful", "Playful tone is inappropriate for fintech B2B newsletter"
        tone_ok = True
        detail = f"tone='{tone}'"
    except Exception as e:
        detail = str(e)
    checks.append({"name": "Newsletter tone is appropriate (professional/conversational, not playful)", "passed": tone_ok, "detail": detail})

    # ── Scoring ───────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall_passed = passed_count >= 9  # Must pass at least 9/11

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)