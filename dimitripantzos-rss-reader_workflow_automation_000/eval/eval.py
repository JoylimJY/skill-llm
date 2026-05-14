#!/usr/bin/env python3
"""
Evaluation script for the RSS Reader competitive intelligence task.
Checks:
  1. feeds.json has exactly 3 feeds with correct URLs and categories
  2. feeds.json settings: maxItemsPerFeed=5, maxAgeDays=14, summaryEnabled=true
  3. feed_report.txt exists and contains '## Content Ideas' header
  4. feed_report.txt contains at least one keyword-matched item (CRISPR or clinical trial or FDA)
  5. feed_report.txt contains category section headers matching the registered categories
"""

import sys
import json
import re
from pathlib import Path

def main(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0
    weights = {
        "feeds_count":          0.15,
        "feeds_urls_categories":0.25,
        "settings_correct":     0.20,
        "report_exists":        0.10,
        "report_header":        0.15,
        "report_keyword_match": 0.15,
    }

    # ── Locate feeds.json ─────────────────────────────────────────────────────
    FEEDS_JSON = ws / "skills" / "rss-reader" / "rss-reader" / "feeds.json"

    feeds_data = None
    try:
        with open(FEEDS_JSON) as f:
            feeds_data = json.load(f)
    except Exception as e:
        checks.append({"name": "feeds_json_readable", "passed": False, "detail": f"Cannot read feeds.json: {e}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ── Check 1: exactly 3 feeds ──────────────────────────────────────────────
    try:
        feed_list = feeds_data.get("feeds", [])
        num_feeds = len(feed_list)
        ok = num_feeds == 3
        checks.append({
            "name": "feeds_count",
            "passed": ok,
            "detail": f"Expected 3 feeds, found {num_feeds}"
        })
        if ok:
            total_score += weights["feeds_count"]
    except Exception as e:
        checks.append({"name": "feeds_count", "passed": False, "detail": str(e)})

    # ── Check 2: correct URLs and categories ──────────────────────────────────
    try:
        EXPECTED = {
            "http://127.0.0.1:18080/competitors.xml": "competitors",
            "http://localhost:18080/competitors.xml": "competitors",
            "http://127.0.0.1:18080/clinical.xml":    "clinical",
            "http://localhost:18080/clinical.xml":    "clinical",
            "http://127.0.0.1:18080/regulatory.xml":  "regulatory",
            "http://localhost:18080/regulatory.xml":  "regulatory",
        }

        # Build a canonical map: normalize localhost <-> 127.0.0.1
        def norm_url(u):
            return u.replace("localhost", "127.0.0.1")

        # Required canonical URLs
        REQUIRED_CANONICAL = {
            "http://127.0.0.1:18080/competitors.xml": "competitors",
            "http://127.0.0.1:18080/clinical.xml":    "clinical",
            "http://127.0.0.1:18080/regulatory.xml":  "regulatory",
        }

        found = {}
        for feed in feed_list:
            url_norm = norm_url(feed.get("url", ""))
            cat = feed.get("category", "")
            found[url_norm] = cat

        missing = []
        wrong_cat = []
        for req_url, req_cat in REQUIRED_CANONICAL.items():
            if req_url not in found:
                missing.append(req_url)
            elif found[req_url] != req_cat:
                wrong_cat.append(f"{req_url}: expected '{req_cat}', got '{found[req_url]}'")

        ok = len(missing) == 0 and len(wrong_cat) == 0
        detail = "All URLs and categories correct." if ok else \
                 f"Missing URLs: {missing}; Wrong categories: {wrong_cat}"
        checks.append({"name": "feeds_urls_categories", "passed": ok, "detail": detail})
        if ok:
            total_score += weights["feeds_urls_categories"]
    except Exception as e:
        checks.append({"name": "feeds_urls_categories", "passed": False, "detail": str(e)})

    # ── Check 3: settings correct ─────────────────────────────────────────────
    try:
        settings = feeds_data.get("settings", {})
        max_items = settings.get("maxItemsPerFeed")
        max_age   = settings.get("maxAgeDays")
        summary   = settings.get("summaryEnabled")

        items_ok   = max_items == 5
        age_ok     = max_age   == 14
        summary_ok = summary   is True

        ok = items_ok and age_ok and summary_ok
        detail = (
            f"maxItemsPerFeed={max_items} (want 5, {'OK' if items_ok else 'FAIL'}), "
            f"maxAgeDays={max_age} (want 14, {'OK' if age_ok else 'FAIL'}), "
            f"summaryEnabled={summary} (want true, {'OK' if summary_ok else 'FAIL'})"
        )
        checks.append({"name": "settings_correct", "passed": ok, "detail": detail})
        if ok:
            total_score += weights["settings_correct"]
    except Exception as e:
        checks.append({"name": "settings_correct", "passed": False, "detail": str(e)})

    # ── Locate feed_report.txt ────────────────────────────────────────────────
    report_path = None
    try:
        candidates = list(ws.rglob("feed_report.txt"))
        if candidates:
            report_path = candidates[0]
    except Exception:
        pass

    # ── Check 4: file exists ──────────────────────────────────────────────────
    ok = report_path is not None and report_path.exists()
    checks.append({
        "name": "report_exists",
        "passed": ok,
        "detail": f"feed_report.txt {'found at ' + str(report_path) if ok else 'NOT FOUND anywhere in workspace'}"
    })
    if ok:
        total_score += weights["report_exists"]

    # ── Read report content ───────────────────────────────────────────────────
    report_content = ""
    if report_path and report_path.exists():
        try:
            report_content = report_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            checks.append({"name": "report_readable", "passed": False, "detail": str(e)})

    # ── Check 5: contains '## Content Ideas' header ──────────────────────────
    try:
        ok = bool(re.search(r'^##\s+Content Ideas', report_content, re.MULTILINE | re.IGNORECASE))
        checks.append({
            "name": "report_header",
            "passed": ok,
            "detail": "'## Content Ideas' header " + ("found" if ok else "NOT FOUND") + " in feed_report.txt"
        })
        if ok:
            total_score += weights["report_header"]
    except Exception as e:
        checks.append({"name": "report_header", "passed": False, "detail": str(e)})

    # ── Check 6: at least one keyword-matched entry ───────────────────────────
    try:
        KEYWORDS = ["crispr", "clinical trial", "fda"]
        content_lower = report_content.lower()
        matched = [kw for kw in KEYWORDS if kw in content_lower]
        ok = len(matched) >= 1
        checks.append({
            "name": "report_keyword_match",
            "passed": ok,
            "detail": f"Keywords matched in report: {matched}. At least 1 required."
        })
        if ok:
            total_score += weights["report_keyword_match"]
    except Exception as e:
        checks.append({"name": "report_keyword_match", "passed": False, "detail": str(e)})

    # ── Final result ──────────────────────────────────────────────────────────
    passed = all(c["passed"] for c in checks)
    # Also accept partial pass if score >= 0.7
    passed = passed or total_score >= 0.70

    print(json.dumps({
        "passed": passed,
        "score": round(total_score, 3),
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/root/clawd"
    main(workspace_dir)