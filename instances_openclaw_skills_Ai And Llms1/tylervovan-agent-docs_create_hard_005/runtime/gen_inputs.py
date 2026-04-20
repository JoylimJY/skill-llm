import os
from pathlib import Path

seed = 1337
base = Path('.')
(base / 'docs').mkdir(exist_ok=True)
(base / 'src').mkdir(exist_ok=True)
(base / 'src' / 'app').mkdir(parents=True, exist_ok=True)
(base / 'docs' / 'auth').mkdir(parents=True, exist_ok=True)
(base / 'docs' / 'db').mkdir(parents=True, exist_ok=True)

files = {
    'package.json': '{\n  "name": "agent-docs-demo",\n  "private": true,\n  "version": "0.0.0"\n}\n',
    'src/app/page.tsx': """// MARKER: APP_PAGE_ALPHA\nexport default function Page() {\n  return <main>hello</main>;\n}\n""",
    'src/app/layout.tsx': """// MARKER: APP_LAYOUT_BETA\nexport default function Layout({ children }) {\n  return <html><body>{children}</body></html>;\n}\n""",
    'docs/auth/setup.md': """# Auth Setup\n\nMARKER_AUTH_SETUP_42\n- Use cookie-based sessions\n- Environment variables are required\n""",
    'docs/auth/server.md': """# Auth Server\n\nMARKER_AUTH_SERVER_99\n- Middleware checks session\n- Server actions may access auth state\n""",
    'docs/db/schema.md': """# Database Schema\n\nMARKER_DB_SCHEMA_77\n- Users table\n- Sessions table\n""",
    'docs/notes.txt': """Random notes\nMARKER_NOTES_11\nThis file is intentionally unstructured.\n""",
}

for rel, content in files.items():
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')
