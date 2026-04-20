import json
from pathlib import Path

content = """Noise: this line should be ignored.
INCENTIVES The agent performed better when the success criteria were explicit and visible.
Random commentary that should not be used.
DRIFT Behavioral quality slipped after the process changed without review.
CANDOR The most helpful note was a direct explanation of the tradeoff.
INCENTIVES This repeated marker must be ignored.
More noise.
"""
Path('behavior_notes.txt').write_text(content, encoding='utf-8')
