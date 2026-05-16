import os
import random
import string
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── 1. Create ~/news/ with a BROKEN/INCOMPLETE memory.md ─────────────────────
news_dir = Path.home() / "news"
news_dir.mkdir(parents=True, exist_ok=True)

# Malformed memory.md: missing proportions, vague categories, no timing, garbled format pref
(news_dir / "memory.md").write_text("""\
# User Profile

interests: fintech regulation, AI tools (open source)
format: bullets maybe? or narrative idk
timing: mornings i think
last_updated: ???
engagement_notes:
""")

# Empty history.md (exists but blank)
(news_dir / "history.md").write_text("")

# sources.md with one partial entry
(news_dir / "sources.md").write_text("""\
# Trusted Sources

- The Block (crypto/fintech, slightly pro-crypto)
""")

# ── 2. Drop the user's raw preferences note in the workspace ──────────────────
(workspace / "my_news_preferences.txt").write_text("""\
Hey, I want to set up a proper news briefing system. Here's what I care about:

Main focus: fintech regulatory news (like SEC actions, Basel III updates, CBDC policy) -- 
  probably about 65% of what I want to see
Secondary: open-source AI tooling news (new model releases, licensing controversies, 
  framework updates) -- the other 35%

I want bullet points, not long essays. 
Mornings before 9am is when I read this.

Can you get me a briefing today? I care a lot about balanced coverage especially on 
regulatory topics since everyone has an angle. Make sure I know where news is coming from 
and when it broke.
""")

# ── 3. Distractor files – realistic project clutter ──────────────────────────
# Simulate a journalist's working directory with various unrelated files

dirs_to_create = [
    workspace / "drafts" / "articles" / "q2_2024",
    workspace / "drafts" / "articles" / "q3_2024",
    workspace / "drafts" / "pitches",
    workspace / "research" / "basel_iii",
    workspace / "research" / "cbdc" / "europe",
    workspace / "research" / "cbdc" / "usa",
    workspace / "interviews" / "transcripts",
    workspace / "interviews" / "notes",
    workspace / "admin" / "invoices",
    workspace / "admin" / "contacts",
    workspace / "tools" / "scripts",
]

for d in dirs_to_create:
    d.mkdir(parents=True, exist_ok=True)

# Distractor article drafts
(workspace / "drafts" / "articles" / "q2_2024" / "sec_ripple_followup.md").write_text(
    "Draft: Following up on Ripple vs SEC outcome. Need quotes from both sides.\n"
    "Status: In progress\n"
)
(workspace / "drafts" / "articles" / "q2_2024" / "basel_explainer.md").write_text(
    "# Basel III Endgame Explained\nAudience: general finance readers\nDue: TBD\n"
)
(workspace / "drafts" / "articles" / "q3_2024" / "llama_licensing.md").write_text(
    "Meta's LLaMA licensing controversy. Open source community reaction.\n"
    "Sources needed: OSI statement, Meta PR response\n"
)
(workspace / "drafts" / "pitches" / "pitch_cbdc_privacy.txt").write_text(
    "Pitch: CBDC surveillance risks — civil liberties angle\n"
    "Target: Columbia Journalism Review\n"
    "Deadline: Rolling\n"
)

# Research notes
(workspace / "research" / "basel_iii" / "notes.txt").write_text(
    "Basel III Endgame delayed by Fed in Jan 2024. Capital requirements controversy.\n"
    "Key actors: Fed, OCC, FDIC, banking lobby\n"
)
(workspace / "research" / "cbdc" / "europe" / "ecb_notes.md").write_text(
    "ECB digital euro consultation phase. Privacy advocates concerned.\n"
    "Timeline: Pilot 2025?\n"
)
(workspace / "research" / "cbdc" / "usa" / "fed_links.txt").write_text(
    "https://www.federalreserve.gov/cbdc\n"
    "Boston Fed Project Hamilton notes\n"
)

# Interview transcripts (dummy)
for i in range(1, 4):
    (workspace / "interviews" / "transcripts" / f"interview_{i:02d}.txt").write_text(
        f"[Transcript {i}]\nSpeaker: [REDACTED]\nDate: 2024-0{i+3}-15\nTopic: regulatory fintech\n"
        "Content: Lorem ipsum placeholder for transcript content.\n"
    )

(workspace / "interviews" / "notes" / "contact_sheet.txt").write_text(
    "Sarah M. — Fed communications office\n"
    "Dr. Patel — BIS researcher\n"
    "Anonymous — major US bank compliance dept\n"
)

# Admin clutter
for month in ["jan", "feb", "mar", "apr"]:
    (workspace / "admin" / "invoices" / f"invoice_{month}_2024.txt").write_text(
        f"Invoice {month.upper()} 2024\nAmount: ${''.join(random.choices(string.digits, k=4))}\nStatus: Paid\n"
    )

(workspace / "admin" / "contacts" / "editors.csv").write_text(
    "name,publication,email\n"
    "Alice Chen,FinanceWeekly,alice@fw.example\n"
    "Bob Torres,CryptoDesk,bob@cd.example\n"
    "Priya Shah,PolicyBrief,priya@pb.example\n"
)

# Tools
(workspace / "tools" / "scripts" / "word_count.sh").write_text(
    "#!/bin/bash\nwc -w \"$1\"\n"
)
(workspace / "tools" / "scripts" / "format_citations.py").write_text(
    "# placeholder citation formatter\n"
    "import sys\nprint(f'Formatting: {sys.argv[1] if len(sys.argv) > 1 else \"no file\"}')\n"
)

# A stale old news file to test "stale news" trap awareness
(workspace / "old_news_dump.txt").write_text(
    "2023-01-10: SEC charges Genesis. 2023-02-14: Kraken settlement.\n"
    "2022-11-08: FTX collapse. These are OLD events - do not present as current news.\n"
)

print("Workspace initialized successfully.")
print(f"Files created in: {workspace}")
print(f"News memory dir: {news_dir}")