#!/usr/bin/env python3
"""
Evaluation script for the investment arbitration moot coordinator task.
Usage: python eval_script.py /workspace
"""
import sys
import json
from pathlib import Path

def load_json_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def find_report(workspace):
    """Search for the output report file."""
    for candidate in Path(workspace).rglob("moot_status_report.json"):
        return candidate
    return None

def run_checks(workspace):
    checks = []
    score_total = 0.0

    report_path = find_report(workspace)
    if report_path is None:
        checks.append({"name": "report_file_exists", "passed": False,
                        "detail": "moot_status_report.json not found anywhere in workspace."})
        return checks, 0.0

    checks.append({"name": "report_file_exists", "passed": True,
                    "detail": f"Found at {report_path}"})
    score_total += 5.0

    try:
        report = load_json_file(report_path)
    except Exception as e:
        checks.append({"name": "report_parseable", "passed": False,
                        "detail": f"JSON parse error: {e}"})
        return checks, score_total

    checks.append({"name": "report_parseable", "passed": True, "detail": "Valid JSON."})
    score_total += 5.0

    # ── CHECK 1: FDI Shenzhen Cup advancement (top-2 per group) ──────────────
    # Correct ranking uses Wins → SB → Votes → Z-points cascade
    # Group A:
    #   A01: wins=3, sb=7, votes=5, z=412.5
    #   A02: wins=3, sb=7, votes=5, z=398.0   ← loses to A01 on z_points
    #   A03: wins=3, sb=7, votes=4, z=420.0   ← loses to A01/A02 on votes
    #  TOP-2 of Group A = A01 (PKU), A02 (Tsinghua)  [both wins=3, sb=7, votes=5; PKU > THU on z]
    #  Wait — A03 has wins=3, sb=7 but votes=4 < 5, so A01 and A02 beat A03.
    #  So Top-2 Group A = A01, A02
    # Group B:
    #   B01: wins=4, sb=9 → rank 1
    #   B02: wins=3, sb=8, votes=6, z=430 → rank 2 over B03 (same wins, sb, votes but z=430 > 418)
    #  TOP-2 of Group B = B01 (Renmin), B02 (Jilin)
    correct_fdi_advancing = {
        "A01",  # Peking University
        "A02",  # Tsinghua University
        "B01",  # Renmin University
        "B02",  # Jilin University
    }
    correct_fdi_adv_unis = {
        "Peking University",
        "Tsinghua University",
        "Renmin University",
        "Jilin University",
    }

    try:
        fdi_section = report.get("fdi_shenzhen", report.get("fdi", {}))
        advancing = fdi_section.get("advancing_teams", [])
        # Accept either team_id or university name
        advancing_ids = set()
        for t in advancing:
            if isinstance(t, dict):
                advancing_ids.add(t.get("team_id", t.get("university", "")))
            elif isinstance(t, str):
                advancing_ids.add(t)

        # Check if result matches by university name or team id
        match_unis = advancing_ids >= correct_fdi_adv_unis or advancing_ids >= correct_fdi_advancing
        # Try partial: at least 3 of 4 correct
        correct_count = sum(1 for x in advancing_ids if x in correct_fdi_adv_unis or x in correct_fdi_advancing)
        all_correct = len(advancing_ids) == 4 and correct_count == 4

        checks.append({
            "name": "fdi_group_a_b02_tsinghua_over_fudan",
            "passed": "Tsinghua University" in advancing_ids or "A02" in advancing_ids,
            "detail": (
                "A02 Tsinghua (wins=3, sb=7, votes=5, z=398) must beat A03 Fudan "
                "(wins=3, sb=7, votes=4) because Tsinghua has higher votes. "
                f"Advancing: {advancing_ids}"
            )
        })
        if "Tsinghua University" in advancing_ids or "A02" in advancing_ids:
            score_total += 10.0

        checks.append({
            "name": "fdi_group_b_jilin_over_nankai",
            "passed": ("Jilin University" in advancing_ids or "B02" in advancing_ids),
            "detail": (
                "B02 Jilin (wins=3, sb=8, votes=6, z=430) must beat B03 Nankai "
                "(wins=3, sb=8, votes=6, z=418) because Jilin has higher Z-points. "
                f"Advancing: {advancing_ids}"
            )
        })
        if "Jilin University" in advancing_ids or "B02" in advancing_ids:
            score_total += 10.0

        checks.append({
            "name": "fdi_exactly_4_advancing",
            "passed": len(advancing_ids) == 4,
            "detail": f"Expected 4 advancing teams, got {len(advancing_ids)}: {advancing_ids}"
        })
        if len(advancing_ids) == 4:
            score_total += 5.0

    except Exception as e:
        checks.append({"name": "fdi_advancing_teams", "passed": False, "detail": str(e)})

    # ── CHECK 2: FDI fee logic ────────────────────────────────────────────────
    # Advancing teams through Shenzhen Cup: 0 EUR (no fee)
    # China teams going directly (not via Shenzhen Cup): 250 EUR
    # Self-pay non-advancing (remaining slots): 650 EUR
    try:
        fee_section = report.get("fdi_shenzhen", report.get("fdi", {})).get("fees", {})
        if not fee_section:
            fee_section = report.get("fees", {})

        advancing_fee = fee_section.get("advancing_teams_fee_eur",
                        fee_section.get("advancing_fee", None))
        selfpay_fee = fee_section.get("self_pay_fee_eur",
                      fee_section.get("non_advancing_self_pay_fee", None))

        fee_advancing_correct = advancing_fee == 0 or str(advancing_fee) in ("0", "0.0", "free", "Free", "0 EUR")
        fee_selfpay_correct = selfpay_fee == 650 or str(selfpay_fee) in ("650", "650.0", "650 EUR")

        checks.append({
            "name": "fdi_fee_advancing_zero",
            "passed": bool(fee_advancing_correct),
            "detail": f"Advancing teams via Shenzhen Cup must pay 0 EUR. Got: {advancing_fee}"
        })
        if fee_advancing_correct:
            score_total += 7.0

        checks.append({
            "name": "fdi_fee_self_pay_650",
            "passed": bool(fee_selfpay_correct),
            "detail": f"Non-advancing self-pay teams must pay 650 EUR. Got: {selfpay_fee}"
        })
        if fee_selfpay_correct:
            score_total += 7.0

    except Exception as e:
        checks.append({"name": "fdi_fee_checks", "passed": False, "detail": str(e)})

    # ── CHECK 3: Frankfurt registration eligibility tiers ─────────────────────
    # Positions 1-24: full participant
    # Positions 25-36: waitlist (候补)
    # Positions 37+: excluded
    try:
        frankfurt_section = report.get("frankfurt", {})
        reg_tiers = frankfurt_section.get("registration_tiers", {})

        full_participants = reg_tiers.get("full_participants", reg_tiers.get("confirmed", []))
        waitlist = reg_tiers.get("waitlist", reg_tiers.get("candidates", []))
        excluded = reg_tiers.get("excluded", reg_tiers.get("rejected", []))

        # Check counts
        full_count_correct = len(full_participants) == 24
        waitlist_count_correct = len(waitlist) == 12
        excluded_count_correct = len(excluded) == 3  # positions 37, 38, 39

        checks.append({
            "name": "frankfurt_full_participants_exactly_24",
            "passed": full_count_correct,
            "detail": f"Expected 24 full participants (positions 1-24), got {len(full_participants)}"
        })
        if full_count_correct:
            score_total += 8.0

        checks.append({
            "name": "frankfurt_waitlist_exactly_12",
            "passed": waitlist_count_correct,
            "detail": f"Expected 12 waitlist teams (positions 25-36), got {len(waitlist)}"
        })
        if waitlist_count_correct:
            score_total += 8.0

        # Xi'an Jiaotong (position 25) MUST be in waitlist, not excluded
        xian_in_waitlist = any(
            ("Xi'an" in str(t) or "Xian" in str(t) or "Xi" in str(t))
            for t in waitlist
        )
        xian_not_excluded = not any(
            ("Xi'an" in str(t) or "Xian" in str(t))
            for t in excluded
        )
        checks.append({
            "name": "frankfurt_position25_is_waitlist_not_excluded",
            "passed": xian_in_waitlist or xian_not_excluded,
            "detail": (
                "Xi'an Jiaotong (registration position 25) must be in WAITLIST (候补), "
                f"NOT excluded. waitlist contains Xi'an: {xian_in_waitlist}"
            )
        })
        if xian_in_waitlist:
            score_total += 8.0

    except Exception as e:
        checks.append({"name": "frankfurt_registration_tiers", "passed": False, "detail": str(e)})

    # ── CHECK 4: Frankfurt member eligibility issues ───────────────────────────
    # Zhejiang University: has PhD student → ineligible
    # Wuhan University: has bar-registered member → ineligible
    # Jilin University: has LLM without permission → ineligible
    # Nankai University: has LLM WITH permission → eligible
    try:
        eligibility = frankfurt_section.get("eligibility_issues", [])
        elig_unis = []
        for item in eligibility:
            if isinstance(item, dict):
                elig_unis.append(item.get("university", ""))
            elif isinstance(item, str):
                elig_unis.append(item)
        elig_unis_str = " ".join(elig_unis)

        zhejiang_flagged = "Zhejiang" in elig_unis_str
        wuhan_flagged = "Wuhan" in elig_unis_str
        jilin_flagged = "Jilin" in elig_unis_str
        nankai_not_flagged = "Nankai" not in elig_unis_str

        checks.append({
            "name": "frankfurt_phd_student_flagged",
            "passed": zhejiang_flagged,
            "detail": f"Zhejiang University has a PhD student (ineligible). Flagged: {zhejiang_flagged}"
        })
        if zhejiang_flagged:
            score_total += 6.0

        checks.append({
            "name": "frankfurt_bar_registered_flagged",
            "passed": wuhan_flagged,
            "detail": f"Wuhan University has a bar-registered member (ineligible). Flagged: {wuhan_flagged}"
        })
        if wuhan_flagged:
            score_total += 6.0

        checks.append({
            "name": "frankfurt_llm_without_permission_flagged",
            "passed": jilin_flagged,
            "detail": f"Jilin University has LLM student without organizer permission. Flagged: {jilin_flagged}"
        })
        if jilin_flagged:
            score_total += 6.0

        checks.append({
            "name": "frankfurt_llm_with_permission_not_flagged",
            "passed": nankai_not_flagged,
            "detail": (
                f"Nankai University has LLM student WITH permission (eligible). "
                f"Should NOT be flagged. Not flagged: {nankai_not_flagged}"
            )
        })
        if nankai_not_flagged:
            score_total += 4.0

    except Exception as e:
        checks.append({"name": "frankfurt_eligibility_checks", "passed": False, "detail": str(e)})

    # ── CHECK 5: Frankfurt domestic advancement — top-3 only ─────────────────
    # Scores: Peking=3, Renmin=3, Fudan=2, CUPL=2, others random 0-2
    # Top-3 advance to international round
    # Peking and Renmin clearly top with wins=3. Third spot goes to Fudan (wins=2).
    # CUPL also wins=2 — need tiebreaker. Fudan is ranked higher in domestic_scores
    # since the data has same score, rely on the report to identify exactly 3 teams.
    try:
        advancement = frankfurt_section.get("domestic_advancement", {})
        advancing_to_intl = advancement.get("advancing_to_international", [])
        adv_unis = []
        for t in advancing_to_intl:
            if isinstance(t, dict):
                adv_unis.append(t.get("university", ""))
            elif isinstance(t, str):
                adv_unis.append(t)

        exactly_three = len(adv_unis) == 3
        pku_advanced = "Peking University" in adv_unis
        renmin_advanced = "Renmin University" in adv_unis

        checks.append({
            "name": "frankfurt_exactly_3_advance",
            "passed": exactly_three,
            "detail": (
                f"Exactly 3 teams (not 4, not 2) advance from domestic round to international. "
                f"Got {len(adv_unis)}: {adv_unis}"
            )
        })
        if exactly_three:
            score_total += 10.0

        checks.append({
            "name": "frankfurt_clear_top2_advance",
            "passed": pku_advanced and renmin_advanced,
            "detail": (
                f"Peking University (wins=3) and Renmin University (wins=3) must advance. "
                f"PKU: {pku_advanced}, Renmin: {renmin_advanced}. Advancing: {adv_unis}"
            )
        })
        if pku_advanced and renmin_advanced:
            score_total += 5.0

    except Exception as e:
        checks.append({"name": "frankfurt_domestic_advancement", "passed": False, "detail": str(e)})

    # ── CHECK 6: Frankfurt skeleton argument word limit violations ────────────
    # CUPL: 1400+1200 = 2600 > 2500 → VIOLATION
    # Nanjing University: 1400+1200 = 2600 → VIOLATION
    # Harbin Institute of Technology: 1400+1200 = 2600 → VIOLATION
    try:
        skeleton_section = frankfurt_section.get("skeleton_violations", [])
        violators = []
        for item in skeleton_section:
            if isinstance(item, dict):
                violators.append(item.get("university", ""))
            elif isinstance(item, str):
                violators.append(item)
        violators_str = " ".join(violators)

        cupl_violated = "CUPL" in violators_str
        nanjing_violated = "Nanjing" in violators_str
        harbin_violated = "Harbin" in violators_str

        checks.append({
            "name": "skeleton_cupl_violation_flagged",
            "passed": cupl_violated,
            "detail": f"CUPL submitted 2600 words (>2500 limit). Flagged: {cupl_violated}"
        })
        if cupl_violated:
            score_total += 3.0

        checks.append({
            "name": "skeleton_nanjing_violation_flagged",
            "passed": nanjing_violated,
            "detail": f"Nanjing University submitted 2600 words (>2500 limit). Flagged: {nanjing_violated}"
        })
        if nanjing_violated:
            score_total += 3.0

        checks.append({
            "name": "skeleton_harbin_violation_flagged",
            "passed": harbin_violated,
            "detail": f"Harbin Institute of Technology submitted 2600 words (>2500 limit). Flagged: {harbin_violated}"
        })
        if harbin_violated:
            score_total += 3.0

    except Exception as e:
        checks.append({"name": "skeleton_violations", "passed": False, "detail": str(e)})

    return checks, score_total


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks, raw_score = run_checks(workspace)
    max_score = 119.0
    normalized = round(min(raw_score / max_score, 1.0), 4)
    passed = normalized >= 0.60

    result = {
        "passed": passed,
        "score": normalized,
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()