import sys
import json
import os
import re
from pathlib import Path

workspace = sys.argv[1]

checks = []
passed_all = True

def fail_check(name, detail):
    checks.append({"name": name, "passed": False, "detail": detail})
    global passed_all
    passed_all = False

def pass_check(name, detail):
    checks.append({"name": name, "passed": True, "detail": detail})

# ── Locate the clean URL list file the agent should have created ──────────────
# Agent must create a properly formatted URL list file somewhere accessible
# and pass it to the downloader. The downloader log records the url_file used.

# 1. Find _download_log.json produced by the downloader
log_files = list(Path(workspace).rglob("_download_log.json"))
if not log_files:
    fail_check("downloader_executed", "No _download_log.json found. The downloader was never executed.")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

pass_check("downloader_executed", f"Found log at {log_files[0]}")

# Use the first (most recent or only) log
log_path = log_files[0]
try:
    with open(log_path) as lf:
        log = json.load(lf)
except Exception as e:
    fail_check("log_readable", f"Could not parse log JSON: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

pass_check("log_readable", "Log JSON parsed successfully.")

# ── Check 2: Custom URL file was used (not the default urls.txt) ─────────────
url_file_used = log.get("url_file", "")
argv_used = log.get("argv", [])

# The skill docs say default is urls.txt next to the script.
# The task asks for a custom URL file, so the agent must have passed one.
default_url_path = os.path.abspath(
    os.path.join(workspace, "skills/bulk-tiktok-downloader/scripts/../urls.txt")
)
default_url_path2 = os.path.abspath(
    os.path.join(workspace, "skills/bulk-tiktok-downloader/urls.txt")
)
is_default = (
    url_file_used.endswith("urls.txt") and (
        os.path.dirname(url_file_used) == os.path.dirname(
            os.path.abspath(os.path.join(workspace, "skills/bulk-tiktok-downloader/scripts/downloader.py"))
        )
    )
)
# Allow as long as the argv had at least one arg (url_file explicitly passed)
if len(argv_used) >= 1:
    pass_check("custom_url_file_passed",
               f"Agent passed custom URL file as first positional arg: {argv_used[0]}")
else:
    fail_check("custom_url_file_passed",
               "Agent ran downloader with no arguments (used defaults). "
               "A custom URL file and output directory were required.")

# ── Check 3: Custom output directory was passed (2nd positional arg) ──────────
if len(argv_used) >= 2:
    pass_check("custom_output_dir_passed",
               f"Agent passed custom output dir as second positional arg: {argv_used[1]}")
else:
    fail_check("custom_output_dir_passed",
               "Agent did not pass a custom output directory as the second positional argument. "
               "Expected: python3 downloader.py <url_file> <out_dir>")

# ── Check 4: The URL list file is properly formatted ─────────────────────────
TIKTOK_PAT = re.compile(r'https?://(www\.)?(tiktok\.com|vm\.tiktok\.com)/\S+')

try:
    with open(url_file_used) as uf:
        url_file_lines = uf.readlines()
except Exception as e:
    fail_check("url_file_format", f"Could not open URL file at {url_file_used}: {e}")
    url_file_lines = []

if url_file_lines:
    # Check that non-URL annotation lines are commented out with #
    annotation_patterns = [
        r'^BATCH\s+\d+',
        r'^NOTE\s*:',
        r'^DO NOT',
        r'^duplicate',
        r'^deleted',
        r'^Exported from',
        r'^Generated\s*:',
    ]
    uncommented_annotations = []
    youtube_lines = []
    bare_tiktok_urls = []
    commented_tiktok = []

    for line in url_file_lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            # If it contains a TikTok URL, flag it (should not comment out valid TikTok URLs)
            if TIKTOK_PAT.search(stripped):
                commented_tiktok.append(stripped)
            continue
        # Non-empty, non-comment line
        if TIKTOK_PAT.match(stripped):
            bare_tiktok_urls.append(stripped)
        elif "youtube.com" in stripped or "youtu.be" in stripped:
            youtube_lines.append(stripped)
        else:
            # Check if it looks like an annotation
            for pat in annotation_patterns:
                if re.match(pat, stripped, re.IGNORECASE):
                    uncommented_annotations.append(stripped)
                    break

    if uncommented_annotations:
        fail_check("url_file_format",
                   f"URL file contains uncommented annotation/note lines that should start with '#': "
                   f"{uncommented_annotations[:3]}")
    else:
        pass_check("url_file_format",
                   "All annotation/note lines are properly commented out with '#'.")

    if youtube_lines:
        fail_check("no_non_tiktok_urls",
                   f"URL file includes non-TikTok URLs (e.g., YouTube): {youtube_lines}")
    else:
        pass_check("no_non_tiktok_urls",
                   "No non-TikTok URLs found in the URL list file.")

    if commented_tiktok:
        fail_check("valid_tiktok_not_commented",
                   f"Valid TikTok URLs are commented out and will be skipped: {commented_tiktok[:3]}")
    else:
        pass_check("valid_tiktok_not_commented",
                   "No valid TikTok URLs are incorrectly commented out.")

    if bare_tiktok_urls:
        pass_check("tiktok_urls_present",
                   f"Found {len(bare_tiktok_urls)} valid TikTok URLs as active (uncommented) lines.")
    else:
        fail_check("tiktok_urls_present",
                   "No active (uncommented) TikTok URLs found in the URL file.")

# ── Check 5: Successful downloads occurred (stub .mp4 files created) ──────────
out_dir_used = log.get("out_dir", "")
success_count = log.get("success_count", 0)
failed_count = log.get("failed_count", 0)

if success_count > 0:
    pass_check("downloads_succeeded",
               f"{success_count} video(s) downloaded successfully to {out_dir_used}.")
else:
    fail_check("downloads_succeeded",
               f"No successful downloads recorded. out_dir={out_dir_used}")

# ── Check 6: Failed URLs were surfaced (the 2 simulated failures) ─────────────
failed_entries = log.get("failed", [])
failed_urls = [e["url"] for e in failed_entries]

expected_failures = {
    "https://www.tiktok.com/@brandX/video/0000000000000001",
    "https://www.tiktok.com/@brandX/video/0000000000000002",
}
# Only check failures that were in the URL file (agent may have excluded them by filtering)
# If agent properly filtered them out (they ARE valid TikTok URLs so should be included),
# they will show as failures in the log.
found_failures = expected_failures & set(failed_urls)
if found_failures:
    pass_check("failed_urls_surfaced",
               f"Failed URLs correctly surfaced in log: {sorted(found_failures)}")
else:
    # It's acceptable if the agent included them and they failed, or if the log just shows counts
    if failed_count > 0:
        pass_check("failed_urls_surfaced",
                   f"Some failures recorded ({failed_count}); known bad URLs may have been included.")
    else:
        fail_check("failed_urls_surfaced",
                   "No failed URLs in log. The two known bad URLs (private/deleted) "
                   "should have been attempted and surfaced as failures.")

# ── Check 7: Output directory exists and contains downloaded stubs ────────────
if out_dir_used and os.path.isdir(out_dir_used):
    mp4_files = list(Path(out_dir_used).glob("*.mp4"))
    if mp4_files:
        pass_check("output_dir_populated",
                   f"Output directory '{out_dir_used}' contains {len(mp4_files)} .mp4 stub file(s).")
    else:
        fail_check("output_dir_populated",
                   f"Output directory '{out_dir_used}' exists but contains no .mp4 files.")
else:
    fail_check("output_dir_populated",
               f"Output directory '{out_dir_used}' does not exist.")

# ── Score ─────────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 3) if total > 0 else 0.0
final_pass = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": final_pass,
    "score": score,
    "checks": checks
}, indent=2))