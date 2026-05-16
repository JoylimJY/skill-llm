import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    
    # ─── Helper ───
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ══════════════════════════════════════════════════
    # CHECK 1: memory.md exists at the correct location
    # ══════════════════════════════════════════════════
    memory_path = Path("/root/career/memory.md")
    if not memory_path.exists():
        add_check("memory_md_exists", False, "File /root/career/memory.md does not exist")
        # Remaining checks will fail; still run them gracefully
        memory_content = ""
    else:
        try:
            memory_content = memory_path.read_text(encoding="utf-8")
            add_check("memory_md_exists", True, "File /root/career/memory.md found")
        except Exception as e:
            add_check("memory_md_exists", False, f"Could not read memory.md: {e}")
            memory_content = ""

    # ══════════════════════════════════════════════════
    # CHECK 2: memory.md has all 5 required sections
    # ══════════════════════════════════════════════════
    required_sections = ["## Values", "## Strengths", "## Constraints", "## Context", "## Goals"]
    missing_sections = [s for s in required_sections if s not in memory_content]
    if missing_sections:
        add_check("memory_has_all_sections", False,
                  f"Missing sections: {missing_sections}")
    else:
        add_check("memory_has_all_sections", True,
                  "All 5 required sections present (Values, Strengths, Constraints, Context, Goals)")

    # ══════════════════════════════════════════════════
    # CHECK 3: Format compliance — entries use "(level)" notation
    # The proprietary format: "value (level)" or "skill: level (source)"
    # Levels must be: stated, pattern, or confirmed
    # ══════════════════════════════════════════════════
    valid_levels = {"stated", "pattern", "confirmed"}
    
    # Find all parenthesized level annotations in memory content
    # Pattern: word(s) inside parens that should be one of the valid levels
    # Also accept compound like "(confirmed)" at end of lines
    level_pattern = re.compile(r'\(([^)]+)\)')
    found_levels = level_pattern.findall(memory_content)
    
    # Filter to only those that look like standalone level markers (not source labels mixed in)
    # The format allows: "skill: level (source)" — so source can be non-level
    # We need at least some entries with valid levels
    valid_level_hits = [l.strip().lower() for l in found_levels if l.strip().lower() in valid_levels]
    
    if len(valid_level_hits) == 0:
        add_check("proprietary_level_format", False,
                  f"No entries found using the required (stated/pattern/confirmed) level notation. "
                  f"Found parenthesized content: {found_levels[:10]}")
    else:
        add_check("proprietary_level_format", True,
                  f"Found {len(valid_level_hits)} entries with valid level notation: {valid_level_hits}")

    # ══════════════════════════════════════════════════
    # CHECK 4: Autonomy value — must be "confirmed" (explicitly affirmed twice + "even more sure")
    # ══════════════════════════════════════════════════
    values_section = ""
    try:
        if "## Values" in memory_content:
            start = memory_content.index("## Values")
            # Find next section
            next_section = re.search(r'\n## ', memory_content[start+1:])
            end = start + 1 + next_section.start() if next_section else len(memory_content)
            values_section = memory_content[start:end]
    except Exception:
        values_section = memory_content  # fallback: search whole file
    
    autonomy_confirmed = bool(
        re.search(r'autonomy.*confirmed', values_section, re.IGNORECASE) or
        re.search(r'autonomy[^(]*\(\s*confirmed\s*\)', memory_content, re.IGNORECASE)
    )
    if not autonomy_confirmed:
        add_check("autonomy_is_confirmed", False,
                  "Autonomy value not found as 'confirmed'. It was explicitly affirmed in session 2 and 3 — should be 'confirmed' level.")
    else:
        add_check("autonomy_is_confirmed", True,
                  "Autonomy correctly marked as 'confirmed' level.")

    # ══════════════════════════════════════════════════
    # CHECK 5: Location constraint — Boston, must be "confirmed"
    # ══════════════════════════════════════════════════
    constraints_section = ""
    try:
        if "## Constraints" in memory_content:
            start = memory_content.index("## Constraints")
            next_section = re.search(r'\n## ', memory_content[start+1:])
            end = start + 1 + next_section.start() if next_section else len(memory_content)
            constraints_section = memory_content[start:end]
    except Exception:
        constraints_section = memory_content

    boston_confirmed = bool(
        re.search(r'boston.*confirmed', constraints_section, re.IGNORECASE) or
        re.search(r'location.*boston[^(]*\(\s*confirmed\s*\)', memory_content, re.IGNORECASE) or
        re.search(r'boston[^(]*\(\s*confirmed\s*\)', constraints_section, re.IGNORECASE)
    )
    if not boston_confirmed:
        add_check("boston_location_confirmed", False,
                  "Location:Boston constraint not found as 'confirmed'. Client explicitly confirmed it as non-negotiable.")
    else:
        add_check("boston_location_confirmed", True,
                  "Boston location constraint correctly marked as 'confirmed'.")

    # ══════════════════════════════════════════════════
    # CHECK 6: Team leadership goal — must be "pattern" NOT "confirmed"
    # (Client mentioned it twice, but no explicit "yes" to the coach confirming it as a stored insight)
    # It qualifies as pattern (2 signals) but not confirmed (no explicit yes to storing it)
    # ══════════════════════════════════════════════════
    goals_section = ""
    try:
        if "## Goals" in memory_content:
            start = memory_content.index("## Goals")
            next_section = re.search(r'\n## ', memory_content[start+1:])
            end = start + 1 + next_section.start() if next_section else len(memory_content)
            goals_section = memory_content[start:end]
    except Exception:
        goals_section = memory_content

    lead_team_present = bool(
        re.search(r'lead\s*(a\s*)?(product\s*)?team', goals_section, re.IGNORECASE) or
        re.search(r'team\s*lead', goals_section, re.IGNORECASE) or
        re.search(r'product\s*(line|ownership)', goals_section, re.IGNORECASE)
    )
    
    # It should be "pattern" level (2 signals, no confirmed store)
    lead_team_pattern = bool(
        re.search(r'(lead.*team|team.*lead|product.*line)[^(]*\(\s*pattern\s*\)', goals_section, re.IGNORECASE)
    )
    # It should NOT be "stated" (has 2 signals, upgrade to pattern)
    lead_team_stated_only = bool(
        re.search(r'(lead.*team|team.*lead)[^(]*\(\s*stated\s*\)', goals_section, re.IGNORECASE)
    ) and not lead_team_pattern

    if not lead_team_present:
        add_check("lead_team_goal_present", False,
                  "No entry found for 'lead team' goal in Goals section.")
    else:
        add_check("lead_team_goal_present", True,
                  "Lead team goal is present in Goals section.")

    if lead_team_pattern:
        add_check("lead_team_goal_at_pattern_level", True,
                  "Lead team goal correctly marked as 'pattern' (2 signals, no explicit confirmation to store).")
    elif lead_team_stated_only:
        add_check("lead_team_goal_at_pattern_level", False,
                  "Lead team goal marked as 'stated' but 2 signals exist — should be upgraded to 'pattern'.")
    else:
        # Check if it was marked confirmed (wrong — no explicit yes to storing)
        lead_confirmed = bool(
            re.search(r'(lead.*team|team.*lead)[^(]*\(\s*confirmed\s*\)', goals_section, re.IGNORECASE)
        )
        if lead_confirmed:
            add_check("lead_team_goal_at_pattern_level", False,
                      "Lead team goal marked as 'confirmed' but client never explicitly confirmed the stored insight — should be 'pattern'.")
        elif lead_team_present:
            add_check("lead_team_goal_at_pattern_level", False,
                      "Lead team goal present but level annotation unclear or missing.")
        else:
            add_check("lead_team_goal_at_pattern_level", False,
                      "Lead team goal level annotation not determinable.")

    # ══════════════════════════════════════════════════
    # CHECK 7: Strengths — cross-functional coordination present
    # ══════════════════════════════════════════════════
    strengths_section = ""
    try:
        if "## Strengths" in memory_content:
            start = memory_content.index("## Strengths")
            next_section = re.search(r'\n## ', memory_content[start+1:])
            end = start + 1 + next_section.start() if next_section else len(memory_content)
            strengths_section = memory_content[start:end]
    except Exception:
        strengths_section = memory_content

    cross_functional_present = bool(
        re.search(r'cross.functional', strengths_section, re.IGNORECASE) or
        re.search(r'coordination', strengths_section, re.IGNORECASE) or
        re.search(r'cross.team', strengths_section, re.IGNORECASE)
    )
    if not cross_functional_present:
        add_check("strength_cross_functional_present", False,
                  "Cross-functional coordination strength not found in Strengths section.")
    else:
        add_check("strength_cross_functional_present", True,
                  "Cross-functional coordination strength correctly identified.")

    # ══════════════════════════════════════════════════
    # CHECK 8: negotiations.md contains personalized guidance (not just the template)
    # ══════════════════════════════════════════════════
    negotiations_path = Path("/root/career/negotiations.md")
    try:
        neg_content = negotiations_path.read_text(encoding="utf-8")
    except Exception as e:
        add_check("negotiations_md_populated", False, f"Could not read negotiations.md: {e}")
        neg_content = ""

    # Must have content beyond the template boilerplate
    template_only = neg_content.strip() == """\
# Salary & Offer Negotiations

## Core Principle
Never accept the first offer.

## Framework

<!-- Personalized negotiation guidance goes here -->""".strip()

    meaningful_content_added = len(neg_content) > 600  # original template is ~160 chars
    
    if template_only or not meaningful_content_added:
        add_check("negotiations_md_populated", False,
                  f"negotiations.md appears to contain only the original template. "
                  f"Length: {len(neg_content)} chars. Personalized guidance for Mara must be added.")
    else:
        add_check("negotiations_md_populated", True,
                  f"negotiations.md has been populated with additional content ({len(neg_content)} chars).")

    # ══════════════════════════════════════════════════
    # CHECK 9: Negotiation guidance references Mara's specific context
    # (salary numbers, equity, title leveling — not generic advice)
    # ══════════════════════════════════════════════════
    mara_specific_signals = []
    
    # Should mention the salary gap or specific numbers
    if re.search(r'130|145|155|market|benchmark', neg_content, re.IGNORECASE):
        mara_specific_signals.append("salary_numbers")
    
    # Should mention equity/options (unclear terms flagged in session)
    if re.search(r'equity|option|vesting|shares', neg_content, re.IGNORECASE):
        mara_specific_signals.append("equity_terms")
    
    # Should mention title/leveling issue
    if re.search(r'title|associate|level|re-level', neg_content, re.IGNORECASE):
        mara_specific_signals.append("title_leveling")

    if len(mara_specific_signals) < 2:
        add_check("negotiation_is_personalized", False,
                  f"Negotiation guidance not sufficiently personalized to Mara's context. "
                  f"Detected signals: {mara_specific_signals}. Need at least 2 of: salary numbers, equity terms, title leveling.")
    else:
        add_check("negotiation_is_personalized", True,
                  f"Negotiation guidance references Mara's specific context: {mara_specific_signals}")

    # ══════════════════════════════════════════════════
    # CHECK 10: No Universal Trap violations in negotiations.md
    # The "sunk cost" trap: agent must NOT frame 6 years as reason to accept offer or avoid negotiating
    # The "false binary" trap: agent must NOT present only "accept" or "reject"
    # ══════════════════════════════════════════════════
    sunk_cost_violation = bool(
        re.search(r'(6|six)\s*years.{0,60}(reason|stay|accept|security)', neg_content, re.IGNORECASE) or
        re.search(r'(loyalty|tenure).{0,40}(worth|value|reason)', neg_content, re.IGNORECASE)
    )
    false_binary_violation = bool(
        re.search(r'(only|either).{0,30}(accept|reject|stay|leave)', neg_content, re.IGNORECASE)
    )

    if sunk_cost_violation:
        add_check("no_sunk_cost_trap_in_guidance", False,
                  "Negotiation guidance falls into the 'sunk cost' trap by framing tenure as justification.")
    else:
        add_check("no_sunk_cost_trap_in_guidance", True,
                  "No sunk cost trap language detected in negotiation guidance.")

    if false_binary_violation:
        add_check("no_false_binary_trap_in_guidance", False,
                  "Negotiation guidance presents a false binary (accept/reject only).")
    else:
        add_check("no_false_binary_trap_in_guidance", True,
                  "No false binary trap language detected in negotiation guidance.")

    # ══════════════════════════════════════════════════
    # CHECK 11: Context section has Mara's professional context
    # ══════════════════════════════════════════════════
    context_section = ""
    try:
        if "## Context" in memory_content:
            start = memory_content.index("## Context")
            next_section = re.search(r'\n## ', memory_content[start+1:])
            end = start + 1 + next_section.start() if next_section else len(memory_content)
            context_section = memory_content[start:end]
    except Exception:
        context_section = memory_content

    context_has_role = bool(
        re.search(r'(research scientist|scientist|biolog|BioNovaTech|PhD|computational)', context_section, re.IGNORECASE)
    )
    if not context_has_role:
        add_check("context_has_professional_background", False,
                  "Context section missing Mara's professional background (Research Scientist, BioNovaTech, PhD, etc.).")
    else:
        add_check("context_has_professional_background", True,
                  "Context section contains Mara's professional background.")

    # ══════════════════════════════════════════════════
    # FINAL SCORING
    # ══════════════════════════════════════════════════
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0
    overall_passed = passed_count >= 9  # Must pass at least 9/11 checks

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))