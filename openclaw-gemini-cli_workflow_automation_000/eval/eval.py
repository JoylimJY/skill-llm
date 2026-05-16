#!/usr/bin/env python3
import sys
import json
import subprocess
from pathlib import Path

def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Helper ─────────────────────────────────────────────────────────────

    def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── CHECK 1: site_spec.json exists somewhere in workspace ───────────────
    try:
        candidates = list(workspace.rglob("site_spec.json"))
        if candidates:
            spec_file = candidates[0]
            score = add_check(
                "site_spec.json exists",
                True,
                f"Found at: {spec_file.relative_to(workspace)}",
                weight=1.0
            )
        else:
            score = add_check(
                "site_spec.json exists",
                False,
                "site_spec.json not found anywhere in workspace",
                weight=1.0
            )
            spec_file = None
        total_score += score
    except Exception as e:
        add_check("site_spec.json exists", False, f"Error scanning workspace: {e}", weight=1.0)
        spec_file = None

    # ── CHECK 2: site_spec.json is valid JSON ───────────────────────────────
    spec_data = None
    if spec_file:
        try:
            raw = spec_file.read_text(encoding="utf-8")
            spec_data = json.loads(raw)
            total_score += add_check(
                "site_spec.json is valid JSON",
                True,
                "Parsed successfully",
                weight=1.0
            )
        except json.JSONDecodeError as e:
            total_score += add_check(
                "site_spec.json is valid JSON",
                False,
                f"JSON parse error: {e}",
                weight=1.0
            )
        except Exception as e:
            total_score += add_check(
                "site_spec.json is valid JSON",
                False,
                f"Read error: {e}",
                weight=1.0
            )
    else:
        total_score += add_check(
            "site_spec.json is valid JSON",
            False,
            "Skipped — file not found",
            weight=1.0
        )

    # ── CHECK 3: site_spec.json contains all required top-level keys ────────
    REQUIRED_KEYS = {"stack", "pages", "components", "copy_style", "seo_keywords", "risks"}
    if spec_data and isinstance(spec_data, dict):
        present_keys = set(spec_data.keys())
        missing = REQUIRED_KEYS - present_keys
        has_all = len(missing) == 0
        total_score += add_check(
            "site_spec.json has all required keys",
            has_all,
            f"Present: {sorted(present_keys)}, Missing: {sorted(missing)}",
            weight=2.0
        )
    else:
        total_score += add_check(
            "site_spec.json has all required keys",
            False,
            "Skipped — no valid JSON data",
            weight=2.0
        )

    # ── CHECK 4: Verify specific mock-generated values (proves gemini was called correctly) ─
    if spec_data and isinstance(spec_data, dict):
        # Stack must be Next.js (from mock's JSON response)
        stack_ok = spec_data.get("stack", "") == "Next.js"
        total_score += add_check(
            "site_spec.json 'stack' is Next.js (from correct gemini call)",
            stack_ok,
            f"Got stack: {spec_data.get('stack', 'MISSING')}",
            weight=1.5
        )

        # pages must be a list with at least 2 entries
        pages = spec_data.get("pages", [])
        pages_ok = isinstance(pages, list) and len(pages) >= 2
        total_score += add_check(
            "site_spec.json 'pages' is a list with >= 2 entries",
            pages_ok,
            f"pages count: {len(pages) if isinstance(pages, list) else 'not a list'}",
            weight=1.0
        )

        # seo_keywords must be a non-empty list
        seo = spec_data.get("seo_keywords", [])
        seo_ok = isinstance(seo, list) and len(seo) >= 1
        total_score += add_check(
            "site_spec.json 'seo_keywords' is a non-empty list",
            seo_ok,
            f"seo_keywords: {seo[:3] if isinstance(seo, list) else 'not a list'}",
            weight=1.0
        )

        # copy_style must contain 'conversion' or 'energetic' (from mock)
        copy_style = spec_data.get("copy_style", "")
        copy_ok = isinstance(copy_style, str) and any(
            kw in copy_style.lower() for kw in ["conversion", "energetic", "trustworthy"]
        )
        total_score += add_check(
            "site_spec.json 'copy_style' reflects conversion/energetic tone",
            copy_ok,
            f"copy_style: {copy_style}",
            weight=1.0
        )

        # risks must be a non-empty list
        risks = spec_data.get("risks", [])
        risks_ok = isinstance(risks, list) and len(risks) >= 1
        total_score += add_check(
            "site_spec.json 'risks' is a non-empty list",
            risks_ok,
            f"risks count: {len(risks) if isinstance(risks, list) else 'not a list'}",
            weight=1.0
        )
    else:
        for check_name in [
            "site_spec.json 'stack' is Next.js (from correct gemini call)",
            "site_spec.json 'pages' is a list with >= 2 entries",
            "site_spec.json 'seo_keywords' is a non-empty list",
            "site_spec.json 'copy_style' reflects conversion/energetic tone",
            "site_spec.json 'risks' is a non-empty list",
        ]:
            total_score += add_check(check_name, False, "Skipped — no valid JSON data", weight=1.0)

    # ── CHECK 5: review_report.txt exists somewhere in workspace ────────────
    try:
        review_candidates = list(workspace.rglob("review_report.txt"))
        if review_candidates:
            review_file = review_candidates[0]
            total_score += add_check(
                "review_report.txt exists",
                True,
                f"Found at: {review_file.relative_to(workspace)}",
                weight=1.0
            )
        else:
            total_score += add_check(
                "review_report.txt exists",
                False,
                "review_report.txt not found anywhere in workspace",
                weight=1.0
            )
            review_file = None
    except Exception as e:
        total_score += add_check("review_report.txt exists", False, f"Error: {e}", weight=1.0)
        review_file = None

    # ── CHECK 6: review_report.txt has substantive review content ───────────
    if review_file:
        try:
            review_text = review_file.read_text(encoding="utf-8").strip()
            # Must have bullet-point content from mock review (at least 3 bullet lines)
            bullet_lines = [l for l in review_text.splitlines() if l.strip().startswith("•") or l.strip().startswith("-") or l.strip().startswith("*")]
            has_bullets = len(bullet_lines) >= 3
            has_issue_content = any(
                kw in review_text.lower()
                for kw in ["issue", "fix", "cta", "headline", "component", "review"]
            )
            review_ok = has_bullets and has_issue_content and len(review_text) > 100
            total_score += add_check(
                "review_report.txt has substantive bullet-point review content",
                review_ok,
                f"Bullet lines: {len(bullet_lines)}, Length: {len(review_text)}, Has keywords: {has_issue_content}",
                weight=2.0
            )
        except Exception as e:
            total_score += add_check(
                "review_report.txt has substantive bullet-point review content",
                False,
                f"Read error: {e}",
                weight=2.0
            )
    else:
        total_score += add_check(
            "review_report.txt has substantive bullet-point review content",
            False,
            "Skipped — file not found",
            weight=2.0
        )

    # ── CHECK 7: gemini_json.sh was used correctly (validate it works standalone) ──
    try:
        script_path = workspace / "scripts" / "gemini_json.sh"
        if script_path.exists() and os.access(str(script_path), os.X_OK):
            total_score += add_check(
                "scripts/gemini_json.sh is executable",
                True,
                "File exists and is executable",
                weight=0.5
            )
        else:
            total_score += add_check(
                "scripts/gemini_json.sh is executable",
                False,
                f"Exists: {script_path.exists()}, Executable: {os.access(str(script_path), os.X_OK) if script_path.exists() else 'N/A'}",
                weight=0.5
            )
    except Exception as e:
        total_score += add_check("scripts/gemini_json.sh is executable", False, f"Error: {e}", weight=0.5)

    # ── CHECK 8: site_spec.json is NOT a copy of the broken draft ───────────
    try:
        if spec_data:
            # The broken draft had React as stack and was invalid JSON
            # The real generated spec must be different and valid
            not_draft = spec_data.get("stack", "") != "React" or (
                isinstance(spec_data.get("pages", None), list) and
                isinstance(spec_data.get("seo_keywords", None), list)
            )
            total_score += add_check(
                "site_spec.json is newly generated (not a copy of broken draft)",
                not_draft,
                f"stack={spec_data.get('stack')}, pages type={type(spec_data.get('pages')).__name__}",
                weight=1.0
            )
        else:
            total_score += add_check(
                "site_spec.json is newly generated (not a copy of broken draft)",
                False,
                "No valid spec data to verify",
                weight=1.0
            )
    except Exception as e:
        total_score += add_check(
            "site_spec.json is newly generated (not a copy of broken draft)",
            False,
            f"Error: {e}",
            weight=1.0
        )

    # ── Final scoring ───────────────────────────────────────────────────────
    max_score = 1.0 + 1.0 + 2.0 + 1.5 + 1.0 + 1.0 + 1.0 + 1.0 + 1.0 + 2.0 + 0.5 + 1.0
    normalized = round(min(total_score / max_score, 1.0), 4)
    passed = normalized >= 0.70

    return {
        "passed": passed,
        "score": normalized,
        "checks": checks
    }

import os

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "argument_check", "passed": False, "detail": "No workspace directory provided"}
        ]}))
        sys.exit(1)

    result = run_checks(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))