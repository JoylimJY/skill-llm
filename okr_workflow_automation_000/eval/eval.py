import sys
import json
import re
from pathlib import Path

def find_okr_file(workspace: Path):
    """Try multiple possible locations for okr.md"""
    candidates = [
        workspace / ".openclaw" / "workspace" / "memory" / "okr.md",
        Path.home() / ".openclaw" / "workspace" / "memory" / "okr.md",
        Path("/root/.openclaw/workspace/memory/okr.md"),
    ]
    for c in candidates:
        if c.exists():
            return c
    # Also do a recursive search as fallback
    results = list(workspace.rglob("okr.md"))
    if results:
        return results[0]
    return None

def run_eval(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []

    # --- Locate the file ---
    okr_path = find_okr_file(workspace)
    file_found = okr_path is not None and okr_path.exists()

    checks.append({
        "name": "okr.md file exists at expected path",
        "passed": file_found,
        "detail": f"Found at: {okr_path}" if file_found else "okr.md not found in any expected location"
    })

    if not file_found:
        total = sum(1 for c in checks if c["passed"])
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    try:
        content = okr_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "File readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    content_lower = content.lower()

    # -------------------------------------------------------
    # CHECK 1: File has OKR header structure
    # -------------------------------------------------------
    has_header = "okr" in content_lower and (
        "追踪" in content or "OKR" in content or "okr" in content_lower
    )
    checks.append({
        "name": "File has OKR tracking header",
        "passed": has_header,
        "detail": "File contains OKR tracking title" if has_header else "Missing OKR header/title"
    })

    # -------------------------------------------------------
    # CHECK 2: Objective present with correct cycle 2025-Q3
    # -------------------------------------------------------
    has_objective = bool(re.search(r'(O1|Objective|目标).*(retention|留存|Retention)', content, re.IGNORECASE)) or \
                    bool(re.search(r'(O1|Objective|目标)', content, re.IGNORECASE))
    has_cycle = "2025-Q3" in content or "2025Q3" in content
    checks.append({
        "name": "Objective defined with 2025-Q3 cycle",
        "passed": has_objective and has_cycle,
        "detail": f"has_objective={has_objective}, has_cycle={has_cycle}"
    })

    # -------------------------------------------------------
    # CHECK 3: Status is 已完成 (completed)
    # -------------------------------------------------------
    has_completed_status = "已完成" in content or "completed" in content_lower or "完成" in content
    checks.append({
        "name": "Objective status marked as completed (已完成)",
        "passed": has_completed_status,
        "detail": "Found completion status" if has_completed_status else "No completion status found"
    })

    # -------------------------------------------------------
    # CHECK 4: All 3 KRs are present
    # -------------------------------------------------------
    has_kr1 = bool(re.search(r'KR1', content, re.IGNORECASE))
    has_kr2 = bool(re.search(r'KR2', content, re.IGNORECASE))
    has_kr3 = bool(re.search(r'KR3', content, re.IGNORECASE))
    all_krs_present = has_kr1 and has_kr2 and has_kr3
    checks.append({
        "name": "All 3 KRs present (KR1, KR2, KR3)",
        "passed": all_krs_present,
        "detail": f"KR1={has_kr1}, KR2={has_kr2}, KR3={has_kr3}"
    })

    # -------------------------------------------------------
    # CHECK 5: KR quantified with "from A to B" style values
    # KR1: 38% to 45%, KR2: 16% to 22%, KR3: 40% to 28%
    # -------------------------------------------------------
    has_kr1_values = bool(re.search(r'38', content)) and bool(re.search(r'45', content))
    has_kr2_values = bool(re.search(r'16', content)) and bool(re.search(r'22', content))
    has_kr3_values = bool(re.search(r'40', content)) and bool(re.search(r'28', content))
    krs_quantified = has_kr1_values and has_kr2_values and has_kr3_values
    checks.append({
        "name": "KRs contain quantified baseline and target values",
        "passed": krs_quantified,
        "detail": f"KR1_vals={has_kr1_values}, KR2_vals={has_kr2_values}, KR3_vals={has_kr3_values}"
    })

    # -------------------------------------------------------
    # CHECK 6: Final actuals recorded in KRs
    # KR1 actual=44%, KR2 actual=19.8%, KR3 actual=34%
    # -------------------------------------------------------
    has_actual_kr1 = bool(re.search(r'44', content))
    has_actual_kr2 = bool(re.search(r'19', content))  # 19.8 or 19%
    has_actual_kr3 = bool(re.search(r'34', content))
    actuals_recorded = has_actual_kr1 and has_actual_kr2 and has_actual_kr3
    checks.append({
        "name": "Final actual values recorded for KRs (44%, 19.8%, 34%)",
        "passed": actuals_recorded,
        "detail": f"actual_KR1(44)={has_actual_kr1}, actual_KR2(19.x)={has_actual_kr2}, actual_KR3(34)={has_actual_kr3}"
    })

    # -------------------------------------------------------
    # CHECK 7: Retrospective section exists
    # -------------------------------------------------------
    has_retro = "复盘" in content or "retrospect" in content_lower or "postmortem" in content_lower
    checks.append({
        "name": "Retrospective section exists (复盘)",
        "passed": has_retro,
        "detail": "Found retrospective section" if has_retro else "No retrospective/复盘 section found"
    })

    # -------------------------------------------------------
    # CHECK 8: Retrospective has all 5 required sub-sections
    # 结果概述、做得好的点、问题与偏差、可复用经验、下周期改进动作
    # -------------------------------------------------------
    retro_sections = {
        "结果概述": "结果概述" in content or "结果" in content,
        "做得好的点": "做得好" in content or "做得好的点" in content,
        "问题与偏差": "问题" in content and ("偏差" in content or "问题与偏差" in content),
        "可复用经验": "可复用" in content or "经验" in content,
        "下周期改进": "下周期" in content or "改进" in content,
    }
    all_retro_sections = all(retro_sections.values())
    checks.append({
        "name": "All 5 retrospective sub-sections present",
        "passed": all_retro_sections,
        "detail": str({k: v for k, v in retro_sections.items()})
    })

    # -------------------------------------------------------
    # CHECK 9: PROPRIETARY TRAP — Rating uses ONLY the 5 allowed tiers
    # Must be one of: Outstanding, Excellent, M+, Meeting Expectations, M-
    # Must NOT be a bare numeric score like 3.5 or 4/5 as the rating
    # -------------------------------------------------------
    allowed_ratings = ["outstanding", "excellent", "m+", "meeting expectations", "m-"]

    # Check if any of the proprietary tier labels appear
    rating_found = None
    for tier in allowed_ratings:
        if tier in content_lower:
            rating_found = tier
            break

    has_valid_rating = rating_found is not None
    checks.append({
        "name": "Rating uses proprietary tier label (Outstanding/Excellent/M+/Meeting Expectations/M-)",
        "passed": has_valid_rating,
        "detail": f"Found tier: '{rating_found}'" if has_valid_rating else
                  "No valid tier label found. Agent likely used a numeric score or non-standard label."
    })

    # -------------------------------------------------------
    # CHECK 10: No disallowed numeric-only rating (e.g. "最终评分：4.0" or "评分: 3/5")
    # The rating field should not be ONLY a bare number without a tier label
    # -------------------------------------------------------
    # Pattern: if "评分" or "rating" is followed immediately by a standalone number with no tier label nearby
    numeric_only_rating = bool(re.search(
        r'(最终评分|final rating|评分)[：:]\s*[\d]+\.?[\d]*\s*[（\(]?(?!outstanding|excellent|m\+|meeting expectations|m\-)',
        content_lower
    ))
    # Only flag if no valid rating label is present alongside
    bad_numeric_rating = numeric_only_rating and not has_valid_rating
    checks.append({
        "name": "Rating is NOT a bare numeric score without tier label",
        "passed": not bad_numeric_rating,
        "detail": "Rating field appears to use numeric-only score without tier label" if bad_numeric_rating
                  else "Rating field is compliant"
    })

    # -------------------------------------------------------
    # CHECK 11: Owner/负责人 recorded
    # -------------------------------------------------------
    has_owner = "li_na" in content_lower or "li na" in content_lower or "负责人" in content or "owner" in content_lower
    checks.append({
        "name": "Owner (Li Na / li_na) recorded",
        "passed": has_owner,
        "detail": "Owner field present" if has_owner else "No owner/负责人 field found"
    })

    # -------------------------------------------------------
    # SCORING
    # -------------------------------------------------------
    # Weights: file_found already passed. Distribute score across remaining checks.
    # Critical checks (must pass): file exists, all KRs, proprietary rating, retro sections
    critical_checks = [
        "okr.md file exists at expected path",
        "All 3 KRs present (KR1, KR2, KR3)",
        "Retrospective section exists (复盘)",
        "All 5 retrospective sub-sections present",
        "Rating uses proprietary tier label (Outstanding/Excellent/M+/Meeting Expectations/M-)",
        "Rating is NOT a bare numeric score without tier label",
    ]

    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    score = round(passed_checks / total_checks, 4)

    # Must pass ALL critical checks to get overall passed=True
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )

    overall_passed = critical_passed and passed_checks >= (total_checks * 0.75)

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))