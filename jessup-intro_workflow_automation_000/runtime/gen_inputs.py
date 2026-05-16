import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# Create distractor directory structure
dirs = [
    "competition_admin/archive/2023",
    "competition_admin/archive/2024",
    "competition_admin/forms",
    "competition_admin/participants",
    "competition_admin/results",
    "competition_admin/schedule",
    "resources/rules_old",
    "resources/memos",
    "resources/training",
    "logistics/hotels",
    "logistics/travel",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# Distractor files
distractor_files = {
    "competition_admin/archive/2023/standings_2023.txt": "Team A: 3W 1L\nTeam B: 2W 2L\n(old format, do not use)",
    "competition_admin/archive/2024/notes.txt": "Reminder: scoring rules changed in 2024.",
    "competition_admin/forms/registration_template.docx": "BINARY PLACEHOLDER - not a real docx",
    "competition_admin/participants/team_list_draft.csv": "team_id,team_name,school\n1,Alpha,PKU\n2,Beta,THU\n...",
    "competition_admin/schedule/round_schedule.txt": "Round 1: TBD\nRound 2: TBD",
    "resources/rules_old/scoring_v1.txt": "Old system: 5 points total per match. NOT CURRENT.",
    "resources/memos/memo_guidelines.txt": "Memos should be 35 pages max. Font size 12.",
    "resources/training/practice_log.txt": "Week 1: read compromis\nWeek 2: research\nWeek 3: draft memo",
    "logistics/hotels/hotel_options.txt": "Option A: Marriott\nOption B: Hilton",
    "logistics/travel/reimbursement_form.txt": "Submit receipts within 30 days.",
    "competition_admin/results/placeholder.txt": "Results will be posted here after processing.",
}
for path, content in distractor_files.items():
    with open(os.path.join(WORKSPACE, path), "w") as f:
        f.write(content)

# --- MAIN INPUT DATA ---
# 16 teams compete in group stage (4 groups of 4 teams each)
# Each team plays 4 matches (2 as Applicant, 2 as Respondent)
# We need to provide raw match data for all group stage matches

# Team definitions
teams = [
    {"id": f"T{i:02d}", "name": name, "school": school}
    for i, (name, school) in enumerate([
        ("Lex Aeternum", "Peking University"),
        ("Iuris Firma", "Tsinghua University"),
        ("Advocati Mundi", "Fudan University"),
        ("Pax Legalis", "Renmin University"),
        ("Ratio Scripta", "Wuhan University"),
        ("Fides et Iura", "Sun Yat-sen University"),
        ("Bonae Fidei", "Zhejiang University"),
        ("Summum Ius", "Nanjing University"),
        ("Lex Naturalis", "Xiamen University"),
        ("Iura Novit", "CUPL"),
        ("Pacta Servanda", "ECUPL"),
        ("Aequitas et Lex", "SWUPL"),
        ("Mos Maiorum", "Sichuan University"),
        ("Ius Cogens", "Jilin University"),
        ("Opinio Iuris", "Nankai University"),
        ("Terra et Mare", "Ocean University"),
    ], start=0)
]

# Group assignments
groups = {
    "A": ["T00", "T01", "T02", "T03"],
    "B": ["T04", "T05", "T06", "T07"],
    "C": ["T08", "T09", "T10", "T11"],
    "D": ["T12", "T13", "T14", "T15"],
}

def make_memorial_scores():
    """Generate a set of 3 memorial scores for a team in one match."""
    scores = sorted([random.uniform(70, 98) for _ in range(3)])
    return [round(s, 2) for s in scores]  # low, mid, high

def make_oral_scores(num_judges=3):
    """Generate oral argument scores: 3 judges, each gives 2 players a score."""
    # Returns list of 3 judges, each with [player1_score, player2_score]
    judges = []
    for _ in range(num_judges):
        p1 = round(random.uniform(65, 95), 2)
        p2 = round(random.uniform(65, 95), 2)
        judges.append([p1, p2])
    return judges

# Generate all round-robin matches within each group
# Each team plays every other team exactly once as applicant, and once as respondent
# Actually per SKILL.md: 4 matches total, 2 as applicant, 2 as respondent
# In a group of 4, round-robin: each pair plays twice (once each side) - 6 pairs × 2 = 12 matches per group, but that gives 6 matches per team
# SKILL.md says 4 matches total. So round-robin: each team plays the other 3 teams once each, 
# then one extra pairing to make 4. Actually let's do: each team plays 4 matches: 2 as applicant vs 2 opponents, 2 as respondent vs other 2.
# That's a standard balanced tournament within 4 teams.

# Balanced schedule for 4 teams: each plays 4 matches (2A, 2R)
# Pairs: (0v1 A=0,R=1), (2v3 A=2,R=3), (0v2 A=2,R=0), (1v3 A=1,R=3), (0v3 A=0,R=3), (1v2 A=1,R=2)
# Wait, that's 6 matches but teams play 3 each... 
# SKILL.md: "小组赛一个队伍总共打四场，控方两场辩方两场"
# 4 teams, each plays 4 matches → 8 team-slots / 2 per match = 4 matches per group round... 
# but that means not all pairs meet. Let's use a fixed schedule where each of 4 teams plays exactly 4 matches:
# Match 1: T[0] (App) vs T[1] (Resp)
# Match 2: T[2] (App) vs T[3] (Resp)
# Match 3: T[1] (App) vs T[2] (Resp)
# Match 4: T[3] (App) vs T[0] (Resp)
# Match 5: T[0] (App) vs T[2] (Resp)  -- but now T[0] has 3 matches
# This doesn't balance nicely with 4 matches each in a group of 4 without repetition being 6 total...
# The simplest: 4 matches per team, group of 4 = 8 total team appearances = 4 matches total but then each team plays only 2. 
# Let's just do each team plays exactly 4 matches total. For a group of 4 (round-robin, each pair plays once = 6 matches, but each team plays 3):
# SKILL.md says 4 matches. Perhaps the group stage has them play some teams twice? Or perhaps there are 5 teams per group?
# Let's just structure it practically: 4 teams in group, 8 total match-slots, 4 matches, each team plays 2 matches. 
# But SKILL.md says 4 matches. Let's have groups of 5 teams instead, giving each team 4 matches in round-robin.
# 16 teams / 4 groups of 4... but let's do 4 groups of 4 and each team plays 4 matches (round-robin with repeats for 1 extra round).
# Simplest solution: use 5 rounds, each team plays 4 matches total (some opponents twice).
# For evaluation clarity, let's just have 4 matches per team however scheduled.

# New approach: 4 groups of 4 teams. Each team plays exactly 4 matches.
# In each group, we create a schedule where each team plays 4 matches (2A, 2R).
# 4 matches per team × 4 teams = 16 team-appearances = 8 matches per group.
# Schedule: A full double round-robin for pairs (0,1), (0,2), (0,3), (1,2), (1,3), (2,3) = 6 unique pairs
# But 8 matches means 2 extra. Let's do round-robin (6 matches) + 2 rematch for specific pairs.
# This gets complex. Instead, let's just list 8 matches per group explicitly.

def gen_group_schedule(team_ids):
    """
    Generate a balanced schedule: 8 matches, each team plays exactly 4 (2 as App, 2 as Resp).
    """
    t = team_ids
    # Each pair plays once, plus two extra rematches
    base_pairs_ap_resp = [
        (t[0], t[1]),
        (t[2], t[3]),
        (t[0], t[2]),
        (t[1], t[3]),
        (t[1], t[0]),  # rematch with sides swapped
        (t[3], t[2]),
        (t[2], t[0]),
        (t[3], t[1]),
    ]
    return base_pairs_ap_resp

all_matches = []
match_id = 1

for group_name, team_ids in groups.items():
    schedule = gen_group_schedule(team_ids)
    for applicant_id, respondent_id in schedule:
        match = {
            "match_id": f"M{match_id:03d}",
            "group": group_name,
            "round": "group_stage",
            "applicant": applicant_id,
            "respondent": respondent_id,
            "applicant_memorial_scores": make_memorial_scores(),  # [low, mid, high]
            "respondent_memorial_scores": make_memorial_scores(),
            # oral_scores[judge_idx] = [applicant_player1_score, applicant_player2_score]
            "applicant_oral_scores": make_oral_scores(),
            # oral_scores[judge_idx] = [respondent_player1_score, respondent_player2_score]
            "respondent_oral_scores": make_oral_scores(),
        }
        all_matches.append(match)
        match_id += 1

# Save teams file
with open(os.path.join(WORKSPACE, "competition_admin/participants/teams.json"), "w") as f:
    json.dump(teams, f, indent=2, ensure_ascii=False)

# Save groups file
with open(os.path.join(WORKSPACE, "competition_admin/schedule/groups.json"), "w") as f:
    json.dump(groups, f, indent=2, ensure_ascii=False)

# Save raw match data
with open(os.path.join(WORKSPACE, "competition_admin/results/group_stage_raw.json"), "w") as f:
    json.dump(all_matches, f, indent=2, ensure_ascii=False)

# Also create a messy, partially-filled "attempt" file that should be ignored
with open(os.path.join(WORKSPACE, "competition_admin/results/attempt_draft.txt"), "w") as f:
    f.write("Team scores attempt (WRONG - do not use):\n")
    f.write("T00: 3 wins (computed by simple point total - INCORRECT METHOD)\n")
    f.write("T01: 2 wins\n")
    f.write("...\n")
    f.write("This file used the wrong scoring formula. Discard.\n")

print("Workspace generated successfully.")
print(f"Total matches generated: {len(all_matches)}")
print(f"Teams: {len(teams)}")