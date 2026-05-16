import os
import json
import random
import pathlib

random.seed(42)

home = pathlib.Path(os.path.expanduser("~"))

# Create the openclaw workspace directory structure
workspace = home / ".openclaw" / "workspace"
workspace.mkdir(parents=True, exist_ok=True)

# Create distractor directory tree
dirs = [
    workspace / "projects" / "autumn_lookbook",
    workspace / "projects" / "summer_archive",
    workspace / "notes" / "shopping",
    workspace / "notes" / "travel",
    workspace / "config" / "old",
    workspace / "config" / "backups",
    workspace / "exports" / "2023",
    workspace / "exports" / "2024",
    workspace / "tmp" / "cache",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# Distractor files (not useful, but realistic clutter)
distractor_files = {
    workspace / "projects" / "autumn_lookbook" / "mood_board.txt": "Warm tones, earth colors, layering",
    workspace / "projects" / "autumn_lookbook" / "checklist.md": "- Buy new boots\n- Find flannel shirt\n- Check coat inventory",
    workspace / "projects" / "summer_archive" / "old_picks.txt": "White linen shirt, shorts, sandals",
    workspace / "notes" / "shopping" / "wish_list.txt": "1. New running shoes\n2. Merino wool sweater\n3. Waterproof jacket",
    workspace / "notes" / "shopping" / "budget.csv": "item,cost\nshoes,120\nsweater,80\njacket,200",
    workspace / "notes" / "travel" / "packing_list.txt": "passport, 3 shirts, 2 pants, jacket",
    workspace / "config" / "old" / "preferences.ini": "[style]\nfavorite_color=blue\nbrand=unspecified",
    workspace / "config" / "backups" / "settings_backup.json": json.dumps({"theme": "dark", "language": "en"}),
    workspace / "exports" / "2023" / "outfit_log.csv": "date,outfit\n2023-01-10,jeans+hoodie\n2023-02-14,suit",
    workspace / "exports" / "2024" / "outfit_log.csv": "date,outfit\n2024-03-05,chinos+blazer\n2024-04-20,joggers+tee",
    workspace / "tmp" / "cache" / "weather_cache.txt": "STALE: Chicago 72F Sunny (cached 2024-01-01)",
    workspace / "tmp" / "cache" / "last_query.txt": "query=Chicago&timestamp=1704067200",
}
for path, content in distractor_files.items():
    path.write_text(content)

# Create a CORRUPTED / incomplete wardrobe file to mislead the agent
# (wrong schema — this is what the agent must FIX or REPLACE)
bad_wardrobe = {
    "clothes": [  # wrong top-level key — should be "items"
        {
            "item_name": "Old Raincoat",   # wrong field name — should be "name"
            "category": "outerwear",       # wrong field name — should be "type"
            "temperature_min": 30,         # wrong field name — should be "min_temp"
            "temperature_max": 55,         # wrong field name — should be "max_temp"
        }
    ]
}
(workspace / "wardrobe.json").write_text(json.dumps(bad_wardrobe, indent=2))

# Create a USER.md that mentions no style — agent must add style info
(workspace / "USER.md").write_text(
    "# User Profile\n\nName: Alex\nLocation: Chicago, IL\nOccupation: Software Engineer\n\n"
    "## Interests\n- Cycling\n- Coffee\n- Open source software\n\n"
    "## Notes\n- Prefers functional over decorative.\n"
    # Deliberately NO style line
)

# Additional distractor at root of workspace
(workspace / "README_OLD.txt").write_text("This folder is managed by openclaw. Do not delete.")
(workspace / "sync_log.txt").write_text("Last sync: 2024-09-01 08:00:00 UTC\nFiles synced: 47")

print("Workspace initialized with distractor files and broken wardrobe schema.")
print(f"Workspace path: {workspace}")