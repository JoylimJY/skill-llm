from pathlib import Path

root = Path('.')
(root / 'HEARTBEAT.md').write_text('''# Heartbeat\n\nUrgent: none\nBlockers: none\nDate: 2025-05-01\n\n## Project Ideas\n- Improve session logging\n- Add deterministic task selection\n\nMARKER_HEARTBEAT_ALPHA\n''', encoding='utf-8')
(root / 'project_notes.txt').write_text('''Ideas for today:\n- Ship something small\n- Avoid narration loops\n- Keep outputs concise\n\nMARKER_NOTES_BETA\n''', encoding='utf-8')
