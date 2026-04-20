from pathlib import Path
import random

random.seed(42)

text = """At the end of the day, it is important to remember that good communication is about clarity, empathy, and consistency. First, the message should be direct. Secondly, it should avoid unnecessary filler. Finally, it should sound natural and human. I hope this helps, and let me know if you have any questions.

This draft was written to test the humanizer skill. It has been prepared with a few obvious AI-style patterns so the output can be checked reliably.
"""

Path("draft.txt").write_text(text, encoding="utf-8")
Path("marker.txt").write_text("HUMANIZER_MARKER_42\n", encoding="utf-8")
