from pathlib import Path
import random

random.seed(1337)

context = Path('context')
context.mkdir(exist_ok=True)

history = """USER: Kick off the quarterly review for Project Atlas.
ASSISTANT: Sure — I will summarize the latest decisions and track action items.
USER: TODO: reconcile the June numbers with the finance sheet.
ASSISTANT: Noted. Next action is to confirm the variance threshold.
USER: follow-up: include the partner feedback and revise the milestones.
ASSISTANT: Acknowledged. I'll keep the latest four turns visible in the compact summary.
USER: We also need a pending decision about the export format, maybe JSON or CSV.
ASSISTANT: Understood. The summary should surface open decisions and pending tasks.
USER: MARKER_ALPHA_7812
ASSISTANT: Recent context should preserve this marker for verification.
"""

(context / 'history.txt').write_text(history, encoding='utf-8')

notes = """# Auxiliary Notes
This file is intentionally non-essential.
Seed: 1337
Marker: MARKER_ALPHA_7812
"""
(context / 'notes.md').write_text(notes, encoding='utf-8')
