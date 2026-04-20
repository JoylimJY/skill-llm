from pathlib import Path
import json

root = Path('.')
(root / 'tasks').mkdir(exist_ok=True)
(root / 'memory').mkdir(exist_ok=True)

seed = {
    'date': '2025-05-17',
    'agent': 'kai',
    'marker': 'AUTONOMY-SEED-7',
    'completed': [
        'Reviewed heartbeat flow for proactive work',
        'Shipped initial queue scaffolding',
    ],
    'in_progress': [
        'Document team handoff conventions',
    ],
    'blocked': [
        'Finalize cron timing without human approval',
    ],
    'discovered': [
        'Add a follow-up task for daily metrics consolidation',
    ],
}
(root / 'seed.json').write_text(json.dumps(seed, indent=2), encoding='utf-8')
(root / 'tasks' / 'seed_marker.txt').write_text('AUTONOMY-SEED-7\n', encoding='utf-8')
(root / 'memory' / 'seed_notes.txt').write_text(
    'Seed notes for AUTONOMY-SEED-7: the agent should produce queue, heartbeat, daily memory, and metrics outputs.\n',
    encoding='utf-8'
)
