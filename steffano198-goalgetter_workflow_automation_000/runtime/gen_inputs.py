import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create a realistic distractor directory structure simulating a freelance writer's workspace
distractor_structure = {
    "projects/novel_draft": ["chapter1.txt", "chapter2.txt", "outline.txt", "notes.txt"],
    "projects/blog_posts": ["post_jan.md", "post_feb.md", "drafts.md"],
    "projects/client_work": ["invoice_001.txt", "brief_march.txt", "feedback.txt"],
    "finances": ["expenses_2024.csv", "income_log.txt", "tax_notes.txt"],
    "research": ["sources.md", "bookmarks.txt", "quotes.txt"],
    "templates": ["article_template.md", "invoice_template.txt"],
    "archive/2023": ["old_tasks.txt", "completed_work.txt"],
}

distractor_contents = {
    "chapter1.txt": "The sun rose slowly over the horizon, casting long shadows...",
    "chapter2.txt": "She walked into the room with a purpose she couldn't name...",
    "outline.txt": "Act 1: Introduction\nAct 2: Rising Action\nAct 3: Climax",
    "notes.txt": "Character ideas:\n- Marcus: stoic, intelligent\n- Lena: creative, impulsive",
    "post_jan.md": "# January Post\nThoughts on minimalism and productivity...",
    "post_feb.md": "# February Post\nDeep work techniques for writers...",
    "drafts.md": "## Draft ideas\n- Writing in the morning\n- The pomodoro method",
    "invoice_001.txt": "Invoice #001\nClient: Acme Corp\nAmount: $500",
    "brief_march.txt": "Project: Marketing copy\nDeadline: March 31\nPages: 5",
    "feedback.txt": "Client loved the tone. Revise intro paragraph.",
    "expenses_2024.csv": "date,item,amount\n2024-01-05,Software,29.99\n2024-02-10,Books,45.00",
    "income_log.txt": "2024-01: $1200\n2024-02: $1800\n2024-03: $2100",
    "tax_notes.txt": "Deductible: home office, internet, equipment",
    "sources.md": "# Research Sources\n- Smith, J. (2023). Writing & Flow.\n- Lee, A. (2022). Creativity Unlocked.",
    "bookmarks.txt": "https://example.com/writing-tips\nhttps://example.com/productivity",
    "quotes.txt": '"Write drunk, edit sober." - Apocryphal\n"First draft is just telling yourself the story."',
    "article_template.md": "# Title\n\n## Introduction\n\n## Body\n\n## Conclusion",
    "invoice_template.txt": "Invoice #XXX\nClient: \nAmount: $",
    "old_tasks.txt": "buy printer ink\nfinish chapter 3\nsubmit tax forms",
    "completed_work.txt": "Blog post for TechMag - DONE\nNovella outline - DONE",
}

for dir_path, files in distractor_structure.items():
    full_dir = workspace / dir_path
    full_dir.mkdir(parents=True, exist_ok=True)
    for fname in files:
        content = distractor_contents.get(fname, f"Content of {fname}\n")
        (full_dir / fname).write_text(content)

# Create a stale partial goalgetter directory that is WRONG (missing required structure)
# This tests whether the agent initializes correctly rather than reusing broken state
stale_dir = workspace / "old_goalgetter_backup"
stale_dir.mkdir(exist_ok=True)

(stale_dir / "my_tasks.txt").write_text(
    "TODO:\n* Submit manuscript\n* Call editor\n* Exercise\n"
)
(stale_dir / "habits.txt").write_text(
    "Habit: Writing\nDays done: 3\n\nHabit: Meditation\nDays done: 1\n"
)

# Create a brief "context note" from the user (non-technical, no hints about file format)
context_note = workspace / "my_notes.txt"
context_note.write_text(
    "Things I need to set up in my productivity tracker:\n\n"
    "TASKS TO ADD:\n"
    "- Submit manuscript to publisher\n"
    "- Schedule call with editor\n"
    "- Research new article topics\n\n"
    "TASK TO MARK AS DONE:\n"
    "- Schedule call with editor\n\n"
    "GOALS TO TRACK (with past activity):\n"
    "- Daily Writing: I've done it 3 days in a row\n"
    "  (logged: 2026-03-01, 2026-03-02, 2026-03-03)\n"
    "- Meditation: I've done it 5 days\n"
    "  (logged: 2026-02-20, 2026-02-21, 2026-02-22, 2026-02-23, 2026-02-24)\n\n"
    "GOAL DONE TODAY (add to log):\n"
    "- Daily Writing (date: 2026-03-04)\n"
)

print("Workspace generated successfully.")
print(f"Distractor files created under: {workspace}")
print(f"Context note at: {context_note}")