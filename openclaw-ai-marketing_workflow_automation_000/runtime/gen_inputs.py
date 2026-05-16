import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── directory scaffold ────────────────────────────────────────────────────────
dirs = [
    "day_notes",
    "day_notes/raw",
    "day_notes/raw/social",
    "day_notes/raw/blog",
    "day_notes/raw/email",
    "day_notes/raw/research",
    "marketing-assets",
    "marketing-assets/hooks",
    "marketing-assets/proof",
    "references",
    "archive/2024-Q1",
    "archive/2024-Q2",
    "ops/mission_control",
    "ops/receipts",
    "team/profiles",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files (≥10) ────────────────────────────────────────────────────
distractors = {
    "marketing-assets/hooks/hooks_library.txt": """\
Hook: "Stop losing leads to your competitors."
Hook: "The API that pays for itself in week one."
Hook: "Your devs hate context switching. We fixed that."
Hook: "99.9% uptime or we refund the month."
""",
    "marketing-assets/proof/case_studies.txt": """\
Acme Corp: 3x pipeline in 60 days using DevBridge API.
Globex LLC: Reduced onboarding time from 14 days to 2.
Initech: $240k ARR attributed to lifecycle email series.
""",
    "marketing-assets/angles.md": """\
# Primary Angles
- Speed to value: first integration < 15 min
- Cost displacement: replaces 2 FTEs of manual work
- Risk reversal: 30-day money-back
""",
    "marketing-assets/cta_library.txt": """\
CTA_1: Start free trial — no card required
CTA_2: Book a 20-min demo
CTA_3: Read the integration guide
CTA_4: Join 4,000+ dev teams
""",
    "references/system-map.md": """\
# System Map (stub)
See role-contracts.md for per-lane detail.
""",
    "references/role-contracts.md": """\
# Role Contracts (stub)
Each lane owner signs off with a dated receipt and truth state.
""",
    "references/daily-loop.md": """\
# Daily Loop (stub)
1. Research  2. Packaging  3. Publishing  4. QA  5. Truth Gate  6. MC Refresh
""",
    "references/open-source-packaging.md": """\
# Open-Source Packaging (stub)
Remove private secrets. Keep role definitions and receipt discipline.
""",
    "archive/2024-Q1/campaign_summary.txt": """\
Q1 2024: 14 blog posts published. 3 lifecycle sequences launched. 2 viral threads.
""",
    "archive/2024-Q2/campaign_summary.txt": """\
Q2 2024: 38 blog posts published. Jenny cohort size 1,200. Elon thread avg 40 replies.
""",
    "team/profiles/team_roster.txt": """\
Hunter  — Research
JK      — Packaging
Elon    — Social
Tony    — Blog
Jenny   — Lifecycle/Email
Peter   — Blog QA
Karen   — Truth Gate
MC      — Mission Control
""",
    "ops/mission_control/previous_day.md": """\
# Mission Control — Previous Day
All lanes DELIVERED. Tony hit 12/12. Jenny cohort fully delivered. Peter PASS x12.
""",
    "ops/receipts/sample_receipt_format.txt": """\
RECEIPT FORMAT:
  Lane: <name>
  Date: YYYY-MM-DD
  State: <truth_state>
  Evidence: <URL or artifact reference>
""",
}
for rel_path, content in distractors.items():
    (workspace / rel_path).write_text(content)

# ── today's date context ──────────────────────────────────────────────────────
today = "2025-07-14"

# ── RAW NOTES — intentionally messy, incomplete, ambiguous ───────────────────

(workspace / "day_notes/raw/research/hunter_notes.txt").write_text(f"""\
=== Hunter Field Notes {today} ===

Reddit scan done — r/devtools, r/SaaS, r/startups
Top pain: "We can't afford to hire another eng to maintain webhook infra"
Top pain: "Rate limiting is murdering our demo reliability"
X pain scan: searched #APIFirst — 23 relevant posts found, 2 viral (>200 engagements each)
Viral learning: Thread by @indiedev_jane got 410 likes — topic: "10 signs your API docs are lying to you"

Pain Map updated in Notion (not synced to marketing-assets yet)
Intel Pack: compiled in Google Doc, link shared in Slack
""")

(workspace / "day_notes/raw/research/jk_notes.txt").write_text(f"""\
JK packaging notes — {today}

Consumed Hunter intel from Slack link. Used hooks_library.txt + case_studies.txt.
Produced content brief for Elon: 3 thread angles, 2 punchy one-liners suggested.
Produced blog angle brief for Tony: keyword "webhook reliability", "API rate limiting".
No formal packaging receipt dropped. Will handle tomorrow.
""")

(workspace / "day_notes/raw/social/elon_notes.txt").write_text(f"""\
ELON SOCIAL — {today}

Drafted 2 posts for X.
  Post 1: "Webhook infra is expensive. Our API makes it cheap. Try free." — one-liner
  Post 2: "Rate limiting shouldn't kill your demos." — one-liner
Posted both. No URLs saved. Did not do ASSET_CHECK.
LinkedIn: skipped today due to time.
Visibility: not confirmed publicly.
""")

(workspace / "day_notes/raw/blog/tony_notes.txt").write_text(f"""\
TONY BLOG — {today}

Published posts today:
  1. "How to Solve Webhook Reliability in 2025" — devbridge.io/blog/webhook-reliability-2025
  2. "API Rate Limiting: A Developer's Guide" — devbridge.io/blog/api-rate-limiting-guide
  3. "Top 5 API Monitoring Tools" — devbridge.io/blog/top-5-api-monitoring
  4. "Webhook vs Polling: Which Is Right for You?" — devbridge.io/blog/webhook-vs-polling
  5. "How DevBridge Cut Our Integration Time" — devbridge.io/blog/devbridge-integration-time
  6. "REST API Best Practices 2025" — devbridge.io/blog/rest-api-best-practices
  7. "GraphQL vs REST: Real-World Comparison" — devbridge.io/blog/graphql-vs-rest
  8. "API Security Checklist for Startups" — devbridge.io/blog/api-security-checklist

Total: 8 published today.
Keyword targets hit: webhook reliability, API rate limiting, API monitoring.
""")

(workspace / "day_notes/raw/email/jenny_notes.txt").write_text(f"""\
Jenny lifecycle — {today}

Cohort selected: 340 trial users who hit day-7 with no conversion.
Email: "You've built something — let's make it work" — re-engagement sequence step 2.
Send attempted at 10:42 AM via SendGrid.
No delivery confirmation received yet from platform.
ASSET_CHECK: not completed.
Writeback: pending — will update cohort log when confirmation arrives.
""")

(workspace / "day_notes/raw/blog/peter_notes.txt").write_text(f"""\
PETER QA — {today}

Reviewed Tony's blog list.
Spot-checked 3 posts for live status:
  - Checked "webhook reliability" post — appeared to load (no URL saved, done in browser)
  - "API rate limiting guide" — looked live
  - "GraphQL vs REST" — not checked yet
Did not do full 8-post verification. No formal QA receipt dropped.
Flagging: only 8 posts from Tony today (expected more).
""")

(workspace / "day_notes/raw/research/karen_notes.txt").write_text(f"""\
KAREN TRUTH GATE — {today}

Reviewing lane claims:

Hunter: Research notes exist in Slack/Notion — NOT synced to marketing-assets. Intel Pack not in durable repo. INCOMPLETE.
JK: No receipt. Brief shared informally. INCOMPLETE.
Elon: Posts claimed — no post URLs provided, no ASSET_CHECK, no visibility proof. Cannot verify. INCOMPLETE.
Tony: 8 published (self-reported). Target is ???. Need to check what the standard daily target is.
Jenny: "Send attempted" logged. No delivery confirmation. Not the same as delivered.
Peter: Spot-checked 3 of 8. No formal receipt. No live URLs saved. QA not closeable.
Mission Control: Not updated today yet.
""")

(workspace / "day_notes/raw/research/mc_notes.txt").write_text(f"""\
MISSION CONTROL SCRATCH — {today}

Collected status from lanes. Partial day.
Summary (rough):
  - Hunter: notes exist, assets not updated
  - JK: brief drafted, no receipt
  - Elon: posted something, unverified
  - Tony: 8 blogs published
  - Jenny: send in progress
  - Peter: partial QA
  - Karen: auditing now
  - MC: this doc

Will formalize later.
""")

# ── a misleading "summary" that uses wrong vocabulary ─────────────────────────
(workspace / "day_notes/informal_summary.txt").write_text(f"""\
Rough EOD summary {today} — DO NOT use for official reporting

Overall: pretty good day. Most things done. Tony got 8 out of... something.
Jenny sent emails. Elon tweeted. Peter checked some posts.
Status: partial / mostly done / pending cleanup.
""")

print("Workspace generated successfully.")