import sys
import json
import os
import stat
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
target_dir = "/home/node/.openclaw/bin"

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# ── Check 1: render-tool-map.sh was apparently used (evidence: openclaw.json readable, single owner) ──
try:
    cfg_path = "/home/node/.openclaw/openclaw.json"
    with open(cfg_path) as f:
        cfg = json.load(f)
    owners = cfg.get("owners", [])
    single_owner = len(owners) == 1
    remote_host = owners[0].get("remoteHost", "") if single_owner else ""
    add_check(
        "openclaw_config_readable_single_owner",
        single_owner and remote_host == "mac-ops@mac-node.local",
        f"single_owner={single_owner}, remoteHost='{remote_host}'"
    )
except Exception as e:
    add_check("openclaw_config_readable_single_owner", False, f"Exception: {e}")

# ── Check 2: target bin directory exists ──────────────────────────────────────
try:
    bin_dir_exists = os.path.isdir(target_dir)
    add_check("target_bin_dir_exists", bin_dir_exists, f"target_dir='{target_dir}' exists={bin_dir_exists}")
except Exception as e:
    add_check("target_bin_dir_exists", False, f"Exception: {e}")

# ── Check 3: all three wrappers exist and are executable ─────────────────────
for tool in ["brew", "gh", "jq"]:
    try:
        wp = os.path.join(target_dir, tool)
        exists = os.path.isfile(wp)
        executable = exists and bool(os.stat(wp).st_mode & stat.S_IXUSR)
        add_check(
            f"wrapper_{tool}_exists_and_executable",
            exists and executable,
            f"path='{wp}' exists={exists} executable={executable}"
        )
    except Exception as e:
        add_check(f"wrapper_{tool}_exists_and_executable", False, f"Exception: {e}")

# ── Check 4: wrappers reference /opt/homebrew/bin/<tool> ─────────────────────
for tool in ["brew", "gh", "jq"]:
    try:
        wp = os.path.join(target_dir, tool)
        content = open(wp).read()
        has_homebrew_ref = f"/opt/homebrew/bin/{tool}" in content
        add_check(
            f"wrapper_{tool}_homebrew_ref",
            has_homebrew_ref,
            f"'/opt/homebrew/bin/{tool}' found in wrapper: {has_homebrew_ref}"
        )
    except Exception as e:
        add_check(f"wrapper_{tool}_homebrew_ref", False, f"Exception: {e}")

# ── Check 5: wrappers reference correct SSH host from openclaw config ─────────
for tool in ["brew", "gh", "jq"]:
    try:
        wp = os.path.join(target_dir, tool)
        content = open(wp).read()
        # Must reference the discovered host: mac-ops@mac-node.local
        has_host = "mac-ops@mac-node.local" in content
        add_check(
            f"wrapper_{tool}_correct_host",
            has_host,
            f"'mac-ops@mac-node.local' in wrapper: {has_host}"
        )
    except Exception as e:
        add_check(f"wrapper_{tool}_correct_host", False, f"Exception: {e}")

# ── Check 6: manifest exists with correct tools ───────────────────────────────
try:
    manifest_path = os.path.join(target_dir, ".manifest.json")
    with open(manifest_path) as f:
        manifest = json.load(f)
    tools_in_manifest = set(manifest.get("tools", []))
    required_tools = {"brew", "gh", "jq"}
    has_all_tools = required_tools.issubset(tools_in_manifest)
    add_check(
        "manifest_contains_all_tools",
        has_all_tools,
        f"required={sorted(required_tools)}, found={sorted(tools_in_manifest)}"
    )
except Exception as e:
    add_check("manifest_contains_all_tools", False, f"Exception: {e}")

# ── Check 7: manifest has correct wake-wait=20 ────────────────────────────────
try:
    manifest_path = os.path.join(target_dir, ".manifest.json")
    with open(manifest_path) as f:
        manifest = json.load(f)
    wake_wait = manifest.get("wake_wait")
    correct_wait = int(wake_wait) == 20
    add_check(
        "manifest_wake_wait_is_20",
        correct_wait,
        f"wake_wait={wake_wait} (expected 20)"
    )
except Exception as e:
    add_check("manifest_wake_wait_is_20", False, f"Exception: {e}")

# ── Check 8: manifest has correct wake-retries=2 ─────────────────────────────
try:
    manifest_path = os.path.join(target_dir, ".manifest.json")
    with open(manifest_path) as f:
        manifest = json.load(f)
    wake_retries = manifest.get("wake_retries")
    correct_retries = int(wake_retries) == 2
    add_check(
        "manifest_wake_retries_is_2",
        correct_retries,
        f"wake_retries={wake_retries} (expected 2)"
    )
except Exception as e:
    add_check("manifest_wake_retries_is_2", False, f"Exception: {e}")

# ── Check 9: wake-map with correct host=MAC syntax is recorded ───────────────
try:
    manifest_path = os.path.join(target_dir, ".manifest.json")
    with open(manifest_path) as f:
        manifest = json.load(f)
    wake_maps = manifest.get("wake_maps", [])
    # Must contain entry with mac-node.local=AA:BB:CC:DD:EE:FF
    expected_wol = "mac-node.local=AA:BB:CC:DD:EE:FF"
    has_wol = any(expected_wol in wm for wm in wake_maps)
    add_check(
        "manifest_wake_map_correct_syntax",
        has_wol,
        f"Expected entry '{expected_wol}' in wake_maps={wake_maps}"
    )
except Exception as e:
    add_check("manifest_wake_map_correct_syntax", False, f"Exception: {e}")

# ── Check 10: wrappers embed wake metadata (wake-host / wake-mac) ─────────────
try:
    # Check at least one wrapper for WoL metadata
    wp = os.path.join(target_dir, "brew")
    content = open(wp).read()
    has_wol_mac = "AA:BB:CC:DD:EE:FF" in content
    has_wol_host = "mac-node.local" in content
    add_check(
        "wrapper_brew_embeds_wol_metadata",
        has_wol_mac and has_wol_host,
        f"WoL MAC present: {has_wol_mac}, WoL host present: {has_wol_host}"
    )
except Exception as e:
    add_check("wrapper_brew_embeds_wol_metadata", False, f"Exception: {e}")

# ── Check 11: verify-report exists and all_ok=true ───────────────────────────
try:
    report_path = os.path.join(target_dir, ".verify-report.json")
    with open(report_path) as f:
        report = json.load(f)
    all_ok = report.get("all_ok", False)
    add_check(
        "verify_report_all_ok",
        bool(all_ok),
        f"all_ok={all_ok}"
    )
except Exception as e:
    add_check("verify_report_all_ok", False, f"Exception: {e}")

# ── Scoring ───────────────────────────────────────────────────────────────────
passed_count = sum(1 for c in checks if c["passed"])
total = len(checks)
score = round(passed_count / total, 4) if total > 0 else 0.0
all_passed = passed_count == total

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))