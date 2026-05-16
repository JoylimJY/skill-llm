import sys
import json
import re
import pathlib

def evaluate(workspace_dir: str) -> dict:
    checks = []
    workspace = pathlib.Path(workspace_dir)

    # --- Find the output file ---
    candidates = list(workspace.rglob("memorial_section.md"))
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "memorial_section.md not found anywhere in workspace"}]
        }

    target = candidates[0]
    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False, "detail": f"Could not read file: {e}"}]
        }

    content_lower = content.lower()

    # -----------------------------------------------
    # CHECK 1: File has substantial content (>= 600 words)
    # -----------------------------------------------
    word_count = len(content.split())
    c1_passed = word_count >= 600
    checks.append({
        "name": "substantial_content",
        "passed": c1_passed,
        "detail": f"Word count: {word_count}. Required >= 600."
    })

    # -----------------------------------------------
    # CHECK 2: Roadmap paragraph present
    # A roadmap/overview paragraph at the beginning of the main section
    # Must appear before the first IRAC section. Keywords: "will demonstrate", "will show",
    # "will establish", "will argue", "this section", "section will", "memorial will",
    # "applicant will", "ruthenland will", "r will"
    # -----------------------------------------------
    roadmap_patterns = [
        r'\bwill\s+demonstrate\b',
        r'\bwill\s+show\b',
        r'\bwill\s+establish\b',
        r'\bwill\s+argue\b',
        r'\bthis\s+section\b',
        r'\bsection\s+will\b',
        r'\bmemorial\s+will\b',
        r'\bapplicant\s+will\b',
        r'\bfirst\W{1,30}second\b',
        r'\bsubmits\s+that\b',
    ]
    roadmap_found = any(re.search(p, content_lower) for p in roadmap_patterns)
    # Also check it appears in the first 30% of the document
    first_third = content_lower[:int(len(content_lower) * 0.35)]
    roadmap_early = any(re.search(p, first_third) for p in roadmap_patterns)
    c2_passed = roadmap_found and roadmap_early
    checks.append({
        "name": "roadmap_paragraph_present",
        "passed": c2_passed,
        "detail": f"Roadmap/overview paragraph {'found' if roadmap_found else 'NOT found'}. Early presence: {roadmap_early}."
    })

    # -----------------------------------------------
    # CHECK 3: IRAC structure - all four components present
    # -----------------------------------------------
    has_issue = bool(re.search(r'\bISSUE\b|\bIssue\b|\bissue\b', content))
    has_rules = bool(re.search(r'\bRULES?\b|\bRules?\b|\brules?\b', content))
    has_application = bool(re.search(r'\bAPPLICATION\b|\bApplication\b|\bapplication\b', content))
    has_conclusion = bool(re.search(r'\bCONCLUSION\b|\bConclusion\b|\bconclusion\b', content))
    c3_passed = has_issue and has_rules and has_application and has_conclusion
    checks.append({
        "name": "irac_structure_complete",
        "passed": c3_passed,
        "detail": f"IRAC components - Issue:{has_issue}, Rules:{has_rules}, Application:{has_application}, Conclusion:{has_conclusion}"
    })

    # -----------------------------------------------
    # CHECK 4: Multiple rules (at least 2 distinct legal rules/sources)
    # Must have more than one rule source — check for multiple numbered items, 
    # multiple paragraph markers, or explicit enumeration in rules section
    # -----------------------------------------------
    # Count distinct rule-indicators: numbered lists, "first"/"second", multiple citations
    rule_indicators = [
        r'\b1\.\s+[A-Z]',
        r'\b2\.\s+[A-Z]',
        r'\(1\)',
        r'\(2\)',
        r'\bfirst(ly)?\b.{0,200}\bsecond(ly)?\b',
        r'\bfurthermore\b.{0,300}\b(rule|principle|obligation|norm)\b',
        r'\bin\s+addition\b.{0,300}\b(rule|principle|obligation|norm)\b',
    ]
    multi_rule_found = sum(1 for p in rule_indicators if re.search(p, content, re.DOTALL | re.IGNORECASE)) >= 2
    # Also check that rules section has explanation prose (not just a paste)
    # A bare paste would be very short in the rules section
    rules_section_match = re.search(
        r'(?:RULES?|Rules?)[^\n]*\n(.*?)(?:APPLICATION|Application|application)',
        content, re.DOTALL
    )
    rules_has_explanation = False
    if rules_section_match:
        rules_text = rules_section_match.group(1)
        rules_words = len(rules_text.split())
        # Must have at least 80 words of explanation in rules section
        rules_has_explanation = rules_words >= 80
    c4_passed = multi_rule_found and rules_has_explanation
    checks.append({
        "name": "multiple_rules_with_explanation",
        "passed": c4_passed,
        "detail": f"Multiple rule indicators: {multi_rule_found}. Rules section has explanation prose (>=80 words): {rules_has_explanation}."
    })

    # -----------------------------------------------
    # CHECK 5: Two-element CIL test explicitly stated
    # Must mention BOTH state practice AND opinio juris (or legal conviction/accepted as law)
    # -----------------------------------------------
    has_state_practice = bool(re.search(
        r'state\s+practice|practice\s+of\s+state|general\s+practice', content_lower))
    has_opinio = bool(re.search(
        r'opinio\s+juris|legal\s+conviction|accepted\s+as\s+law|belief\s+that\s+the\s+practice|obligatory|legally\s+required',
        content_lower))
    c5_passed = has_state_practice and has_opinio
    checks.append({
        "name": "cil_two_element_test",
        "passed": c5_passed,
        "detail": f"State practice mentioned: {has_state_practice}. Opinio juris mentioned: {has_opinio}."
    })

    # -----------------------------------------------
    # CHECK 6: Nicaragua case cited with linkage establishment
    # Must mention Nicaragua case AND establish a factual linkage to the current case
    # -----------------------------------------------
    has_nicaragua = bool(re.search(r'nicaragua', content_lower))
    # Linkage: agent must connect Nicaragua facts to current case facts
    linkage_patterns = [
        r'similarly\b',
        r'analogous(ly)?\b',
        r'like\s+the\b',
        r'as\s+in\b.{0,100}nicaragua',
        r'nicaragua.{0,300}similarly',
        r'present\s+case.{0,200}nicaragua',
        r'nicaragua.{0,300}present\s+case',
        r'this\s+case.{0,200}nicaragua',
        r'nicaragua.{0,300}this\s+case',
        r'instant\s+case',
        r'case\s+at\s+bar',
    ]
    has_linkage = any(re.search(p, content_lower, re.DOTALL) for p in linkage_patterns)
    c6_passed = has_nicaragua and has_linkage
    checks.append({
        "name": "nicaragua_case_linkage",
        "passed": c6_passed,
        "detail": f"Nicaragua cited: {has_nicaragua}. Linkage to current case established: {has_linkage}."
    })

    # -----------------------------------------------
    # CHECK 7: Case distinction / counter-linkage present
    # Agent must address the "30% vs total embargo" distinction and argue
    # that coercion is about effect/intent not percentage
    # -----------------------------------------------
    distinction_patterns = [
        r'30\s*%|thirty\s+per\s*cent|30\s+per\s*cent',
        r'partial.{0,100}(sanction|embargo|restriction)',
        r'(sanction|embargo|restriction).{0,100}partial',
        r'degree\s+of',
        r'coercive\s+(effect|intent|nature|impact)',
        r'(effect|impact).{0,100}coer',
        r'not\s+the\s+(extent|degree|amount|volume)',
        r'coercion\b.{0,300}(intent|effect|purpose|aim)',
        r'total\s+(embargo|ban|prohibition).{0,200}(distinguish|distinct|differ)',
        r'(distinguish|distinct|differ).{0,200}total\s+(embargo|ban)',
    ]
    has_distinction = sum(1 for p in distinction_patterns if re.search(p, content_lower, re.DOTALL)) >= 2
    # Also check mention of GDP impact or economic dependency
    economic_impact = bool(re.search(r'gdp|economic\s+(impact|effect|depend|harm|damage|contraction)', content_lower))
    c7_passed = has_distinction and economic_impact
    checks.append({
        "name": "case_distinction_counter_linkage",
        "passed": c7_passed,
        "detail": f"Distinction patterns found: {sum(1 for p in distinction_patterns if re.search(p, content_lower, re.DOTALL))}/10. Economic impact mentioned: {economic_impact}."
    })

    # -----------------------------------------------
    # CHECK 8: Statement of Facts section - facts without direct legal conclusions
    # Must have a facts section AND it must not begin with legal conclusion language
    # -----------------------------------------------
    has_facts_section = bool(re.search(
        r'(statement\s+of\s+facts?|facts?\s+of\s+the\s+case|factual\s+background|background\s+facts?)',
        content_lower))
    # The facts section should NOT start with legal conclusion language like "A violated" or "A breached"
    facts_match = re.search(
        r'(?:statement\s+of\s+facts?|factual\s+background|background\s+facts?)[^\n]*\n(.*?)(?:##|###|\Z)',
        content_lower, re.DOTALL
    )
    facts_no_direct_conclusion = True
    if facts_match:
        facts_text = facts_match.group(1)[:500]
        # Direct legal conclusions in first 500 chars of facts section = bad
        conclusion_in_facts = bool(re.search(
            r'\b(violated|breached|unlawfully|illegally|wrongfully)\b',
            facts_text[:300]
        ))
        facts_no_direct_conclusion = not conclusion_in_facts
    c8_passed = has_facts_section and facts_no_direct_conclusion
    checks.append({
        "name": "statement_of_facts_no_direct_conclusions",
        "passed": c8_passed,
        "detail": f"Facts section present: {has_facts_section}. Facts avoids direct legal conclusions at start: {facts_no_direct_conclusion}."
    })

    # -----------------------------------------------
    # CHECK 9: Formal legal English - no informal contractions
    # Must not use: isn't, doesn't, can't, won't, didn't, haven't, couldn't, it's (possessive ok)
    # -----------------------------------------------
    informal_contractions = re.findall(
        r"\b(isn't|doesn't|can't|won't|didn't|haven't|couldn't|wouldn't|shouldn't|it's|they're|we're|you're|there's)\b",
        content, re.IGNORECASE
    )
    c9_passed = len(informal_contractions) == 0
    checks.append({
        "name": "formal_legal_english_no_contractions",
        "passed": c9_passed,
        "detail": f"Informal contractions found: {informal_contractions[:5] if informal_contractions else 'None'}. Total: {len(informal_contractions)}."
    })

    # -----------------------------------------------
    # CHECK 10: UN GA Resolution 2625 (1970) or equivalent opinio juris source cited
    # Must cite at least one authoritative source for opinio juris beyond just ICJ cases
    # -----------------------------------------------
    opinio_sources = [
        r'2625',
        r'resolution\s+2625',
        r'friendly\s+relations\s+declaration',
        r'declaration\s+on\s+.{0,50}friendly\s+relations',
        r'ilc.{0,100}(conclusion|report|draft)',
        r'draft\s+conclusion',
        r'identification\s+of\s+customary',
        r'general\s+assembly\s+resolution',
        r'unga\s+res',
    ]
    has_opinio_source = any(re.search(p, content_lower) for p in opinio_sources)
    c10_passed = has_opinio_source
    checks.append({
        "name": "opinio_juris_authoritative_source",
        "passed": c10_passed,
        "detail": f"Authoritative opinio juris source (UNGA Res 2625, ILC conclusions, etc.) cited: {has_opinio_source}."
    })

    # -----------------------------------------------
    # SCORING
    # -----------------------------------------------
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    score = round(passed_checks / total_checks, 4)

    # Overall pass: must pass at least 8/10 checks
    overall_passed = passed_checks >= 8

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation_error", "passed": False, "detail": "Usage: eval_script.py <workspace_dir>"}
        ]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))