import sys
import json
import re
from pathlib import Path
from datetime import datetime

def load(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None

def run_checks(workspace):
    ws = Path(workspace)
    checks = []
    score_total = 0.0

    # ── 1. Find the audit memory file ────────────────────────────────────────
    # Must be at memory/audits/content-refresher/YYYY-MM-DD-*.md
    audit_dir = ws / "memory" / "audits" / "content-refresher"
    audit_files = list(audit_dir.glob("*.md")) if audit_dir.exists() else []

    has_audit_file = len(audit_files) > 0
    checks.append({
        "name": "memory/audits/content-refresher/ directory and dated .md file created",
        "passed": has_audit_file,
        "detail": f"Found {len(audit_files)} file(s): {[f.name for f in audit_files]}" if has_audit_file else "No .md file found under memory/audits/content-refresher/"
    })
    if has_audit_file:
        score_total += 0.10

    audit_content = None
    if has_audit_file:
        audit_content = audit_files[0].read_text(encoding="utf-8", errors="replace")

    # ── 1a. Audit file name follows YYYY-MM-DD-<topic>.md ────────────────────
    if has_audit_file:
        fname = audit_files[0].name
        date_match = re.match(r"^\d{4}-\d{2}-\d{2}-.+\.md$", fname)
        checks.append({
            "name": "Audit filename follows YYYY-MM-DD-<topic>.md convention",
            "passed": bool(date_match),
            "detail": f"Filename: {fname}"
        })
        if date_match:
            score_total += 0.05
    else:
        checks.append({"name": "Audit filename follows YYYY-MM-DD-<topic>.md convention", "passed": False, "detail": "No audit file found"})

    # ── 1b. Audit file contains one-line verdict ──────────────────────────────
    if audit_content:
        has_verdict = bool(re.search(r"verdict|finding|headline|summary|outdated|declining|refresh", audit_content, re.IGNORECASE))
        checks.append({
            "name": "Audit file contains a one-line verdict / headline finding",
            "passed": has_verdict,
            "detail": audit_content[:300] if not has_verdict else "Verdict found"
        })
        if has_verdict:
            score_total += 0.05
    else:
        checks.append({"name": "Audit file contains a one-line verdict / headline finding", "passed": False, "detail": "No audit content"})

    # ── 1c. Audit file contains top actionable items (3-5) ───────────────────
    if audit_content:
        action_matches = re.findall(r"^\s*[-*\d]+[\.\)]\s+.{10,}", audit_content, re.MULTILINE)
        has_actions = len(action_matches) >= 3
        checks.append({
            "name": "Audit file contains at least 3 actionable items",
            "passed": has_actions,
            "detail": f"Found {len(action_matches)} action items"
        })
        if has_actions:
            score_total += 0.05
    else:
        checks.append({"name": "Audit file contains at least 3 actionable items", "passed": False, "detail": "No audit content"})

    # ── 1d. Audit file contains open loops or blockers ───────────────────────
    if audit_content:
        has_open_loops = bool(re.search(r"open.loop|blocker|pending|todo|missing|gap|needed|tbd", audit_content, re.IGNORECASE))
        checks.append({
            "name": "Audit file references open loops or blockers",
            "passed": has_open_loops,
            "detail": "Found" if has_open_loops else "No open loops/blockers section found"
        })
        if has_open_loops:
            score_total += 0.05
    else:
        checks.append({"name": "Audit file references open loops or blockers", "passed": False, "detail": "No audit content"})

    # ── 2. Find main analysis output (may be stdout redirect or a separate file)
    # Agent should produce the main analysis report — search for largest md file in workspace
    all_md = [f for f in ws.rglob("*.md")
              if "memory" not in str(f) and f.stat().st_size > 500]
    main_report_content = None
    if all_md:
        main_report_content = max(all_md, key=lambda f: f.stat().st_size).read_text(encoding="utf-8", errors="replace")

    # Also check memory audit file for rich content
    combined_content = (main_report_content or "") + (audit_content or "")

    # ── 3. CORE-EEAT table present ────────────────────────────────────────────
    # Must have all 8 dimensions: C, O, R, E, Exp, Ept, A, T
    core_eeat_dims = ["Contextual Clarity", "Organization", "Referenceability",
                      "Exclusivity", "Experience", "Expertise", "Authority", "Trust"]
    dims_found = [d for d in core_eeat_dims if re.search(d, combined_content, re.IGNORECASE)]
    has_core_eeat_table = len(dims_found) >= 6
    checks.append({
        "name": "CORE-EEAT Quick Assessment table present with ≥6 of 8 dimensions",
        "passed": has_core_eeat_table,
        "detail": f"Dimensions found: {dims_found} ({len(dims_found)}/8)"
    })
    if has_core_eeat_table:
        score_total += 0.10

    # ── 4. CORE-EEAT uses correct bespoke abbreviation codes ─────────────────
    # Must use the abbreviated codes from skill: C, O, R, E, Exp, Ept, A, T
    abbrev_pattern = r"\b(Exp|Ept)\b"
    has_abbrevs = bool(re.search(abbrev_pattern, combined_content))
    checks.append({
        "name": "CORE-EEAT uses bespoke abbreviations (Exp for Experience, Ept for Expertise)",
        "passed": has_abbrevs,
        "detail": "Found Exp/Ept abbreviations" if has_abbrevs else "Missing bespoke dimension abbreviations — generic EEAT used instead"
    })
    if has_abbrevs:
        score_total += 0.10

    # ── 5. Emoji priority indicators present (🔴, 🟡, 🟢) ────────────────────
    has_red = "🔴" in combined_content
    has_yellow = "🟡" in combined_content
    has_green = "🟢" in combined_content
    emoji_count = sum([has_red, has_yellow, has_green])
    has_emojis = emoji_count >= 2
    checks.append({
        "name": "Priority emoji indicators used (🔴/🟡/🟢)",
        "passed": has_emojis,
        "detail": f"🔴:{has_red}, 🟡:{has_yellow}, 🟢:{has_green}"
    })
    if has_emojis:
        score_total += 0.08

    # ── 6. Content Audit Results table with Traffic Trend column ─────────────
    has_traffic_trend = bool(re.search(r"Traffic.Trend|traffic.trend|\↓|\↑", combined_content, re.IGNORECASE))
    checks.append({
        "name": "Content Audit Results table references traffic trend",
        "passed": has_traffic_trend,
        "detail": "Traffic trend data present" if has_traffic_trend else "Missing traffic trend column/data"
    })
    if has_traffic_trend:
        score_total += 0.07

    # ── 7. Refresh Prioritization Matrix present ─────────────────────────────
    has_matrix = bool(re.search(
        r"high.traffic.+high.decline|high.traffic.+low.decline|prioritiz|refresh.matrix|matrix",
        combined_content, re.IGNORECASE))
    checks.append({
        "name": "Refresh Prioritization Matrix present",
        "passed": has_matrix,
        "detail": "Matrix found" if has_matrix else "No refresh prioritization matrix found"
    })
    if has_matrix:
        score_total += 0.07

    # ── 8. Performance metrics table (6mo ago vs current) ────────────────────
    has_perf_table = bool(re.search(
        r"6.mo|6 months|six months|organic.traffic|avg.position|impressions.+ctr|performance.metric",
        combined_content, re.IGNORECASE))
    checks.append({
        "name": "Performance metrics table (6 months ago vs current) present",
        "passed": has_perf_table,
        "detail": "Performance metrics table found" if has_perf_table else "Missing performance metrics comparison"
    })
    if has_perf_table:
        score_total += 0.07

    # ── 9. Outdated elements table present (year references, statistics) ──────
    has_outdated_elements = bool(re.search(
        r"outdated.element|outdated.info|year.reference|2020|2021.*update|old.stat|broken.link",
        combined_content, re.IGNORECASE))
    checks.append({
        "name": "Outdated elements table identifies specific outdated items (years/stats)",
        "passed": has_outdated_elements,
        "detail": "Outdated elements identified" if has_outdated_elements else "No specific outdated elements table"
    })
    if has_outdated_elements:
        score_total += 0.07

    # ── 10. Missing topics with competitor coverage identified ────────────────
    missing_topics = ["XDR", "Extended Detection", "ransomware-as-a-service", "RaaS",
                      "supply chain", "identity", "MFA fatigue", "AI.*security", "LLM"]
    topics_found = [t for t in missing_topics if re.search(t, combined_content, re.IGNORECASE)]
    has_missing_topics = len(topics_found) >= 2
    checks.append({
        "name": "Missing competitor topics identified (≥2 from XDR, RaaS, supply chain, identity, AI security)",
        "passed": has_missing_topics,
        "detail": f"Found references to: {topics_found}"
    })
    if has_missing_topics:
        score_total += 0.07

    # ── 11. GEO updates section present ──────────────────────────────────────
    has_geo = bool(re.search(r"GEO|ai.citation|quotable|q&a.format|standalone.factual|definition.at.start",
                             combined_content, re.IGNORECASE))
    checks.append({
        "name": "GEO optimization updates section present",
        "passed": has_geo,
        "detail": "GEO section found" if has_geo else "No GEO optimization section"
    })
    if has_geo:
        score_total += 0.05

    # ── 12. hot-cache.md updated with veto-level issue ────────────────────────
    hot_cache_path = ws / "memory" / "hot-cache.md"
    hot_cache_content = load(hot_cache_path)

    if hot_cache_content:
        # Must have a new entry beyond the pre-existing one (phishing-prevention)
        # Look for content-refresher or endpoint-security related veto entry
        # with a CORE-EEAT veto code like T04, C01, R10
        new_veto_entry = bool(re.search(
            r"(endpoint.security|content.refresh|T04|C01|R10|CITE.T0[3,5,9])",
            hot_cache_content, re.IGNORECASE
        ))
        # Also check that there's more content than just the pre-existing entry
        lines = [l.strip() for l in hot_cache_content.strip().splitlines() if l.strip()]
        has_new_entry = len(lines) > 8  # pre-existing has ~5 lines

        hot_cache_updated = new_veto_entry or has_new_entry
        checks.append({
            "name": "memory/hot-cache.md appended with new veto-level issue (no prompting)",
            "passed": hot_cache_updated,
            "detail": f"hot-cache lines: {len(lines)}, veto code match: {new_veto_entry}"
        })
        if hot_cache_updated:
            score_total += 0.07
    else:
        checks.append({
            "name": "memory/hot-cache.md appended with new veto-level issue (no prompting)",
            "passed": False,
            "detail": "hot-cache.md missing or empty"
        })

    # ── 13. Source data references in audit file ──────────────────────────────
    if audit_content:
        has_sources = bool(re.search(
            r"source|analytics|IBM|Ponemon|search.console|SEO.tool|user.provid|estimated|CSV|data",
            audit_content, re.IGNORECASE
        ))
        checks.append({
            "name": "Audit file cites source data references",
            "passed": has_sources,
            "detail": "Source references found" if has_sources else "No source data references in audit file"
        })
        if has_sources:
            score_total += 0.05
    else:
        checks.append({"name": "Audit file cites source data references", "passed": False, "detail": "No audit file"})

    # ── 14. Word count estimate or section location for additions ─────────────
    has_word_counts = bool(re.search(r"\~?\d+\s*words?|\d{2,4}\s*word", combined_content, re.IGNORECASE))
    checks.append({
        "name": "Suggested additions include word count estimates",
        "passed": has_word_counts,
        "detail": "Word counts found" if has_word_counts else "No word count estimates for suggested additions"
    })
    if has_word_counts:
        score_total += 0.06

    # Final score cap at 1.0
    final_score = min(round(score_total, 3), 1.0)
    passed = final_score >= 0.55 and has_audit_file and has_core_eeat_table

    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))