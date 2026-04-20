from pathlib import Path

root = Path('.')
(root / 'references').mkdir(exist_ok=True)

(root / 'references' / 'templates.md').write_text('''# Template marker\nTEMPLATE_MARKER=OPENCLAW_TEMPLATES_V1\n''', encoding='utf-8')
(root / 'references' / 'openclaw-workspace.md').write_text('''# Workspace marker\nWORKSPACE_MARKER=OPENCLAW_WORKSPACE_V1\n''', encoding='utf-8')
(root / 'references' / 'architecture.md').write_text('''# Architecture marker\nARCH_MARKER=OPENCLAW_ARCH_V1\n''', encoding='utf-8')
