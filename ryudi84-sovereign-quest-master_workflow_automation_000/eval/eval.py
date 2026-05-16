import sys
import json
import re
from pathlib import Path

workspace = sys.argv[1]

checks = []

def find_file(name):
    results = list(Path(workspace).rglob(name))
    return results[0] if results else None

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# ── File 1: daily_quests.txt ──────────────────────────────────────────────────
dq_file = find_file("daily_quests.txt")
if dq_file is None:
    add_check("daily_quests_file_exists", False, "daily_quests.txt not found anywhere in workspace")
    dq_content = ""
else:
    add_check("daily_quests_file_exists", True, f"Found at {dq_file}")
    dq_content = dq_file.read_text()

# Check header emoji and structure
header_ok = "📋" in dq_content and "TODAY'S QUESTS" in dq_content.upper()
add_check("daily_quests_header_format", header_ok,
    "Must contain 📋 emoji and TODAY'S QUESTS header" if not header_ok else "Header present")

# Check Main Quests section
main_section = "Main Quest" in dq_content
add_check("daily_quests_main_section", main_section,
    "Must have a 'Main Quests' section" if not main_section else "Main Quests section found")

# Check Side Quests section
side_section = "Side Quest" in dq_content
add_check("daily_quests_side_section", side_section,
    "Must have a 'Side Quests' section" if not side_section else "Side Quests section found")

# Count total quests ([ ] markers) — must be 3-5 main quests + side quests (3+)
quest_markers = re.findall(r'\[ \]', dq_content)
total_quests = len(quest_markers)
quests_count_ok = total_quests >= 6  # at least 3 main + 3 side
add_check("daily_quests_count_adequate", quests_count_ok,
    f"Found {total_quests} quest markers [ ], need at least 6 (3 main + 3 side)" if not quests_count_ok else f"Found {total_quests} quests")

# Check stat variety — must reference multiple stat categories
stat_abbrevs = ["INT", "STR", "CRE", "DIS", "SOC"]
stats_used = [s for s in stat_abbrevs if s in dq_content]
stat_mix_ok = len(stats_used) >= 3
add_check("daily_quests_stat_mix", stat_mix_ok,
    f"Only {len(stats_used)} stat types found ({stats_used}), need at least 3" if not stat_mix_ok else f"Stats used: {stats_used}")

# Check XP format (+NN STAT XP or +NN XP)
xp_pattern = re.findall(r'\+\d+\s+(?:INT|STR|CRE|DIS|SOC)\s+XP', dq_content)
xp_format_ok = len(xp_pattern) >= 4
add_check("daily_quests_xp_format", xp_format_ok,
    f"Found {len(xp_pattern)} properly formatted XP rewards (e.g., '+25 INT XP'), need ≥4" if not xp_format_ok else f"XP rewards formatted correctly: {len(xp_pattern)}")

# Check references to player's actual goals (fitness/running, ML/learning, networking/LinkedIn)
goal_refs = []
for kw in ["run", "gym", "5k", "10k", "strength", "machine learning", "ml", "course", "linkedin", "network", "connect"]:
    if kw.lower() in dq_content.lower():
        goal_refs.append(kw)
goal_ref_ok = len(goal_refs) >= 2
add_check("daily_quests_references_player_goals", goal_ref_ok,
    f"Quests should reference Alex's actual goals (running, ML, networking). Found keywords: {goal_refs}" if not goal_ref_ok else f"Goal references found: {goal_refs}")

# Adaptive difficulty note — player has 97% completion rate, should mention increased difficulty
difficulty_keywords = ["increase", "harder", "difficult", "ramp", "challenge", "leveled up", "bump", "elevated", "raised", "tougher"]
adaptive_ok = any(kw.lower() in dq_content.lower() for kw in difficulty_keywords)
add_check("daily_quests_adaptive_difficulty_noted", adaptive_ok,
    "No mention of increased difficulty despite 97% completion rate in logs" if not adaptive_ok else "Adaptive difficulty acknowledged")

# ── File 2: boss_fight.txt ────────────────────────────────────────────────────
bf_file = find_file("boss_fight.txt")
if bf_file is None:
    add_check("boss_fight_file_exists", False, "boss_fight.txt not found anywhere in workspace")
    bf_content = ""
else:
    add_check("boss_fight_file_exists", True, f"Found at {bf_file}")
    bf_content = bf_file.read_text()

# Check boss fight emoji and header
bf_header_ok = "🐉" in bf_content and ("BOSS FIGHT" in bf_content.upper() or "Boss Fight" in bf_content)
add_check("boss_fight_header_format", bf_header_ok,
    "Must contain 🐉 emoji and BOSS FIGHT header" if not bf_header_ok else "Boss fight header present")

# Check the goal title matches config
portfolio_ok = "Portfolio" in bf_content or "portfolio" in bf_content
add_check("boss_fight_references_goal_title", portfolio_ok,
    "Boss fight should reference 'Portfolio Website' goal from config" if not portfolio_ok else "Portfolio goal referenced")

# Check phases exist (Phase 1, Phase 2, etc.)
phases = re.findall(r'Phase\s+\d+', bf_content, re.IGNORECASE)
phases_ok = len(phases) >= 3
add_check("boss_fight_has_phases", phases_ok,
    f"Found {len(phases)} phases, need at least 3" if not phases_ok else f"Found {len(phases)} phases")

# Check total reward mentioned
total_ok = "Total" in bf_content and "XP" in bf_content
add_check("boss_fight_has_total_reward", total_ok,
    "Boss fight must include a 'Total' XP reward summary" if not total_ok else "Total XP reward present")

# Check bonus achievement mentioned (achievement if completed on time)
bonus_ok = any(kw in bf_content for kw in ["Bonus", "bonus", "achievement", "Achievement", "Ship It", "on time", "on-time"])
add_check("boss_fight_has_bonus_achievement", bonus_ok,
    "Boss fight must include a bonus achievement for on-time completion" if not bonus_ok else "Bonus achievement present")

# Check correct stats (INT, CRE, DIS referenced — those are the related_stats in config)
bf_stats = [s for s in ["INT", "CRE", "DIS"] if s in bf_content]
bf_stats_ok = len(bf_stats) >= 2
add_check("boss_fight_correct_stats", bf_stats_ok,
    f"Boss fight should use INT, CRE, DIS stats per config. Found: {bf_stats}" if not bf_stats_ok else f"Boss fight stats: {bf_stats}")

# ── File 3: quest_completion_report.txt ──────────────────────────────────────
qcr_file = find_file("quest_completion_report.txt")
if qcr_file is None:
    add_check("quest_completion_report_exists", False, "quest_completion_report.txt not found")
    qcr_content = ""
else:
    add_check("quest_completion_report_exists", True, f"Found at {qcr_file}")
    qcr_content = qcr_file.read_text()

# Check completed quest markers [x]
completed_markers = re.findall(r'\[x\]|\[X\]', qcr_content)
completions_ok = len(completed_markers) >= 4
add_check("quest_completion_marked_done", completions_ok,
    f"Found {len(completed_markers)} [x] markers, need at least 4 (5 activities reported)" if not completions_ok else f"Found {len(completed_markers)} completed quests")

# Check XP awarded for each completion
xp_awarded = re.findall(r'\+\d+\s+(?:INT|STR|CRE|DIS|SOC)\s+XP', qcr_content)
xp_awarded_ok = len(xp_awarded) >= 4
add_check("quest_completion_xp_awarded", xp_awarded_ok,
    f"Found {len(xp_awarded)} XP awards, need at least 4" if not xp_awarded_ok else f"XP awards: {len(xp_awarded)}")

# Check that activities are correctly mapped to stats:
# running → STR, ML lecture → INT, LinkedIn/networking → SOC, cold shower → DIS, blog post → CRE/INT
str_awarded = "STR" in qcr_content
int_awarded = "INT" in qcr_content
soc_awarded = "SOC" in qcr_content
dis_awarded = "DIS" in qcr_content
stat_mapping_ok = str_awarded and int_awarded and soc_awarded and dis_awarded
add_check("quest_completion_correct_stat_mapping", stat_mapping_ok,
    f"Activities not mapped to correct stats. STR={str_awarded}, INT={int_awarded}, SOC={soc_awarded}, DIS={dis_awarded}" if not stat_mapping_ok else "All stat mappings correct")

# Check "Daily Clear" achievement — all main quests completed
daily_clear_ok = "Daily Clear" in qcr_content or "daily clear" in qcr_content.lower()
add_check("quest_completion_daily_clear_achievement", daily_clear_ok,
    "Must check/award 'Daily Clear' achievement when all main quests are done" if not daily_clear_ok else "Daily Clear achievement present")

# ── Final scoring ─────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 3)
overall_passed = passed_count >= int(total * 0.75)

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))