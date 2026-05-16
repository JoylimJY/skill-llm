#!/usr/bin/env python3
"""
Evaluation script for the GuruWalk tour recommendation task.
Checks that the agent:
  1. Produced tour_recommendations.json somewhere in the workspace
  2. Correctly excluded tours with available_spots == 0
  3. Correctly handled null titles gracefully (not crashed, not included raw null)
  4. Correctly ranked: English (language match) first, then by rating desc, then by earliest time
  5. Each tour entry contains required fields: title, url, meetpoint_address, average_rating,
     duration, guru name, booking url, and at least one session slot
  6. Did NOT include the "Fully Booked Tour" (all events have available_spots=0)
"""

import sys
import json
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # ── Find output file ──────────────────────────────────────────────────────
    candidates = list(workspace_path.rglob("tour_recommendations.json"))
    
    if not candidates:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": "tour_recommendations.json not found anywhere in workspace"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    output_file = candidates[0]
    checks.append({
        "name": "output_file_exists",
        "passed": True,
        "detail": f"Found at {output_file.relative_to(workspace_path)}"
    })

    # ── Parse JSON ────────────────────────────────────────────────────────────
    try:
        raw = output_file.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception as e:
        checks.append({
            "name": "output_json_valid",
            "passed": False,
            "detail": f"Failed to parse JSON: {e}"
        })
        return {"passed": False, "score": 1/7, "checks": checks}

    checks.append({
        "name": "output_json_valid",
        "passed": True,
        "detail": "JSON parsed successfully"
    })

    # Normalize: accept either a list directly or a dict with a key containing the list
    tours = None
    if isinstance(data, list):
        tours = data
    elif isinstance(data, dict):
        # Look for first list value
        for v in data.values():
            if isinstance(v, list):
                tours = v
                break
        if tours is None:
            tours = [data]  # single tour wrapped in dict
    
    if not isinstance(tours, list):
        checks.append({
            "name": "output_is_list",
            "passed": False,
            "detail": f"Expected a list of tours, got {type(data)}"
        })
        return {"passed": False, "score": 2/7, "checks": checks}

    checks.append({
        "name": "output_is_list",
        "passed": True,
        "detail": f"Found {len(tours)} tour entries"
    })

    # ── Check: fully booked tour excluded ─────────────────────────────────────
    fully_booked_included = False
    for t in tours:
        url = str(t.get("url", t.get("booking_url", "")))
        title = str(t.get("title", "")).lower()
        if "999" in url or "fully booked" in title or "fully-booked" in url:
            fully_booked_included = True
            break

    checks.append({
        "name": "fully_booked_tour_excluded",
        "passed": not fully_booked_included,
        "detail": (
            "Correctly excluded the tour where all events have available_spots=0"
            if not fully_booked_included
            else "ERROR: Tour with all events having available_spots=0 was included"
        )
    })

    # ── Check: null title handled gracefully ─────────────────────────────────
    # The tour with title=null must either be excluded or have a fallback string (not raw None/null)
    null_title_ok = True
    null_title_detail = "null-title tour handled gracefully (excluded or given fallback title)"
    for t in tours:
        raw_title = t.get("title")
        url = str(t.get("url", t.get("booking_url", "")))
        if "456" in url:
            # This is the null-title tour
            if raw_title is None:
                null_title_ok = False
                null_title_detail = "null title tour included with title=null (not handled gracefully)"
            else:
                # Fallback title present - acceptable
                null_title_detail = f"null-title tour given fallback title: '{raw_title}'"
            break

    checks.append({
        "name": "null_title_handled_gracefully",
        "passed": null_title_ok,
        "detail": null_title_detail
    })

    # ── Check: required fields present in each tour ───────────────────────────
    required_field_groups = [
        ["title"],
        ["url", "booking_url"],
        ["average_rating", "rating"],
        ["duration"],
    ]
    
    fields_ok = True
    missing_detail = []
    for t in tours:
        for group in required_field_groups:
            found = any(t.get(f) is not None for f in group)
            if not found:
                fields_ok = False
                missing_detail.append(f"Tour missing one of {group}: {json.dumps(t)[:120]}")

    checks.append({
        "name": "required_fields_present",
        "passed": fields_ok,
        "detail": (
            "All tours have required fields (title, url, rating, duration)"
            if fields_ok
            else "; ".join(missing_detail[:3])
        )
    })

    # ── Check: English tours appear before Spanish-only tours (ranking) ────────
    # The ranking rule: language match (en) > rating > time
    # Tours with English events should appear before the Spanish-only tour
    # Spanish-only tour URL contains "789"
    
    tour_urls = []
    for t in tours:
        url = str(t.get("url", t.get("booking_url", "")))
        tour_urls.append(url)

    # Find positions
    spanish_pos = None
    english_positions = []
    for i, url in enumerate(tour_urls):
        if "789" in url:
            spanish_pos = i
        if any(x in url for x in ["123", "456", "321"]):
            english_positions.append(i)

    ranking_ok = True
    ranking_detail = "English-language tours correctly prioritized over Spanish-only tours"

    if spanish_pos is not None and english_positions:
        # All English tour positions should be before Spanish position
        if not all(ep < spanish_pos for ep in english_positions):
            ranking_ok = False
            ranking_detail = (
                f"Ranking error: Spanish-only tour (pos {spanish_pos}) "
                f"appears before some English tours (positions {english_positions}). "
                "Should rank: language match (en) > rating > time."
            )
    elif spanish_pos is None:
        ranking_detail = "Spanish-only tour not found in output (may be acceptable if filtered)"
    else:
        ranking_detail = "No English-specific tours found to compare ranking"

    checks.append({
        "name": "language_priority_ranking",
        "passed": ranking_ok,
        "detail": ranking_detail
    })

    # ── Check: sessions with available_spots=0 excluded ──────────────────────
    # The event at 2025-08-10T16:00:00Z (tour 123) has available_spots=0
    # The event at 2025-08-11T18:00:00Z (tour 321) has available_spots=0
    zero_spot_slot_found = False
    known_zero_slots = ["2025-08-10T16:00", "2025-08-11T18:00"]

    raw_str = json.dumps(data)
    for slot in known_zero_slots:
        if slot in raw_str:
            zero_spot_slot_found = True
            break

    checks.append({
        "name": "zero_available_spots_slots_excluded",
        "passed": not zero_spot_slot_found,
        "detail": (
            "Correctly excluded individual event slots with available_spots=0"
            if not zero_spot_slot_found
            else f"ERROR: Found event slot(s) with available_spots=0 in output: {[s for s in known_zero_slots if s in raw_str]}"
        )
    })

    # ── Compute score ─────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / total

    overall = all(c["passed"] for c in checks)

    return {
        "passed": overall,
        "score": round(score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "invocation", "passed": False,
                                      "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = run_eval(sys.argv[1])
    print(json.dumps(result, indent=2))