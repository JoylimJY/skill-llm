import os
import random

random.seed(42)

base = "/workspace"

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "references",
    "student_records",
    "admin/old_drafts",
    "admin/school_memos",
    "admin/timetable_templates",
    "planning_notes",
    "university_info/waterloo",
    "university_info/mcmaster",
    "university_info/uoft",
    "misc",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# ── REFERENCE FILE 1: graduation-and-planning-rules.md ───────────────────────
grad_rules = """\
# Ontario OSSD Graduation & Planning Rules

## Credit Requirements
- Total credits required: 30
  - Compulsory credits: 17
  - Elective credits: 13
- Community involvement hours: 40
- Ontario Secondary School Literacy Test (OSSLT): must be passed (or OSSLC completed)
- Online learning requirement: minimum **2** credits must be earned via online (e-learning) courses

## Compulsory Credit Breakdown (17 total)
| Subject Area | Credits Required |
|---|---|
| English (1 per grade, Grades 9–12) | 4 |
| Mathematics (1 in Grade 11 or 12) | 3 |
| Science | 2 |
| Canadian History (Grade 10) | 1 |
| Canadian Geography (Grade 9) | 1 |
| Arts | 1 |
| Health & Physical Education | 1 |
| French as a Second Language | 1 |
| Career Studies (0.5) | 0.5 |
| Civics (0.5) | 0.5 |
| Any 1 additional from: English, FSL, Native Language, Classical or Intl Language, Social Sciences, Canadian & World Studies, Guidance, Cooperative Ed | 1 |
| Any 1 additional from: Health & PE, The Arts, Business Studies, CS&T | 1 |

## Yearly Course Load
- Standard: **8 courses per year** (2 semesters × 4 courses each)
- 7-course years are **not permitted** at this school
- Grade 9: must include Geography (CGC1D), English (ENL1W or ENG1D), Math (MTH1W), Science (SNC1W)
- Grade 10: must include History (CHC2D), English (ENG2D), Math (MPM2D or MFM2P), Science (SNC2D or SNC2P)

## Spares
- Spares (free periods) are allowed only in **Grade 12**, maximum **1 spare per semester**
- No spares in Grades 9, 10, or 11

## Cross-Grade Enrolment
- Students may take a Grade 12 (4U/4M) course in Grade 11 if they have the prerequisite and written teacher approval
- Maximum **1 cross-grade course** per year

## Summer School
- Refer to `summer-school-catalog.md` for allowed offerings
- Maximum **1 course per summer** (per calendar year)
- Summer courses taken between Grade 10→11 count toward Grade 11 year
- Summer courses taken between Grade 11→12 count toward Grade 12 year

## Online (e-Learning) Requirement
- At least 2 of the 30 credits must be completed as online/e-learning courses
- Online courses are tagged [ONLINE] in the course catalog
- A course taken via summer school in an online format counts if tagged [ONLINE] in the summer catalog

## Minimum Grades for Advancement
- No formal minimum average required for promotion under OSSD
- University-stream (U/M) courses recommended for university-bound students
"""

with open(os.path.join(base, "references/graduation-and-planning-rules.md"), "w") as f:
    f.write(grad_rules)

# ── REFERENCE FILE 2: course-catalog.md ─────────────────────────────────────
course_catalog = """\
# School Course Catalog (Current Year)

## Legend
- Type: D=Destination | P=Applied | U=Academic/University | M=University/College | O=Open | W=Workplace
- [ONLINE] = available as e-learning section
- [PREREQ: code] = prerequisite course code

---

## Grade 9 Courses

| Code | Name | Type | Compulsory Area | Credits |
|---|---|---|---|---|
| ENG1D | English, Grade 9 | U | English | 1 |
| ENL1W | English, Grade 9 (Locally Developed) | O | English | 1 |
| MTH1W | Mathematics, Grade 9 | U | Mathematics | 1 |
| SNC1W | Science, Grade 9 | U | Science | 1 |
| CGC1D | Canadian Geography | U | Geography | 1 |
| FSF1D | Core French, Grade 9 | U | FSL | 1 |
| PPL1O | Health & PE, Grade 9 | O | HPE | 1 |
| AVI1O | Visual Arts, Grade 9 | O | Arts | 1 |
| AMU1O | Music, Grade 9 | O | Arts | 1 |
| TTJ1O | Technological Design, Grade 9 | O | CS&T | 1 |
| ICS2O | Introduction to Computer Studies, Grade 10 | O | CS&T | 1 |
| TGJ2O | Communications Technology, Grade 10 | O | CS&T | 1 |

## Grade 10 Courses

| Code | Name | Type | Compulsory Area | Credits |
|---|---|---|---|---|
| ENG2D | English, Grade 10 | U | English | 1 |
| MPM2D | Principles of Mathematics, Grade 10 | U | Mathematics | 1 |
| MFM2P | Foundations of Mathematics, Grade 10 | P | Mathematics | 1 |
| SNC2D | Science, Grade 10 | U | Science | 1 |
| SNC2P | Science, Grade 10 Applied | P | Science | 1 |
| CHC2D | Canadian History since WWI | U | History | 1 |
| FSF2D | Core French, Grade 10 [PREREQ: FSF1D] | U | FSL | 1 |
| PPL2O | Health & PE, Grade 10 | O | HPE | 1 |
| AVI2O | Visual Arts, Grade 10 | O | Arts | 1 |
| AMU2O | Music, Grade 10 | O | Arts | 1 |
| ICS2O | Introduction to Computer Studies, Grade 10 | O | CS&T | 1 |
| TGJ2O | Communications Technology, Grade 10 | O | CS&T | 1 |
| GLC2O | Career Studies | O | Compulsory-0.5 | 0.5 |
| CHV2O | Civics and Citizenship | O | Compulsory-0.5 | 0.5 |

## Grade 11 Courses

| Code | Name | Type | Compulsory Area | Credits |
|---|---|---|---|---|
| ENG3U | English, Grade 11 [PREREQ: ENG2D] | U | English | 1 |
| MCR3U | Functions, Grade 11 [PREREQ: MPM2D] | U | Mathematics | 1 |
| MCF3M | Functions & Applications [PREREQ: MPM2D or MFM2P] | M | Mathematics | 1 |
| SCH3U | Chemistry, Grade 11 [PREREQ: SNC2D] | U | Science | 1 |
| SPH3U | Physics, Grade 11 [PREREQ: SNC2D] | U | Science | 1 |
| SBI3U | Biology, Grade 11 [PREREQ: SNC2D] | U | Science | 1 |
| ICS3U | Introduction to Computer Science, Grade 11 [PREREQ: ICS2O] [ONLINE] | U | CS&T | 1 |
| FSF3U | Core French, Grade 11 [PREREQ: FSF2D] | U | FSL | 1 |
| PPL3O | Health & PE, Grade 11 | O | HPE | 1 |
| AVI3M | Visual Arts, Grade 11 | M | Arts | 1 |
| AMU3M | Music, Grade 11 | M | Arts | 1 |
| BAF3M | Financial Accounting Fundamentals | M | Business | 1 |
| HSP3U | Introduction to Anthropology, Psychology, Sociology | U | Social Sciences | 1 |

## Grade 12 Courses

| Code | Name | Type | Compulsory Area | Credits |
|---|---|---|---|---|
| ENG4U | English, Grade 12 [PREREQ: ENG3U] | U | English | 1 |
| MHF4U | Advanced Functions [PREREQ: MCR3U] | U | Mathematics | 1 |
| MCV4U | Calculus & Vectors [PREREQ: MCR3U or concurrent MHF4U] | U | Mathematics | 1 |
| MDM4U | Mathematics of Data Management [PREREQ: MCR3U or MCF3M] | U | Mathematics | 1 |
| SCH4U | Chemistry, Grade 12 [PREREQ: SCH3U] | U | Science | 1 |
| SPH4U | Physics, Grade 12 [PREREQ: SPH3U] | U | Science | 1 |
| SBI4U | Biology, Grade 12 [PREREQ: SBI3U] | U | Science | 1 |
| ICS4U | Computer Science, Grade 12 [PREREQ: ICS3U] | U | CS&T | 1 |
| FSF4U | Core French, Grade 12 [PREREQ: FSF3U] | U | FSL | 1 |
| PPL4O | Health & PE, Grade 12 | O | HPE | 1 |
| AVI4M | Visual Arts, Grade 12 | M | Arts | 1 |
| AMU4M | Music, Grade 12 | M | Arts | 1 |
| BAT4M | Accounting, Grade 12 [PREREQ: BAF3M] | M | Business | 1 |
| HSB4U | Challenge & Change in Society [PREREQ: HSP3U] | U | Social Sciences | 1 |
| BOH4M | Business Leadership | M | Business | 1 |
| CGW4U | World Issues: A Geographic Analysis | U | Canadian & World Studies | 1 |
| EWC4U | The Writer's Craft [PREREQ: ENG3U] [ONLINE] | U | English | 1 |

## Notes
- ICS3U is the **only** Grade 11 CS&T U-level course offered at this school
- MCV4U may be taken concurrently with MHF4U in Grade 12 (same semester allowed if timetable permits)
- EWC4U (online) can substitute for a second Grade 12 English elective
- Cross-grade: Grade 11 students may take MHF4U with teacher approval if MCR3U is complete
"""

with open(os.path.join(base, "references/course-catalog.md"), "w") as f:
    f.write(course_catalog)

# ── REFERENCE FILE 3: required-bands-by-grade.md ────────────────────────────
bands = """\
# Required Course Bands by Grade

## Grade 9 Required Courses (must all appear in Grade 9 plan)
- ENG1D (or ENL1W)
- MTH1W
- SNC1W
- CGC1D
- FSF1D (recommended; required if school offers and student has no FSL exemption)
- PPL1O (required for HPE compulsory credit)

## Grade 10 Required Courses (must all appear in Grade 10 plan)
- ENG2D
- MPM2D (for university-bound students)
- SNC2D (for university-bound students)
- CHC2D
- GLC2O (Career Studies, 0.5 credit)
- CHV2O (Civics, 0.5 credit)

## Grade 11 Required Courses (university-bound)
- ENG3U [PREREQ: ENG2D]
- MCR3U [PREREQ: MPM2D] — required for 4U Math pathway

## Grade 12 Required for University Admission (OSSD)
- ENG4U [PREREQ: ENG3U] — required by virtually all Ontario universities

## Top 6 Notes
- "Top 6" = the six highest Grade 12 U or M (12U/M) course final grades used by universities to compute admissions average
- Only courses at the 4U or 4M level qualify
- If a student has > 6 such courses, the 6 highest are used
- Summer school 4U/M courses taken between Grade 11 and Grade 12 can count toward Top 6 **only if the university accepts them** — verify per institution
- EWC4U is accepted in Top 6 by most Ontario universities as an elective
"""

with open(os.path.join(base, "references/required-bands-by-grade.md"), "w") as f:
    f.write(bands)

# ── REFERENCE FILE 4: summer-school-catalog.md ──────────────────────────────
summer_catalog = """\
# Summer School Catalog

## Rules
- Maximum 1 course per summer session
- Summer school is offered between school years only (not mid-semester)
- Courses listed below are the ONLY courses available via summer school at this school
- No Grade 12 U-level (4U) or M-level (4M) courses are available via summer school at this school
- Online summer sections are tagged [ONLINE]

## Available Summer Courses

| Code | Name | Type | Grade Level | Credits | Online? |
|---|---|---|---|---|---|
| CHV2O | Civics and Citizenship | O | 10 | 0.5 | [ONLINE] |
| GLC2O | Career Studies | O | 10 | 0.5 | [ONLINE] |
| PPL2O | Health & PE, Grade 10 | O | 10 | 1 | No |
| FSF1D | Core French, Grade 9 | U | 9 | 1 | No |
| TTJ1O | Technological Design, Grade 9 | O | 9 | 1 | No |
| ICS2O | Introduction to Computer Studies, Grade 10 | O | 10 | 1 | No |
| AVI2O | Visual Arts, Grade 10 | O | 10 | 1 | No |

## Notes
- CHV2O and GLC2O via summer school count as [ONLINE] and satisfy the online learning requirement
- No exemptions: 4U/4M courses cannot be added to the summer catalog without a policy change memo from administration
- If a student needs a 4U course early, they must use the cross-grade enrolment policy (in-school, with teacher approval)
"""

with open(os.path.join(base, "references/summer-school-catalog.md"), "w") as f:
    f.write(summer_catalog)

# ── STUDENT RECORD (partially complete — entering Grade 11) ──────────────────
student_record = """\
# Student Record — Alex Chen

## Personal Info
- Current Grade: Entering Grade 11 (fall semester upcoming)
- Special Programs: None
- Community Hours Completed: 15 / 40

## Completed Courses (Grade 9)
| Code | Name | Grade | Final Mark |
|---|---|---|---|
| ENG1D | English, Grade 9 | 9 | 82 |
| MTH1W | Mathematics, Grade 9 | 9 | 88 |
| SNC1W | Science, Grade 9 | 9 | 85 |
| CGC1D | Canadian Geography | 9 | 79 |
| FSF1D | Core French, Grade 9 | 9 | 74 |
| PPL1O | Health & PE, Grade 9 | 9 | 91 |
| AVI1O | Visual Arts, Grade 9 | 9 | 88 |
| TTJ1O | Technological Design, Grade 9 | 9 | 83 |

## Completed Courses (Grade 10)
| Code | Name | Grade | Final Mark |
|---|---|---|---|
| ENG2D | English, Grade 10 | 10 | 84 |
| MPM2D | Principles of Mathematics, Grade 10 | 10 | 90 |
| SNC2D | Science, Grade 10 | 10 | 86 |
| CHC2D | Canadian History since WWI | 10 | 81 |
| FSF2D | Core French, Grade 10 | 10 | 76 |
| PPL2O | Health & PE, Grade 10 | 10 | 88 |
| ICS2O | Introduction to Computer Studies | 10 | 92 |
| TGJ2O | Communications Technology | 10 | 80 |

## Summer (between Grade 10 and 11)
| Code | Name | Notes |
|---|---|---|
| CHV2O | Civics and Citizenship | Completed online [ONLINE], 0.5 credit |
| GLC2O | Career Studies | Completed online [ONLINE], 0.5 credit |

## Credits Accumulated
- Total: 17
- Compulsory: 12.5  (missing: 1 Arts [need 4M/higher or another Arts], 1 Math-Gr11-or-12, 1 English Gr11, 1 English Gr12, 0.5 remaining compulsory slot from elective groups)
- Elective: 4.5
- Online: 1 (CHV2O) + 1 (GLC2O) = 2 online credits ALREADY MET

## Targets
1. University of Waterloo — Computer Science (co-op)
2. McMaster University — Engineering (likely Electrical or Computer Engineering)

## Priorities
- pressureFocus: protect_11_12
- summerSchool.enabled: true
- summerSchool.maxPerYear: 1
- summerSchool.useFor: nonTop6
- maximizeAverage: true
- preferEasierElectives: true
- planRobustness: normal
"""

with open(os.path.join(base, "student_records/alex_chen_transcript.md"), "w") as f:
    f.write(student_record)

# ── DISTRACTOR FILES ─────────────────────────────────────────────────────────

# Old draft plan (wrong/outdated)
old_draft = """\
# OLD DRAFT PLAN v0.1 — DO NOT USE
## Grade 11 (tentative)
- ENG3U
- MCR3U
- SCH3U
- SPH3U
- ICS3U (NOTE: may be removed from catalog — CHECK)
- SBI3U
- FSF3U
- BAF3M

## Grade 12 (tentative)
- ENG4U, MHF4U, MCV4U, SCH4U, SPH4U, ICS4U, MHF4U (duplicate error!)
- ??? still 2 more slots needed

Notes: forgot Civics and Careers! Also summer school not planned.
This draft ignores protect_11_12 mode entirely.
"""
with open(os.path.join(base, "admin/old_drafts/plan_v0.1_DRAFT.md"), "w") as f:
    f.write(old_draft)

# School memo about a catalog change
catalog_memo = """\
# Memo — School Administration
Date: August 15, 2024
To: Guidance Counselors
Re: 2024-2025 Course Catalog Update

Effective immediately:
1. ICS3U (Introduction to Computer Science, Grade 11) has been REMOVED from the in-school timetable for the upcoming school year.
   - Students who have already registered for ICS3U should be advised to take it via the e-learning (online) section, which remains available.
   - The online section of ICS3U retains the [ONLINE] tag and counts toward the online credit requirement.
   - ICS3U online is ONLY available as a full-year online course (not semestered).

2. A new elective, TTJ2O (Technological Design, Grade 10), is added to the Grade 10 catalog. 
   Note: This was previously labeled TTJ1O in Grade 10 context — the correct code going forward is TTJ2O for Grade 10.

This memo must be reflected in the course catalog before any new plans are finalized.
"""
with open(os.path.join(base, "admin/school_memos/catalog_update_aug2024.md"), "w") as f:
    f.write(catalog_memo)

# Waterloo CS admission info (distractor — intentionally vague/incomplete)
waterloo_info = """\
# Waterloo CS Admissions — Unofficial Notes (may be outdated)

Typical prerequisites mentioned on forums:
- Advanced Functions (4U)
- Calculus & Vectors (4U) — sometimes listed as "recommended"
- English (4U)
- Grade 12 average in the low 90s for co-op

Top 6: Usually MHF4U, MCV4U, ENG4U + 3 others
Some say SCH4U helps, others say ICS4U is preferred.

NOTE: Always verify at uwaterloo.ca — this doc was last updated 2022.
"""
with open(os.path.join(base, "university_info/waterloo/cs_admissions_notes.md"), "w") as f:
    f.write(waterloo_info)

# McMaster Engineering info (distractor)
mcmaster_info = """\
# McMaster Engineering Admissions — Rough Notes

Hard prerequisites (from their site ~2023):
- ENG4U
- MHF4U or MCV4U (at least one)
- SCH4U or SPH4U (at least one science)
- Two more 4U/M courses for Top 6

Competitive average: mid-high 80s.
"""
with open(os.path.join(base, "university_info/mcmaster/eng_notes.md"), "w") as f:
    f.write(mcmaster_info)

# Timetable template (irrelevant distractor)
timetable = """\
# Timetable Template 2024-2025
Semester 1: Sep – Jan
Semester 2: Feb – Jun
Period 1: 8:30–9:45
Period 2: 9:50–11:05
Lunch: 11:05–11:50
Period 3: 11:50–13:05
Period 4: 13:10–14:25
"""
with open(os.path.join(base, "admin/timetable_templates/2024-25-bell-schedule.md"), "w") as f:
    f.write(timetable)

# Misc planning notes (noise)
for i, note in enumerate([
    "Talked to guidance — said Alex can take MHF4U early if MCR3U done by end of Grade 11.",
    "Remember: online courses count for e-learning requirement. Alex already has 2 from summer.",
    "ICS4U prereq is ICS3U. If ICS3U goes online-only, still same prereq chain.",
    "Waterloo AIF form due Feb 1. Start thinking about extracurriculars.",
], start=1):
    with open(os.path.join(base, f"planning_notes/note_{i:02d}.txt"), "w") as f:
        f.write(note + "\n")

# Misc distractors
with open(os.path.join(base, "misc/ossd_overview_2019.txt"), "w") as f:
    f.write("OSSD overview from 2019 — may be outdated. 30 credits required, 40 community hours, literacy requirement.\n")

with open(os.path.join(base, "misc/university_application_checklist.txt"), "w") as f:
    f.write("OUAC application deadline: Jan 15\nFinal transcripts: Jun\nAIF: varies by school\n")

with open(os.path.join(base, "university_info/uoft/cs_general.txt"), "w") as f:
    f.write("UofT CS is very competitive. Top 6 usually requires all heavy 4U. Not a target for Alex currently.\n")

with open(os.path.join(base, "student_records/community_hours_log.txt"), "w") as f:
    f.write("Volunteer hours: 15 hrs at local library (summer 2023). Need 25 more.\n")

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(base):
    for fn in files:
        print(" ", os.path.join(root, fn).replace(base, ""))