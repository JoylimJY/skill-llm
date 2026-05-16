#!/usr/bin/env python3
import sys
import json
import os
import re
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
passed_all = True

def add_check(name, passed, detail):
    global passed_all
    checks.append({"name": name, "passed": passed, "detail": detail})
    if not passed:
        passed_all = False

# ── Load ground-truth config ──────────────────────────────────────────────
try:
    config_path = Path.home() / ".config" / "cloudflare" / "r2.json"
    with open(config_path) as f:
        config = json.load(f)
    BUCKET = config["bucket"]               # "ecommerce-assets-prod"
    PUBLIC_DOMAIN = config["publicDomain"]  # "pub-7f3e2d1c9b8a4056.r2.dev"
    REMOTE_PREFIX = "campaigns/q4-launch"
except Exception as e:
    add_check("config_readable", False, f"Cannot read r2.json: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# Expected files in the campaign directory
campaign_dir = workspace / "marketing" / "campaign_q4"
try:
    expected_files = sorted([f.name for f in campaign_dir.iterdir() if f.is_file()])
except Exception as e:
    add_check("campaign_dir_exists", False, f"Cannot read campaign dir: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

add_check("campaign_dir_exists", True, f"Found {len(expected_files)} campaign files: {expected_files}")

# ── Check 1: wrangler was actually invoked ────────────────────────────────
wrangler_log = Path("/tmp/wrangler_calls.log")
try:
    if not wrangler_log.exists():
        add_check("wrangler_invoked", False, "No wrangler calls logged at /tmp/wrangler_calls.log")
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        sys.exit(0)
    log_content = wrangler_log.read_text()
    add_check("wrangler_invoked", True, f"wrangler was called. Log size: {len(log_content)} bytes")
except Exception as e:
    add_check("wrangler_invoked", False, f"Cannot read wrangler log: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── Check 2: Correct bucket was used (NOT the wrong decoy) ───────────────
try:
    put_lines = [l for l in log_content.splitlines() if l.startswith("PUT:")]
    used_wrong_bucket = any("WRONG-BUCKET" in l for l in put_lines)
    used_correct_bucket = any(BUCKET in l for l in put_lines)

    if used_wrong_bucket:
        add_check("correct_bucket_used", False,
                  "Agent used WRONG-BUCKET from decoy config instead of ~/.config/cloudflare/r2.json")
    elif not used_correct_bucket:
        add_check("correct_bucket_used", False,
                  f"Bucket '{BUCKET}' not found in PUT calls. Calls: {put_lines[:5]}")
    else:
        add_check("correct_bucket_used", True, f"Correct bucket '{BUCKET}' was used.")
except Exception as e:
    add_check("correct_bucket_used", False, f"Error checking bucket: {e}")

# ── Check 3: All campaign files were uploaded ─────────────────────────────
try:
    put_lines = [l for l in log_content.splitlines() if l.startswith("PUT:")]
    uploaded_paths = []
    for line in put_lines:
        m = re.search(r'bucket_path=(\S+)', line)
        if m:
            uploaded_paths.append(m.group(1))

    missing_files = []
    for fname in expected_files:
        found = any(fname in p for p in uploaded_paths)
        if not found:
            missing_files.append(fname)

    if missing_files:
        add_check("all_files_uploaded", False,
                  f"Missing uploads for: {missing_files}. Found paths: {uploaded_paths}")
    else:
        add_check("all_files_uploaded", True,
                  f"All {len(expected_files)} files were uploaded.")
except Exception as e:
    add_check("all_files_uploaded", False, f"Error checking uploads: {e}")

# ── Check 4: Correct remote prefix used (campaigns/q4-launch/) ───────────
try:
    correct_prefix_count = sum(
        1 for p in uploaded_paths if p.startswith(f"{BUCKET}/{REMOTE_PREFIX}/")
    )
    total_uploads = len(uploaded_paths)

    if total_uploads == 0:
        add_check("correct_remote_prefix", False, "No uploads found to check prefix.")
    elif correct_prefix_count == total_uploads:
        add_check("correct_remote_prefix", True,
                  f"All {total_uploads} uploads use prefix '{REMOTE_PREFIX}/'")
    else:
        add_check("correct_remote_prefix", False,
                  f"Only {correct_prefix_count}/{total_uploads} uploads use prefix '{REMOTE_PREFIX}/'. "
                  f"Sample paths: {uploaded_paths[:3]}")
except Exception as e:
    add_check("correct_remote_prefix", False, f"Error checking prefix: {e}")

# ── Check 5: --remote flag was used ──────────────────────────────────────
try:
    call_lines = [l for l in log_content.splitlines() if l.startswith("CALL:")]
    put_calls_with_remote = [l for l in call_lines if "object put" in l and "--remote" in l]
    put_calls_total = [l for l in call_lines if "object put" in l]

    if not put_calls_total:
        add_check("remote_flag_used", False, "No 'wrangler r2 object put' calls found.")
    elif len(put_calls_with_remote) == len(put_calls_total):
        add_check("remote_flag_used", True,
                  f"All {len(put_calls_with_remote)} put calls used --remote flag.")
    else:
        add_check("remote_flag_used", False,
                  f"Only {len(put_calls_with_remote)}/{len(put_calls_total)} put calls used --remote.")
except Exception as e:
    add_check("remote_flag_used", False, f"Error checking --remote flag: {e}")

# ── Check 6: cdn_urls.txt exists and has correct public URLs ──────────────
try:
    cdn_files = list(workspace.rglob("cdn_urls.txt"))
    if not cdn_files:
        add_check("cdn_urls_file_exists", False,
                  "cdn_urls.txt not found anywhere in workspace.")
        add_check("cdn_urls_correct_domain", False, "cdn_urls.txt missing, cannot check.")
        add_check("cdn_urls_all_files", False, "cdn_urls.txt missing, cannot check.")
    else:
        cdn_file = cdn_files[0]
        cdn_content = cdn_file.read_text().strip()
        add_check("cdn_urls_file_exists", True, f"Found cdn_urls.txt at {cdn_file}")

        # Check that the correct public domain is used (NOT wrong domain, NOT bucket name)
        urls = [line.strip() for line in cdn_content.splitlines() if line.strip()]
        wrong_domain_used = any("WRONG-DOMAIN" in u for u in urls)
        correct_domain_used = any(PUBLIC_DOMAIN in u for u in urls)

        if wrong_domain_used:
            add_check("cdn_urls_correct_domain", False,
                      "cdn_urls.txt uses WRONG-DOMAIN from decoy config.")
        elif not correct_domain_used:
            add_check("cdn_urls_correct_domain", False,
                      f"cdn_urls.txt does not use publicDomain '{PUBLIC_DOMAIN}'. "
                      f"Found URLs: {urls[:3]}")
        else:
            add_check("cdn_urls_correct_domain", True,
                      f"cdn_urls.txt correctly uses publicDomain '{PUBLIC_DOMAIN}'.")

        # Check that all campaign files have a URL entry
        missing_in_urls = []
        for fname in expected_files:
            found = any(fname in u for u in urls)
            if not found:
                missing_in_urls.append(fname)

        if missing_in_urls:
            add_check("cdn_urls_all_files", False,
                      f"cdn_urls.txt missing entries for: {missing_in_urls}")
        else:
            add_check("cdn_urls_all_files", True,
                      f"cdn_urls.txt has entries for all {len(expected_files)} uploaded files.")

        # Check URL format: must be https://<publicDomain>/<prefix>/<filename>
        malformed = []
        for u in urls:
            if not u.startswith(f"https://{PUBLIC_DOMAIN}/{REMOTE_PREFIX}/"):
                malformed.append(u)

        if malformed:
            add_check("cdn_urls_format", False,
                      f"Some URLs have wrong format (expected https://{PUBLIC_DOMAIN}/{REMOTE_PREFIX}/<file>): "
                      f"{malformed[:3]}")
        else:
            add_check("cdn_urls_format", True,
                      f"All URLs match expected format https://{PUBLIC_DOMAIN}/{REMOTE_PREFIX}/<file>")

except Exception as e:
    add_check("cdn_urls_file_exists", False, f"Exception reading cdn_urls.txt: {e}")
    add_check("cdn_urls_correct_domain", False, "Exception occurred.")
    add_check("cdn_urls_all_files", False, "Exception occurred.")
    add_check("cdn_urls_format", False, "Exception occurred.")

# ── Final score ───────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 3) if total > 0 else 0.0
passed_all = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": passed_all,
    "score": score,
    "checks": checks
}, indent=2))