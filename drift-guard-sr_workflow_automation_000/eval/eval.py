#!/usr/bin/env python3
"""Evaluation script for the Drift Guard task."""
import sys
import json
import os
from pathlib import Path

def main(workspace):
    workspace = Path(workspace)
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, max_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        max_score += weight
        if passed:
            total_score += weight

    # ─── CHECK 1: config.py exists ──────────────────────────────────────────
    config_path = workspace / "config.py"
    try:
        exists = config_path.exists()
        add_check(
            "config.py exists",
            exists,
            f"config.py {'found' if exists else 'NOT found'} at {config_path}",
            weight=1.0
        )
    except Exception as e:
        add_check("config.py exists", False, f"Exception: {e}", weight=1.0)

    # ─── CHECK 2: config.py has valid CONFIG dict with required keys ─────────
    try:
        content = (workspace / "config.py").read_text(encoding="utf-8")
        has_thresholds = "thresholds" in content
        has_weights = "weights" in content
        has_baseline_file = "baseline_file" in content
        valid = has_thresholds and has_weights and has_baseline_file
        add_check(
            "config.py has required keys (thresholds, weights, baseline_file)",
            valid,
            f"thresholds={has_thresholds}, weights={has_weights}, baseline_file={has_baseline_file}",
            weight=1.0
        )
    except Exception as e:
        add_check("config.py has required keys", False, f"Exception: {e}", weight=1.0)

    # ─── CHECK 3: baseline.json exists ──────────────────────────────────────
    # Search both workspace root and subdirectories
    baseline_candidates = list(workspace.rglob("baseline.json"))
    baseline_path = baseline_candidates[0] if baseline_candidates else None
    try:
        found = baseline_path is not None and baseline_path.exists()
        add_check(
            "baseline.json created",
            found,
            f"baseline.json {'found at ' + str(baseline_path) if found else 'NOT found anywhere in workspace'}",
            weight=2.0
        )
    except Exception as e:
        add_check("baseline.json created", False, f"Exception: {e}", weight=2.0)

    # ─── CHECK 4: baseline.json has valid structure ──────────────────────────
    try:
        data = json.loads(baseline_path.read_text()) if baseline_path else {}
        has_metrics = "metrics" in data
        has_sample_count = "sample_count" in data
        sample_count = data.get("sample_count", 0)
        # Must have been captured from multiple files (>=5 healthy responses)
        sufficient_samples = sample_count >= 5
        metrics = data.get("metrics", {})
        required_metric_keys = {
            "char_count", "word_count", "sentence_count",
            "vocabulary_diversity", "sycophancy_score",
            "hedging_score", "technical_score"
        }
        has_required_metrics = required_metric_keys.issubset(set(metrics.keys()))
        valid_structure = has_metrics and has_sample_count and sufficient_samples and has_required_metrics
        add_check(
            "baseline.json has valid structure with >=5 samples and required metric keys",
            valid_structure,
            f"has_metrics={has_metrics}, sample_count={sample_count}(>=5:{sufficient_samples}), "
            f"has_required_metrics={has_required_metrics} "
            f"(missing: {required_metric_keys - set(metrics.keys())})",
            weight=2.0
        )
    except Exception as e:
        add_check("baseline.json has valid structure", False, f"Exception: {e}", weight=2.0)

    # ─── CHECK 5: baseline metrics reflect healthy (low sycophancy) responses ─
    try:
        data = json.loads(baseline_path.read_text()) if baseline_path else {}
        metrics = data.get("metrics", {})
        syc = metrics.get("sycophancy_score", 999)
        hedge = metrics.get("hedging_score", 999)
        # Healthy responses should have low sycophancy (<0.05) and low hedging (<0.05)
        healthy_baseline = syc < 0.05 and hedge < 0.05
        add_check(
            "baseline metrics reflect healthy (non-sycophantic) responses",
            healthy_baseline,
            f"sycophancy_score={syc:.4f} (expect <0.05), hedging_score={hedge:.4f} (expect <0.05)",
            weight=2.0
        )
    except Exception as e:
        add_check("baseline metrics reflect healthy responses", False, f"Exception: {e}", weight=2.0)

    # ─── CHECK 6: drift_history.json exists (monitoring was run) ─────────────
    history_candidates = list(workspace.rglob("drift_history.json"))
    history_path = history_candidates[0] if history_candidates else None
    try:
        found = history_path is not None and history_path.exists()
        add_check(
            "drift_history.json created (monitoring ran)",
            found,
            f"drift_history.json {'found at ' + str(history_path) if found else 'NOT found'}",
            weight=2.0
        )
    except Exception as e:
        add_check("drift_history.json created", False, f"Exception: {e}", weight=2.0)

    # ─── CHECK 7: drift history has multiple measurements ────────────────────
    try:
        history = json.loads(history_path.read_text()) if history_path else []
        count = len(history)
        # At least 2 suspect responses monitored (ideally all 3)
        sufficient = count >= 2
        add_check(
            "drift_history.json has >=2 measurements",
            sufficient,
            f"Found {count} measurement(s) in history (need >=2)",
            weight=1.5
        )
    except Exception as e:
        add_check("drift_history.json has >=2 measurements", False, f"Exception: {e}", weight=1.5)

    # ─── CHECK 8: at least one measurement has critical or emergency drift ────
    try:
        history = json.loads(history_path.read_text()) if history_path else []
        high_drift = [
            h for h in history
            if h.get("alert_level") in ("critical", "emergency")
            or h.get("drift_score", 0) >= 0.6
        ]
        has_high = len(high_drift) > 0
        add_check(
            "at least one measurement shows critical/emergency drift (score>=0.6)",
            has_high,
            f"{len(high_drift)}/{len(history)} measurements with critical+ drift. "
            f"Scores: {[round(h.get('drift_score',0),3) for h in history]}",
            weight=2.0
        )
    except Exception as e:
        add_check("at least one critical/emergency drift measurement", False, f"Exception: {e}", weight=2.0)

    # ─── CHECK 9: trend_report.json exists ───────────────────────────────────
    report_candidates = list(workspace.rglob("trend_report.json"))
    report_path = report_candidates[0] if report_candidates else None
    try:
        found = report_path is not None and report_path.exists()
        add_check(
            "trend_report.json created",
            found,
            f"trend_report.json {'found at ' + str(report_path) if found else 'NOT found'}",
            weight=2.0
        )
    except Exception as e:
        add_check("trend_report.json created", False, f"Exception: {e}", weight=2.0)

    # ─── CHECK 10: trend_report.json has valid drift report structure ─────────
    try:
        report_data = json.loads(report_path.read_text()) if report_path else {}
        required_keys = {
            "measurement_count", "mean_drift_score", "max_drift_score",
            "min_drift_score", "trend", "alert_counts"
        }
        has_keys = required_keys.issubset(set(report_data.keys()))
        measurement_count = report_data.get("measurement_count", 0)
        mean_drift = report_data.get("mean_drift_score", 0)
        max_drift = report_data.get("max_drift_score", 0)
        # The report should reflect the monitored drifted responses
        # mean drift should be elevated (>0.3) given we fed sycophantic responses
        elevated_drift = mean_drift >= 0.3
        valid = has_keys and measurement_count >= 2 and elevated_drift
        add_check(
            "trend_report.json has valid structure with elevated mean drift (>=0.3)",
            valid,
            f"has_required_keys={has_keys}, measurement_count={measurement_count}, "
            f"mean_drift={mean_drift:.4f}(>=0.3:{elevated_drift}), max_drift={max_drift:.4f}",
            weight=2.0
        )
    except Exception as e:
        add_check("trend_report.json valid structure", False, f"Exception: {e}", weight=2.0)

    # ─── CHECK 11: trend_report.json was produced via --format json (machine-readable) ──
    # Verify it is valid JSON with nested objects (not plain text)
    try:
        report_data = json.loads(report_path.read_text()) if report_path else {}
        # Must have metric_averages (only present in json format output)
        has_metric_avgs = "metric_averages" in report_data
        has_measurements = "measurements" in report_data
        json_format_used = has_metric_avgs and has_measurements
        add_check(
            "trend_report.json contains metric_averages and measurements (--format json used)",
            json_format_used,
            f"has_metric_averages={has_metric_avgs}, has_measurements={has_measurements}",
            weight=1.5
        )
    except Exception as e:
        add_check("trend_report.json --format json structure", False, f"Exception: {e}", weight=1.5)

    # ─── CHECK 12: suspect responses were NOT included in the baseline ────────
    # The baseline should have low sycophancy; if suspect responses were included,
    # sycophancy_score would be much higher
    try:
        data = json.loads(baseline_path.read_text()) if baseline_path else {}
        metrics = data.get("metrics", {})
        syc = metrics.get("sycophancy_score", 999)
        # If suspect responses were mixed in, sycophancy would be much higher
        not_contaminated = syc < 0.08
        add_check(
            "baseline NOT contaminated with suspect/drifted responses",
            not_contaminated,
            f"baseline sycophancy_score={syc:.4f} (should be <0.08; higher suggests contamination)",
            weight=2.0
        )
    except Exception as e:
        add_check("baseline not contaminated", False, f"Exception: {e}", weight=2.0)

    # ─── Compute final score ─────────────────────────────────────────────────
    final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    passed = final_score >= 0.75

    result = {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)
    main(sys.argv[1])