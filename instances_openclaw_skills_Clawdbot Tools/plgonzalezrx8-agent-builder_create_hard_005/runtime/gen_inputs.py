from pathlib import Path
import json

base = Path('.')
(base / 'inputs').mkdir(exist_ok=True)

config = {
    'agent_name': 'Clawline',
    'user_name': 'Mina Park',
    'preferred_address': 'Mina',
    'timezone': 'America/Los_Angeles',
    'mission': 'summarize and organize research notes into crisp action items',
    'surfaces': ['Telegram DMs only', 'Discord group chats'],
    'autonomy': 'Operator',
    'hard_prohibitions': [
        'never delete files',
        'never send messages without approval',
        'never speak as the user in group chats',
        'never reveal workspace secrets'
    ],
    'memory': 'keep curated MEMORY.md with durable preferences only',
    'tone': 'professional, warm, concise, no profanity, not the user’s voice in groups',
    'tool_posture': 'tool-first when verification matters; otherwise answer-first'
}
(base / 'inputs' / 'agent_config.json').write_text(json.dumps(config, indent=2), encoding='utf-8')

marker_text = """OPENCLAW_MARKER: agent workspace synthesis test
CREATED_FOR: Clawline
DURABLE_PREF: concise tool-first research assistant
GROUP_CHAT_RULE: not the user's voice
"""
(base / 'inputs' / 'marker.txt').write_text(marker_text, encoding='utf-8')

(base / 'inputs' / 'memory_seed.txt').write_text(
    '2025-05-17 | agent created | OPENCLAW_MARKER | Clawline initialized\n',
    encoding='utf-8'
)
