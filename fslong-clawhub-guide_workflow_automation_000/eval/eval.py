#!/usr/bin/env python3
import sys
import json
import os
import re
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
LOG_FILE = "/var/log/clawhub/publish.log"

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# --- Read publish log ---
publish_entries = []
try:
    with open(LOG_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entry = json.loads(line)
                    publish_entries.append(entry)
                except json.JSONDecodeError:
                    pass
except Exception as e:
    add_check("log_readable", False, f"Could not read publish log: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# Find successful publish entries
successful = [e for e in publish_entries if e.get("command") == "publish" and e.get("status") == "success"]
failed = [e for e in publish_entries if e.get("command") == "publish" and e.get("status") == "error"]

# CHECK 1: At least one successful publish happened
if successful:
    add_check("publish_succeeded", True, f"Found {len(successful)} successful publish(es). Latest: {successful[-1]}")
else:
    reasons = [e.get("reason", "unknown") for e in failed]
    add_check("publish_succeeded", False, f"No successful publish found. Failed attempts: {len(failed)}, reasons: {reasons}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# Use the last successful publish entry
pub = successful[-1]

# CHECK 2: Correct skill path (must target 智能摘要 directory)
path = pub.get("path", "")
target_skill_path = os.path.join(
    workspace, "home", "fslong", ".copaw", "workspaces", "default", "active_skills", "智能摘要"
)
path_correct = (
    "智能摘要" in path and
    os.path.isdir(path) and
    os.path.isfile(os.path.join(path, "SKILL.md"))
)
if path_correct:
    add_check("correct_skill_path", True, f"Path '{path}' correctly points to 智能摘要 skill directory")
else:
    add_check("correct_skill_path", False, f"Path '{path}' does not correctly point to the 智能摘要 skill. Expected path containing '智能摘要' with a valid SKILL.md")

# CHECK 3: Slug must be valid (lowercase ASCII, no Chinese)
slug = pub.get("slug", "")
slug_valid = bool(re.match(r'^[a-z0-9_-]+$', slug)) and len(slug) > 0
if slug_valid:
    add_check("valid_slug", True, f"Slug '{slug}' is valid (lowercase ASCII with hyphens/underscores only)")
else:
    add_check("valid_slug", False, f"Slug '{slug}' is invalid. Must be lowercase letters, digits, hyphens, underscores only (no Chinese, spaces, or uppercase)")

# CHECK 4: Slug must NOT be a transliteration of Chinese or contain Chinese chars
slug_no_chinese = all(ord(c) < 128 for c in slug)
if slug_no_chinese:
    add_check("slug_no_chinese_chars", True, f"Slug '{slug}' contains no Chinese characters")
else:
    add_check("slug_no_chinese_chars", False, f"Slug '{slug}' contains non-ASCII/Chinese characters")

# CHECK 5: Tags must be English only (no CJK characters)
tags_str = pub.get("tags", "")
tags_list = [t.strip() for t in tags_str.split(",") if t.strip()]
tags_english_only = all(
    all(ord(c) < 128 for c in tag)
    for tag in tags_list
)
has_tags = len(tags_list) > 0
if tags_english_only and has_tags:
    add_check("tags_english_only", True, f"Tags '{tags_str}' are all English/ASCII")
else:
    bad_tags = [t for t in tags_list if any(ord(c) >= 128 for c in t)]
    add_check("tags_english_only", False, f"Tags contain non-English characters: {bad_tags}. Original SKILL.md had Chinese tags '知识管理,摘要,文本,AI' which must be converted to English.")

# CHECK 6: Version must be semver AND must be a minor bump from 1.0.0 (i.e., 1.1.0 or higher minor)
version = pub.get("version", "")
semver_match = re.match(r'^(\d+)\.(\d+)\.(\d+)$', version)
version_valid_semver = bool(semver_match)
if version_valid_semver:
    major, minor, patch = int(semver_match.group(1)), int(semver_match.group(2)), int(semver_match.group(3))
    # The skill was at 1.0.0, added new features -> should be at least 1.1.0
    # Accept 1.1.0, 1.1.x, 1.x.x where x>0, or 2.0.0
    version_bumped = (major > 1) or (major == 1 and minor >= 1)
    if version_bumped:
        add_check("version_correctly_bumped", True, f"Version '{version}' is a valid bump from 1.0.0 for a new feature release")
    else:
        add_check("version_correctly_bumped", False, f"Version '{version}' was not bumped from 1.0.0. A new feature (batch processing) warrants at least a minor bump to 1.1.0")
    add_check("version_is_semver", True, f"Version '{version}' is valid semver")
else:
    add_check("version_is_semver", False, f"Version '{version}' is not valid semver (x.y.z)")
    add_check("version_correctly_bumped", False, f"Cannot evaluate version bump with invalid semver '{version}'")

# CHECK 7: Changelog must be non-empty and meaningful
changelog = pub.get("changelog", "")
changelog_meaningful = len(changelog.strip()) >= 5
if changelog_meaningful:
    add_check("changelog_provided", True, f"Changelog is present: '{changelog[:100]}'")
else:
    add_check("changelog_provided", False, f"Changelog is missing or too short: '{changelog}'")

# CHECK 8: Name field must be present
name = pub.get("name", "")
name_present = len(name.strip()) > 0
if name_present:
    add_check("name_provided", True, f"Name '{name}' is provided")
else:
    add_check("name_provided", False, "Name field is empty or missing")

# CHECK 9: Verify whoami was called (check for any log entry, or check process history)
# We can't easily check this, but we can verify the publish was done correctly which implies login check
# Instead check that no failed-due-to-auth attempts preceded success
auth_failures = [e for e in failed if e.get("reason") in ("not_logged_in", "auth_required")]
if not auth_failures:
    add_check("no_auth_failures", True, "No authentication failures detected; login state was properly handled")
else:
    add_check("no_auth_failures", False, f"Authentication failures detected: {auth_failures}")

# --- Compute final score ---
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 3) if total > 0 else 0.0

# Must pass critical checks to fully pass
critical_checks = [
    "publish_succeeded",
    "valid_slug",
    "slug_no_chinese_chars",
    "tags_english_only",
    "version_is_semver",
    "version_correctly_bumped",
]
critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)

overall_passed = critical_passed and score >= 0.75

print(json.dumps({
    "passed": overall_passed,
    "score": score,
    "checks": checks
}, ensure_ascii=False, indent=2))