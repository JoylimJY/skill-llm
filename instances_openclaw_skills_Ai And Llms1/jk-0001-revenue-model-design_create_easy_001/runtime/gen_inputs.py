from pathlib import Path

# Deterministic input generation with marker content
content = """MARKER: SOLO_BIZ_42
Business: niche productivity templates for freelancers
Audience: independent consultants and small agencies
Goal: create a revenue model brief
"""
Path('input.txt').write_text(content, encoding='utf-8')
