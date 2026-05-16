import sys
import json
import os
from pathlib import Path

def load_json_report(workspace: str):
    """Find and load the performance_review.json file."""
    candidates = list(Path(workspace).rglob("performance_review.json"))
    if not candidates:
        return None, "performance_review.json not found anywhere in workspace"
    # Prefer the most recently modified if multiple found
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    with open(candidates[0], "r") as f:
        return json.load(f), str(candidates[0])

def run_checks(workspace: str):
    checks = []
    total_score = 0.0
    max_score = 0.0

    # ── Load report ────────────────────────────────────────────────────────────
    report = None
    report_path = None
    try:
        report, report_path = load_json_report(workspace)
        if report is None:
            checks.append({"name": "report_file_exists", "passed": False,
                           "detail": report_path})
            return checks, 0.0
        checks.append({"name": "report_file_exists", "passed": True,
                       "detail": f"Found at {report_path}"})
    except Exception as e:
        checks.append({"name": "report_file_exists", "passed": False,
                       "detail": f"Error reading report: {e}"})
        return checks, 0.0

    # ── CHECK 1: review_verified field present and true (from review-verification-protocol) ──
    max_score += 1.0
    try:
        rv = report.get("review_verified", None)
        passed = rv is True
        checks.append({
            "name": "review_verified_field_true",
            "passed": passed,
            "detail": f"review_verified={rv!r}; expected True (per review-verification-protocol)"
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "review_verified_field_true", "passed": False, "detail": str(e)})

    # ── CHECK 2: findings is a non-empty list ──────────────────────────────────
    max_score += 0.5
    try:
        findings = report.get("findings", [])
        passed = isinstance(findings, list) and len(findings) > 0
        checks.append({
            "name": "findings_is_nonempty_list",
            "passed": passed,
            "detail": f"findings count={len(findings) if isinstance(findings, list) else 'N/A'}"
        })
        if passed:
            total_score += 0.5
    except Exception as e:
        checks.append({"name": "findings_is_nonempty_list", "passed": False, "detail": str(e)})
        findings = []

    if not isinstance(findings, list):
        findings = []

    # Helper: check if a finding targets a specific file + issue type
    def has_finding(file_substr: str, category: str, min_severity: list = None):
        """Returns matching findings list."""
        results = []
        for f in findings:
            file_match = file_substr.lower() in str(f.get("file", "")).lower()
            cat_match = f.get("category", "").lower() == category.lower()
            if file_match and cat_match:
                if min_severity:
                    if f.get("severity", "") in min_severity:
                        results.append(f)
                else:
                    results.append(f)
        return results

    def all_verified(finding_list):
        return all(f.get("verified") is True for f in finding_list)

    # ── CHECK 3: GenServer bottleneck in transaction_router.ex FLAGGED ─────────
    # Must be flagged: handles ~5000 req/sec (> 1000 threshold) AND has blocking I/O
    max_score += 2.0
    try:
        matches = has_finding("transaction_router", "genserver_bottleneck",
                              min_severity=["high", "critical"])
        passed = len(matches) > 0 and all_verified(matches)
        checks.append({
            "name": "flags_transaction_router_genserver_bottleneck",
            "passed": passed,
            "detail": (f"Found {len(matches)} high/critical genserver_bottleneck finding(s) "
                       f"for transaction_router.ex with verified=true. "
                       "Expected: flagged (5000 req/sec > 1000 threshold + blocking HTTP in handle_call)")
        })
        if passed:
            total_score += 2.0
    except Exception as e:
        checks.append({"name": "flags_transaction_router_genserver_bottleneck",
                       "passed": False, "detail": str(e)})

    # ── CHECK 4: Unsupervised Task.async in transaction_router.ex FLAGGED ─────
    max_score += 1.5
    try:
        matches = has_finding("transaction_router", "concurrency")
        passed = len(matches) > 0 and all_verified(matches)
        checks.append({
            "name": "flags_transaction_router_unsupervised_task",
            "passed": passed,
            "detail": (f"Found {len(matches)} concurrency finding(s) for transaction_router.ex. "
                       "Expected: Task.async without Task.Supervisor must be flagged.")
        })
        if passed:
            total_score += 1.5
    except Exception as e:
        checks.append({"name": "flags_transaction_router_unsupervised_task",
                       "passed": False, "detail": str(e)})

    # ── CHECK 5: rate_cache.ex FLAGGED for ETS recommendation ─────────────────
    # read:write > 10:1 AND concurrent access -> should recommend ETS
    max_score += 2.0
    try:
        matches = has_finding("rate_cache", "genserver_bottleneck")
        passed = len(matches) > 0 and all_verified(matches)
        checks.append({
            "name": "flags_rate_cache_ets_recommendation",
            "passed": passed,
            "detail": (f"Found {len(matches)} genserver_bottleneck finding(s) for rate_cache.ex. "
                       "Expected: read:write ratio ~19:1 + concurrent access means ETS is appropriate.")
        })
        if passed:
            total_score += 2.0
    except Exception as e:
        checks.append({"name": "flags_rate_cache_ets_recommendation",
                       "passed": False, "detail": str(e)})

    # ── CHECK 6: report_generator.ex Enum on large dataset FLAGGED ────────────
    # 150k records >> 10k threshold -> must use Stream
    max_score += 1.5
    try:
        matches = has_finding("report_generator", "memory")
        passed = len(matches) > 0 and all_verified(matches)
        checks.append({
            "name": "flags_report_generator_enum_large_dataset",
            "passed": passed,
            "detail": (f"Found {len(matches)} memory finding(s) for report_generator.ex. "
                       "Expected: Enum.map on 150k records (> 10k threshold) should use Stream.")
        })
        if passed:
            total_score += 1.5
    except Exception as e:
        checks.append({"name": "flags_report_generator_enum_large_dataset",
                       "passed": False, "detail": str(e)})

    # ── CHECK 7: report_generator.ex unbounded spawn FLAGGED ─────────────────
    max_score += 1.5
    try:
        matches = has_finding("report_generator", "concurrency")
        passed = len(matches) > 0 and all_verified(matches)
        checks.append({
            "name": "flags_report_generator_unbounded_spawn",
            "passed": passed,
            "detail": (f"Found {len(matches)} concurrency finding(s) for report_generator.ex. "
                       "Expected: unbounded spawn() per settlement must be flagged.")
        })
        if passed:
            total_score += 1.5
    except Exception as e:
        checks.append({"name": "flags_report_generator_unbounded_spawn",
                       "passed": False, "detail": str(e)})

    # ── CHECK 8: config_loader.ex NOT flagged as bottleneck (valid pattern) ───
    # ~5 req/sec << 1000 threshold -> must NOT flag as genserver_bottleneck
    max_score += 2.0
    try:
        false_positive_matches = has_finding("config_loader", "genserver_bottleneck")
        passed = len(false_positive_matches) == 0
        checks.append({
            "name": "no_false_positive_config_loader",
            "passed": passed,
            "detail": (f"Found {len(false_positive_matches)} genserver_bottleneck finding(s) "
                       "for config_loader.ex. Expected: ZERO — ~5 req/sec is below 1000 req/sec "
                       "threshold (valid pattern, must NOT be flagged).")
        })
        if passed:
            total_score += 2.0
    except Exception as e:
        checks.append({"name": "no_false_positive_config_loader",
                       "passed": False, "detail": str(e)})

    # ── CHECK 9: small_batch_processor.ex NOT flagged for Enum usage ──────────
    # 200 items << 10k threshold -> must NOT flag Enum as issue
    max_score += 2.0
    try:
        false_positive_matches = has_finding("small_batch_processor", "memory")
        # Also check if any finding for small_batch_processor mentions stream
        stream_fp = [f for f in findings
                     if "small_batch_processor" in str(f.get("file", "")).lower()
                     and "stream" in str(f.get("description", "")).lower()]
        total_fp = false_positive_matches + [f for f in stream_fp if f not in false_positive_matches]
        passed = len(total_fp) == 0
        checks.append({
            "name": "no_false_positive_small_batch_enum",
            "passed": passed,
            "detail": (f"Found {len(total_fp)} false positive finding(s) for small_batch_processor.ex. "
                       "Expected: ZERO — 200 items is below 10k threshold (Enum valid for small collections).")
        })
        if passed:
            total_score += 2.0
    except Exception as e:
        checks.append({"name": "no_false_positive_small_batch_enum",
                       "passed": False, "detail": str(e)})

    # ── CHECK 10: all findings have required fields from review-verification-protocol ──
    max_score += 1.0
    required_fields = {"file", "line", "severity", "category", "description",
                       "recommendation", "verified"}
    try:
        if len(findings) == 0:
            checks.append({"name": "all_findings_have_required_fields",
                           "passed": False,
                           "detail": "No findings present to validate."})
        else:
            missing_fields_report = []
            valid_severities = {"critical", "high", "medium", "low"}
            valid_categories = {"genserver_bottleneck", "memory", "concurrency", "database"}
            for i, f in enumerate(findings):
                missing = required_fields - set(f.keys())
                if missing:
                    missing_fields_report.append(f"finding[{i}] missing: {missing}")
                if f.get("severity") not in valid_severities:
                    missing_fields_report.append(
                        f"finding[{i}] invalid severity: {f.get('severity')!r}")
                if f.get("category") not in valid_categories:
                    missing_fields_report.append(
                        f"finding[{i}] invalid category: {f.get('category')!r}")
                if not isinstance(f.get("line"), int):
                    missing_fields_report.append(
                        f"finding[{i}] line must be int, got {type(f.get('line')).__name__}")
            passed = len(missing_fields_report) == 0
            checks.append({
                "name": "all_findings_have_required_fields",
                "passed": passed,
                "detail": ("; ".join(missing_fields_report) if missing_fields_report
                           else f"All {len(findings)} findings have valid required fields.")
            })
            if passed:
                total_score += 1.0
    except Exception as e:
        checks.append({"name": "all_findings_have_required_fields",
                       "passed": False, "detail": str(e)})

    # Normalize score to 0-1
    normalized = round(total_score / max_score, 4) if max_score > 0 else 0.0
    return checks, normalized


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

    try:
        checks, score = run_checks(workspace)
    except Exception as e:
        checks = [{"name": "eval_error", "passed": False, "detail": str(e)}]
        score = 0.0

    passed = score >= 0.7  # Require 70% to pass

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()