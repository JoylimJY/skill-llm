#!/usr/bin/env python3
"""Evaluation script for the GitHub DNS Helper task."""
import sys
import json
import re
from pathlib import Path

def main(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # ── Load expected data ────────────────────────────────────────────────────
    try:
        expected = json.loads((workspace / ".eval_expected.json").read_text())
        expected_entries = expected["github_entries_from_mock"]
        marker_start = expected["marker_start"]
        marker_end = expected["marker_end"]
    except Exception as e:
        print(json.dumps({
            "passed": False, "score": 0.0,
            "checks": [{"name": "eval_setup", "passed": False,
                        "detail": f"Could not load expected data: {e}"}]
        }))
        return

    # ── Read current /etc/hosts ───────────────────────────────────────────────
    try:
        hosts_content = Path("/etc/hosts").read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "hosts_readable", "passed": False,
                       "detail": f"Cannot read /etc/hosts: {e}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ── CHECK 1: Markers present ──────────────────────────────────────────────
    has_start = marker_start in hosts_content
    has_end = marker_end in hosts_content
    checks.append({
        "name": "hosts_has_markers",
        "passed": has_start and has_end,
        "detail": (
            f"START marker present: {has_start}, END marker present: {has_end}. "
            "The script should wrap GitHub entries between '# GitHub DNS Fix - START' and '# GitHub DNS Fix - END'."
        )
    })

    # ── CHECK 2: Stale old entries replaced (not just appended) ──────────────
    # The old entry was: 140.82.112.3  github.com (from 2023)
    # New should be: 140.82.114.4  github.com
    old_stale_ip = "140.82.112.3"
    # Count occurrences within the new block
    block_match = re.search(
        rf"{re.escape(marker_start)}(.*?){re.escape(marker_end)}",
        hosts_content, re.DOTALL
    )
    block_content = block_match.group(1) if block_match else ""

    stale_not_in_block = old_stale_ip not in block_content
    # Also make sure there's only ONE GitHub DNS Fix block (no duplicates)
    start_count = hosts_content.count(marker_start)
    single_block = start_count == 1
    checks.append({
        "name": "stale_entries_replaced",
        "passed": stale_not_in_block and single_block,
        "detail": (
            f"Old stale IP ({old_stale_ip}) in new block: {not stale_not_in_block}. "
            f"Number of GitHub DNS Fix blocks: {start_count} (expected 1). "
            "The script must replace—not append—the old GitHub block."
        )
    })

    # ── CHECK 3: New entries from mock server are present ────────────────────
    # Check key entries that should come from the mock server
    critical_entries = [
        ("140.82.114.4", "github.com"),         # new IP for github.com
        ("140.82.114.5", "api.github.com"),      # new entry
        ("185.199.108.133", "raw.githubusercontent.com"),
        ("52.217.128.40", "codeload.github.com"),
    ]
    entry_results = []
    for ip, hostname in critical_entries:
        # Search within the block
        pattern = rf"{re.escape(ip)}\s+{re.escape(hostname)}"
        found = bool(re.search(pattern, block_content))
        entry_results.append((f"{ip} {hostname}", found))

    all_entries_found = all(r[1] for r in entry_results)
    entry_detail = "; ".join(f"{e}: {'FOUND' if f else 'MISSING'}" for e, f in entry_results)
    checks.append({
        "name": "mock_server_entries_present",
        "passed": all_entries_found,
        "detail": f"Critical entries from mock server: {entry_detail}"
    })

    # ── CHECK 4: Non-GitHub entries NOT inserted into block ──────────────────
    # The mock server data includes "192.0.2.1 some.random.domain.com" and
    # "203.0.113.5 another.non-github.example.net" — these must NOT appear in hosts
    non_github_noise = ["some.random.domain.com", "another.non-github.example.net"]
    noise_found = [n for n in non_github_noise if n in block_content]
    checks.append({
        "name": "non_github_entries_excluded",
        "passed": len(noise_found) == 0,
        "detail": (
            f"Non-GitHub entries incorrectly inserted: {noise_found}. "
            "The script should only write GitHub-related entries, not all hosts."
        )
    })

    # ── CHECK 5: Custom URL was used (mock server entries verify this) ────────
    # Presence of 140.82.114.5 (api.github.com with new IP) proves the -u flag was used
    # since the default URL (hellogithub) would return different/no data in this container
    custom_url_evidence = "140.82.114.5" in hosts_content  # Only in mock server data
    checks.append({
        "name": "custom_url_flag_used",
        "passed": custom_url_evidence,
        "detail": (
            f"IP 140.82.114.5 (api.github.com, only served by mock server) in hosts: {custom_url_evidence}. "
            "Agent must have used the -u/--url flag pointing to http://localhost:18080/hosts."
        )
    })

    # ── CHECK 6: localhost/system entries preserved ───────────────────────────
    localhost_ok = "127.0.0.1" in hosts_content and "localhost" in hosts_content
    checks.append({
        "name": "system_entries_preserved",
        "passed": localhost_ok,
        "detail": (
            f"127.0.0.1 localhost entry preserved: {localhost_ok}. "
            "The fix script must not destroy pre-existing system hosts entries."
        )
    })

    # ── Compute score ─────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 4)
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "invocation", "passed": False,
                                      "detail": "No workspace path provided"}]}))
        sys.exit(1)
    main(sys.argv[1])