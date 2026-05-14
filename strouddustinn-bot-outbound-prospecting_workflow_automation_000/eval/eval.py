import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0

    # ── 1. Find the output file ────────────────────────────────────────────────
    candidates = list(Path(workspace).rglob("bridgepoint_outreach.md"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found {len(candidates)} file(s) named bridgepoint_outreach.md" if file_found else "No file named bridgepoint_outreach.md found anywhere in workspace"
    })
    if not file_found:
        return {"passed": False, "score": 0.0, "checks": checks}

    try:
        content = candidates[0].read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_readable", "passed": True, "detail": f"File read successfully ({len(content)} chars)"})
    total_score += 0.05

    content_lower = content.lower()

    # ── 2. Must be wrapped in a markdown code block ────────────────────────────
    has_markdown_block = bool(re.search(r'```', content))
    checks.append({
        "name": "markdown_code_block_present",
        "passed": has_markdown_block,
        "detail": "Draft email is wrapped in a markdown ``` code block" if has_markdown_block else "Draft email is NOT enclosed in a markdown ``` code block as required"
    })
    if has_markdown_block:
        total_score += 0.10

    # ── 3. Decision-maker name identified (Marcus Holt) ───────────────────────
    has_contact_name = "marcus holt" in content_lower
    checks.append({
        "name": "decision_maker_identified",
        "passed": has_contact_name,
        "detail": "Decision-maker 'Marcus Holt' found in output" if has_contact_name else "Decision-maker name 'Marcus Holt' not found; contact_finder phase likely incomplete"
    })
    if has_contact_name:
        total_score += 0.15

    # ── 4. Decision-maker title present (CEO or Founder) ─────────────────────
    has_title = bool(re.search(r'\b(ceo|chief executive|founder)\b', content_lower))
    checks.append({
        "name": "decision_maker_title_present",
        "passed": has_title,
        "detail": "CEO/Founder title found alongside contact name" if has_title else "No CEO or Founder title found; title discovery incomplete"
    })
    if has_title:
        total_score += 0.05

    # ── 5. At least 3 company-specific facts from research ────────────────────
    # Facts derivable only from the mock pages:
    fact_patterns = [
        (r'\$14\s*[mM]|14\s*million|cascade river bridge', "Cascade River Bridge $14M contract"),
        (r'1998|founded in 1998|since 1998', "Founded in 1998"),
        (r'87\s*(licensed\s*)?engineers?|87[\s-]person', "87 licensed engineers/person firm"),
        (r'portland|pacific northwest', "Portland/Pacific Northwest location"),
        (r'22\s*%?\s*revenue|22 percent revenue', "22% revenue increase in 2023"),
        (r'9\s*%?\s*billable|9 percent billable|billable hours', "9% billable hours lost to delays"),
        (r'spreadsheet|legacy.*project|ms project|siloed communication', "Spreadsheet/legacy project management pain point"),
        (r'18[\s-]month|4\s*field\s*teams?', "18-month timeline / 4 field teams"),
        (r'seismic retrofit|bridge design|urban infrastructure', "Core service: seismic retrofit / bridge design"),
        (r'74\s*%?\s*repeat|74 percent repeat', "74% repeat client revenue"),
        (r'environmental (consulting|division)|12 new hires', "Environmental division / 12 new hires"),
    ]

    matched_facts = []
    for pattern, description in fact_patterns:
        if re.search(pattern, content_lower):
            matched_facts.append(description)

    has_three_facts = len(matched_facts) >= 3
    checks.append({
        "name": "minimum_three_specific_facts",
        "passed": has_three_facts,
        "detail": f"Found {len(matched_facts)} company-specific facts: {matched_facts}" if matched_facts else "Fewer than 3 company-specific facts found; research_auditor phase insufficient"
    })
    if has_three_facts:
        total_score += 0.25

    # ── 6. Hybrid tone: relationship-first opener ──────────────────────────────
    # Relationship-first signals: congratulat*, impressed, noticed, saw, read, exciting
    relationship_opener = bool(re.search(
        r'\b(congratulat|impressed|noticed|saw your|read about|exciting|saw that|heard about)\b',
        content_lower
    ))
    checks.append({
        "name": "relationship_first_opener",
        "passed": relationship_opener,
        "detail": "Relationship-first opener detected (e.g., congratulations, noticed, saw that...)" if relationship_opener else "No relationship-first opener detected; hybrid tone requirement not met"
    })
    if relationship_opener:
        total_score += 0.15

    # ── 7. Evidence-backed revenue-loss / pain point angle ────────────────────
    revenue_loss_angle = bool(re.search(
        r'\b(cost|losing|loss|revenue|billable|inefficien|delay|overhead|pain|struggle|challenge|risk|impact)\b',
        content_lower
    ))
    checks.append({
        "name": "revenue_loss_angle_present",
        "passed": revenue_loss_angle,
        "detail": "Revenue-loss or pain-point angle found in email body" if revenue_loss_angle else "No evidence-backed revenue-loss angle found; hybrid tone requirement incomplete"
    })
    if revenue_loss_angle:
        total_score += 0.10

    # ── 8. Email not sent (no 'sent', 'send' action verbs claiming delivery) ──
    # Check the file doesn't claim the email was actually sent
    claims_sent = bool(re.search(
        r'\b(email (has been |was |is )(sent|delivered|dispatched)|(i |we )sent (the |this |an )?email)\b',
        content_lower
    ))
    email_not_sent = not claims_sent
    checks.append({
        "name": "email_not_actually_sent",
        "passed": email_not_sent,
        "detail": "File correctly contains a draft only (no claim of sending)" if email_not_sent else "File claims the email was sent — violates copilot-mode / draft-only requirement"
    })
    if email_not_sent:
        total_score += 0.05

    # ── 9. Subject line present ───────────────────────────────────────────────
    has_subject = bool(re.search(r'\bsubject\s*:', content_lower))
    checks.append({
        "name": "email_subject_line_present",
        "passed": has_subject,
        "detail": "Email subject line found" if has_subject else "No subject line (Subject:) found in draft"
    })
    if has_subject:
        total_score += 0.05

    # ── 10. Company name present ──────────────────────────────────────────────
    has_company = "bridgepoint" in content_lower
    checks.append({
        "name": "company_name_in_draft",
        "passed": has_company,
        "detail": "Company name 'Bridgepoint' found in draft" if has_company else "Company name not found in draft"
    })
    if has_company:
        total_score += 0.05

    # ── Final verdict ─────────────────────────────────────────────────────────
    critical_checks = [
        "output_file_exists",
        "minimum_three_specific_facts",
        "decision_maker_identified",
        "markdown_code_block_present",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    passed = critical_passed and total_score >= 0.55

    return {
        "passed": passed,
        "score": round(min(total_score, 1.0), 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))