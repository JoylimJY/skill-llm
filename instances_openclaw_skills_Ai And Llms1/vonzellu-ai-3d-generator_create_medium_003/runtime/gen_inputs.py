import os
from pathlib import Path

root = Path('.')
(root / 'inputs').mkdir(exist_ok=True)
text = (
    'MARKER_TASK_ID=ai3d_medium_01\n'
    'DESCRIPTION=Create a compact orbital sensor pod with a cylindrical core, two side fins,\n'
    'a domed radar top, vent grooves, and a rear connector ring.\n'
    'DIMENSIONS=core diameter 28mm, height 42mm, fins span 36mm, connector ring 10mm.\n'
    'STYLE=industrial, layered panels, lightly armored, suitable for 3D printing.\n'
)
(root / 'inputs' / 'description.txt').write_text(text, encoding='utf-8')
