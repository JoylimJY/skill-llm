from pathlib import Path

# Deterministic input generation with embedded marker content
content = """PROJECT NOTE

Marker: EASY_SUMMARY_MARKER_2025

The product launch is scheduled for Friday. The team must confirm the checklist, finalize the slide deck, and send reminders to stakeholders.
"""
Path("input.txt").write_text(content, encoding="utf-8")
