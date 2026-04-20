from pathlib import Path
import json
import random

random.seed(1337)
root = Path('.')
inputs = root / 'inputs'
inputs.mkdir(exist_ok=True)

files = {
    'trace_alpha.txt': """# RV-TRACE MARKER: ALPHA-001\nstep=1 observation=0.91 contraction=0.12\nstep=2 observation=0.88 contraction=0.18\nstep=3 observation=0.84 contraction=0.21\n""",
    'trace_beta.txt': """# RV-TRACE MARKER: BETA-002\nlayer: 1 | obs: 0.77 | contraction: 0.08\nlayer: 2 | obs: 0.73 | contraction: 0.11\nlayer: 3 | obs: 0.69 | contraction: 0.16\n""",
    'trace_gamma.txt': """# RV-TRACE MARKER: GAMMA-003\n[0] obs=0.95 shrink=0.05\n[1] obs=0.92 shrink=0.07\n[2] obs=0.90 shrink=0.09\n""",
}

for name, content in files.items():
    (inputs / name).write_text(content, encoding='utf-8')

metadata = {
    'expected_markers': ['ALPHA-001', 'BETA-002', 'GAMMA-003'],
    'files': sorted(files.keys()),
    'deterministic_seed': 1337,
}
(root / 'inputs_manifest.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
