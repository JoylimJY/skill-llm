import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Locate output file ───────────────────────────────────────────────────
    candidates = list(workspace.rglob("charter_itineraries.json"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found charter_itineraries.json at: {candidates[0]}" if file_found
                  else "charter_itineraries.json not found anywhere in workspace"
    })
    if not file_found:
        return {"passed": False, "score": 0.0, "checks": checks}

    output_path = candidates[0]

    # ── Parse JSON ───────────────────────────────────────────────────────────
    try:
        with open(output_path, "r") as f:
            data = json.load(f)
        checks.append({"name": "valid_json", "passed": True, "detail": "File is valid JSON"})
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Check three itineraries present ─────────────────────────────────────
    # Accept: list of 3 items, or dict with 3 keys, or dict with "itineraries" key
    itineraries = []
    if isinstance(data, list):
        itineraries = data
    elif isinstance(data, dict):
        # Could be {"itineraries": [...]} or {"REQ-001": ..., "REQ-002": ..., "REQ-003": ...}
        if "itineraries" in data and isinstance(data["itineraries"], list):
            itineraries = data["itineraries"]
        else:
            # Try to extract 3 top-level entries
            itineraries = list(data.values())

    has_three = len(itineraries) == 3
    checks.append({
        "name": "three_itineraries_present",
        "passed": has_three,
        "detail": f"Found {len(itineraries)} itinerary entries (expected 3)"
    })

    # Flatten all text for content checks
    full_text = json.dumps(data).lower()

    # ── BVI-specific anchorage content ───────────────────────────────────────
    bvi_locations = ["baths", "norman island", "jost van dyke", "anegada",
                     "tortola", "virgin gorda", "cooper island", "peter island",
                     "road town", "cane garden"]
    found_locations = [loc for loc in bvi_locations if loc in full_text]
    bvi_ok = len(found_locations) >= 3
    checks.append({
        "name": "bvi_specific_anchorages",
        "passed": bvi_ok,
        "detail": f"Found BVI locations: {found_locations} ({len(found_locations)}/3 minimum required)"
    })

    # ── Parameter mapping: beginner (REQ-001 "novice" → "beginner") ─────────
    beginner_ok = "beginner" in full_text
    checks.append({
        "name": "novice_mapped_to_beginner",
        "passed": beginner_ok,
        "detail": "'beginner' experience level present in output (REQ-001 'novice' must map to 'beginner')"
                  if beginner_ok else "Missing 'beginner' — 'novice' must be mapped to valid 'beginner' value"
    })

    # ── Parameter mapping: expert (REQ-002 "advanced" → "expert") ───────────
    expert_ok = "expert" in full_text
    checks.append({
        "name": "advanced_mapped_to_expert",
        "passed": expert_ok,
        "detail": "'expert' experience level present in output (REQ-002 'advanced' must map to 'expert')"
                  if expert_ok else "Missing 'expert' — 'advanced' must be mapped to valid 'expert' value"
    })

    # ── Parameter mapping: intermediate (REQ-003 "some experience" → "intermediate") ──
    intermediate_ok = "intermediate" in full_text
    checks.append({
        "name": "some_experience_mapped_to_intermediate",
        "passed": intermediate_ok,
        "detail": "'intermediate' present in output (REQ-003 'some experience' maps to 'intermediate')"
                  if intermediate_ok else "Missing 'intermediate' — 'some experience' must map to valid 'intermediate' value"
    })

    # ── Provisioning content (guest-count-scaled list) ───────────────────────
    provisioning_terms = ["provision", "food", "water", "supply", "grocery",
                          "meal", "drink", "sundowner", "ice", "snack"]
    found_prov = [t for t in provisioning_terms if t in full_text]
    provisioning_ok = len(found_prov) >= 2
    checks.append({
        "name": "provisioning_content_present",
        "passed": provisioning_ok,
        "detail": f"Provisioning-related content found: {found_prov}"
                  if provisioning_ok else "No provisioning content detected in output"
    })

    # ── Day-by-day itinerary structure ───────────────────────────────────────
    day_pattern = re.search(r'\bday\s*[123456789]', full_text)
    day_itinerary_ok = day_pattern is not None
    checks.append({
        "name": "day_by_day_itinerary",
        "passed": day_itinerary_ok,
        "detail": "Day-by-day itinerary content detected in output"
                  if day_itinerary_ok else "No day-by-day itinerary structure found (expected 'Day 1', 'Day 2', etc.)"
    })

    # ── Weather/trade winds content ───────────────────────────────────────────
    weather_terms = ["trade wind", "wind", "weather", "swell", "hurricane",
                     "knot", "sea state", "passage"]
    found_weather = [t for t in weather_terms if t in full_text]
    weather_ok = len(found_weather) >= 1
    checks.append({
        "name": "weather_routing_content",
        "passed": weather_ok,
        "detail": f"Weather/routing terms found: {found_weather}"
                  if weather_ok else "No weather or routing content detected"
    })

    # ── Guest counts preserved (4, 8, 2) ────────────────────────────────────
    counts_found = []
    for count in ["4", "8", "2"]:
        if count in full_text:
            counts_found.append(count)
    guest_counts_ok = len(counts_found) >= 2
    checks.append({
        "name": "guest_counts_reflected",
        "passed": guest_counts_ok,
        "detail": f"Guest counts found in output: {counts_found} (need at least 2 of [2, 4, 8])"
    })

    # ── Compute score ────────────────────────────────────────────────────────
    weights = {
        "output_file_exists": 0.05,
        "valid_json": 0.05,
        "three_itineraries_present": 0.15,
        "bvi_specific_anchorages": 0.15,
        "novice_mapped_to_beginner": 0.10,
        "advanced_mapped_to_expert": 0.10,
        "some_experience_mapped_to_intermediate": 0.10,
        "provisioning_content_present": 0.10,
        "day_by_day_itinerary": 0.10,
        "weather_routing_content": 0.05,
        "guest_counts_reflected": 0.05,
    }
    score = sum(weights.get(c["name"], 0.0) for c in checks if c["passed"])
    passed = score >= 0.75

    return {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))