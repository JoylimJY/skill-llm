from pathlib import Path

root = Path('.')
(root / 'docs' / 'auth').mkdir(parents=True, exist_ok=True)
(root / 'docs' / 'db').mkdir(parents=True, exist_ok=True)
(root / 'references').mkdir(parents=True, exist_ok=True)

(root / 'docs' / 'auth' / 'llms.txt').write_text(
    'Auth docs marker: AUTH-LOCK-17\nUse server-side session checks.\n',
    encoding='utf-8'
)
(root / 'docs' / 'db' / 'schema.md').write_text(
    '# Database Schema\n\nDB marker: DB-SCHEMA-42\nTables: users, sessions, audit_logs\n',
    encoding='utf-8'
)
(root / 'references' / 'advanced-patterns.md').write_text(
    '# Advanced Patterns\n\nReference marker: ADV-RAG-09\nInclude compressed index strategy and security hardening notes.\n',
    encoding='utf-8'
)
(root / 'README.md').write_text(
    '# Sample Repo\n\nThis repo is prepared for agent docs tasks.\n',
    encoding='utf-8'
)
