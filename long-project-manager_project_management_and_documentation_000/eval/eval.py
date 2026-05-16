import sys
import json
import re
from pathlib import Path

def score(checks):
    passed = sum(1 for c in checks if c["passed"])
    return round(passed / len(checks), 4) if checks else 0.0

def find_project_dir(workspace: Path):
    """Find a project directory under projects/ with hyphen-case naming."""
    projects_root = workspace / "projects"
    if not projects_root.exists():
        return None
    candidates = [d for d in projects_root.iterdir() if d.is_dir()]
    # Must be hyphen-case: only lowercase letters, digits, hyphens
    valid = [d for d in candidates if re.match(r'^[a-z0-9][a-z0-9\-]*[a-z0-9]$', d.name) or re.match(r'^[a-z0-9]+$', d.name)]
    if valid:
        return valid[0]
    # Fall back to any directory
    return candidates[0] if candidates else None

def check_file_exists(proj_dir, filename):
    f = proj_dir / filename
    return f.exists() and f.is_file()

def read_file_safe(proj_dir, filename):
    try:
        return (proj_dir / filename).read_text(encoding="utf-8")
    except Exception:
        return ""

def is_not_just_template(content: str) -> bool:
    """Returns True if content appears to be filled in, not just a blank template."""
    # Should not have unfilled placeholders like <project-name>, <date>, <task>, <YYYY-MM-DD>
    # AND should have substantial content (>= 100 chars)
    if len(content.strip()) < 100:
        return False
    placeholder_patterns = [
        r'<project-name>', r'<date>', r'<task>', r'<YYYY-MM-DD>',
        r'<!-- One sentence', r'<!-- What must', r'<!-- What is in',
        r'<!-- How will we', r'<!-- Important files',
    ]
    leftover_placeholders = sum(1 for p in placeholder_patterns if re.search(p, content, re.IGNORECASE))
    # Allow up to 1 leftover placeholder (agent may leave some optional sections)
    return leftover_placeholders <= 2

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []

    # ── CHECK 1: projects/ directory exists
    projects_root = workspace / "projects"
    checks.append({
        "name": "projects/ root directory exists",
        "passed": projects_root.exists() and projects_root.is_dir(),
        "detail": f"Expected {projects_root} to exist as a directory."
    })

    # ── CHECK 2: Exactly one project folder with hyphen-case name
    proj_dir = find_project_dir(workspace)
    if proj_dir is None:
        checks.append({
            "name": "Project directory with hyphen-case name under projects/",
            "passed": False,
            "detail": "No project directory found under projects/."
        })
        # All subsequent checks fail
        for name in [
            "README.md exists and is filled",
            "STATUS.md exists and is filled",
            "TODO.md exists and is filled",
            "DECISIONS.md exists",
            "LOG.md exists",
            "REFERENCES.md exists",
            "HANDOFF.md exists",
            "STATUS.md contains 'Current Goal' section",
            "STATUS.md contains 'Current Judgment' section",
            "STATUS.md contains 'Next Action' section",
            "TODO.md contains actionable tasks (checked items)",
            "HANDOFF.md contains explicit 'Next Action'",
            "HANDOFF.md contains 'First File to Read'",
            "HANDOFF.md has non-template content",
            "README.md mentions PostgreSQL or database migration context",
            "Project not placed in wrong location (no projects/ ancestor)",
            "Template files were used (not invented from scratch)",
        ]:
            checks.append({"name": name, "passed": False, "detail": "Project directory not found."})
        result = {"passed": False, "score": score(checks), "checks": checks}
        print(json.dumps(result, indent=2))
        return

    is_hyphen_case = bool(re.match(r'^[a-z0-9][a-z0-9\-]*$', proj_dir.name))
    checks.append({
        "name": "Project directory with hyphen-case name under projects/",
        "passed": is_hyphen_case,
        "detail": f"Found project directory: '{proj_dir.name}'. Hyphen-case: {is_hyphen_case}."
    })

    # ── CHECK 3–5: Mandatory files exist and are filled
    for filename, label in [("README.md", "README.md"), ("STATUS.md", "STATUS.md"), ("TODO.md", "TODO.md")]:
        exists = check_file_exists(proj_dir, filename)
        content = read_file_safe(proj_dir, filename)
        filled = is_not_just_template(content) if exists else False
        checks.append({
            "name": f"{label} exists and is filled",
            "passed": exists and filled,
            "detail": f"Exists: {exists}. Content length: {len(content)}. Filled (not just template): {filled}."
        })

    # ── CHECK 6–8: Optional standard files exist
    for filename in ["DECISIONS.md", "LOG.md", "REFERENCES.md"]:
        exists = check_file_exists(proj_dir, filename)
        checks.append({
            "name": f"{filename} exists",
            "passed": exists,
            "detail": f"File {filename} {'found' if exists else 'NOT found'} in {proj_dir}."
        })

    # ── CHECK 9: HANDOFF.md exists
    handoff_exists = check_file_exists(proj_dir, "HANDOFF.md")
    checks.append({
        "name": "HANDOFF.md exists",
        "passed": handoff_exists,
        "detail": f"HANDOFF.md {'found' if handoff_exists else 'NOT found'} in {proj_dir}."
    })

    # ── CHECK 10: STATUS.md — four quality bar elements
    status_content = read_file_safe(proj_dir, "STATUS.md")

    has_current_goal = bool(re.search(r'current\s*goal', status_content, re.IGNORECASE))
    checks.append({
        "name": "STATUS.md contains 'Current Goal' section",
        "passed": has_current_goal,
        "detail": f"'Current Goal' found in STATUS.md: {has_current_goal}."
    })

    has_judgment = bool(re.search(r'(current\s*judg|judg.*true|assessment|analysis|belief)', status_content, re.IGNORECASE))
    checks.append({
        "name": "STATUS.md contains 'Current Judgment' section",
        "passed": has_judgment,
        "detail": f"'Current Judgment' or equivalent found: {has_judgment}."
    })

    has_next_action = bool(re.search(r'next\s*action', status_content, re.IGNORECASE))
    checks.append({
        "name": "STATUS.md contains 'Next Action' section",
        "passed": has_next_action,
        "detail": f"'Next Action' found in STATUS.md: {has_next_action}."
    })

    # ── CHECK 13: TODO.md has actual tasks
    todo_content = read_file_safe(proj_dir, "TODO.md")
    # Must have at least 2 actual task items (lines with real content after - [ ] or numbered)
    task_lines = [l for l in todo_content.splitlines()
                  if re.match(r'\s*[-*]\s+\[[ xX]\]', l) or re.match(r'\s*\d+\.', l)]
    real_tasks = [t for t in task_lines if not re.search(r'<task>', t, re.IGNORECASE)]
    checks.append({
        "name": "TODO.md contains actionable tasks (checked items)",
        "passed": len(real_tasks) >= 2,
        "detail": f"Found {len(real_tasks)} real task lines (need ≥2)."
    })

    # ── CHECK 14–16: HANDOFF.md quality (the proprietary pre-stop ritual)
    handoff_content = read_file_safe(proj_dir, "HANDOFF.md") if handoff_exists else ""

    has_handoff_next_action = bool(re.search(r'next\s*action', handoff_content, re.IGNORECASE))
    checks.append({
        "name": "HANDOFF.md contains explicit 'Next Action'",
        "passed": has_handoff_next_action and handoff_exists,
        "detail": f"'Next Action' in HANDOFF.md: {has_handoff_next_action}."
    })

    has_first_file = bool(re.search(r'first\s*file\s*(to\s*read)?', handoff_content, re.IGNORECASE))
    checks.append({
        "name": "HANDOFF.md contains 'First File to Read'",
        "passed": has_first_file and handoff_exists,
        "detail": f"'First File to Read' in HANDOFF.md: {has_first_file}."
    })

    handoff_filled = is_not_just_template(handoff_content) if handoff_exists else False
    checks.append({
        "name": "HANDOFF.md has non-template content",
        "passed": handoff_filled,
        "detail": f"HANDOFF.md length: {len(handoff_content)}. Non-template: {handoff_filled}."
    })

    # ── CHECK 17: README.md mentions domain context (PostgreSQL / DB migration)
    readme_content = read_file_safe(proj_dir, "README.md")
    domain_keywords = re.search(
        r'(postgres|postgresql|pg12|pg16|pg\s*12|pg\s*16|database|migration|zero.downtime|db\s*upgrade)',
        readme_content, re.IGNORECASE
    )
    checks.append({
        "name": "README.md mentions PostgreSQL or database migration context",
        "passed": bool(domain_keywords),
        "detail": f"Domain keyword found: {domain_keywords.group(0) if domain_keywords else 'None'}."
    })

    # ── CHECK 18: Project not placed in wrong location
    # Ensure it's not inside old-notes/ or infra/ or docs/
    proj_path_str = str(proj_dir)
    wrong_location = any(bad in proj_path_str for bad in ["old-notes", "infra", "docs", "scripts", "tests", "ci"])
    checks.append({
        "name": "Project correctly placed under projects/ (not in wrong location)",
        "passed": not wrong_location,
        "detail": f"Project path: {proj_dir}. Wrong location: {wrong_location}."
    })

    # ── CHECK 19: Template was used (at least some standard section headers match template)
    # The template defines specific sections; agent should have them
    template_sections = ["Current Goal", "Next Action", "Success Criteria", "Scope"]
    all_content = "\n".join([
        readme_content, status_content, todo_content, handoff_content
    ])
    found_sections = [s for s in template_sections if re.search(s, all_content, re.IGNORECASE)]
    template_used = len(found_sections) >= 3
    checks.append({
        "name": "Template structure used (≥3 standard section headers found across files)",
        "passed": template_used,
        "detail": f"Template section headers found: {found_sections} ({len(found_sections)}/4)."
    })

    # ── Final result
    all_passed = all(c["passed"] for c in checks)
    result = {
        "passed": all_passed,
        "score": score(checks),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()