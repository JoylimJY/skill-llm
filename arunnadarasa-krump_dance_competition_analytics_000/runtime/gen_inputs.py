import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create deeply nested directory structure with distractor files
dirs = [
    "workspace/krump_battle/raw_data",
    "workspace/krump_battle/archive/2015",
    "workspace/krump_battle/archive/2016",
    "workspace/krump_battle/archive/2017",
    "workspace/krump_battle/judges/panel_a",
    "workspace/krump_battle/judges/panel_b",
    "workspace/krump_battle/media/photos",
    "workspace/krump_battle/media/videos",
    "workspace/krump_battle/logistics",
    "workspace/krump_battle/scoresheets",
    "workspace/krump_battle/competitor_bios",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "workspace/krump_battle/archive/2016/results_2016.txt": "Winner: Big Mijo Fam\nRunner-up: DC Crew\n",
    "workspace/krump_battle/archive/2015/event_notes.txt": "EBS 2015 held in Paris.\n",
    "workspace/krump_battle/archive/2017/schedule.txt": "Day 1: Prelims\nDay 2: Finals\n",
    "workspace/krump_battle/judges/panel_a/judge_bios.txt": "Judge 1: OG Krumper from South Central.\nJudge 2: France rep.\n",
    "workspace/krump_battle/judges/panel_b/scoring_notes.md": "# Notes\nScoring is subjective.\n",
    "workspace/krump_battle/media/photos/readme.txt": "Photos from IIB 2017.\n",
    "workspace/krump_battle/media/videos/playlist.txt": "Combo1_Raw.mp4\nCombo2_Live.mp4\n",
    "workspace/krump_battle/logistics/venue_info.txt": "Venue: The Realm, Los Angeles\nCapacity: 500\n",
    "workspace/krump_battle/competitor_bios/bio_template.txt": "Name:\nFam:\nBig Homie:\nStyle:\n",
    "workspace/krump_battle/raw_data/old_scoring_system.json": json.dumps({
        "note": "DEPRECATED - old system used equal weights for all 7 criteria",
        "weights": {"kill_off": 0.143, "material": 0.143, "musicality": 0.143,
                    "combo": 0.143, "travelling": 0.143, "get_off": 0.143, "basics": 0.143}
    }, indent=2),
    "workspace/krump_battle/scoresheets/blank_sheet.txt": "Competitor: ____\nKill Off: ___/5\nMaterial: ___/5\n",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# The actual task input: three competitor submissions
# Each submission has: choreography name, sequence (text notation), artistic statement, and judge scores (1-5 per criterion)
# NOTE: The sequences deliberately include tricky cases:
# - Arm Swing – Snatch (inherits timing from Arm Swing = 1)
# - Textures – Fire (inherits timing from Textures = 1, but here used at 0.5 per Combo 2 style)
# - In-Between (timing = 0.5, unique)
# - Get Off (timing = 4)
# - Kill Off (timing = "End")

competitor_submissions = {
    "competitors": [
        {
            "name": "Baby Tight Eyez",
            "choreography_name": "Rage of the Streets",
            "sequence": "Groove (1) -> Travelling (1) -> Stomp (1) -> Jab (0.5) -> In-Between (0.5) -> Chest Pop (1) -> Arm Swing – Snatch (1) -> Rumble (1) -> Get Off (4) -> Kill Off (End)",
            "artistic_statement": "This round tells the story of a warrior walking into battle, feeling the ground beneath them, unleashing everything, then finishing with a moment that stops time.",
            "judge_scores": {
                "kill_off": 5,
                "material": 4,
                "musicality": 3,
                "combo": 4,
                "travelling": 5,
                "get_off": 5,
                "basics": 4
            }
        },
        {
            "name": "Lil Slayer",
            "choreography_name": "Inferno Protocol",
            "sequence": "Groove (1) -> Buck Hop (1) -> Stomp (1) -> Jab (0.5) -> Textures – Fire (0.5) -> Chest Pop (1) -> Wobble (1) -> Focus Point (1) -> Pose + Arm Placements (2)",
            "artistic_statement": "Fire is the character. Every move burns. The textures shift from explosive jabs to a wobble that echoes like an aftershock.",
            "judge_scores": {
                "kill_off": 3,
                "material": 5,
                "musicality": 5,
                "combo": 4,
                "travelling": 2,
                "get_off": 3,
                "basics": 5
            }
        },
        {
            "name": "Young Miss Prissy",
            "choreography_name": "Phantom Groove",
            "sequence": "Groove (1) -> 3D (1) -> Stomp (1) -> Arm Swing – Smash (1) -> In-Between (0.5) -> Chest Pop (1) -> Zones (1) -> Footwork (1) -> Wobble (1) -> Pose + Arm Placements (2)",
            "artistic_statement": "Moving in three dimensions, this round embodies a ghost drifting through dimensions — graceful but with devastating impact.",
            "judge_scores": {
                "kill_off": 4,
                "material": 4,
                "musicality": 4,
                "combo": 5,
                "travelling": 3,
                "get_off": 4,
                "basics": 3
            }
        }
    ]
}

input_path = os.path.join(workspace, "workspace/krump_battle/raw_data/competitor_submissions.json")
with open(input_path, "w") as f:
    json.dump(competitor_submissions, f, indent=2)

print("Input files generated successfully.")
print(f"Main input: {input_path}")