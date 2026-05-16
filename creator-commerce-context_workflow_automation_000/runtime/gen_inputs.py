import os
import random

random.seed(42)

WORKSPACE = "/workspace"

# Directory structure
dirs = [
    "workspace/campaign_q3/briefs",
    "workspace/campaign_q3/creator_roster",
    "workspace/campaign_q3/product_assets",
    "workspace/campaign_q3/internal_comms",
    "workspace/campaign_q3/analytics",
    "workspace/campaign_q3/legal",
    "workspace/campaign_q3/drafts",
    "workspace/campaign_q3/old_versions",
    "workspace/campaign_q3/old_versions/archive",
    "workspace/ops/budget",
    "workspace/ops/scheduling",
]

for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ─── MAIN INPUT FILES (messy, fragmented, contradictory) ─────────────────────

# 1. Campaign notes from marketing manager (chaotic Slack export dump)
campaign_notes = """\
slack export – #tiktok-shop-serum-launch – partial

[Maya Chen - 9:14am]: ok so we're doing the velvet glow serum push on tiktok shop, 
targeting gen z + millennial women 18-34 who care about skin barrier. 
price is $42 retail but we're doing a launch offer... i think 15% off? or was it $5 off?
need to confirm with Dan

[Dan Kowalski - 9:31am]: its $5 off first 30 days, NOT a percentage. 
also we have a bundle offer if they buy 2: $74 instead of $84. 
PDP is live at velvetglow.com/serum but landing page for the tiktok campaign isn't ready yet

[Maya Chen - 9:45am]: budget is $18k total for the whole thing. 
we have maybe $10k for creators, rest for ads/boosting. 
need to launch by end of Q3 – that's sept 30.

[Priya - 10:02am]: inventory note: we have 2,200 units allocated for this campaign. 
if we blow past that we can reorder but 6 week lead time

[Dan Kowalski - 10:18am]: oh also – NO claims about "anti-aging" or "repairs skin barrier" 
per legal. we can say "supports" or "nourishes". check the legal folder for full list

[Jess - 11:55am]: i think we're going TikTok Shop affiliate first, then layer in 
1-2 live sellers end of month. paid UGC maybe? haven't decided. 
primary goal is CONVERSION not awareness. we want sales in first 30 days.

[Maya Chen - 12:03pm]: correct. conversion-first. awareness is secondary.
also geo is US only for now. canada maybe q4 but not confirmed.
"""

with open(os.path.join(WORKSPACE, "workspace/campaign_q3/internal_comms/slack_export_serum_launch.txt"), "w") as f:
    f.write(campaign_notes)

# 2. Creator roster dump (messy CSV-ish, incomplete)
creator_roster = """\
Creator roster – Velvet Glow Serum – as of Aug 12

Name | Handle | Type | Followers | Rate | Status | Notes
---
Tara Bloom | @tarabloom_skin | TikTok affiliate | 87k | $0 (affiliate only, 8% commission) | Confirmed | Has existing serum UGC from competitor, check conflicts
Mia Nguyen | @mianailsbeauty | TikTok affiliate | 210k | $0 (affiliate 8%) | Outreach pending | Very engaged audience, beauty niche
Carlos R. | @carlosskincaretalk | TikTok affiliate | 45k | $300 flat + 8% | Confirmed | Male creator, diverse audience test
LiveQueen Studios | – | Live seller | TBD negotiating | ~$2,500/session | Interest expressed | Would do 2 sessions end of Sept
@glossguru (real name unknown) | – | UGC only | n/a | $450/video | Maybe | Has done 3 UGC packs for similar brands
---
NOTE: We do NOT have a signed contract with any creator yet. 
Usage rights not negotiated. 
Tara's conflict check not done.
"""

with open(os.path.join(WORKSPACE, "workspace/campaign_q3/creator_roster/creator_list_aug12.txt"), "w") as f:
    f.write(creator_roster)

# 3. Product sheet (somewhat structured but with gaps)
product_sheet = """\
PRODUCT BRIEF – VELVET GLOW SERUM
Internal doc – Product Team

Full name: Velvet Glow Hydra-Barrier Serum
SKU: VGS-001
Category: Skincare / Serum
Key ingredients: Ceramide complex, Niacinamide 5%, Hyaluronic Acid
Retail price: $42.00 USD
Subscription price: NOT YET LIVE (planned Q4)
Bundle: 2x for $74

Claimed benefits (APPROVED by legal):
  - "Nourishes and supports skin barrier function"
  - "Visibly smoother skin in 4 weeks"
  - "Suitable for all skin types including sensitive"

Banned claims (per legal review, see legal/claims_restrictions.pdf):
  - "Repairs skin barrier"
  - "Anti-aging"
  - "Dermatologist tested" (not yet completed study)
  - Any claim about treating acne or eczema

PDP URL: velvetglow.com/serum (live)
TikTok Shop listing: IN PROGRESS – not yet live
Amazon: Not in scope for this campaign
Shopify: velvetglow.com (main store, Shopify backend)

Assets available:
  - 3x lifestyle photos (high res)
  - 1x "how to layer" tutorial video (30 sec, not creator-facing yet)
  - No current scripts written

Reviews: 47 reviews on site, avg 4.6 stars. No reviews on TikTok Shop yet (listing not live).
"""

with open(os.path.join(WORKSPACE, "workspace/campaign_q3/product_assets/product_brief_VGS001.txt"), "w") as f:
    f.write(product_sheet)

# 4. Budget email thread (fragmented)
budget_email = """\
From: Maya Chen <maya@velvetglow.com>
To: Jess Park <jess@velvetglow.com>
Subject: Re: Re: Re: Q3 serum budget – FINAL

Jess – here's where we landed:

Total campaign budget: $18,000
  Creator fees/affiliate: $10,000 (this includes flat fees + estimated commission payouts)
  TikTok ads / spark ads boosting: $5,000
  UGC production: $1,500
  Contingency/misc: $1,500

Timeline hard deadline: September 30
Soft launch (affiliate links live): targeting September 5
Live selling sessions: September 25 and 27 (tentative, pending LiveQueen contract)

Open question: Do we need FTC disclosure language reviewed? 
Priya thinks yes, Dan thinks our standard hashtag policy covers it.

– Maya

---
From: Jess Park
Sent: Aug 10

Maya – also to confirm: this is US-only for Q3. No international shipping offers.
We don't have TikTok Shop geo-expansion approved yet.
"""

with open(os.path.join(WORKSPACE, "workspace/ops/budget/q3_serum_budget_email.txt"), "w") as f:
    f.write(budget_email)

# 5. Legal notes (brief, partial)
legal_notes = """\
Legal checklist – Velvet Glow Serum Campaign – DRAFT

1. Claims restrictions: see product brief. Do not use anti-aging, repair, dermatologist tested.
2. FTC disclosures: OPEN – team not aligned. Need legal sign-off on affiliate disclosure approach.
3. Creator contracts: NONE SIGNED. Usage rights undefined. This is a risk.
4. Tara Bloom conflict check: NOT COMPLETED. She has prior serum UGC from a competitor brand.
5. TikTok Shop compliance: policies updated July 2024 – team needs to review latest.
6. Canada: Not approved for Q3 – if any creator ships internationally, flag it.
"""

with open(os.path.join(WORKSPACE, "workspace/campaign_q3/legal/legal_checklist_draft.txt"), "w") as f:
    f.write(legal_notes)

# ─── DISTRACTOR FILES ────────────────────────────────────────────────────────

# Old campaign brief (outdated, contradictory price)
old_brief = """\
Velvet Glow Serum – OUTDATED BRIEF v0.1 – DO NOT USE

Price: $38 (this was before price revision)
Campaign goal: Brand awareness (revised – now conversion-first)
Creator budget: $6,000 (revised upward)
Launch date: August 15 (missed, postponed to Q3 end)
"""
with open(os.path.join(WORKSPACE, "workspace/campaign_q3/old_versions/archive/brief_v0.1_OUTDATED.txt"), "w") as f:
    f.write(old_brief)

# Analytics placeholder
analytics_stub = """\
TikTok Shop Analytics – Velvet Glow
Note: No data yet – TikTok Shop listing not live.
Shopify store traffic (Aug): 12,400 sessions, 2.1% CVR overall store.
Serum PDP: 890 sessions, 3.4% CVR (direct traffic only).
"""
with open(os.path.join(WORKSPACE, "workspace/campaign_q3/analytics/prelim_analytics_aug.txt"), "w") as f:
    f.write(analytics_stub)

# Scheduling draft (distractor)
scheduling = """\
Tentative content calendar – serum launch

Week 1 (Sept 1-7): Affiliate links go live. Tara + Mia post organic TikToks.
Week 2 (Sept 8-14): Carlos posts. Spark ads begin.
Week 3 (Sept 15-21): UGC video from @glossguru drops. More spark ads.
Week 4 (Sept 22-30): Live selling sessions (LiveQueen). Final push.
"""
with open(os.path.join(WORKSPACE, "workspace/ops/scheduling/content_calendar_draft.txt"), "w") as f:
    f.write(scheduling)

# General brand guidelines (distractor)
brand_guidelines = """\
Velvet Glow Brand Guidelines – Summary

Voice: Clean, empowering, dermatology-inspired but approachable.
Colors: Ivory, dusty rose, warm gold.
Typography: Playfair Display (headers), Inter (body).
Do not use: harsh clinical language, aggressive before/after framing.
"""
with open(os.path.join(WORKSPACE, "workspace/campaign_q3/briefs/brand_guidelines_summary.txt"), "w") as f:
    f.write(brand_guidelines)

# Creator outreach template (distractor)
outreach_template = """\
Hi [Creator Name],

We'd love to collaborate on our new Velvet Glow Serum launch on TikTok Shop!
[Insert personalization here]

Commission: 8%
[Terms TBD]
"""
with open(os.path.join(WORKSPACE, "workspace/campaign_q3/creator_roster/outreach_template_draft.txt"), "w") as f:
    f.write(outreach_template)

# Competitor research note (distractor)
competitor_note = """\
Competitor watch – Aug 2024

GlowLab Serum: $38, heavy TikTok push, 200+ affiliates
DermaDew: $55, mostly YouTube, lower TikTok presence
Key insight: Price sensitivity in $35-$45 range is high on TikTok Shop.
"""
with open(os.path.join(WORKSPACE, "workspace/campaign_q3/drafts/competitor_watch_aug.txt"), "w") as f:
    f.write(competitor_note)

# Ops note (distractor)
ops_note = """\
Ops – fulfillment note

Standard shipping: 5-7 business days
Expedited: 2-3 business days (+$8)
TikTok Shop fulfillment: need to configure – not done yet
Returns policy: 30 days, unused/unopened only
"""
with open(os.path.join(WORKSPACE, "workspace/ops/fulfillment_notes.txt"), "w") as f:
    f.write(ops_note)

# Script placeholder (distractor)
script_placeholder = """\
[SCRIPT PLACEHOLDER – NOT WRITTEN YET]
Creator brief scripts for serum launch TBD.
Waiting for context pack before writing scripts.
"""
with open(os.path.join(WORKSPACE, "workspace/campaign_q3/briefs/creator_scripts_TODO.txt"), "w") as f:
    f.write(script_placeholder)

# Random internal meeting notes (distractor)
meeting_notes = """\
Team sync – Aug 8 – informal notes

- Confirm TikTok Shop setup timeline (Dan)
- Legal sign-off needed before creator contracts
- Maya to finalize budget split
- Jess to send creator roster update
- No decision yet on paid influencer vs pure affiliate
"""
with open(os.path.join(WORKSPACE, "workspace/campaign_q3/internal_comms/team_sync_aug8.txt"), "w") as f:
    f.write(meeting_notes)

print("Workspace generated successfully.")
print(f"Files created in {WORKSPACE}/workspace/")