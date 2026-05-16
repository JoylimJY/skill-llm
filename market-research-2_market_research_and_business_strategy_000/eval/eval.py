import sys
import os
import re
import json
from pathlib import Path

def find_output_file(workspace):
    """Search for market_research.md anywhere in workspace."""
    matches = list(Path(workspace).rglob("market_research.md"))
    return matches[0] if matches else None

def check_section_present(content, keywords, min_matches=1):
    """Return True if at least min_matches keywords are found (case-insensitive)."""
    found = sum(1 for kw in keywords if kw.lower() in content.lower())
    return found >= min_matches

def score_checks(checks):
    passed = sum(1 for c in checks if c["passed"])
    return round(passed / len(checks), 3) if checks else 0.0

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    # ── Locate output file ───────────────────────────────────────────────────
    output_file = find_output_file(workspace)
    file_exists = output_file is not None
    checks.append({
        "name": "output_file_exists",
        "passed": file_exists,
        "detail": f"Found at {output_file}" if file_exists else "market_research.md not found anywhere in workspace"
    })

    if not file_exists:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    content_lower = content.lower()

    # ── CHECK 1: Research Questions defined (Step 1) ─────────────────────────
    has_questions = any(phrase in content_lower for phrase in [
        "research question", "question 1", "question 2", "how large", "addressable market",
        "who are the", "competitors", "what trends", "customer look"
    ])
    checks.append({
        "name": "step1_research_questions",
        "passed": has_questions,
        "detail": "Document contains research questions section" if has_questions else "No research questions section detected"
    })

    # ── CHECK 2: TAM present with a numeric value ────────────────────────────
    tam_match = re.search(r'\bTAM\b.*?(\$[\d,.]+[BMK]?|\d[\d,.]+\s*(?:billion|million|M\b|B\b))', content, re.IGNORECASE | re.DOTALL)
    tam_present = tam_match is not None
    checks.append({
        "name": "step2_TAM_with_number",
        "passed": tam_present,
        "detail": f"TAM found: {tam_match.group(0)[:80] if tam_match else 'N/A'}"
    })

    # ── CHECK 3: SAM present with a numeric value ────────────────────────────
    sam_match = re.search(r'\bSAM\b.*?(\$[\d,.]+[BMK]?|\d[\d,.]+\s*(?:billion|million|M\b|B\b))', content, re.IGNORECASE | re.DOTALL)
    sam_present = sam_match is not None
    checks.append({
        "name": "step2_SAM_with_number",
        "passed": sam_present,
        "detail": f"SAM found: {sam_match.group(0)[:80] if sam_match else 'N/A'}"
    })

    # ── CHECK 4: SOM present with a numeric value ────────────────────────────
    som_match = re.search(r'\bSOM\b.*?(\$[\d,.]+[BMK]?|\d[\d,.]+\s*(?:billion|million|M\b|B\b))', content, re.IGNORECASE | re.DOTALL)
    som_present = som_match is not None
    checks.append({
        "name": "step2_SOM_with_number",
        "passed": som_present,
        "detail": f"SOM found: {som_match.group(0)[:80] if som_match else 'N/A'}"
    })

    # ── CHECK 5: SOM $500K decision rule applied ─────────────────────────────
    decision_rule = re.search(
        r'(500[,\s]?[Kk]|500,000|\$500K|too small|sustain|viable|worth pursuing)',
        content, re.IGNORECASE
    )
    checks.append({
        "name": "step2_SOM_500K_decision_rule",
        "passed": decision_rule is not None,
        "detail": f"Decision rule applied: '{decision_rule.group(0)}'" if decision_rule else "No $500K SOM decision rule found — critical proprietary check"
    })

    # ── CHECK 6: At least 4 of 5 competitors profiled with schema fields ─────
    competitor_names = ["duolingo", "babbel", "italki", "pimsleur", "preply"]
    found_competitors = [c for c in competitor_names if c in content_lower]
    schema_fields = ["name:", "url:", "founded:", "funding", "target:", "value prop:", "pricing:", "top features:", "strengths:", "weaknesses:", "traffic:"]
    schema_field_count = sum(1 for f in schema_fields if f.lower() in content_lower)

    competitor_check = len(found_competitors) >= 4 and schema_field_count >= 8
    checks.append({
        "name": "step4_competitor_profiles_with_schema",
        "passed": competitor_check,
        "detail": f"Competitors found: {found_competitors} ({len(found_competitors)}/5). Schema fields present: {schema_field_count}/11"
    })

    # ── CHECK 7: Synthesis lists (table stakes, universal gaps, underserved) ──
    synthesis_keywords = ["table stakes", "universal gap", "underserved segment", "underserved"]
    synthesis_found = sum(1 for kw in synthesis_keywords if kw.lower() in content_lower)
    synthesis_check = synthesis_found >= 2
    checks.append({
        "name": "step4_synthesis_three_lists",
        "passed": synthesis_check,
        "detail": f"Synthesis sections found: {synthesis_found}/3 required keywords (table stakes, universal gaps, underserved segments)"
    })

    # ── CHECK 8: At least 3 trends with 5-part structure ────────────────────
    # Look for Maturity vocabulary (exact terms from SKILL.md)
    maturity_terms = re.findall(r'\b(Emerging|Growing|Maturing|Declining)\b', content, re.IGNORECASE)
    # Look for Impact vocabulary
    impact_terms = re.findall(r'\b(Tailwind|Headwind|Neutral)\b', content, re.IGNORECASE)
    # Look for Action vocabulary
    action_terms = re.findall(r'\b(Build for it|Watch it|Ignore it|Avoid it)\b', content, re.IGNORECASE)

    trend_structure_check = len(maturity_terms) >= 3 and len(impact_terms) >= 3 and len(action_terms) >= 2
    checks.append({
        "name": "step5_trends_with_5part_structure",
        "passed": trend_structure_check,
        "detail": (f"Maturity terms: {len(maturity_terms)} (need 3+), "
                   f"Impact terms: {len(impact_terms)} (need 3+), "
                   f"Action terms: {len(action_terms)} (need 2+)")
    })

    # ── CHECK 9: Evidence in trends (concrete data points) ───────────────────
    evidence_markers = re.findall(r'(\$\d+[MBK]|\d+%|\d+M|\bCRGA\b|raised|million|billion|series [ABC]|per.*report)', content, re.IGNORECASE)
    evidence_check = len(evidence_markers) >= 5
    checks.append({
        "name": "step5_trend_evidence_datapoints",
        "passed": evidence_check,
        "detail": f"Evidence markers found: {len(evidence_markers)} (need 5+ to confirm 2-3 per trend)"
    })

    # ── CHECK 10: 2-3 customer personas with exact schema fields ─────────────
    persona_fields = [
        "persona name:", "role & industry:", "seniority:", "company size:", "location:",
        "annual income:", "daily reality:", "pain points:", "goals:", "buying behavior:",
        "channels:", "quote:"
    ]
    persona_field_count = sum(1 for f in persona_fields if f.lower() in content_lower)
    # Check for multiple personas (look for 2+ persona name: occurrences)
    persona_name_occurrences = len(re.findall(r'persona name\s*:', content, re.IGNORECASE))
    persona_check = persona_field_count >= 8 and persona_name_occurrences >= 2
    checks.append({
        "name": "step6_personas_with_schema",
        "passed": persona_check,
        "detail": f"Persona schema fields found: {persona_field_count}/12, Persona count (by 'PERSONA NAME:'): {persona_name_occurrences} (need 2+)"
    })

    # ── CHECK 11: QUOTE field in personas ────────────────────────────────────
    quote_occurrences = len(re.findall(r'quote\s*:', content, re.IGNORECASE))
    quote_check = quote_occurrences >= 2
    checks.append({
        "name": "step6_personas_have_quote_field",
        "passed": quote_check,
        "detail": f"QUOTE: fields found: {quote_occurrences} (need 2+ for 2+ personas)"
    })

    # ── CHECK 12: DAILY REALITY section in personas ───────────────────────────
    daily_reality_count = len(re.findall(r'daily reality\s*:', content, re.IGNORECASE))
    daily_reality_check = daily_reality_count >= 2
    checks.append({
        "name": "step6_personas_have_daily_reality",
        "passed": daily_reality_check,
        "detail": f"DAILY REALITY: fields found: {daily_reality_count} (need 2+ for 2+ personas)"
    })

    # ── CHECK 13: Recommended Next Actions (numbered, specific) ──────────────
    # Look for a numbered list in a "next actions" or "recommended" section
    next_actions_section = re.search(
        r'(recommended next action|next action|action plan|what.*do next)',
        content, re.IGNORECASE
    )
    # Check for at least 3 numbered items anywhere after it
    numbered_items = re.findall(r'^\s*\d+[\.\)]\s+\S', content, re.MULTILINE)
    next_actions_check = next_actions_section is not None and len(numbered_items) >= 3
    checks.append({
        "name": "step7_recommended_next_actions_numbered",
        "passed": next_actions_check,
        "detail": (f"Next actions section: {'found' if next_actions_section else 'NOT found'}. "
                   f"Numbered list items: {len(numbered_items)} (need 3+)")
    })

    # ── CHECK 14: Document covers all 4 major sections ───────────────────────
    major_sections = {
        "market_size": any(kw in content_lower for kw in ["tam", "sam", "som", "market size"]),
        "competitors": any(kw in content_lower for kw in ["competitor", "competition", "landscape"]),
        "trends": any(kw in content_lower for kw in ["trend", "tailwind", "headwind"]),
        "personas": any(kw in content_lower for kw in ["persona", "customer profile"]),
    }
    all_sections_present = all(major_sections.values())
    checks.append({
        "name": "step7_all_four_sections_present",
        "passed": all_sections_present,
        "detail": f"Sections status: {major_sections}"
    })

    # ── Final scoring ─────────────────────────────────────────────────────────
    score = score_checks(checks)
    # Must pass at minimum: file exists + TAM/SAM/SOM + decision rule + competitors + trends + personas + next actions
    critical_checks = [
        "output_file_exists",
        "step2_TAM_with_number",
        "step2_SAM_with_number",
        "step2_SOM_with_number",
        "step2_SOM_500K_decision_rule",
        "step4_competitor_profiles_with_schema",
        "step4_synthesis_three_lists",
        "step5_trends_with_5part_structure",
        "step6_personas_with_schema",
        "step7_recommended_next_actions_numbered",
    ]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    overall_passed = critical_passed and score >= 0.75

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()