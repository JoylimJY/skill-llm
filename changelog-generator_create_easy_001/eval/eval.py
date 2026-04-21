import sys
import os
import json
import re

def find_changelog_files(dir_path):
    candidates = []
    for fname in os.listdir(dir_path):
        if fname.lower().endswith('.md') and ('changelog' in fname.lower() or 'release' in fname.lower()):
            candidates.append(os.path.join(dir_path, fname))
    return candidates

def read_file(path):
    try:
        with open(path, encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return ''

def text_contains_any(text, keywords):
    text_lower = text.lower()
    return any(k.lower() in text_lower for k in keywords)

def categorize_commit_messages(text):
    # Try find the 3 sections: New Features, Improvements, Bug Fixes
    # Some tolerance to heading style and spacing
    categories = {'new features': [], 'improvements': [], 'bug fixes': []}

    # Pattern: headings followed by lists
    # We just split text by lines and assign lines under each heading
    lines = text.splitlines()
    current_cat = None

    for line in lines:
        # Check headings
        lline = line.lower().strip()
        if re.search(r'new features?', lline):
            current_cat = 'new features'
            continue
        elif re.search(r'improvements?', lline):
            current_cat = 'improvements'
            continue
        elif re.search(r'bug fixes?', lline):
            current_cat = 'bug fixes'
            continue

        # Add lines starting with bullet if in a category
        if current_cat and re.match(r'\s*[-*+•]\s+', line):
            # Clean bullet and trim
            item = re.sub(r'^\s*[-*+•]\s+', '', line).strip()
            if item:
                categories[current_cat].append(item)

    return categories

def score_check(name, passed, detail=''):
    return {"name": name, "passed": passed, "detail": detail}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [score_check("args", False, "Missing workspace directory argument.")]}))
        return

    workspace = sys.argv[1]
    changelog_files = find_changelog_files(workspace)

    if not changelog_files:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [score_check("changelog_file_found", False, "No changelog markdown files found.")]}))
        return

    best_score = 0.0
    best_report = None

    # Evaluate all candidate files and keep highest
    for changelog_path in changelog_files:
        content = read_file(changelog_path)

        checks = []

        # Check 1: file not empty
        checks.append(score_check("file_not_empty", len(content.strip()) > 0, "Changelog file should not be empty."))

        # Extract commits by categories
        cats = categorize_commit_messages(content)

        # Check 2: contains 'New Features' section with at least one item
        checks.append(score_check(
            "new_features_section",
            len(cats.get('new features', [])) >= 1,
            "No new features found in changelog."))

        # Check 3: contains 'Improvements' section with at least one item
        checks.append(score_check(
            "improvements_section",
            len(cats.get('improvements', [])) >= 1,
            "No improvements found in changelog."))

        # Check 4: contains 'Bug Fixes' section with at least one item
        checks.append(score_check(
            "bug_fixes_section",
            len(cats.get('bug fixes', [])) >= 1,
            "No bug fixes found in changelog."))

        # Check 5: No refactoring or test commits mentioned (exclude internal)
        # We assume user prompt said to exclude these
        forbidden_keywords = ['refactor', 'test']
        found_forbidden = any(text_contains_any(item, forbidden_keywords) for cat in cats.values() for item in cat)
        checks.append(score_check(
            "exclude_internal_commits",
            not found_forbidden,
            "Internal commits (refactor, test) should not be present."))

        # Check 6: Commits converted to user-friendly language (no raw commit tags like feat:, fix:)
        raw_tags = ['feat:', 'fix:', 'refactor:', 'test:', 'docs:', 'improvement:']
        raw_tag_found = any(text_contains_any(item, raw_tags) for cat in cats.values() for item in cat)
        checks.append(score_check(
            "user_friendly_language",
            not raw_tag_found,
            "Commit messages should be translated to user-friendly language without raw tags."))

        score = sum(1 for c in checks if c['passed']) / len(checks)
        passed = score >= 0.8

        result = {"passed": passed, "score": score, "checks": checks, "file": changelog_path}

        if score > best_score:
            best_score = score
            best_report = result

    if best_report is None:
        best_report = {"passed": False, "score": 0.0, "checks": [score_check("evaluation", False, "No changelog file passed evaluation.")]} 

    print(json.dumps(best_report))

if __name__ == '__main__':
    main()
