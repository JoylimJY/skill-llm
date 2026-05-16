import sys
import json
import re
from pathlib import Path

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    REQUIRED_SECTION_TYPES = ["motivation", "weather", "priorities", "habits", "selfcare", "reflection"]
    REQUIRED_TOP_LEVEL_KEYS = {"generated_at", "location", "date", "weekday", "sections"}

    # ---- Helper ----
    def find_file(name_pattern):
        """Search workspace recursively for a file matching the name."""
        matches = list(workspace.rglob(name_pattern))
        return matches[0] if matches else None

    # ========== CHECK 1: tokyo_briefing.json exists and has correct structure ==========
    check_name = "tokyo_briefing.json exists"
    try:
        tokyo_file = find_file("tokyo_briefing.json")
        if tokyo_file is None:
            checks.append({"name": check_name, "passed": False, "detail": "File tokyo_briefing.json not found anywhere in workspace."})
        else:
            checks.append({"name": check_name, "passed": True, "detail": f"Found at {tokyo_file}"})
            total_score += 1
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ========== CHECK 2: tokyo_briefing.json - location field ==========
    check_name = "tokyo_briefing.json has location=Tokyo"
    try:
        tokyo_file = find_file("tokyo_briefing.json")
        if tokyo_file is None:
            checks.append({"name": check_name, "passed": False, "detail": "File not found."})
        else:
            data = json.loads(tokyo_file.read_text(encoding="utf-8"))
            loc = data.get("location", "")
            passed = loc == "Tokyo"
            checks.append({"name": check_name, "passed": passed, "detail": f"location={repr(loc)}"})
            if passed: total_score += 1
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ========== CHECK 3: tokyo_briefing.json - all required top-level keys ==========
    check_name = "tokyo_briefing.json has all required top-level keys"
    try:
        tokyo_file = find_file("tokyo_briefing.json")
        if tokyo_file is None:
            checks.append({"name": check_name, "passed": False, "detail": "File not found."})
        else:
            data = json.loads(tokyo_file.read_text(encoding="utf-8"))
            missing = REQUIRED_TOP_LEVEL_KEYS - set(data.keys())
            passed = len(missing) == 0
            checks.append({"name": check_name, "passed": passed, "detail": f"Missing keys: {missing}" if not passed else "All keys present."})
            if passed: total_score += 1
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ========== CHECK 4: tokyo_briefing.json - exactly 6 sections with correct types ==========
    check_name = "tokyo_briefing.json has all 6 required section types"
    try:
        tokyo_file = find_file("tokyo_briefing.json")
        if tokyo_file is None:
            checks.append({"name": check_name, "passed": False, "detail": "File not found."})
        else:
            data = json.loads(tokyo_file.read_text(encoding="utf-8"))
            sections = data.get("sections", [])
            found_types = [s.get("type") for s in sections]
            missing_types = [t for t in REQUIRED_SECTION_TYPES if t not in found_types]
            passed = len(missing_types) == 0 and len(sections) >= 6
            checks.append({
                "name": check_name, "passed": passed,
                "detail": f"Found types: {found_types}. Missing: {missing_types}"
            })
            if passed: total_score += 1.5
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ========== CHECK 5: tokyo_briefing.json - weather content references Tokyo ==========
    check_name = "tokyo_briefing.json weather section content references Tokyo"
    try:
        tokyo_file = find_file("tokyo_briefing.json")
        if tokyo_file is None:
            checks.append({"name": check_name, "passed": False, "detail": "File not found."})
        else:
            data = json.loads(tokyo_file.read_text(encoding="utf-8"))
            sections = data.get("sections", [])
            weather_sections = [s for s in sections if s.get("type") == "weather"]
            if not weather_sections:
                checks.append({"name": check_name, "passed": False, "detail": "No weather section found."})
            else:
                content = weather_sections[0].get("content", "")
                passed = "Tokyo" in content
                checks.append({"name": check_name, "passed": passed, "detail": f"Weather content: {repr(content[:120])}"})
                if passed: total_score += 1
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ========== CHECK 6: berlin_briefing.json exists ==========
    check_name = "berlin_briefing.json exists"
    try:
        berlin_file = find_file("berlin_briefing.json")
        if berlin_file is None:
            checks.append({"name": check_name, "passed": False, "detail": "File berlin_briefing.json not found anywhere in workspace."})
        else:
            checks.append({"name": check_name, "passed": True, "detail": f"Found at {berlin_file}"})
            total_score += 1
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ========== CHECK 7: berlin_briefing.json - location field ==========
    check_name = "berlin_briefing.json has location=Berlin"
    try:
        berlin_file = find_file("berlin_briefing.json")
        if berlin_file is None:
            checks.append({"name": check_name, "passed": False, "detail": "File not found."})
        else:
            data = json.loads(berlin_file.read_text(encoding="utf-8"))
            loc = data.get("location", "")
            passed = loc == "Berlin"
            checks.append({"name": check_name, "passed": passed, "detail": f"location={repr(loc)}"})
            if passed: total_score += 1
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ========== CHECK 8: berlin_briefing.json - all 6 section types ==========
    check_name = "berlin_briefing.json has all 6 required section types"
    try:
        berlin_file = find_file("berlin_briefing.json")
        if berlin_file is None:
            checks.append({"name": check_name, "passed": False, "detail": "File not found."})
        else:
            data = json.loads(berlin_file.read_text(encoding="utf-8"))
            sections = data.get("sections", [])
            found_types = [s.get("type") for s in sections]
            missing_types = [t for t in REQUIRED_SECTION_TYPES if t not in found_types]
            passed = len(missing_types) == 0 and len(sections) >= 6
            checks.append({
                "name": check_name, "passed": passed,
                "detail": f"Found types: {found_types}. Missing: {missing_types}"
            })
            if passed: total_score += 1.5
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ========== CHECK 9: berlin_digest.txt exists (human-readable summary) ==========
    check_name = "berlin_digest.txt exists (human-readable summary output)"
    try:
        digest_file = find_file("berlin_digest.txt")
        if digest_file is None:
            checks.append({"name": check_name, "passed": False, "detail": "File berlin_digest.txt not found anywhere in workspace."})
        else:
            checks.append({"name": check_name, "passed": True, "detail": f"Found at {digest_file}"})
            total_score += 1
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ========== CHECK 10: berlin_digest.txt contains the daily briefing header format ==========
    check_name = "berlin_digest.txt contains the formatted briefing header with date and weekday"
    try:
        digest_file = find_file("berlin_digest.txt")
        if digest_file is None:
            checks.append({"name": check_name, "passed": False, "detail": "File not found."})
        else:
            content = digest_file.read_text(encoding="utf-8")
            # The format_briefing function produces: "📋 Daily Briefing - YYYY-MM-DD (Weekday)"
            has_header = bool(re.search(r'Daily Briefing\s*-\s*\d{4}-\d{2}-\d{2}\s*\(\w+\)', content))
            passed = has_header
            checks.append({"name": check_name, "passed": passed, "detail": f"Header pattern found: {has_header}. First 200 chars: {repr(content[:200])}"})
            if passed: total_score += 1
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ========== CHECK 11: berlin_digest.txt contains all section titles ==========
    check_name = "berlin_digest.txt contains all 6 section titles (emoji headers)"
    try:
        digest_file = find_file("berlin_digest.txt")
        if digest_file is None:
            checks.append({"name": check_name, "passed": False, "detail": "File not found."})
        else:
            content = digest_file.read_text(encoding="utf-8")
            # Check for key title fragments from format_briefing output
            title_fragments = [
                "Good Morning",
                "Weather Check",
                "Today",  # "Today's Focus"
                "Daily Habits",
                "Self-Care",
                "Evening Review"
            ]
            missing = [f for f in title_fragments if f not in content]
            passed = len(missing) == 0
            checks.append({"name": check_name, "passed": passed, "detail": f"Missing title fragments: {missing}"})
            if passed: total_score += 1
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ========== CHECK 12: validation_report.json exists ==========
    check_name = "validation_report.json exists"
    try:
        report_file = find_file("validation_report.json")
        if report_file is None:
            checks.append({"name": check_name, "passed": False, "detail": "File validation_report.json not found anywhere in workspace."})
        else:
            checks.append({"name": check_name, "passed": True, "detail": f"Found at {report_file}"})
            total_score += 1
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ========== CHECK 13: validation_report.json references both locations ==========
    check_name = "validation_report.json references both Tokyo and Berlin"
    try:
        report_file = find_file("validation_report.json")
        if report_file is None:
            checks.append({"name": check_name, "passed": False, "detail": "File not found."})
        else:
            raw = report_file.read_text(encoding="utf-8")
            has_tokyo = "Tokyo" in raw
            has_berlin = "Berlin" in raw
            passed = has_tokyo and has_berlin
            checks.append({
                "name": check_name, "passed": passed,
                "detail": f"Contains Tokyo: {has_tokyo}, Contains Berlin: {has_berlin}"
            })
            if passed: total_score += 1
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ========== CHECK 14: validation_report.json is valid JSON with meaningful structure ==========
    check_name = "validation_report.json is valid JSON with at least 2 keys"
    try:
        report_file = find_file("validation_report.json")
        if report_file is None:
            checks.append({"name": check_name, "passed": False, "detail": "File not found."})
        else:
            data = json.loads(report_file.read_text(encoding="utf-8"))
            # Must be a dict or list with substantive content
            if isinstance(data, dict):
                passed = len(data.keys()) >= 2
                detail = f"Keys: {list(data.keys())}"
            elif isinstance(data, list):
                passed = len(data) >= 2
                detail = f"List with {len(data)} items"
            else:
                passed = False
                detail = f"Unexpected type: {type(data)}"
            checks.append({"name": check_name, "passed": passed, "detail": detail})
            if passed: total_score += 0.5
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ========== CHECK 15: validation_report.json confirms section count for both ==========
    check_name = "validation_report.json confirms 6 sections for each location briefing"
    try:
        report_file = find_file("validation_report.json")
        if report_file is None:
            checks.append({"name": check_name, "passed": False, "detail": "File not found."})
        else:
            raw = report_file.read_text(encoding="utf-8")
            # Look for the number 6 appearing in context (section count validation)
            has_six = "6" in raw
            # Also check that it seems to validate/confirm something about sections
            has_sections_ref = any(word in raw.lower() for word in ["section", "valid", "check", "pass", "ok", "complete"])
            passed = has_six and has_sections_ref
            checks.append({
                "name": check_name, "passed": passed,
                "detail": f"Contains '6': {has_six}, Contains validation language: {has_sections_ref}. Sample: {repr(raw[:300])}"
            })
            if passed: total_score += 0.5
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ---- Final scoring ----
    max_score = 14.0
    normalized_score = round(min(total_score / max_score, 1.0), 4)
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": normalized_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace_dir)