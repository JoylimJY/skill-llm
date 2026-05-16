import sys
import json
import re
from pathlib import Path

def find_analysis_file(workspace):
    """Search for the output analysis file."""
    candidates = list(Path(workspace).rglob("voltgrid_analysis.md"))
    if not candidates:
        candidates = list(Path(workspace).rglob("voltgrid_analysis.txt"))
    return candidates[0] if candidates else None

def load_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return None

def check_required_sections(content):
    """
    The SKILL.md mandates exactly these 7 section headers (case-insensitive match):
    1. Goal
    2. Assumptions
    3. What is actually true
    4. Irreducible components
    5. Constraints and tradeoffs
    6. Rebuilt solution
    7. Best next action
    """
    required = [
        r"goal",
        r"assumptions",
        r"what is actually true",
        r"irreducible components",
        r"constraints and tradeoffs",
        r"rebuilt solution",
        r"best next action",
    ]
    results = {}
    content_lower = content.lower()
    for section in required:
        found = bool(re.search(section, content_lower))
        results[section] = found
    return results

def check_assumptions_are_challenged(content):
    """
    The SKILL.md says: surface explicit AND hidden assumptions, 
    and separate facts from analogies/conventions.
    The brief has 7 explicit assumptions. At least 3 must be surfaced and challenged.
    Key assumption phrases from brief:
    - "more stations" / "scale"
    - "highway" / "interstate"  
    - "industry standard" / "competitors"
    - "margins" / "scale problem"
    """
    content_lower = content.lower()
    assumption_challenges = {
        "challenges_scale_assumption": bool(
            re.search(r"(more station|scale.{0,50}(not|false|wrong|myth|analogy|assumption)|assumption.{0,80}scale)", content_lower)
        ),
        "challenges_highway_analogy": bool(
            re.search(r"(highway.{0,80}(analogy|assumption|not|wrong|gas station)|gas station.{0,80}(analogy|not applicable|false|wrong)|charging.{0,40}(home|85|residential).{0,40}(highway|station))", content_lower)
        ),
        "challenges_competitor_copying": bool(
            re.search(r"(copy.{0,60}(competitor|industry)|industry.{0,60}(standard|benchmark).{0,60}(not|wrong|assumption|analogy|convention)|benchmark.{0,40}(mislead|wrong|false|not))", content_lower)
        ),
        "mentions_home_charging_reality": bool(
            re.search(r"(home.{0,40}charg|85.{0,20}%.{0,40}home|residential.{0,40}(utiliz|session|higher|better))", content_lower)
        ),
    }
    return assumption_challenges

def check_irreducible_components(content):
    """
    The SKILL.md requires breaking the problem into irreducible components — 
    fundamental truths that cannot be further decomposed.
    In this domain, core irreducibles would include:
    - What EV drivers actually need (energy delivery, not 'charging')
    - Where/when energy is actually consumed (home vs. transit)
    - Revenue = sessions × kWh × price margin
    - Charger value = utilization × revenue_per_session - cost_per_day
    """
    content_lower = content.lower()
    irreducible_checks = {
        "has_fundamental_unit_economics": bool(
            re.search(r"(session.{0,40}(revenue|kwh|cost)|utiliz.{0,40}(revenue|profit|margin)|revenue.{0,40}session|unit econom)", content_lower)
        ),
        "identifies_actual_use_context": bool(
            re.search(r"(home.{0,40}charg|where.{0,40}charg|when.{0,40}charg|parking.{0,40}charg|dwell.{0,40}time|overnight)", content_lower)
        ),
        "separates_facts_from_defaults": bool(
            re.search(r"(fact|actually true|what is true|must be true|evidence|data show|data suggest)", content_lower)
        ),
    }
    return irreducible_checks

def check_rebuilt_solution_originality(content):
    """
    The rebuilt solution must not just echo the original strategy.
    It should recommend a materially different approach, e.g.:
    - Prioritize residential/destination charging over highway
    - Focus on utilization rate over station count
    - Different capital allocation
    """
    content_lower = content.lower()
    solution_checks = {
        "recommends_non_highway_focus": bool(
            re.search(r"(residential|apartment|workplace|destination|hotel|home.{0,40}(install|charg|deploy)|dwell)", content_lower)
        ),
        "reframes_success_metric": bool(
            re.search(r"(utiliz.{0,40}(metric|measure|kpi|focus|instead|over)|session.{0,40}day|revenue.{0,40}charger|metric.{0,40}station.{0,40}count)", content_lower)
        ),
        "provides_concrete_next_action": bool(
            re.search(r"(next.{0,30}(step|action)|action|deploy|allocat|invest|pilot|test|launch).{0,100}(residential|apartment|workplace|destination|utiliz)", content_lower)
        ),
    }
    return solution_checks

def check_no_analogy_as_truth(content):
    """
    SKILL.md: Do not treat analogy as understanding.
    The agent should explicitly call out that gas-station analogy is wrong.
    """
    content_lower = content.lower()
    return bool(
        re.search(
            r"(gas station.{0,80}(analogy|not|wrong|different|mislead|false)|analogy.{0,60}gas|charg.{0,40}(not|unlike|different).{0,40}gas)",
            content_lower
        )
    )

def check_goal_clarity(content):
    """The Goal section must articulate a specific, clarified real objective."""
    content_lower = content.lower()
    after_goal = content_lower.split("goal")[-1][:500] if "goal" in content_lower else ""
    return bool(
        re.search(r"(profit|margin|sustainable|utiliz|return|capital|deploy)", after_goal)
    )

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "workspace_argument", "passed": False, "detail": "No workspace path provided."}
        ]}))
        sys.exit(0)

    workspace = sys.argv[1]
    checks = []

    # ── Check 1: File exists ────────────────────────────────────────────────
    output_file = find_analysis_file(workspace)
    file_exists = output_file is not None
    checks.append({
        "name": "output_file_exists",
        "passed": file_exists,
        "detail": f"Found: {output_file}" if file_exists else "voltgrid_analysis.md (or .txt) not found anywhere in workspace."
    })

    if not file_exists:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        sys.exit(0)

    content = load_file(output_file)
    if content is None:
        checks.append({"name": "file_readable", "passed": False, "detail": "File exists but could not be read."})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        sys.exit(0)

    checks.append({"name": "file_readable", "passed": True, "detail": f"File read successfully ({len(content)} chars)."})

    min_length = len(content) >= 600
    checks.append({
        "name": "minimum_content_length",
        "passed": min_length,
        "detail": f"Content length: {len(content)} chars (minimum 600 required)."
    })

    # ── Check 2: All 7 required sections present ────────────────────────────
    section_results = check_required_sections(content)
    all_sections_present = all(section_results.values())
    missing_sections = [s for s, found in section_results.items() if not found]
    checks.append({
        "name": "all_seven_sections_present",
        "passed": all_sections_present,
        "detail": (
            "All 7 SKILL.md sections found." if all_sections_present
            else f"Missing sections: {missing_sections}"
        )
    })
    for section, found in section_results.items():
        checks.append({
            "name": f"section__{section.replace(' ', '_')}",
            "passed": found,
            "detail": f"Section '{section}': {'found' if found else 'NOT FOUND'}."
        })

    # ── Check 3: Assumptions are surfaced and challenged ────────────────────
    assumption_checks = check_assumptions_are_challenged(content)
    assumptions_passed = sum(assumption_checks.values())
    checks.append({
        "name": "assumptions_surfaced_and_challenged",
        "passed": assumptions_passed >= 3,
        "detail": f"{assumptions_passed}/4 assumption challenge signals found: {assumption_checks}"
    })

    # ── Check 4: Irreducible components are real ────────────────────────────
    irr_checks = check_irreducible_components(content)
    irr_passed = sum(irr_checks.values())
    checks.append({
        "name": "irreducible_components_substantive",
        "passed": irr_passed >= 2,
        "detail": f"{irr_passed}/3 irreducible component signals found: {irr_checks}"
    })

    # ── Check 5: Rebuilt solution is original ───────────────────────────────
    sol_checks = check_rebuilt_solution_originality(content)
    sol_passed = sum(sol_checks.values())
    checks.append({
        "name": "rebuilt_solution_is_original",
        "passed": sol_passed >= 2,
        "detail": f"{sol_passed}/3 original solution signals found: {sol_checks}"
    })

    # ── Check 6: Gas-station analogy explicitly rejected ────────────────────
    analogy_rejected = check_no_analogy_as_truth(content)
    checks.append({
        "name": "gas_station_analogy_rejected",
        "passed": analogy_rejected,
        "detail": "Gas-station analogy explicitly challenged." if analogy_rejected else "No explicit rejection of gas-station analogy found."
    })

    # ── Check 7: Goal section is specific ───────────────────────────────────
    goal_specific = check_goal_clarity(content)
    checks.append({
        "name": "goal_section_is_specific",
        "passed": goal_specific,
        "detail": "Goal section references profitability/utilization/capital." if goal_specific else "Goal section appears generic or missing key business terms."
    })

    # ── Check 8: Uses actual data from workspace files ──────────────────────
    uses_data = bool(
        re.search(r"(6\.3|4\.7|2\.9|1\.2|85.{0,10}%|residential.{0,40}session|hotel.{0,40}session|apartment.{0,40}(session|utiliz))", content.lower())
    )
    checks.append({
        "name": "references_actual_workspace_data",
        "passed": uses_data,
        "detail": "Analysis references specific data points from workspace files." if uses_data else "No references to specific data values from workspace (e.g., 6.3 sessions/day, 4.7, 85%)."
    })

    # ── Scoring ──────────────────────────────────────────────────────────────
    critical_checks = [
        "output_file_exists",
        "all_seven_sections_present",
        "assumptions_surfaced_and_challenged",
        "irreducible_components_substantive",
        "rebuilt_solution_is_original",
        "gas_station_analogy_rejected",
    ]
    bonus_checks = [
        "goal_section_is_specific",
        "references_actual_workspace_data",
        "minimum_content_length",
    ]

    critical_passed = sum(1 for c in checks if c["name"] in critical_checks and c["passed"])
    bonus_passed = sum(1 for c in checks if c["name"] in bonus_checks and c["passed"])

    critical_score = critical_passed / len(critical_checks)
    bonus_score = bonus_passed / len(bonus_checks)
    final_score = round(critical_score * 0.8 + bonus_score * 0.2, 3)

    all_critical_passed = critical_passed == len(critical_checks)
    overall_passed = all_critical_passed and final_score >= 0.75

    print(json.dumps({
        "passed": overall_passed,
        "score": final_score,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()