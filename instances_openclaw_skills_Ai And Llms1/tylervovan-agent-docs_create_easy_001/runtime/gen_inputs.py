from pathlib import Path
import json

root = Path('.')
(root / 'docs').mkdir(exist_ok=True)
(root / 'src').mkdir(exist_ok=True)
(root / 'references').mkdir(exist_ok=True)

(root / 'package.json').write_text(json.dumps({
    "name": "agent-docs-demo",
    "private": True,
    "scripts": {
        "build": "python -m compileall src",
        "test": "python -m pytest -q",
        "lint": "python -m ruff check src"
    }
}, indent=2), encoding='utf-8')

(root / 'docs' / 'auth.md').write_text(
    "# Authentication Guide\n\nMARKER: AUTH_DOC_V1\n\nUse session cookies for server-side auth.\n",
    encoding='utf-8'
)
(root / 'docs' / 'db-schema.md').write_text(
    "# Database Schema\n\nMARKER: DB_SCHEMA_V1\n\nThe app uses SQLite for local development.\n",
    encoding='utf-8'
)
(root / 'references' / 'style.md').write_text(
    "# Style Guide\n\nMARKER: STYLE_GUIDE_V1\n\nPrefer short, direct instructions.\n",
    encoding='utf-8'
)
(root / 'src' / 'app.py').write_text(
    "def main():\n    return 'hello'\n",
    encoding='utf-8'
)
