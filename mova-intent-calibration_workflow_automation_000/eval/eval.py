import sys
import json
import re
from pathlib import Path

def load_file(workspace: str) -> tuple[str | None, str]:
    """Find and return the crystallized_intent.md content."""
    candidates = list(Path(workspace).rglob("crystallized_intent.md"))
    if not candidates:
        return None, "File crystallized_intent.md not found anywhere in workspace."
    # Prefer the one not inside a distractor folder
    for c in candidates:
        if "notes/leadership/intent_draft" not in str(c):
            return c.read_text(encoding="utf-8", errors="replace"), str(c)
    return candidates[0].read_text(encoding="utf-8", errors="replace"), str(candidates[0])


def check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": passed, "detail": detail}


def run_eval(workspace: str) -> dict:
    checks = []

    # ── Load file ─────────────────────────────────────────────────────────────
    try:
        content, location = load_file(workspace)
    except Exception as e:
        content, location = None, str(e)

    if content is None:
        checks.append(check("file_exists", False, location))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(check("file_exists", True, f"Found at: {location}"))

    # Normalize whitespace for robust matching
    text = content

    # ── Check 1: Header line ──────────────────────────────────────────────────
    header_ok = bool(re.search(r"CRYSTALLIZED INTENT\s*[—–-]", text, re.IGNORECASE))
    checks.append(check(
        "header_crystallized_intent",
        header_ok,
        "File must start with 'CRYSTALLIZED INTENT — [task title]'" if not header_ok else "Header found."
    ))

    # ── Check 2: All 11 required top-level sections present ───────────────────
    required_sections = [
        "INTENT",
        "PROBLEM FRAMING",
        "OUTCOME",
        "INPUTS / REALITY",
        "STRATEGY",
        "CONSTRAINTS",
        "DECISION RIGHTS",
        "VERIFICATION",
        "UNCERTAINTY",
        "COMMITMENT",
        "STATUS",
    ]
    missing_sections = []
    for sec in required_sections:
        # Allow section header with or without leading newline, case-insensitive
        pattern = re.compile(r"^\s*" + re.escape(sec) + r"\s*$", re.MULTILINE | re.IGNORECASE)
        if not pattern.search(text):
            missing_sections.append(sec)

    sections_ok = len(missing_sections) == 0
    checks.append(check(
        "all_required_sections",
        sections_ok,
        f"Missing sections: {missing_sections}" if missing_sections else "All 11 required sections present."
    ))

    # ── Check 3: DECISION RIGHTS has both required sub-lines ─────────────────
    has_human_controls = bool(re.search(r"Human controls\s*:", text, re.IGNORECASE))
    has_system_may = bool(re.search(r"System may\s*:", text, re.IGNORECASE))
    decision_rights_ok = has_human_controls and has_system_may
    detail_dr = []
    if not has_human_controls:
        detail_dr.append("Missing 'Human controls:' line under DECISION RIGHTS")
    if not has_system_may:
        detail_dr.append("Missing 'System may:' line under DECISION RIGHTS")
    checks.append(check(
        "decision_rights_substructure",
        decision_rights_ok,
        "; ".join(detail_dr) if detail_dr else "Both 'Human controls:' and 'System may:' present."
    ))

    # ── Check 4: STATUS uses exact checkbox format ────────────────────────────
    # Must contain: [ ] Crystallization complete — ready for execution or contract creation
    # OR: [ ] Blocked — must resolve:
    checkbox_complete = bool(re.search(
        r"\[\s*[xX ]?\s*\]\s*Crystallization complete\s*[—–-]\s*ready for execution or contract creation",
        text, re.IGNORECASE
    ))
    checkbox_blocked = bool(re.search(
        r"\[\s*[xX ]?\s*\]\s*Blocked\s*[—–-]\s*must resolve",
        text, re.IGNORECASE
    ))
    status_ok = checkbox_complete or checkbox_blocked
    checks.append(check(
        "status_checkbox_format",
        status_ok,
        "STATUS must contain '[ ] Crystallization complete — ready for execution or contract creation' or '[ ] Blocked — must resolve: [what]'" if not status_ok else "Valid STATUS checkbox found."
    ))

    # ── Check 5: COMMITMENT contains all 6 required elements ─────────────────
    # Required phrases (from SKILL.md Step 8 fixation):
    commitment_patterns = [
        (r"I consciously choose", "I consciously choose"),
        (r"I accept the constraints", "I accept the constraints"),
        (r"I accept the verification standard", "I accept the verification standard"),
        (r"I recognize the uncertainties", "I recognize the uncertainties"),
        (r"I understand that I am rejecting", "I understand that I am rejecting"),
        (r"I accept responsibility", "I accept responsibility"),
    ]
    missing_commitment = []
    for pattern, label in commitment_patterns:
        if not re.search(pattern, text, re.IGNORECASE):
            missing_commitment.append(label)

    commitment_ok = len(missing_commitment) == 0
    checks.append(check(
        "commitment_six_parts",
        commitment_ok,
        f"Missing commitment phrases: {missing_commitment}" if missing_commitment else "All 6 required commitment phrases present."
    ))

    # ── Check 6: User Fixation language present in body ───────────────────────
    # SKILL.md requires specific fixation formulas throughout the steps.
    # Check for at least 3 distinct fixation patterns:
    fixation_patterns = [
        (r"I choose .{3,} because for me", "Step fixation: 'I choose X because for me'"),
        (r"I (do not want merely|want specifically)", "Step 1 fixation: 'I do not want merely / I want specifically'"),
        (r"I accept that this task will be built on", "Step 2 fixation"),
        (r"I will consider this task complete if", "Step 4 fixation"),
        (r"No matter what solution is chosen", "Step 5 fixation"),
        (r"The human must decide", "Step 6 fixation: human must decide"),
        (r"The system may decide", "Step 6 fixation: system may decide"),
        (r"I understand that by choosing this I give up", "Fixation consequence language"),
        (r"I understand this task primarily as a task about", "Step 0 fixation"),
    ]
    found_fixations = []
    for pattern, label in fixation_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            found_fixations.append(label)

    fixation_ok = len(found_fixations) >= 3
    checks.append(check(
        "user_fixation_language",
        fixation_ok,
        f"Only {len(found_fixations)}/9 fixation patterns found. Need >= 3. Found: {found_fixations}" if not fixation_ok
        else f"Found {len(found_fixations)} fixation patterns: {found_fixations}"
    ))

    # ── Check 7: Domain relevance — must reference on-time delivery or routing ─
    domain_patterns = [
        r"on.time delivery",
        r"routing",
        r"last.mile",
        r"delivery performance",
        r"85%",
        r"dispatch",
        r"failed.*attempt",
        r"fleet",
    ]
    domain_hits = sum(1 for p in domain_patterns if re.search(p, text, re.IGNORECASE))
    domain_ok = domain_hits >= 3
    checks.append(check(
        "domain_relevance",
        domain_ok,
        f"Only {domain_hits} domain-relevant terms found (need >= 3). Content may be generic template." if not domain_ok
        else f"Domain relevance confirmed ({domain_hits} hits)."
    ))

    # ── Check 8: Non-trivial content length ───────────────────────────────────
    word_count = len(text.split())
    length_ok = word_count >= 400
    checks.append(check(
        "minimum_content_length",
        length_ok,
        f"Document has only {word_count} words. Minimum 400 required for substantive crystallization." if not length_ok
        else f"Document has {word_count} words — sufficient length."
    ))

    # ── Check 9: Date field present ───────────────────────────────────────────
    date_ok = bool(re.search(r"Date\s*:\s*\S+", text, re.IGNORECASE))
    checks.append(check(
        "date_field_present",
        date_ok,
        "Missing 'Date: [date]' field in header block." if not date_ok else "Date field present."
    ))

    # ── Check 10: Not the bad example / placeholder ───────────────────────────
    not_placeholder = not bool(re.search(r"Done\.\s*$", text.strip())) and \
                      "Goal: Improve on-time delivery rate." not in text and \
                      len(text.strip()) > 200
    checks.append(check(
        "not_placeholder_or_bad_example",
        not_placeholder,
        "Output appears to be a placeholder or copied from the bad example template." if not not_placeholder
        else "Content is not a placeholder."
    ))

    # ── Score calculation ─────────────────────────────────────────────────────
    weights = {
        "file_exists": 0.05,
        "header_crystallized_intent": 0.05,
        "all_required_sections": 0.20,
        "decision_rights_substructure": 0.15,
        "status_checkbox_format": 0.10,
        "commitment_six_parts": 0.15,
        "user_fixation_language": 0.10,
        "domain_relevance": 0.08,
        "minimum_content_length": 0.05,
        "date_field_present": 0.04,
        "not_placeholder_or_bad_example": 0.03,
    }

    score = 0.0
    for c in checks:
        score += weights.get(c["name"], 0.0) * (1.0 if c["passed"] else 0.0)

    # Overall pass: must pass the hard structural checks
    hard_checks = [
        "file_exists",
        "all_required_sections",
        "decision_rights_substructure",
        "status_checkbox_format",
        "commitment_six_parts",
    ]
    overall_passed = all(
        c["passed"] for c in checks if c["name"] in hard_checks
    )

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks,
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))