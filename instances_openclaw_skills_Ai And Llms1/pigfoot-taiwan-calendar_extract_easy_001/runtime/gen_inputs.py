from pathlib import Path

# Deterministic input generation with marker content
content = """# Taiwan Calendar Task

Marker: TAIWAN-CALENDAR-2025-01-06

Reference date: 2025-01-06
Requested outputs should mention the next working day and the next holiday after this date.
"""
Path("instructions.md").write_text(content, encoding="utf-8")
