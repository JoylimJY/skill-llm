#!/usr/bin/env python3
"""Evaluation script for the markdown-lint task."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

def run(cmd, cwd=None, capture=True):
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=capture, text=True
    )
    return result.returncode, result.stdout, result.stderr

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    ws = Path(workspace)

    checks = []

    # ------------------------------------------------------------------
    # CHECK 1: .markdownlint.json exists and has correct structure
    # ------------------------------------------------------------------
    mdlint_path = ws / ".markdownlint.json"
    mdlint_ok = False
    mdlint_detail = ""
    try:
        import json as _json
        with open(mdlint_path) as f:
            cfg = _json.load(f)

        required_disabled = ["MD013", "MD033", "MD035", "MD036", "MD041", "MD060"]
        wrong = []
        for rule in required_disabled:
            val = cfg.get(rule)
            if val is not False:
                wrong.append(f"{rule}={val!r} (expected false)")

        # MD024 must be {"siblings_only": true}, not just false
        md024 = cfg.get("MD024")
        if not (isinstance(md024, dict) and md024.get("siblings_only") is True):
            wrong.append(f"MD024={md024!r} (expected {{\"siblings_only\": true}})")

        # default must be true
        if cfg.get("default") is not True:
            wrong.append(f"default={cfg.get('default')!r} (expected true)")

        if wrong:
            mdlint_detail = "Incorrect values: " + "; ".join(wrong)
        else:
            mdlint_ok = True
            mdlint_detail = "All required rules correctly configured"
    except FileNotFoundError:
        mdlint_detail = ".markdownlint.json not found"
    except Exception as e:
        mdlint_detail = f"Error reading .markdownlint.json: {e}"

    checks.append({
        "name": "markdownlint_config_correct",
        "passed": mdlint_ok,
        "detail": mdlint_detail
    })

    # ------------------------------------------------------------------
    # CHECK 2: Horizontal rules removed from ALL md files (frontmatter preserved)
    # ------------------------------------------------------------------
    hr_ok = False
    hr_detail = ""
    try:
        md_files = [
            str(p) for p in ws.rglob("*.md")
            if "node_modules" not in str(p)
        ]
        rc, stdout, stderr = run(
            f"bash {ws}/scripts/check-horizontal-rules.sh " + " ".join(f'"{f}"' for f in md_files),
            cwd=str(ws)
        )
        if rc == 0:
            hr_ok = True
            hr_detail = "No horizontal rules found outside frontmatter"
        else:
            hr_detail = f"Horizontal rules still present:\n{stdout}\n{stderr}"
    except Exception as e:
        hr_detail = f"Error running HR check: {e}"

    checks.append({
        "name": "horizontal_rules_removed",
        "passed": hr_ok,
        "detail": hr_detail
    })

    # ------------------------------------------------------------------
    # CHECK 3: YAML frontmatter --- delimiters are PRESERVED
    # ------------------------------------------------------------------
    frontmatter_ok = True
    frontmatter_detail = ""
    frontmatter_issues = []
    try:
        files_with_frontmatter = [
            "docs/clinical/protocols/infusion_protocol.md",
            "docs/regulatory/submissions/510k_summary.md",
            "docs/engineering/architecture/system_overview.md",
            "docs/engineering/api/pump_api.md",
            "docs/onboarding/developer_setup.md",
        ]
        for rel in files_with_frontmatter:
            fpath = ws / rel
            if not fpath.exists():
                frontmatter_issues.append(f"{rel}: file missing")
                continue
            content = fpath.read_text()
            lines = content.splitlines()
            # Must start with ---
            if not lines or lines[0].strip() != "---":
                frontmatter_issues.append(f"{rel}: frontmatter opening '---' missing (line 1 is {lines[0]!r})")
                continue
            # Find closing ---
            closing_found = False
            for i, line in enumerate(lines[1:], start=1):
                if line.strip() == "---":
                    closing_found = True
                    break
            if not closing_found:
                frontmatter_issues.append(f"{rel}: frontmatter closing '---' missing")

        if frontmatter_issues:
            frontmatter_ok = False
            frontmatter_detail = "Frontmatter damage detected: " + "; ".join(frontmatter_issues)
        else:
            frontmatter_detail = "YAML frontmatter delimiters intact in all files"
    except Exception as e:
        frontmatter_ok = False
        frontmatter_detail = f"Error checking frontmatter: {e}"

    checks.append({
        "name": "yaml_frontmatter_preserved",
        "passed": frontmatter_ok,
        "detail": frontmatter_detail
    })

    # ------------------------------------------------------------------
    # CHECK 4: Fenced code blocks have language identifiers (MD040 fixed)
    # ------------------------------------------------------------------
    md040_ok = True
    md040_detail = ""
    md040_violations = []
    try:
        md_files_to_check = list(ws.rglob("docs/**/*.md"))
        for fpath in md_files_to_check:
            content = fpath.read_text()
            lines = content.splitlines()
            for i, line in enumerate(lines, start=1):
                # Match opening fence with NO language (``` or ~~~ alone on line)
                if re.match(r'^```\s*$', line) or re.match(r'^~~~\s*$', line):
                    md040_violations.append(f"{fpath.relative_to(ws)}:{i}: bare fence")

        if md040_violations:
            md040_ok = False
            md040_detail = f"Code blocks missing language identifiers ({len(md040_violations)} violations): " + \
                           "; ".join(md040_violations[:8])
        else:
            md040_detail = "All fenced code blocks have language identifiers"
    except Exception as e:
        md040_ok = False
        md040_detail = f"Error checking MD040: {e}"

    checks.append({
        "name": "code_blocks_have_language",
        "passed": md040_ok,
        "detail": md040_detail
    })

    # ------------------------------------------------------------------
    # CHECK 5: markdownlint-cli2 passes cleanly on all docs
    # ------------------------------------------------------------------
    lint_ok = False
    lint_detail = ""
    try:
        rc, stdout, stderr = run(
            'npx markdownlint-cli2 "docs/**/*.md"',
            cwd=str(ws)
        )
        combined = stdout + stderr
        if rc == 0:
            lint_ok = True
            lint_detail = "markdownlint-cli2 passes with zero violations"
        else:
            # Count violations
            violations = [l for l in combined.splitlines() if re.search(r'MD\d+', l)]
            lint_detail = f"markdownlint-cli2 found violations (rc={rc}):\n" + \
                          "\n".join(violations[:20])
    except Exception as e:
        lint_detail = f"Error running markdownlint-cli2: {e}"

    checks.append({
        "name": "markdownlint_passes_cleanly",
        "passed": lint_ok,
        "detail": lint_detail
    })

    # ------------------------------------------------------------------
    # CHECK 6: MD024 siblings_only — duplicate sibling headings OK, non-siblings flagged
    # This verifies MD024 is not just disabled but set with siblings_only:true
    # We verify by checking the config value (already done in check 1)
    # Additionally verify by running lint on a test with sibling duplicates
    # ------------------------------------------------------------------
    md024_behavior_ok = False
    md024_behavior_detail = ""
    try:
        test_md = ws / "__test_md024.md"
        # This file has duplicate h3 under different h2 parents - should be OK with siblings_only
        test_md.write_text("""\
# Top

## Section A

### Details

Content here.

## Section B

### Details

Content here too.
""")
        rc, stdout, stderr = run(
            f'npx markdownlint-cli2 "__test_md024.md"',
            cwd=str(ws)
        )
        combined = stdout + stderr
        test_md.unlink()
        if rc == 0:
            md024_behavior_ok = True
            md024_behavior_detail = "MD024 siblings_only=true: duplicate headings under different parents allowed correctly"
        else:
            md024_violations = [l for l in combined.splitlines() if "MD024" in l]
            if md024_violations:
                md024_behavior_detail = f"MD024 wrongly flagged non-sibling duplicates: {md024_violations}"
            else:
                md024_behavior_detail = f"markdownlint failed for unexpected reason (rc={rc}): {combined[:300]}"
    except Exception as e:
        md024_behavior_detail = f"Error testing MD024 behavior: {e}"
        try:
            (ws / "__test_md024.md").unlink(missing_ok=True)
        except Exception:
            pass

    checks.append({
        "name": "md024_siblings_only_behavior",
        "passed": md024_behavior_ok,
        "detail": md024_behavior_detail
    })

    # ------------------------------------------------------------------
    # Final scoring
    # ------------------------------------------------------------------
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    all_passed = passed_count == total

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())