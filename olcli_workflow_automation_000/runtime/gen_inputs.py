import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# Create a realistic distractor directory structure simulating a researcher's workspace
dirs = [
    "workspace/old_drafts/v1",
    "workspace/old_drafts/v2",
    "workspace/references",
    "workspace/figures/raw",
    "workspace/figures/processed",
    "workspace/experiments/results",
    "workspace/experiments/logs",
    "workspace/scripts",
    "workspace/reviews",
    "workspace/supplementary",
]

for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "workspace/old_drafts/v1/main.tex": r"""\documentclass{article}
\begin{document}
Old draft version 1. Do not use.
\end{document}
""",
    "workspace/old_drafts/v2/main.tex": r"""\documentclass{article}
\begin{document}
Old draft version 2. Superseded.
\end{document}
""",
    "workspace/old_drafts/v2/references.bib": """@inproceedings{lecun1998,
  author={LeCun, Y.},
  title={Gradient-based learning applied to document recognition},
  year={1998}
}
""",
    "workspace/references/papers.bib": """@article{vaswani2017,
  author={Vaswani, A. and others},
  title={Attention is all you need},
  year={2017}
}
""",
    "workspace/figures/raw/experiment_plot.png.placeholder": "placeholder for figure",
    "workspace/figures/processed/fig1_cropped.placeholder": "processed figure placeholder",
    "workspace/experiments/results/accuracy.csv": "epoch,train_acc,val_acc\n1,0.72,0.68\n2,0.81,0.75\n3,0.88,0.82\n",
    "workspace/experiments/logs/run_001.log": "2024-01-15 10:23:11 INFO Training started\n2024-01-15 12:44:02 INFO Epoch 3 complete\n",
    "workspace/scripts/preprocess.py": """#!/usr/bin/env python3
# Data preprocessing script
import sys
print('Preprocessing data...')
""",
    "workspace/scripts/plot_results.py": """#!/usr/bin/env python3
# Plot experiment results
import sys
print('Plotting...')
""",
    "workspace/reviews/reviewer1_comments.txt": """Reviewer 1:
- The abstract needs to be clearer about the main contribution.
- Please update the abstract to explicitly mention the 12% accuracy improvement.
- Add .bbl file for arXiv submission.
""",
    "workspace/reviews/reviewer2_comments.txt": """Reviewer 2:
- Good work overall.
- Minor: Fix typo in Section 3.
""",
    "workspace/supplementary/appendix_notes.txt": "Additional derivations to be included in supplementary material.\n",
    "workspace/notes.txt": "TODO: sync changes to overleaf, compile final version, get bbl for arxiv\n",
}

for filepath, content in distractor_files.items():
    p = Path(filepath)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

# Create the task brief for the agent
task_brief = """TASK BRIEF
==========

Our paper "NeurIPS_2024_Paper" is hosted on our team's cloud LaTeX editor.
We need to prepare the final camera-ready version for arXiv submission.

Steps needed:
1. Authenticate with the cloud LaTeX service using the session cookie: s%3AaBcDeFgHiJkLmNoPqRsTuVwXyZ123456.abcdefghijklmnopqrstuvwxyz0123456789
2. Pull the project "NeurIPS_2024_Paper" locally.
3. Update the abstract in main.tex: replace the existing abstract text with
   "We present a novel approach achieving 12% improvement over baselines."
4. Preview what changes would be uploaded (dry run), then push the updated file.
5. Compile and download the PDF, saving it as camera_ready.pdf inside the project directory.
6. List available compiled outputs, then download the bibliography output file,
   saving it as main.bbl inside the project directory (needed for arXiv).
"""

Path("workspace/task_brief.txt").write_text(task_brief)

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(Path("workspace").rglob("*")):
    if f.is_file():
        print(f"  {f}")