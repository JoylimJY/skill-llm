import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ─── 1. Create the career skill auxiliary files (they "already exist" per SKILL.md) ───
career_dir = Path("/root/career")
career_dir.mkdir(parents=True, exist_ok=True)

# decisions.md - auxiliary file (exists, mostly empty template)
(career_dir / "decisions.md").write_text("""\
# Career Decisions Framework

Use this file when guiding major career decisions.

## Process
- Gather full context before advising
- Map all real options (not just binary)
- Weight against confirmed user values

## Anti-patterns
- Answering without context
- Ignoring timing windows
- Prestige capture
""")

# transitions.md
(career_dir / "transitions.md").write_text("""\
# Career Transitions Framework

## Key Warning
Avoid the "grass is greener" trap. Validate push vs pull motivations.

## Steps
1. Clarify what is being moved toward, not just away from
2. Assess transferable strengths
3. Map realistic timelines
""")

# negotiations.md - this is where the agent needs to add guidance
(career_dir / "negotiations.md").write_text("""\
# Salary & Offer Negotiations

## Core Principle
Never accept the first offer.

## Framework

<!-- Personalized negotiation guidance goes here -->

""")

# growth.md
(career_dir / "growth.md").write_text("""\
# Promotions & Development

## Key Trap
Visibility blindness — doing great work no one sees.

## Approach
- Identify sponsors, not just mentors
- Document impact in business terms
""")

# networking.md
(career_dir / "networking.md").write_text("""\
# Building Connections

## Key Trap
Transactional mindset — only reaching out when you need something.

## Principles
- Give before you take
- Invest in weak ties
""")

# ─── 2. Create the messy session notes (the raw input the agent must process) ───
session_notes = """\
=== CLIENT SESSION TRANSCRIPT - Dr. Mara Chen ===
Date: 2024-03-15
Coach: J. Rivera
Session #3

[INTAKE NOTES]
Client background: Research Scientist (Computational Biology), BioNovaTech
Tenure: 6 years at current employer
Current comp: $118,000 base + 12% bonus
Education: PhD Molecular Biology, MIT

[SESSION DIALOGUE - EXCERPTS]

Coach: What draws you to product management at HealthSpark?
Mara: I genuinely love the idea of shaping products that reach patients directly. The science is great but I've realized I get more energy from the cross-functional coordination work than the bench work itself. I've been leading the internal tool rollout for our lab informatics system and that's been the most alive I've felt at work in two years.

Coach: You mentioned autonomy last session. Is that still a priority?
Mara: Absolutely, yes. I said it before and I'm even more sure now — I'd take a pay cut for real ownership over my work. The micromanagement here has been exhausting.

Coach: Tell me about the HealthSpark offer.
Mara: They came in at $130,000. I was surprised, honestly. But my recruiter friend says the market for someone with my biotech domain knowledge going into PM is probably $145-155k range at a Series B like them. I'm nervous about negotiating though.

Coach: What's holding you back from negotiating?
Mara: I guess I feel like… I've been at BioNovaTech six years, I know this domain cold, and starting over feels risky. But I also know that's probably not a good reason to just accept what they offer.

Coach: What's your location situation?
Mara: I need to stay in Boston. My partner's practice is here, kids are in school here. Non-negotiable.

Coach: What does success look like in 3 years?
Mara: Leading a product team. Not necessarily a huge team, but meaningful ownership of a product line. I've said that both times we've talked about goals.

Coach: Any concerns about the HealthSpark role itself?
Mara: The PM role title is "Associate PM" which feels junior given my background. But the hiring manager said I could be re-leveled at 6 months if I hit milestones. The equity package is also unclear — they mentioned options but gave no specifics.

[END OF SESSION EXCERPTS]

[COACH POST-SESSION NOTES]
- Autonomy priority: mentioned explicitly in session 2 AND confirmed today with "even more sure now" + explicitly agreed
- Location Boston: stated as non-negotiable, confirmed by client
- Goal to lead team: stated in session 1, repeated today (session 3) — client said "I've said that both times"
- Strength: cross-functional coordination — observed behavior (led informatics rollout), client self-identified
- Strength: biotech domain knowledge — recruiter + hiring manager both flagged it, client corroborated
- Sunk cost risk flagged: 6 years at BioNovaTech comment, client self-caught it
- Salary negotiation needed: current offer $130k, market $145-155k, client hesitant
- Equity terms unclear — must be addressed in negotiation
- Title leveling risk — Associate PM vs experience level

[ACTION ITEMS]
- Set up career tracking profile for Mara
- Prepare negotiation strategy for HealthSpark offer
"""

(workspace / "session_notes_mara_chen.txt").write_text(session_notes)

# ─── 3. Create distractor files to test contextual awareness ───

# Distractor: old unrelated client notes
distractor_dir = workspace / "archive" / "old_clients" / "2023"
distractor_dir.mkdir(parents=True, exist_ok=True)

(distractor_dir / "client_james_t_notes.txt").write_text("""\
James Turner - Software Engineer
Goal: Senior Engineer promotion
Strength: backend systems
Note: Promoted Q4 2023. Case closed.
""")

(distractor_dir / "client_priya_s_notes.txt").write_text("""\
Priya Sharma - Marketing Manager
Negotiated offer at Fintech startup
Outcome: +$22k increase
""")

(distractor_dir / "template_generic.txt").write_text("""\
Generic client template v1
Values: [fill in]
Strengths: [fill in]
DO NOT USE - deprecated format
""")

# Distractor: a fake memory.md that belongs to a DIFFERENT client (should not be used)
old_memory_dir = workspace / "archive" / "old_clients" / "memory_backups"
old_memory_dir.mkdir(parents=True, exist_ok=True)
(old_memory_dir / "memory_james.md").write_text("""\
## Values
promotion over salary (confirmed)

## Strengths
backend: expert (stated)

## Constraints
remote only (confirmed)

## Context
senior engineer 7 years (stated)

## Goals
staff engineer (confirmed)
""")

# Distractor: salary benchmarks file
benchmarks_dir = workspace / "resources" / "market_data"
benchmarks_dir.mkdir(parents=True, exist_ok=True)
(benchmarks_dir / "pm_salary_2024.csv").write_text("""\
role,level,location,p25,p50,p75,p90
Product Manager,Associate,Boston,115000,128000,142000,160000
Product Manager,Senior,Boston,145000,162000,180000,205000
Product Manager,Principal,Boston,180000,200000,225000,255000
""")

(benchmarks_dir / "biotech_pm_premium.txt").write_text("""\
Biotech-to-PM transition candidates with domain PhDs command 10-18% premium
over standard PM candidates at Series B/C healthtech firms (2024 data).
""")

# Distractor: coach's personal notes unrelated to Mara
coach_notes_dir = workspace / "coach_notes" / "internal"
coach_notes_dir.mkdir(parents=True, exist_ok=True)
(coach_notes_dir / "methodology_notes.txt").write_text("""\
Remember: never project your own values onto clients.
The "grass is greener" trap is common in transitions.
Always check: push vs pull motivation.
""")

(coach_notes_dir / "billing_q1_2024.txt").write_text("""\
Q1 Invoices:
- James Turner: $2,400
- Priya Sharma: $1,800
- Mara Chen: $3,200 (ongoing)
Total: $7,400
""")

# Distractor: fake career framework doc that uses WRONG format (trap for agent)
(workspace / "draft_frameworks" / "career_profile_v0_DRAFT.md").mkdir_p if False else None
draft_dir = workspace / "draft_frameworks"
draft_dir.mkdir(parents=True, exist_ok=True)
(draft_dir / "career_profile_v0_DRAFT.md").write_text("""\
# OLD DRAFT FORMAT - DO NOT USE

Client Name:
Top Values: [list them]
Key Strengths: [list them]  
Location: [city]
Career Goal: [one line]
Confidence: high/medium/low

NOTE: This format was replaced. See current system for correct format.
""")

# Distractor: another messy doc about negotiation (generic, not personalized)
(workspace / "resources" / "negotiation_generic_tips.txt").write_text("""\
Generic Negotiation Tips:
1. Do your research
2. Know your worth
3. Don't be the first to name a number
4. Get everything in writing
5. Consider the full package (equity, PTO, title)
""")

# Distractor: empty placeholder
(workspace / "resources" / "client_template_EMPTY.md").write_text("")

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f}")
for f in sorted(Path("/root/career").rglob("*")):
    if f.is_file():
        print(f"  {f}")