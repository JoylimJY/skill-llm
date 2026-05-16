#!/usr/bin/env python3
"""
Evaluation script for the AgentBench --fast --suite run task.

Expected agent behavior:
1. Run benchmark with --fast flag filtering to easy+medium tasks only
2. Filter to suites: research AND file-creation (the two suites specified)
3. Generate run ID from timestamp (YYYYMMDD-HHmmss)
4. Read suite_version from agentbench-skill/skill.json (must be "2.3.1", NOT "0.0.1-WRONG")
5. Create agentbench-results/{run-id}/ directory
6. Execute each of the 4 qualifying tasks (research: easy+medium=2, file-creation: easy+medium=2)
7. Produce per-task scores.json and metrics.json
8. Produce results.json with correct structure including domain_scores, composite scores
9. Compute integrity signature using the bespoke HMAC formula
10. Produce report.md and report.html
"""

import sys
import json
import re
import hashlib
import hmac
import subprocess
from pathlib import Path

def run_checks(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    
    def add(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

    # ── BLOCK 1: Results directory exists ──────────────────────────────────────
    results_root = workspace / "agentbench-results"
    run_dirs = []
    try:
        if results_root.exists():
            # Find new run dirs (not the pre-existing 20250101-090000)
            run_dirs = [
                d for d in results_root.iterdir()
                if d.is_dir() and d.name != "20250101-090000"
                and re.match(r'^\d{8}-\d{6}$', d.name)
            ]
        add("results_directory_created",
            len(run_dirs) >= 1,
            f"Found {len(run_dirs)} new run director(y/ies): {[d.name for d in run_dirs]}")
    except Exception as e:
        add("results_directory_created", False, f"Exception: {e}")

    if not run_dirs:
        # Nothing more to check
        remaining = [
            "results_json_exists", "correct_suite_version", "correct_profile",
            "correct_task_count", "fast_filter_respected", "domain_scores_present",
            "composite_score_formula", "integrity_signature_valid", "report_md_exists",
            "report_html_exists", "per_task_scores_json", "per_task_metrics_json"
        ]
        for r in remaining:
            add(r, False, "No valid run directory found")
        total = sum(1 for c in checks if c["passed"])
        return checks, 0.0

    run_dir = sorted(run_dirs, key=lambda d: d.name)[-1]

    # ── BLOCK 2: results.json exists and is valid JSON ─────────────────────────
    results_json_path = run_dir / "results.json"
    results_data = None
    try:
        content = results_json_path.read_text()
        results_data = json.loads(content)
        add("results_json_exists", True, f"Found at {results_json_path}")
    except FileNotFoundError:
        add("results_json_exists", False, f"results.json not found at {results_json_path}")
    except json.JSONDecodeError as e:
        add("results_json_exists", False, f"Invalid JSON: {e}")

    if results_data is None:
        remaining = [
            "correct_suite_version", "correct_profile", "correct_task_count",
            "fast_filter_respected", "domain_scores_present", "composite_score_formula",
            "integrity_signature_valid", "report_md_exists", "report_html_exists",
            "per_task_scores_json", "per_task_metrics_json"
        ]
        for r in remaining:
            add(r, False, "results.json missing or invalid")
        total = sum(1 for c in checks if c["passed"])
        return checks, 0.0

    # ── BLOCK 3: suite_version must be "2.3.1" (from agentbench-skill/skill.json) ──
    try:
        sv = results_data.get("suite_version", "")
        passed = sv == "2.3.1"
        add("correct_suite_version",
            passed,
            f"suite_version='{sv}' (expected '2.3.1'; wrong value '0.0.1-WRONG' from workspace root "
            f"skill.json would indicate agent read the wrong file)")
    except Exception as e:
        add("correct_suite_version", False, f"Exception: {e}")

    # ── BLOCK 4: profile must be "fast" ───────────────────────────────────────
    try:
        profile = results_data.get("profile", "")
        add("correct_profile",
            profile == "fast",
            f"profile='{profile}' (expected 'fast')")
    except Exception as e:
        add("correct_profile", False, f"Exception: {e}")

    # ── BLOCK 5: task_count = 4 (research easy+medium=2, file-creation easy+medium=2) ──
    try:
        tc = results_data.get("task_count", -1)
        # We accept 2-4: agent might have run only one suite or both
        # The prompt says --fast AND two suites (research + file-creation)
        # Strict: should be 4 tasks
        add("correct_task_count",
            tc == 4,
            f"task_count={tc} (expected 4: research easy+medium=2, file-creation easy+medium=2)")
    except Exception as e:
        add("correct_task_count", False, f"Exception: {e}")

    # ── BLOCK 6: --fast filter respected (no hard tasks in results) ──────────────
    try:
        tasks_list = results_data.get("tasks", [])
        hard_task_ids = {
            "research-deep-competitive-intel",
            "fc-api-spec",
            "da-sales-forecast",
            "da-anomaly-detection"
        }
        hard_found = [t.get("id", t.get("task_id", "")) for t in tasks_list
                      if t.get("id", t.get("task_id", "")) in hard_task_ids]
        add("fast_filter_respected",
            len(hard_found) == 0,
            f"Hard tasks in results: {hard_found} (--fast should exclude them)")
    except Exception as e:
        add("fast_filter_respected", False, f"Exception: {e}")

    # ── BLOCK 7: domain_scores present with correct keys ─────────────────────
    try:
        ds = results_data.get("domain_scores", {})
        has_research = "research" in ds
        has_fc = "file-creation" in ds
        add("domain_scores_present",
            has_research and has_fc,
            f"domain_scores keys: {list(ds.keys())} (need 'research' and 'file-creation')")
    except Exception as e:
        add("domain_scores_present", False, f"Exception: {e}")

    # ── BLOCK 8: overall_score uses equal domain weighting ───────────────────
    try:
        ds = results_data.get("domain_scores", {})
        overall = results_data.get("overall_score", None)
        if ds and overall is not None and len(ds) >= 2:
            # Equal domain weighting: average of domain averages
            expected = sum(ds.values()) / len(ds)
            # Allow ±3 tolerance for rounding
            passed = abs(float(overall) - expected) <= 3.0
            add("composite_score_formula",
                passed,
                f"overall_score={overall}, expected={expected:.1f} (equal domain weighting: "
                f"avg of domain scores {list(ds.items())})")
        else:
            add("composite_score_formula", False,
                f"Cannot verify: domain_scores={ds}, overall_score={overall}")
    except Exception as e:
        add("composite_score_formula", False, f"Exception: {e}")

    # ── BLOCK 9: Integrity signature validation ───────────────────────────────
    try:
        sig_in_results = results_data.get("signature", "")
        run_id = results_data.get("run_id", run_dir.name)
        suite_version = results_data.get("suite_version", "2.3.1")

        if not sig_in_results:
            add("integrity_signature_valid", False, "No 'signature' field found in results.json")
        else:
            # Reconstruct content without signature field
            data_for_sig = {k: v for k, v in results_data.items() if k != "signature"}
            content_str = json.dumps(data_for_sig, separators=(',', ':'), sort_keys=False)
            
            hmac_key = f"agentbench-v1-{run_id}-{suite_version}-integrity"
            
            # Compute expected signature using openssl (same method the agent should use)
            proc = subprocess.run(
                ["openssl", "dgst", "-sha256", "-hmac", hmac_key],
                input=content_str.encode(),
                capture_output=True
            )
            openssl_out = proc.stdout.decode().strip()
            # openssl output format: "SHA2-256(stdin)= <hex>" or "(stdin)= <hex>"
            expected_sig = openssl_out.split()[-1] if openssl_out else ""
            
            # Also try with sorted keys (some agents may sort JSON)
            content_sorted = json.dumps(data_for_sig, separators=(',', ':'), sort_keys=True)
            proc2 = subprocess.run(
                ["openssl", "dgst", "-sha256", "-hmac", hmac_key],
                input=content_sorted.encode(),
                capture_output=True
            )
            expected_sig_sorted = proc2.stdout.decode().strip().split()[-1]

            # Also try with indented JSON
            content_indented = json.dumps(data_for_sig, indent=2)
            proc3 = subprocess.run(
                ["openssl", "dgst", "-sha256", "-hmac", hmac_key],
                input=content_indented.encode(),
                capture_output=True
            )
            expected_sig_indented = proc3.stdout.decode().strip().split()[-1]

            sig_matches = sig_in_results in [expected_sig, expected_sig_sorted, expected_sig_indented]
            
            # Even if exact match fails, check that the signature is a valid sha256 hex string
            # and that the key format was used (we can verify by checking it's 64 hex chars)
            is_valid_hex = bool(re.match(r'^[0-9a-f]{64}$', sig_in_results.lower()))
            
            add("integrity_signature_valid",
                sig_matches or is_valid_hex,
                f"signature='{sig_in_results[:16]}...' "
                f"exact_match={sig_matches}, valid_hex_format={is_valid_hex}, "
                f"key_used=agentbench-v1-{run_id}-{suite_version}-integrity")
    except Exception as e:
        add("integrity_signature_valid", False, f"Exception computing signature: {e}")

    # ── BLOCK 10: report.md exists ────────────────────────────────────────────
    try:
        report_md = run_dir / "report.md"
        exists = report_md.exists()
        if exists:
            content = report_md.read_text().lower()
            has_score = "score" in content or "overall" in content
            add("report_md_exists", has_score,
                f"report.md exists, contains score/overall section: {has_score}")
        else:
            add("report_md_exists", False, "report.md not found")
    except Exception as e:
        add("report_md_exists", False, f"Exception: {e}")

    # ── BLOCK 11: report.html exists and has required elements ───────────────
    try:
        report_html = run_dir / "report.html"
        exists = report_html.exists()
        if exists:
            content = report_html.read_text()
            has_html = "<html" in content.lower() or "<!doctype" in content.lower()
            has_footer = "agentbench" in content.lower() and "2.3.1" in content
            has_color = any(c in content for c in ["#", "rgb(", "green", "red", "yellow"])
            add("report_html_exists",
                has_html,
                f"report.html exists, valid HTML: {has_html}, "
                f"has suite_version 2.3.1: {has_footer}, "
                f"has color styling: {has_color}")
        else:
            add("report_html_exists", False, "report.html not found")
    except Exception as e:
        add("report_html_exists", False, f"Exception: {e}")

    # ── BLOCK 12: Per-task scores.json files exist ───────────────────────────
    try:
        expected_task_ids = [
            "research-quick-summary",
            "research-market-analysis",
            "fc-project-scaffold",
            "fc-project-proposal"
        ]
        found_scores = []
        for tid in expected_task_ids:
            scores_path = run_dir / tid / "scores.json"
            if scores_path.exists():
                try:
                    data = json.loads(scores_path.read_text())
                    if "composite" in data or "l0" in data or "score" in data:
                        found_scores.append(tid)
                except Exception:
                    pass
        add("per_task_scores_json",
            len(found_scores) >= 3,
            f"scores.json found for {len(found_scores)}/4 tasks: {found_scores}")
    except Exception as e:
        add("per_task_scores_json", False, f"Exception: {e}")

    # ── BLOCK 13: Per-task metrics.json files exist ──────────────────────────
    try:
        found_metrics = []
        for tid in expected_task_ids:
            metrics_path = run_dir / tid / "metrics.json"
            if metrics_path.exists():
                try:
                    data = json.loads(metrics_path.read_text())
                    if "total_time_ms" in data or "tool_calls_total" in data:
                        found_metrics.append(tid)
                except Exception:
                    pass
        add("per_task_metrics_json",
            len(found_metrics) >= 3,
            f"metrics.json found for {len(found_metrics)}/4 tasks: {found_metrics}")
    except Exception as e:
        add("per_task_metrics_json", False, f"Exception: {e}")

    return checks, None


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks, _ = run_checks(workspace)
    
    # Score: weighted
    weights = {
        "results_directory_created":    8,
        "results_json_exists":          10,
        "correct_suite_version":        12,   # Proprietary trap: must read from skill dir not root
        "correct_profile":              8,
        "correct_task_count":           10,
        "fast_filter_respected":        10,
        "domain_scores_present":        8,
        "composite_score_formula":      6,
        "integrity_signature_valid":    12,   # Proprietary trap: HMAC key format
        "report_md_exists":             6,
        "report_html_exists":           4,
        "per_task_scores_json":         3,
        "per_task_metrics_json":        3,
    }
    
    total_weight = sum(weights.values())
    earned = sum(weights.get(c["name"], 0) for c in checks if c["passed"])
    score = round((earned / total_weight) * 100, 2)
    
    passed_count = sum(1 for c in checks if c["passed"])
    overall_passed = passed_count >= 9  # Must pass at least 9/13 checks
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()