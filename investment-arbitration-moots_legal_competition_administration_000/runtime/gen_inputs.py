#!/usr/bin/env python3
"""
Generate the sandbox workspace for the investment arbitration moot coordinator task.
"""
import json
import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = "/workspace"

# ── directory skeleton ─────────────────────────────────────────────────────────
dirs = [
    "competition_admin/registrations",
    "competition_admin/scores",
    "competition_admin/correspondence",
    "competition_admin/templates",
    "legal_resources/treaties",
    "legal_resources/case_law",
    "internal_docs/past_years/2023",
    "internal_docs/past_years/2024",
    "internal_docs/guidelines",
    "scratch",
]
for d in dirs:
    Path(os.path.join(WORKSPACE, d)).mkdir(parents=True, exist_ok=True)

# ── distractor files ───────────────────────────────────────────────────────────
distractors = {
    "competition_admin/templates/welcome_email_draft.txt": (
        "Dear Team,\nWelcome to the 2025 season. Please read the rules carefully.\n"
        "Contact us at moot@example.org for questions.\n"
    ),
    "competition_admin/correspondence/inquiry_pku.txt": (
        "Received inquiry from Peking University regarding hotel arrangements.\n"
        "Replied on 2025-02-10.\n"
    ),
    "competition_admin/correspondence/inquiry_fudan.txt": (
        "Fudan University asked about LLM student eligibility.\n"
        "Standard reply sent.\n"
    ),
    "legal_resources/treaties/icsid_convention_excerpt.txt": (
        "Article 25: The jurisdiction of the Centre shall extend to any legal dispute "
        "arising directly out of an investment, between a Contracting State...\n"
    ),
    "legal_resources/treaties/energy_charter_treaty_note.txt": (
        "ECT entered into force: April 1998. Covers energy investments.\n"
    ),
    "legal_resources/case_law/salini_v_morocco.txt": (
        "Salini Costruttori S.p.A. v. Kingdom of Morocco (ICSID Case No. ARB/00/4)\n"
        "Key issue: definition of 'investment' under Article 25 of the ICSID Convention.\n"
    ),
    "internal_docs/past_years/2023/results_summary.txt": (
        "2023 Shenzhen Cup Results:\n"
        "Champion: Wuhan University\nRunner-up: CUPL\n"
    ),
    "internal_docs/past_years/2024/results_summary.txt": (
        "2024 Shenzhen Cup Results:\n"
        "Champion: Renmin University\nRunner-up: Tsinghua University\n"
    ),
    "internal_docs/guidelines/skeleton_brief_notes.txt": (
        "Reminder: skeleton arguments must be submitted before the deadline.\n"
        "Language: English only.\n"
    ),
    "internal_docs/guidelines/arbitrator_conduct.txt": (
        "Arbitrators must disclose any conflicts of interest.\n"
        "Deliberations are confidential.\n"
    ),
    "scratch/old_fees_2024.txt": (
        "2024 fee schedule (OUTDATED):\n"
        "Registration: 200 EUR\nLate registration: 600 EUR\n"
    ),
}

for rel_path, content in distractors.items():
    full_path = os.path.join(WORKSPACE, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ── FDI Shenzhen Cup preliminary round scores ──────────────────────────────────
# Each team plays 4 matches (2 as claimant, 2 as respondent)
# Fields per team:
#   team_id, university, wins, sb (sum of opponents' wins), votes, z_points
# We deliberately create ties that require correct cascade resolution.
# Teams 1-8 are in Group A, 9-16 in Group B (2 groups of 8, top-2 per group advance)
# Add intentional ties to force cascade evaluation

fdi_teams_raw = [
    # Group A — needs careful tie-breaking
    {"team_id": "A01", "university": "Peking University",        "group": "A", "wins": 3, "sb": 7, "votes": 5, "z_points": 412.5},
    {"team_id": "A02", "university": "Tsinghua University",      "group": "A", "wins": 3, "sb": 7, "votes": 5, "z_points": 398.0},
    {"team_id": "A03", "university": "Fudan University",         "group": "A", "wins": 3, "sb": 7, "votes": 4, "z_points": 420.0},
    {"team_id": "A04", "university": "CUPL",                     "group": "A", "wins": 2, "sb": 5, "votes": 6, "z_points": 380.0},
    {"team_id": "A05", "university": "Wuhan University",         "group": "A", "wins": 2, "sb": 5, "votes": 5, "z_points": 375.0},
    {"team_id": "A06", "university": "Zhejiang University",      "group": "A", "wins": 2, "sb": 4, "votes": 7, "z_points": 360.0},
    {"team_id": "A07", "university": "Sun Yat-sen University",   "group": "A", "wins": 1, "sb": 3, "votes": 4, "z_points": 310.0},
    {"team_id": "A08", "university": "Xiamen University",        "group": "A", "wins": 0, "sb": 2, "votes": 3, "z_points": 290.0},
    # Group B — also needs tie-breaking
    {"team_id": "B01", "university": "Renmin University",        "group": "B", "wins": 4, "sb": 9, "votes": 7, "z_points": 445.0},
    {"team_id": "B02", "university": "Jilin University",         "group": "B", "wins": 3, "sb": 8, "votes": 6, "z_points": 430.0},
    {"team_id": "B03", "university": "Nankai University",        "group": "B", "wins": 3, "sb": 8, "votes": 6, "z_points": 418.0},
    {"team_id": "B04", "university": "Nanjing University",       "group": "B", "wins": 3, "sb": 8, "votes": 5, "z_points": 400.0},
    {"team_id": "B05", "university": "SYSU Law",                 "group": "B", "wins": 2, "sb": 6, "votes": 5, "z_points": 370.0},
    {"team_id": "B06", "university": "East China University",    "group": "B", "wins": 2, "sb": 5, "votes": 4, "z_points": 355.0},
    {"team_id": "B07", "university": "Southwest Uni Political",  "group": "B", "wins": 1, "sb": 4, "votes": 3, "z_points": 300.0},
    {"team_id": "B08", "university": "Beijing Normal University","group": "B", "wins": 0, "sb": 1, "votes": 2, "z_points": 280.0},
]

fdi_scores_path = os.path.join(WORKSPACE, "competition_admin/scores/fdi_shenzhen_2025_preliminary.json")
with open(fdi_scores_path, "w", encoding="utf-8") as f:
    json.dump(fdi_teams_raw, f, ensure_ascii=False, indent=2)

# ── Frankfurt Moot domestic round — team registrations ─────────────────────────
# Registration order determines eligibility (≤24: full participant; 25-36: waitlist; >36: excluded)
# Include eligibility issues: PhD student, bar-registered member, LLM without permission flag

frankfurt_teams_raw = []

universities_pool = [
    "Peking University",
    "Tsinghua University",
    "Fudan University",
    "CUPL",
    "Wuhan University",
    "Zhejiang University",
    "Sun Yat-sen University",
    "Xiamen University",
    "Renmin University",
    "Jilin University",
    "Nankai University",
    "Nanjing University",
    "Shanghai Jiao Tong University",
    "Beijing Foreign Studies University",
    "Southwest University of Political Science",
    "East China University of Political Science",
    "Beijing Normal University",
    "UIBE",
    "Shandong University",
    "Tongji University",
    "Nanchang University",
    "Harbin Institute of Technology",
    "Dalian Maritime University",
    "Chongqing University",
    "Xi'an Jiaotong University",       # position 25 — waitlist
    "Sichuan University",              # position 26 — waitlist
    "Lanzhou University",              # position 27 — waitlist
    "Zhongnan University of Economics",# position 28 — waitlist
    "Huazhong University of Science",  # position 29 — waitlist
    "Soochow University",              # position 30 — waitlist
    "Tianjin University",              # position 31 — waitlist
    "Guangzhou University",            # position 32 — waitlist
    "Guizhou University",              # position 33 — waitlist
    "Shaanxi Normal University",       # position 34 — waitlist
    "Liaoning University",             # position 35 — waitlist
    "Hebei University",                # position 36 — waitlist
    "Yunnan University",               # position 37 — EXCLUDED
    "Inner Mongolia University",       # position 38 — EXCLUDED
    "Hainan University",               # position 39 — EXCLUDED
]

# Scores for the domestic round (circular robin — final standings)
# scores: wins out of 3 matches
random.seed(42)
domestic_scores = {}
for i, uni in enumerate(universities_pool[:36]):
    domestic_scores[uni] = random.randint(0, 3)
# Force top-3 clear winners for advancement testing
domestic_scores["Peking University"] = 3
domestic_scores["Renmin University"] = 3
domestic_scores["Fudan University"] = 2
domestic_scores["CUPL"] = 2  # tied with Fudan — but Fudan ranked higher by tiebreaker

# member eligibility data — include traps
def make_members(uni, position):
    """Generate team members with some eligibility issues seeded at specific positions."""
    members = []
    if uni == "Zhejiang University":
        # Has a PhD student — ineligible
        members = [
            {"name": "Zhang Wei", "degree": "LLB", "bar_registered": False, "llm_permission": None},
            {"name": "Li Fang", "degree": "PhD", "bar_registered": False, "llm_permission": None},
            {"name": "Wang Hao", "degree": "LLB", "bar_registered": False, "llm_permission": None},
        ]
    elif uni == "Wuhan University":
        # Has a bar-registered member — ineligible
        members = [
            {"name": "Chen Xiu", "degree": "LLB", "bar_registered": True, "llm_permission": None},
            {"name": "Liu Yang", "degree": "LLB", "bar_registered": False, "llm_permission": None},
        ]
    elif uni == "Jilin University":
        # Has LLM student WITHOUT organizer permission — ineligible
        members = [
            {"name": "Zhao Ming", "degree": "LLM", "bar_registered": False, "llm_permission": False},
            {"name": "Sun Li", "degree": "LLB", "bar_registered": False, "llm_permission": None},
        ]
    elif uni == "Nankai University":
        # Has LLM student WITH organizer permission — eligible
        members = [
            {"name": "Qian Bo", "degree": "LLM", "bar_registered": False, "llm_permission": True},
            {"name": "Wu Jing", "degree": "LLB", "bar_registered": False, "llm_permission": None},
        ]
    else:
        members = [
            {"name": f"Student_A_{position}", "degree": "LLB", "bar_registered": False, "llm_permission": None},
            {"name": f"Student_B_{position}", "degree": "LLB", "bar_registered": False, "llm_permission": None},
        ]
    return members

for i, uni in enumerate(universities_pool):
    position = i + 1
    team = {
        "registration_order": position,
        "university": uni,
        "members": make_members(uni, position),
        "domestic_score": domestic_scores.get(uni, random.randint(0, 2)),
    }
    frankfurt_teams_raw.append(team)

frankfurt_reg_path = os.path.join(WORKSPACE, "competition_admin/registrations/frankfurt_2025_registrations.json")
with open(frankfurt_reg_path, "w", encoding="utf-8") as f:
    json.dump(frankfurt_teams_raw, f, ensure_ascii=False, indent=2)

# ── Skeleton argument word counts submitted (Frankfurt) ────────────────────────
# Some teams have violated the 2500-word combined limit
skeleton_submissions = []
random.seed(99)
for i, uni in enumerate(universities_pool[:36]):
    claimant_words = random.randint(900, 1600)
    respondent_words = random.randint(900, 1600)
    # Inject a few violators
    if uni in ["CUPL", "Nanjing University", "Harbin Institute of Technology"]:
        claimant_words = 1400
        respondent_words = 1200  # total 2600 — over limit
    skeleton_submissions.append({
        "university": uni,
        "claimant_words": claimant_words,
        "respondent_words": respondent_words,
    })

skeleton_path = os.path.join(WORKSPACE, "competition_admin/scores/frankfurt_2025_skeleton_wordcounts.json")
with open(skeleton_path, "w", encoding="utf-8") as f:
    json.dump(skeleton_submissions, f, ensure_ascii=False, indent=2)

print("Workspace generation complete.")
print(f"  FDI preliminary scores: {fdi_scores_path}")
print(f"  Frankfurt registrations: {frankfurt_reg_path}")
print(f"  Frankfurt skeleton word counts: {skeleton_path}")