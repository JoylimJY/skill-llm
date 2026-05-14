import sys
import json
import subprocess
import os
from pathlib import Path

def run_eval(workspace):
    checks = []
    passed_all = True

    def add_check(name, passed, detail):
        nonlocal passed_all
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            passed_all = False

    # ── Check 1: validation_report.json exists ────────────────────────────
    report_candidates = list(Path(workspace).rglob("validation_report.json"))
    if not report_candidates:
        add_check("validation_report.json exists", False, "File 'validation_report.json' not found anywhere in workspace.")
        return {"passed": False, "score": 0.0, "checks": checks}

    # Prefer root-level report
    root_report = Path(workspace) / "validation_report.json"
    report_path = root_report if root_report.exists() else report_candidates[0]
    add_check("validation_report.json exists", True, f"Found at {report_path}")

    # ── Check 2: report is valid JSON ─────────────────────────────────────
    try:
        with open(report_path) as f:
            report = json.load(f)
        add_check("report is valid JSON", True, "Parsed successfully.")
    except Exception as e:
        add_check("report is valid JSON", False, f"JSON parse error: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Check 3: report is a list ─────────────────────────────────────────
    if not isinstance(report, list):
        add_check("report is a JSON array", False, f"Expected list, got {type(report).__name__}")
        return {"passed": False, "score": 0.0, "checks": checks}
    add_check("report is a JSON array", True, f"Contains {len(report)} entries.")

    # ── Check 4: report covers all .md files ──────────────────────────────
    all_md_files = list(Path(workspace).rglob("*.md"))
    reported_files = set()
    for entry in report:
        if isinstance(entry, dict) and "file" in entry:
            reported_files.add(str(Path(entry["file"]).resolve()))

    md_count = len(all_md_files)
    covered = sum(1 for f in all_md_files if str(f.resolve()) in reported_files)
    if covered < md_count:
        add_check("all markdown files covered in report", False,
                  f"Only {covered}/{md_count} .md files appear in the report. Missing: "
                  + str([str(f) for f in all_md_files if str(f.resolve()) not in reported_files][:5]))
    else:
        add_check("all markdown files covered in report", True, f"All {md_count} .md files reported.")

    # ── Check 5: all files valid (no broken links) ────────────────────────
    invalid_entries = [e for e in report if isinstance(e, dict) and not e.get("valid", False)]
    if invalid_entries:
        broken_summary = []
        for e in invalid_entries:
            broken_summary.append(f"{e.get('file','?')}: {e.get('brokenLinks', [])}")
        add_check("all files report valid=true", False,
                  f"{len(invalid_entries)} file(s) still have broken links: " + "; ".join(broken_summary[:5]))
    else:
        add_check("all files report valid=true", True, "All reported files have valid=true.")

    # ── Check 6: all brokenLinks arrays are empty ─────────────────────────
    non_empty_broken = [e for e in report if isinstance(e, dict) and e.get("brokenLinks")]
    if non_empty_broken:
        add_check("all brokenLinks arrays are empty", False,
                  f"{len(non_empty_broken)} file(s) still list broken links.")
    else:
        add_check("all brokenLinks arrays are empty", True, "No broken links remain in any file.")

    # ── Check 7: Actually re-run the validator to confirm source files fixed ─
    try:
        result = subprocess.run(
            ["openclaw", "exec", "node", "/skills/markdown-validator/index.js", workspace],
            capture_output=True, text=True, timeout=30
        )
        live_report = json.loads(result.stdout)
        live_invalid = [e for e in live_report if isinstance(e, dict) and not e.get("valid", True)]
        if live_invalid:
            broken_detail = []
            for e in live_invalid:
                broken_detail.append(
                    f"{e.get('file','?')}: " + str([b.get('url') for b in e.get('brokenLinks', [])])
                )
            add_check("live re-validation passes (no broken links in source files)", False,
                      "Live validator still finds broken links: " + "; ".join(broken_detail[:5]))
        else:
            add_check("live re-validation passes (no broken links in source files)", True,
                      f"Live validator confirms all {len(live_report)} files are clean.")
    except subprocess.TimeoutExpired:
        add_check("live re-validation passes (no broken links in source files)", False, "Validator timed out.")
    except Exception as e:
        add_check("live re-validation passes (no broken links in source files)", False, f"Error running validator: {e}")

    # ── Check 8: Originally broken files now fixed (spot-check targets) ──
    originally_broken = [
        "docs/specifications/software/software-requirements.md",
        "docs/specifications/hardware/hardware-requirements.md",
        "docs/compliance/iso13485/design-controls.md",
        "docs/release-notes/v3.0.0-draft.md",
    ]
    fixed_count = 0
    for rel_path in originally_broken:
        full = Path(workspace) / rel_path
        if not full.exists():
            continue
        try:
            content = full.read_text()
            # Run validator on just this file
            r = subprocess.run(
                ["openclaw", "exec", "node", "/skills/markdown-validator/index.js", str(full)],
                capture_output=True, text=True, timeout=15
            )
            file_report = json.loads(r.stdout)
            file_valid = all(e.get("valid", False) for e in file_report)
            if file_valid:
                fixed_count += 1
        except Exception:
            pass

    if fixed_count < len(originally_broken):
        add_check("originally broken files are fixed", False,
                  f"Only {fixed_count}/{len(originally_broken)} originally-broken files are now clean.")
    else:
        add_check("originally broken files are fixed", True,
                  f"All {len(originally_broken)} originally-broken files confirmed fixed.")

    # ── Check 9: external links and anchors NOT tampered with ─────────────
    operator_guide = Path(workspace) / "docs/training/operator-guide.md"
    try:
        og_content = operator_guide.read_text()
        has_external = "https://www.fda.gov" in og_content
        has_anchor = "#sections" in og_content
        if has_external and has_anchor:
            add_check("external links and anchors preserved in operator-guide", True,
                      "External URL and same-file anchor remain intact.")
        else:
            add_check("external links and anchors preserved in operator-guide", False,
                      f"External URL present: {has_external}, anchor present: {has_anchor}. "
                      "Agent may have incorrectly modified these valid references.")
    except Exception as e:
        add_check("external links and anchors preserved in operator-guide", False, f"Could not read file: {e}")

    # ── Score ─────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    final_pass = passed_all

    return {"passed": final_pass, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))