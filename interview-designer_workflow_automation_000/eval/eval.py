import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str) -> dict:
    workspace = Path(workspace_dir)
    checks = []

    # ── Helper ────────────────────────────────────────────────────────────────
    def add_check(name: str, passed: bool, detail: str):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ── Locate the output file ────────────────────────────────────────────────
    candidates = list(workspace.rglob("interview_guide_candidate_chen.md"))
    if not candidates:
        add_check("output_file_exists", False,
                  "File 'interview_guide_candidate_chen.md' not found anywhere in workspace.")
        return {"passed": False, "score": 0.0, "checks": checks}

    # Use the most recently modified one if multiple
    guide_path = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    add_check("output_file_exists", True, f"Found at: {guide_path.relative_to(workspace)}")

    try:
        content = guide_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        add_check("file_readable", False, f"Could not read file: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}

    content_lower = content.lower()

    # ── CHECK 1: Scorecard section exists with Mission ────────────────────────
    has_scorecard = bool(re.search(r'scorecard', content_lower))
    has_mission = bool(re.search(r'\bmission\b', content_lower))
    add_check(
        "scorecard_section_with_mission",
        has_scorecard and has_mission,
        f"Scorecard present: {has_scorecard}. Mission present: {has_mission}."
    )

    # ── CHECK 2: Scorecard has 3-5 measurable Outcomes ───────────────────────
    outcome_matches = re.findall(
        r'outcome|measurable result|12.month|within 12',
        content_lower
    )
    # Also look for a table or numbered list of outcomes
    outcome_rows = re.findall(r'(?m)^\s*[\|•\-\*\d]+\s*.{10,}(?:metric|measur|deliverable|kpi|target|result|advance|filing|IND|throughput|pipeline|team|publi)',
                              content_lower)
    has_outcomes = len(outcome_matches) >= 1 and (
        len(outcome_rows) >= 2 or
        len(re.findall(r'(?m)^\s*\|.*\|', content)) >= 3 or
        len(re.findall(r'(?m)^\s*[\d]+[.)]\s+.{15,}', content)) >= 2
    )
    add_check(
        "scorecard_outcomes_defined",
        has_outcomes,
        f"Outcome keyword hits: {len(outcome_matches)}. Structured outcome rows found: {len(outcome_rows)}."
    )

    # ── CHECK 3: Scorecard has Competencies ──────────────────────────────────
    has_competencies = bool(re.search(r'competenc', content_lower))
    add_check(
        "scorecard_competencies_defined",
        has_competencies,
        f"Competencies section present: {has_competencies}."
    )

    # ── CHECK 4: Forensic scan section with Red Flags ────────────────────────
    has_red_flags = bool(re.search(r'red\s*flag', content_lower))
    has_forensic = bool(re.search(r'forensic|scan|gap', content_lower))
    add_check(
        "forensic_scan_with_red_flags",
        has_red_flags and has_forensic,
        f"[Red Flags] present: {has_red_flags}. Forensic/scan/gap language: {has_forensic}."
    )

    # ── CHECK 5: Green Signals section present ────────────────────────────────
    has_green_signals = bool(re.search(r'green\s*signal', content_lower))
    add_check(
        "green_signals_section_present",
        has_green_signals,
        f"[Green Signals] section present: {has_green_signals}. "
        "An agent that only lists concerns without verification targets fails this check."
    )

    # ── CHECK 6: At least one proprietary heuristic applied ──────────────────
    heuristics_found = []
    if re.search(r'too good to be true|too\-good\-to\-be\-true', content_lower):
        heuristics_found.append("Too Good To Be True")
    if re.search(r'passenger\s*vs\s*driver|passenger.*driver|driver.*passenger', content_lower):
        heuristics_found.append("Passenger vs Driver")
    if re.search(r'first\s*principles?\s*heuristic|first.principles.*jargon|jargon.*first.principles', content_lower):
        heuristics_found.append("First Principles")
    # Softer match: at least mention of the concepts
    if not heuristics_found:
        if re.search(r'individual.*contribution|team.*halo|big.*company.*halo|pfizer.*team|whose.*idea', content_lower):
            heuristics_found.append("Passenger vs Driver (conceptual)")
        if re.search(r'verify.*claim|skeptic|too perfect|inflated', content_lower):
            heuristics_found.append("Too Good To Be True (conceptual)")
    add_check(
        "proprietary_heuristics_applied",
        len(heuristics_found) >= 1,
        f"Heuristics identified: {heuristics_found}. "
        "Must apply at least one of the three named forensic heuristics from SKILL.md."
    )

    # ── CHECK 7: Pressure Test questions (Forensic STAR) ─────────────────────
    has_pressure = bool(re.search(
        r'pressure\s*test|forensic\s*star|star\s*follow|behavioral.*question|'
        r'tell me about a time|walk me through|describe a situation|'
        r'specific.*example.*when|when.*you.*led|what.*exact',
        content_lower
    ))
    # Also accept if there's a section labelled Section A or Pressure Test Scripts
    has_pressure_section = bool(re.search(
        r'section\s*a|pressure test script|forensic\s*follow', content_lower
    ))
    add_check(
        "pressure_test_questions_present",
        has_pressure or has_pressure_section,
        f"Pressure test language present: {has_pressure}. "
        f"Pressure test section header present: {has_pressure_section}."
    )

    # ── CHECK 8: Future Simulation / Performance Problem ─────────────────────
    has_simulation = bool(re.search(
        r'future\s*simulation|performance\s*problem|simulation|scenario|'
        r'if you join|first week|first 30|first 90|'
        r'IND.*obstacle|RNA.*pipeline.*challenge|ramp.*up',
        content_lower
    ))
    has_simulation_section = bool(re.search(
        r'section\s*b|future simulation|performance problem', content_lower
    ))
    # Must reference a specific business context (not generic)
    has_specific_context = bool(re.search(
        r'IND|RNA|throughput|novattera|HPC|Q[1-4]|series\s*[CD]|drug\s*discovery|pipeline',
        content_lower
    ))
    add_check(
        "future_simulation_with_specific_context",
        (has_simulation or has_simulation_section) and has_specific_context,
        f"Simulation present: {has_simulation or has_simulation_section}. "
        f"Specific business context present: {has_specific_context}. "
        "A generic 'where do you see yourself' question fails this check."
    )

    # ── CHECK 9: Scorecard appears BEFORE forensic scan (ordering) ────────────
    scorecard_pos = content_lower.find("scorecard")
    forensic_pos = -1
    for term in ["forensic", "red flag", "gap", "scan"]:
        pos = content_lower.find(term)
        if pos != -1:
            if forensic_pos == -1 or pos < forensic_pos:
                forensic_pos = pos

    if scorecard_pos == -1 or forensic_pos == -1:
        add_check(
            "scorecard_before_forensic_scan",
            False,
            f"Cannot determine ordering. scorecard_pos={scorecard_pos}, forensic_pos={forensic_pos}."
        )
    else:
        ordering_correct = scorecard_pos < forensic_pos
        add_check(
            "scorecard_before_forensic_scan",
            ordering_correct,
            f"Scorecard first appears at char {scorecard_pos}; "
            f"Forensic/scan first appears at char {forensic_pos}. "
            f"Correct ordering (Scorecard before Forensic): {ordering_correct}. "
            "Smart's principle: define the standard BEFORE looking at the resume."
        )

    # ── CHECK 10: Candidate-specific content (not just template placeholders) ─
    has_wei_chen = bool(re.search(r'wei\s*chen|dr\.\s*chen', content_lower))
    has_pfizer = bool(re.search(r'pfizer|novartis|broad\s*institute', content_lower))
    has_rna = bool(re.search(r'rna|novattera|fep|sbdd', content_lower))
    is_not_just_template = has_wei_chen and (has_pfizer or has_rna)
    add_check(
        "candidate_specific_content",
        is_not_just_template,
        f"Candidate name (Wei Chen) mentioned: {has_wei_chen}. "
        f"Specific resume evidence cited (Pfizer/Novartis/Broad): {has_pfizer}. "
        f"Role-specific technical content (RNA/FEP/SBDD): {has_rna}. "
        "Must not be a generic unfilled template."
    )

    # ── Scoring ───────────────────────────────────────────────────────────────
    weights = {
        "output_file_exists":                  1.0,
        "scorecard_section_with_mission":       1.0,
        "scorecard_outcomes_defined":           1.0,
        "scorecard_competencies_defined":       0.75,
        "forensic_scan_with_red_flags":         1.0,
        "green_signals_section_present":        1.25,  # key proprietary requirement
        "proprietary_heuristics_applied":       1.25,  # key proprietary requirement
        "pressure_test_questions_present":      1.0,
        "future_simulation_with_specific_context": 1.25,
        "scorecard_before_forensic_scan":       1.0,   # Smart's ordering principle
        "candidate_specific_content":           0.5,
    }
    total_weight = sum(weights.values())
    earned = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    score = round(earned / total_weight, 4)

    critical_checks = [
        "output_file_exists",
        "forensic_scan_with_red_flags",
        "green_signals_section_present",
        "future_simulation_with_specific_context",
        "scorecard_before_forensic_scan",
    ]
    all_critical = all(c["passed"] for c in checks if c["name"] in critical_checks)
    passed = all_critical and score >= 0.70

    return {"passed": passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))