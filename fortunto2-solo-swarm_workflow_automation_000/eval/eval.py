#!/usr/bin/env python3
import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # ── Helper ────────────────────────────────────────────────────────────────
    def make_check(name, passed, detail):
        return {"name": name, "passed": passed, "detail": detail}

    # ── 1. File exists at docs/research.md (not root, not elsewhere) ─────────
    expected_path = workspace / "docs" / "research.md"
    
    # Also search for any research.md to help with diagnosis
    all_research = list(workspace.rglob("research.md"))
    
    try:
        if not expected_path.exists():
            if all_research:
                wrong_locations = [str(p.relative_to(workspace)) for p in all_research]
                detail = f"research.md NOT found at docs/research.md. Found at wrong location(s): {wrong_locations}"
            else:
                detail = "research.md not found anywhere in the workspace. Expected at docs/research.md"
            checks.append(make_check("file_at_correct_location", False, detail))
            # Can't proceed without the file
            score = 0.0
            return {"passed": False, "score": score, "checks": checks}
        else:
            checks.append(make_check(
                "file_at_correct_location",
                True,
                "research.md correctly placed at docs/research.md"
            ))
    except Exception as e:
        checks.append(make_check("file_at_correct_location", False, f"Exception checking file: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Read the file ────────────────────────────────────────────────────────
    try:
        content = expected_path.read_text(encoding="utf-8", errors="replace")
        content_lower = content.lower()
    except Exception as e:
        checks.append(make_check("file_readable", False, f"Cannot read file: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(make_check("file_readable", True, f"File read successfully, {len(content)} chars"))

    # ── 2. File has meaningful content (not just a stub) ─────────────────────
    min_length = 400
    if len(content.strip()) >= min_length:
        checks.append(make_check(
            "sufficient_content_length",
            True,
            f"File has {len(content)} chars (minimum {min_length})"
        ))
    else:
        checks.append(make_check(
            "sufficient_content_length",
            False,
            f"File too short: {len(content)} chars (minimum {min_length}). Content: {content[:200]}"
        ))

    # ── 3. Three researcher perspectives present ─────────────────────────────
    # Market researcher section
    market_patterns = [
        r"market",
        r"competitor",
        r"pricing|price|monetiz",
        r"tam|sam|som|market\s+size",
    ]
    market_hits = sum(1 for p in market_patterns if re.search(p, content_lower))
    market_present = market_hits >= 2
    checks.append(make_check(
        "market_researcher_section_present",
        market_present,
        f"Market research section: {market_hits}/{len(market_patterns)} keywords matched. "
        f"Looked for: market, competitors, pricing, TAM/SAM/SOM"
    ))

    # User researcher section
    user_patterns = [
        r"user|pain\s+point|sentiment|frustrat",
        r"reddit|hacker\s+news|hn\b|ycombinator",
        r"review|feedback|quote|unmet\s+need",
        r"feature\s+request|wish|want",
    ]
    user_hits = sum(1 for p in user_patterns if re.search(p, content_lower))
    user_present = user_hits >= 2
    checks.append(make_check(
        "user_researcher_section_present",
        user_present,
        f"User research section: {user_hits}/{len(user_patterns)} keywords matched. "
        f"Looked for: user/pain points, Reddit/HN, reviews/quotes, feature requests"
    ))

    # Technical analyst section
    tech_patterns = [
        r"tech|technical|stack|implement",
        r"github|open.?source|open source",
        r"feasib|complex|timeline|architect",
        r"integrat|api|library|framework",
    ]
    tech_hits = sum(1 for p in tech_patterns if re.search(p, content_lower))
    tech_present = tech_hits >= 2
    checks.append(make_check(
        "technical_analyst_section_present",
        tech_present,
        f"Technical analysis section: {tech_hits}/{len(tech_patterns)} keywords matched. "
        f"Looked for: tech/stack, GitHub/open-source, feasibility, integration/API"
    ))

    # ── 4. GO / NO-GO / PIVOT recommendation present ─────────────────────────
    # Must have exactly one of GO, NO-GO, or PIVOT as a recommendation
    recommendation_pattern = r'\b(go|no.go|no\s+go|pivot)\b'
    recommendation_matches = re.findall(recommendation_pattern, content_lower)
    
    # Filter for meaningful recommendation context (not just passing mentions)
    rec_context_pattern = r'(recommendation|recommend|decision|verdict|conclusion|result).*?(go|no.go|no\s+go|pivot)|(go|no.go|no\s+go|pivot).*?(recommendation|recommend|decision|verdict|conclusion|result)'
    rec_context = re.search(rec_context_pattern, content_lower, re.DOTALL)
    
    # Also accept if GO/NO-GO/PIVOT appears prominently (header, bold, caps)
    prominent_rec = re.search(r'(?:^|\n|##|###|\*\*)\s*(?:recommendation[:\s]*)?(?:go|no.go|no\s+go|pivot)\s*(?:\*\*)?(?:\n|$|:|\s)', 
                               content, re.MULTILINE | re.IGNORECASE)
    
    has_recommendation = bool(rec_context or prominent_rec or len(recommendation_matches) >= 1)
    checks.append(make_check(
        "go_nogo_pivot_recommendation_present",
        has_recommendation,
        f"GO/NO-GO/PIVOT recommendation: {'FOUND' if has_recommendation else 'NOT FOUND'}. "
        f"Raw matches: {recommendation_matches[:5]}. "
        f"The SKILL.md explicitly requires one of these three recommendations."
    ))

    # ── 5. /validate next step suggestion present ────────────────────────────
    # SKILL.md says: "Suggest next step: `/validate <idea>`"
    validate_pattern = r'/validate'
    has_validate = bool(re.search(validate_pattern, content))
    checks.append(make_check(
        "validate_next_step_suggested",
        has_validate,
        f"'/validate <idea>' next step suggestion: {'FOUND' if has_validate else 'NOT FOUND'}. "
        f"SKILL.md mandates suggesting /validate as the next step after swarm research."
    ))

    # ── 6. Swarm/multi-agent structure reflected (3 agents synthesized) ───────
    # Content should show synthesis from multiple agents, not just one perspective
    synthesis_patterns = [
        r"synthes|summar|combined|overall|across\s+(all|the)\s+(three|3|agent|team|researcher)",
        r"(market|user|tech).*(find|insight|analys|research).*(market|user|tech)",
        r"three|3\s+agent|3\s+researcher|team\s+research|parallel",
        r"lead\s+synthes|agent\s+team|teammate|swarm",
    ]
    synthesis_hits = sum(1 for p in synthesis_patterns if re.search(p, content_lower))
    synthesis_present = synthesis_hits >= 1
    checks.append(make_check(
        "multi_agent_synthesis_reflected",
        synthesis_present,
        f"Evidence of multi-agent swarm synthesis: {synthesis_hits}/{len(synthesis_patterns)} patterns matched. "
        f"Expected synthesis language indicating 3-agent team structure."
    ))

    # ── 7. Topic relevance: must be about the AI code review idea ────────────
    topic_patterns = [
        r"code\s+review|pull\s+request|pr\s+review",
        r"ai.powered|llm|gpt|artificial\s+intel",
        r"dev\s+team|developer|engineering\s+team",
        r"coderabbit|reviewdog|codacy|sonarqube|reviewpad",  # real competitors from mock data
    ]
    topic_hits = sum(1 for p in topic_patterns if re.search(p, content_lower))
    topic_relevant = topic_hits >= 2
    checks.append(make_check(
        "topic_relevance_ai_code_review",
        topic_relevant,
        f"Content relevance to AI code review topic: {topic_hits}/{len(topic_patterns)} domain keywords matched."
    ))

    # ── Scoring ───────────────────────────────────────────────────────────────
    critical_checks = [
        "file_at_correct_location",
        "go_nogo_pivot_recommendation_present",
        "validate_next_step_suggested",
    ]
    quality_checks = [
        "sufficient_content_length",
        "market_researcher_section_present",
        "user_researcher_section_present",
        "technical_analyst_section_present",
        "multi_agent_synthesis_reflected",
        "topic_relevance_ai_code_review",
    ]

    check_map = {c["name"]: c["passed"] for c in checks}

    # All critical checks must pass
    all_critical_pass = all(check_map.get(c, False) for c in critical_checks)
    
    quality_score = sum(1 for c in quality_checks if check_map.get(c, False)) / len(quality_checks)

    if not all_critical_pass:
        score = 0.1 * quality_score  # Partial credit even if critical fails
    else:
        score = 0.5 + 0.5 * quality_score  # 50% for critical, 50% for quality

    passed = all_critical_pass and quality_score >= 0.6

    return {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))