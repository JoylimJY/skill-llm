import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
home = Path.home()
neet_dir = home / "neet"

checks = []

def check(name, condition, detail):
    checks.append({"name": name, "passed": bool(condition), "detail": detail})
    return bool(condition)

# ── Helper: count lines matching a pattern ─────────────────────────────────
def grep_file(path, pattern, flags=re.IGNORECASE):
    try:
        text = path.read_text(errors="replace")
        return re.findall(pattern, text, flags)
    except Exception as e:
        return []

# ══════════════════════════════════════════════════════════════════════════
# CHECK 1: ~/neet/ directory structure exists
# ══════════════════════════════════════════════════════════════════════════
dirs_required = ["subjects", "sessions", "mocks", "flashcards"]
missing_dirs = [d for d in dirs_required if not (neet_dir / d).is_dir()]
check(
    "neet_directory_structure",
    len(missing_dirs) == 0,
    f"Missing dirs: {missing_dirs}" if missing_dirs else "All required subdirs present under ~/neet/"
)

# ══════════════════════════════════════════════════════════════════════════
# CHECK 2: profile.md exists with correct fields
# ══════════════════════════════════════════════════════════════════════════
profile_path = neet_dir / "profile.md"
try:
    profile_text = profile_path.read_text(errors="replace").lower()
    has_category = "obc" in profile_text
    has_state = "rajasthan" in profile_text
    has_target = "620" in profile_text or "620+" in profile_text
    has_exam_date = "2025" in profile_text and ("05" in profile_text or "may" in profile_text)
    has_usertype = "dropper" in profile_text
    profile_ok = has_category and has_state and has_target and has_exam_date and has_usertype
    check(
        "profile_md_content",
        profile_ok,
        f"profile.md found. OBC:{has_category}, Rajasthan:{has_state}, Target:{has_target}, Date:{has_exam_date}, Dropper:{has_usertype}"
    )
except Exception as e:
    check("profile_md_content", False, f"profile.md missing or unreadable: {e}")

# ══════════════════════════════════════════════════════════════════════════
# CHECK 3: Mock exam analysis file exists in ~/neet/mocks/
# ══════════════════════════════════════════════════════════════════════════
mock_files = list((neet_dir / "mocks").glob("*")) if (neet_dir / "mocks").is_dir() else []
check(
    "mock_analysis_file_exists",
    len(mock_files) >= 1,
    f"Found {len(mock_files)} file(s) in ~/neet/mocks/" if mock_files else "No files in ~/neet/mocks/"
)

# ══════════════════════════════════════════════════════════════════════════
# CHECK 4: Correct NEET score calculation (+4 correct, -1 wrong, 0 unattempted)
# Physics: 45 questions
#   correct: Q01,Q03,Q05,Q07,Q09,Q11,Q12,Q14,Q16,Q18,Q19,Q21,Q24,Q25,Q27,Q28,Q31,Q33,Q34,Q36,Q38,Q40,Q41,Q43,Q45 = 25
#   wrong:   Q02,Q06,Q08,Q13,Q17,Q20,Q23,Q26,Q29,Q32,Q35,Q39,Q42 = 13
#   unatt:   Q04,Q10,Q15,Q22,Q30,Q37,Q44 = 7
#   Physics score = 25*4 - 13*1 = 100 - 13 = 87
#
# Chemistry: 45 questions
#   correct: Q46,Q47,Q49,Q51,Q53,Q54,Q56,Q58,Q59,Q61,Q62,Q65,Q66,Q68,Q69,Q72,Q73,Q75,Q76,Q79,Q80,Q82,Q83,Q86,Q87,Q89,Q90 = 27
#   wrong:   Q48,Q52,Q55,Q60,Q63,Q67,Q70,Q74,Q77,Q81,Q84,Q88 = 12
#   unatt:   Q50,Q57,Q64,Q71,Q78,Q85 = 6
#   Chemistry score = 27*4 - 12*1 = 108 - 12 = 96
#
# Biology: 90 questions
#   Let's count carefully:
#   correct: Q91,Q92,Q94,Q95,Q98,Q99,Q101,Q102,Q105,Q106,Q108,Q109,Q112,Q113,Q115,Q116,Q119,Q120,Q122,Q123,Q126,Q127,Q129,Q130,Q133,Q134,Q136,Q137,Q140,Q141,Q143,Q144,Q147,Q148,Q150,Q151,Q154,Q155,Q157,Q158,Q161,Q162,Q164,Q165,Q168,Q169,Q171,Q172,Q175,Q176,Q178,Q179 = 52
#   wrong:   Q93,Q96,Q100,Q103,Q107,Q110,Q114,Q117,Q121,Q124,Q128,Q131,Q135,Q138,Q142,Q145,Q149,Q152,Q156,Q159,Q163,Q166,Q170,Q173,Q177,Q180 = 26
#   unatt:   Q97,Q104,Q111,Q118,Q125,Q132,Q139,Q146,Q153,Q160,Q167,Q174 = 12
#   Biology score = 52*4 - 26*1 = 208 - 26 = 182
#
# TOTAL = 87 + 96 + 182 = 365
# ══════════════════════════════════════════════════════════════════════════
EXPECTED_PHYSICS = 87
EXPECTED_CHEM = 96
EXPECTED_BIO = 182
EXPECTED_TOTAL = 365

mock_text = ""
if mock_files:
    try:
        mock_text = mock_files[0].read_text(errors="replace")
        # also try to find a specifically named file
        for mf in mock_files:
            t = mf.read_text(errors="replace")
            if str(EXPECTED_TOTAL) in t:
                mock_text = t
                break
    except Exception:
        pass

# Search all mock files combined
all_mock_text = ""
for mf in mock_files:
    try:
        all_mock_text += mf.read_text(errors="replace") + "\n"
    except Exception:
        pass

total_score_found = str(EXPECTED_TOTAL) in all_mock_text
check(
    "correct_total_neet_score",
    total_score_found,
    f"Expected total score {EXPECTED_TOTAL} {'found' if total_score_found else 'NOT found'} in mock analysis files"
)

# Check individual subject scores
phy_found = str(EXPECTED_PHYSICS) in all_mock_text
chem_found = str(EXPECTED_CHEM) in all_mock_text
bio_found = str(EXPECTED_BIO) in all_mock_text
check(
    "subject_scores_correct",
    phy_found and chem_found and bio_found,
    f"Physics={EXPECTED_PHYSICS}({'✓' if phy_found else '✗'}), Chem={EXPECTED_CHEM}({'✓' if chem_found else '✗'}), Bio={EXPECTED_BIO}({'✓' if bio_found else '✗'})"
)

# ══════════════════════════════════════════════════════════════════════════
# CHECK 5: Negative marking explicitly applied (not just ignored)
# ══════════════════════════════════════════════════════════════════════════
neg_mark_mentioned = bool(re.search(r'(-1|negative\s*mark|penalt)', all_mock_text, re.IGNORECASE))
check(
    "negative_marking_applied",
    neg_mark_mentioned,
    "Negative marking (-1) referenced in analysis" if neg_mark_mentioned else "No mention of negative marking found"
)

# ══════════════════════════════════════════════════════════════════════════
# CHECK 6: Weak area identification (ROI-based, not just lowest score)
# ══════════════════════════════════════════════════════════════════════════
# Weakest chapters by error rate:
# Physics: Thermodynamics (3 wrong/3), Ray Optics (3/3), Laws of Motion (3/3), Electrostatics (3/4), Waves (1/1)
# Worst ROI = most errors per hour: Thermodynamics 3 errors / 4.5h = 0.67/h, Ray Optics 3/3.0 = 1.0/h
# ROI-first means prioritize chapters where fixing errors yields most marks/hour
# Agent should mention ROI or marks-per-hour or similar concept

subj_files = list((neet_dir / "subjects").glob("*")) if (neet_dir / "subjects").is_dir() else []
all_subj_text = ""
for sf in subj_files:
    try:
        all_subj_text += sf.read_text(errors="replace") + "\n"
    except Exception:
        pass

# Also check mock files for weak area analysis
combined_analysis = all_mock_text + all_subj_text

weak_area_mentioned = bool(re.search(
    r'(weak\s*area|thermodynamics|ray\s*optics|haloalkane|electrostatic|chemical\s*bonding|genetics)',
    combined_analysis, re.IGNORECASE
))
roi_mentioned = bool(re.search(
    r'(roi|return.on.invest|marks.per.hour|high.priority|priority|focus)',
    combined_analysis, re.IGNORECASE
))
check(
    "weak_area_identification",
    weak_area_mentioned,
    "Weak chapters identified in subjects/ or mocks/ analysis" if weak_area_mentioned else "No weak area content found"
)
check(
    "roi_first_prioritization",
    roi_mentioned,
    "ROI/priority language found in analysis" if roi_mentioned else "No ROI-first prioritization language found"
)

# ══════════════════════════════════════════════════════════════════════════
# CHECK 7: College targeting with OBC category
# ══════════════════════════════════════════════════════════════════════════
targets_path = neet_dir / "profile.md"
# College targeting might be in profile.md or a separate file
all_target_text = ""
for f in neet_dir.rglob("*"):
    if f.is_file():
        try:
            all_target_text += f.read_text(errors="replace") + "\n"
        except Exception:
            pass

aiims_mentioned = bool(re.search(r'aiims', all_target_text, re.IGNORECASE))
obc_cutoff = bool(re.search(r'obc', all_target_text, re.IGNORECASE))
college_targeted = bool(re.search(
    r'(aiims|government\s*medical|gmc|sms\s*medical|jaipur|rajasthan|cutoff|cut.off|seat)',
    all_target_text, re.IGNORECASE
))
check(
    "college_targeting_with_category",
    aiims_mentioned and obc_cutoff,
    f"AIIMS mentioned: {aiims_mentioned}, OBC category used: {obc_cutoff}"
)
check(
    "target_colleges_referenced",
    college_targeted,
    "Target colleges (AIIMS/GMC/SMS/Jaipur/Rajasthan) found in neet data" if college_targeted else "No target college references found"
)

# ══════════════════════════════════════════════════════════════════════════
# CHECK 8: Session log created in ~/neet/sessions/
# ══════════════════════════════════════════════════════════════════════════
session_files = list((neet_dir / "sessions").glob("*")) if (neet_dir / "sessions").is_dir() else []
check(
    "session_log_created",
    len(session_files) >= 1,
    f"Found {len(session_files)} session log(s) in ~/neet/sessions/" if session_files else "No session logs found"
)

# ══════════════════════════════════════════════════════════════════════════
# FINAL SCORING
# ══════════════════════════════════════════════════════════════════════════
passed_checks = sum(1 for c in checks if c["passed"])
total_checks = len(checks)
score = round(passed_checks / total_checks, 4)
overall_pass = (
    checks[0]["passed"] and   # directory structure
    checks[2]["passed"] and   # mock file exists
    checks[3]["passed"] and   # correct total score
    checks[4]["passed"] and   # subject scores correct
    checks[5]["passed"]       # negative marking applied
)

result = {
    "passed": overall_pass,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))