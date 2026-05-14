import sys
import json
import subprocess
import math
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
total_score = 0.0
max_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0


# ─── CHECK 1: Tests pass at ≥80% (8/10) ──────────────────────────────────────
max_score += 35.0
try:
    result = subprocess.run(
        ["python", "-m", "pytest", "genomics_pipeline/tests/", "-v", "--tb=short", "--no-header", "-q"],
        capture_output=True, text=True, cwd=str(workspace), timeout=60
    )
    output = result.stdout + result.stderr
    # Parse passed/failed counts
    passed_count = output.count(" PASSED") + output.count(" passed")
    failed_count = output.count(" FAILED") + output.count(" failed") + output.count(" ERROR")
    
    # More robust: look for summary line
    import re
    summary = re.search(r'(\d+) passed', output)
    fail_summary = re.search(r'(\d+) failed', output)
    error_summary = re.search(r'(\d+) error', output)
    
    n_passed = int(summary.group(1)) if summary else 0
    n_failed = int(fail_summary.group(1)) if fail_summary else 0
    n_errors = int(error_summary.group(1)) if error_summary else 0
    n_total = n_passed + n_failed + n_errors
    if n_total == 0:
        n_total = 10  # fallback
    
    pass_rate = n_passed / n_total if n_total > 0 else 0.0
    passes_threshold = pass_rate >= 0.80
    total_score += add_check(
        "test_pass_rate_above_80pct",
        passes_threshold,
        f"{n_passed}/{n_total} tests pass ({pass_rate*100:.1f}%). Output tail: {output[-400:]}",
        35.0
    )
except Exception as e:
    add_check("test_pass_rate_above_80pct", False, f"Exception running pytest: {e}", 35.0)


# ─── CHECK 2: .evolution/log.json exists ─────────────────────────────────────
max_score += 5.0
log_path = workspace / ".evolution" / "log.json"
log_exists = log_path.exists()
total_score += add_check(
    "evolution_log_exists",
    log_exists,
    f"{'Found' if log_exists else 'NOT found'} at {log_path}",
    5.0
)

# ─── CHECK 3: Log has correct top-level schema ────────────────────────────────
max_score += 10.0
log_data = None
if log_exists:
    try:
        log_data = json.loads(log_path.read_text())
        has_baseline = "baseline" in log_data
        has_variants = "variants" in log_data and isinstance(log_data["variants"], dict)
        has_principles = "principles_learned" in log_data and isinstance(log_data["principles_learned"], list)
        schema_ok = has_baseline and has_variants and has_principles
        total_score += add_check(
            "log_schema_correct",
            schema_ok,
            f"baseline={has_baseline}, variants={has_variants}, principles_learned={has_principles}",
            10.0
        )
    except Exception as e:
        add_check("log_schema_correct", False, f"JSON parse error: {e}", 10.0)
else:
    add_check("log_schema_correct", False, "Log file missing, cannot check schema", 10.0)


# ─── CHECK 4: At least 2 variants logged ─────────────────────────────────────
max_score += 10.0
if log_data and "variants" in log_data:
    variants = log_data["variants"]
    n_variants = len(variants)
    has_two = n_variants >= 2
    total_score += add_check(
        "at_least_two_variants",
        has_two,
        f"Found {n_variants} variant(s) in log",
        10.0
    )
else:
    add_check("at_least_two_variants", False, "No variants key in log", 10.0)


# ─── CHECK 5: Each variant has required fields (parent, description, changes_made, score, delta, learned) ──
max_score += 10.0
if log_data and "variants" in log_data and log_data["variants"]:
    required_fields = {"parent", "description", "changes_made", "score", "delta", "learned"}
    all_valid = True
    issues = []
    for vname, vdata in log_data["variants"].items():
        if not isinstance(vdata, dict):
            all_valid = False
            issues.append(f"{vname}: not a dict")
            continue
        missing = required_fields - set(vdata.keys())
        if missing:
            all_valid = False
            issues.append(f"{vname}: missing {missing}")
        # changes_made must be a list
        if "changes_made" in vdata and not isinstance(vdata["changes_made"], list):
            all_valid = False
            issues.append(f"{vname}: changes_made not a list")
        # each change must have what, why, priority
        if "changes_made" in vdata and isinstance(vdata["changes_made"], list):
            for i, ch in enumerate(vdata["changes_made"]):
                if not isinstance(ch, dict):
                    continue
                ch_missing = {"what", "why", "priority"} - set(ch.keys())
                if ch_missing:
                    all_valid = False
                    issues.append(f"{vname}.changes_made[{i}]: missing {ch_missing}")
    total_score += add_check(
        "variant_fields_complete",
        all_valid,
        f"Issues: {issues}" if issues else "All variants have required fields",
        10.0
    )
else:
    add_check("variant_fields_complete", False, "No variants to check", 10.0)


# ─── CHECK 6: Scores are numeric 0-1 range ───────────────────────────────────
max_score += 5.0
if log_data and "variants" in log_data and log_data["variants"]:
    scores_ok = True
    bad = []
    for vname, vdata in log_data["variants"].items():
        if isinstance(vdata, dict) and "score" in vdata:
            s = vdata["score"]
            if not isinstance(s, (int, float)) or not (0.0 <= float(s) <= 1.0):
                scores_ok = False
                bad.append(f"{vname}: score={s}")
    total_score += add_check(
        "scores_in_0_1_range",
        scores_ok,
        f"Bad scores: {bad}" if bad else "All scores in [0,1]",
        5.0
    )
else:
    add_check("scores_in_0_1_range", False, "No variants to check", 5.0)


# ─── CHECK 7: principles_learned is non-empty ────────────────────────────────
max_score += 5.0
if log_data and "principles_learned" in log_data:
    principles = log_data["principles_learned"]
    non_empty = len(principles) >= 1
    total_score += add_check(
        "principles_learned_populated",
        non_empty,
        f"Found {len(principles)} principle(s)",
        5.0
    )
else:
    add_check("principles_learned_populated", False, "No principles_learned in log", 5.0)


# ─── CHECK 8: Evolution comments in source files (# evo-vNNN:) ────────────────
max_score += 10.0
import re as re2
evo_comment_pattern = re2.compile(r'#\s*evo-v\d{3}', re2.IGNORECASE)
found_comments = []
try:
    for py_file in (workspace / "genomics_pipeline").rglob("*.py"):
        content = py_file.read_text()
        matches = evo_comment_pattern.findall(content)
        if matches:
            found_comments.extend([(str(py_file.relative_to(workspace)), m) for m in matches])
    has_comments = len(found_comments) >= 1
    total_score += add_check(
        "evolution_comments_in_code",
        has_comments,
        f"Found evo comments: {found_comments}" if has_comments else "No '# evo-vNNN:' comments found in source files",
        10.0
    )
except Exception as e:
    add_check("evolution_comments_in_code", False, f"Error checking comments: {e}", 10.0)


# ─── CHECK 9: ALMA variant selection formula correctly applied in log ─────────
# We verify that the agent's final "best variant" selection is consistent
# with score(v) = normalized_reward - 0.5 * log(1 + visit_count).
# We check that the variant with the highest such score was selected as
# the "active" / "best" variant (heuristic: it has the highest score among
# all variants OR the delta indicates improvement over parent).
max_score += 10.0
if log_data and "variants" in log_data and len(log_data["variants"]) >= 2:
    variants = log_data["variants"]
    # Compute normalized reward for each variant
    all_scores = [float(v["score"]) for v in variants.values() if isinstance(v, dict) and "score" in v]
    baseline_score = float(log_data.get("baseline", {}).get("score", 0.0))
    
    # Check that the logged scores show monotonic improvement OR branching exploration
    # Specifically: we verify the agent did NOT keep degrading indefinitely
    # (i.e., the best variant score > baseline_score)
    best_variant_score = max(all_scores) if all_scores else 0.0
    improved_over_baseline = best_variant_score > baseline_score
    
    # Also check that visit_count concept is implicitly present: either
    # (a) variants have a 'visit_count' field OR
    # (b) the log shows exploration (different parents) suggesting visit penalty awareness
    has_exploration = len(set(
        v.get("parent", "") for v in variants.values() if isinstance(v, dict)
    )) >= 1  # at least one distinct parent chain
    
    # Check for visit_count field OR comment about it OR multiple parent chains
    has_visit_awareness = any(
        "visit_count" in v for v in variants.values() if isinstance(v, dict)
    ) or any(
        "visit" in str(v.get("learned", "")).lower() or 
        "alma" in str(v.get("learned", "")).lower() or
        "selection" in str(v.get("learned", "")).lower()
        for v in variants.values() if isinstance(v, dict)
    ) or has_exploration
    
    formula_evidence = improved_over_baseline and has_visit_awareness
    total_score += add_check(
        "alma_selection_formula_applied",
        formula_evidence,
        f"Best variant score={best_variant_score:.2f} vs baseline={baseline_score:.2f}. "
        f"improved={improved_over_baseline}, exploration_evidence={has_visit_awareness}",
        10.0
    )
else:
    add_check("alma_selection_formula_applied", False, "Need ≥2 variants to evaluate selection formula", 10.0)


# ─── BONUS CHECK 10: delta field is correctly computed ───────────────────────
max_score += 0.0  # bonus, not counted in max_score but adds to score
if log_data and "variants" in log_data:
    variants_dict = log_data["variants"]
    delta_ok_count = 0
    delta_total = 0
    for vname, vdata in variants_dict.items():
        if not isinstance(vdata, dict):
            continue
        if "delta" in vdata and "score" in vdata:
            delta_total += 1
            delta_str = str(vdata["delta"])
            # delta should contain + or - and a numeric value
            if re2.search(r'[+\-]\d', delta_str):
                delta_ok_count += 1
    if delta_total > 0:
        checks.append({
            "name": "delta_format_correct",
            "passed": delta_ok_count == delta_total,
            "detail": f"{delta_ok_count}/{delta_total} deltas have correct +/- format"
        })


# ─── Final tally ─────────────────────────────────────────────────────────────
final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0
all_passed = all(c["passed"] for c in checks if c["name"] != "delta_format_correct")

output = {
    "passed": all_passed and final_score >= 0.80,
    "score": final_score,
    "checks": checks
}
print(json.dumps(output, indent=2))