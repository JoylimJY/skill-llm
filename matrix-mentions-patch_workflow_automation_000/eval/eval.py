#!/usr/bin/env python3
"""
Evaluation script for the Matrix Mentions Patch task.
Usage: python3 eval.py <workspace_dir>
(workspace_dir is unused here since all paths are absolute/HOME-based,
 but accepted for interface compliance)
"""

import sys
import os
import json
import glob

HOME = "/root"

DIST_DIR = f"{HOME}/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/dist"
FORMATTING_TS = (
    f"{HOME}/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw"
    f"/extensions/matrix/src/matrix/send/formatting.ts"
)
CLI_LOG = f"{HOME}/.openclaw/logs/openclaw-cli-calls.log"

checks = []

def make_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}


# ── Check 1: Backup file exists ───────────────────────────────────────────────
try:
    bak_files = glob.glob(f"{DIST_DIR}/auth-profiles-*.js.bak")
    if bak_files:
        c = make_check(
            "backup_created",
            True,
            f"Backup file found: {bak_files[0]}"
        )
    else:
        c = make_check(
            "backup_created",
            False,
            f"No auth-profiles-*.js.bak found in {DIST_DIR}"
        )
except Exception as e:
    c = make_check("backup_created", False, f"Exception: {e}")
checks.append(c)


# ── Check 2: Dist JS file is patched with extractMentionsFromText ─────────────
try:
    dist_files = glob.glob(f"{DIST_DIR}/auth-profiles-*.js")
    # Exclude .bak files
    dist_js = [f for f in dist_files if not f.endswith(".bak")]
    if not dist_js:
        c = make_check(
            "dist_js_patched",
            False,
            f"No auth-profiles-*.js (non-bak) found in {DIST_DIR}"
        )
    else:
        content = open(dist_js[0], "r").read()
        if "extractMentionsFromText" in content:
            # Also check the m.mentions payload is present
            has_mentions_payload = (
                "org.matrix.msc3952.mentions" in content or
                "m.mentions" in content or
                "user_ids" in content
            )
            if has_mentions_payload:
                c = make_check(
                    "dist_js_patched",
                    True,
                    f"Dist JS contains extractMentionsFromText and m.mentions payload in {dist_js[0]}"
                )
            else:
                c = make_check(
                    "dist_js_patched",
                    False,
                    f"Dist JS has extractMentionsFromText but missing m.mentions/user_ids payload in {dist_js[0]}"
                )
        else:
            c = make_check(
                "dist_js_patched",
                False,
                f"Dist JS does NOT contain extractMentionsFromText in {dist_js[0]}"
            )
except Exception as e:
    c = make_check("dist_js_patched", False, f"Exception: {e}")
checks.append(c)


# ── Check 3: formatting.ts contains extractMentionsFromText ───────────────────
try:
    if not os.path.exists(FORMATTING_TS):
        c = make_check(
            "formatting_ts_marked",
            False,
            f"formatting.ts not found at {FORMATTING_TS}"
        )
    else:
        ts_content = open(FORMATTING_TS, "r").read()
        if "extractMentionsFromText" in ts_content:
            c = make_check(
                "formatting_ts_marked",
                True,
                "formatting.ts contains extractMentionsFromText — patch status marker present"
            )
        else:
            c = make_check(
                "formatting_ts_marked",
                False,
                "formatting.ts does NOT contain extractMentionsFromText — patch not applied or status check was skipped"
            )
except Exception as e:
    c = make_check("formatting_ts_marked", False, f"Exception: {e}")
checks.append(c)


# ── Check 4: Gateway restart was called ───────────────────────────────────────
try:
    if not os.path.exists(CLI_LOG):
        c = make_check(
            "gateway_restarted",
            False,
            f"CLI call log not found at {CLI_LOG}"
        )
    else:
        log_content = open(CLI_LOG, "r").read()
        if "openclaw gateway restart" in log_content:
            c = make_check(
                "gateway_restarted",
                True,
                "openclaw gateway restart was invoked (found in CLI call log)"
            )
        else:
            c = make_check(
                "gateway_restarted",
                False,
                f"'openclaw gateway restart' NOT found in CLI log. Log content:\n{log_content[:500]}"
            )
except Exception as e:
    c = make_check("gateway_restarted", False, f"Exception: {e}")
checks.append(c)


# ── Check 5: Backup content matches original unpatched JS ─────────────────────
try:
    bak_files = glob.glob(f"{DIST_DIR}/auth-profiles-*.js.bak")
    dist_js = [f for f in glob.glob(f"{DIST_DIR}/auth-profiles-*.js") if not f.endswith(".bak")]
    if bak_files and dist_js:
        bak_content = open(bak_files[0], "r").read()
        js_content = open(dist_js[0], "r").read()
        # Backup should NOT have the patch (it's the original)
        bak_is_original = "extractMentionsFromText" not in bak_content
        # Patched file should differ from backup
        files_differ = bak_content != js_content
        if bak_is_original and files_differ:
            c = make_check(
                "backup_is_original",
                True,
                "Backup is the original unpatched file, and patched file differs from backup"
            )
        elif not bak_is_original:
            c = make_check(
                "backup_is_original",
                False,
                "Backup file already contains the patch — backup was not taken from the original"
            )
        else:
            c = make_check(
                "backup_is_original",
                False,
                "Backup and patched file are identical — patching may not have occurred"
            )
    else:
        c = make_check(
            "backup_is_original",
            False,
            "Cannot compare: bak or dist JS not found"
        )
except Exception as e:
    c = make_check("backup_is_original", False, f"Exception: {e}")
checks.append(c)


# ── Final scoring ─────────────────────────────────────────────────────────────
num_passed = sum(1 for c in checks if c["passed"])
total = len(checks)
score = round(num_passed / total, 4)
passed = num_passed == total

result = {
    "passed": passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))
sys.exit(0 if passed else 1)