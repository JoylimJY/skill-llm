from pathlib import Path

# Deterministic input with a verifiable marker.
content = """# Task Input
Marker: TAIWAN_CALENDAR_TASK_2025_01
Date to check: 2025-01-06
Need: working-day status and next holiday after that date
"""
Path("input.txt").write_text(content, encoding="utf-8")
