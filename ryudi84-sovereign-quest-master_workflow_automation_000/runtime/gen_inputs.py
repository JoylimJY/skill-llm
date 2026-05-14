import os
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Directory structure ---
dirs = [
    "config",
    "logs",
    "logs/weekly",
    "logs/archive",
    "players",
    "players/stats",
    "players/achievements",
    "engine",
    "engine/xp",
    "engine/rules",
    "quests",
    "quests/templates",
    "quests/completed",
    "reports",
    "docs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- config/goals.json (the key input file) ---
goals = {
    "player_name": "Alex",
    "level": 14,
    "goals": [
        {
            "id": "fitness",
            "description": "Run a 10K race in under 55 minutes",
            "primary_stat": "STR",
            "secondary_stat": "DIS"
        },
        {
            "id": "learning",
            "description": "Complete an advanced machine learning course",
            "primary_stat": "INT",
            "secondary_stat": "CRE"
        },
        {
            "id": "social",
            "description": "Grow professional network to 500 LinkedIn connections",
            "primary_stat": "SOC",
            "secondary_stat": "CRE"
        }
    ],
    "current_stats": {
        "INT": 340,
        "STR": 180,
        "CRE": 210,
        "DIS": 155,
        "SOC": 290
    },
    "boss_fight_goal": {
        "title": "Launch Personal Portfolio Website by Sunday",
        "deadline": "Sunday",
        "related_stats": ["INT", "CRE", "DIS"]
    }
}
with open(os.path.join(workspace, "config/goals.json"), "w") as f:
    json.dump(goals, f, indent=2)

# --- logs/completion_history.json (shows player completing everything easily - triggers adaptive difficulty) ---
completion_history = {
    "last_7_days": [
        {"date": "2024-01-08", "main_quests_total": 3, "main_quests_completed": 3, "side_quests_total": 3, "side_quests_completed": 3},
        {"date": "2024-01-09", "main_quests_total": 3, "main_quests_completed": 3, "side_quests_total": 3, "side_quests_completed": 3},
        {"date": "2024-01-10", "main_quests_total": 4, "main_quests_completed": 4, "side_quests_total": 3, "side_quests_completed": 3},
        {"date": "2024-01-11", "main_quests_total": 3, "main_quests_completed": 3, "side_quests_total": 3, "side_quests_completed": 2},
        {"date": "2024-01-12", "main_quests_total": 4, "main_quests_completed": 4, "side_quests_total": 3, "side_quests_completed": 3},
        {"date": "2024-01-13", "main_quests_total": 3, "main_quests_completed": 3, "side_quests_total": 3, "side_quests_completed": 3},
        {"date": "2024-01-14", "main_quests_total": 4, "main_quests_completed": 4, "side_quests_total": 3, "side_quests_completed": 3}
    ],
    "completion_rate_7d": 0.97
}
with open(os.path.join(workspace, "logs/completion_history.json"), "w") as f:
    json.dump(completion_history, f, indent=2)

# --- logs/today_activity_report.txt (natural language completion messages to parse) ---
activity_report = """Player activity log for today (2024-01-15):

08:15 - "done with my morning run, pushed hard for 5K"
10:30 - "finished the ML lecture on neural networks, took notes"
14:00 - "sent connection requests to 8 people on LinkedIn and replied to everyone in my inbox"
16:30 - "cold shower done, felt brutal but did it"
20:00 - "wrote a blog post draft about my ML learning journey"
"""
with open(os.path.join(workspace, "logs/today_activity_report.txt"), "w") as f:
    f.write(activity_report)

# --- Distractor files ---
# players/stats/alex_snapshot.json
with open(os.path.join(workspace, "players/stats/alex_snapshot.json"), "w") as f:
    json.dump({"note": "old snapshot from last month, not current", "INT": 300, "STR": 150}, f)

# engine/xp/multipliers.json
with open(os.path.join(workspace, "engine/xp/multipliers.json"), "w") as f:
    json.dump({"weekend_bonus": 1.5, "streak_multiplier": 1.1}, f)

# engine/rules/stat_caps.json
with open(os.path.join(workspace, "engine/rules/stat_caps.json"), "w") as f:
    json.dump({"max_xp_per_quest": 150, "daily_xp_cap": 500}, f)

# quests/templates/generic_template.txt
with open(os.path.join(workspace, "quests/templates/generic_template.txt"), "w") as f:
    f.write("[ ] Quest description → +XP STAT XP\n")

# quests/completed/archive_dec.json
with open(os.path.join(workspace, "quests/completed/archive_dec.json"), "w") as f:
    json.dump({"month": "december", "total_completed": 87, "note": "archive only"}, f)

# logs/weekly/week_01.txt
with open(os.path.join(workspace, "logs/weekly/week_01.txt"), "w") as f:
    f.write("Weekly summary placeholder - no relevant data\n")

# logs/archive/old_quests.txt
with open(os.path.join(workspace, "logs/archive/old_quests.txt"), "w") as f:
    f.write("Archived quest data from previous system version.\n")

# players/achievements/earned.json
with open(os.path.join(workspace, "players/achievements/earned.json"), "w") as f:
    json.dump(["Early Bird", "Consistency King", "First Blood"], f)

# docs/system_overview.txt (misleading generic doc)
with open(os.path.join(workspace, "docs/system_overview.txt"), "w") as f:
    f.write("System overview: This is a gamified productivity tracker. See config/ for setup.\n")

# engine/rules/xp_table.json
with open(os.path.join(workspace, "engine/rules/xp_table.json"), "w") as f:
    json.dump({"easy": 10, "medium": 25, "hard": 50, "boss": 100}, f)

# reports/.gitkeep
with open(os.path.join(workspace, "reports/.gitkeep"), "w") as f:
    f.write("")

print("Workspace generated successfully.")