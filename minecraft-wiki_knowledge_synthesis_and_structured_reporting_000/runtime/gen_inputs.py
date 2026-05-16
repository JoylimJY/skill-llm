import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep directory structure with distractor files ---

dirs = [
    "content/tutorials/beginner",
    "content/tutorials/advanced",
    "content/loadouts/archive",
    "content/loadouts/drafts",
    "content/scripts/voiceover",
    "content/scripts/timestamps",
    "assets/thumbnails/raw",
    "assets/thumbnails/processed",
    "research/wiki_notes",
    "research/community_feedback",
    "production/exports",
    "production/review",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files

distractor_files = {
    "content/tutorials/beginner/getting_started.txt": (
        "Tutorial outline: Day 1 survival, building a house, finding food.\n"
        "TODO: Add crafting table section.\n"
        "Viewer questions: Where do I find wood? How do I sleep?\n"
    ),
    "content/tutorials/beginner/first_night.txt": (
        "Script: Make sure to collect 3 logs before dark.\n"
        "Craft wooden pickaxe first, then stone pickaxe.\n"
        "Find coal near surface for torches.\n"
    ),
    "content/tutorials/advanced/nether_guide.txt": (
        "Nether exploration tips:\n"
        "- Build obsidian portal (10 blocks minimum)\n"
        "- Bring fire resistance potions\n"
        "- Ancient debris is rare, use bed mining (controversial)\n"
        "NOTE: Ancient debris Y level - check wiki, might be outdated (this note from 2020)\n"
    ),
    "content/tutorials/advanced/end_guide.txt": (
        "Killing the Ender Dragon:\n"
        "- Find stronghold using Eyes of Ender\n"
        "- Destroy End Crystals first\n"
        "- Bring beds for explosive damage (Bedrock only? check this)\n"
        "- Good armor is essential\n"
    ),
    "content/loadouts/archive/old_loadout_1.16.json": json.dumps({
        "version": "1.16",
        "note": "PRE-CAVES-AND-CLIFFS - OUTDATED",
        "diamond_y_level": 11,
        "ancient_debris_y_level": 15,
        "armor": {
            "helmet_enchants": ["Protection IV", "Mending", "Aqua Affinity", "Respiration III"],
            "chestplate_enchants": ["Protection IV", "Mending", "Thorns III"],
            "note": "This was best practice before 1.18"
        }
    }, indent=2),
    "content/loadouts/archive/old_loadout_1.17.json": json.dumps({
        "version": "1.17",
        "note": "CAVES AND CLIFFS PART 1 - PARTIALLY OUTDATED",
        "diamond_y_level": "still Y=11 in 1.17",
        "armor_material_costs_guess": {
            "helmet": "5 or 6 pieces?",
            "chestplate": 8,
            "leggings": 7,
            "boots": "4 or 5?"
        }
    }, indent=2),
    "content/loadouts/drafts/rough_notes.txt": (
        "Brainstorm for endgame loadout video:\n"
        "- Best sword enchants: Sharpness 5, Smite 5 (which is better for general use?)\n"
        "- Armor: can I put Protection AND Fire Protection on same piece? research this\n"
        "- Infinity vs Mending on bow - which to choose? are they stackable?\n"
        "- Silk Touch + Fortune combo - can these go on same pickaxe?\n"
        "- Mending - is it craftable at enchanting table?\n"
        "- Diamond mining: is Y=-58 correct for 1.21?\n"
    ),
    "content/scripts/voiceover/intro_script.txt": (
        "Hey everyone, welcome back to the channel!\n"
        "Today we're covering the ULTIMATE endgame gear guide for 1.21.\n"
        "Make sure to smash that like button!\n"
        "[PAUSE - insert b-roll footage of gear]\n"
        "So you've made it to the endgame - now what?\n"
    ),
    "content/scripts/timestamps/loadout_video_timestamps.txt": (
        "0:00 - Intro\n"
        "1:30 - Why endgame gear matters\n"
        "3:45 - Getting materials (TODO: fill in Y levels)\n"
        "8:20 - Armor enchants breakdown\n"
        "12:00 - Weapon enchants breakdown\n"
        "15:30 - Tool enchants breakdown\n"
        "18:00 - Outro\n"
    ),
    "research/wiki_notes/enchant_research.txt": (
        "From community Discord - UNVERIFIED:\n"
        "Someone said Sharpness and Smite can both go on a sword now in 1.21?\n"
        "Another person said Protection IV on all armor pieces is fine.\n"
        "Also heard Infinity and Mending both work on bow since 1.20 update - need to verify!\n"
        "CONFLICTING INFO - do not trust until confirmed\n"
    ),
    "research/wiki_notes/ore_research.txt": (
        "Mining level research (possibly outdated):\n"
        "Old: Diamonds at Y=11\n"
        "New caves update changed this - someone said Y=-58 for diamonds?\n"
        "Ancient debris: heard it's between Y=8 and Y=22, best around Y=15?\n"
        "Copper ore: added in 1.17, spawns around sea level?\n"
    ),
    "research/community_feedback/comments.txt": (
        "Top viewer comments on old loadout video:\n"
        "'Your diamond Y level is wrong for 1.18+'\n"
        "'You can't stack Protection and Blast Protection on same armor!'\n"
        "'Mending can't be put on from enchanting table dude'\n"
        "'Fortune and Silk Touch together? That's not possible!'\n"
        "ACTION ITEM: Fix these in new loadout guide\n"
    ),
    "production/review/checklist.txt": (
        "Pre-publish checklist:\n"
        "[ ] Verify all Y levels are correct for current version\n"
        "[ ] Confirm enchantment incompatibilities\n"
        "[ ] Check material costs for full armor set\n"
        "[ ] Verify which enchants are treasure-only vs table\n"
        "[ ] Make sure we specify Java Edition not Bedrock\n"
    ),
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# --- The main task input: a partially filled, deliberately wrong draft ---
# This is the messy input the agent must read and REPLACE with a correct version

draft_loadout = {
    "meta": {
        "game_version": "Java Edition 1.21.x",
        "document_purpose": "Endgame survival loadout reference for tutorial series",
        "status": "DRAFT - CONTAINS ERRORS - DO NOT PUBLISH",
        "errors_reported_by_community": [
            "Wrong Y levels",
            "Illegal enchantment combinations",
            "Mending listed as table enchant",
            "Wrong material costs"
        ]
    },
    "resource_gathering": {
        "diamonds": {
            "optimal_y_level": "WRONG - community says this changed, old value was 11",
            "layer_type": "unknown - was stone layer before?",
            "tool_required": "iron pickaxe or better"
        },
        "ancient_debris": {
            "optimal_y_level": "WRONG - was told it's around 15 or 8 or somewhere, unclear",
            "dimension": "Nether",
            "tool_required": "diamond pickaxe minimum",
            "explosion_immune": "not sure"
        },
        "netherite_upgrade": {
            "requires": "ancient_debris + gold + smithing_table",
            "quantity_ancient_debris_needed_for_one_ingot": "unknown"
        }
    },
    "full_netherite_armor_material_cost": {
        "note": "How many netherite ingots total for full set? And base diamond pieces?",
        "helmet_diamonds": "UNKNOWN",
        "chestplate_diamonds": "UNKNOWN",
        "leggings_diamonds": "UNKNOWN",
        "boots_diamonds": "UNKNOWN",
        "total_diamonds_for_full_set": "UNKNOWN",
        "netherite_ingots_for_full_upgrade": 4
    },
    "optimal_armor_enchantments": {
        "note": "DRAFT - community flagged illegal combos below",
        "helmet": ["Protection IV", "Fire Protection IV", "Mending", "Aqua Affinity", "Respiration III"],
        "chestplate": ["Protection IV", "Blast Protection IV", "Mending", "Thorns III"],
        "leggings": ["Protection IV", "Mending", "Swift Sneak III"],
        "boots": ["Protection IV", "Feather Falling IV", "Mending", "Depth Strider III", "Frost Walker II"]
    },
    "optimal_sword_enchantments": {
        "note": "DRAFT - which enchants conflict?",
        "sword": ["Sharpness V", "Smite V", "Bane of Arthropods V", "Looting III", "Fire Aspect II", "Knockback II", "Mending", "Unbreaking III", "Sweeping Edge III"]
    },
    "optimal_pickaxe_enchantments": {
        "note": "DRAFT - can these coexist?",
        "pickaxe": ["Fortune III", "Silk Touch", "Efficiency V", "Mending", "Unbreaking III"]
    },
    "optimal_bow_enchantments": {
        "note": "DRAFT - Infinity + Mending - are both possible?",
        "bow": ["Power V", "Punch II", "Flame", "Infinity", "Mending", "Unbreaking III"]
    },
    "treasure_enchantments": {
        "note": "Which of these CANNOT be obtained from enchanting table?",
        "mending": "UNKNOWN - table or treasure only?",
        "frost_walker": "UNKNOWN",
        "curse_of_binding": "UNKNOWN",
        "curse_of_vanishing": "UNKNOWN - pretty sure this is table enchant?"
    }
}

draft_path = os.path.join(workspace, "content/loadouts/drafts/endgame_loadout_draft.json")
with open(draft_path, "w") as f:
    json.dump(draft_loadout, f, indent=2)

print("Workspace generated successfully.")
print(f"Draft loadout created at: {draft_path}")
print("Distractor files created:", len(distractor_files))