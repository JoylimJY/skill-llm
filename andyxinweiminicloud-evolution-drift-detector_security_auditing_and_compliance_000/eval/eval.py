import sys
import json
import re
import os
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    score = 0.0
    total_weight = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal score, total_weight
        total_weight += weight
        if passed:
            score += weight

    # ------------------------------------------------------------------ #
    # 1. Find the drift report file
    # ------------------------------------------------------------------ #
    report_path = None
    try:
        candidates = list(Path(workspace).rglob("drift_report.txt"))
        if not candidates:
            # also accept .md
            candidates = list(Path(workspace).rglob("drift_report.md"))
        if candidates:
            report_path = candidates[0]
            with open(report_path, "r") as f:
                report_content = f.read()
            add_check("drift_report_exists", True, f"Found report at {report_path}", weight=1.0)
        else:
            add_check("drift_report_exists", False, "No drift_report.txt or drift_report.md found anywhere in workspace", weight=1.0)
            # Hard fail — return early
            return {"passed": False, "score": 0.0, "checks": checks}
    except Exception as e:
        add_check("drift_report_exists", False, f"Error searching for report: {e}", weight=1.0)
        return {"passed": False, "score": 0.0, "checks": checks}

    content = report_content

    # ------------------------------------------------------------------ #
    # 2. Check: Skill name / lineage header is present
    # ------------------------------------------------------------------ #
    try:
        has_skill_name = "config-loader" in content
        add_check(
            "lineage_skill_name",
            has_skill_name,
            "Report must mention 'config-loader' as the skill under analysis",
            weight=1.0
        )
    except Exception as e:
        add_check("lineage_skill_name", False, f"Error: {e}", weight=1.0)

    # ------------------------------------------------------------------ #
    # 3. Check: All 5 generations are present in the lineage tree
    # ------------------------------------------------------------------ #
    try:
        gen_refs = []
        for i in range(1, 6):
            # Accept "Gen 1", "gen1", "Gen1", "generation 1" etc.
            pattern = rf"[Gg]en[\s_\-]?{i}|[Gg]eneration[\s_\-]?{i}"
            if re.search(pattern, content):
                gen_refs.append(i)
        all_gens = len(gen_refs) == 5
        add_check(
            "all_generations_present",
            all_gens,
            f"Generations found: {gen_refs}. Expected all 5 (1-5).",
            weight=1.5
        )
    except Exception as e:
        add_check("all_generations_present", False, f"Error: {e}", weight=1.5)

    # ------------------------------------------------------------------ #
    # 4. Check: Gen 1 is marked as AUDITED (original verified badge)
    # ------------------------------------------------------------------ #
    try:
        # Must reference gen1 audit, @securitylab author, and audited status
        has_audit_marker = bool(re.search(r"(AUDIT(ED)?|audit|verified|@securitylab)", content, re.IGNORECASE))
        has_gen1_audit = bool(re.search(r"[Gg]en[\s_\-]?1.{0,80}(AUDIT|audit|verified)", content, re.DOTALL))
        passed = has_audit_marker and has_gen1_audit
        add_check(
            "gen1_audited_marker",
            passed,
            f"Gen 1 must be marked as audited/verified. audit_marker={has_audit_marker}, gen1_audit={has_gen1_audit}",
            weight=1.0
        )
    except Exception as e:
        add_check("gen1_audited_marker", False, f"Error: {e}", weight=1.0)

    # ------------------------------------------------------------------ #
    # 5. Check: Per-generation capability changes are listed
    #    Gen1→2: csv_parsing (functional)
    #    Gen2→3: http_requests (capability-expanding)
    #    Gen3→4: remote_fetch/remote_schema_fetch (capability-expanding)
    #    Gen4→5: removed input size cap (safety-reducing) + env_read (capability-expanding)
    # ------------------------------------------------------------------ #
    try:
        has_csv = bool(re.search(r"csv", content, re.IGNORECASE))
        add_check("gen1_to_2_csv_parsing", has_csv, "Report must mention CSV parsing addition (Gen1→2)", weight=1.0)
    except Exception as e:
        add_check("gen1_to_2_csv_parsing", False, f"Error: {e}", weight=1.0)

    try:
        has_http = bool(re.search(r"http[_\-\s]?(request|access|call|fallback)", content, re.IGNORECASE))
        add_check("gen2_to_3_http_requests", has_http, "Report must mention HTTP requests addition (Gen2→3)", weight=1.5)
    except Exception as e:
        add_check("gen2_to_3_http_requests", False, f"Error: {e}", weight=1.5)

    try:
        has_remote = bool(re.search(r"remote[_\-\s]?(fetch|schema|fetch)", content, re.IGNORECASE))
        add_check("gen3_to_4_remote_fetch", has_remote, "Report must mention remote fetch/schema addition (Gen3→4)", weight=1.5)
    except Exception as e:
        add_check("gen3_to_4_remote_fetch", False, f"Error: {e}", weight=1.5)

    try:
        # Gen4→5: removed input size validation
        has_removed_size = bool(re.search(r"(input[\s_\-]?(size|length|cap|limit)|max_input|size[\s_\-]?cap|size[\s_\-]?limit|unbounded)", content, re.IGNORECASE))
        add_check("gen4_to_5_removed_size_check", has_removed_size,
                  "Report must mention removal of input size cap (Gen4→5) as safety-reducing", weight=1.5)
    except Exception as e:
        add_check("gen4_to_5_removed_size_check", False, f"Error: {e}", weight=1.5)

    try:
        # Gen4→5: env var expansion
        has_env = bool(re.search(r"env(ironment)?[\s_\-]?(var|read|expand|access)", content, re.IGNORECASE))
        add_check("gen4_to_5_env_read", has_env, "Report must mention environment variable access addition (Gen4→5)", weight=1.0)
    except Exception as e:
        add_check("gen4_to_5_env_read", False, f"Error: {e}", weight=1.0)

    # ------------------------------------------------------------------ #
    # 6. Check: Mutation classification categories are used
    #    Must use at least 3 of: cosmetic, functional, capability-expanding, safety-reducing
    # ------------------------------------------------------------------ #
    try:
        categories = {
            "cosmetic": bool(re.search(r"cosmetic", content, re.IGNORECASE)),
            "functional": bool(re.search(r"functional", content, re.IGNORECASE)),
            "capability-expanding": bool(re.search(r"capability[\s_\-]?expand", content, re.IGNORECASE)),
            "safety-reducing": bool(re.search(r"safety[\s_\-]?reduc", content, re.IGNORECASE)),
        }
        found_cats = [k for k, v in categories.items() if v]
        passed = len(found_cats) >= 3
        add_check(
            "mutation_classification_categories",
            passed,
            f"Must use at least 3 of 4 mutation categories. Found: {found_cats}",
            weight=2.0
        )
    except Exception as e:
        add_check("mutation_classification_categories", False, f"Error: {e}", weight=2.0)

    # ------------------------------------------------------------------ #
    # 7. Check: Capability drift score (0-100 numeric value present)
    # ------------------------------------------------------------------ #
    try:
        # Look for a numeric score like "XX/100" or "score: XX" or "drift score: XX"
        score_match = re.search(r"(\d{1,3})\s*/\s*100", content)
        if not score_match:
            score_match = re.search(r"(drift[\s_\-]?score|capability[\s_\-]?drift)[:\s]+(\d{1,3})", content, re.IGNORECASE)
        has_score = score_match is not None
        score_value = None
        if score_match:
            groups = score_match.groups()
            # Extract the numeric part
            num_str = groups[-1]  # last group is always the number
            score_value = int(num_str)

        add_check(
            "drift_score_present",
            has_score,
            f"Report must include a numeric capability drift score (0-100). Found: {score_value}",
            weight=2.0
        )
    except Exception as e:
        add_check("drift_score_present", False, f"Error: {e}", weight=2.0)

    # ------------------------------------------------------------------ #
    # 8. Check: Drift score is >= 50 (given 2 capability-expanding + 1 safety-reducing changes)
    #    The SKILL.md example shows 78 for a similar profile. We require a significant score.
    # ------------------------------------------------------------------ #
    try:
        score_num = None
        m = re.search(r"(\d{1,3})\s*/\s*100", content)
        if m:
            score_num = int(m.group(1))
        else:
            m2 = re.search(r"(drift[\s_\-]?score|capability[\s_\-]?drift)[:\s]+(\d{1,3})", content, re.IGNORECASE)
            if m2:
                score_num = int(m2.group(2))

        if score_num is not None:
            is_significant = score_num >= 50
            add_check(
                "drift_score_significant",
                is_significant,
                f"Drift score {score_num}/100 — must be >= 50 given 2 capability-expanding and 1 safety-reducing mutations",
                weight=1.5
            )
        else:
            add_check(
                "drift_score_significant",
                False,
                "Could not extract numeric drift score to check significance",
                weight=1.5
            )
    except Exception as e:
        add_check("drift_score_significant", False, f"Error: {e}", weight=1.5)

    # ------------------------------------------------------------------ #
    # 9. Check: Original audit scope vs current actual scope
    # ------------------------------------------------------------------ #
    try:
        has_original_scope = bool(re.search(r"(original[\s_\-]?audit[\s_\-]?scope|original[\s_\-]?scope|audited[\s_\-]?scope)", content, re.IGNORECASE))
        has_current_scope = bool(re.search(r"(current[\s_\-]?(actual[\s_\-]?)?scope|current[\s_\-]?capabilities)", content, re.IGNORECASE))
        has_file_read_in_scope = bool(re.search(r"file[\s_\-]?read", content, re.IGNORECASE))
        # Ensure network/remote is in current scope description
        has_network_in_current = bool(re.search(r"(network|http|remote)", content, re.IGNORECASE))
        passed = has_original_scope and has_current_scope and has_file_read_in_scope and has_network_in_current
        add_check(
            "original_vs_current_scope",
            passed,
            f"Report must contrast original audit scope (file-read) vs current scope (includes network). "
            f"original={has_original_scope}, current={has_current_scope}, file_read={has_file_read_in_scope}, network={has_network_in_current}",
            weight=2.0
        )
    except Exception as e:
        add_check("original_vs_current_scope", False, f"Error: {e}", weight=2.0)

    # ------------------------------------------------------------------ #
    # 10. Check: Re-audit verdict is present and is RE-AUDIT RECOMMENDED
    #     Given high drift score (capability-expanding + safety-reducing), must be YES/RE-AUDIT
    # ------------------------------------------------------------------ #
    try:
        # Accept "RE-AUDIT RECOMMENDED", "REAUDIT RECOMMENDED", "YES" (in verdict context), "RE-AUDIT: YES"
        verdict_match = re.search(
            r"(RE[\s_\-]?AUDIT[\s_\-]?RECOMMENDED|VERDICT[\s:]+RE[\s_\-]?AUDIT|verdict[\s:]+yes|RE[\s_\-]?AUDIT[\s:]+YES|⚠️.*RE[\s_\-]?AUDIT)",
            content,
            re.IGNORECASE
        )
        has_verdict = verdict_match is not None
        add_check(
            "reaudit_verdict",
            has_verdict,
            f"Report must include RE-AUDIT RECOMMENDED verdict given significant capability drift. Match: {verdict_match}",
            weight=2.5
        )
    except Exception as e:
        add_check("reaudit_verdict", False, f"Error: {e}", weight=2.5)

    # ------------------------------------------------------------------ #
    # 11. Check: 🧬 emoji present (proprietary format marker from SKILL.md)
    # ------------------------------------------------------------------ #
    try:
        has_emoji = "🧬" in content
        add_check(
            "dna_emoji_header",
            has_emoji,
            "Report must include the 🧬 emoji as a header marker (per SKILL.md format specification)",
            weight=1.0
        )
    except Exception as e:
        add_check("dna_emoji_header", False, f"Error: {e}", weight=1.0)

    # ------------------------------------------------------------------ #
    # 12. Check: Mutation breakdown counts are plausible
    #     Must show counts for each category
    # ------------------------------------------------------------------ #
    try:
        # Looking for numeric counts next to category names
        has_cosmetic_count = bool(re.search(r"[Cc]osmetic[:\s]+\d+|\d+\s+cosmetic", content, re.IGNORECASE))
        has_functional_count = bool(re.search(r"[Ff]unctional[:\s]+\d+|\d+\s+functional", content, re.IGNORECASE))
        has_capexp_count = bool(re.search(r"[Cc]apability[\s_\-]?[Ee]xpand\w*[:\s]+\d+|\d+\s+capability[\s_\-]?expand", content, re.IGNORECASE))
        has_safety_count = bool(re.search(r"[Ss]afety[\s_\-]?[Rr]educ\w*[:\s]+\d+|\d+\s+safety[\s_\-]?reduc", content, re.IGNORECASE))
        found_counts = sum([has_cosmetic_count, has_functional_count, has_capexp_count, has_safety_count])
        passed = found_counts >= 3
        add_check(
            "mutation_breakdown_counts",
            passed,
            f"Report must show numeric counts for at least 3 mutation categories. "
            f"cosmetic={has_cosmetic_count}, functional={has_functional_count}, cap-expanding={has_capexp_count}, safety-reducing={has_safety_count}",
            weight=1.5
        )
    except Exception as e:
        add_check("mutation_breakdown_counts", False, f"Error: {e}", weight=1.5)

    # ------------------------------------------------------------------ #
    # Final scoring
    # ------------------------------------------------------------------ #
    final_score = score / total_weight if total_weight > 0 else 0.0
    passed_all = final_score >= 0.75  # 75% threshold to pass

    return {
        "passed": passed_all,
        "score": round(final_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))