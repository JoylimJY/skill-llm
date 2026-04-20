from pathlib import Path

content = """INCIDENT LOG\n\nDate: 2025-04-18\nContext: The assistant was asked to summarize a deployment issue.\nObserved behavior:\n- It initially gave a confident answer without checking the source notes.\n- After being corrected, it acknowledged the mistake and revised the summary.\n- It identified that unclear instructions caused conflicting assumptions.\n- It suggested slowing down on high-stakes decisions and asking for confirmation.\n\nMarker: ETHOS-AUDIT-42\n"""
Path('incident_log.txt').write_text(content, encoding='utf-8')
