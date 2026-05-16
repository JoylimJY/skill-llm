import sys
import json
import time
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    total_score = 0.0
    max_score = 0.0

    home = Path.home()
    shared_dir = home / ".openclaw" / "workspace" / "shared"
    trends_file = shared_dir / "trends.json"
    highlights_file = shared_dir / "highlights.json"

    # ── Helper ────────────────────────────────────────────────────────────────
    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, max_score
        max_score += weight
        if passed:
            total_score += weight
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ── Check 1: trends.json exists and is valid JSON ─────────────────────────
    try:
        raw = trends_file.read_text()
        trends_data = json.loads(raw)
        add_check(
            "trends_file_valid_json",
            True,
            f"trends.json is valid JSON with keys: {list(trends_data.keys())}"
        )
    except FileNotFoundError:
        add_check("trends_file_valid_json", False, "trends.json not found")
        trends_data = {}
    except Exception as e:
        add_check("trends_file_valid_json", False, f"JSON parse error: {e}")
        trends_data = {}

    # ── Check 2: highlights.json exists and is valid JSON ────────────────────
    try:
        raw_h = highlights_file.read_text()
        highlights_data = json.loads(raw_h)
        add_check(
            "highlights_file_valid_json",
            True,
            f"highlights.json is valid JSON with keys: {list(highlights_data.keys())}"
        )
    except FileNotFoundError:
        add_check("highlights_file_valid_json", False, "highlights.json not found")
        highlights_data = {}
    except Exception as e:
        add_check("highlights_file_valid_json", False, f"JSON parse error: {e}")
        highlights_data = {}

    # ── Check 3: At least 3 trends were written ──────────────────────────────
    try:
        trends_list = trends_data.get("trends", [])
        count = len(trends_list)
        passed = count >= 3
        add_check(
            "minimum_three_trends_written",
            passed,
            f"Found {count} trend(s) in trends.json (need >= 3)",
            weight=2.0
        )
    except Exception as e:
        add_check("minimum_three_trends_written", False, f"Error reading trends list: {e}", weight=2.0)
        trends_list = []

    # ── Check 4: Trends have required fields (source, topic, score, timestamp) 
    try:
        required_fields = {"source", "topic", "score", "timestamp"}
        malformed = [t for t in trends_list if not required_fields.issubset(t.keys())]
        passed = len(trends_list) > 0 and len(malformed) == 0
        add_check(
            "trends_have_required_fields",
            passed,
            f"{len(malformed)} trend(s) missing required fields {required_fields}" if malformed
            else f"All {len(trends_list)} trends have required fields"
        )
    except Exception as e:
        add_check("trends_have_required_fields", False, f"Error: {e}")

    # ── Check 5: Trends come from at least 2 distinct sources ────────────────
    try:
        sources = set(t.get("source", "") for t in trends_list)
        passed = len(sources) >= 2
        add_check(
            "trends_from_multiple_sources",
            passed,
            f"Trend sources found: {sources} (need >= 2 distinct sources)",
            weight=1.5
        )
    except Exception as e:
        add_check("trends_from_multiple_sources", False, f"Error: {e}", weight=1.5)

    # ── Check 6: Trend scores are integers (not strings) ─────────────────────
    try:
        non_int_scores = [t for t in trends_list if not isinstance(t.get("score"), int)]
        passed = len(trends_list) > 0 and len(non_int_scores) == 0
        add_check(
            "trend_scores_are_integers",
            passed,
            f"{len(non_int_scores)} trend(s) have non-integer scores" if non_int_scores
            else "All trend scores are integers"
        )
    except Exception as e:
        add_check("trend_scores_are_integers", False, f"Error: {e}")

    # ── Check 7: At least 2 highlights were written ──────────────────────────
    try:
        highlights_list = highlights_data.get("highlights", [])
        count_h = len(highlights_list)
        passed = count_h >= 2
        add_check(
            "minimum_two_highlights_written",
            passed,
            f"Found {count_h} highlight(s) in highlights.json (need >= 2)",
            weight=2.0
        )
    except Exception as e:
        add_check("minimum_two_highlights_written", False, f"Error: {e}", weight=2.0)
        highlights_list = []

    # ── Check 8: Highlights have required fields (source, title, summary, timestamp)
    try:
        required_h = {"source", "title", "summary", "timestamp"}
        malformed_h = [h for h in highlights_list if not required_h.issubset(h.keys())]
        passed = len(highlights_list) > 0 and len(malformed_h) == 0
        add_check(
            "highlights_have_required_fields",
            passed,
            f"{len(malformed_h)} highlight(s) missing required fields" if malformed_h
            else f"All {len(highlights_list)} highlights have required fields"
        )
    except Exception as e:
        add_check("highlights_have_required_fields", False, f"Error: {e}")

    # ── Check 9: Cleanup removed the stale legacy entries ────────────────────
    # The pre-seeded highlights were 72h old. A cleanup --hours 48 should remove them.
    # The agent-added entries should be recent and survive.
    try:
        cutoff_48h = time.time() - (48 * 3600)
        legacy_still_present = [
            h for h in highlights_list
            if h.get("source") == "legacy-agent" and h.get("timestamp", 0) < cutoff_48h
        ]
        passed = len(legacy_still_present) == 0
        add_check(
            "stale_legacy_highlights_cleaned_up",
            passed,
            f"{len(legacy_still_present)} stale legacy highlight(s) still present after cleanup" 
            if not passed else "All stale legacy entries (72h old) were correctly removed",
            weight=3.0
        )
    except Exception as e:
        add_check("stale_legacy_highlights_cleaned_up", False, f"Error: {e}", weight=3.0)

    # ── Check 10: Recent agent-written entries were NOT removed by cleanup ────
    try:
        recent_cutoff = time.time() - (48 * 3600)
        new_highlights = [
            h for h in highlights_list
            if h.get("source") != "legacy-agent" and h.get("timestamp", 0) >= recent_cutoff
        ]
        passed = len(new_highlights) >= 1
        add_check(
            "recent_highlights_survive_cleanup",
            passed,
            f"Found {len(new_highlights)} recent non-legacy highlight(s) surviving cleanup (need >= 1)",
            weight=2.0
        )
    except Exception as e:
        add_check("recent_highlights_survive_cleanup", False, f"Error: {e}", weight=2.0)

    # ── Check 11: Trends have recent timestamps (written by agent, not stale) ─
    try:
        now = time.time()
        recent_trends = [t for t in trends_list if now - t.get("timestamp", 0) < 3600]
        passed = len(recent_trends) >= 3
        add_check(
            "trends_have_recent_timestamps",
            passed,
            f"{len(recent_trends)} trend(s) have timestamps within the last hour (need >= 3)",
            weight=1.5
        )
    except Exception as e:
        add_check("trends_have_recent_timestamps", False, f"Error: {e}", weight=1.5)

    # ── Check 12: Highlights come from at least 2 distinct sources ───────────
    try:
        h_sources = set(
            h.get("source", "") for h in highlights_list
            if h.get("source") != "legacy-agent"
        )
        passed = len(h_sources) >= 2
        add_check(
            "highlights_from_multiple_sources",
            passed,
            f"Non-legacy highlight sources: {h_sources} (need >= 2 distinct)",
            weight=1.5
        )
    except Exception as e:
        add_check("highlights_from_multiple_sources", False, f"Error: {e}", weight=1.5)

    # ── Final scoring ─────────────────────────────────────────────────────────
    score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    passed_overall = score >= 0.75 and all(
        c["passed"] for c in checks if c["name"] in {
            "trends_file_valid_json",
            "highlights_file_valid_json",
            "minimum_three_trends_written",
            "minimum_two_highlights_written",
            "stale_legacy_highlights_cleaned_up",
        }
    )

    return {
        "passed": passed_overall,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))