from pathlib import Path

markers = {
    'project_name.txt': 'MARKER_PROJECT=agent-sync-demo',
    'seed_note.txt': 'MARKER_SEED=42',
}
for name, content in markers.items():
    Path(name).write_text(content + '\n', encoding='utf-8')
