import sys
import json
import re
from pathlib import Path

def find_guide(workspace: Path):
    """Locate the produced interview guide."""
    # Accept any markdown file named with 'interview_guide' or 'priya' anywhere
    candidates = list(workspace.rglob("interview_guide_priya*.md"))
    candidates += list(workspace.rglob("interview_guide_priya*.txt"))
    candidates += list(workspace.rglob("priya*interview*.md"))
    candidates += list(workspace.rglob("priya*interview*.txt"))
    # Broader fallback: any new .md in hiring/ or workspace root that isn't template/SKILL
    candidates += [
        p for p in workspace.rglob("*.md")
        if p.name not in ("SKILL.md", "interview_guide_template.md")
        and ("interview" in p.name.lower() or "guide" in p.name.lower() or "priya" in p.name.lower())
    ]
    if not candidates:
        return None
    # Prefer the one with most content
    candidates = sorted(set(candidates), key=lambda p: p.stat().st_size, reverse=True)
    return candidates[0]

def run_checks(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    score = 0.0

    guide_path = find_guide(workspace)

    # ── Check 0: File existence ────────────────────────────────────────────────
    if guide_path is None:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": "No interview guide file found in workspace."
        })
        return False, 0.0, checks

    try:
        content = guide_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": f"Could not read guide file: {e}"
        })
        return False, 0.0, checks

    checks.append({
        "name": "output_file_exists",
        "passed": True,
        "detail": f"Guide found at: {guide_path.relative_to(workspace)} ({len(content)} chars)"
    })
    score += 0.10

    content_lower = content.lower()

    # ── Check 1: Scorecard section present (Scorecard-First principle) ─────────
    has_scorecard_section = bool(re.search(
        r'scorecard|a.?player standard|a player standard',
        content_lower
    ))
    has_mission = bool(re.search(r'\bmission\b', content_lower))
    has_outcomes = bool(re.search(r'\boutcome|deliverable|measurable result', content_lower))
    has_competencies = bool(re.search(r'\bcompeten', content_lower))
    scorecard_ok = has_scorecard_section and has_mission and has_outcomes and has_competencies
    checks.append({
        "name": "scorecard_section_present",
        "passed": scorecard_ok,
        "detail": (
            f"Scorecard section: {has_scorecard_section}, Mission: {has_mission}, "
            f"Outcomes: {has_outcomes}, Competencies: {has_competencies}"
        )
    })
    if scorecard_ok:
        score += 0.15

    # ── Check 2: Scorecard appears BEFORE resume analysis ─────────────────────
    scorecard_pos = -1
    for pattern in [r'scorecard', r'a.?player', r'mission']:
        m = re.search(pattern, content_lower)
        if m:
            scorecard_pos = m.start()
            break

    resume_analysis_pos = -1
    for pattern in [r'forensic|resume scan|resume analysis|gap|high point|green signal|red flag']:
        m = re.search(pattern, content_lower)
        if m:
            resume_analysis_pos = m.start()
            break

    scorecard_before_analysis = (
        scorecard_pos != -1 and resume_analysis_pos != -1
        and scorecard_pos < resume_analysis_pos
    )
    checks.append({
        "name": "scorecard_defined_before_resume_analysis",
        "passed": scorecard_before_analysis,
        "detail": (
            f"Scorecard first occurrence at char {scorecard_pos}, "
            f"resume analysis section at char {resume_analysis_pos}. "
            f"Scorecard-first principle {'respected' if scorecard_before_analysis else 'VIOLATED'}."
        )
    })
    if scorecard_before_analysis:
        score += 0.15

    # ── Check 3: At least one Forensic Heuristic named/applied ───────────────
    heuristic_tgtb = bool(re.search(r'too good to be true|tgtb', content_lower))
    heuristic_pv = bool(re.search(r'passenger.{0,15}driver|driver.{0,15}passenger|individual contribution|halo', content_lower))
    heuristic_fp = bool(re.search(r'first principles?|principle understanding|jargon', content_lower))
    heuristics_applied = sum([heuristic_tgtb, heuristic_pv, heuristic_fp])
    heuristics_ok = heuristics_applied >= 2
    checks.append({
        "name": "forensic_heuristics_applied",
        "passed": heuristics_ok,
        "detail": (
            f"Heuristics found: 'Too Good To Be True'={heuristic_tgtb}, "
            f"'Passenger vs Driver'={heuristic_pv}, 'First Principles'={heuristic_fp}. "
            f"Need >= 2, found {heuristics_applied}."
        )
    })
    if heuristics_ok:
        score += 0.10

    # ── Check 4: [Red Flags] AND [Green Signals] both present ─────────────────
    has_red_flags = bool(re.search(r'\[red flag', content_lower) or re.search(r'red flag', content_lower))
    has_green_signals = bool(re.search(r'\[green signal', content_lower) or re.search(r'green signal', content_lower))
    dual_polarity_ok = has_red_flags and has_green_signals
    checks.append({
        "name": "dual_polarity_red_flags_and_green_signals",
        "passed": dual_polarity_ok,
        "detail": (
            f"[Red Flags] present: {has_red_flags}, [Green Signals] present: {has_green_signals}. "
            f"Both required for objective assessment per SKILL.md."
        )
    })
    if dual_polarity_ok:
        score += 0.15

    # ── Check 5: Pressure Test (past STAR-based forensic questions) ───────────
    has_pressure_test = bool(re.search(
        r'pressure test|star|forensic.{0,20}question|behavior.{0,20}question|'
        r'tell me about a time|walk me through|what exact',
        content_lower
    ))
    # Must reference Priya-specific concerns (Google/IBM halo, large-team vs small-team)
    pressure_is_specific = bool(re.search(
        r'google|ibm|willow|large.{0,20}team|startup|small.{0,20}team|resource.{0,20}scarcity|'
        r'individual contribution|your specific role',
        content_lower
    ))
    pressure_ok = has_pressure_test and pressure_is_specific
    checks.append({
        "name": "pressure_test_past_behavior_questions",
        "passed": pressure_ok,
        "detail": (
            f"Has pressure test section: {has_pressure_test}, "
            f"Questions are candidate-specific (not generic): {pressure_is_specific}."
        )
    })
    if pressure_ok:
        score += 0.15

    # ── Check 6: Future Simulation with QuantumLeap-specific scenario ─────────
    has_future_sim = bool(re.search(
        r'future simulation|performance problem|simulation|if you join|first.{0,10}week|'
        r'first.{0,10}month|scenario|imagine you',
        content_lower
    ))
    sim_is_company_specific = bool(re.search(
        r'quantumleap|qubit|qec|roche|os v2|error correction|1000.qubit|logical qubit|'
        r'23 engineer|scale.{0,20}team|surface code',
        content_lower
    ))
    future_sim_ok = has_future_sim and sim_is_company_specific
    checks.append({
        "name": "future_simulation_company_specific",
        "passed": future_sim_ok,
        "detail": (
            f"Has future simulation section: {has_future_sim}, "
            f"Scenario is QuantumLeap-specific (not generic): {sim_is_company_specific}."
        )
    })
    if future_sim_ok:
        score += 0.15

    # ── Check 7: Template structure respected (key section headers present) ───
    template_sections = [
        bool(re.search(r'interview guide', content_lower)),
        bool(re.search(r'priya|venkataraman', content_lower)),
        bool(re.search(r'section [123]|##.*(scorecard|forensic|question|pressure|simulation)', content_lower)),
    ]
    template_ok = sum(template_sections) >= 2
    checks.append({
        "name": "template_structure_respected",
        "passed": template_ok,
        "detail": (
            f"Template structure checks (title, candidate name, section headers): "
            f"{template_sections} — {sum(template_sections)}/3 found."
        )
    })
    if template_ok:
        score += 0.05

    # ── Final verdict ──────────────────────────────────────────────────────────
    critical_checks = [
        "scorecard_section_present",
        "dual_polarity_red_flags_and_green_signals",
        "pressure_test_past_behavior_questions",
        "future_simulation_company_specific",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    overall_passed = critical_passed and score >= 0.55

    return overall_passed, round(min(score, 1.0), 3), checks


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "invocation", "passed": False,
                                      "detail": "No workspace path provided."}]}))
        sys.exit(1)

    passed, score, checks = run_checks(sys.argv[1])
    print(json.dumps({"passed": passed, "score": score, "checks": checks}, indent=2))


if __name__ == "__main__":
    main()