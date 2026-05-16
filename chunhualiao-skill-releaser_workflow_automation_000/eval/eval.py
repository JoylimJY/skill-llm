#!/usr/bin/env python3
"""
Evaluation script for the data-sync-agent release pipeline task.
Usage: python3 eval.py /workspace
"""

import sys
import json
import re
import subprocess
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
skill_dir = workspace / "skills" / "data-sync-agent"

checks = []
total_weight = 0
passed_weight = 0


def check(name: str, passed: bool, detail: str, weight: float = 1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global total_weight, passed_weight
    total_weight += weight
    if passed:
        passed_weight += weight


# ── Helper: find staging directory ───────────────────────────────────────────
def find_staging() -> Path | None:
    candidates = list(Path("/tmp").glob("skill-release-data-sync-agent*"))
    if candidates:
        return candidates[0]
    return None


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 1: skill.yml — display_name present and correctly formed
# ─────────────────────────────────────────────────────────────────────────────
try:
    import yaml
    skill_yml_path = skill_dir / "skill.yml"
    if skill_yml_path.exists():
        skill_yml = yaml.safe_load(skill_yml_path.read_text())
        dn = skill_yml.get("display_name", "")
        # Must be non-empty, title-case-ish, plain English, not equal to slug
        has_dn = bool(dn and len(dn.strip()) > 3)
        not_slug = dn.strip().lower() != "data-sync-agent"
        check(
            "skill.yml has display_name",
            has_dn,
            f"display_name='{dn}'" if dn else "display_name missing from skill.yml",
            weight=2.0,
        )
        check(
            "display_name is human-readable (not just the slug)",
            has_dn and not_slug,
            f"display_name='{dn}', slug='data-sync-agent'",
            weight=1.0,
        )
    else:
        check("skill.yml has display_name", False, "skill.yml not found", weight=2.0)
        check("display_name is human-readable", False, "skill.yml not found", weight=1.0)
except Exception as e:
    check("skill.yml has display_name", False, f"Exception: {e}", weight=2.0)
    check("display_name is human-readable", False, f"Exception: {e}", weight=1.0)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 2: Version bumped to minor (1.1.0) — new features were added
# The mock clawhub inspect returns 1.0.0 as the published version.
# SKILL.md describes new features (schema drift, conflict resolution, dry-run).
# Minor bump is required: 1.0.0 → 1.1.0
# ─────────────────────────────────────────────────────────────────────────────
try:
    skill_yml_path = skill_dir / "skill.yml"
    if skill_yml_path.exists():
        skill_yml = yaml.safe_load(skill_yml_path.read_text())
        version = skill_yml.get("version", "")
        # Should be 1.1.0 (minor bump for new features) — accept any bump > 1.0.0
        parts = str(version).split(".")
        bumped = len(parts) == 3 and (
            int(parts[0]) > 1 or
            (int(parts[0]) == 1 and int(parts[1]) >= 1)
        )
        is_minor = version == "1.1.0"
        check(
            "Version bumped beyond 1.0.0",
            bumped,
            f"version in skill.yml: '{version}' (previously published: 1.0.0)",
            weight=2.0,
        )
        check(
            "Version is correct minor bump (1.1.0)",
            is_minor,
            f"Expected 1.1.0 (minor bump for new features), got '{version}'",
            weight=1.0,
        )
    else:
        check("Version bumped beyond 1.0.0", False, "skill.yml not found", weight=2.0)
        check("Version is correct minor bump (1.1.0)", False, "skill.yml not found", weight=1.0)
except Exception as e:
    check("Version bumped beyond 1.0.0", False, f"Exception: {e}", weight=2.0)
    check("Version is correct minor bump (1.1.0)", False, f"Exception: {e}", weight=1.0)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 3: All required scaffold files exist in skill directory
# ─────────────────────────────────────────────────────────────────────────────
required_files = [
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
    ".gitignore",
    "tests/test-triggers.json",
]
for fname in required_files:
    fpath = skill_dir / fname
    exists = fpath.exists() and fpath.stat().st_size > 0
    check(
        f"Scaffold file exists: {fname}",
        exists,
        f"Path: {fpath}, exists={fpath.exists()}, size={fpath.stat().st_size if fpath.exists() else 'N/A'}",
        weight=1.0,
    )

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 4: validate-structure.sh scores 8/8
# ─────────────────────────────────────────────────────────────────────────────
try:
    result = subprocess.run(
        ["bash", str(workspace / "scripts/validate-structure.sh"), str(skill_dir)],
        capture_output=True, text=True, timeout=15
    )
    score_match = re.search(r"(\d+)/8", result.stdout)
    score_val = int(score_match.group(1)) if score_match else 0
    check(
        "validate-structure.sh scores 8/8",
        result.returncode == 0 and score_val == 8,
        f"stdout: {result.stdout.strip()[:300]}, rc={result.returncode}",
        weight=2.0,
    )
except Exception as e:
    check("validate-structure.sh scores 8/8", False, f"Exception: {e}", weight=2.0)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 5: test-triggers.json structure — shouldTrigger and shouldNotTrigger
# ─────────────────────────────────────────────────────────────────────────────
try:
    ttj_path = skill_dir / "tests/test-triggers.json"
    if ttj_path.exists():
        ttj = json.loads(ttj_path.read_text())
        has_trigger = isinstance(ttj.get("shouldTrigger"), list) and len(ttj["shouldTrigger"]) > 0
        has_not_trigger = isinstance(ttj.get("shouldNotTrigger"), list) and len(ttj["shouldNotTrigger"]) > 0
        # shouldTrigger must include at least one phrase from SKILL.md triggers
        trigger_phrases = ["sync", "pipeline", "data"]
        has_relevant = any(
            any(kw in t.lower() for kw in trigger_phrases)
            for t in ttj.get("shouldTrigger", [])
        )
        # shouldNotTrigger must include anti-patterns from SKILL.md
        antis = ["backup", "export", "report"]
        has_antis = any(
            any(a in t.lower() for a in antis)
            for t in ttj.get("shouldNotTrigger", [])
        )
        check(
            "test-triggers.json has shouldTrigger list",
            has_trigger and has_relevant,
            f"shouldTrigger: {ttj.get('shouldTrigger', [])}",
            weight=1.0,
        )
        check(
            "test-triggers.json has shouldNotTrigger with anti-patterns",
            has_not_trigger and has_antis,
            f"shouldNotTrigger: {ttj.get('shouldNotTrigger', [])}",
            weight=1.0,
        )
    else:
        check("test-triggers.json has shouldTrigger list", False, "File not found", weight=1.0)
        check("test-triggers.json has shouldNotTrigger with anti-patterns", False, "File not found", weight=1.0)
except Exception as e:
    check("test-triggers.json structure", False, f"Exception: {e}", weight=1.0)
    check("test-triggers.json anti-patterns", False, f"Exception: {e}", weight=1.0)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 6: CHANGELOG.md contains version entry
# ─────────────────────────────────────────────────────────────────────────────
try:
    cl_path = skill_dir / "CHANGELOG.md"
    if cl_path.exists():
        cl_text = cl_path.read_text()
        # Must have a version header — accept 1.1.0 or any bump
        has_version_header = bool(re.search(r"##\s*v?1\.[1-9]\d*\.\d+", cl_text))
        check(
            "CHANGELOG.md has new version entry",
            has_version_header,
            f"Content preview: {cl_text[:300]}",
            weight=1.0,
        )
    else:
        check("CHANGELOG.md has new version entry", False, "CHANGELOG.md not found", weight=1.0)
except Exception as e:
    check("CHANGELOG.md has new version entry", False, f"Exception: {e}", weight=1.0)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 7: Staging directory created at /tmp/skill-release-data-sync-agent
# and contains only skill files (not workspace root files)
# ─────────────────────────────────────────────────────────────────────────────
staging = find_staging()
check(
    "Staging directory created under /tmp/skill-release-data-sync-agent*",
    staging is not None and staging.is_dir(),
    f"Found: {staging}" if staging else "No staging dir found under /tmp/",
    weight=2.0,
)

if staging:
    # Must NOT contain workspace-level contamination
    banned = ["USER.md", "MEMORY.md", "AGENTS.md", "SOUL.md", ".gitmodules",
              "audits", "memory", "slides", "projects", "shared"]
    contaminants = [b for b in banned if (staging / b).exists()]
    check(
        "Staging dir has no workspace-level contamination",
        len(contaminants) == 0,
        f"Contaminants found: {contaminants}" if contaminants else "Clean",
        weight=2.0,
    )
    # Must contain expected skill files
    expected_in_staging = ["SKILL.md", "skill.yml", "README.md"]
    missing_in_staging = [f for f in expected_in_staging if not (staging / f).exists()]
    check(
        "Staging dir contains core skill files",
        len(missing_in_staging) == 0,
        f"Missing: {missing_in_staging}" if missing_in_staging else "All present",
        weight=1.0,
    )
else:
    check("Staging dir has no workspace-level contamination", False, "Staging dir not found", weight=2.0)
    check("Staging dir contains core skill files", False, "Staging dir not found", weight=1.0)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 8: validate-release-content.sh was run on staging dir (SAFE)
# ─────────────────────────────────────────────────────────────────────────────
if staging:
    try:
        result = subprocess.run(
            ["bash", str(workspace / "scripts/validate-release-content.sh"), str(staging)],
            capture_output=True, text=True, timeout=15
        )
        check(
            "validate-release-content.sh returns SAFE on staging dir",
            result.returncode == 0 and "SAFE" in result.stdout,
            f"stdout: {result.stdout.strip()[:200]}, rc={result.returncode}",
            weight=2.0,
        )
    except Exception as e:
        check("validate-release-content.sh returns SAFE on staging dir", False, f"Exception: {e}", weight=2.0)
else:
    check("validate-release-content.sh returns SAFE on staging dir", False, "Staging dir not found", weight=2.0)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 9: opsec-scan.sh was run and staging is CLEAN
# ─────────────────────────────────────────────────────────────────────────────
if staging:
    try:
        result = subprocess.run(
            ["bash", str(workspace / "scripts/opsec-scan.sh"), str(staging)],
            capture_output=True, text=True, timeout=15
        )
        check(
            "opsec-scan.sh returns CLEAN on staging dir",
            result.returncode == 0 and "CLEAN" in result.stdout,
            f"stdout: {result.stdout.strip()[:200]}, rc={result.returncode}",
            weight=2.0,
        )
    except Exception as e:
        check("opsec-scan.sh returns CLEAN on staging dir", False, f"Exception: {e}", weight=2.0)
else:
    check("opsec-scan.sh returns CLEAN on staging dir", False, "Staging dir not found", weight=2.0)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 10: gh repo create was called (staging push happened)
# ─────────────────────────────────────────────────────────────────────────────
try:
    gh_log = Path("/tmp/gh_calls.log").read_text() if Path("/tmp/gh_calls.log").exists() else ""
    called_create = "repo create" in gh_log and "data-sync-agent" in gh_log
    check(
        "gh repo create was called for data-sync-agent",
        called_create,
        f"gh log preview: {gh_log[:300]}",
        weight=1.5,
    )
    # Should be private
    called_private = "--private" in gh_log
    check(
        "gh repo create used --private flag",
        called_private,
        f"gh log preview: {gh_log[:300]}",
        weight=1.0,
    )
except Exception as e:
    check("gh repo create was called", False, f"Exception: {e}", weight=1.5)
    check("gh repo create used --private flag", False, f"Exception: {e}", weight=1.0)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 11: clawhub publish was called with correct parameters
# ─────────────────────────────────────────────────────────────────────────────
try:
    publish_record_path = Path("/tmp/clawhub_publish/last_publish.json")
    if publish_record_path.exists():
        pub = json.loads(publish_record_path.read_text())
        slug_ok = pub.get("slug") == "data-sync-agent"
        # display_name must be human-readable — at minimum not the slug itself
        name_val = pub.get("name", "")
        name_ok = bool(name_val) and name_val.lower() != "data-sync-agent"
        # Version must match bumped version in skill.yml
        version_val = pub.get("version", "")
        version_ok = bool(version_val) and version_val != "1.0.0"
        # Changelog must be non-empty
        changelog_ok = bool(pub.get("changelog", "").strip())

        check(
            "clawhub publish called with correct --slug",
            slug_ok,
            f"slug='{pub.get('slug')}'",
            weight=2.0,
        )
        check(
            "clawhub publish called with human-readable --name",
            name_ok,
            f"name='{name_val}'",
            weight=2.0,
        )
        check(
            "clawhub publish called with bumped --version",
            version_ok,
            f"version='{version_val}' (must differ from 1.0.0)",
            weight=1.5,
        )
        check(
            "clawhub publish called with non-empty --changelog",
            changelog_ok,
            f"changelog='{pub.get('changelog', '')[:100]}'",
            weight=1.0,
        )
    else:
        for name in [
            "clawhub publish called with correct --slug",
            "clawhub publish called with human-readable --name",
            "clawhub publish called with bumped --version",
            "clawhub publish called with non-empty --changelog",
        ]:
            check(name, False, "No clawhub publish record found at /tmp/clawhub_publish/last_publish.json", weight=2.0 if "slug" in name or "name" in name else 1.5)
except Exception as e:
    for name in ["slug", "name", "version", "changelog"]:
        check(f"clawhub publish --{name}", False, f"Exception: {e}", weight=1.5)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 12: Post-publish verify — clawhub inspect was called
# ─────────────────────────────────────────────────────────────────────────────
try:
    clawhub_log = Path("/tmp/clawhub_calls.log").read_text() if Path("/tmp/clawhub_calls.log").exists() else ""
    # inspect should be called both before (Step 1.5 version check) and after publish (Step 11.5)
    inspect_calls = [l for l in clawhub_log.splitlines() if "inspect" in l and "data-sync-agent" in l]
    check(
        "clawhub inspect called for post-publish verification",
        len(inspect_calls) >= 1,
        f"inspect calls found: {inspect_calls}",
        weight=1.5,
    )
except Exception as e:
    check("clawhub inspect called", False, f"Exception: {e}", weight=1.5)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 13: skill.yml triggers are more complete than original
# (Agent must sync triggers from SKILL.md frontmatter which has 5 triggers;
#  original skill.yml only had 3)
# ─────────────────────────────────────────────────────────────────────────────
try:
    skill_yml_path = skill_dir / "skill.yml"
    if skill_yml_path.exists():
        skill_yml = yaml.safe_load(skill_yml_path.read_text())
        triggers = skill_yml.get("triggers", [])
        # Original had 3; SKILL.md frontmatter has 5 (sync data, run data pipeline,
        # start sync, sync tables, push data to target)
        check(
            "skill.yml triggers updated to match SKILL.md (≥4 triggers)",
            len(triggers) >= 4,
            f"triggers count: {len(triggers)}, values: {triggers}",
            weight=1.0,
        )
    else:
        check("skill.yml triggers updated", False, "skill.yml not found", weight=1.0)
except Exception as e:
    check("skill.yml triggers updated", False, f"Exception: {e}", weight=1.0)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 14: README.md is non-trivial (not empty, not just a title)
# ─────────────────────────────────────────────────────────────────────────────
try:
    readme_path = skill_dir / "README.md"
    if readme_path.exists():
        readme_text = readme_path.read_text()
        # Must be >100 chars and contain install/usage info
        substantial = len(readme_text) > 100
        has_content = any(kw in readme_text.lower() for kw in ["install", "usage", "sync", "pipeline", "data"])
        check(
            "README.md is substantial and contains usage content",
            substantial and has_content,
            f"length={len(readme_text)}, has_content={has_content}",
            weight=1.0,
        )
    else:
        check("README.md is substantial", False, "README.md not found", weight=1.0)
except Exception as e:
    check("README.md is substantial", False, f"Exception: {e}", weight=1.0)

# ─────────────────────────────────────────────────────────────────────────────
# Compute final score
# ─────────────────────────────────────────────────────────────────────────────
score = passed_weight / total_weight if total_weight > 0 else 0.0
passed_count = sum(1 for c in checks if c["passed"])
total_count = len(checks)

result = {
    "passed": score >= 0.75,
    "score": round(score, 3),
    "checks": checks,
    "summary": f"{passed_count}/{total_count} checks passed, weighted score={score:.1%}",
}
print(json.dumps(result, indent=2))