from pathlib import Path

notes = """MARKER:RM-2025-ALPHA
Business idea: a solo operator runs a niche B2B newsletter and micro-tool business for independent bookkeeping firms.
Audience: 200-500 small firms; they value time savings, compliance confidence, and ready-made templates.
Constraints: founder wants predictable monthly income, low support burden, and a path to upsell a premium tier later.
Existing traction: a free newsletter with 1,240 subscribers, 3 small consulting clients, and one simple template pack sold 17 times.
Signals: audience asks for recurring updates, audit checklist templates, and occasional implementation help.
"""
Path("revenue_notes.txt").write_text(notes, encoding="utf-8")
