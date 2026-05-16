import os
import random
import json

random.seed(42)

WORKSPACE = "/workspace"

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "SKILL.md",                              # skill entry point (file, not dir)
    "references",
    "internal/research",
    "internal/drafts",
    "internal/archive",
    "internal/metrics",
    "internal/crm_notes",
    "internal/social",
    "competitors/raw",
    "competitors/processed",
    "opportunities/threads",
    "opportunities/board_snapshots",
    "opportunities/flagged",
    "reports",
]
for d in dirs:
    full = os.path.join(WORKSPACE, d)
    if not full.endswith(".md"):
        os.makedirs(full, exist_ok=True)

# ── SKILL.md ─────────────────────────────────────────────────────────────────
skill_md = """---
name: hubspot-community
description: Research HubSpot Community profiles, boards, unanswered threads, leaderboards, and Community Champion opportunities to identify visibility patterns and produce non-spam participation plans, reply drafts, and scorecards. Use when the user mentions HubSpot Community, Community Champions, Community Champion Opportunities, unanswered HubSpot threads, profile signals, leaderboards, earning visibility, or wants a HubSpot Community playbook or skill.
---

# HubSpot Community

Use this skill when the task is about winning visibility on HubSpot Community through higher-quality participation, not automation.

## Guardrails

- Do not automate posting, liking, upvoting, commenting, or any spammy behavior.
- Prefer public profile, board, and leaderboard pages. If a page needs login, say what is blocked and continue with public sources.
- When Champion guidance is relevant, read [references/champion-opportunities.md](references/champion-opportunities.md).
- If drafting content that may be AI-assisted, note that Champion guidance asks for disclosure and accuracy review before publishing.

## Default workflow

1. Clarify the objective.
   - Common goals: competitor teardown, daily opportunity scan, reply drafting, leaderboard benchmarking, Champion opportunity review.
2. Gather profile signals.
   - Use `https://community.hubspot.com/t5/user/viewprofilepage/user-id/<id>`.
   - Capture member-since date, solutions, replies, upvotes received, ideas, badges, bio, and visible activity.
   - Review the `recent`, `Most Upvotes`, and `Accepted Solutions` tabs.
   - Sample at least 3 recent threads and 3 high-signal contributions.
3. Gather current opportunity sources.
   - Inspect the target boards directly.
   - Use unanswered-thread shortcuts from [references/champion-opportunities.md](references/champion-opportunities.md) instead of relying on flaky board filters.
   - Review the Community Champion Opportunities board when the user cares about points, visibility, or official priorities.
4. Analyze what is working.
   - Look for response speed, board mix, answer structure, follow-up behavior, accepted solutions, and recurring themes.
   - Separate durable patterns from one-off campaign prompts.
5. Produce an actionable output.
   - Default report sections: `Target activity`, `Opportunities today`, `Suggested replies/posts`, and `Progress scorecard`.
   - If access is blocked, add a short `Blocked / data limits` note and give the best next actions.

## What to optimize for

- Prioritize fresh threads with clear business consequences, usually under 48 hours old and with low reply counts.
- Higher quality beats higher volume. Strong replies usually include:
  - direct recommendation
  - rationale or tradeoff
  - concrete implementation steps
  - validation or fallback path
- Focus first on boards where operators need real help, for example CRM, workflows, reporting, sales email, and high-intent marketing questions.
- When benchmarking a strong competitor, note whether they:
  - answer quickly
  - simplify decisions
  - stay in-thread for follow-up
  - convert replies into accepted solutions
  - use signatures or calls to mark the answer as a solution

## HubSpot-specific sources

- Profile pages for signal collection
- Board homepages for recent questions
- Unanswered topic pages from the Champion shortcuts reference
- Community Champion Opportunities board for official visibility and point incentives
- Community leaderboard for benchmarking recognized contributors

## Output patterns

- For competitor analysis: compare board focus, response shape, accepted-solution behavior, and visible brand signals.
- For daily planning: recommend a small number of high-conviction replies and one thought-leadership post, not broad activity quotas.
- For draft generation: write replies that are specific enough to be useful, but never submit them automatically.
"""

with open(os.path.join(WORKSPACE, "SKILL.md"), "w") as f:
    f.write(skill_md)

# ── references/champion-opportunities.md ─────────────────────────────────────
os.makedirs(os.path.join(WORKSPACE, "references"), exist_ok=True)
champion_md = """# Champion Opportunities

Durable notes from the official HubSpot Community Champion Opportunities board, reviewed on March 9, 2026.

## What this board is for

- HubSpot uses this board to publish monthly Community Champion tasks.
- The stated goals are thought leadership, personal brand growth, networking, and expertise sharing.
- Points are awarded for completed tasks.

## Program rules and best practices

- The Community Champions program is open to Community members with an active profile.
- New opportunities are typically posted monthly and usually stay active for about one month.
- To receive points, participants are asked to comment on the opportunity thread with proof, usually a link or an `I completed this` note.
- The board explicitly suggests using filters to find opportunity types such as `Social Amplification` and `External Forums`.
- The board advises responsible generative AI use: disclose AI assistance and verify accuracy before posting.
- HubSpot also links to separate Community blogger guidelines for members who want to publish blog content.

## Opportunity types seen on the board

- `Community`
- `Social Amplification`
- `Content Engagement`
- `User-Generated Content`

Use these categories as an official signal of what HubSpot is currently rewarding. Do not treat them as a reason to spam low-value activity.

## Current themes seen in March 2026

- HUG leadership applications
- HubSpot Academy bootcamps
- LinkedIn sharing around Academy and agent updates
- Data Hub course completion and takeaway sharing
- AI agent configuration examples
- Workflow showcases and selling-profile showcases

These are useful for topic discovery and tone calibration. They are weaker as direct visibility levers than high-quality answers on real customer questions.

## Leaderboard signal

The board includes a public Community Champions leaderboard. On the reviewed page, the top visible names were:

- `danmoyle`
- `DarrenScottUK`
- `SNigam`
- `Jigar_Thakker`
- `himanshurauthan`

Use the leaderboard to choose benchmark profiles, then inspect their public profile pages and recent activity directly.

## Evergreen opportunity post

HubSpot maintains a durable post with direct shortcuts to unanswered questions:

- `https://community.hubspot.com/t5/Community-Champion-Opportunities/Can-you-answer-these-questions-on-the-HubSpot-Community/ba-p/1090142`

This is more reliable than trying to force board UI filters from a browser automation session.

## Unanswered-thread shortcuts

### English

- All unanswered posts:
  - `https://community.hubspot.com/t5/forums/unansweredtopicspage/node-display-id/category:hubspot_community_en`
- Marketing Hub:
  - `https://community.hubspot.com/t5/forums/unansweredtopicspage/node-display-id/category:marketing`
- Sales Hub:
  - `https://community.hubspot.com/t5/forums/unansweredtopicspage/node-display-id/category:sales`
- Service Hub:
  - `https://community.hubspot.com/t5/forums/unansweredtopicspage/node-display-id/category:service_hub`
- Developers:
  - `https://community.hubspot.com/t5/forums/unansweredtopicspage/node-display-id/category%3Adevelopers/page/1`

### Other languages

- French:
  - `https://community.hubspot.com/t5/forums/unansweredtopicspage/node-display-id/category:hubspot_community_fr`
- Spanish:
  - `https://community.hubspot.com/t5/forums/unansweredtopicspage/node-display-id/category:hubspot_community_es`
- Portuguese:
  - `https://community.hubspot.com/t5/forums/unansweredtopicspage/node-display-id/category:hubspot_community_pt`
- German:
  - `https://community.hubspot.com/t5/forums/unansweredtopicspage/node-display-id/category:hubspot_community_de`
- Japanese:
  - `https://community.hubspot.com/t5/forums/unansweredtopicspage/node-display-id/category:hubspot_community_jp`

## How to use this board in practice

- Use it to find official HubSpot visibility incentives and current themes.
- Use the unanswered-thread shortcuts to find live answer opportunities.
- Use the leaderboard to choose benchmark contributors.
- Prefer durable, useful replies over points-chasing. The strongest long-term visibility signal is still accepted solutions on real user questions.
"""

with open(os.path.join(WORKSPACE, "references", "champion-opportunities.md"), "w") as f:
    f.write(champion_md)

# ── DISTRACTOR FILES ──────────────────────────────────────────────────────────

# 1. A stale competitor notes file with wrong structure
with open(os.path.join(WORKSPACE, "competitors/raw", "danmoyle_old_notes.txt"), "w") as f:
    f.write("""OLD NOTES - DO NOT USE (2024)
danmoyle profile scraped manually
solutions: 89 (stale)
replies: 312 (stale)
These numbers are from last year. Profile has changed significantly.
Last updated: January 2024
""")

# 2. A partial profile dump in wrong JSON format
with open(os.path.join(WORKSPACE, "competitors/raw", "profile_dump_broken.json"), "w") as f:
    json.dump({
        "user": "SNigam",
        "partial_data": True,
        "solutions": "unknown",
        "note": "scrape failed, captcha encountered"
    }, f, indent=2)

# 3. Archive of old opportunity board scrape - outdated
with open(os.path.join(WORKSPACE, "internal/archive", "opportunity_board_2025_01.txt"), "w") as f:
    f.write("""ARCHIVED - January 2025 Champion Opportunities
Tasks that month: LinkedIn post, Academy badge share
Points available: 50 per task
STATUS: EXPIRED - do not use for current planning
""")

# 4. Misleading "best practices" doc with wrong reply structure
with open(os.path.join(WORKSPACE, "internal/research", "reply_template_wrong.md"), "w") as f:
    f.write("""# Reply Template (DRAFT - NOT APPROVED)
A good reply should:
1. Be friendly and empathetic
2. Include a relevant link
3. End with a question to keep the thread going

NOTE: This was drafted before the current guidelines. Use with caution.
""")

# 5. Metrics file with red-herring KPIs
with open(os.path.join(WORKSPACE, "internal/metrics", "vanity_metrics.csv"), "w") as f:
    f.write("""metric,value,note
total_posts_last_month,47,includes low-value replies
profile_views,892,unverified
likes_given,230,not a useful signal per new guidelines
followers_gained,12,platform does not show follower counts
""")

# 6. CRM notes distractor
with open(os.path.join(WORKSPACE, "internal/crm_notes", "hubspot_contacts.txt"), "w") as f:
    f.write("""Internal CRM pipeline notes - Q1 2026
Prospect A: interested in HubSpot onboarding
Prospect B: asked about workflow automation
These are sales pipeline notes, not community insights.
""")

# 7. Social media calendar - distractor
with open(os.path.join(WORKSPACE, "internal/social", "linkedin_calendar_feb.md"), "w") as f:
    f.write("""# LinkedIn Post Calendar - February 2026
Week 1: Share Academy certification post
Week 2: Repost HubSpot product update
Week 3: Write original thought-leadership post
Week 4: Engage on 3 partner posts

This calendar was made independently of community strategy.
""")

# 8. Competitors processed folder - stub
with open(os.path.join(WORKSPACE, "competitors/processed", "README_stub.txt"), "w") as f:
    f.write("This folder is for processed competitor analysis outputs. Currently empty.\n")

# 9. Thread snapshots - messy raw HTML-like dump (distractor)
with open(os.path.join(WORKSPACE, "opportunities/board_snapshots", "crm_board_raw_dump.txt"), "w") as f:
    f.write("""<raw_scrape timestamp="2026-03-08T09:00:00Z">
Thread: "Contact properties not syncing after workflow trigger"
Posted: 2026-03-07 14:22 UTC
Replies: 0
Board: CRM

Thread: "How do I set up a deal stage automation?"
Posted: 2026-03-06 09:11 UTC
Replies: 3
Board: CRM

Thread: "Bulk import failing with UTF-8 encoding error"
Posted: 2026-03-08 06:45 UTC
Replies: 0
Board: CRM

Thread: "Custom report not showing expected records"
Posted: 2026-03-05 17:30 UTC
Replies: 7
Board: Reporting

Thread: "Workflow enrollment criteria not triggering correctly"
Posted: 2026-03-08 11:15 UTC
Replies: 1
Board: Workflows
</raw_scrape>""")

# 10. Flagged opportunities file - partial, unstructured
with open(os.path.join(WORKSPACE, "opportunities/flagged", "march_flagged.txt"), "w") as f:
    f.write("""Flagged by team member on 2026-03-08:
- Some thread about email deliverability (Sales Hub) - posted yesterday, no replies
- Workflow question about re-enrollment (Workflows board) - 0 replies, unclear date
- CRM duplicate merging - 2 replies already, maybe skip
No URLs captured. Notes incomplete.
""")

# 11. Profile data for the BENCHMARK competitor (DarrenScottUK) - provided as research input
# This is the KEY input file the agent must use
with open(os.path.join(WORKSPACE, "competitors/raw", "DarrenScottUK_profile_research.md"), "w") as f:
    f.write("""# Profile Research: DarrenScottUK
## Source
Public profile page: https://community.hubspot.com/t5/user/viewprofilepage/user-id/DarrenScottUK
Reviewed: March 9, 2026

## Basic Signals
- Member since: March 2018
- Accepted Solutions: 412
- Total replies: 1,847
- Upvotes received: 3,204
- Ideas submitted: 14
- Badges: HubSpot Champion (2023, 2024, 2025), Super Contributor, Top Solution Author
- Bio: "HubSpot RevOps consultant | UK | Helping operators get more from HubSpot workflows, CRM, and reporting"

## Recent Activity (last 30 days)
- Answered 23 threads
- 9 accepted as solutions
- Boards: CRM (8 replies), Workflows (7 replies), Reporting (5 replies), Sales Hub (3 replies)
- Avg time to first reply: ~3.1 hours
- Follow-up replies (same thread): 11 out of 23 threads

## Sampled Recent Threads
1. "How to use calculated properties in a workflow branch?"
   - Board: Workflows
   - Reply: Gave step-by-step setup, named the specific property type limitation, offered workaround via custom coded action
   - Accepted solution: YES
   - Follow-up: 2 additional replies to OP clarification questions

2. "Deal pipeline report showing duplicates"
   - Board: Reporting
   - Reply: Identified the cross-object join issue, gave filter fix, mentioned the known bug in custom report builder
   - Accepted solution: YES
   - Follow-up: 1 reply confirming resolution

3. "Contact-based workflow not enrolling re-entered contacts"
   - Board: Workflows
   - Reply: Explained re-enrollment criteria checkbox location, noted the 'AND' vs 'OR' filter logic gotcha
   - Accepted solution: NO (OP never marked but commented it worked)
   - Follow-up: YES

## Sampled High-Signal Contributions (Most Upvotes tab)
1. "Master guide: HubSpot workflow troubleshooting checklist" - 89 upvotes
2. "When to use lists vs active lists in segmentation" - 67 upvotes  
3. "CRM data hygiene playbook for RevOps teams" - 54 upvotes

## Behavioral Patterns
- Always gives a direct answer in the first paragraph
- Structures replies: recommendation → why it works → exact steps → what to check if it fails
- Ends most replies with: "Let me know if you hit a snag — happy to dig in further"
- Does NOT use a promotional signature
- Occasionally links to his own thought-leadership posts when directly relevant

## Access notes
- Recent tab: fully public
- Most Upvotes tab: fully public
- Accepted Solutions tab: fully public
""")

# 12. Unanswered threads input data for today's opportunity scan
with open(os.path.join(WORKSPACE, "opportunities/threads", "unanswered_march09_2026.md"), "w") as f:
    f.write("""# Unanswered Threads Snapshot - March 9, 2026 ~10:00 UTC
## Source
Pulled from unanswered-thread shortcut URLs per champion-opportunities.md

---
### Thread 1
**Title:** "Workflow not triggering on contact property change - date field"
**Board:** Workflows (category:marketing)
**Posted:** 2026-03-09 06:14 UTC (3h 46m ago)
**Replies:** 0
**OP summary:** Contact property "Last Activity Date" changes daily but enrollment trigger never fires. Using property-based enrollment. No errors shown.

---
### Thread 2
**Title:** "Sales sequence email showing wrong sender name after rep reassignment"  
**Board:** Sales Hub (category:sales)
**Posted:** 2026-03-09 02:30 UTC (7h 30m ago)
**Replies:** 0
**OP summary:** Rep was reassigned mid-sequence. Emails now show old rep's name in From field even though contact owner updated.

---
### Thread 3
**Title:** "Custom report: revenue by original source drill-down not working"
**Board:** Reporting
**Posted:** 2026-03-08 18:45 UTC (15h 15m ago)
**Replies:** 0
**OP summary:** Revenue attribution report built in custom report builder. Original source drill-down shows blank for ~30% of contacts. Contacts do have original source set in CRM.

---
### Thread 4
**Title:** "How do I add HubSpot tracking code to a Webflow site?"
**Board:** Marketing Hub (category:marketing)
**Posted:** 2026-03-08 09:00 UTC (25h ago)
**Replies:** 2
**OP summary:** Basic tracking code install question, has 2 replies already.

---
### Thread 5
**Title:** "API: batch upsert contacts returning 400 on custom properties"
**Board:** Developers (category:developers)
**Posted:** 2026-03-09 08:55 UTC (1h 5m ago)
**Replies:** 0
**OP summary:** Using v3 contacts API batch upsert. Works for standard properties, fails with 400 error on custom internal name. Properties exist and are correct type.

---
### Thread 6
**Title:** "Deal stage changed webhook not firing for pipeline 2"
**Board:** Developers
**Posted:** 2026-03-07 14:00 UTC (44h ago)
**Replies:** 1
**OP summary:** Webhook set up for deal stage change. Works on default pipeline, not on second custom pipeline. App subscription settings look correct.

---
### Thread 7
**Title:** "Best CRM for a small team - HubSpot vs Salesforce?"
**Board:** CRM
**Posted:** 2026-03-09 07:30 UTC (2h 30m ago)
**Replies:** 3
**OP summary:** Opinion/comparison question, 3 replies already.

---
### Thread 8
**Title:** "Contact merge duplicates - losing custom property values"
**Board:** CRM
**Posted:** 2026-03-08 22:10 UTC (11h 50m ago)
**Replies:** 0
**OP summary:** When merging duplicate contacts, one custom property value is always overwritten with blank. Merge winner selected correctly. Issue is reproducible.
""")

# 13. Internal draft scratchpad - noise
with open(os.path.join(WORKSPACE, "internal/drafts", "random_ideas.txt"), "w") as f:
    f.write("""Random ideas for community participation:
- Post more
- Comment on everything
- Get 100 likes this month
- Ask HubSpot employees to follow me

NOTE: These ideas were written before strategy review. Likely violate current guidelines.
""")

# 14. Old leaderboard screenshot description - wrong names (trap)
with open(os.path.join(WORKSPACE, "internal/research", "leaderboard_old.txt"), "w") as f:
    f.write("""Leaderboard captured December 2024 (OUTDATED):
1. JohnDoeHS
2. MarketingMaven99  
3. CRMGuru2024
4. DarrenScottUK
5. WorkflowWizard

WARNING: This is from December 2024. Use champion-opportunities.md for current leaderboard names.
""")

# 15. Opportunity types wrong list (trap for agents using outdated data)
with open(os.path.join(WORKSPACE, "internal/archive", "old_opportunity_types.txt"), "w") as f:
    f.write("""Old Champion Opportunity categories (2023):
- Peer-to-Peer Help
- Blog Submission  
- Video Content
- Event Participation

These categories were retired. See current champion-opportunities.md for active types.
""")

print("Workspace scaffold created successfully.")
print(f"Files created in {WORKSPACE}")