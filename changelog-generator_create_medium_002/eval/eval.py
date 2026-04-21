import sys
import os
import re
import json


def find_markdown_files(dir_path):
    md_files = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.lower().endswith('.md'):
                md_files.append(os.path.join(root, file))
    return md_files


def text_contains_any(text, keywords):
    text_lower = text.lower()
    return any(k.lower() in text_lower for k in keywords)


def check_changelog_sections(content):
    sections = {
        'new_features': ['new feature', 'features', '✨ new features'],
        'improvements': ['improvements', 'enhancements', '✨ improvements'],
        'bug_fixes': ['bug fix', 'fixes', '🐛 fixes', 'bugs'],
        'breaking_changes': ['breaking change', 'breaking changes', '🚨 breaking changes']
    }
    found = {k: False for k in sections}

    for key, kw_list in sections.items():
        for kw in kw_list:
            if kw.lower() in content.lower():
                found[key] = True
                break
    return found


def check_excluded_terms(content):
    # Commit types to exclude: tests, refactor, chore, docs
    exclude_terms = ['test', 'refactor', 'chore', 'docs', 'internal', 'maintenance']
    # We expect these NOT to appear as change categories or commit messages
    # But some docs may appear under a Docs section in changelog - user prompt excludes only tests, refactor, internal commits
    # So exclude tests, refactor, chore commits from changelog
    # We check changelog content does NOT talk about test or refactor commits as changes
    return any(term.lower() in content.lower() for term in exclude_terms)


def check_customer_friendly_language(content):
    # We expect that changelog avoids raw technical commit messages e.g. no commit hashes, no command syntax
    # and uses plain English, no git jargon.
    # So check no git commit hashes (hex SHA 7+ chars)
    # and no git commands like 'chore:' or 'refs '
    if re.search(r'\b[0-9a-f]{7,}\b', content, re.IGNORECASE):
        return False
    if re.search(r'\b(chore|refactor|test|docs):', content, re.IGNORECASE):
        return False
    # Also no raw git command lines like 'git commit' or similar
    if re.search(r'git\s+commit', content, re.IGNORECASE):
        return False
    return True


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "arg_check", "passed": False, "detail": "Missing directory arg"}]
        }))
        return

    workspace_dir = sys.argv[1]
    md_files = find_markdown_files(workspace_dir)

    if not md_files:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_existence", "passed": False, "detail": "No markdown files found"}]
        }))
        return

    # Evaluate all markdown files, keep best
    best_score = 0
    best_report = None

    for md_file in md_files:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        checks = []

        # Check 1: filename exact (matches CHANGELOG.md)
        fname_ok = os.path.basename(md_file).lower() == 'changelog.md'
        checks.append({"name": "filename_check", "passed": fname_ok, "detail": f"Filename is {os.path.basename(md_file)}"})

        # Check 2: Has categories New Features, Improvements, Bug Fixes, Breaking Changes
        sections_found = check_changelog_sections(content)
        for sec_name, found in sections_found.items():
            checks.append({"name": f"section_{sec_name}", "passed": found, "detail": f"Section '{sec_name}' found: {found}"})

        # Check 3: Excludes commits related to tests, refactor, chore (these terms should not appear)
        exclude_terms_present = check_excluded_terms(content)
        checks.append({"name": "excluded_terms_absent", "passed": not exclude_terms_present, "detail": "No excluded internal terms present" if not exclude_terms_present else "Found excluded internal terms"})

        # Check 4: Customer friendly language
        friendly = check_customer_friendly_language(content)
        checks.append({"name": "customer_friendly_language", "passed": friendly, "detail": "User-friendly language confirmed" if friendly else "Technical terms or raw commits present"})

        # Check 5: Mentions commits inside date range (detect key commit summaries known from gen_inputs)
        expected_markers = [
            "user profile customization",
            "crash on login",
            "dark mode",
            "typo in payment",
            "dashboard load time",
            "API endpoint",
        ]
        found_markers = [m for m in expected_markers if m.lower() in content.lower()]
        present = len(found_markers) >= 4  # At least 4 of 6 markers appear
        checks.append({"name": "include_expected_changes", "passed": present, "detail": f"Changes found: {found_markers}"})

        score = sum(1 for c in checks if c["passed"]) / len(checks)
        passed = (score >= 0.8)

        if score > best_score:
            best_score = score
            best_report = {
                "passed": passed,
                "score": score,
                "checks": checks
            }

    if best_report is None:
        best_report = {"passed": False, "score": 0.0, "checks": []}

    print(json.dumps(best_report))


if __name__ == "__main__":
    main()
