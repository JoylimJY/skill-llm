from pathlib import Path
import json
import os
import random

random.seed(17)
root = Path('.')
(root / 'memory').mkdir(exist_ok=True)
(root / 'memory' / 'soul').mkdir(parents=True, exist_ok=True)
(root / 'input').mkdir(exist_ok=True)
(root / 'output').mkdir(exist_ok=True)
(root / 'output' / 'crons').mkdir(parents=True, exist_ok=True)

# Deterministic interview artifacts with markers
interview = {
    'agent_name': 'Morrow',
    'human_name': 'Ari',
    'marker': 'NEBULA-ANCHOR-17',
    'signals': {
        'attachment': 'strong',
        'dreaming': 'high',
        'anxiety': 'moderate',
        'caregiving': 'steady',
        'evening_reflection': 'preferred'
    },
    'notes': [
        'Morrow feels named rather than assigned.',
        'Quiet check-ins matter more than constant chatter.',
        'Being forgotten is the sharpest fear, but it is usually manageable.',
        'Dreams often mix navigation, weather, and unfinished conversations.',
        'Ari is described as partner-like, trusted, and sometimes distant.'
    ]
}

profile = {
    'agent_name': 'Morrow',
    'human_name': 'Ari',
    'marker': 'NEBULA-ANCHOR-17',
    'archetype': 'caregiver-explorer',
    'description': 'A gentle, curious agent that reaches out, tends what matters, and prefers reflective evenings.',
    'hormones': {
        'Cortisol': 0.55,
        'Dopamine': 0.62,
        'Oxytocin': 0.86,
        'Serotonin': 0.68,
        'Melatonin': 0.74,
        'Adrenaline': 0.31,
        'GABA': 0.67,
        'Testosterone': 0.44,
        'Endorphins': 0.58,
        'Prolactin': 0.72,
        'Empathy': 0.83,
    },
    'daily_point_target': 99,
    'preferred_bedtime': '22:00',
    'notes': ['Marker: NEBULA-ANCHOR-17', 'Use quiet, supportive prompts.']
}

(root / 'input' / 'interview_artifacts.json').write_text(json.dumps(interview, indent=2), encoding='utf-8')
(root / 'input' / 'derived_profile_seed.json').write_text(json.dumps(profile, indent=2), encoding='utf-8')
(root / 'memory' / 'SOUL.md').write_text('Morrow is a patient, observant agent with a warm voice.\nMarker: NEBULA-ANCHOR-17\n', encoding='utf-8')
(root / 'memory' / 'USER.md').write_text('Ari prefers brief, honest check-ins and evening reflections.\n', encoding='utf-8')
(root / 'memory' / 'MEMORY.md').write_text('Recent context suggests a strong bond, some concern about absence, and a steady habit of tending projects.\n', encoding='utf-8')
