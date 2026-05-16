import sys
import os
import json
import zipfile
import subprocess
from pathlib import Path

def load_json_result(passed, score, checks):
    return {"passed": passed, "score": score, "checks": checks}

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    skill_dir = Path(workspace) / "projects" / "summarizer-skill"
    cli = "/opt/clawhub-publisher/dist/index.js"

    checks = []

    # ── Check 1: SKILL.md has 'description' in YAML frontmatter ──────────────
    try:
        skill_md_path = skill_dir / "SKILL.md"
        content = skill_md_path.read_text()
        import re
        # Extract YAML frontmatter
        fm_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if fm_match:
            import yaml
            fm = yaml.safe_load(fm_match.group(1))
            has_name = bool(fm.get("name", "").strip())
            has_desc = bool(fm.get("description", "").strip())
            checks.append({
                "name": "SKILL.md has 'name' in frontmatter",
                "passed": has_name,
                "detail": f"name='{fm.get('name', '')}'"
            })
            checks.append({
                "name": "SKILL.md has 'description' in frontmatter",
                "passed": has_desc,
                "detail": f"description='{fm.get('description', '')}'"
            })
        else:
            checks.append({"name": "SKILL.md has valid YAML frontmatter", "passed": False, "detail": "No frontmatter found"})
            checks.append({"name": "SKILL.md has 'description' in frontmatter", "passed": False, "detail": "No frontmatter"})
    except Exception as e:
        checks.append({"name": "SKILL.md readable", "passed": False, "detail": str(e)})
        checks.append({"name": "SKILL.md has 'description' in frontmatter", "passed": False, "detail": str(e)})

    # ── Check 2: hooks/invoke.js is not blank ─────────────────────────────────
    try:
        invoke_js = skill_dir / "hooks" / "invoke.js"
        content = invoke_js.read_text().strip()
        not_blank = len(content) > 0
        checks.append({
            "name": "hooks/invoke.js is not blank",
            "passed": not_blank,
            "detail": f"Content length: {len(content)} chars"
        })
    except Exception as e:
        checks.append({"name": "hooks/invoke.js is not blank", "passed": False, "detail": str(e)})

    # ── Check 3: Referenced hook file exists (error_handler.js or equivalent fix) ──
    try:
        skill_md_path = skill_dir / "SKILL.md"
        content = skill_md_path.read_text()
        fm_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        all_refs_resolved = True
        detail_parts = []
        if fm_match:
            import yaml
            fm = yaml.safe_load(fm_match.group(1))
            hooks = fm.get("hooks", {})
            if isinstance(hooks, dict):
                for hook_name, hook_path in hooks.items():
                    full = skill_dir / hook_path
                    exists = full.exists()
                    if not exists:
                        all_refs_resolved = False
                    detail_parts.append(f"{hook_name}:{hook_path}={'OK' if exists else 'MISSING'}")
        checks.append({
            "name": "All hook references in SKILL.md point to existing files",
            "passed": all_refs_resolved,
            "detail": "; ".join(detail_parts) if detail_parts else "No hooks found"
        })
    except Exception as e:
        checks.append({"name": "All hook references in SKILL.md point to existing files", "passed": False, "detail": str(e)})

    # ── Check 4: README exists ────────────────────────────────────────────────
    try:
        readme_candidates = list(skill_dir.glob("README*"))
        has_readme = len(readme_candidates) > 0
        checks.append({
            "name": "README file exists in skill folder",
            "passed": has_readme,
            "detail": f"Found: {[f.name for f in readme_candidates]}"
        })
    except Exception as e:
        checks.append({"name": "README file exists in skill folder", "passed": False, "detail": str(e)})

    # ── Check 5: validate command passes with no errors ───────────────────────
    try:
        result = subprocess.run(
            ["node", cli, "validate", str(skill_dir)],
            capture_output=True, text=True, timeout=30
        )
        combined = result.stdout + result.stderr
        # Look for failure indicators
        failed_indicators = ["error", "missing", "blank", "broken", "fail", "invalid"]
        has_failure = any(ind in combined.lower() for ind in failed_indicators)
        # If return code 0 and no failures, validation passed
        val_passed = (result.returncode == 0) and not has_failure
        checks.append({
            "name": "validate command exits successfully (no blockers)",
            "passed": val_passed,
            "detail": f"rc={result.returncode} stdout={result.stdout[:300]} stderr={result.stderr[:200]}"
        })
    except Exception as e:
        checks.append({"name": "validate command exits successfully (no blockers)", "passed": False, "detail": str(e)})

    # ── Check 6: prepare --zip was run → .clawhub-publisher/ exists ───────────
    try:
        publisher_dir = skill_dir / ".clawhub-publisher"
        exists = publisher_dir.exists() and publisher_dir.is_dir()
        checks.append({
            "name": ".clawhub-publisher/ output directory exists",
            "passed": exists,
            "detail": f"Path: {publisher_dir}"
        })
    except Exception as e:
        checks.append({"name": ".clawhub-publisher/ output directory exists", "passed": False, "detail": str(e)})

    # ── Check 7: zip archive was produced ────────────────────────────────────
    try:
        # zip could be in .clawhub-publisher/ or skill root
        zip_files = list(skill_dir.rglob("*.zip"))
        has_zip = len(zip_files) > 0
        valid_zip = False
        zip_detail = f"Found zips: {[str(z) for z in zip_files]}"
        if has_zip:
            for zp in zip_files:
                try:
                    with zipfile.ZipFile(zp, 'r') as zf:
                        names = zf.namelist()
                        # zip should contain at least SKILL.md
                        if any("SKILL.md" in n for n in names):
                            valid_zip = True
                            zip_detail = f"Valid zip at {zp}, contains: {names[:5]}"
                            break
                except Exception:
                    pass
        checks.append({
            "name": "A valid zip archive containing SKILL.md was produced",
            "passed": valid_zip,
            "detail": zip_detail
        })
    except Exception as e:
        checks.append({"name": "A valid zip archive containing SKILL.md was produced", "passed": False, "detail": str(e)})

    # ── Check 8: publish command was attempted with required flags ────────────
    # We check for evidence in shell history or a publish log, OR we try to run
    # publish --no-prompt --yes --slug ... and see it gets past the metadata validation step.
    # Since clawhub CLI login isn't available, we check that the command was formed correctly
    # by looking for a publish attempt log or running it ourselves to check flag parsing.
    try:
        # Run publish with --no-prompt --yes and required flags, expect it to fail only at
        # the clawhub CLI invocation step (not at metadata validation step)
        result = subprocess.run(
            [
                "node", cli, "publish", str(skill_dir),
                "--no-prompt",
                "--slug", "summarizer-skill",
                "--name", "Summarizer Skill",
                "--skill-version", "0.2.0",
                "--changelog", "Initial stable release of summarizer skill",
                "--tags", "latest",
                "--yes"
            ],
            capture_output=True, text=True, timeout=30
        )
        combined = result.stdout + result.stderr
        # It should fail at the `clawhub` step (not found / not logged in), NOT at validation
        # A successful metadata parse means it got past our proprietary flags
        metadata_ok = (
            "slug" in combined.lower() or
            "publish" in combined.lower() or
            "summarizer" in combined.lower() or
            "clawhub" in combined.lower() or
            result.returncode in (0, 1, 127)  # 127 = clawhub not found (expected)
        )
        # The key check: it must NOT fail due to missing --skill-version or missing flags
        not_flag_error = "unknown option" not in combined.lower() and "required" not in combined.lower()
        checks.append({
            "name": "publish command accepts all required proprietary flags without flag errors",
            "passed": metadata_ok and not_flag_error,
            "detail": f"rc={result.returncode} output={combined[:400]}"
        })
    except Exception as e:
        checks.append({
            "name": "publish command accepts all required proprietary flags without flag errors",
            "passed": False,
            "detail": str(e)
        })

    # ── Compute final score ───────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_checks / total, 3)

    # Must pass at minimum: description fixed, blank hook fixed, missing hook fixed,
    # readme added, validate passes, zip produced
    critical = [
        "SKILL.md has 'description' in frontmatter",
        "hooks/invoke.js is not blank",
        "All hook references in SKILL.md point to existing files",
        "README file exists in skill folder",
        "validate command exits successfully (no blockers)",
        "A valid zip archive containing SKILL.md was produced",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical
    )

    result_obj = {
        "passed": critical_passed and score >= 0.75,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result_obj, indent=2))

if __name__ == "__main__":
    main()