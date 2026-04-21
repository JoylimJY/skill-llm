import sys
import os
import json
import re

def case_insensitive_contains(haystack, needles):
    haystack = haystack.lower()
    return any(n.lower() in haystack for n in needles)

def main(workdir):
    result = {"passed": False, "score": 0.0, "checks": []}
    changelog_files = []

    # Find all markdown files (e.g., CHANGELOG.md)
    for f in os.listdir(workdir):
        if f.lower().endswith('.md'):
            changelog_files.append(os.path.join(workdir, f))
    
    if not changelog_files:
        result["checks"].append({"name": "changelog_file_found", "passed": False, "detail": "No markdown changelog file found in workspace."})
        print(json.dumps(result))
        return

    best_score = 0.0
    best_detail = []

    for changelog_path in changelog_files:
        with open(changelog_path, 'r', encoding='utf-8') as f:
            text = f.read()

        checks = []

        # Check 1: Filename is exactly CHANGELOG.md
        filename_passed = os.path.basename(changelog_path) == 'CHANGELOG.md'
        checks.append({
            "name": "correct_filename",
            "passed": filename_passed,
            "detail": f"Filename is {os.path.basename(changelog_path)}"
        })

        # Check 2: Content contains sections 'Features', 'Improvements', 'Fixes'
        # (Allow variations like ✨ New Features etc.) Check with keywords
        has_features = case_insensitive_contains(text, ["feature", "new features", "✨ new features"])
        has_improvements = case_insensitive_contains(text, ["improvement", "improvements", "🔧 improvements"])
        has_fixes = case_insensitive_contains(text, ["fix", "fixes", "🐛 fixes"])

        checks.append({"name": "has_features_section", "passed": has_features, "detail": "Features section detected." if has_features else "Features section missing."})
        checks.append({"name": "has_improvements_section", "passed": has_improvements, "detail": "Improvements section detected." if has_improvements else "Improvements section missing."})
        checks.append({"name": "has_fixes_section", "passed": has_fixes, "detail": "Fixes section detected." if has_fixes else "Fixes section missing."})

        # Check 3: No mention of docs, test, refactor commits included
        # So changelog should NOT contain these keywords
        excludes = ["docs", "refactor", "test"]
        excludes_present = any(case_insensitive_contains(text, [word]) for word in excludes)
        checks.append({"name": "no_internal_commits", "passed": not excludes_present, "detail": "No internal commits (docs/test/refactor) included." if not excludes_present else "Internal commits found in changelog."})

        # Check 4: Commit messages have been transformed user-friendly language
        # For example, 'feat: Add user profile customization option' -> something like 'Add user profile customization option'
        # Check for some expected phrases from input commits
        expected_features = ["user profile customization", "dark mode"]
        expected_improvements = ["speed up sync"]
        expected_fixes = ["crash when uploading large files", "timezone display"]

        features_found = all(case_insensitive_contains(text, [feat]) for feat in expected_features)
        improvements_found = all(case_insensitive_contains(text, [imp]) for imp in expected_improvements)
        fixes_found = all(case_insensitive_contains(text, [fix]) for fix in expected_fixes)

        checks.append({"name": "features_described", "passed": features_found, "detail": "All expected feature descriptions found." if features_found else "Expected feature descriptions missing."})
        checks.append({"name": "improvements_described", "passed": improvements_found, "detail": "All expected improvement descriptions found." if improvements_found else "Expected improvement descriptions missing."})
        checks.append({"name": "fixes_described", "passed": fixes_found, "detail": "All expected fixes described." if fixes_found else "Expected fixes missing."})

        # Calculate score
        passed_count = sum(1 for c in checks if c["passed"])
        total_count = len(checks)
        score = passed_count / total_count

        if score > best_score:
            best_score = score
            best_detail = checks

    result["passed"] = best_score == 1.0
    result["score"] = best_score
    result["checks"] = best_detail

    print(json.dumps(result))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Expected workspace directory as argument."}]}))
        sys.exit(1)
    main(sys.argv[1])
