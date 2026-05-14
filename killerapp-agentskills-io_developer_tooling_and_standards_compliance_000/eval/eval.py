import sys
import os
import json
import re
import subprocess
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def find_skill_dir(workspace):
    """Find a directory named 'fraud-detection-workflow' anywhere under workspace."""
    for p in Path(workspace).rglob("fraud-detection-workflow"):
        if p.is_dir() and (p / "SKILL.md").exists():
            return p
    return None

def load_frontmatter(skill_md_path):
    """Parse YAML frontmatter from SKILL.md."""
    import yaml
    content = skill_md_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        raise ValueError("No frontmatter delimiter found")
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Frontmatter not properly closed")
    fm = yaml.safe_load(parts[1])
    body = parts[2]
    return fm, body

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    
    # ── CHECK 1: Correct directory name exists ────────────────────────────────
    def check_dir_name():
        skill_dir = find_skill_dir(workspace)
        if skill_dir is None:
            return False, "No directory named 'fraud-detection-workflow' with SKILL.md found"
        return True, f"Found skill directory at {skill_dir}"
    checks.append(run_check("correct_directory_name", check_dir_name))

    # Bail early if directory not found — all subsequent checks need it
    skill_dir = find_skill_dir(workspace)
    if skill_dir is None:
        checks.append({"name": "frontmatter_valid_name", "passed": False, "detail": "Skill dir not found"})
        checks.append({"name": "description_valid", "passed": False, "detail": "Skill dir not found"})
        checks.append({"name": "version_quoted", "passed": False, "detail": "Skill dir not found"})
        checks.append({"name": "no_forbidden_subdirs", "passed": False, "detail": "Skill dir not found"})
        checks.append({"name": "no_deep_references", "passed": False, "detail": "Skill dir not found"})
        checks.append({"name": "referenced_files_exist", "passed": False, "detail": "Skill dir not found"})
        checks.append({"name": "skills_ref_validates", "passed": False, "detail": "Skill dir not found"})
        score = 0.0
        result = {"passed": False, "score": score, "checks": checks}
        print(json.dumps(result))
        return

    skill_md_path = skill_dir / "SKILL.md"

    # ── CHECK 2: name field is valid (hyphens only, matches dir) ─────────────
    def check_name_field():
        fm, _ = load_frontmatter(skill_md_path)
        name = fm.get("name", "")
        pattern = r'^[a-z0-9]+(-[a-z0-9]+)*$'
        if not re.match(pattern, name):
            return False, f"name '{name}' does not match ^[a-z0-9]+(-[a-z0-9]+)*$"
        if name != "fraud-detection-workflow":
            return False, f"name is '{name}', expected 'fraud-detection-workflow'"
        if skill_dir.name != name:
            return False, f"Dir name '{skill_dir.name}' doesn't match name field '{name}'"
        return True, f"name='{name}' is valid and matches directory"
    checks.append(run_check("frontmatter_valid_name", check_name_field))

    # ── CHECK 3: description is valid (<= 1024 chars, has "Use when") ─────────
    def check_description():
        fm, _ = load_frontmatter(skill_md_path)
        desc = fm.get("description", "")
        if len(desc) > 1024:
            return False, f"description is {len(desc)} chars, must be <=1024"
        if "use when" not in desc.lower():
            return False, f"description missing 'Use when...' trigger phrase"
        return True, f"description valid ({len(desc)} chars, contains 'Use when')"
    checks.append(run_check("description_valid", check_description))

    # ── CHECK 4: version is quoted string in YAML ─────────────────────────────
    def check_version_quoted():
        import yaml
        content = skill_md_path.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        fm = yaml.safe_load(parts[1])
        metadata = fm.get("metadata", {})
        if metadata is None:
            return False, "No metadata block found"
        version = metadata.get("version")
        if version is None:
            return False, "No version field in metadata"
        if not isinstance(version, str):
            return False, f"version is type {type(version).__name__} (value: {version}), must be a quoted string"
        return True, f"version='{version}' is correctly a string"
    checks.append(run_check("version_quoted", check_version_quoted))

    # ── CHECK 5: No forbidden subdirectories (only scripts/, references/, assets/) ──
    def check_no_forbidden_subdirs():
        allowed = {"scripts", "references", "assets"}
        actual_dirs = {p.name for p in skill_dir.iterdir() if p.is_dir()}
        forbidden = actual_dirs - allowed
        if forbidden:
            return False, f"Forbidden subdirectories present: {forbidden}. Only scripts/, references/, assets/ allowed."
        return True, f"Subdirectories are valid: {actual_dirs}"
    checks.append(run_check("no_forbidden_subdirs", check_no_forbidden_subdirs))

    # ── CHECK 6: No deep (>1 level) file references ───────────────────────────
    def check_no_deep_references():
        content = skill_md_path.read_text(encoding="utf-8")
        # Find all references like (references/v2/foo.md) or (scripts/sub/bar.py)
        deep_refs = re.findall(r'(?:references|scripts|assets)/[^)\s"\']+/[^)\s"\']+', content)
        if deep_refs:
            return False, f"Deep references found (violates one-level rule): {deep_refs}"
        return True, "No deep file references found"
    checks.append(run_check("no_deep_references", check_no_deep_references))

    # ── CHECK 7: All referenced files in SKILL.md actually exist ──────────────
    def check_referenced_files_exist():
        content = skill_md_path.read_text(encoding="utf-8")
        refs = re.findall(r'(?:references|scripts|assets)/[^)\s"\']+', content)
        missing = []
        for ref in refs:
            ref_path = skill_dir / ref
            if not ref_path.exists():
                missing.append(ref)
        if missing:
            return False, f"Referenced files missing: {missing}"
        if not refs:
            return True, "No file references found (acceptable if removed)"
        return True, f"All {len(refs)} referenced files exist: {refs}"
    checks.append(run_check("referenced_files_exist", check_referenced_files_exist))

    # ── CHECK 8: skills-ref validate passes ──────────────────────────────────
    def check_skills_ref_validates():
        env = os.environ.copy()
        env["PATH"] = "/root/.cargo/bin:/root/.local/bin:" + env.get("PATH", "")
        result = subprocess.run(
            ["uvx", "--from",
             "git+https://github.com/agentskills/agentskills#subdirectory=skills-ref",
             "skills-ref", "validate", str(skill_dir)],
            capture_output=True, text=True, timeout=120, env=env
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        combined = (stdout + "\n" + stderr).strip()
        if result.returncode == 0:
            return True, f"skills-ref validate passed. Output: {combined[:500]}"
        else:
            return False, f"skills-ref validate FAILED (rc={result.returncode}). Output: {combined[:800]}"
    checks.append(run_check("skills_ref_validates", check_skills_ref_validates))

    # ── Scoring ───────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()