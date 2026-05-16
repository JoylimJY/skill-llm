import sys
import json
import os
import re
from pathlib import Path

workspace = sys.argv[1]

checks = []
score_total = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ── 1. Read the sanitized SKILL.md ──────────────────────────────────────────
skill_md_path = Path(workspace) / "MAIBOT/skills/obsidian-daily/SKILL.md"

skill_content = ""
try:
    with open(skill_md_path, "r", encoding="utf-8") as f:
        skill_content = f.read()
    score_total += add_check(
        "SKILL.md exists and is readable",
        True,
        f"File found at {skill_md_path}"
    )
except Exception as e:
    score_total += add_check(
        "SKILL.md exists and is readable",
        False,
        f"Could not read SKILL.md: {e}"
    )

# ── 2. Check Korean text removed ────────────────────────────────────────────
KOREAN_PATTERN = re.compile(r'[\uAC00-\uD7A3]')
has_korean = bool(KOREAN_PATTERN.search(skill_content))
score_total += add_check(
    "No Korean characters in SKILL.md",
    not has_korean,
    "Korean text found — sanitization incomplete" if has_korean else "No Korean text detected"
)

# ── 3. Check personal paths removed ─────────────────────────────────────────
personal_patterns = [
    r'C:\\Users\\jini9',
    r'C:/Users/jini9',
    r'JINI_SYNC',
    r'jini9@',
    r'jini9\\',
]
found_personal = []
for pat in personal_patterns:
    if re.search(pat, skill_content, re.IGNORECASE):
        found_personal.append(pat)

score_total += add_check(
    "No personal paths or account names in SKILL.md",
    len(found_personal) == 0,
    f"Found personal references: {found_personal}" if found_personal else "All personal paths removed"
)

# ── 4. Generic placeholders present ─────────────────────────────────────────
# Must have replaced personal paths with something generic
placeholder_patterns = [
    r'\$VAULT_PATH|~/vault|your-username|\$HOME|<your-',
]
has_placeholder = any(re.search(p, skill_content, re.IGNORECASE) for p in placeholder_patterns)
score_total += add_check(
    "Generic placeholders used in SKILL.md",
    has_placeholder,
    "No generic placeholder found (e.g. $VAULT_PATH, ~/vault)" if not has_placeholder else "Generic placeholder detected"
)

# ── 5. Description field is in English ──────────────────────────────────────
desc_match = re.search(r'^description:\s*(.+)$', skill_content, re.MULTILINE)
desc_ok = False
desc_detail = "description: field not found"
if desc_match:
    desc_value = desc_match.group(1).strip()
    desc_has_korean = bool(KOREAN_PATTERN.search(desc_value))
    desc_ok = not desc_has_korean
    desc_detail = f"description value: '{desc_value}'" + (" [KOREAN DETECTED]" if desc_has_korean else " [English OK]")
score_total += add_check(
    "description: field is in English",
    desc_ok,
    desc_detail
)

# ── 6. Read publish attempts from mock state ─────────────────────────────────
STATE_FILE = "/usr/local/lib/clawhub-mock/clawhub_state.json"
attempts = []
try:
    with open(STATE_FILE, "r") as f:
        mock_state = json.load(f)
    attempts = mock_state.get("publish_attempts", [])
except Exception as e:
    pass

# ── 7. Agent attempted publish ───────────────────────────────────────────────
score_total += add_check(
    "clawhub publish was invoked at least once",
    len(attempts) > 0,
    f"Total publish attempts recorded: {len(attempts)}"
)

# ── 8. Agent attempted conflict slug first, then -mai suffix ────────────────
slugs_attempted = [a.get("slug", "") for a in attempts]
tried_base = "obsidian-daily" in slugs_attempted
tried_mai = "obsidian-daily-mai" in slugs_attempted

score_total += add_check(
    "Slug conflict encountered and resolved with -mai suffix",
    tried_mai,
    f"Slugs attempted: {slugs_attempted}. Expected final slug to be 'obsidian-daily-mai'."
)

# ── 9. Final successful publish has correct version (1.1.0 for translation) ──
# Version rule: first publish with content-fix/translation → 1.1.0
final_attempt = None
for a in reversed(attempts):
    if a.get("slug") == "obsidian-daily-mai":
        final_attempt = a
        break

version_ok = False
version_detail = "No successful publish attempt with slug 'obsidian-daily-mai' found"
if final_attempt:
    v = final_attempt.get("version", "")
    version_ok = (v == "1.1.0")
    version_detail = f"Version used: '{v}' (expected '1.1.0' — translation/content-fix = minor bump)"

score_total += add_check(
    "Correct version 1.1.0 used (translation = minor bump)",
    version_ok,
    version_detail,
    weight=1.5
)

# ── 10. Required flags present in final publish call ────────────────────────
flags_ok = False
flags_detail = "No successful -mai publish attempt found"
if final_attempt:
    missing = []
    if not final_attempt.get("slug"):
        missing.append("--slug")
    if not final_attempt.get("name"):
        missing.append("--name")
    if not final_attempt.get("version"):
        missing.append("--version")
    if not final_attempt.get("changelog"):
        missing.append("--changelog")
    flags_ok = len(missing) == 0
    flags_detail = f"Missing flags: {missing}" if missing else f"All required flags present. changelog='{final_attempt.get('changelog')}'"

score_total += add_check(
    "All required publish flags used (--slug, --name, --version, --changelog)",
    flags_ok,
    flags_detail
)

# ── 11. Skill path argument passed to publish ────────────────────────────────
path_ok = False
path_detail = "No publish attempt with skill path found"
if final_attempt:
    sp = final_attempt.get("skill_path", "") or ""
    # Accept various valid path forms pointing to obsidian-daily
    path_ok = "obsidian-daily" in sp
    path_detail = f"Skill path passed: '{sp}'"

score_total += add_check(
    "Skill folder path passed to clawhub publish",
    path_ok,
    path_detail
)

# ── Compute final score ───────────────────────────────────────────────────────
# Weights: most checks = 1.0, version check = 1.5. Total possible = 11 + 0.5 = 11.5
max_score = 11.5
final_score = round(score_total / max_score, 3)
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": final_score,
    "checks": checks
}

print(json.dumps(result, indent=2))