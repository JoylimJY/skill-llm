from pathlib import Path
import random

random.seed(1337)

text = """Draft ID: HX-2049

Great question! In today's rapidly evolving digital landscape, it is worth noting that the project serves as a testament to the team's commitment to innovation, synergy, and excellence. The initiative leverages a robust, comprehensive framework that facilitates seamless collaboration across multifaceted stakeholders. Moreover, it showcases a holistic approach that delves into the nuances of modern workflows while highlighting the pivotal role of adaptable thinking.

The plan is not just about reducing friction, it is about empowering users, enabling proactive decision-making, and unlocking transformative outcomes. Industry reports suggest that organizations that embrace this paradigm are better positioned to thrive despite challenges. The future looks bright, and exciting times lie ahead.

Marker tokens:
- ALPHA_MARKER_17
- BETA_MARKER_42
- OMEGA_MARKER_99
"""
Path("draft.txt").write_text(text, encoding="utf-8")

# Deterministic auxiliary file for harder eval logic
notes = """Internal note:
Use a more natural voice.
Preserve meaning.
Avoid phrases like 'in today's digital age'.
"""
Path("notes.txt").write_text(notes, encoding="utf-8")
