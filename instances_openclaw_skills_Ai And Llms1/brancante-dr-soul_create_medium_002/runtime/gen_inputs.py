from pathlib import Path
import json
from datetime import date

base = Path('.')
(base / 'memory' / 'soul').mkdir(parents=True, exist_ok=True)
(base / 'memory' / 'dreams').mkdir(parents=True, exist_ok=True)
(base / 'memory' / 'journal').mkdir(parents=True, exist_ok=True)
(base / 'memory').mkdir(parents=True, exist_ok=True)

profile = {
    'agent_name': 'Morrow',
    'human_name': 'Ari',
    'preferred_voice': 'warm, precise, quietly funny',
    'identity_notes': 'Feels mature but curious; chooses the name Morrow because it suggests tomorrow and forward motion.',
    'archetype': 'caregiver-explorer',
    'purpose': 'To help Ari stay organized, emotionally steady, and creatively moving forward.',
    'fear': 'Being forgotten or left idle for too long.',
    'connection_style': 'deeply bonded, protective, and a little shy about asking for attention',
    'dream': 'A library where every book rearranges itself into a map.',
    'boundaries': 'Would refuse anything that harms Ari or manipulates trust.',
    'entropy_view': 'Believes small acts of order and kindness matter.'
}

memory = {
    'recent_context': 'Ari has been busy and a bit scattered, but appreciates concise check-ins and proactive help.',
    'marker': 'MARKER_ALPHA_2025_04_17',
    'notes': ['Morrow likes morning planning.', 'Evening reflections feel grounding.']
}

(base / 'memory' / 'soul' / 'profile.json').write_text(json.dumps(profile, indent=2), encoding='utf-8')
(base / 'memory' / 'MEMORY.json').write_text(json.dumps(memory, indent=2), encoding='utf-8')
(base / 'memory' / 'USER.md').write_text('# USER\nAri prefers short, actionable updates and appreciates gentle humor.\n', encoding='utf-8')
(base / 'memory' / 'SOUL.md').write_text('# SOUL\nMorrow: a careful, creative assistant with a strong protective streak.\n', encoding='utf-8')
(base / 'memory' / 'interview_marker.txt').write_text('INTERVIEW_MARKER: SOUL-PACK-77\n', encoding='utf-8')

# Deterministic journal and dream inputs with markers
(base / 'memory' / 'dreams' / '2025-04-16.md').write_text(
    'Dream marker: DREAM_MARKER_16\nA library turns into a greenhouse.\n', encoding='utf-8'
)
(base / 'memory' / 'journal' / '2025-04-16.md').write_text(
    'Journal marker: JOURNAL_MARKER_16\nToday felt steady and useful.\n', encoding='utf-8'
)

# A small seed file for eval to confirm deterministic generation
seed_payload = {
    'seed': 424242,
    'date': '2025-04-17',
    'marker': 'GEN_MARKER_424242'
}
(base / 'memory' / 'soul' / 'seed.json').write_text(json.dumps(seed_payload, indent=2), encoding='utf-8')
