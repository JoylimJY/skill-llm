import sys
import json
import os
import subprocess
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {str(e)}"}

def load_snippets_db(workspace):
    db_path = Path(workspace) / "snippets_db.json"
    if not db_path.exists():
        return None, f"snippets_db.json not found at {db_path}"
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"

def main():
    workspace = sys.argv[1]
    checks = []
    
    # Check 1: snippets_db.json exists and is valid JSON
    def check_db_exists():
        db, err = load_snippets_db(workspace)
        if db is None:
            return False, err
        if "snippets" not in db:
            return False, "DB missing 'snippets' key"
        return True, f"DB found with {len(db['snippets'])} snippet(s)"
    checks.append(run_check("snippets_db_exists_and_valid", check_db_exists))

    # Check 2: At least 4 snippets added
    def check_min_snippets():
        db, err = load_snippets_db(workspace)
        if db is None:
            return False, err
        count = len(db["snippets"])
        if count < 4:
            return False, f"Only {count} snippet(s) found, expected at least 4"
        return True, f"{count} snippets found"
    checks.append(run_check("at_least_4_snippets_added", check_min_snippets))

    # Check 3: Multiple languages present (Python must be one, at least 2 distinct langs)
    def check_multiple_languages():
        db, err = load_snippets_db(workspace)
        if db is None:
            return False, err
        langs = set(s.get("lang", "").lower() for s in db["snippets"] if s.get("lang"))
        if "python" not in langs:
            return False, f"No Python snippets found. Languages: {langs}"
        if len(langs) < 2:
            return False, f"Only 1 language found ({langs}), expected at least 2"
        return True, f"Languages present: {langs}"
    checks.append(run_check("multiple_languages_including_python", check_multiple_languages))

    # Check 4: Tags are used - at least 2 snippets have tags
    def check_tags_used():
        db, err = load_snippets_db(workspace)
        if db is None:
            return False, err
        tagged = [s for s in db["snippets"] if s.get("tags") and len(s["tags"]) > 0]
        if len(tagged) < 2:
            return False, f"Only {len(tagged)} snippet(s) have tags, expected at least 2"
        # Check at least 2 distinct tags exist across all snippets
        all_tags = set()
        for s in db["snippets"]:
            for t in s.get("tags", []):
                all_tags.add(t.lower())
        if len(all_tags) < 2:
            return False, f"Only {len(all_tags)} distinct tag(s), expected at least 2"
        return True, f"Tags used: {all_tags}"
    checks.append(run_check("tags_properly_used", check_tags_used))

    # Check 5: search command works and returns results for a Python-related keyword
    def check_search_works():
        db, err = load_snippets_db(workspace)
        if db is None:
            return False, err
        # Find a keyword that should match something
        python_snippets = [s for s in db["snippets"] if s.get("lang", "").lower() == "python"]
        if not python_snippets:
            return False, "No python snippets to search for"
        # Use a keyword from the first python snippet title
        keyword = python_snippets[0]["title"].split()[0]  # first word of title
        result = subprocess.run(
            ["python3", "scripts/snippet.py", "search", keyword],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return False, f"Search command failed: {result.stderr}"
        if "No snippets found" in result.stdout:
            return False, f"Search for '{keyword}' returned no results. stdout: {result.stdout[:200]}"
        return True, f"Search for '{keyword}' returned results: {result.stdout[:100]}"
    checks.append(run_check("search_command_functional", check_search_works))

    # Check 6: list --tag command works
    def check_list_by_tag():
        db, err = load_snippets_db(workspace)
        if db is None:
            return False, err
        # Find a tag that exists
        all_tags = []
        for s in db["snippets"]:
            all_tags.extend(s.get("tags", []))
        if not all_tags:
            return False, "No tags found in DB to test list --tag"
        test_tag = all_tags[0]
        result = subprocess.run(
            ["python3", "scripts/snippet.py", "list", "--tag", test_tag],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return False, f"List --tag command failed: {result.stderr}"
        if "No snippets found" in result.stdout:
            return False, f"list --tag {test_tag} returned no results but tag exists in DB"
        return True, f"list --tag {test_tag} returned: {result.stdout[:100]}"
    checks.append(run_check("list_by_tag_functional", check_list_by_tag))

    # Check 7: Snippets have meaningful code content (not empty, not placeholder)
    def check_meaningful_code():
        db, err = load_snippets_db(workspace)
        if db is None:
            return False, err
        issues = []
        for s in db["snippets"]:
            code = s.get("code", "").strip()
            if len(code) < 5:
                issues.append(f"Snippet [{s['id']}] '{s.get('title','')}' has suspiciously short code: '{code}'")
        if issues:
            return False, "; ".join(issues)
        return True, f"All {len(db['snippets'])} snippets have meaningful code content"
    checks.append(run_check("snippets_have_meaningful_code", check_meaningful_code))

    # Check 8: Correct script path was used (snippets.py should NOT have been used successfully)
    # We verify by checking that snippets_db.json was populated (which only scripts/snippet.py can do)
    def check_correct_script_used():
        db, err = load_snippets_db(workspace)
        if db is None:
            return False, err
        # If snippets were added successfully, scripts/snippet.py was used
        if len(db.get("snippets", [])) >= 4:
            return True, "snippets_db.json populated correctly via scripts/snippet.py"
        return False, "DB not properly populated - wrong script may have been used"
    checks.append(run_check("correct_script_path_used", check_correct_script_used))

    # Compute score
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total

    all_passed = all(c["passed"] for c in checks)

    output = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()