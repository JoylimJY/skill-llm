import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, max_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        max_score += weight
        if passed:
            total_score += weight

    # --- Find the output file ---
    target_files = list(Path(workspace_dir).rglob("research_memo.json"))

    if not target_files:
        add_check("output_file_exists", False, "research_memo.json not found anywhere in workspace", weight=2.0)
        return {"passed": False, "score": 0.0, "checks": checks}

    target_file = target_files[0]
    add_check("output_file_exists", True, f"Found at {target_file}", weight=2.0)

    # --- Parse JSON ---
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            memo = json.load(f)
    except Exception as e:
        add_check("json_parseable", False, f"Failed to parse JSON: {e}", weight=2.0)
        return {"passed": False, "score": 0.0, "checks": checks}

    add_check("json_parseable", True, "JSON parsed successfully", weight=2.0)

    # === CHECK 1: query_plans exists and has at least 3 entries ===
    query_plans = memo.get("query_plans", [])
    has_enough_plans = isinstance(query_plans, list) and len(query_plans) >= 3
    add_check(
        "query_plans_minimum_count",
        has_enough_plans,
        f"Found {len(query_plans)} query plans (need >= 3)",
        weight=1.5
    )

    if not has_enough_plans:
        query_plans = query_plans if isinstance(query_plans, list) else []

    # === CHECK 2: Westlaw proximity operators (NEAR/ or /p or /s) ===
    # These are Westlaw-specific operators from SKILL.md - a generic agent won't know these
    full_text = json.dumps(memo, ensure_ascii=False)
    has_proximity_ops = bool(
        re.search(r'NEAR/\d+', full_text, re.IGNORECASE) or
        re.search(r'\s/p\s', full_text) or
        re.search(r'\s/s\s', full_text) or
        re.search(r'/p\s+', full_text) or
        re.search(r'\s/s\b', full_text)
    )
    add_check(
        "westlaw_proximity_operators_present",
        has_proximity_ops,
        "Must use Westlaw proximity operators like NEAR/3, /p, /s (from SKILL.md advanced query examples)",
        weight=2.0
    )

    # === CHECK 3: SKILL.md-specified databases present (not generic ones) ===
    # Required databases from SKILL.md (must appear at least partially)
    skill_databases = [
        r'oxford\s*(public\s*international\s*law|OPIL)',
        r'OPIL',
        r'HeinOnline',
        r'(Oxford\s*Legal\s*Research\s*Library|OLRL)',
        r'(MPIL|Max\s*Planck)',
        r'Oxford\s*(Law\s*Citator|OLC)',
        r'Westlaw',
        r'ICJ\s*(case\s*law|database|库)',
    ]
    # Must find at least 3 distinct SKILL.md databases
    matched_dbs = []
    for pattern in skill_databases:
        if re.search(pattern, full_text, re.IGNORECASE):
            matched_dbs.append(pattern)

    has_skill_dbs = len(matched_dbs) >= 3
    add_check(
        "skill_specific_databases_referenced",
        has_skill_dbs,
        f"Found {len(matched_dbs)} SKILL.md databases. Must reference OPIL, HeinOnline, Oxford Legal Research Library, MPIL, OLC, Westlaw, or ICJ database (need >= 3)",
        weight=2.0
    )

    # === CHECK 4: Oxford Legal Research Library mapped to Vis/arbitration (not generic) ===
    # SKILL.md explicitly says OLRL is for Vis Moot / commercial arbitration context
    olrl_pattern = r'(Oxford\s*Legal\s*Research\s*Library|OLRL|牛津法律研究图书馆)'
    olrl_present = bool(re.search(olrl_pattern, full_text, re.IGNORECASE))
    
    # Check if it's associated with arbitration/Vis context
    if olrl_present:
        # Find context around OLRL mention
        olrl_match = re.search(olrl_pattern, full_text, re.IGNORECASE)
        if olrl_match:
            start = max(0, olrl_match.start() - 200)
            end = min(len(full_text), olrl_match.end() + 200)
            context = full_text[start:end]
            arbitration_context = bool(re.search(
                r'(arbitrat|Vis|commercial|仲裁)', context, re.IGNORECASE
            ))
        else:
            arbitration_context = False
        add_check(
            "oxford_legal_research_library_arbitration_context",
            arbitration_context,
            "Oxford Legal Research Library must be specifically tied to Vis Moot / commercial arbitration (per SKILL.md, not general int'l law)",
            weight=2.0
        )
    else:
        add_check(
            "oxford_legal_research_library_arbitration_context",
            False,
            "Oxford Legal Research Library not found in memo at all",
            weight=2.0
        )

    # === CHECK 5: keyword_ladder with at least 3 levels ===
    keyword_ladder = memo.get("keyword_ladder", None)
    
    if keyword_ladder is None:
        add_check("keyword_ladder_exists", False, "No 'keyword_ladder' key in JSON", weight=2.0)
        add_check("keyword_ladder_three_levels", False, "keyword_ladder missing", weight=1.5)
    else:
        add_check("keyword_ladder_exists", True, "keyword_ladder key present", weight=2.0)
        
        # Must have broad, narrow, and fallback (3 levels per SKILL.md "收与放")
        ladder_text = json.dumps(keyword_ladder, ensure_ascii=False)
        has_broad = bool(re.search(r'(broad|宽|广|general|wide)', ladder_text, re.IGNORECASE))
        has_narrow = bool(re.search(r'(narrow|限定|精|specific|refined)', ladder_text, re.IGNORECASE))
        has_fallback = bool(re.search(r'(fallback|退|back|alternative|broader|expand|类比|联想)', ladder_text, re.IGNORECASE))
        
        # Also accept structure with at least 3 distinct keys or list items
        if isinstance(keyword_ladder, dict):
            ladder_levels = len(keyword_ladder.keys()) >= 3
        elif isinstance(keyword_ladder, list):
            ladder_levels = len(keyword_ladder) >= 3
        else:
            ladder_levels = False
        
        has_three_levels = (has_broad and has_narrow and has_fallback) or ladder_levels
        add_check(
            "keyword_ladder_three_levels",
            has_three_levels,
            f"Keyword ladder must show broad→narrow→fallback (收与放). Found broad:{has_broad}, narrow:{has_narrow}, fallback:{has_fallback}, structure_levels:{ladder_levels}",
            weight=1.5
        )

    # === CHECK 6: AI guidance section ===
    ai_guidance = memo.get("ai_guidance", None)
    
    if ai_guidance is None:
        add_check("ai_guidance_section_exists", False, "No 'ai_guidance' key in JSON", weight=1.5)
        add_check("ai_cannot_do_fake_citations", False, "ai_guidance missing", weight=1.5)
        add_check("ai_cannot_do_footnote_format", False, "ai_guidance missing", weight=1.5)
        add_check("ai_cannot_do_detail_prose", False, "ai_guidance missing", weight=1.5)
    else:
        add_check("ai_guidance_section_exists", True, "ai_guidance section found", weight=1.5)
        ai_text = json.dumps(ai_guidance, ensure_ascii=False)
        
        # SKILL.md: AI cannot do 3 things:
        # 1. Generate real citations (makes up fake ones)
        # 2. Generate footnote formats (errors)
        # 3. Generate detail prose (inappropriate granularity, incoherent)
        
        cannot_fake_citations = bool(re.search(
            r'(fake|fabricat|hallucin|invent|fictitious|non.?exist|编造|幻觉|假文献|假案例|cite|citation|reference)',
            ai_text, re.IGNORECASE
        ))
        add_check(
            "ai_cannot_do_fake_citations",
            cannot_fake_citations,
            "AI guidance must warn that AI fabricates/hallucinates non-existent citations/cases (key SKILL.md constraint)",
            weight=1.5
        )
        
        cannot_footnote = bool(re.search(
            r'(footnote|脚注|citation format|引用格式|bibliography|参考文献格式)',
            ai_text, re.IGNORECASE
        ))
        add_check(
            "ai_cannot_do_footnote_format",
            cannot_footnote,
            "AI guidance must mention AI cannot reliably generate footnote/citation formats (SKILL.md constraint)",
            weight=1.5
        )
        
        cannot_detail_prose = bool(re.search(
            r'(detail|细节|prose|正文|coherent|连贯|granular|分寸|nuanced|specific text|具体文字)',
            ai_text, re.IGNORECASE
        ))
        add_check(
            "ai_cannot_do_detail_prose",
            cannot_detail_prose,
            "AI guidance must mention AI's limitation in generating detailed/nuanced legal prose (SKILL.md constraint)",
            weight=1.5
        )

    # === CHECK 7: site: domain restriction in at least one query ===
    # SKILL.md shows: site:ejil.org OR site:cilj.co.uk
    has_site_restriction = bool(re.search(r'site:[a-z.]+\.[a-z]+', full_text, re.IGNORECASE))
    add_check(
        "site_domain_restriction_in_query",
        has_site_restriction,
        "At least one query must use site: domain restriction (e.g., site:ejil.org) as shown in SKILL.md",
        weight=1.5
    )

    # === CHECK 8: DATE / temporal operator in at least one query ===
    # SKILL.md shows DATE(AFTER 2000) or BEFORE:2024
    has_date_operator = bool(re.search(
        r'(DATE\s*\(|AFTER\s+\d{4}|BEFORE\s*:\s*\d{4}|BEFORE\s+\d{4}|\bdate\b.*\d{4})',
        full_text, re.IGNORECASE
    ))
    add_check(
        "temporal_date_operator_in_query",
        has_date_operator,
        "At least one query must include a temporal/date operator like DATE(AFTER 2000) or BEFORE:2024 (from SKILL.md examples)",
        weight=1.0
    )

    # === CHECK 9: NOT exclusion operator in at least one query ===
    # SKILL.md shows: NOT "civil procedure"
    has_not_operator = bool(re.search(r'\bNOT\b', full_text))
    add_check(
        "NOT_exclusion_operator_present",
        has_not_operator,
        "At least one query must use NOT exclusion operator (from SKILL.md advanced query examples)",
        weight=1.0
    )

    # === CHECK 10: AUTHOR() field specifier in at least one query ===
    # SKILL.md shows: AUTHOR("Hazel Fox" OR "Roger O'Keefe")
    has_author_field = bool(re.search(r'AUTHOR\s*\(', full_text, re.IGNORECASE))
    add_check(
        "AUTHOR_field_specifier_present",
        has_author_field,
        "At least one query should use AUTHOR() field specifier (from SKILL.md advanced query examples)",
        weight=1.0
    )

    # === CHECK 11: query_plans have database mapping per entry ===
    if query_plans:
        plans_with_db = 0
        for plan in query_plans:
            if isinstance(plan, dict):
                plan_text = json.dumps(plan, ensure_ascii=False)
                # Must have a database field or mention a database name
                if re.search(
                    r'(database|db|库|HeinOnline|Westlaw|OPIL|Oxford|MPIL|ICJ)',
                    plan_text, re.IGNORECASE
                ):
                    plans_with_db += 1
        
        all_plans_mapped = plans_with_db >= len(query_plans)
        add_check(
            "query_plans_each_mapped_to_database",
            all_plans_mapped,
            f"{plans_with_db}/{len(query_plans)} query plans have explicit database mappings",
            weight=1.5
        )
    else:
        add_check(
            "query_plans_each_mapped_to_database",
            False,
            "No query plans to evaluate",
            weight=1.5
        )

    # === FINAL SCORING ===
    score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    
    # Must pass critical checks to overall pass
    critical_checks = [
        "output_file_exists",
        "json_parseable",
        "westlaw_proximity_operators_present",
        "skill_specific_databases_referenced",
        "keyword_ladder_three_levels",
        "ai_cannot_do_fake_citations",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.65

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))