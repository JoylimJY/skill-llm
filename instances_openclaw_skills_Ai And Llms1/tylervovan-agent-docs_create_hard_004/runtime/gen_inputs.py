from pathlib import Path
import json

root = Path('.')
(root / 'src').mkdir(exist_ok=True)
(root / 'docs').mkdir(exist_ok=True)
(root / 'references').mkdir(exist_ok=True)

(root / 'src' / 'app.py').write_text(
    '"""Marker app file for agent-docs task.\nPROJECT_MARKER: ALPHA-42\n"""\n\n'
    'def main():\n    return "ok"\n',
    encoding='utf-8'
)

(root / 'docs' / 'auth').mkdir(parents=True, exist_ok=True)
(root / 'docs' / 'db').mkdir(parents=True, exist_ok=True)

(root / 'docs' / 'auth' / 'setup.md').write_text(
    '# Auth Setup\n\nAUTH_MARKER: BRAVO-17\n\nUse environment variables for auth configuration.\n',
    encoding='utf-8'
)

(root / 'docs' / 'db' / 'schema.md').write_text(
    '# DB Schema\n\nDB_MARKER: CHARLIE-88\n\nTables: users, sessions, audit_logs.\n',
    encoding='utf-8'
)

(root / 'references' / 'advanced-patterns.md').write_text(
    '# Advanced Patterns\n\nADV_MARKER: DELTA-900\n\nThis file seeds the docs library for the benchmark.\n',
    encoding='utf-8'
)

(root / 'project-metadata.json').write_text(
    json.dumps({
        'name': 'agent-docs-sandbox',
        'version': '1.0.0',
        'markers': ['ALPHA-42', 'BRAVO-17', 'CHARLIE-88', 'DELTA-900']
    }, indent=2),
    encoding='utf-8'
)
