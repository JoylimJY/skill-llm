import sys
import os
import json
import re
from pathlib import Path

def evaluate(workspace: str) -> dict:
    checks = []

    # ── Helper ────────────────────────────────────────────────────────────────
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ── Locate the report file ────────────────────────────────────────────────
    report_path = None
    try:
        candidates = list(Path(workspace).rglob("skills_recommendation_report.md"))
        if candidates:
            report_path = candidates[0]
            add_check(
                "report_file_exists",
                True,
                f"Found report at: {report_path}"
            )
        else:
            add_check("report_file_exists", False, "skills_recommendation_report.md not found anywhere in workspace.")
            return {"passed": False, "score": 0.0, "checks": checks}
    except Exception as e:
        add_check("report_file_exists", False, f"Error searching for report: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Read report content ───────────────────────────────────────────────────
    try:
        content = report_path.read_text(encoding="utf-8")
        content_lower = content.lower()
    except Exception as e:
        add_check("report_readable", False, f"Could not read report: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}

    add_check("report_readable", True, f"Report length: {len(content)} characters.")

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 1: Development Intent → github (primary)
    # The developer colleague's profile requires Development intent handling.
    # Expected primary: github (Official, 52,300 downloads)
    # ══════════════════════════════════════════════════════════════════════════

    # 1a. 'github' slug appears
    github_slug = bool(re.search(r'\bgithub\b', content_lower))
    add_check(
        "dev_skill_github_mentioned",
        github_slug,
        "'github' slug found in report." if github_slug else "'github' slug NOT found — required for Development intent."
    )

    # 1b. Official Integration status mentioned for github
    official_near_github = False
    try:
        idx = content_lower.find("github")
        window = content_lower[max(0, idx - 200): idx + 500]
        official_near_github = "official" in window
    except Exception:
        pass
    add_check(
        "dev_github_official_status",
        official_near_github,
        "Official status mentioned in context of github recommendation." if official_near_github
        else "Official Integration status for github not found near its mention."
    )

    # 1c. Download count for github (52,300) present near github mention
    download_near_github = False
    try:
        idx = content_lower.find("github")
        window = content[max(0, idx - 200): idx + 600]
        download_near_github = bool(re.search(r'52[,.]?300', window))
    except Exception:
        pass
    add_check(
        "dev_github_download_count",
        download_near_github,
        "Download count 52,300 found near github section." if download_near_github
        else "Download count 52,300 for github not found — must read popular_skills.md."
    )

    # 1d. Install command for github: `clawhub install github`
    github_install = bool(re.search(r'clawhub\s+install\s+github', content, re.IGNORECASE))
    add_check(
        "dev_github_install_command",
        github_install,
        "Install command 'clawhub install github' found." if github_install
        else "Install command 'clawhub install github' NOT found — proprietary CLI format required."
    )

    # 1e. Link for github
    github_link = bool(re.search(
        r'https://github\.com/openclaw/clawhub/tree/main/skills/github',
        content
    ))
    add_check(
        "dev_github_link",
        github_link,
        "Correct ClawHub link for github found." if github_link
        else "ClawHub link for github not found or incorrect URL pattern used."
    )

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 2: Productivity Intent → byterover or automation-workflows
    # The PM colleague has scheduling/automation needs (NOT project-tracking).
    # Per recommendation_logic.md: scheduling signals → byterover or automation-workflows
    # NOT linear (which is for project tracking / issue management).
    # ══════════════════════════════════════════════════════════════════════════

    # 2a. byterover OR automation-workflows slug appears
    prod_skill_found = bool(re.search(r'\b(byterover|automation-workflows|automation_workflows)\b', content_lower))
    add_check(
        "prod_scheduling_skill_mentioned",
        prod_skill_found,
        "byterover or automation-workflows found — correct for scheduling intent." if prod_skill_found
        else "Neither byterover nor automation-workflows found — agent failed to apply sub-signal logic from recommendation_logic.md."
    )

    # 2b. The correct install command for the chosen productivity skill
    prod_install_found = bool(re.search(
        r'clawhub\s+install\s+(byterover|automation-workflows)',
        content, re.IGNORECASE
    ))
    add_check(
        "prod_skill_install_command",
        prod_install_found,
        "Install command for byterover or automation-workflows found." if prod_install_found
        else "Install command for scheduling productivity skill not found with correct 'clawhub install <slug>' format."
    )

    # 2c. Correct link for productivity skill
    prod_link_found = bool(re.search(
        r'https://github\.com/openclaw/clawhub/tree/main/skills/(byterover|automation-workflows)',
        content
    ))
    add_check(
        "prod_skill_link",
        prod_link_found,
        "Correct ClawHub link for productivity skill found." if prod_link_found
        else "ClawHub link for scheduling/productivity skill not found or incorrect."
    )

    # 2d. Download count for the chosen skill is present
    # byterover: 21,500  |  automation-workflows: 17,200
    prod_downloads_found = bool(re.search(r'(21[,.]?500|17[,.]?200)', content))
    add_check(
        "prod_skill_download_count",
        prod_downloads_found,
        "Download count for chosen productivity skill found (21,500 or 17,200)." if prod_downloads_found
        else "Download count for productivity skill not found — must read popular_skills.md."
    )

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 3: Anti-hallucination & Structure Checks
    # ══════════════════════════════════════════════════════════════════════════

    # 3a. Two separate recommendation blocks (multi-intent handling)
    # Look for at least 2 occurrences of "clawhub install" (one per intent block)
    install_commands = re.findall(r'clawhub\s+install\s+\S+', content, re.IGNORECASE)
    two_blocks = len(install_commands) >= 2
    add_check(
        "two_separate_recommendation_blocks",
        two_blocks,
        f"Found {len(install_commands)} install command(s) — need at least 2 for two intent blocks." 
    )

    # 3b. No same skill recommended twice
    slugs = [m.split()[-1].lower() for m in install_commands]
    no_duplicates = len(slugs) == len(set(slugs))
    add_check(
        "no_duplicate_skill_recommendations",
        no_duplicates,
        f"Slugs found: {slugs}. No duplicates." if no_duplicates
        else f"Duplicate skill slugs found: {slugs} — violates disqualification rules."
    )

    # 3c. linear is NOT the primary recommendation for the PM (scheduling context)
    #     linear is for project tracking, not scheduling — this is the key sub-signal trap
    linear_as_only_prod = False
    try:
        # If byterover/automation-workflows are absent AND linear is present → fail
        if not prod_skill_found and bool(re.search(r'\blinear\b', content_lower)):
            linear_as_only_prod = True
    except Exception:
        pass
    add_check(
        "no_linear_as_scheduling_recommendation",
        not linear_as_only_prod,
        "Did not incorrectly use linear for scheduling intent." if not linear_as_only_prod
        else "linear was used for scheduling intent — recommendation_logic.md sub-signal requires byterover/automation-workflows for scheduling."
    )

    # 3d. No hallucinated non-ClawHub slugs (e.g., 'zapier', 'trello', 'github-desktop')
    banned_hallucinations = ['zapier', 'trello', 'github-desktop', 'github desktop', 'notion', 'asana']
    hallucination_found = any(h in content_lower for h in banned_hallucinations)
    add_check(
        "no_hallucinated_external_tools",
        not hallucination_found,
        "No external tool hallucinations detected." if not hallucination_found
        else f"Hallucinated non-ClawHub tool found in report — agent used pre-training instead of reading references."
    )

    # 3e. "Why it fits" section exists for at least one recommendation
    why_fits = bool(re.search(r'why\s+it\s+fits', content_lower))
    add_check(
        "why_it_fits_section_present",
        why_fits,
        "'Why it fits' section found — matches required output schema." if why_fits
        else "'Why it fits' field missing — required by SKILL.md output format."
    )

    # ══════════════════════════════════════════════════════════════════════════
    # SCORING
    # ══════════════════════════════════════════════════════════════════════════
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = round(len(passed_checks) / total, 4)

    # Overall pass: must pass all critical checks
    critical_checks = [
        "report_file_exists",
        "dev_skill_github_mentioned",
        "dev_github_install_command",
        "dev_github_link",
        "prod_scheduling_skill_mentioned",
        "prod_skill_install_command",
        "two_separate_recommendation_blocks",
        "no_duplicate_skill_recommendations",
        "no_linear_as_scheduling_recommendation",
        "no_hallucinated_external_tools",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )

    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))