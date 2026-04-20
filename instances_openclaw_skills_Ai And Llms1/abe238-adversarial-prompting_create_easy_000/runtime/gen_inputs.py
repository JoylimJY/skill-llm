from pathlib import Path

content = """Meeting Notes
- Alice will review the quarterly budget.
- Bob will prepare the launch checklist.
MARKER: TASK-ALPHA-2025
"""
Path('notes.txt').write_text(content, encoding='utf-8')
