import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Directory structure ---
dirs = [
    "notes",
    "logs/raw",
    "logs/processed",
    "context/goals",
    "context/archive",
    "drafts",
    "tools/prompts",
    "tools/scripts",
    "meetings/q2",
    "meetings/q3",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
(workspace / "drafts" / "blog_post_ai_agents.md").write_text(
    "# AI Agents are the future\n\nDraft ideas for MediaPlus blog...\n"
)
(workspace / "drafts" / "pitch_deck_notes.txt").write_text(
    "Pitch deck for Q3 budget review — emphasize ROI of AI tooling.\n"
)
(workspace / "context" / "archive" / "old_goals_2023.md").write_text(
    "## 2023 Goals\n- Learn Python\n- Read more books\n- Explore NFTs\n"
)
(workspace / "context" / "goals" / "q1_okrs.md").write_text(
    "Q1 OKRs: Ship 3 AI demos, onboard 2 clients, write 5 blog posts.\n"
)
(workspace / "meetings" / "q2" / "team_sync_notes.md").write_text(
    "Meeting notes: Discussed AI budget, headcount requests, vendor evaluations.\n"
)
(workspace / "meetings" / "q3" / "strategy_offsite.md").write_text(
    "Offsite agenda: Vision 2025, AI integration roadmap, talent strategy.\n"
)
(workspace / "tools" / "prompts" / "summarizer_v2.txt").write_text(
    "Prompt: Summarize the following text in 3 bullet points...\n"
)
(workspace / "tools" / "scripts" / "batch_rename.sh").write_text(
    "#!/bin/bash\n# rename files in bulk\n"
)
(workspace / "logs" / "processed" / "march_summary.md").write_text(
    "March processed: 12 interactions logged, 3 patterns confirmed.\n"
)
(workspace / "context" / "goals" / "personal_bets.md").write_text(
    "Personal bets: AI trading bot, fintech startup, media AI tools.\n"
)

# --- USER.md (existing, partial) ---
(workspace / "USER.md").write_text(
    """# Enzo — User Profile

## Role
Global AI Lead at MediaPlus Group

## Known Interests
- AI tools and demos
- Hackathons

## Goals
- Stay sharp on AI trends
- Build AI-assisted development workflows
- Explore AI trading & fintech
- Participate in hackathons

## Notes
Profile last updated: 2024-03-15
"""
)

# --- Raw interaction logs for the agent to process ---
# These are intentionally messy, unstructured conversation snippets

(workspace / "logs" / "raw" / "interaction_2024-06-01.txt").write_text(
    """Date: 2024-06-01
Enzo shared a link to a Lenny's Newsletter piece about the 'Jobs To Be Done' framework for product marketing.
He said: "This is exactly the mental model I've been missing for positioning our AI products. Saving this to use in the next campaign brief."
Later he asked: "Do you think this applies to B2B SaaS or only consumer?"
He also complained: "Our agency keeps overpromising on AI capabilities to clients — pure AI porn, honestly."
"""
)

(workspace / "logs" / "raw" / "interaction_2024-06-03.txt").write_text(
    """Date: 2024-06-03
Enzo dropped a prompt template he built for rapid competitor analysis using GPT-4.
He wants to use it at the upcoming TechCrunch hackathon next month.
He also shared an idea: "What if we built a tool that auto-generates media briefs from campaign data? I want to prototype this."
He mentioned Sahil Bloom's content as something he finds consistently inspiring — the way Sahil breaks down personal finance and growth frameworks.
"""
)

(workspace / "logs" / "raw" / "interaction_2024-06-05.txt").write_text(
    """Date: 2024-06-05
Enzo shared a second marketing framework — the 'Pirate Metrics (AARRR)' model — and said he uses it to structure all his growth thinking.
He was frustrated again: "I pitched the CMO on an AI content pipeline and she had no idea what prompt engineering even means. Feels like I'm always translating."
He's been asking a lot about how other Global AI Leads at media companies structure their teams.
"""
)

(workspace / "logs" / "raw" / "interaction_2024-06-07.txt").write_text(
    """Date: 2024-06-07
Enzo shared ANOTHER marketing framework — specifically Porter's Five Forces adapted for digital media markets.
He said he's building a 'personal frameworks library' and wants to revisit all of these before the Q3 strategy offsite.
He also shared a GPT-based trading signal prompt he found on Twitter — wants to test it for his personal fintech experiments.
He asked: "Is there a way to backtest this kind of prompt-driven signal against historical data?"
"""
)

(workspace / "logs" / "raw" / "interaction_2024-06-09.txt").write_text(
    """Date: 2024-06-09
Enzo shared a fourth marketing framework — the '4Ps of Marketing' applied to AI product launches.
He's clearly building something systematic here.
He mentioned he hasn't worked on his AI trading project in weeks and feels behind.
He also praised Andrej Karpathy's teaching style as deeply inspiring for how he explains neural nets to non-experts.
"""
)

# --- notes/patterns.md does NOT exist yet — agent must create it ---
# Ensure it doesn't exist
patterns_path = workspace / "notes" / "patterns.md"
if patterns_path.exists():
    patterns_path.unlink()

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")