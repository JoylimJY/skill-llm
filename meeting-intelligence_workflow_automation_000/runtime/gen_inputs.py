import os
import random

random.seed(42)

# Create deeply nested directory structure with distractor files
dirs = [
    "meetings/q3_planning",
    "meetings/archive/2025",
    "meetings/archive/2024",
    "docs/product",
    "docs/engineering",
    "team/profiles",
    "team/schedules",
    "reports/weekly",
    "reports/monthly",
    "templates/old",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files
distractors = {
    "meetings/archive/2025/q1_retro_notes.txt": """Q1 Retrospective - March 2025
What went well: shipping cadence improved
What didn't: too many context switches
Action: reduce WIP limit (no owner assigned)
""",
    "meetings/archive/2025/q2_kickoff.txt": """Q2 Kickoff Notes
- Discussed roadmap items
- Team velocity: 42 points avg
- No clear decisions made
""",
    "meetings/archive/2024/annual_planning.txt": """Annual Planning 2024
Budget approved: $2.1M
Headcount: +3 engineers
Deferred: mobile app rewrite
""",
    "docs/product/roadmap_v2.md": """# Product Roadmap v2
## Themes
- Growth
- Retention
- Platform stability

## Status: DRAFT
""",
    "docs/product/prd_notifications.md": """# PRD: Smart Notifications
Author: Priya Sharma
Status: In Review
Last updated: 2026-01-10
""",
    "docs/engineering/arch_decisions.md": """# Architecture Decision Records
## ADR-001: Use PostgreSQL for primary store
Decision: Approved
## ADR-002: Microservices vs Monolith
Decision: Pending
""",
    "team/profiles/team_roster.txt": """Engineering:
- Marcus Chen (Staff Eng)
- Aisha Okonkwo (Senior Eng)
- Dev Patel (Mid-level Eng)
Product:
- Priya Sharma (PM)
Design:
- Leo Fontaine (Lead Designer)
""",
    "team/schedules/pto_calendar.txt": """PTO Calendar Q3 2026
Marcus Chen: July 14-18
Leo Fontaine: August 4-8
Dev Patel: July 28
""",
    "reports/weekly/week_23.txt": """Week 23 Report
Velocity: 38 pts
Bugs resolved: 12
PRs merged: 27
Blockers: Auth service latency spike
""",
    "reports/monthly/june_summary.txt": """June 2026 Monthly Summary
Revenue: $1.24M MRR
Churn: 2.3%
NPS: 41
New features shipped: 3
""",
    "templates/old/meeting_template_v1.txt": """OLD TEMPLATE - DO NOT USE
Meeting Title:
Date:
Attendees:
Notes:
- 
Action Items:
- 
""",
    "docs/engineering/sprint_24_plan.md": """# Sprint 24 Plan
Start: July 7, 2026
End: July 18, 2026
Goal: Ship notifications v1 + Fix auth latency
Capacity: 48 points
""",
}

for path, content in distractors.items():
    with open(path, "w") as f:
        f.write(content)

# THE MAIN INPUT: Messy, realistic meeting transcript
transcript = """[Recording started]

[00:00:12] Priya Sharma (PM): Okay I think we're all here now, let me just—Marcus can you hear me? 
[00:00:18] Marcus Chen (Staff Eng): Yeah yeah I'm here, had some lag on my end.
[00:00:22] Priya Sharma (PM): Perfect. Alright, so this is our Q3 2026 roadmap planning session. We've got Marcus, Aisha, Dev, Leo, and myself. Should be about an hour. Let's dig in.

[00:00:38] Priya Sharma (PM): So the main topics today: first, we need to finalize the Q3 feature priorities, second we're deciding what to do about the auth service latency issue that's been blocking Dev's team, and third Leo wants to walk us through the new onboarding redesign proposal.

[00:01:05] Aisha Okonkwo (Senior Eng): Before we start—just flagging that the auth latency issue is really urgent, it's actively blocking our integration tests. We need a fix today or the whole CI pipeline stays red.
[00:01:20] Marcus Chen (Staff Eng): Agreed. I'll take ownership of the auth investigation. I can have a root cause analysis done by end of day today.
[00:01:30] Dev Patel (Mid-level Eng): That would unblock me. I've got the integration suite ready to go the moment auth is stable.

[00:01:45] Priya Sharma (PM): Great. Let's mark that as the top priority then. Moving on—Q3 priorities. So I've been talking to sales and the top ask is the smart notifications feature. Customers keep churning because they miss critical alerts. 
[00:02:10] Leo Fontaine (Lead Designer): I finished the notification UI designs last week, they're in Figma. I'll share the link in Slack after this call.
[00:02:22] Aisha Okonkwo (Senior Eng): I reviewed the PRD. The backend work is straightforward. I can own the notifications backend and have it ready for QA this week—probably by Friday July 11th.
[00:02:38] Dev Patel (Mid-level Eng): I'll pick up the frontend implementation once the auth fix lands. Should be able to deliver the frontend component by end of next week, July 18th.

[00:03:00] Priya Sharma (PM): Perfect. What about API rate limiting? That's been on the backlog forever.
[00:03:10] Marcus Chen (Staff Eng): Rate limiting is important but honestly it can wait. When we have time, maybe Q4. It's not blocking anything right now.
[00:03:22] Priya Sharma (PM): Fair enough, let's keep it in the backlog.

[00:03:35] Leo Fontaine (Lead Designer): Okay so the onboarding redesign—I want to walk you through the core idea. We're seeing 40% drop-off in the first 3 minutes of the product. The redesign targets that. I've done user research with 8 participants.
[00:03:55] Priya Sharma (PM): The research sounds compelling. What do you need from engineering?
[00:04:05] Leo Fontaine (Lead Designer): I need someone to review the designs and give me technical feasibility feedback. Soon would be great—ideally this week so we can plan for Q3.
[00:04:18] Marcus Chen (Staff Eng): I can do that. I'll review Leo's onboarding designs and give technical feedback by end of this week.

[00:04:30] Priya Sharma (PM): Great. One thing I didn't see addressed—what about the mobile responsiveness bugs? We had 3 customer complaints last week.
[00:04:42] Aisha Okonkwo (Senior Eng): Oh yeah, those are real. Someone should file proper tickets for those.
[00:04:50] Dev Patel (Mid-level Eng): I can file the mobile bug tickets. I'll get to it eventually, maybe next sprint when things calm down.
[00:05:00] Priya Sharma (PM): Yeah no rush on that one.

[00:05:10] Priya Sharma (PM): Okay so decisions—we're going Q3 with: notifications as top feature, auth fix is P0, and onboarding redesign is on the roadmap pending technical review. Rate limiting pushed to Q4 backlog.
[00:05:30] Marcus Chen (Staff Eng): One thing we didn't fully resolve—should we upgrade the database to Postgres 16? I started looking into it, there are performance gains, but it's a migration and there are risks. I didn't have time to finish the evaluation.
[00:05:50] Priya Sharma (PM): Let's not decide that today. Can you bring a recommendation next week?
[00:06:00] Marcus Chen (Staff Eng): Sure, I'll prepare the Postgres 16 upgrade analysis and bring it to next week's sync.

[00:06:15] Priya Sharma (PM): Alright I think that's everything. Next meeting is Tuesday July 15th at 2pm. Thanks everyone.

[00:06:25] [Recording ended]
"""

with open("meetings/q3_planning/transcript.txt", "w") as f:
    f.write(transcript)

print("Workspace generated successfully.")
print("Key file: meetings/q3_planning/transcript.txt")