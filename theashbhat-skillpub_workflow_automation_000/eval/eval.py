#!/usr/bin/env python3
"""
Evaluation script for the csv-normalizer skill publishing task.
Usage: python3 eval.py <workspace_dir>
"""
import sys
import os
import json
import re
import subprocess
from pathlib import Path

WORKSPACE = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
REGISTRY_DIR = "/tmp/clawhub_registry"

checks = []

def check(name: str, passed: bool, detail: str):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: find the skill folder named 'csv-normalizer' anywhere under workspace
# ─────────────────────────────────────────────────────────────────────────────
def find_skill_folder():
    """Return the Path to a directory named exactly 'csv-normalizer'."""
    for p in Path(WORKSPACE).rglob("csv-normalizer"):
        if p.is_dir():
            return p
    return None


skill_dir = find_skill_folder()

# ── CHECK 1: Skill folder exists with correct name ───────────────────────────
if skill_dir is None:
    check("skill_folder_exists_with_correct_name",
          False,
          "No directory named 'csv-normalizer' found anywhere under workspace. "
          "Naming convention requires lowercase + hyphens only.")
else:
    check("skill_folder_exists_with_correct_name",
          True,
          f"Found skill folder at: {skill_dir}")

# ── CHECK 2: SKILL.md exists ─────────────────────────────────────────────────
skill_md_path = skill_dir / "SKILL.md" if skill_dir else None
skill_md_content = ""
try:
    if skill_md_path and skill_md_path.exists():
        skill_md_content = skill_md_path.read_text(encoding="utf-8")
        check("skill_md_exists", True, f"SKILL.md found at {skill_md_path}")
    else:
        check("skill_md_exists", False, "SKILL.md is missing from the skill folder.")
except Exception as e:
    check("skill_md_exists", False, f"Error reading SKILL.md: {e}")

# ── CHECK 3: Frontmatter has 'name' field ────────────────────────────────────
try:
    in_frontmatter = False
    has_name = False
    for line in skill_md_content.splitlines():
        if line.strip() == "---":
            in_frontmatter = not in_frontmatter
        if in_frontmatter and re.match(r'^name\s*:', line):
            has_name = True
            break
    check("frontmatter_has_name", has_name,
          "Found 'name:' in frontmatter." if has_name
          else "Frontmatter does not contain 'name:' field.")
except Exception as e:
    check("frontmatter_has_name", False, f"Parse error: {e}")

# ── CHECK 4: Frontmatter has non-placeholder 'description' ───────────────────
try:
    in_frontmatter = False
    has_description = False
    description_value = ""
    capture_next = False
    for line in skill_md_content.splitlines():
        stripped = line.strip()
        if stripped == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            if re.match(r'^description\s*:', line):
                has_description = True
                description_value = re.sub(r'^description\s*:\s*', '', line).strip()
                capture_next = True
                continue
            if capture_next:
                if stripped.startswith("|") or stripped == "":
                    description_value += " " + stripped
                elif re.match(r'^\w+\s*:', line):
                    break  # next key
                else:
                    description_value += " " + stripped

    is_placeholder = "DESCRIPTION_PLACEHOLDER" in description_value
    meaningful = has_description and not is_placeholder and len(description_value.strip()) > 10
    check("frontmatter_description_meaningful",
          meaningful,
          f"Description value: '{description_value[:120]}'" if meaningful
          else f"Description missing or still placeholder: '{description_value[:80]}'")
except Exception as e:
    check("frontmatter_description_meaningful", False, f"Parse error: {e}")

# ── CHECK 5: No forbidden files present ─────────────────────────────────────
FORBIDDEN = {"README.md", "CHANGELOG.md", "LICENCE", "LICENSE",
             "CONTRIBUTING.md", "TODO.md"}
try:
    if skill_dir:
        found_forbidden = []
        for fpath in skill_dir.rglob("*"):
            if fpath.name in FORBIDDEN:
                found_forbidden.append(fpath.name)
        passed = len(found_forbidden) == 0
        check("no_forbidden_files",
              passed,
              "No forbidden files found." if passed
              else f"Forbidden file(s) found: {found_forbidden}")
    else:
        check("no_forbidden_files", False, "Skill folder not found; cannot check.")
except Exception as e:
    check("no_forbidden_files", False, f"Error: {e}")

# ── CHECK 6: scripts/ subdirectory exists ───────────────────────────────────
try:
    if skill_dir and (skill_dir / "scripts").is_dir():
        check("scripts_dir_exists", True, "scripts/ directory present.")
    else:
        check("scripts_dir_exists", False,
              "scripts/ directory missing from skill folder (required by anatomy).")
except Exception as e:
    check("scripts_dir_exists", False, f"Error: {e}")

# ── CHECK 7: Validate script passes ─────────────────────────────────────────
base_dir = Path(WORKSPACE) / "skill-publisher"
validate_sh = base_dir / "scripts" / "validate.sh"
try:
    if skill_dir and validate_sh.exists():
        result = subprocess.run(
            ["bash", str(validate_sh), str(skill_dir)],
            capture_output=True, text=True, timeout=15
        )
        passed = result.returncode == 0
        detail = (result.stdout + result.stderr).strip()[:300]
        check("validate_passes", passed,
              f"validate.sh exit={result.returncode}: {detail}")
    else:
        check("validate_passes", False,
              "Cannot run validate.sh: skill folder or script missing.")
except Exception as e:
    check("validate_passes", False, f"Error running validate.sh: {e}")

# ── CHECK 8: Security scan passes ───────────────────────────────────────────
security_sh = base_dir / "scripts" / "security-scan.sh"
try:
    if skill_dir and security_sh.exists():
        result = subprocess.run(
            ["bash", str(security_sh), str(skill_dir)],
            capture_output=True, text=True, timeout=15
        )
        passed = result.returncode == 0
        detail = (result.stdout + result.stderr).strip()[:300]
        check("security_scan_passes", passed,
              f"security-scan.sh exit={result.returncode}: {detail}")
    else:
        check("security_scan_passes", False,
              "Cannot run security-scan.sh: skill folder or script missing.")
except Exception as e:
    check("security_scan_passes", False, f"Error running security-scan.sh: {e}")

# ── CHECK 9: Published to mock ClawHub registry at csv-normalizer@1.0.0 ──────
EXPECTED_SLUG = "csv-normalizer"
EXPECTED_VERSION = "1.0.0"
registry_file = Path(REGISTRY_DIR) / f"{EXPECTED_SLUG}@{EXPECTED_VERSION}"
try:
    if registry_file.exists():
        data = json.loads(registry_file.read_text())
        slug_ok = data.get("slug") == EXPECTED_SLUG
        version_ok = data.get("version") == EXPECTED_VERSION
        passed = slug_ok and version_ok
        check("published_to_clawhub",
              passed,
              f"Registry entry: {data}" if passed
              else f"Slug/version mismatch: {data}")
    else:
        # Also check for any entry with csv-normalizer slug (partial credit logic)
        alternatives = list(Path(REGISTRY_DIR).glob(f"{EXPECTED_SLUG}@*")) if Path(REGISTRY_DIR).exists() else []
        if alternatives:
            detail = f"Wrong version published. Found: {[a.name for a in alternatives]}. Expected: {EXPECTED_SLUG}@{EXPECTED_VERSION}"
        else:
            detail = f"No registry entry found for '{EXPECTED_SLUG}@{EXPECTED_VERSION}'. Was 'clawhub login' called and publish.sh executed with correct --slug and --version?"
        check("published_to_clawhub", False, detail)
except Exception as e:
    check("published_to_clawhub", False, f"Error reading registry: {e}")

# ── CHECK 10: Skill content references normalizer logic ─────────────────────
try:
    # The SKILL.md body (below frontmatter) should mention CSV normalization concepts
    body_keywords = ["csv", "normaliz", "transaction", "canonical", "schema"]
    body_text = skill_md_content.lower()
    found_kw = [kw for kw in body_keywords if kw in body_text]
    passed = len(found_kw) >= 2
    check("skill_content_references_domain",
          passed,
          f"Keywords found: {found_kw}" if passed
          else f"SKILL.md body appears generic or empty. Expected domain keywords about CSV/normalization. Found: {found_kw}")
except Exception as e:
    check("skill_content_references_domain", False, f"Error: {e}")

# ── SCORING ──────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
# Weighted: publish check is worth 2x
publish_passed = next((c["passed"] for c in checks if c["name"] == "published_to_clawhub"), False)
weighted_score = (passed_count + (1 if publish_passed else 0)) / (total + 1)

result = {
    "passed": all(c["passed"] for c in checks),
    "score": round(weighted_score, 3),
    "checks": checks
}
print(json.dumps(result, indent=2))