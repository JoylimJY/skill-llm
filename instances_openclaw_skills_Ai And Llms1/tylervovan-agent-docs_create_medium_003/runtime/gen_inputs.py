from pathlib import Path
import json
import random

random.seed(1337)
root = Path('.')
(root / 'src').mkdir(exist_ok=True)
(root / 'docs').mkdir(exist_ok=True)
(root / 'references').mkdir(exist_ok=True)

(root / 'src' / 'app.py').write_text(
    """def create_user(data):\n    return {'id': 1, 'name': data.get('name', 'unknown')}\n\n\ndef validate_session(token):\n    return token == 'marker-session-token' and {'user_id': 1} or None\n\n\ndef process_payment(intent):\n    return {'status': 'ok', 'intent_id': intent.get('id', 'marker-intent')}\n""",
    encoding='utf-8'
)

(root / 'docs' / 'auth.md').write_text(
    """# Auth\n\nMarker: AUTH-INDEX-7F3A\n\nUse cookie-based sessions for server routes.\n""",
    encoding='utf-8'
)

(root / 'docs' / 'db-schema.md').write_text(
    """# Database Schema\n\nMarker: DB-SCHEMA-91C2\n\nTables: users, sessions, payments.\n""",
    encoding='utf-8'
)

(root / 'references' / 'advanced-patterns.md').write_text(
    """# Advanced Patterns\n\nMarker: ADV-PATTERN-4D11\n\nUse compressed indexes and explicit constraints.\n""",
    encoding='utf-8'
)

manifest = {
    'project': 'acme-docs-demo',
    'seed': 1337,
    'markers': ['AUTH-INDEX-7F3A', 'DB-SCHEMA-91C2', 'ADV-PATTERN-4D11'],
}
(root / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
