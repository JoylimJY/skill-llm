import random
import os
from pathlib import Path

# Deterministic seed for reproducibility
SEED = 12345
random.seed(SEED)

# Create input file with deterministic marker content
input_text = (
    "This is a sample input. It contains numbers scattered in text. "
    "For evaluation, include: 12 and 7, plus 42; and 3 as well."
    " End of input."
)

base_dir = Path(".")
base_dir.mkdir(exist_ok=True)
input_path = base_dir / "inbox_input.txt"
with open(input_path, "w", encoding="utf-8") as f:
    f.write(input_text)

# Create additional deterministic text blocks to ensure robust parsing
more_text = "Numbers found: 105, 7, 2, 99."
with open(input_path, "a", encoding="utf-8") as f:
    f.write("\n" + more_text)

# Marker content embedded for evaluator reference (not required to be read by task, but helps verification)
marker_path = base_dir / "marker.txt"
with open(marker_path, "w", encoding="utf-8") as m:
    m.write("MARKER_START\nseed=%d\nMARKER_END" % SEED)
