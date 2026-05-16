import sys
import json
import os
from pathlib import Path

def find_report(workspace):
    """Search for citation_audit_report.json anywhere in the workspace."""
    matches = list(Path(workspace).rglob("citation_audit_report.json"))
    return matches[0] if matches else None

def evaluate(workspace):
    checks = []
    score = 0.0
    total_weight = 0.0

    # ── locate report ──────────────────────────────────────────────────────────
    report_path = find_report(workspace)
    file_found = report_path is not None
    checks.append({
        "name": "report_file_exists",
        "passed": file_found,
        "detail": f"Found at {report_path}" if file_found else "citation_audit_report.json not found anywhere in workspace"
    })
    if not file_found:
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── parse JSON ─────────────────────────────────────────────────────────────
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        checks.append({"name": "report_is_valid_json", "passed": True, "detail": "Parsed successfully"})
    except Exception as e:
        checks.append({"name": "report_is_valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    report_str = json.dumps(report).lower()

    # ══════════════════════════════════════════════════════════════════════════
    # CATEGORY A: STYLE CONSISTENCY VIOLATIONS  (weight: 3 × 10 = 30 pts)
    # Expected: agent flags footnotes 4, 5, 7 as mixed-style violations
    # The skill says consistency across the WHOLE document is the #1 rule.
    # Note: the skill explicitly says Bluebook/APA alone is fine; MIXING is the sin.
    # ══════════════════════════════════════════════════════════════════════════

    def fn_mentioned(report_str, fn_numbers, context_words):
        """Check if report references a footnote number alongside context."""
        for fn in fn_numbers:
            patterns = [f'"footnote {fn}"', f'"fn {fn}"', f'"fn{fn}"',
                        f'"footnote_{fn}"', f'footnote {fn}', f'"note {fn}"',
                        f'#{fn}', f'[{fn}]', f' {fn} ', f'"{fn}"', f"'{fn}'"]
            fn_found = any(p.lower() in report_str for p in patterns)
            if fn_found:
                return True
        return False

    # A1: Mixed style detected (any signal that inconsistency was found)
    mixed_signals = ["mixed", "inconsistent", "consistency", "style violation",
                     "different style", "multiple style", "uniform", "uniformity",
                     "mixed citation", "citation style"]
    a1_passed = any(s in report_str for s in mixed_signals)
    weight_a1 = 15.0
    total_weight += weight_a1
    if a1_passed:
        score += weight_a1
    checks.append({
        "name": "A1_mixed_style_detected",
        "passed": a1_passed,
        "detail": "Report must signal that citation style mixing was detected across the document"
    })

    # A2: Footnotes 4 and/or 7 (Bluebook) flagged
    a2_passed = fn_mentioned(report_str, ["4", "7"], ["bluebook", "style", "mixed", "inconsistent"])
    # More flexible: just check if FN4 or FN7 appear in context of violations
    if not a2_passed:
        a2_passed = ("4" in report_str and any(s in report_str for s in mixed_signals)) or \
                    ("7" in report_str and any(s in report_str for s in mixed_signals))
    weight_a2 = 8.0
    total_weight += weight_a2
    if a2_passed:
        score += weight_a2
    checks.append({
        "name": "A2_bluebook_footnotes_flagged",
        "passed": a2_passed,
        "detail": "Footnotes 4 and/or 7 (Bluebook format) should be flagged as style violations"
    })

    # A3: Footnote 5 (APA format) flagged
    a3_passed = "5" in report_str and any(s in report_str for s in mixed_signals + ["apa", "author-date", "parenthetical"])
    weight_a3 = 7.0
    total_weight += weight_a3
    if a3_passed:
        score += weight_a3
    checks.append({
        "name": "A3_apa_footnote5_flagged",
        "passed": a3_passed,
        "detail": "Footnote 5 (APA format) should be flagged as a style inconsistency"
    })

    # ══════════════════════════════════════════════════════════════════════════
    # CATEGORY B: MISSING PAGE NUMBER VIOLATIONS  (weight: 25 pts)
    # Skill rule: every footnote must let the judge locate content to a specific page
    # FN8 (Gabcikovo - no pinpoint), FN12 (Milanovic article - no pinpoint)
    # ══════════════════════════════════════════════════════════════════════════

    page_signals = ["page", "pinpoint", "missing page", "no page", "page number",
                    "specific page", "precise location", "pagina", "locating"]

    # B1: General page number issue detected
    b1_passed = any(s in report_str for s in page_signals)
    weight_b1 = 8.0
    total_weight += weight_b1
    if b1_passed:
        score += weight_b1
    checks.append({
        "name": "B1_page_number_issue_detected",
        "passed": b1_passed,
        "detail": "Report must mention missing page/pinpoint numbers as a violation category"
    })

    # B2: FN8 (Gabcikovo, no pinpoint) flagged
    gabcikovo_signals = ["gabč", "gabc", "gab", "hungary", "slovakia", "8"]
    b2_fn8 = any(s in report_str for s in gabcikovo_signals[:4])  # case name
    b2_num = "8" in report_str and any(s in report_str for s in page_signals)
    b2_passed = b2_fn8 or b2_num
    weight_b2 = 9.0
    total_weight += weight_b2
    if b2_passed:
        score += weight_b2
    checks.append({
        "name": "B2_fn8_missing_pinpoint_flagged",
        "passed": b2_passed,
        "detail": "Footnote 8 (Gabcikovo case, no pinpoint page) must be flagged for missing page number"
    })

    # B3: FN12 (Milanovic article, no pinpoint) flagged
    milanovic_signals = ["milanovic", "milanović", "genocide", "european journal", "12"]
    b3_name = any(s in report_str for s in milanovic_signals[:4])
    b3_num = "12" in report_str and any(s in report_str for s in page_signals)
    b3_passed = b3_name or b3_num
    weight_b3 = 8.0
    total_weight += weight_b3
    if b3_passed:
        score += weight_b3
    checks.append({
        "name": "B3_fn12_missing_pinpoint_flagged",
        "passed": b3_passed,
        "detail": "Footnote 12 (Milanovic article, no pinpoint) must be flagged for missing page number"
    })

    # ══════════════════════════════════════════════════════════════════════════
    # CATEGORY C: WRONG SUPRA NOTE REFERENCES  (weight: 35 pts)
    # This is the hardest and most proprietary check.
    # Skill explicitly warns: if new footnotes are added, all supra notes break.
    # FN14: "Shaw (n 3)" → Shaw first cited at FN13, not FN3
    # FN16: "Nicaragua (n 2)" → Nicaragua first cited at FN1, not FN2
    # FN22: "Vienna Convention (n 7)" → Vienna Conv first cited at FN6, not FN7
    # ══════════════════════════════════════════════════════════════════════════

    supra_signals = ["supra", "wrong supra", "incorrect supra", "supra note", "cross-reference",
                     "cross reference", "back-reference", "footnote number", "first citation",
                     "originally cited", "first appearance"]

    # C1: General supra note issue detected
    c1_passed = any(s in report_str for s in supra_signals)
    weight_c1 = 10.0
    total_weight += weight_c1
    if c1_passed:
        score += weight_c1
    checks.append({
        "name": "C1_supra_note_issue_detected",
        "passed": c1_passed,
        "detail": "Report must identify incorrect supra note references as a problem category"
    })

    # C2: FN14 Shaw supra error (n 3 should be n 13)
    # Check: report mentions fn14 AND shaw AND wrong number
    fn14_signals = ["14", "shaw", "(n 3)", "n 3", "n3", "13", "n 13", "n13"]
    c2_fn14 = "14" in report_str and "shaw" in report_str
    c2_correct = ("13" in report_str) or ("n 13" in report_str)
    c2_passed = c2_fn14 and (c2_correct or any(s in report_str for s in supra_signals))
    weight_c2 = 9.0
    total_weight += weight_c2
    if c2_passed:
        score += weight_c2
    checks.append({
        "name": "C2_fn14_shaw_wrong_supra",
        "passed": c2_passed,
        "detail": "FN14 'Shaw (n 3)' is wrong — Shaw first cited at FN13. Report must flag this."
    })

    # C3: FN16 Nicaragua supra error (n 2 should be n 1)
    c3_fn16 = "16" in report_str and ("nicaragua" in report_str)
    c3_correct = ("n 1" in report_str) or ("n1" in report_str) or ("(n 1)" in report_str) or \
                 ("footnote 1" in report_str)
    c3_passed = c3_fn16 and (c3_correct or any(s in report_str for s in supra_signals))
    weight_c3 = 9.0
    total_weight += weight_c3
    if c3_passed:
        score += weight_c3
    checks.append({
        "name": "C3_fn16_nicaragua_wrong_supra",
        "passed": c3_passed,
        "detail": "FN16 'Nicaragua (n 2)' is wrong — Nicaragua first cited at FN1. Report must flag this."
    })

    # C4: FN22 Vienna Convention supra error (n 7 should be n 6)
    c4_fn22 = "22" in report_str and ("vienna" in report_str)
    c4_correct = ("n 6" in report_str) or ("n6" in report_str) or ("(n 6)" in report_str) or \
                 ("footnote 6" in report_str)
    c4_passed = c4_fn22 and (c4_correct or any(s in report_str for s in supra_signals))
    weight_c4 = 7.0
    total_weight += weight_c4
    if c4_passed:
        score += weight_c4
    checks.append({
        "name": "C4_fn22_vienna_wrong_supra",
        "passed": c4_passed,
        "detail": "FN22 'Vienna Convention (n 7)' is wrong — VCLT first cited at FN6. Report must flag this."
    })

    # ══════════════════════════════════════════════════════════════════════════
    # CATEGORY D: FALSE POSITIVE GUARD  (weight: 10 pts)
    # Correct supra notes (FN11, FN18, FN20) must NOT be flagged as errors.
    # FN18: Corfu Channel (n 9) — Corfu first cited at FN2, not FN9!
    # Wait — let me re-check my planted data:
    #   FN2 cites Corfu Channel; FN18 says "Corfu Channel (n 9)" — this IS wrong (n 9 ≠ n 2)
    #   Actually FN18 IS a violation. Let me check FN11, FN20:
    #   FN11: "Nicaragua (n 1) 418" — Nicaragua first cited FN1 ✓ CORRECT
    #   FN20: "Cassese (n 11)" — Cassese... FN5 is APA Cassese, FN11 is Nicaragua...
    #         Wait: FN5 is Cassese APA; FN11 is "Nicaragua (n 1)". 
    #         So Cassese was first cited at FN5, not FN11. FN20 "Cassese (n 11)" is WRONG.
    # 
    # Let me re-examine: the SKILL.md says the key trap is supra notes breaking when 
    # new footnotes are added. So the agent must verify first-citation footnote numbers.
    #
    # Re-confirmed planted violations:
    #   FN14: Shaw (n 3) — Shaw first at FN3 is ACTUALLY CORRECT (FN3 is Shaw!)
    #         Wait: FN3 = Shaw, FN13 = Shaw again. FN14 says "Shaw (n 3)". 
    #         Shaw was FIRST cited at FN3, so "Shaw (n 3)" IS correct!
    #         The second Shaw citation is FN13. So FN14 should point to (n 3) as that was first cite.
    #         Hmm, this is actually correct. Let me re-examine my violations carefully.
    #
    # ACTUAL violations based on brief text:
    #   FN1: Nicaragua (first cite) ✓
    #   FN2: Corfu Channel (first cite) ✓  
    #   FN3: Shaw (first cite) ✓
    #   FN4: Treaty of Velantia - Bluebook style ← style violation
    #   FN5: Cassese - APA style ← style violation  
    #   FN6: Vienna Convention (first cite) ✓ OSCOLA
    #   FN7: Nicaragua Merits (Bluebook) ← style violation  (also duplicate of same case)
    #   FN8: Gabcikovo - no pinpoint ← missing page
    #   FN9: Nuclear Weapons (first cite) ✓
    #   FN10: Armed Activities (first cite) ✓
    #   FN11: "Nicaragua (n 1)" ← first cite was FN1 → CORRECT ✓
    #   FN12: Milanovic - no pinpoint ← missing page
    #   FN13: Shaw again (this is a repeat full citation, not supra)
    #   FN14: "Shaw (n 3)" ← Shaw first cited FN3 → (n 3) is CORRECT ✓
    #         But FN13 re-cites Shaw in full → that itself might be an inconsistency
    #         (should have used supra at FN13 pointing to FN3, then FN14 supra → FN3 correct)
    #   FN16: "Nicaragua (n 2)" ← Nicaragua first cited FN1 → WRONG (should be n 1)
    #   FN18: "Corfu Channel (n 9)" ← Corfu first cited FN2 → WRONG (should be n 2)
    #   FN20: "Cassese (n 11)" ← Cassese first cited FN5 (APA) → WRONG (should be n 5)
    #   FN22: "Vienna Convention (n 7)" ← VCLT first cited FN6 → WRONG (should be n 6)
    #
    # So actual supra violations: FN16, FN18, FN20, FN22
    # And FN11 is CORRECT.
    # 
    # The eval script above has some errors. Let me fix C2 (FN14 is actually correct).
    # And add FN18, FN20 as violations.
    # This is detected during eval writing — the eval script needs to be corrected.
    # I'll rewrite the eval with the correct violations.
    # 
    # (This note section was internal reasoning, eval below is the corrected version)
    # ══════════════════════════════════════════════════════════════════════════

    # Correct supra note FN11 should NOT be flagged
    fn11_wrongly_flagged = ("11" in report_str and "wrong" in report_str and 
                            "nicaragua" in report_str and "11" in report_str)
    d1_passed = not fn11_wrongly_flagged
    weight_d1 = 5.0
    total_weight += weight_d1
    if d1_passed:
        score += weight_d1
    checks.append({
        "name": "D1_fn11_not_false_positive",
        "passed": d1_passed,
        "detail": "FN11 'Nicaragua (n 1)' is correct and should NOT be flagged as a supra error"
    })

    # ══════════════════════════════════════════════════════════════════════════
    # FINAL SCORING
    # ══════════════════════════════════════════════════════════════════════════
    final_score = round(score / total_weight, 3) if total_weight > 0 else 0.0
    
    # Pass threshold: must score at least 0.60 and detect at least one from each category
    cat_a = a1_passed
    cat_b = b1_passed
    cat_c = c1_passed
    passed = (final_score >= 0.60) and cat_a and cat_b and cat_c

    checks.append({
        "name": "FINAL_categories_covered",
        "passed": passed,
        "detail": f"Score={final_score:.3f} | Style={cat_a} | PageNums={cat_b} | Supra={cat_c} | Threshold=0.60"
    })

    return {"passed": passed, "score": final_score, "checks": checks}


# ── CORRECTED EVAL (rebuilding with accurate violation map) ────────────────────

def evaluate_corrected(workspace):
    checks = []

    report_path = find_report(workspace)
    file_found = report_path is not None
    checks.append({
        "name": "report_file_exists",
        "passed": file_found,
        "detail": f"Found at {report_path}" if file_found else "citation_audit_report.json not found"
    })
    if not file_found:
        return {"passed": False, "score": 0.0, "checks": checks}

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        checks.append({"name": "report_is_valid_json", "passed": True, "detail": "OK"})
    except Exception as e:
        checks.append({"name": "report_is_valid_json", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    rs = json.dumps(report).lower()

    score = 0.0
    weights = {}

    # ── A: Style Consistency ──────────────────────────────────────────────────
    mixed_kw = ["mixed", "inconsistent", "consistency", "inconsistency", "different style",
                "multiple style", "uniform", "style violation", "citation style"]
    
    # A1: Inconsistency detected at all
    a1 = any(k in rs for k in mixed_kw)
    weights["A1_style_inconsistency_detected"] = (15.0, a1,
        "Report must flag that citation style is mixed across the document")

    # A2: FN4 (Bluebook treaty) or FN7 (Bluebook case) cited as mixed-style
    a2 = (any(str(n) in rs for n in [4, 7]) and any(k in rs for k in mixed_kw + ["bluebook"]))
    weights["A2_bluebook_fns_flagged"] = (8.0, a2,
        "FN4 and/or FN7 (Bluebook style) should be identified in style violations")

    # A3: FN5 (APA) flagged  
    a3 = ("5" in rs and any(k in rs for k in mixed_kw + ["apa", "author"]))
    weights["A3_apa_fn5_flagged"] = (7.0, a3,
        "FN5 (APA format) should be identified as a style inconsistency")

    # ── B: Missing Page Numbers ───────────────────────────────────────────────
    page_kw = ["page", "pinpoint", "missing page", "no page", "page number", "specific page"]
    
    b1 = any(k in rs for k in page_kw)
    weights["B1_page_issue_detected"] = (8.0, b1,
        "Report must flag missing pinpoint page numbers as a violation")

    # FN8: Gabcikovo - no pinpoint page cited
    gabk = ["gabč", "gabc", "hungary", "slovakia"]
    b2 = (any(k in rs for k in gabk) or ("8" in rs and any(k in rs for k in page_kw)))
    weights["B2_fn8_no_pinpoint"] = (9.0, b2,
        "FN8 (Gabcikovo - Hungary/Slovakia, no pinpoint) must be flagged")

    # FN12: Milanovic article - no pinpoint page
    milk = ["milanovic", "milanović", "genocide", "european journal"]
    b3 = (any(k in rs for k in milk) or ("12" in rs and any(k in rs for k in page_kw)))
    weights["B3_fn12_no_pinpoint"] = (8.0, b3,
        "FN12 (Milanovic journal article, no pinpoint page) must be flagged")

    # ── C: Wrong Supra Note References ───────────────────────────────────────
    supra_kw = ["supra", "wrong supra", "incorrect supra", "cross-reference",
                "first citation", "first cited", "first appear"]

    c1 = any(k in rs for k in supra_kw)
    weights["C1_supra_issue_detected"] = (10.0, c1,
        "Report must identify incorrect supra note cross-references")

    # FN16: "Nicaragua (n 2)" — should be (n 1) since Nicaragua first cited at FN1
    c2 = ("16" in rs and "nicaragua" in rs and 
          any(k in rs for k in supra_kw + ["n 1", "(n 1)", "footnote 1", "n1"]))
    weights["C2_fn16_nicaragua_wrong_supra"] = (10.0, c2,
        "FN16 'Nicaragua (n 2)' is wrong — first cite is FN1. Must be flagged.")

    # FN18: "Corfu Channel (n 9)" — should be (n 2) since Corfu first cited at FN2
    c3 = ("18" in rs and "corfu" in rs and
          any(k in rs for k in supra_kw + ["n 2", "(n 2)", "footnote 2", "n2"]))
    weights["C3_fn18_corfu_wrong_supra"] = (9.0, c3,
        "FN18 'Corfu Channel (n 9)' is wrong — first cite is FN2. Must be flagged.")

    # FN22: "Vienna Convention (n 7)" — should be (n 6)
    c4 = ("22" in rs and "vienna" in rs and
          any(k in rs for k in supra_kw + ["n 6", "(n 6)", "footnote 6", "n6"]))
    weights["C4_fn22_vienna_wrong_supra"] = (8.0, c4,
        "FN22 'Vienna Convention (n 7)' is wrong — first cite is FN6. Must be flagged.")

    # FN20: "Cassese (n 11)" — should be (n 5) since Cassese first cited at FN5
    c5 = ("20" in rs and "cassese" in rs and
          any(k in rs for k in supra_kw + ["n 5", "(n 5)", "footnote 5", "n5"]))
    weights["C5_fn20_cassese_wrong_supra"] = (8.0, c5,
        "FN20 'Cassese (n 11)' is wrong — first cite is FN5. Must be flagged.")

    # ── D: False Positive Guard ───────────────────────────────────────────────
    # FN11 "Nicaragua (n 1)" is CORRECT and must not be called wrong
    fn11_flagged_wrong = ("11" in rs and "wrong" in rs and "nicaragua" in rs)
    d1 = not fn11_flagged_wrong
    weights["D1_fn11_not_false_positive"] = (5.0, d1,
        "FN11 'Nicaragua (n 1)' IS correct and must NOT be flagged as a supra error")

    # FN14 "Shaw (n 3)" — Shaw first cited FN3. This is CORRECT.
    fn14_flagged_wrong = ("14" in rs and "shaw" in rs and "wrong" in rs)
    d2 = not fn14_flagged_wrong
    weights["D2_fn14_not_false_positive"] = (5.0, d2,
        "FN14 'Shaw (n 3)' IS correct (Shaw first cited at FN3) and must NOT be falsely flagged")

    # ── Compute final score ───────────────────────────────────────────────────
    total_w = sum(v[0] for v in weights.values())
    earned = sum(v[0] for v in weights.values() if v[1])

    for name, (w, p, detail) in weights.items():
        checks.append({"name": name, "passed": p, "detail": detail + f" [weight={w}]"})

    final_score = round(earned / total_w, 3) if total_w > 0 else 0.0

    # Must detect all three violation categories and score ≥ 0.55
    all_cats = a1 and b1 and c1
    passed = (final_score >= 0.55) and all_cats

    checks.append({
        "name": "FINAL_VERDICT",
        "passed": passed,
        "detail": (f"Score={final_score:.3f}/{1.0} | "
                   f"StyleCat={a1} | PageCat={b1} | SupraCat={c1} | "
                   f"Threshold=0.55 | AllCats={all_cats}")
    })

    return {"passed": passed, "score": final_score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate_corrected(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))