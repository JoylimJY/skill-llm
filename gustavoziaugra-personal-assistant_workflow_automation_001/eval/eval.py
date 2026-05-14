import sys
import json
import os
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    total_score = 0.0

    # -----------------------------------------------------------------------
    # CHECK 1: Does austin_briefing.json exist somewhere in the workspace?
    # -----------------------------------------------------------------------
    target_files = list(Path(workspace).rglob("austin_briefing.json"))
    file_found = len(target_files) > 0
    checks.append({
        "name": "austin_briefing.json exists",
        "passed": file_found,
        "detail": f"Found at: {target_files[0]}" if file_found else "File not found anywhere in workspace."
    })

    if not file_found:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    target_file = target_files[0]

    # -----------------------------------------------------------------------
    # CHECK 2: File is valid JSON
    # -----------------------------------------------------------------------
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        checks.append({"name": "Valid JSON", "passed": True, "detail": "Parsed successfully."})
    except Exception as e:
        checks.append({"name": "Valid JSON", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.1, "checks": checks}

    # -----------------------------------------------------------------------
    # CHECK 3: Top-level fields present: generated_at, location, date, weekday, sections
    # -----------------------------------------------------------------------
    required_top = {"generated_at", "location", "date", "weekday", "sections"}
    missing_top = required_top - set(data.keys())
    top_fields_ok = len(missing_top) == 0
    checks.append({
        "name": "Top-level fields (generated_at, location, date, weekday, sections)",
        "passed": top_fields_ok,
        "detail": f"Missing: {missing_top}" if not top_fields_ok else "All present."
    })

    # -----------------------------------------------------------------------
    # CHECK 4: location field equals "Austin"
    # -----------------------------------------------------------------------
    location_ok = data.get("location", "").strip() == "Austin"
    checks.append({
        "name": "location == 'Austin'",
        "passed": location_ok,
        "detail": f"Got: {data.get('location', 'MISSING')}"
    })

    # -----------------------------------------------------------------------
    # CHECK 5: sections is a list of exactly 6 items
    # -----------------------------------------------------------------------
    sections = data.get("sections", [])
    sections_count_ok = isinstance(sections, list) and len(sections) == 6
    checks.append({
        "name": "sections has exactly 6 items",
        "passed": sections_count_ok,
        "detail": f"Got {len(sections)} section(s)." if isinstance(sections, list) else "sections is not a list."
    })

    # -----------------------------------------------------------------------
    # CHECK 6: Section types in correct order
    # -----------------------------------------------------------------------
    expected_types = ["motivation", "weather", "priorities", "habits", "selfcare", "reflection"]
    if isinstance(sections, list) and len(sections) == 6:
        actual_types = [s.get("type", "") for s in sections]
        types_ok = actual_types == expected_types
        checks.append({
            "name": "Section types in correct order",
            "passed": types_ok,
            "detail": f"Expected: {expected_types}\nGot: {actual_types}"
        })
    else:
        checks.append({
            "name": "Section types in correct order",
            "passed": False,
            "detail": "Cannot check - wrong number of sections."
        })
        types_ok = False

    # -----------------------------------------------------------------------
    # CHECK 7: Each section has title, content, type fields
    # -----------------------------------------------------------------------
    section_fields_ok = True
    section_fields_detail = []
    for i, section in enumerate(sections):
        for field in ["title", "content", "type"]:
            if field not in section:
                section_fields_ok = False
                section_fields_detail.append(f"Section {i} missing '{field}'")
    checks.append({
        "name": "Each section has title, content, type",
        "passed": section_fields_ok,
        "detail": "; ".join(section_fields_detail) if section_fields_detail else "All sections have required fields."
    })

    # -----------------------------------------------------------------------
    # CHECK 8: Weather section content contains "Austin"
    # -----------------------------------------------------------------------
    weather_ok = False
    weather_detail = "Weather section not found."
    for s in sections:
        if s.get("type") == "weather":
            content = s.get("content", "")
            weather_ok = "Austin" in content
            weather_detail = f"Weather content: {content[:120]}"
            break
    checks.append({
        "name": "Weather section content references 'Austin'",
        "passed": weather_ok,
        "detail": weather_detail
    })

    # -----------------------------------------------------------------------
    # CHECK 9: generated_at is a valid ISO format timestamp string (UTC)
    # -----------------------------------------------------------------------
    from datetime import datetime
    gen_at = data.get("generated_at", "")
    gen_at_ok = False
    gen_at_detail = f"Value: {gen_at}"
    try:
        # Accept both +00:00 and Z suffixed ISO strings
        parsed = datetime.fromisoformat(gen_at.replace("Z", "+00:00"))
        gen_at_ok = True
        gen_at_detail = f"Parsed: {parsed.isoformat()}"
    except Exception as e:
        gen_at_detail = f"Could not parse '{gen_at}': {e}"
    checks.append({
        "name": "generated_at is valid ISO timestamp",
        "passed": gen_at_ok,
        "detail": gen_at_detail
    })

    # -----------------------------------------------------------------------
    # CHECK 10: date and weekday fields are non-empty strings
    # -----------------------------------------------------------------------
    date_ok = isinstance(data.get("date", ""), str) and len(data.get("date", "")) == 10
    weekday_ok = isinstance(data.get("weekday", ""), str) and len(data.get("weekday", "")) > 0
    date_weekday_ok = date_ok and weekday_ok
    checks.append({
        "name": "date (YYYY-MM-DD) and weekday fields are valid",
        "passed": date_weekday_ok,
        "detail": f"date={data.get('date','MISSING')}, weekday={data.get('weekday','MISSING')}"
    })

    # -----------------------------------------------------------------------
    # Scoring
    # -----------------------------------------------------------------------
    passed_checks = [c for c in checks if c["passed"]]
    score = round(len(passed_checks) / len(checks), 4)
    overall_passed = score >= 0.85  # Must pass at least 85%

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))