import sys
import json
import re
from pathlib import Path

workspace = sys.argv[1]

checks = []

def find_snapshot(workspace):
    candidates = list(Path(workspace).rglob("numerology_snapshot.md"))
    return candidates[0] if candidates else None

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# --- Locate file ---
snapshot_path = find_snapshot(workspace)
file_exists = snapshot_path is not None
check("file_exists", file_exists, f"Found at: {snapshot_path}" if file_exists else "numerology_snapshot.md not found anywhere in workspace")

if not file_exists:
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

try:
    content = snapshot_path.read_text(encoding="utf-8")
except Exception as e:
    check("file_readable", False, f"Could not read file: {e}")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

content_lower = content.lower()

# ---------------------------------------------------------------
# CHECK 1: Correct Life Path Number
# DOB: 29/02/1988
# Step 1: Day=29 → 2+9=11 → PRESERVE as master number 11
# OR: reduce everything together: 2+9+0+2+1+9+8+8 = 39 → 3+9=12 → 1+2=3
# OR month+day+year: 2 + 2+9 + 1+9+8+8 = 2+11+26 = ... many valid paths
# The canonical Pythagorean method: add month, day, year separately then combine
#   Month: 02 → 2
#   Day:   29 → 2+9 = 11 (MASTER NUMBER, preserve)
#   Year:  1988 → 1+9+8+8 = 26 → 2+6 = 8
#   Sum:   2 + 11 + 8 = 21 → 2+1 = 3
# So Life Path = 3 (with master number 11 appearing at day step)
# Alternative flat reduction: 2+9+2+1+9+8+8 = 39 → 12 → 3 (also gives 3)
# Both land on 3. Accept 3 as the Life Path number.
# ---------------------------------------------------------------
lp_correct = bool(re.search(r'life\s*path[^0-9]*\b3\b', content_lower))
check(
    "life_path_number_correct",
    lp_correct,
    "Life Path number should be 3 (DOB: 29/02/1988). " +
    ("Found correctly." if lp_correct else "Not found or incorrect in output.")
)

# ---------------------------------------------------------------
# CHECK 2: Life Path math steps shown
# Must show arithmetic steps, not just the final answer
# e.g., "2+9", "11", "1+9+8+8", "26", etc.
# ---------------------------------------------------------------
math_indicators = [
    r'2\s*[+＋]\s*9',       # day reduction 2+9
    r'1\s*[+＋]\s*9\s*[+＋]\s*8\s*[+＋]\s*8',  # year 1+9+8+8
    r'\b26\b',              # year sub-total
    r'\b11\b',              # master number appearance
]
math_shown_count = sum(1 for pat in math_indicators if re.search(pat, content))
math_shown = math_shown_count >= 2
check(
    "life_path_math_shown",
    math_shown,
    f"Reduction steps visible: {math_shown_count}/4 expected patterns. "
    "Must show arithmetic steps (e.g., 2+9=11, 1+9+8+8=26)."
)

# ---------------------------------------------------------------
# CHECK 3: Master number 11 acknowledged
# The day 29 reduces to 11, which is a master number.
# Must be acknowledged (even if further reduced later, must mention it).
# ---------------------------------------------------------------
master_mentioned = bool(re.search(r'\b11\b', content)) and (
    'master' in content_lower or
    re.search(r'\b11\b.*\b(preserve|kept|master|stop)\b', content_lower) or
    re.search(r'2\s*[+＋]\s*9\s*[=→\-]*\s*11', content) or
    re.search(r'\b11\b.*life\s*path|life\s*path.*\b11\b', content_lower) or
    # Accept if 11 appears prominently in the math section
    content.count('11') >= 2
)
check(
    "master_number_11_acknowledged",
    master_mentioned,
    "Master number 11 (from day 29→11) must be acknowledged. " +
    ("Found." if master_mentioned else "Not found — agent may have skipped master number rule.")
)

# ---------------------------------------------------------------
# CHECK 4: Expression/Destiny number computed
# Name: Héléna Vögel-Moraes (must normalize diacritics)
# Normalized: HELENA VOGEL MORAES
# Pythagorean mapping (A=1,B=2,...,I=9,J=1,K=2,...,Z=8):
# H=8, E=5, L=3, E=5, N=5, A=1 → 27 → 9
# V=4, O=6, G=7, E=5, L=3 → 25 → 7
# M=4, O=6, R=9, A=1, E=5, S=1 → 26 → 8
# Total: 9+7+8=24 → 6
# Expression Number = 6
# (Hyphen treated as separator, not a letter — standard)
# ---------------------------------------------------------------
expr_correct = bool(re.search(r'(expression|destiny)[^0-9]*\b6\b', content_lower))
check(
    "expression_number_correct",
    expr_correct,
    "Expression/Destiny number should be 6 for 'Héléna Vögel-Moraes' (Pythagorean). " +
    ("Found correctly." if expr_correct else "Not found or incorrect.")
)

# ---------------------------------------------------------------
# CHECK 5: Diacritics handling stated
# Must mention normalization of accented characters
# ---------------------------------------------------------------
diacritics_handled = bool(re.search(
    r'(normaliz|diacritic|accent|é|ö|strip|unicode|decompos|ascii)',
    content_lower
))
check(
    "diacritics_handling_stated",
    diacritics_handled,
    "Must acknowledge handling of accented characters (é, ö). " +
    ("Found." if diacritics_handled else "No mention of diacritics normalization.")
)

# ---------------------------------------------------------------
# CHECK 6: Method declared (Pythagorean)
# ---------------------------------------------------------------
method_declared = bool(re.search(r'(pythagorean|method\s*:)', content_lower))
check(
    "method_declared",
    method_declared,
    "Output must declare the numerology method used (e.g., 'Pythagorean'). " +
    ("Found." if method_declared else "Method not declared.")
)

# ---------------------------------------------------------------
# CHECK 7: Disclaimer present
# Must mention entertainment/reflection and not science/professional advice
# ---------------------------------------------------------------
disclaimer_present = bool(re.search(
    r'(entertainment|reflection|not.*science|not.*professional|not.*advice|disclaimer)',
    content_lower
))
check(
    "disclaimer_present",
    disclaimer_present,
    "Must include a disclaimer (entertainment/reflection only, not professional advice). " +
    ("Found." if disclaimer_present else "Disclaimer missing.")
)

# ---------------------------------------------------------------
# CHECK 8: Correct input names in output
# Must reference the actual name and DOB from the request
# ---------------------------------------------------------------
name_in_output = bool(re.search(r'h[eé]l[eé]na|vogel|moraes', content_lower))
dob_in_output = bool(re.search(r'(29|1988|02|february|feb)', content_lower))
inputs_present = name_in_output and dob_in_output
check(
    "inputs_referenced",
    inputs_present,
    f"Name in output: {name_in_output}, DOB in output: {dob_in_output}. "
    "Both the name and birth date must appear in the output."
)

# ---------------------------------------------------------------
# CHECK 9: Themes section present (2+ bullets)
# ---------------------------------------------------------------
themes_present = bool(re.search(r'(theme|meaning|symbolic|insight)', content_lower))
bullet_count = len(re.findall(r'^\s*[-*•]\s+.+', content, re.MULTILINE))
themes_check = themes_present and bullet_count >= 2
check(
    "themes_section_present",
    themes_check,
    f"Themes section found: {themes_present}, bullets found: {bullet_count}. "
    "Need a themes section with at least 2 bullet points."
)

# ---------------------------------------------------------------
# CHECK 10: Expression math steps shown
# Must show letter-to-number mapping steps
# ---------------------------------------------------------------
expr_math_shown = bool(re.search(
    r'([h-H]\s*[=:]\s*8|[e-E]\s*[=:]\s*5|[l-L]\s*[=:]\s*3|[v-V]\s*[=:]\s*4|[m-M]\s*[=:]\s*4)',
    content
))
check(
    "expression_math_shown",
    expr_math_shown,
    "Expression calculation must show letter-to-digit mapping (e.g., H=8, E=5, L=3). " +
    ("Found." if expr_math_shown else "Letter mapping steps not visible.")
)

# ---------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4)
all_passed = passed_count == total

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))