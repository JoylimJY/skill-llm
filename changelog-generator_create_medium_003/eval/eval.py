import sys
import os
import json
import re

def read_file_content(filepath):
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception:
        return ""

def case_insensitive_contains(text, keywords):
    text_lower = text.lower()
    return any(k.lower() in text_lower for k in keywords)

def check_section_presence(text, section_keywords):
    # Check if any of the section keywords exist to mark presence
    return case_insensitive_contains(text, section_keywords)

def score_category(text, category_keywords, min_items=1):
    # Count that category section exists and at least one bullet point
    # Flexible checks to prevent false negatives
    lower_text = text.lower()
    # Look for heading keywords
    if not any(k.lower() in lower_text for k in category_keywords):
        return False, 'Category heading missing'

    # Look for bullet points indicated by - or *
    bullets = re.findall(r'^[\s]*[-*]\s+', text, flags=re.MULTILINE)
    if len(bullets) < min_items:
        return False, f'Expected >= {min_items} bullet points, found {len(bullets)}'

    return True, 'Category present with adequate items'

def contains_excluded_terms(text, excluded_terms):
    # We want to check that excluded commits (tests, refactor, docs-only) do NOT appear
    lower_text = text.lower()
    return any(t.lower() in lower_text for t in excluded_terms)

def check_translation(text, markers):
    # ensure at least one commit translated from marker commits
    return case_insensitive_contains(text, markers)

def contains_filename(text, filename):
    # just sanity check that should not be in output
    return filename.lower() in text.lower()

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0, "checks": [{"name": "input", "passed": False, "detail": "Missing workspace path argument"}]}))
        return

    workspace = sys.argv[1]

    # find the changelog markdown file named exactly CHANGELOG.md
    candidates = [f for f in os.listdir(workspace) if f.lower() == 'changelog.md']

    checks = []

    if not candidates:
        checks.append({"name": "file_presence", "passed": False, "detail": "CHANGELOG.md not found in workspace root"})
        print(json.dumps({"passed": False, "score": 0, "checks": checks}))
        return

    # Evaluate best scoring file if multiple appear (should be only one, but be robust)
    best_score = 0
    best_checks = None

    for fname in candidates:
        path = os.path.join(workspace, fname)
        content = read_file_content(path)

        file_checks = []

        # Check 1: Required categories present
        categories = {
            "Features": ["feature", "✨ new features", "features"],
            "Improvements": ["improvement", "improved", "performance", "optimization"],
            "Bug Fixes": ["fix", "bug fix", "🐛 fixes", "bug"],
            "Breaking Changes": ["breaking change", "breaking"],
            "Security": ["security"]
        }
        for cat, keywords in categories.items():
            present, detail = score_category(content, keywords, min_items=1)
            file_checks.append({"name": f"category_{cat.lower().replace(' ','_')}", "passed": present, "detail": detail})

        # Check 2: No excluded commit types included (tests, refactor, docs)
        excluded_terms = ['test', 'tests', 'refactor', 'refactoring', 'docs', 'documentation']
        excluded_found = contains_excluded_terms(content, excluded_terms)
        file_checks.append({"name": "excluded_commits_filtered", "passed": not excluded_found, "detail": "Found excluded internal commits in changelog" if excluded_found else "Excluded commits correctly filtered out"})

        # Check 3: Translations of commit content to user-friendly text
        # We check that at least one user-friendly phrase appears
        translation_markers = ["users", "user-friendly", "customers", "release notes", "feature", "fix", "update", "improve"]
        translated = check_translation(content, translation_markers)
        file_checks.append({"name": "translation_to_user_language", "passed": translated, "detail": "No user-friendly language found" if not translated else "User-friendly language present"})

        # Check 4: Output file named exactly CHANGELOG.md
        correct_name = (fname == 'CHANGELOG.md')
        file_checks.append({"name": "filename_correct", "passed": correct_name, "detail": "Filename must be exactly CHANGELOG.md" if not correct_name else "Filename is correct"})

        # Aggregate
        passed_count = sum(1 for c in file_checks if c.get('passed') == True)
        score = passed_count / len(file_checks) if file_checks else 0

        if score > best_score:
            best_score = score
            best_checks = file_checks

    overall_passed = best_score == 1.0

    result = {"passed": overall_passed, "score": best_score, "checks": best_checks}
    print(json.dumps(result))

if __name__ == '__main__':
    main()
