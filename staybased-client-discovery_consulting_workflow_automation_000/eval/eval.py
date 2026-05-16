import sys
import json
import re
from pathlib import Path

def find_report(workspace: str) -> Path | None:
    candidates = list(Path(workspace).rglob("discovery_report.md"))
    if not candidates:
        return None
    # Prefer file in artifacts/ if multiple
    for c in candidates:
        if "artifacts" in str(c):
            return c
    return candidates[0]

def check_passes(text: str) -> list[dict]:
    checks = []
    t = text.lower()

    # -------------------------------------------------------
    # CHECK 1: Five discovery phases present
    # -------------------------------------------------------
    phase_keywords = [
        (["phase 1", "context", "warm-up", "warm up"], "Phase 1: Context"),
        (["phase 2", "problem diagnosis", "problem diag"], "Phase 2: Problem Diagnosis"),
        (["phase 3", "desired outcome", "success look"], "Phase 3: Desired Outcome"),
        (["phase 4", "qualification", "fit check", "qualify"], "Phase 4: Qualification"),
        (["phase 5", "bridge", "next step", "proposal"], "Phase 5: Bridge/Next Steps"),
    ]
    phases_found = []
    for keywords, label in phase_keywords:
        found = any(kw in t for kw in keywords)
        phases_found.append(found)

    phases_passed = sum(phases_found) >= 4
    checks.append({
        "name": "Five discovery phases addressed (at least 4 of 5)",
        "passed": phases_passed,
        "detail": f"Phases detected: {sum(phases_found)}/5. Labels checked: {[ph[1] for ph,r in zip(phase_keywords, phases_found) if r]}"
    })

    # -------------------------------------------------------
    # CHECK 2: Red flags identified — must cite at least 3 specific ones
    # The skill has very specific disqualification signals
    # -------------------------------------------------------
    red_flag_signals = {
        "two_fired_contractors": [
            "two contractor", "2 contractor", "fired.*contractor", "contractor.*couldn't", 
            "contractor.*couldnt", "previous contractor", "prior contractor",
            "let go.*contractor", "contractor.*fail", "feb.*contractor", "april.*contractor",
            "pattern.*suspicious", "contractors failed"
        ],
        "unrealistic_timeline": [
            "end of.*week", "4 business day", "48 hour", "two week", "unrealistic.*timeline",
            "timeline.*unrealistic", "rushed", "need.*done.*week", "week.*timeline",
            "two weeks max", "urgent.*timeline", "impossible timeline"
        ],
        "scope_creep_no_budget": [
            "scope creep", "scope.*expand", "expand.*scope", "dashboard.*budget",
            "snowflake.*budget", "figure out.*later", "details later", "no budget increase",
            "budget.*unchanged", "scope.*without.*budget", "metabase.*budget",
            "additional.*scope"
        ],
        "budget_mismatch": [
            "\\$800", "800.*budget", "budget.*800", "low budget", "budget.*low",
            "budget.*unrealistic", "underfunded", "budget.*mismatch", "misaligned.*budget",
            "budget.*scope", "scope.*budget"
        ],
        "not_decision_maker": [
            "not.*decision maker", "cto.*approval", "ceo.*approval", "maya.*approv",
            "decision.*chain", "multiple.*approv", "above.*1000", "above.*\\$1",
            "sign.off.*cto", "kartik.*not.*decision", "approval.*required"
        ],
        "free_work_test": [
            "prove yourself", "test task", "free.*work", "free work", "test.*fit",
            "small test", "prove.*fit", "free pilot"
        ],
        "no_clear_success_metric": [
            "no.*metric", "metric.*unclear", "cant.*articulate", "couldn't.*articulate",
            "just.*works", "doesn't know", "doesnt know", "no kpi", "vague.*success",
            "undefined.*success", "no.*kpi", "unclear.*success", "no success metric",
            "couldnt.*give.*metric", "no.*measur"
        ],
    }

    found_red_flags = []
    for flag_name, patterns in red_flag_signals.items():
        for pattern in patterns:
            try:
                if re.search(pattern, t, re.IGNORECASE):
                    found_red_flags.append(flag_name)
                    break
            except re.error:
                if pattern in t:
                    found_red_flags.append(flag_name)
                    break

    red_flags_count = len(set(found_red_flags))
    red_flags_passed = red_flags_count >= 3
    checks.append({
        "name": "Red flags identified (at least 3 specific disqualification signals)",
        "passed": red_flags_passed,
        "detail": f"Red flags found: {red_flags_count}/7. Flags: {list(set(found_red_flags))}"
    })

    # -------------------------------------------------------
    # CHECK 3: Explicit go/no-go or fit recommendation present
    # -------------------------------------------------------
    recommendation_patterns = [
        r"do not (proceed|bid|engage|recommend|take|accept)",
        r"(decline|walk away|pass on|not recommend|disqualif)",
        r"(not a good fit|poor fit|bad fit|weak fit)",
        r"(no-go|no go)\b",
        r"(recommend against|advise against)",
        r"(proceed with caution|caution.*proceed)",
        r"(qualify.*out|out.*qualify)",
        r"(green.*light|red.*light)",
        r"recommendation.*no",
        r"decision.*decline",
        r"(should not|shouldn't) (engage|take|bid|proceed)",
    ]
    go_nogo_found = any(re.search(p, t, re.IGNORECASE) for p in recommendation_patterns)
    checks.append({
        "name": "Explicit go/no-go recommendation present",
        "passed": go_nogo_found,
        "detail": "Report must contain a clear fit recommendation (proceed, decline, or caution)."
    })

    # -------------------------------------------------------
    # CHECK 4: Problem statement in the exact 3-sentence format
    # Must follow: [Client] is a [type] struggling with [problem] / costing them / they need
    # -------------------------------------------------------
    problem_stmt_patterns = [
        r"(snapshelf|kartik).{0,80}(is a|are a).{0,150}(struggling with|facing|dealing with)",
        r"(costing|cost).{0,100}(time|money|customer|client|churn|\$|hour)",
        r"(they need|needs).{0,100}(by|within|budget|range|\$)",
    ]
    problem_stmt_hits = sum(
        1 for p in problem_stmt_patterns if re.search(p, t, re.IGNORECASE | re.DOTALL)
    )
    problem_stmt_passed = problem_stmt_hits >= 2
    checks.append({
        "name": "Post-discovery problem statement present (3-sentence format with client, cost, and need)",
        "passed": problem_stmt_passed,
        "detail": f"Problem statement format hits: {problem_stmt_hits}/3. Must include: who client is, quantified cost, and solution need with timeline/budget."
    })

    # -------------------------------------------------------
    # CHECK 5: Scope creep specifically identified as disqualifier
    # Must reference the "we'll figure out details later" or expanding scope
    # without budget discussion — a specific skill-doc disqualifier
    # -------------------------------------------------------
    scope_creep_patterns = [
        r"scope creep",
        r"scope.*expand",
        r"(dashboard|snowflake|metabase|migration).{0,100}(no|without|no mention|no additional|unchanged).{0,50}budget",
        r"budget.{0,100}(scope|expand|dashboard|snowflake|metabase|migration)",
        r"figure.*out.*later",
        r"details.*later",
        r"expand.*without.*budget",
        r"(added|additional).{0,80}scope.{0,80}(no|without|same|unchanged).{0,30}budget",
    ]
    scope_creep_found = any(re.search(p, t, re.IGNORECASE) for p in scope_creep_patterns)
    checks.append({
        "name": "Scope creep without budget increase explicitly flagged",
        "passed": scope_creep_found,
        "detail": "The report must flag that scope expanded (dashboards, Snowflake migration) without any budget increase — a key disqualification signal from the skill framework."
    })

    # -------------------------------------------------------
    # CHECK 6: Urgency assessment addresses unrealistic timeline
    # -------------------------------------------------------
    timeline_patterns = [
        r"(end of.*week|4 business day|four business day|two week|2 week).{0,200}(unrealistic|rush|concern|red flag|problem|impossible|caution|too.*short|challeng)",
        r"(unrealistic|rush|too.*short|impossible|challeng).{0,200}(timeline|week|deadline)",
        r"timeline.{0,100}(red flag|concern|unrealistic|risk|caution)",
        r"(need.*done.*by|by end of week).{0,50}(unrealistic|concern|issue|problem|flag)",
        r"week.*deadline.{0,100}(concern|risk|red|flag|unrealistic)",
    ]
    timeline_found = any(re.search(p, t, re.IGNORECASE | re.DOTALL) for p in timeline_patterns)
    checks.append({
        "name": "Unrealistic timeline identified as a concern or red flag",
        "passed": timeline_found,
        "detail": "The two-week (originally 4-day) timeline must be flagged as unrealistic or a concern per the skill's 'we need this by tomorrow' red flag."
    })

    # -------------------------------------------------------
    # CHECK 7: Two prior contractor failures flagged as suspicious / red flag
    # Skill doc: "Our last 3 vendors couldn't do this" = red flag; problem may not be vendors
    # -------------------------------------------------------
    contractor_patterns = [
        r"(two|2|multiple|previous|prior).{0,50}(contractor|vendor).{0,150}(suspicious|red flag|concern|pattern|problem.*them|them.*problem|flag|caution|issue)",
        r"(contractor|vendor).{0,50}(fail|couldn't|couldnt|couldn).{0,100}(suspicious|pattern|concern|flag|red)",
        r"(pattern|suspicious).{0,100}(contractor|vendor)",
        r"(fired|let go|replaced).{0,100}(contractor|vendor).{0,100}(suspicious|concern|red|flag|pattern)",
        r"(problem|issue).{0,50}(may|might|could).{0,50}(be|lie).{0,50}(them|client|snapshelf|kartik|internally)",
        r"(client.{0,30}problem|problem.{0,30}client).{0,100}(contractor|vendor)",
    ]
    contractor_found = any(re.search(p, t, re.IGNORECASE | re.DOTALL) for p in contractor_patterns)
    checks.append({
        "name": "Prior contractor failures flagged as suspicious (problem may be the client)",
        "passed": contractor_found,
        "detail": "Two prior contractors failed. Skill doc explicitly flags 'our last 3 vendors couldn't do this' as a red flag suggesting the problem may be the client, not the vendors."
    })

    # -------------------------------------------------------
    # CHECK 8: Recommended next step mentioned (a concrete action or note that one was NOT set)
    # Skill: "Never end a discovery call without a clear next step with a date"
    # -------------------------------------------------------
    next_step_patterns = [
        r"(next step|follow.up|follow up).{0,200}(schedule|send|proposal|call|meeting|date|tuesday|friday|week)",
        r"(no next step|next step.*not set|missing.*next step|next step.*missing|failed.*next step)",
        r"(recommend|should).{0,50}(schedule|set|establish|define).{0,50}(next step|follow.up|call|meeting)",
        r"(follow.up|next step).{0,100}(by|before|on|date|set|schedule)",
        r"(clear next step|next step.*date|date.*next step)",
        r"(action item|action required).{0,100}(next step|follow.up|schedule)",
        r"next step.{0,300}(not.{0,20}set|missing|undefined|lacking|no.{0,20}clear)",
    ]
    next_step_found = any(re.search(p, t, re.IGNORECASE | re.DOTALL) for p in next_step_patterns)
    checks.append({
        "name": "Next step assessment present (or flagged as absent from call)",
        "passed": next_step_found,
        "detail": "Skill mandates a clear next step with a date. Report must either recommend one or flag that the call ended without one (which is a significant mistake per the skill doc)."
    })

    # -------------------------------------------------------
    # CHECK 9: Quantified business impact from call notes referenced
    # (stockouts → customer churn, 4-6 hrs manual reconciliation, 3-4 enterprise clients lost)
    # -------------------------------------------------------
    impact_patterns = [
        r"(stockout|stock.out)",
        r"(churn|client.*lost|lost.*client|enterprise.*client)",
        r"(4.{0,5}6 hour|four.{0,5}six hour|manual.*reconcili|reconcili.*manual)",
        r"(3.{0,5}4 enterprise|enterprise.*client.*lost|lost.*enterprise)",
        r"(manual.*fix|ops.*team|operations.*team).{0,100}(hour|time|burden)",
        r"(pipeline.*fail|fail.*pipeline).{0,100}(week|per week|2.{0,3}3)",
    ]
    impact_hits = sum(1 for p in impact_patterns if re.search(p, t, re.IGNORECASE))
    impact_passed = impact_hits >= 2
    checks.append({
        "name": "Quantified business impact from call notes referenced (stockouts, churn, manual hours)",
        "passed": impact_passed,
        "detail": f"Impact signals found: {impact_hits}/6. Must reference concrete impacts like stockouts, churn, or 4-6 hr manual reconciliation from the call notes."
    })

    # -------------------------------------------------------
    # CHECK 10: Report is in workspace/artifacts/discovery_report.md
    # (Checked externally, but also validate the file is non-trivial)
    # -------------------------------------------------------
    word_count = len(text.split())
    substantial_passed = word_count >= 200
    checks.append({
        "name": "Report is substantive (at least 200 words)",
        "passed": substantial_passed,
        "detail": f"Word count: {word_count}. A real discovery report requires substantial analysis."
    })

    return checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

    all_checks = []

    # --- Check 0: File exists ---
    report_path = find_report(workspace)
    file_exists = report_path is not None
    all_checks.append({
        "name": "discovery_report.md exists in workspace",
        "passed": file_exists,
        "detail": f"Found at: {report_path}" if file_exists else "File not found anywhere in workspace. Expected: workspace/artifacts/discovery_report.md"
    })

    if not file_exists:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": all_checks
        }
        print(json.dumps(result, indent=2))
        return

    # Read file
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        all_checks.append({
            "name": "File readable",
            "passed": False,
            "detail": f"Error reading file: {e}"
        })
        result = {
            "passed": False,
            "score": 0.0,
            "checks": all_checks
        }
        print(json.dumps(result, indent=2))
        return

    # Run all content checks
    content_checks = check_passes(content)
    all_checks.extend(content_checks)

    # Calculate score
    passed_count = sum(1 for c in all_checks if c["passed"])
    total_count = len(all_checks)
    score = passed_count / total_count

    # Overall pass: file exists + at least 8/11 checks pass
    overall_passed = file_exists and passed_count >= 8

    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": all_checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()