#!/usr/bin/env python3
"""
Evaluation script for the discogs-cli task.
Checks:
1. Binary was compiled (install.sh was run).
2. Config was set with correct flags (-u, -t) and includes mock base URL.
3. Both Aphex Twin and Boards of Canada releases were added to wantlist
   (verified via mock server state persisted in log, or via wantlist list output).
4. collection sync was run (cache file exists and is valid).
5. collection value was run and output saved to collection_value_report.txt
   with correct total.
"""
import sys
import json
import os
import re
import subprocess
from pathlib import Path

workspace = sys.argv[1] if len(args := sys.argv) > 1 else "/workspace"

checks = []

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}: {detail}")

# ── Check 1: Binary compiled ──────────────────────────────────────────────────
try:
    bin_path = Path(workspace) / "skills/discogs-cli/bin/discogs-cli"
    exists = bin_path.exists() and os.access(bin_path, os.X_OK)
    check("binary_compiled", exists,
          f"Binary found at {bin_path}" if exists else f"Binary missing at {bin_path}")
except Exception as e:
    check("binary_compiled", False, f"Exception: {e}")

# ── Check 2: Config file has username and token ───────────────────────────────
try:
    import yaml
    config_path = Path.home() / ".config/discogs-cli/config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        has_user = bool(cfg.get("username"))
        has_token = bool(cfg.get("token"))
        has_base = bool(cfg.get("base_url"))
        detail = f"username={cfg.get('username')}, token_set={has_token}, base_url={cfg.get('base_url')}"
        check("config_credentials_set", has_user and has_token,
              detail if has_user and has_token else f"Missing fields. {detail}")
        # Check base_url points to local mock (critical for all subsequent commands to work)
        base_ok = "127.0.0.1" in (cfg.get("base_url") or "") or "localhost" in (cfg.get("base_url") or "")
        check("config_base_url_local", base_ok,
              f"base_url={cfg.get('base_url')}" + (" (points to local mock)" if base_ok else " (does NOT point to local mock)"))
    else:
        check("config_credentials_set", False, f"Config file not found at {config_path}")
        check("config_base_url_local", False, "Config file missing")
except Exception as e:
    check("config_credentials_set", False, f"Exception reading config: {e}")
    check("config_base_url_local", False, f"Exception: {e}")

# ── Check 3: Cache file populated (sync was run) ───────────────────────────────
try:
    cache_path = Path.home() / ".cache/discogs-cli/collection.json"
    if cache_path.exists():
        with open(cache_path) as f:
            cache = json.load(f)
        has_entries = isinstance(cache, list) and len(cache) >= 4
        total_value = sum(e.get("value", 0) for e in cache)
        check("cache_populated", has_entries,
              f"Cache has {len(cache)} entries, total value=${total_value:.2f}" if isinstance(cache, list)
              else "Cache is not a list")
        check("cache_values_present", total_value > 0,
              f"Sum of values in cache: ${total_value:.2f}")
    else:
        check("cache_populated", False, f"Cache file not found at {cache_path}")
        check("cache_values_present", False, "Cache file missing")
except Exception as e:
    check("cache_populated", False, f"Exception: {e}")
    check("cache_values_present", False, f"Exception: {e}")

# ── Check 4: collection_value_report.txt exists and has correct total ─────────
try:
    # Search for the report file anywhere in workspace
    report_files = list(Path(workspace).rglob("collection_value_report.txt"))
    if not report_files:
        check("report_file_exists", False, "collection_value_report.txt not found in workspace")
        check("report_total_correct", False, "File missing")
    else:
        report_path = report_files[0]
        with open(report_path) as f:
            content = f.read()
        check("report_file_exists", True, f"Found at {report_path}")
        # Expected total: 42.50 + 38.00 + 55.75 + 61.20 = 197.45
        expected_total = 197.45
        # Look for a dollar amount matching the expected total
        matches = re.findall(r"\$?([\d,]+\.\d{2})", content)
        found_total = False
        for m in matches:
            val = float(m.replace(",", ""))
            if abs(val - expected_total) < 0.02:
                found_total = True
                break
        check("report_total_correct", found_total,
              f"Expected total ${expected_total:.2f} {'found' if found_total else 'NOT found'} in report. Amounts found: {matches[:10]}")
except Exception as e:
    check("report_file_exists", False, f"Exception: {e}")
    check("report_total_correct", False, f"Exception: {e}")

# ── Check 5: Wantlist additions (verify via mock server log or wantlist list) ──
try:
    # Try to call the mock server's wantlist endpoint directly
    import urllib.request
    import urllib.error

    # Read config for username
    config_path = Path.home() / ".config/discogs-cli/config.yaml"
    username = "vinyl_tester"
    try:
        import yaml
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        username = cfg.get("username", username)
    except Exception:
        pass

    # Check wantlist via mock server
    url = f"http://127.0.0.1:8765/users/{username}/wants"
    with urllib.request.urlopen(url, timeout=5) as resp:
        data = json.loads(resp.read())

    wants = data.get("wants", [])
    want_ids = {int(w["id"]) for w in wants}

    # Expected: Aphex Twin SAW85-92 = 3575126, BoC MHTRTC = 7526507
    aphex_id = 3575126
    boc_id = 7526507

    aphex_added = aphex_id in want_ids
    boc_added = boc_id in want_ids

    check("wantlist_aphex_twin_added", aphex_added,
          f"Release {aphex_id} (Aphex Twin - Selected Ambient Works 85-92) {'in' if aphex_added else 'NOT in'} wantlist. Current IDs: {want_ids}")
    check("wantlist_boc_added", boc_added,
          f"Release {boc_id} (Boards of Canada - Music Has the Right to Children) {'in' if boc_added else 'NOT in'} wantlist. Current IDs: {want_ids}")

except Exception as e:
    check("wantlist_aphex_twin_added", False, f"Could not verify wantlist: {e}")
    check("wantlist_boc_added", False, f"Could not verify wantlist: {e}")

# ── Scoring ───────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4) if total > 0 else 0.0
overall = passed_count == total

result = {
    "passed": overall,
    "score": score,
    "checks": checks,
}
print(json.dumps(result, indent=2))