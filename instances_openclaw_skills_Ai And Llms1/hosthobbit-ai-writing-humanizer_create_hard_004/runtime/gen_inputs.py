from pathlib import Path

source = """At the end of the day, the team was tasked with reviewing a draft that had been written in a very polished but unmistakably mechanical style. First, the memo had been built around broad claims, Secondly, it was padded with transition words, Finally, it ended with the familiar line, I hope this helps. The project lead, Maya Chen, noted that the report was delivered on 2025-04-18 and that the budget figure of 1840 dollars has been approved. It is important to remember that the client asked for a version that sounded direct, calm, and human. There were also a few side notes in parentheses that made the text feel overexplained, and the same point was repeated three times in different forms. At the end of the day, the goal was simple: produce a cleaner version without changing the facts, the date, the name, or the amount. Let me know if you have any questions."""

Path("input.txt").write_text(source, encoding="utf-8")
Path("marker.txt").write_text("MARKER_AI_HUMANIZER_7F3A\n", encoding="utf-8")
