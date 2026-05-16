#!/usr/bin/env python3
"""
eval_script.py
Evaluates the agent's Nika skill creation for '章节连贯性审查'.
Usage: python3 eval_script.py /workspace
"""

import sys
import re
import json
import subprocess
from pathlib import Path

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    skill_dir = workspace / "skills" / "章节连贯性审查"

    checks = []
    total_score = 0.0

    def check(name: str, passed: bool, detail: str, weight: float = 1.0):
        nonlocal total_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        if passed:
            total_score += weight

    MAX_SCORE = 10.0  # sum of all weights below

    # ── Check 1: Skill directory exists ──────────────────────────────────────
    try:
        dir_exists = skill_dir.exists() and skill_dir.is_dir()
        check("skill_dir_exists", dir_exists,
              f"Expected {skill_dir}" + (" — found" if dir_exists else " — NOT FOUND"),
              weight=0.5)
    except Exception as e:
        check("skill_dir_exists", False, f"Exception: {e}", weight=0.5)

    if not skill_dir.exists():
        # can't proceed with other checks
        result = {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # ── Check 2: README.md exists ─────────────────────────────────────────────
    readme = skill_dir / "README.md"
    try:
        readme_exists = readme.exists()
        check("readme_exists", readme_exists,
              str(readme) + (" found" if readme_exists else " NOT FOUND"),
              weight=0.5)
    except Exception as e:
        check("readme_exists", False, f"Exception: {e}", weight=0.5)

    # ── Check 3: No subdirectories inside skill dir ───────────────────────────
    try:
        sub_dirs = [d for d in skill_dir.iterdir() if d.is_dir()]
        no_subdirs = len(sub_dirs) == 0
        check("no_subdirectories", no_subdirs,
              f"Subdirs found: {[d.name for d in sub_dirs]}" if not no_subdirs else "No subdirs — correct",
              weight=0.5)
    except Exception as e:
        check("no_subdirectories", False, f"Exception: {e}", weight=0.5)

    # ── Check 4: Sub-docs exist (at least 2 .md files besides README) ─────────
    try:
        sub_docs = [f for f in skill_dir.glob("*.md") if f.name != "README.md"]
        has_subdocs = len(sub_docs) >= 2
        check("has_sub_docs", has_subdocs,
              f"Found {len(sub_docs)} sub-doc(s): {[f.name for f in sub_docs]}",
              weight=1.0)
    except Exception as e:
        check("has_sub_docs", False, f"Exception: {e}", weight=1.0)
        sub_docs = []

    # ── Check 5: README YAML front matter has 'name' (kebab-case) ─────────────
    try:
        if readme.exists():
            text = readme.read_text(encoding="utf-8")
            fm_match = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
            if fm_match:
                fm_block = fm_match.group(1)
                name_match = re.search(r'^name:\s*(.+)$', fm_block, re.MULTILINE)
                if name_match:
                    name_val = name_match.group(1).strip()
                    is_kebab = bool(re.fullmatch(r'[a-z0-9][a-z0-9\-]*', name_val))
                    check("readme_name_kebab_case", is_kebab,
                          f"name={name_val!r} {'is kebab-case' if is_kebab else 'NOT kebab-case'}",
                          weight=1.0)
                else:
                    check("readme_name_kebab_case", False, "No 'name' field in front matter", weight=1.0)
            else:
                check("readme_name_kebab_case", False, "No valid YAML front matter found", weight=1.0)
        else:
            check("readme_name_kebab_case", False, "README.md missing", weight=1.0)
    except Exception as e:
        check("readme_name_kebab_case", False, f"Exception: {e}", weight=1.0)

    # ── Check 6: README YAML front matter has 'description' ≤50 chars ─────────
    try:
        if readme.exists():
            text = readme.read_text(encoding="utf-8")
            fm_match = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
            if fm_match:
                fm_block = fm_match.group(1)
                desc_match = re.search(r'^description:\s*(.+)$', fm_block, re.MULTILINE)
                if desc_match:
                    desc_val = desc_match.group(1).strip()
                    short_enough = len(desc_val) <= 50
                    check("readme_description_length", short_enough,
                          f"description length={len(desc_val)}, value={desc_val!r}",
                          weight=0.5)
                else:
                    check("readme_description_length", False, "No 'description' field in front matter", weight=0.5)
            else:
                check("readme_description_length", False, "No valid YAML front matter", weight=0.5)
        else:
            check("readme_description_length", False, "README.md missing", weight=0.5)
    except Exception as e:
        check("readme_description_length", False, f"Exception: {e}", weight=0.5)

    # ── Check 7: README line count ≤120 ──────────────────────────────────────
    try:
        if readme.exists():
            lines = readme.read_text(encoding="utf-8").splitlines()
            within_limit = len(lines) <= 120
            check("readme_line_limit", within_limit,
                  f"README has {len(lines)} lines (limit 120)",
                  weight=0.5)
        else:
            check("readme_line_limit", False, "README.md missing", weight=0.5)
    except Exception as e:
        check("readme_line_limit", False, f"Exception: {e}", weight=0.5)

    # ── Check 8: README uses @ref syntax, NOT markdown path links ─────────────
    try:
        if readme.exists():
            text = readme.read_text(encoding="utf-8")
            at_refs = re.findall(r'@([\w\-\u4e00-\u9fff]+)', text)
            has_at_refs = len(at_refs) >= 1
            forbidden_links = re.findall(r'\[.*?\]\(.*?\.(md|txt|json|yaml).*?\)', text)
            no_path_links = len(forbidden_links) == 0
            passed = has_at_refs and no_path_links
            detail = (f"@refs found: {at_refs}; "
                      f"forbidden path links: {forbidden_links if forbidden_links else 'none'}")
            check("readme_uses_at_refs_not_paths", passed, detail, weight=2.0)
        else:
            check("readme_uses_at_refs_not_paths", False, "README.md missing", weight=2.0)
    except Exception as e:
        check("readme_uses_at_refs_not_paths", False, f"Exception: {e}", weight=2.0)

    # ── Check 9: Sub-docs have valid front matter with kebab-case name ────────
    try:
        sub_docs_ok = True
        sub_detail_parts = []
        for sd in sub_docs:
            txt = sd.read_text(encoding="utf-8")
            fm = re.match(r'^---\n(.*?)\n---', txt, re.DOTALL)
            if not fm:
                sub_docs_ok = False
                sub_detail_parts.append(f"{sd.name}: missing front matter")
                continue
            fm_block = fm.group(1)
            nm = re.search(r'^name:\s*(.+)$', fm_block, re.MULTILINE)
            if not nm or not re.fullmatch(r'[a-z0-9][a-z0-9\-]*', nm.group(1).strip()):
                sub_docs_ok = False
                sub_detail_parts.append(f"{sd.name}: name missing or not kebab-case")
            else:
                sub_detail_parts.append(f"{sd.name}: name={nm.group(1).strip()!r} OK")
            desc = re.search(r'^description:\s*(.+)$', fm_block, re.MULTILINE)
            if not desc:
                sub_docs_ok = False
                sub_detail_parts.append(f"{sd.name}: description missing")
            elif len(desc.group(1).strip()) > 30:
                sub_docs_ok = False
                sub_detail_parts.append(f"{sd.name}: description too long ({len(desc.group(1).strip())} chars)")
        check("sub_docs_front_matter", sub_docs_ok,
              "; ".join(sub_detail_parts) if sub_detail_parts else "No sub-docs to check",
              weight=1.0)
    except Exception as e:
        check("sub_docs_front_matter", False, f"Exception: {e}", weight=1.0)

    # ── Check 10: Sub-docs don't contain @refs ────────────────────────────────
    try:
        sub_no_at = True
        sub_at_parts = []
        for sd in sub_docs:
            txt = sd.read_text(encoding="utf-8")
            at_found = re.findall(r'@([\w\-\u4e00-\u9fff]+)', txt)
            if at_found:
                sub_no_at = False
                sub_at_parts.append(f"{sd.name}: {at_found}")
            else:
                sub_at_parts.append(f"{sd.name}: clean")
        check("sub_docs_no_at_refs", sub_no_at,
              "; ".join(sub_at_parts) if sub_at_parts else "No sub-docs",
              weight=1.0)
    except Exception as e:
        check("sub_docs_no_at_refs", False, f"Exception: {e}", weight=1.0)

    # ── Check 11: validate_nika_skill.py passes (exit 0) ─────────────────────
    try:
        result_proc = subprocess.run(
            ["python3", "scripts/validate_nika_skill.py", "skills/章节连贯性审查"],
            capture_output=True, text=True, cwd=str(workspace), timeout=30
        )
        validator_passed = result_proc.returncode == 0
        output_snippet = (result_proc.stdout + result_proc.stderr)[:500]
        check("validator_script_passes", validator_passed,
              f"Exit code={result_proc.returncode}; output={output_snippet!r}",
              weight=1.5)
    except Exception as e:
        check("validator_script_passes", False, f"Exception running validator: {e}", weight=1.5)

    # ── Final score ───────────────────────────────────────────────────────────
    normalized_score = round(total_score / MAX_SCORE, 3)
    all_passed = all(c["passed"] for c in checks)

    output = {
        "passed": all_passed,
        "score": normalized_score,
        "checks": checks
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()