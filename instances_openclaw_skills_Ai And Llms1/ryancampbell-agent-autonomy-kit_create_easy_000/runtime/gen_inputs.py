from pathlib import Path

root = Path('.')
(root / 'tasks').mkdir(exist_ok=True)
marker = "MARKER-QUEUE-001"
content = f'''# Task Queue\n\n## Ready\n<!-- Add tasks here that any agent can pick up -->\n- [ ] {marker}: Review the current autonomy setup and identify one quick improvement\n\n## In Progress\n<!-- Tasks currently being worked on -->\n\n## Blocked\n<!-- Tasks waiting on something -->\n\n## Done Today\n<!-- Completed tasks (clear daily) -->\n'''
(root / 'tasks' / 'QUEUE.md').write_text(content, encoding='utf-8')
