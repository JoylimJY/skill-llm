import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── distractor directory tree (10+ files) ──────────────────────────────────
distractor_dirs = [
    workspace / "notes" / "biology",
    workspace / "notes" / "physics",
    workspace / "notes" / "chemistry",
    workspace / "old_results",
    workspace / "schedule_drafts",
    workspace / "resources" / "ncert_summaries",
    workspace / "resources" / "previous_years",
    workspace / "misc",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractors = {
    workspace / "notes" / "biology" / "cell_biology.txt": "Chapter notes on cell biology - mitosis, meiosis, cell cycle.",
    workspace / "notes" / "biology" / "genetics_raw.txt": "Mendel's laws, incomplete dominance, codominance notes (unformatted).",
    workspace / "notes" / "physics" / "optics_draft.txt": "Ray optics formulas - mirror formula, lens formula etc.",
    workspace / "notes" / "chemistry" / "organic_reactions.txt": "SN1, SN2, E1, E2 reactions. Addition, elimination, substitution.",
    workspace / "old_results" / "2023_attempt.txt": "Score: 480/720. Did not qualify.",
    workspace / "old_results" / "coaching_test_march.txt": "Coaching mock #3: 390 marks. Weak in Thermodynamics.",
    workspace / "schedule_drafts" / "week1_plan.txt": "Monday: Physics 3h, Bio 2h. Tuesday: Chem 3h.",
    workspace / "resources" / "ncert_summaries" / "bio_class12_ch1.txt": "Reproduction in Organisms summary.",
    workspace / "resources" / "previous_years" / "neet2022_paper.txt": "NEET 2022 paper key: [placeholder keys only]",
    workspace / "resources" / "ncert_summaries" / "chem_class11_ch1.txt": "Some basic concepts of chemistry summary.",
    workspace / "misc" / "todo.txt": "Buy stationery. Print admit card. Register on NTA portal.",
    workspace / "misc" / "motivation.txt": "You can do this! Keep going.",
}
for path, content in distractors.items():
    path.write_text(content)

# ── The actual raw input the agent must process ────────────────────────────
# Student context file — messy, unstructured, not in the ~/neet/ format
student_context = workspace / "student_info.txt"
student_context.write_text("""\
Student Name: Priya Sharma
Exam Date: 2025-05-04
Category: OBC
State Domicile: Rajasthan
Target Colleges: AIIMS Jodhpur, AIIMS Jodhpur (state quota), Government Medical College Jaipur, SMS Medical College
Current self-estimate: 560-590 range
User type: dropper (second attempt)
Days already studied this cycle: 210

Target score: 620+
""")

# Raw mock exam attempt — messy CSV-like format, not yet analyzed
mock_exam_raw = workspace / "mock_exam_attempt.txt"
mock_exam_raw.write_text("""\
Mock Exam #7  |  Date: 2025-03-15
Format: 180 questions, 4 marks each correct, unattempted = 0

PHYSICS (45 questions)
Q01: correct
Q02: wrong
Q03: correct
Q04: unattempted
Q05: correct
Q06: wrong
Q07: correct
Q08: wrong
Q09: correct
Q10: unattempted
Q11: correct
Q12: correct
Q13: wrong
Q14: correct
Q15: unattempted
Q16: correct
Q17: wrong
Q18: correct
Q19: correct
Q20: wrong
Q21: correct
Q22: unattempted
Q23: wrong
Q24: correct
Q25: correct
Q26: wrong
Q27: correct
Q28: correct
Q29: wrong
Q30: unattempted
Q31: correct
Q32: wrong
Q33: correct
Q34: correct
Q35: wrong
Q36: correct
Q37: unattempted
Q38: correct
Q39: wrong
Q40: correct
Q41: correct
Q42: wrong
Q43: correct
Q44: unattempted
Q45: correct

Physics chapter mapping (for weak area analysis):
Q02,Q06,Q08: Thermodynamics
Q13,Q17,Q20: Ray Optics
Q23,Q26,Q29: Laws of Motion
Q32,Q35,Q39: Electrostatics
Q42: Waves

CHEMISTRY (45 questions)
Q46: correct
Q47: correct
Q48: wrong
Q49: correct
Q50: unattempted
Q51: correct
Q52: wrong
Q53: correct
Q54: correct
Q55: wrong
Q56: correct
Q57: unattempted
Q58: correct
Q59: correct
Q60: wrong
Q61: correct
Q62: correct
Q63: wrong
Q64: unattempted
Q65: correct
Q66: correct
Q67: wrong
Q68: correct
Q69: correct
Q70: wrong
Q71: unattempted
Q72: correct
Q73: correct
Q74: wrong
Q75: correct
Q76: correct
Q77: wrong
Q78: unattempted
Q79: correct
Q80: correct
Q81: wrong
Q82: correct
Q83: correct
Q84: wrong
Q85: unattempted
Q86: correct
Q87: correct
Q88: wrong
Q89: correct
Q90: correct

Chemistry chapter mapping (for weak area analysis):
Q48,Q52,Q55: Organic Chemistry - Haloalkanes
Q60,Q63,Q67: Chemical Bonding
Q70,Q74,Q77: Equilibrium
Q81,Q84,Q88: Electrochemistry

BIOLOGY (90 questions — counts double weight in NEET)
Q91: correct
Q92: correct
Q93: wrong
Q94: correct
Q95: correct
Q96: wrong
Q97: unattempted
Q98: correct
Q99: correct
Q100: wrong
Q101: correct
Q102: correct
Q103: wrong
Q104: unattempted
Q105: correct
Q106: correct
Q107: wrong
Q108: correct
Q109: correct
Q110: wrong
Q111: unattempted
Q112: correct
Q113: correct
Q114: wrong
Q115: correct
Q116: correct
Q117: wrong
Q118: unattempted
Q119: correct
Q120: correct
Q121: wrong
Q122: correct
Q123: correct
Q124: wrong
Q125: unattempted
Q126: correct
Q127: correct
Q128: wrong
Q129: correct
Q130: correct
Q131: wrong
Q132: unattempted
Q133: correct
Q134: correct
Q135: wrong
Q136: correct
Q137: correct
Q138: wrong
Q139: unattempted
Q140: correct
Q141: correct
Q142: wrong
Q143: correct
Q144: correct
Q145: wrong
Q146: unattempted
Q147: correct
Q148: correct
Q149: wrong
Q150: correct
Q151: correct
Q152: wrong
Q153: unattempted
Q154: correct
Q155: correct
Q156: wrong
Q157: correct
Q158: correct
Q159: wrong
Q160: unattempted
Q161: correct
Q162: correct
Q163: wrong
Q164: correct
Q165: correct
Q166: wrong
Q167: unattempted
Q168: correct
Q169: correct
Q170: wrong
Q171: correct
Q172: correct
Q173: wrong
Q174: unattempted
Q175: correct
Q176: correct
Q177: wrong
Q178: correct
Q179: correct
Q180: wrong

Biology chapter mapping (for weak area analysis):
Q93,Q96,Q100: Genetics - Mendelian
Q103,Q107,Q110: Human Reproduction
Q114,Q117,Q121: Plant Physiology
Q124,Q128,Q131: Ecology
Q135,Q138,Q142: Evolution
Q145,Q149,Q152: Molecular Biology
Q156,Q159,Q163: Biotechnology
Q166,Q170,Q173: Animal Kingdom
Q177,Q180: Cell Biology
""")

# Per-subject time-spent data (raw, unprocessed)
time_data = workspace / "study_time_log.txt"
time_data.write_text("""\
Subject time invested (hours) - last 30 days:
Physics: 42 hours
Chemistry: 38 hours
Biology: 55 hours

Chapter-level time (hours):
Thermodynamics: 4.5
Ray Optics: 3.0
Laws of Motion: 5.0
Electrostatics: 4.0
Waves: 2.5
Haloalkanes: 3.5
Chemical Bonding: 4.0
Equilibrium: 4.5
Electrochemistry: 3.0
Genetics - Mendelian: 6.0
Human Reproduction: 4.0
Plant Physiology: 5.5
Ecology: 4.0
Evolution: 3.5
Molecular Biology: 5.0
Biotechnology: 4.5
Animal Kingdom: 3.0
Cell Biology: 2.0
""")

print("Workspace generated successfully.")
print(f"Files created: {len(list(workspace.rglob('*')))} total entries")