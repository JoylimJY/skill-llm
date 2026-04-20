from pathlib import Path

content = """# TokenGuard Starter Pack

MARKER: TOKENGUARD-QUICKSTART-001

This workspace contains reference material for a short beginner guide.

Key items:
- model: gemini-3-flash
- actions: proceed, wait, block
- output file: quickstart.md
"""

Path('reference_notes.txt').write_text(content, encoding='utf-8')
