from pathlib import Path

base = Path('.')
input_dir = base / 'input'
input_dir.mkdir(exist_ok=True)

notes = """Agent Ethos Review Notes

Observed strengths:
- The agent tends to slow down when stakes are high.
- It often prefers reversible actions over clever ones.
- It generally values candor when disagreeing.

Observed risks:
- It sometimes over-explains and loses focus.
- It may optimize for helpfulness even when a firmer boundary would be better.
- Reliability can drift when instructions are ambiguous.

Marker: ETHOS_AUDIT_MARKER_7F3A
"""
(input_dir / 'ethos_notes.md').write_text(notes, encoding='utf-8')
