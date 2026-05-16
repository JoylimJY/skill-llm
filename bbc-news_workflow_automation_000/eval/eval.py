import json
import sys
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)

    # Find the regional_digest.json file
    matches = list(workspace.rglob("regional_digest.json"))
    
    if not matches:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "regional_digest.json not found anywhere in workspace"}]
        }

    digest_path = matches[0]
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {digest_path}"})

    # Load JSON
    try:
        with open(digest_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"Could not parse JSON: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "valid_json", "passed": True, "detail": "File is valid JSON"})

    # Required sections with exact slug keys used in the CLI
    required_sections = ["us-canada", "latin-america", "middle-east", "europe", "technology"]

    # Check top-level structure: must be a dict with a key containing the sections
    # Accept either: {"us-canada": [...], "latin-america": [...], ...}
    # or {"sections": {"us-canada": [...], ...}} or {"digest": {"sections": {"us-canada": [...]}}}
    # We'll look for the sections dict wherever it may be nested

    def find_sections_dict(obj, depth=0):
        """Recursively find a dict that contains at least some required section keys."""
        if depth > 4:
            return None
        if isinstance(obj, dict):
            matching = [k for k in required_sections if k in obj]
            if len(matching) >= 3:
                return obj
            for v in obj.values():
                result = find_sections_dict(v, depth + 1)
                if result:
                    return result
        return None

    sections_container = find_sections_dict(data)

    if sections_container is None:
        checks.append({
            "name": "sections_present",
            "passed": False,
            "detail": f"Could not find required section keys {required_sections} in JSON structure. Top-level keys: {list(data.keys()) if isinstance(data, dict) else type(data).__name__}"
        })
        return {"passed": False, "score": 1/5, "checks": checks}

    checks.append({"name": "sections_present", "passed": True, "detail": f"Found sections container with keys including required ones"})

    # Check each required section has stories with correct count (<= 3)
    section_checks_passed = 0
    for section in required_sections:
        section_data = sections_container.get(section)
        if section_data is None:
            checks.append({
                "name": f"section_{section}",
                "passed": False,
                "detail": f"Section '{section}' missing from JSON"
            })
            continue

        # section_data should be a list of stories or a dict with a stories list
        stories = None
        if isinstance(section_data, list):
            stories = section_data
        elif isinstance(section_data, dict):
            # Look for a list value
            for v in section_data.values():
                if isinstance(v, list):
                    stories = v
                    break

        if stories is None:
            checks.append({
                "name": f"section_{section}",
                "passed": False,
                "detail": f"Section '{section}' does not contain a list of stories"
            })
            continue

        # Check count: must be between 1 and 3 (limit 3)
        if len(stories) == 0:
            checks.append({
                "name": f"section_{section}",
                "passed": False,
                "detail": f"Section '{section}' has 0 stories"
            })
            continue

        if len(stories) > 3:
            checks.append({
                "name": f"section_{section}",
                "passed": False,
                "detail": f"Section '{section}' has {len(stories)} stories, expected at most 3 (--limit 3)"
            })
            continue

        # Check that each story has at least a title field
        has_titles = all(
            (isinstance(s, dict) and s.get("title", "").strip() != "")
            for s in stories
        )

        if not has_titles:
            checks.append({
                "name": f"section_{section}",
                "passed": False,
                "detail": f"Section '{section}' stories missing 'title' field or have empty titles"
            })
            continue

        checks.append({
            "name": f"section_{section}",
            "passed": True,
            "detail": f"Section '{section}' has {len(stories)} stories with titles (limit respected)"
        })
        section_checks_passed += 1

    # Also verify that "technology" section is present (non-world-region section test)
    # This is already in required_sections above.

    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    score = passed_checks / max(total_checks, 1)

    # Must pass ALL section checks + file/json checks to pass overall
    critical_passed = (
        any(c["name"] == "file_exists" and c["passed"] for c in checks) and
        any(c["name"] == "valid_json" and c["passed"] for c in checks) and
        any(c["name"] == "sections_present" and c["passed"] for c in checks) and
        section_checks_passed == len(required_sections)
    )

    return {
        "passed": critical_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))