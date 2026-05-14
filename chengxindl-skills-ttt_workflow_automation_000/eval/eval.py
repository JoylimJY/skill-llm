import sys
import os
import json
import subprocess
import yaml
import re
from pathlib import Path

def find_skill_dir(base_path: str, skill_name_pattern: str) -> Path | None:
    """Find a skill directory matching the pattern under known locations."""
    # Check the canonical deepagents skills location
    deepagents_skills = Path(os.path.expanduser("~/.deepagents/agent/skills"))
    if deepagents_skills.exists():
        for d in deepagents_skills.iterdir():
            if d.is_dir() and "fhir" in d.name.lower():
                return d
    # Also check workspace
    workspace = Path(base_path)
    for d in workspace.rglob("SKILL.md"):
        if "fhir" in str(d.parent.name).lower() and "archive" not in str(d):
            return d.parent
    return None

def parse_frontmatter(content: str):
    if not content.startswith("---"):
        return None, content
    end = content.find("---", 3)
    if end == -1:
        return None, content
    fm_str = content[3:end].strip()
    try:
        fm = yaml.safe_load(fm_str)
        body = content[end+3:].strip()
        return fm, body
    except Exception as e:
        return None, content

def run_quick_validate(skill_path: str) -> tuple[bool, str]:
    """Run quick_validate.py and return (passed, output)."""
    try:
        result = subprocess.run(
            ["python3", "/workspace/scripts/quick_validate.py", skill_path],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output
    except Exception as e:
        return False, str(e)

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    # ── FIND THE SKILL ──────────────────────────────────────────────────────
    skill_dir = find_skill_dir(workspace, "fhir")
    
    check_skill_exists = {
        "name": "fhir skill directory exists",
        "passed": skill_dir is not None,
        "detail": f"Found at: {skill_dir}" if skill_dir else "No fhir-* skill directory found in ~/.deepagents/agent/skills/ or workspace"
    }
    checks.append(check_skill_exists)

    if skill_dir is None:
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    # ── CHECK 1: Name is hyphen-case ─────────────────────────────────────────
    HYPHEN_CASE_PATTERN = re.compile(r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$')
    dir_name = skill_dir.name
    name_is_hyphen_case = bool(HYPHEN_CASE_PATTERN.match(dir_name))
    checks.append({
        "name": "skill directory name is hyphen-case",
        "passed": name_is_hyphen_case,
        "detail": f"Directory name: {dir_name!r} — {'valid' if name_is_hyphen_case else 'INVALID: must be hyphen-case like fhir-transformer'}"
    })

    # ── CHECK 2: SKILL.md exists ─────────────────────────────────────────────
    skill_md_path = skill_dir / "SKILL.md"
    skill_md_exists = skill_md_path.is_file()
    checks.append({
        "name": "SKILL.md file exists",
        "passed": skill_md_exists,
        "detail": str(skill_md_path)
    })

    if not skill_md_exists:
        result = {"passed": False, "score": len([c for c in checks if c["passed"]]) / len(checks), "checks": checks}
        print(json.dumps(result))
        return

    # ── READ AND PARSE SKILL.MD ───────────────────────────────────────────────
    try:
        skill_md_content = skill_md_path.read_text()
        fm, body = parse_frontmatter(skill_md_content)
    except Exception as e:
        checks.append({"name": "SKILL.md is readable and parseable", "passed": False, "detail": str(e)})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    fm_ok = fm is not None and isinstance(fm, dict)
    checks.append({
        "name": "SKILL.md has valid YAML frontmatter",
        "passed": fm_ok,
        "detail": f"Frontmatter parsed: {fm}" if fm_ok else "Could not parse YAML frontmatter"
    })

    if not fm_ok:
        result = {"passed": False, "score": len([c for c in checks if c["passed"]]) / len(checks), "checks": checks}
        print(json.dumps(result))
        return

    # ── CHECK 3: Required fields present ─────────────────────────────────────
    has_name = "name" in fm
    has_description = "description" in fm
    checks.append({
        "name": "frontmatter has required 'name' field",
        "passed": has_name,
        "detail": f"name = {fm.get('name')!r}"
    })
    checks.append({
        "name": "frontmatter has required 'description' field",
        "passed": has_description,
        "detail": f"description length = {len(str(fm.get('description', '')))}"
    })

    # ── CHECK 4: No disallowed frontmatter fields ─────────────────────────────
    ALLOWED_FIELDS = {"name", "description", "license", "allowed-tools", "metadata"}
    disallowed = [f for f in fm if f not in ALLOWED_FIELDS]
    no_disallowed_fields = len(disallowed) == 0
    checks.append({
        "name": "no disallowed frontmatter fields (e.g., version, author)",
        "passed": no_disallowed_fields,
        "detail": f"Disallowed fields found: {disallowed}" if disallowed else "All frontmatter fields are allowed"
    })

    # ── CHECK 5: Description has no angle brackets ────────────────────────────
    desc = str(fm.get("description", ""))
    no_angle_brackets = "<" not in desc and ">" not in desc
    checks.append({
        "name": "description contains no angle brackets (< or >)",
        "passed": no_angle_brackets,
        "detail": f"Description: {desc[:100]}..." if len(desc) > 100 else f"Description: {desc}"
    })

    # ── CHECK 6: Description length within 1024 chars ────────────────────────
    desc_length_ok = len(desc) <= 1024
    checks.append({
        "name": "description is within 1024 character limit",
        "passed": desc_length_ok,
        "detail": f"Description length: {len(desc)} chars (limit: 1024)"
    })

    # ── CHECK 7: Name field matches directory name and is hyphen-case ─────────
    name_val = str(fm.get("name", ""))
    name_matches_dir = name_val == dir_name
    name_valid_format = bool(HYPHEN_CASE_PATTERN.match(name_val)) if name_val else False
    checks.append({
        "name": "SKILL.md 'name' field is hyphen-case and matches directory name",
        "passed": name_matches_dir and name_valid_format,
        "detail": f"name field={name_val!r}, dir={dir_name!r}, hyphen-case={name_valid_format}"
    })

    # ── CHECK 8: Name max 64 chars ────────────────────────────────────────────
    name_len_ok = len(name_val) <= 64
    checks.append({
        "name": "skill name is within 64 character limit",
        "passed": name_len_ok,
        "detail": f"Name length: {len(name_val)}"
    })

    # ── CHECK 9: SKILL.md body has substantive content ────────────────────────
    body_substantive = len(body.strip()) >= 100
    checks.append({
        "name": "SKILL.md body has substantive content (>=100 chars)",
        "passed": body_substantive,
        "detail": f"Body length: {len(body.strip())} chars"
    })

    # ── CHECK 10: Body contains fhir-related content ─────────────────────────
    body_relevant = any(kw in body.lower() for kw in ["fhir", "transform", "resource", "patient", "observation", "hl7"])
    checks.append({
        "name": "SKILL.md body contains FHIR-domain content",
        "passed": body_relevant,
        "detail": f"Body snippet: {body[:200]!r}"
    })

    # ── CHECK 11: No README.md in skill directory ─────────────────────────────
    readme_files = list(skill_dir.rglob("README.md")) + list(skill_dir.rglob("README.txt"))
    no_readme = len(readme_files) == 0
    checks.append({
        "name": "no README.md or auxiliary documentation files in skill",
        "passed": no_readme,
        "detail": f"Found forbidden files: {[str(f) for f in readme_files]}" if readme_files else "No README/auxiliary docs found"
    })

    # ── CHECK 12: Has a references/ directory with content ───────────────────
    references_dir = skill_dir / "references"
    has_references = references_dir.is_dir() and len(list(references_dir.iterdir())) > 0
    # Check no example_reference.md placeholder remains as the ONLY content
    ref_files = list(references_dir.glob("*.md")) if references_dir.is_dir() else []
    # Accept if there's at least one non-placeholder reference file OR the example was customized
    meaningful_refs = False
    if references_dir.is_dir():
        for rf in ref_files:
            content = rf.read_text()
            if len(content.strip()) > 50 and "TODO: Add reference material" not in content:
                meaningful_refs = True
                break
    checks.append({
        "name": "skill has a references/ directory with meaningful content",
        "passed": has_references and meaningful_refs,
        "detail": f"references/ exists: {references_dir.is_dir()}, files: {[f.name for f in ref_files]}, meaningful: {meaningful_refs}"
    })

    # ── CHECK 13: Description mentions FHIR domain ───────────────────────────
    desc_relevant = any(kw in desc.lower() for kw in ["fhir", "transform", "healthcare", "hl7", "resource"])
    checks.append({
        "name": "description mentions FHIR/healthcare domain context",
        "passed": desc_relevant,
        "detail": f"Description: {desc[:150]}"
    })

    # ── CHECK 14: Description mentions trigger phrases (when to use) ──────────
    desc_has_triggers = any(kw in desc.lower() for kw in ["use when", "when to use", "when the user", "trigger", "use this"]) or \
                        any(ch in desc for ch in ["(1)", "(2)", "1.", "2."])
    checks.append({
        "name": "description includes 'when to use' triggers",
        "passed": desc_has_triggers,
        "detail": f"Description: {desc[:200]}"
    })

    # ── CHECK 15: Validation script passes ───────────────────────────────────
    validate_passed, validate_output = run_quick_validate(str(skill_dir))
    checks.append({
        "name": "quick_validate.py passes successfully",
        "passed": validate_passed,
        "detail": f"Validator output: {validate_output.strip()}"
    })

    # ── CHECK 16: init_skill.py was used (inferred: skill was NOT copied from archive) ─
    # The archive/old-skills/broken-attempt has wrong format. If agent just copied it,
    # the disallowed fields check and angle brackets check would fail.
    # We verify indirectly: the skill must be in ~/.deepagents/agent/skills/ (canonical path)
    canonical_skills = Path(os.path.expanduser("~/.deepagents/agent/skills"))
    in_canonical_location = canonical_skills in skill_dir.parents or skill_dir.parent == canonical_skills
    checks.append({
        "name": "skill is in canonical ~/.deepagents/agent/skills/ location",
        "passed": in_canonical_location,
        "detail": f"Skill path: {skill_dir}"
    })

    # ── SCORE ──────────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total_count = len(checks)
    score = passed_count / total_count

    # Critical checks that must ALL pass for overall pass
    critical_checks = [
        "fhir skill directory exists",
        "SKILL.md file exists",
        "SKILL.md has valid YAML frontmatter",
        "no disallowed frontmatter fields (e.g., version, author)",
        "description contains no angle brackets (< or >)",
        "description is within 1024 character limit",
        "quick_validate.py passes successfully",
        "skill is in canonical ~/.deepagents/agent/skills/ location",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    overall_passed = critical_passed and score >= 0.75

    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()