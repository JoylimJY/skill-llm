from pathlib import Path
import json

root = Path('.')
(root / 'src').mkdir(exist_ok=True)
(root / 'docs' / 'auth').mkdir(parents=True, exist_ok=True)
(root / 'docs' / 'db').mkdir(parents=True, exist_ok=True)
(root / 'references').mkdir(exist_ok=True)

files = {
    'package.json': {
        'name': 'agent-docs-demo',
        'private': True,
        'type': 'module',
        'scripts': {
            'build': 'node build.mjs',
            'test': 'node test.mjs',
            'lint': 'node lint.mjs'
        },
        'dependencies': {
            'next': '16.0.0',
            'react': '19.0.0',
            'react-dom': '19.0.0',
            '@supabase/ssr': '0.5.0'
        },
        'devDependencies': {
            'typescript': '5.6.3'
        }
    },
    'src/app.tsx': """// MARKER: APP_ROUTER_ONLY\nexport const appRouter = true;\n// MARKER: NO_PAGES_DIR\n""",
    'src/db.ts': """// MARKER: DB_SCHEMA_FILE\nexport const dbSchemaLocation = 'docs/db/schema.md';\n""",
    'src/auth.ts': """// MARKER: AUTH_DOC_FILE\nexport const authDocLocation = 'docs/auth/llms.txt';\n""",
    'docs/auth/llms.txt': """MARKER_AUTH_INDEX\nSetup: environment vars and server/client session handling\nServer: cookie handling and middleware\n""",
    'docs/db/schema.md': """# Database Schema\n\nMARKER_DB_SCHEMA\nTables: users, sessions, payments\nRLS: enabled\n""",
    'references/advanced-patterns.md': """# Advanced Documentation Patterns\n\nMARKER_ADVANCED\nInclude compressed index strategy, llms.txt implementation, cost-efficiency, and security hardening.\n""",
}

for rel, content in files.items():
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, dict):
        path.write_text(json.dumps(content, indent=2) + '\n', encoding='utf-8')
    else:
        path.write_text(content, encoding='utf-8')

(root / 'README.md').write_text("""# Agent Docs Demo\n\nMARKER_README\nUse AGENTS.md for agent governance.\n""", encoding='utf-8')
