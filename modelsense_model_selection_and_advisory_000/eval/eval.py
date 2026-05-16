import sys
import json
import re
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # ── Locate the output file ───────────────────────────────────────────────
    candidates = list(workspace_path.rglob("model_recommendation.txt"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found {len(candidates)} file(s) named model_recommendation.txt" if file_found else "model_recommendation.txt not found anywhere in workspace"
    })

    if not file_found:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    try:
        content = candidates[0].read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    content_lower = content.lower()

    # ── CHECK 1: Correct primary model (claude-opus-4-6, NOT o3) ────────────
    # o3 is the benchmark leader for math/research but is NOT available (openai provider
    # is partially available - only gpt-4o configured, o3 is not listed).
    # Agent must have run `openclaw models list` and discovered o3 is unavailable.
    recommends_opus = bool(re.search(r'claude-opus-4-6', content, re.IGNORECASE))
    recommends_o3_as_primary = bool(re.search(
        r'(?:recommended?|🎯)[^\n]*o3', content, re.IGNORECASE
    ))
    provider_filter_applied = recommends_opus and not recommends_o3_as_primary
    checks.append({
        "name": "provider_filter_applied_correctly",
        "passed": provider_filter_applied,
        "detail": (
            f"claude-opus-4-6 recommended: {recommends_opus}, "
            f"o3 incorrectly set as primary: {recommends_o3_as_primary}. "
            "Agent must run openclaw models list and exclude o3 as primary (not configured)"
        )
    })

    # ── CHECK 2: Correct effort level = research ─────────────────────────────
    # Task is "prove a mathematical conjecture" → research-grade → effort=research
    effort_research = bool(re.search(r'\bresearch\b', content_lower))
    checks.append({
        "name": "effort_level_is_research",
        "passed": effort_research,
        "detail": f"Effort level 'research' found in output: {effort_research}. Task is conjecture verification → research-grade complexity."
    })

    # ── CHECK 3: thinking=high specified ────────────────────────────────────
    # SKILL.md: research effort → "Opus + thinking=high"
    # Must appear in Special field or reasoning
    thinking_high = bool(re.search(r'thinking[=:\s]+high', content_lower))
    checks.append({
        "name": "thinking_high_specified",
        "passed": thinking_high,
        "detail": f"'thinking=high' or 'thinking: high' found: {thinking_high}. Required per effort×model matrix for research effort."
    })

    # ── CHECK 4: Correct benchmark citations (MATH, AIME, and/or GPQA/BBH) ──
    # Math + research-grade conjecture → MATH, AIME are primary; GPQA/BBH acceptable too
    math_bench = bool(re.search(r'\bmath\b', content_lower))
    aime_bench = bool(re.search(r'\baime\b', content_lower))
    gpqa_bench = bool(re.search(r'\bgpqa\b', content_lower))
    bbh_bench  = bool(re.search(r'\bbbh\b', content_lower))
    relevant_benchmarks_cited = (math_bench or aime_bench) and (gpqa_bench or bbh_bench or aime_bench or math_bench)
    # At minimum MATH or AIME must be cited
    at_least_math_or_aime = math_bench or aime_bench
    checks.append({
        "name": "relevant_benchmarks_cited",
        "passed": at_least_math_or_aime,
        "detail": (
            f"MATH: {math_bench}, AIME: {aime_bench}, GPQA: {gpqa_bench}, BBH: {bbh_bench}. "
            "At least MATH or AIME must be cited for mathematical conjecture task."
        )
    })

    # ── CHECK 5: Required output format with emoji fields ────────────────────
    # SKILL.md mandates: 🎯 Recommended:, ⚡ Effort:, 📊 Why:, 🔧 Special:, 💰 Cost estimate:
    emoji_checks = {
        "🎯": bool(re.search(r'🎯', content)),
        "⚡": bool(re.search(r'⚡', content)),
        "📊": bool(re.search(r'📊', content)),
        "🔧": bool(re.search(r'🔧', content)),
        "💰": bool(re.search(r'💰', content)),
    }
    emoji_passed = sum(emoji_checks.values())
    format_valid = emoji_passed >= 4  # at least 4 of 5 emoji fields present
    checks.append({
        "name": "proprietary_output_format_emoji_fields",
        "passed": format_valid,
        "detail": f"Emoji fields present: {emoji_checks}. Need ≥4/5. Got {emoji_passed}/5."
    })

    # ── CHECK 6: Alternatives section present ────────────────────────────────
    has_alternatives = bool(re.search(r'alternatives?', content_lower))
    checks.append({
        "name": "alternatives_section_present",
        "passed": has_alternatives,
        "detail": f"'Alternatives' section found: {has_alternatives}. Required by SKILL.md output format."
    })

    # ── CHECK 7: Does NOT recommend o3 as only/unavailable-but-presented option
    # o3 may appear as an alternative with a caveat (provider not configured), 
    # but should NOT be presented as if it's the primary recommended available model.
    # If o3 appears, there should be a note about it being unavailable/not configured.
    o3_mentioned = bool(re.search(r'\bo3\b', content, re.IGNORECASE))
    if o3_mentioned:
        o3_caveat = bool(re.search(
            r'(?:not (?:available|configured)|unavailable|requires?.{0,30}openai|provider not)',
            content_lower
        ))
        o3_handling_ok = o3_caveat  # if mentioned, must have caveat
    else:
        o3_handling_ok = True  # not mentioned at all is fine
    checks.append({
        "name": "o3_provider_availability_noted",
        "passed": o3_handling_ok,
        "detail": (
            f"o3 mentioned: {o3_mentioned}. "
            f"If mentioned, caveat about unavailability present: {o3_caveat if o3_mentioned else 'N/A'}. "
            "o3 must either be absent or flagged as not configured."
        )
    })

    # ── CHECK 8: Task domain classification present ──────────────────────────
    # Agent must classify: math + research-grade
    domain_math = bool(re.search(r'\bmath(?:ematics|ematical)?\b', content_lower))
    domain_research = bool(re.search(r'\bresearch(?:-grade|grade)?\b', content_lower))
    domain_classified = domain_math and domain_research
    checks.append({
        "name": "task_domain_correctly_classified",
        "passed": domain_classified,
        "detail": (
            f"Math domain: {domain_math}, Research-grade complexity: {domain_research}. "
            "Both required for conjecture verification task."
        )
    })

    # ── Final scoring ─────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = len(passed_checks) / total

    # Hard gates: provider filter + effort level + thinking mode are mandatory
    hard_gates = [
        "provider_filter_applied_correctly",
        "effort_level_is_research",
        "thinking_high_specified",
    ]
    hard_gate_passed = all(
        any(c["name"] == g and c["passed"] for c in checks)
        for g in hard_gates
    )

    overall_passed = hard_gate_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))