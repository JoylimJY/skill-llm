import os
import random
import json

random.seed(42)

WORKSPACE = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "references",
    "ideas/raw_notes",
    "ideas/market_research",
    "competitors/scraped",
    "competitors/analysis",
    "internal/ops",
    "internal/finance",
    "drafts/old_pitches",
    "drafts/rejected",
    "assets/logos",
    "assets/copy",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── Reference template stubs (exist but are EMPTY/incomplete on purpose) ─────
# The agent must produce real content that conforms to the SKILL.md schema,
# not just copy-paste these stubs.

references = {
    "references/experiment-brief.md": """\
# Experiment Brief Template
<!-- Fill in: who, pain, promise, channel, metric, threshold -->
""",
    "references/landing-page-checklist.md": """\
# Landing Page Checklist
- [ ] Headline
- [ ] CTA
- [ ] Social proof
- [ ] Analytics snippet
""",
    "references/seo-10-page-plan.md": """\
# SEO 10-Page Plan Template
<!-- Define money pages and support pages -->
""",
    "references/weekly-loop.md": """\
# Weekly Loop Template
<!-- Double down / Kill / Add experiment -->
""",
}
for path, content in references.items():
    with open(os.path.join(WORKSPACE, path), "w") as f:
        f.write(content)

# ── Distractor files (noise to test contextual awareness) ───────────────────

# 1. Raw unstructured idea notes
with open(os.path.join(WORKSPACE, "ideas/raw_notes/brain_dump.txt"), "w") as f:
    f.write("""\
Vet clinics are overwhelmed. Lots of no-shows. SMS reminders don't work well.
Maybe build something? Could be SaaS. Pet owners forget. Clinics lose money.
Competition: PetDesk, VetHero, some others. But expensive and complex.
Could do something simpler?
Tried calling 5 clinic owners in Austin - all complained about no-shows.
""")

# 2. Market size spreadsheet dump
with open(os.path.join(WORKSPACE, "ideas/market_research/market_size_notes.csv"), "w") as f:
    f.write("""\
segment,clinics_us,avg_revenue,pain_score
independent_vet_clinics,28000,480000,9
corporate_chains,4000,2100000,3
mobile_vet,1200,190000,7
""")

# 3. Competitor notes
with open(os.path.join(WORKSPACE, "competitors/analysis/competitor_matrix.md"), "w") as f:
    f.write("""\
| Tool        | Price/mo | No-show Feature | SMS | Complexity |
|-------------|----------|-----------------|-----|------------|
| PetDesk     | $299     | Yes             | Yes | High       |
| VetHero     | $199     | Partial         | Yes | Medium     |
| Simple SMS  | $49      | No              | Yes | Low        |

Gap: no simple, affordable no-show reducer for independent clinics under $99/mo.
""")

# 4. Old rejected pitch deck notes
with open(os.path.join(WORKSPACE, "drafts/old_pitches/pitch_v1_notes.txt"), "w") as f:
    f.write("""\
REJECTED: Too broad. We tried to build for all healthcare, not just vets.
Feedback from YC office hours: narrow the wedge. Pick one vertical.
Revenue after 3 months: $0. Signups: 12 (friends).
""")

# 5. Finance distractor
with open(os.path.join(WORKSPACE, "internal/finance/burn_rate_q1.json"), "w") as f:
    json.dump({"monthly_burn": 8500, "runway_months": 6, "currency": "USD"}, f, indent=2)

# 6. Ops distractor
with open(os.path.join(WORKSPACE, "internal/ops/team_roster.md"), "w") as f:
    f.write("""\
# Team
- Alice (founder, eng)
- Bob (founder, growth)
Advisors: none yet
""")

# 7. Asset copy attempts (bad, vague, AI-sounding)
with open(os.path.join(WORKSPACE, "assets/copy/headline_attempts.txt"), "w") as f:
    f.write("""\
Attempt 1: "AI-powered scheduling for the modern veterinary practice"
Attempt 2: "Revolutionize your clinic with smart reminders"
Attempt 3: "Reduce no-shows with our platform"
-- All rejected: too generic, AI-says tone, no specific promise
""")

# 8. Scraped competitor URLs (distractor)
with open(os.path.join(WORKSPACE, "competitors/scraped/urls.txt"), "w") as f:
    f.write("\n".join([
        "https://www.petdesk.com/pricing",
        "https://www.vethero.com/features",
        "https://www.capterra.com/veterinary-software/",
    ]))

# 9. Drafts/rejected
with open(os.path.join(WORKSPACE, "drafts/rejected/channel_ideas.txt"), "w") as f:
    f.write("""\
Ideas we brainstormed but didn't pick:
- TikTok for vet owners? Probably not.
- Google Ads - too expensive for us now
- Instagram - low intent
- LinkedIn - maybe later
- Reddit /r/veterinary - allowed posting, high intent
- SEO blog about vet clinic management - viable
- Newsletter to vet clinic owners - viable
We can't do all of them. Need to pick one.
""")

# 10. Logo placeholder
with open(os.path.join(WORKSPACE, "assets/logos/placeholder.txt"), "w") as f:
    f.write("Logo TBD - Figma link goes here\n")

# 11. Random config distractor
with open(os.path.join(WORKSPACE, "internal/ops/deploy_config_DRAFT.yaml"), "w") as f:
    f.write("""\
# DRAFT - not finalized
environment: staging
feature_flags:
  sms_reminders: false
  email_capture: true
  analytics: false  # TODO: enable before launch
""")

# ── The KEY task input: a vague founder brief ────────────────────────────────
# This is the "messy real-world input" the agent must transform into a proper plan.
with open(os.path.join(WORKSPACE, "founder_brief.txt"), "w") as f:
    f.write("""\
FOUNDER BRIEF - VetPing (working title)
========================================
We want to build something to help independent vet clinic owners reduce no-shows
and missed appointment reminders. We've talked to ~5 clinics in Austin, TX and
they all hate how complicated and expensive existing tools are.

Target users: independent vet clinic owners (NOT corporate chains).
Core frustration: no-shows cost them ~$150/appointment, and current SMS tools
are either too expensive (>$200/mo) or too dumb (no scheduling integration).

Our rough idea: a dead-simple no-show reducer under $79/mo with 2-click setup.
No EHR integration required at launch. Just SMS + email reminders synced to
Google Calendar.

We have 6 months runway. We need to validate fast. What do we do first?

We've heard about a "ship fast and validate with real distribution" approach
but don't know the exact steps to follow. Please create a full sprint plan
as a single Markdown file named `sprint_plan.md`.
""")

print("Workspace initialized.")
print("Files created:")
for root, dirs_list, files in os.walk(WORKSPACE):
    for file in files:
        print(os.path.join(root, file).replace(WORKSPACE, ""))