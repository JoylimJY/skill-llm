import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Locate the output file ───────────────────────────────────────────────
    # Accept any .md or .txt file named incident_timeline or incident_report
    candidates = list(workspace.rglob("incident_timeline.md")) + \
                 list(workspace.rglob("incident_timeline.txt")) + \
                 list(workspace.rglob("incident_report.md")) + \
                 list(workspace.rglob("incident_report.txt"))

    if not candidates:
        # Broader search fallback
        candidates = [p for p in workspace.rglob("*.md")
                      if any(kw in p.name.lower() for kw in ("incident", "timeline", "postmortem", "report"))]
        candidates += [p for p in workspace.rglob("*.txt")
                       if any(kw in p.name.lower() for kw in ("incident", "timeline", "postmortem", "report"))
                       and "draft" not in p.name.lower()
                       and "notes" not in p.name.lower()
                       and str(p).find("raw_logs") == -1]

    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False,
                        "detail": "No incident timeline output file found in workspace."}]
        }

    # Pick the most recently modified candidate
    output_file = max(candidates, key=lambda p: p.stat().st_mtime)

    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False,
                        "detail": f"Could not read file {output_file}: {e}"}]
        }

    content_lower = content.lower()
    lines = [l for l in content.splitlines() if l.strip()]

    # ── CHECK 1: File exists and is non-trivial ──────────────────────────────
    file_ok = len(content.strip()) >= 300
    checks.append({
        "name": "file_exists_and_substantial",
        "passed": file_ok,
        "detail": f"File found at {output_file} with {len(content.strip())} chars. Need >=300."
    })
    if file_ok:
        total_score += 0.05

    # ── CHECK 2: Situation Summary present AND <= 5 lines ───────────────────
    # Look for a section header containing "situation" or "summary"
    situation_section_found = False
    situation_line_count = 0
    try:
        # Find the situation/summary section and count its body lines
        section_pattern = re.compile(
            r'(?:situation\s*summary|summary|situation)[^\n]*\n((?:(?!#+\s|\Z).+\n?)*)',
            re.IGNORECASE
        )
        match = section_pattern.search(content)
        if match:
            body = match.group(1).strip()
            body_lines = [l for l in body.splitlines() if l.strip()]
            situation_line_count = len(body_lines)
            situation_section_found = situation_line_count <= 5 and situation_line_count >= 1
    except Exception:
        situation_section_found = False

    checks.append({
        "name": "situation_summary_max_5_lines",
        "passed": situation_section_found,
        "detail": (f"Situation summary body has {situation_line_count} lines. Must be 1-5 lines."
                   if situation_section_found or situation_line_count > 0
                   else "No situation summary section detected.")
    })
    if situation_section_found:
        total_score += 0.15

    # ── CHECK 3: Top Findings present and contain ranking / impact language ──
    findings_ok = False
    try:
        has_findings_section = bool(re.search(
            r'(?:top\s+findings?|findings?|key\s+findings?)[^\n]*\n', content, re.IGNORECASE))
        # Check for ranking evidence: numbered list (1. 2. 3.) or "impact" language
        ranked_items = re.findall(r'^\s*[1-9]\d*[\.\)]\s+.+', content, re.MULTILINE)
        has_impact_language = bool(re.search(
            r'\b(impact|severity|critical|high|medium|low|p[0-9]|sev-[0-9])\b',
            content, re.IGNORECASE))
        findings_ok = has_findings_section and (len(ranked_items) >= 2 or has_impact_language)
    except Exception:
        findings_ok = False

    checks.append({
        "name": "top_findings_ranked_by_impact",
        "passed": findings_ok,
        "detail": ("Top findings section present with ranking/impact indicators."
                   if findings_ok
                   else "Missing top findings section or findings are not ranked by impact.")
    })
    if findings_ok:
        total_score += 0.15

    # ── CHECK 4: Action plan with BOTH "today" AND "this week" sub-sections ──
    action_plan_ok = False
    try:
        has_today = bool(re.search(r'\btoday\b', content, re.IGNORECASE))
        has_this_week = bool(re.search(r'\bthis\s+week\b', content, re.IGNORECASE))
        has_action_section = bool(re.search(
            r'(?:action\s+plan|actions?|next\s+steps?)[^\n]*\n', content, re.IGNORECASE))
        action_plan_ok = has_action_section and has_today and has_this_week
    except Exception:
        action_plan_ok = False

    checks.append({
        "name": "action_plan_today_and_this_week",
        "passed": action_plan_ok,
        "detail": ("Action plan has both 'today' and 'this week' sub-sections."
                   if action_plan_ok
                   else "Action plan missing or lacks explicit 'today'/'this week' split.")
    })
    if action_plan_ok:
        total_score += 0.15

    # ── CHECK 5: Risks + Mitigations section present ─────────────────────────
    risks_ok = False
    try:
        has_risks = bool(re.search(
            r'(?:risks?\s*\+?\s*mitigations?|risks?\s+and\s+mitigations?|mitigation)[^\n]*\n',
            content, re.IGNORECASE))
        risks_ok = has_risks
    except Exception:
        risks_ok = False

    checks.append({
        "name": "risks_and_mitigations_section",
        "passed": risks_ok,
        "detail": ("Risks + mitigations section found."
                   if risks_ok
                   else "No risks/mitigations section detected.")
    })
    if risks_ok:
        total_score += 0.10

    # ── CHECK 6: Fallback plan present (Quality Gate) ────────────────────────
    fallback_ok = False
    try:
        fallback_ok = bool(re.search(
            r'\b(fallback|contingency|if\s+primary\s+(plan\s+)?fails?|backup\s+plan|alternative\s+plan)\b',
            content, re.IGNORECASE))
    except Exception:
        fallback_ok = False

    checks.append({
        "name": "fallback_plan_present",
        "passed": fallback_ok,
        "detail": ("Fallback/contingency plan mentioned in document."
                   if fallback_ok
                   else "No fallback plan found. Quality gate requires explicit fallback.")
    })
    if fallback_ok:
        total_score += 0.10

    # ── CHECK 7: Owner + ETA per next step (Quality Gate) ────────────────────
    owner_eta_ok = False
    try:
        # Look for owner-like patterns (names or roles) alongside ETA-like patterns
        has_owner = bool(re.search(
            r'\b(owner|assigned\s+to|responsible|@\w+|alice|bob|charlie|sre|oncall|on-call)\b',
            content, re.IGNORECASE))
        has_eta = bool(re.search(
            r'\b(eta|by\s+(eod|tomorrow|monday|friday|\d{4}-\d{2}-\d{2})|due\s+(by|date)|deadline|within\s+\d+\s+(hour|day|week))\b',
            content, re.IGNORECASE))
        owner_eta_ok = has_owner and has_eta
    except Exception:
        owner_eta_ok = False

    checks.append({
        "name": "owner_and_eta_per_next_step",
        "passed": owner_eta_ok,
        "detail": ("Owner and ETA patterns found in document."
                   if owner_eta_ok
                   else "Missing owner assignment and/or ETA for next steps. Quality gate requires both.")
    })
    if owner_eta_ok:
        total_score += 0.10

    # ── CHECK 8: Checklist or exact commands present ─────────────────────────
    checklist_ok = False
    try:
        # Checkbox syntax or numbered action items or code block with commands
        has_checkbox = bool(re.search(r'- \[[ x]\]', content))
        has_code_block = bool(re.search(r'```', content))
        # Or at least 3 numbered action items
        numbered = re.findall(r'^\s*[1-9]\d*[\.\)]\s+.{10,}', content, re.MULTILINE)
        checklist_ok = has_checkbox or has_code_block or len(numbered) >= 3
    except Exception:
        checklist_ok = False

    checks.append({
        "name": "checklist_or_commands_present",
        "passed": checklist_ok,
        "detail": ("Checklist or commands/code block present."
                   if checklist_ok
                   else "No checklist (- [ ]) or code block or numbered items >= 3 found.")
    })
    if checklist_ok:
        total_score += 0.05

    # ── CHECK 9: Evidence-backed: references actual data from inputs ──────────
    evidence_ok = False
    try:
        # Must reference specific artifacts from the raw inputs
        has_deploy_ref = bool(re.search(r'd4e5f6|d3c4b5|v2\.4\.[01]', content))
        has_metric_ref = bool(re.search(r'(db.?pool|connection.?pool|pool.?size|pool.?exhausted)', content, re.IGNORECASE))
        has_slo_or_duration = bool(re.search(
            r'(26\s*min|02:29|02:55|76\s*%|99\.9\s*%|SLO\s*breach|TICK-88)', content, re.IGNORECASE))
        evidence_ok = (has_deploy_ref or has_metric_ref) and has_slo_or_duration
    except Exception:
        evidence_ok = False

    checks.append({
        "name": "evidence_backed_with_real_data",
        "passed": evidence_ok,
        "detail": ("Document references specific evidence from incident data (deploy IDs, metrics, duration, SLO)."
                   if evidence_ok
                   else "Document lacks specific evidence from raw logs (deploy hash, pool metrics, SLO breach details).")
    })
    if evidence_ok:
        total_score += 0.10

    # ── CHECK 10: Explicit assumptions/tradeoffs stated (Quality Gate) ───────
    assumptions_ok = False
    try:
        assumptions_ok = bool(re.search(
            r'\b(assumption|assumed|unknown|tradeoff|trade-off|caveat|limitation|pending|not\s+confirmed)\b',
            content, re.IGNORECASE))
    except Exception:
        assumptions_ok = False

    checks.append({
        "name": "explicit_assumptions_or_tradeoffs",
        "passed": assumptions_ok,
        "detail": ("Explicit assumptions or tradeoffs/unknowns stated."
                   if assumptions_ok
                   else "No explicit assumptions or tradeoffs found. Quality gate requires them.")
    })
    if assumptions_ok:
        total_score += 0.05

    # ── Final pass/fail ──────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    # Must pass at least 7/10 checks, including the two hardest proprietary ones
    must_pass = [
        "situation_summary_max_5_lines",
        "action_plan_today_and_this_week",
        "fallback_plan_present",
        "owner_and_eta_per_next_step",
    ]
    hard_gates_passed = all(
        any(c["name"] == mp and c["passed"] for c in checks) for mp in must_pass
    )
    overall_passed = passed_checks >= 7 and hard_gates_passed and total_score >= 0.65

    return {
        "passed": overall_passed,
        "score": round(min(total_score, 1.0), 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "invocation", "passed": False,
                                      "detail": "No workspace path provided."}]}))
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))