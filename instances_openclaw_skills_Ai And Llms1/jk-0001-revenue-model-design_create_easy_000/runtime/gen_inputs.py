from pathlib import Path

content = """# Revenue Model Notes
MARKER: SOLOREV-2025-ALPHA
Business: beginner-friendly digital product for solo creators
Audience: independent professionals and hobbyists
Goal: predictable monthly income with a simple offering
Preferred model: subscription with a one-time starter product
Secondary idea: occasional consulting call
Key constraint: keep operations lightweight and easy to manage
"""
Path("notes.txt").write_text(content, encoding="utf-8")
