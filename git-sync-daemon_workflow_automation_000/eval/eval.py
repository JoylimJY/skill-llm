#!/usr/bin/env python3
"""
Evaluation script for the git-sync-daemon task.

Checks:
1. init was run: STATE_DIR exists and repos.conf exists
2. pipeline-aligner registered correctly (branch=main, remote=origin, enabled=1)
3. variant-caller registered correctly (branch=develop, remote=origin, enabled=1)
4. qc-dashboard registered correctly (branch=main, remote=origin, enabled=1)
5. legacy-assembler registered with enabled=0 (paused, NOT removed)
6. ref-genome-tools NOT registered at all
7. run-once was executed (log file is non-empty and contains sync cycle markers)
8. legacy-assembler skipped in log (SKIP disabled message)
9. pipeline-aligner, variant-caller, qc-dashboard processed in log
"""

import sys
import os
import re
import json
from pathlib import Path

def load_repos_conf(state_dir):
    conf_path = Path(state_dir) / "repos.conf"
    if not conf_path.exists():
        return None, str(conf_path)
    entries = []
    with open(conf_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                entries.append(line)
    return entries, str(conf_path)

def parse_entry(line):
    """Parse pipe-delimited entry into dict."""
    parts = line.split("|")
    path = parts[0].strip()
    props = {}
    for kv in parts[1:]:
        kv = kv.strip()
        if "=" in kv:
            k, v = kv.split("=", 1)
            props[k.strip()] = v.strip()
    return path, props

def find_entry_for_repo(entries, repo_name):
    """Find entry whose path ends with repo_name."""
    for line in entries:
        path, props = parse_entry(line)
        if path.rstrip("/").endswith("/" + repo_name) or path.rstrip("/") == repo_name:
            return path, props, line
    return None, None, None

def is_enabled(props):
    val = props.get("enabled", "1").lower()
    return val not in ("0", "false")

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

    # Determine state dir (default)
    home = Path.home()
    state_dir = home / ".config" / "git-sync-daemon"
    repos_conf_path = state_dir / "repos.conf"
    log_path = state_dir / "git-sync-daemon.log"

    checks = []
    total_score = 0.0
    total_weight = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, total_weight
        checks.append({"name": name, "passed": passed, "detail": detail})
        total_weight += weight
        if passed:
            total_score += weight

    # ── Check 1: init was run (state dir and repos.conf exist)
    try:
        init_ok = state_dir.exists() and repos_conf_path.exists()
        add_check(
            "init_ran",
            init_ok,
            f"State dir: {state_dir} exists={state_dir.exists()}, repos.conf exists={repos_conf_path.exists()}",
            weight=1.0
        )
    except Exception as e:
        add_check("init_ran", False, f"Exception: {e}", weight=1.0)

    # ── Load repos.conf
    entries = []
    try:
        if repos_conf_path.exists():
            with open(repos_conf_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        entries.append(line)
    except Exception as e:
        add_check("repos_conf_readable", False, f"Could not read repos.conf: {e}", weight=1.0)
        entries = []

    # ── Check 2: pipeline-aligner registered with branch=main, enabled=1
    try:
        path, props, raw = find_entry_for_repo(entries, "pipeline-aligner")
        if path is None:
            add_check("pipeline_aligner_registered", False,
                      "pipeline-aligner not found in repos.conf", weight=2.0)
        else:
            branch_ok = props.get("branch", "main") == "main"
            remote_ok = props.get("remote", "origin") == "origin"
            enabled_ok = is_enabled(props)
            ok = branch_ok and remote_ok and enabled_ok
            add_check("pipeline_aligner_registered", ok,
                      f"Entry: {raw} | branch_ok={branch_ok} remote_ok={remote_ok} enabled_ok={enabled_ok}",
                      weight=2.0)
    except Exception as e:
        add_check("pipeline_aligner_registered", False, f"Exception: {e}", weight=2.0)

    # ── Check 3: variant-caller registered with branch=develop, enabled=1
    try:
        path, props, raw = find_entry_for_repo(entries, "variant-caller")
        if path is None:
            add_check("variant_caller_registered", False,
                      "variant-caller not found in repos.conf", weight=2.0)
        else:
            branch_ok = props.get("branch", "") == "develop"
            remote_ok = props.get("remote", "origin") == "origin"
            enabled_ok = is_enabled(props)
            ok = branch_ok and remote_ok and enabled_ok
            add_check("variant_caller_registered", ok,
                      f"Entry: {raw} | branch_ok={branch_ok} remote_ok={remote_ok} enabled_ok={enabled_ok}",
                      weight=2.0)
    except Exception as e:
        add_check("variant_caller_registered", False, f"Exception: {e}", weight=2.0)

    # ── Check 4: qc-dashboard registered with branch=main, enabled=1
    try:
        path, props, raw = find_entry_for_repo(entries, "qc-dashboard")
        if path is None:
            add_check("qc_dashboard_registered", False,
                      "qc-dashboard not found in repos.conf", weight=2.0)
        else:
            branch_ok = props.get("branch", "main") == "main"
            remote_ok = props.get("remote", "origin") == "origin"
            enabled_ok = is_enabled(props)
            ok = branch_ok and remote_ok and enabled_ok
            add_check("qc_dashboard_registered", ok,
                      f"Entry: {raw} | branch_ok={branch_ok} remote_ok={remote_ok} enabled_ok={enabled_ok}",
                      weight=2.0)
    except Exception as e:
        add_check("qc_dashboard_registered", False, f"Exception: {e}", weight=2.0)

    # ── Check 5: legacy-assembler registered BUT with enabled=0 (paused, not deleted)
    try:
        path, props, raw = find_entry_for_repo(entries, "legacy-assembler")
        if path is None:
            add_check("legacy_assembler_paused", False,
                      "legacy-assembler not found in repos.conf at all (should be present with enabled=0)",
                      weight=3.0)
        else:
            disabled = not is_enabled(props)
            add_check("legacy_assembler_paused", disabled,
                      f"Entry: {raw} | enabled value: {props.get('enabled', 'not set')} | is_disabled={disabled}",
                      weight=3.0)
    except Exception as e:
        add_check("legacy_assembler_paused", False, f"Exception: {e}", weight=3.0)

    # ── Check 6: ref-genome-tools NOT registered (decommissioned)
    try:
        path, props, raw = find_entry_for_repo(entries, "ref-genome-tools")
        not_present = (path is None)
        add_check("ref_genome_tools_absent", not_present,
                  f"ref-genome-tools should NOT be in repos.conf. Found={not not_present}, entry={raw}",
                  weight=2.0)
    except Exception as e:
        add_check("ref_genome_tools_absent", False, f"Exception: {e}", weight=2.0)

    # ── Check 7: run-once was executed (log file non-empty, has cycle markers)
    try:
        if not log_path.exists():
            add_check("run_once_executed", False,
                      f"Log file not found at {log_path}", weight=2.0)
        else:
            log_content = log_path.read_text()
            has_start = "Sync cycle start" in log_content
            has_end = "Sync cycle end" in log_content
            ok = has_start and has_end
            add_check("run_once_executed", ok,
                      f"Log exists={log_path.exists()} cycle_start={has_start} cycle_end={has_end}",
                      weight=2.0)
    except Exception as e:
        add_check("run_once_executed", False, f"Exception: {e}", weight=2.0)

    # ── Check 8: legacy-assembler was SKIPPED (disabled) in log
    try:
        if not log_path.exists():
            add_check("legacy_assembler_skipped_in_log", False,
                      "Log file not found, cannot verify skip.", weight=1.5)
        else:
            log_content = log_path.read_text()
            skipped = ("legacy-assembler" in log_content and
                       ("SKIP" in log_content or "disabled" in log_content.lower()))
            add_check("legacy_assembler_skipped_in_log", skipped,
                      f"Log mentions legacy-assembler with skip/disabled signal: {skipped}",
                      weight=1.5)
    except Exception as e:
        add_check("legacy_assembler_skipped_in_log", False, f"Exception: {e}", weight=1.5)

    # ── Check 9: active repos processed in log
    try:
        if not log_path.exists():
            add_check("active_repos_processed_in_log", False,
                      "Log file not found.", weight=1.5)
        else:
            log_content = log_path.read_text()
            aligner_ok = "pipeline-aligner" in log_content
            caller_ok = "variant-caller" in log_content
            qc_ok = "qc-dashboard" in log_content
            ok = aligner_ok and caller_ok and qc_ok
            add_check("active_repos_processed_in_log", ok,
                      f"pipeline-aligner={aligner_ok}, variant-caller={caller_ok}, qc-dashboard={qc_ok}",
                      weight=1.5)
    except Exception as e:
        add_check("active_repos_processed_in_log", False, f"Exception: {e}", weight=1.5)

    # ── Final scoring
    score = round(total_score / total_weight, 4) if total_weight > 0 else 0.0
    passed = score >= 0.85 and all(
        c["passed"] for c in checks
        if c["name"] in {
            "init_ran",
            "pipeline_aligner_registered",
            "variant_caller_registered",
            "qc_dashboard_registered",
            "legacy_assembler_paused",
            "ref_genome_tools_absent",
            "run_once_executed",
        }
    )

    result = {
        "passed": passed,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()