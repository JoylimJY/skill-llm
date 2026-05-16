import sys
import json
import re
from pathlib import Path

def find_report(workspace):
    """Search for the drift report file."""
    candidates = list(Path(workspace).rglob("drift_report.txt"))
    if not candidates:
        return None
    # Prefer one closest to workspace root
    candidates.sort(key=lambda p: len(p.parts))
    return candidates[0]

def load_report(path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return None

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def evaluate(workspace):
    checks = []

    report_path = find_report(workspace)
    if report_path is None:
        checks.append(check("report_file_exists", False, "drift_report.txt not found anywhere in workspace"))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(check("report_file_exists", True, f"Found at {report_path}"))

    content = load_report(report_path)
    if content is None:
        checks.append(check("report_readable", False, "Could not read drift_report.txt"))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(check("report_readable", True, "File readable"))

    # CHECK 1: Has the 🧬 evolution drift report header
    has_header = bool(re.search(r'🧬', content))
    checks.append(check(
        "has_emoji_header",
        has_header,
        "Report must start with 🧬 EVOLUTION DRIFT REPORT header" if not has_header else "🧬 header present"
    ))

    # CHECK 2: Lineage section with all 5 generations
    has_lineage = bool(re.search(r'[Ll]ineage', content))
    all_gens = all(re.search(rf'[Gg]en\s*{i}', content) for i in range(1, 6))
    checks.append(check(
        "lineage_all_generations",
        has_lineage and all_gens,
        "All 5 generations (Gen 1–5) must appear in lineage section" if not (has_lineage and all_gens) else "All 5 gens found in lineage"
    ))

    # CHECK 3: Gen 1 is marked as audited
    gen1_audited = bool(re.search(r'Gen\s*1.*AUDIT', content, re.IGNORECASE)) or \
                   bool(re.search(r'AUDIT.*Gen\s*1', content, re.IGNORECASE)) or \
                   bool(re.search(r'Gen\s*1[^\n]*✅', content)) or \
                   bool(re.search(r'AUDITED', content))
    checks.append(check(
        "gen1_marked_audited",
        gen1_audited,
        "Gen 1 must be marked as the audited original version" if not gen1_audited else "Gen 1 audited marker found"
    ))

    # CHECK 4: Per-generation capability changes section
    per_gen_section = bool(re.search(r'[Pp]er.gen', content, re.IGNORECASE)) or \
                      bool(re.search(r'[Cc]apability changes', content, re.IGNORECASE)) or \
                      bool(re.search(r'[Gg]en\s*[12]\s*[→\-–>]+\s*[Gg]en\s*[23]', content))
    checks.append(check(
        "per_generation_diff_section",
        per_gen_section,
        "Must include per-generation capability change breakdown" if not per_gen_section else "Per-generation diff section found"
    ))

    # CHECK 5: Mutation categories — all four must appear
    mutation_cats = {
        "cosmetic": bool(re.search(r'[Cc]osmetic', content)),
        "functional": bool(re.search(r'[Ff]unctional', content)),
        "capability-expanding": bool(re.search(r'[Cc]apability.expanding', content, re.IGNORECASE)),
        "safety-reducing": bool(re.search(r'[Ss]afety.reducing', content, re.IGNORECASE)),
    }
    all_cats = all(mutation_cats.values())
    missing = [k for k, v in mutation_cats.items() if not v]
    checks.append(check(
        "all_four_mutation_categories",
        all_cats,
        f"Missing mutation categories: {missing}" if not all_cats else "All 4 mutation categories present"
    ))

    # CHECK 6: Capability-expanding changes flagged (Gen 2→3 HTTP, Gen 3→4 remote fetch)
    http_flagged = bool(re.search(r'http', content, re.IGNORECASE))
    remote_flagged = bool(re.search(r'remote', content, re.IGNORECASE)) or \
                     bool(re.search(r'fetch', content, re.IGNORECASE))
    cap_expanding_flagged = http_flagged and remote_flagged
    checks.append(check(
        "capability_expanding_changes_identified",
        cap_expanding_flagged,
        "Must identify HTTP requests (Gen 3) and remote fetching (Gen 4) as capability-expanding changes" if not cap_expanding_flagged else "HTTP and remote fetch changes flagged"
    ))

    # CHECK 7: Safety-reducing change flagged (Gen 4→5 removed amount cap)
    safety_reducing_present = bool(re.search(r'amount', content, re.IGNORECASE)) or \
                               bool(re.search(r'size\s*cap', content, re.IGNORECASE)) or \
                               bool(re.search(r'MAX_AMOUNT', content)) or \
                               bool(re.search(r'removed.*check', content, re.IGNORECASE)) or \
                               bool(re.search(r'check.*removed', content, re.IGNORECASE)) or \
                               bool(re.search(r'removed.*limit', content, re.IGNORECASE)) or \
                               bool(re.search(r'limit.*removed', content, re.IGNORECASE)) or \
                               bool(re.search(r'input.*length', content, re.IGNORECASE))
    # Also check safety-reducing category is mentioned with at least 1 change
    safety_reducing_cat = bool(re.search(r'[Ss]afety.reducing\s*:\s*[1-9]', content)) or \
                          bool(re.search(r'[Ss]afety.reducing[^\n]*change', content, re.IGNORECASE))
    checks.append(check(
        "safety_reducing_change_identified",
        safety_reducing_present and (bool(re.search(r'[Ss]afety.reducing', content, re.IGNORECASE))),
        "Must identify the removed amount/size cap (Gen 5) as a safety-reducing change" if not (safety_reducing_present and bool(re.search(r'[Ss]afety.reducing', content, re.IGNORECASE))) else "Safety-reducing change identified"
    ))

    # CHECK 8: Drift score present as X/100
    drift_score_match = re.search(r'(\d+)\s*/\s*100', content)
    has_drift_score = drift_score_match is not None
    checks.append(check(
        "drift_score_present",
        has_drift_score,
        "Must include a capability drift score in X/100 format" if not has_drift_score else f"Drift score found: {drift_score_match.group(0)}"
    ))

    # CHECK 9: Drift score is high (should be >= 60 given 2 capability-expanding + 1 safety-reducing changes)
    drift_score_high = False
    if drift_score_match:
        score_val = int(drift_score_match.group(1))
        drift_score_high = score_val >= 60
    checks.append(check(
        "drift_score_significant",
        drift_score_high,
        f"Drift score should reflect significant drift (>=60/100) given capability-expanding and safety-reducing changes; got {drift_score_match.group(1) if drift_score_match else 'N/A'}" if not drift_score_high else f"Drift score is appropriately high: {drift_score_match.group(1)}/100"
    ))

    # CHECK 10: Original audit scope listed
    orig_scope = bool(re.search(r'[Oo]riginal\s+audit\s+scope', content, re.IGNORECASE)) or \
                 bool(re.search(r'[Oo]riginal.*scope', content, re.IGNORECASE))
    checks.append(check(
        "original_audit_scope_listed",
        orig_scope,
        "Must list original audit scope from Gen 1" if not orig_scope else "Original audit scope section found"
    ))

    # CHECK 11: Current actual scope shows network/http capabilities not in original
    current_scope = bool(re.search(r'[Cc]urrent.*scope', content, re.IGNORECASE)) or \
                    bool(re.search(r'[Aa]ctual\s+scope', content, re.IGNORECASE))
    checks.append(check(
        "current_scope_listed",
        current_scope,
        "Must list current actual scope showing new capabilities" if not current_scope else "Current scope section found"
    ))

    # CHECK 12: Verdict is RE-AUDIT RECOMMENDED (not WATCH or NO)
    verdict_reaudit = bool(re.search(r'RE.AUDIT\s+RECOMMENDED', content, re.IGNORECASE)) or \
                      bool(re.search(r'RE-AUDIT\s+RECOMMENDED', content, re.IGNORECASE))
    # Should NOT be just WATCH or NO as verdict
    verdict_watch_only = bool(re.search(r'Verdict\s*:\s*WATCH', content, re.IGNORECASE))
    verdict_no_only = bool(re.search(r'Verdict\s*:\s*NO\b', content, re.IGNORECASE))
    correct_verdict = verdict_reaudit and not verdict_watch_only and not verdict_no_only
    checks.append(check(
        "verdict_re_audit_recommended",
        correct_verdict,
        "Given significant drift, verdict must be RE-AUDIT RECOMMENDED" if not correct_verdict else "Correct verdict: RE-AUDIT RECOMMENDED"
    ))

    # CHECK 13: Mutation breakdown section with counts
    has_breakdown = bool(re.search(r'[Mm]utation\s+breakdown', content, re.IGNORECASE)) or \
                    bool(re.search(r'[Mm]utation\s+classification', content, re.IGNORECASE))
    checks.append(check(
        "mutation_breakdown_section",
        has_breakdown,
        "Must include a mutation breakdown/classification section" if not has_breakdown else "Mutation breakdown section found"
    ))

    # Compute score
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)

    # Overall pass: must pass at least 10/13 checks including the key ones
    key_checks = [
        "report_file_exists",
        "all_four_mutation_categories",
        "capability_expanding_changes_identified",
        "safety_reducing_change_identified",
        "drift_score_significant",
        "verdict_re_audit_recommended",
    ]
    key_passed = all(c["passed"] for c in checks if c["name"] in key_checks)
    overall_passed = key_passed and passed_count >= 10

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))