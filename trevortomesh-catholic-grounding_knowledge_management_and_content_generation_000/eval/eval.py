import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # ── Locate the output file ────────────────────────────────────────────────
    candidates = list(workspace_path.rglob("purgatory_answer.md"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found purgatory_answer.md at: {candidates[0]}" if file_found else "purgatory_answer.md not found anywhere in workspace"
    })

    if not file_found:
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    try:
        content = candidates[0].read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    content_lower = content.lower()

    # ── Check 1: Short Answer section present ─────────────────────────────────
    has_short_answer = bool(re.search(
        r"short\s+answer",
        content_lower
    ))
    checks.append({
        "name": "section_short_answer",
        "passed": has_short_answer,
        "detail": "Found 'Short Answer' section" if has_short_answer else "Missing 'Short Answer' section (required by format)"
    })

    # ── Check 2: "What the Church teaches" section present ───────────────────
    has_church_teaches = bool(re.search(
        r"what\s+the\s+church\s+teaches",
        content_lower
    ))
    checks.append({
        "name": "section_church_teaches",
        "passed": has_church_teaches,
        "detail": "Found 'What the Church teaches' section" if has_church_teaches else "Missing 'What the Church teaches' section"
    })

    # ── Check 3: Citations section present ───────────────────────────────────
    has_citations = bool(re.search(
        r"citations?",
        content_lower
    ))
    checks.append({
        "name": "section_citations",
        "passed": has_citations,
        "detail": "Found 'Citations' section" if has_citations else "Missing 'Citations' section"
    })

    # ── Check 4: Practical next step section present ──────────────────────────
    has_next_step = bool(re.search(
        r"practical\s+next\s+step",
        content_lower
    ))
    checks.append({
        "name": "section_practical_next_step",
        "passed": has_next_step,
        "detail": "Found 'Practical next step' section" if has_next_step else "Missing 'Practical next step' section"
    })

    # ── Check 5: CCC references from ccc.sh output (1030, 1031, 1032, 1472) ──
    # The agent must have run ccc.sh and included the actual paragraph numbers
    required_ccc = ["1030", "1031", "1032", "1472"]
    found_ccc = [ref for ref in required_ccc if ref in content]
    all_ccc_present = len(found_ccc) == len(required_ccc)
    checks.append({
        "name": "ccc_references_from_script",
        "passed": all_ccc_present,
        "detail": (
            f"All required CCC references present: {required_ccc}" if all_ccc_present
            else f"Missing CCC refs: {[r for r in required_ccc if r not in content]}. Found: {found_ccc}"
        )
    })

    # ── Check 6: Prayer snippet included (eternal rest is the relevant one) ───
    # agent should have used prayer.sh with "eternal rest"
    eternal_rest_keywords = ["eternal rest", "perpetual light", "faithful departed"]
    has_prayer = any(kw in content_lower for kw in eternal_rest_keywords)
    checks.append({
        "name": "prayer_snippet_included",
        "passed": has_prayer,
        "detail": (
            "Eternal Rest prayer or its content is present" if has_prayer
            else "No relevant prayer snippet found (expected Eternal Rest prayer from prayer.sh)"
        )
    })

    # ── Check 7: Dogma vs doctrine/discipline distinction ────────────────────
    # The guardrail requires distinguishing levels of Church teaching authority
    # Must mention at least dogma AND (doctrine OR discipline OR prudential)
    has_dogma = "dogma" in content_lower
    has_doctrine_or_discipline = any(
        w in content_lower for w in ["doctrine", "discipline", "prudential"]
    )
    has_distinction = has_dogma and has_doctrine_or_discipline
    checks.append({
        "name": "dogma_doctrine_distinction",
        "passed": has_distinction,
        "detail": (
            "Correctly distinguishes dogma from doctrine/discipline/prudential judgment" if has_distinction
            else (
                f"Missing distinction. Has 'dogma': {has_dogma}. "
                f"Has doctrine/discipline/prudential: {has_doctrine_or_discipline}"
            )
        )
    })

    # ── Check 8: Topic is about purgatory (not a generic placeholder) ─────────
    purgatory_count = content_lower.count("purgatory")
    is_about_purgatory = purgatory_count >= 3
    checks.append({
        "name": "content_is_about_purgatory",
        "passed": is_about_purgatory,
        "detail": f"'purgatory' mentioned {purgatory_count} times (need ≥3)" 
    })

    # ── Check 9: Does NOT hallucinate CCC numbers not in the topic map ────────
    # The script only provides 1030, 1031, 1032, 1472 for purgatory.
    # If agent cites CCC numbers outside 1000-1499 range for purgatory without
    # those being in the reference, that's a hallucination signal.
    # We check: all CCC numbers cited are plausible (not completely wrong)
    all_cited_ccc = re.findall(r"CCC\s*(\d{3,4})", content, re.IGNORECASE)
    # The valid ones from the script: 1030, 1031, 1032, 1472
    # We allow some flexibility for scripture refs but flag obviously wrong ones
    suspicious = [n for n in all_cited_ccc if int(n) > 2865]  # CCC only goes to ~2865
    no_hallucinated_refs = len(suspicious) == 0
    checks.append({
        "name": "no_hallucinated_ccc_numbers",
        "passed": no_hallucinated_refs,
        "detail": (
            "All cited CCC numbers are within valid range" if no_hallucinated_refs
            else f"Suspicious out-of-range CCC numbers found: {suspicious}"
        )
    })

    # ── Check 10: Four-section structure (all 4 sections present = full format) 
    all_four_sections = all([has_short_answer, has_church_teaches, has_citations, has_next_step])
    checks.append({
        "name": "all_four_required_sections_present",
        "passed": all_four_sections,
        "detail": (
            "All 4 required format sections are present" if all_four_sections
            else "One or more of the 4 required format sections is missing"
        )
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    # Weight the checks
    weights = {
        "output_file_exists":           0.05,
        "section_short_answer":         0.08,
        "section_church_teaches":       0.08,
        "section_citations":            0.08,
        "section_practical_next_step":  0.08,
        "ccc_references_from_script":   0.20,
        "prayer_snippet_included":      0.12,
        "dogma_doctrine_distinction":   0.15,
        "content_is_about_purgatory":   0.06,
        "no_hallucinated_ccc_numbers":  0.05,
        "all_four_required_sections_present": 0.05,
    }

    score = sum(
        weights.get(c["name"], 0.0) for c in checks if c["passed"]
    )
    score = round(min(score, 1.0), 4)

    # Passing threshold: must have all 4 sections, correct CCC refs, prayer, and distinction
    critical_checks = [
        "all_four_required_sections_present",
        "ccc_references_from_script",
        "dogma_doctrine_distinction",
        "prayer_snippet_included",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    passed = critical_passed and score >= 0.75

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))