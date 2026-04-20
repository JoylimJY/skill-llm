from pathlib import Path
import json

base = Path('.')
(base / 'memory' / 'rpg' / 'neon_harbor_case').mkdir(parents=True, exist_ok=True)

world = {
    'campaign_name': 'neon_harbor_case',
    'setting': 'Cyberpunk',
    'tone': 'Noir',
    'system': 'd20',
    'time': 'Night, rain-heavy',
    'location': 'Neon Harbor District',
    'weather': 'acid rain',
    'flags': {
        'case_open': True,
        'marker_world': 'HARBOR-7'
    },
    'clocks': {
        'guards_arrive': 1,
        'data_vanishes': 0
    }
}
character = {
    'name': 'Zris Vale',
    'archetype': 'Hacker',
    'hp': 12,
    'resources': {
        'credits': 180,
        'sanity': 6
    },
    'stats': {
        'STR': 1,
        'DEX': 3,
        'INT': 4,
        'WIL': 2,
        'CHA': 1
    },
    'drive': 'Expose the people who erased their sister from the system.',
    'flaw': 'Compulsive curiosity',
    'status_effects': ['watchlisted'],
    'inventory': ['Splice Deck', 'Umbrella Coat', 'Encrypted Shard']
}

npcs = {
    'npcs': [
        {
            'name': 'Mara Quill',
            'role': 'Fixer',
            'bond': 'Knows the first clue in the Neon Harbor case',
            'agenda': 'Wants the truth buried or sold, depending on the bidder'
        },
        {
            'name': 'Officer Renn',
            'role': 'Detective',
            'bond': 'On the edge of helping or arresting the crew',
            'agenda': 'Investigating a series of disappearances'
        }
    ],
    'marker_npc': 'BLACK LANTERN'
}

journal = """Day 1: HARBOR-7 begins under acid rain.
The Neon Harbor case opens with a dead drop, a broken alibi, and a message that reads: BLACK LANTERN.
Zris Vale enters the scene with a Splice Deck and too many questions.
"""
summary = """Campaign: Neon Harbor Case
Premise: A noir cyberpunk investigation in the Neon Harbor District.
Hook: A dead drop leads to a conspiracy tied to BLACK LANTERN and HARBOR-7.
Drive: Expose the people who erased their sister from the system.
Flaw: Compulsive curiosity.
System: d20
Tone: Noir
"""

(base / 'memory' / 'rpg' / 'neon_harbor_case' / 'world.json').write_text(json.dumps(world, indent=2), encoding='utf-8')
(base / 'memory' / 'rpg' / 'neon_harbor_case' / 'character.json').write_text(json.dumps(character, indent=2), encoding='utf-8')
(base / 'memory' / 'rpg' / 'neon_harbor_case' / 'npcs.json').write_text(json.dumps(npcs, indent=2), encoding='utf-8')
(base / 'memory' / 'rpg' / 'neon_harbor_case' / 'journal.md').write_text(journal, encoding='utf-8')
(base / 'campaign_summary.md').write_text(summary, encoding='utf-8')
