import os
import random

random.seed(42)

BASE = "/workspace"

# === Directory Structure ===
dirs = [
    "campaign_assets/briefs/drafts",
    "campaign_assets/briefs/archive",
    "campaign_assets/creatives/video",
    "campaign_assets/creatives/static",
    "campaign_assets/performance_data",
    "brand_guidelines/fonts",
    "brand_guidelines/colors",
    "brand_guidelines/messaging",
    "compliance/legal_review",
    "compliance/claims_log",
    "product_info/ingredients",
    "product_info/certifications",
    "channel_specs/meta",
    "channel_specs/tiktok",
    "channel_specs/youtube",
    "references",
    "team_notes",
    "stakeholder_feedback",
]

for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# === Distractor Files ===

# 1. Old archived brief (distractor - wrong product)
with open(os.path.join(BASE, "campaign_assets/briefs/archive/brief_Q1_2023.md"), "w") as f:
    f.write("""# Archived Brief - Q1 2023
Product: SleepWave Gummies
Audience: Insomniacs 35-55
Goal: Drive trial purchases
DO NOT USE - superseded
""")

# 2. Performance data CSV (distractor)
with open(os.path.join(BASE, "campaign_assets/performance_data/meta_july_results.csv"), "w") as f:
    f.write("""campaign,spend,ctr,roas
sleepwave_q1,14200,2.1%,1.8
focus_q2,9800,3.4%,2.6
vitd_q3,5100,1.9%,1.4
""")

# 3. Color palette file (distractor)
with open(os.path.join(BASE, "brand_guidelines/colors/palette_2024.txt"), "w") as f:
    f.write("Primary: #2C7A4B\nSecondary: #F5E6CC\nAccent: #E8734A\n")

# 4. Font list (distractor)
with open(os.path.join(BASE, "brand_guidelines/fonts/approved_fonts.txt"), "w") as f:
    f.write("Headlines: Neue Haas Grotesk\nBody: Inter\nAccent: Playfair Display\n")

# 5. Messaging framework old version (distractor)
with open(os.path.join(BASE, "brand_guidelines/messaging/voice_guide_v1.txt"), "w") as f:
    f.write("""Brand Voice: Confident, clinical-friendly, approachable.
Avoid: overly medical tone, fear-based language.
Note: This is v1 - see v2 for updated guidelines (v2 not yet uploaded).
""")

# 6. Ingredient sheet (context, but raw and unfiltered)
with open(os.path.join(BASE, "product_info/ingredients/clarity_plus_ingredients.txt"), "w") as f:
    f.write("""Clarity Plus - Full Ingredient Deck (Internal)
- Lion's Mane Mushroom Extract: 500mg (KSM-66 equivalent grade)
- Bacopa Monnieri: 300mg (standardized to 45% bacosides)
- L-Theanine: 200mg
- Vitamin B12 (Methylcobalamin): 500mcg
- Zinc: 10mg
- Excipients: Rice flour, HPMC (vegetarian capsule), magnesium stearate
Third party tested: NSF Certified, COA on file.
""")

# 7. Certification doc (distractor, raw)
with open(os.path.join(BASE, "product_info/certifications/nsf_cert_summary.txt"), "w") as f:
    f.write("""NSF Certification # NF-00482-C
Product: Clarity Plus 60-cap
Date of Issue: March 2024
Scope: Ingredient identity, potency, and contaminant testing.
Note: Certification does not imply FDA approval or disease treatment claims.
""")

# 8. Legal claims log (distractor)
with open(os.path.join(BASE, "compliance/claims_log/rejected_claims_2024.txt"), "w") as f:
    f.write("""REJECTED CLAIMS (Legal Review - Do Not Use):
- "Clinically proven to cure brain fog" - rejected 2024-02-14
- "FDA approved formula" - rejected 2024-03-01
- "Reverses cognitive decline" - rejected 2024-03-15
- "Guaranteed results in 7 days" - rejected 2024-04-02
""")

# 9. Channel spec - Meta (distractor)
with open(os.path.join(BASE, "channel_specs/meta/meta_video_specs_2024.txt"), "w") as f:
    f.write("""Meta Reels / Feed Video Specs:
Aspect ratio: 9:16 (Reels), 1:1 (Feed)
Max length: 60s (Reels), 15s recommended for Feed
File format: MP4, H.264
Caption: Always-on recommended (85% watch muted)
CTA buttons: Shop Now, Learn More, Get Offer
""")

# 10. TikTok spec (distractor)
with open(os.path.join(BASE, "channel_specs/tiktok/tiktok_brand_policy_note.txt"), "w") as f:
    f.write("""TikTok Health Supplement Policy Note (Internal):
- Before/after imagery requires disclaimer
- Cannot claim to treat, cure, or prevent disease
- Testimonials must include: "Results not typical"
- Health professionals in ads require credential verification
""")

# 11. YouTube spec (distractor)
with open(os.path.join(BASE, "channel_specs/youtube/youtube_preroll_specs.txt"), "w") as f:
    f.write("""YouTube Pre-roll:
Skippable after 5s. Hook must land in first 3-5 seconds.
Max 30s for non-skippable.
Brand safe categories only.
""")

# 12. Stakeholder feedback (distractor, noisy)
with open(os.path.join(BASE, "stakeholder_feedback/growth_team_comments_aug.txt"), "w") as f:
    f.write("""Slack export - #growth-creative Aug 12
Jake: last brief was too long, nobody read it
Priya: we need something the UGC creators can actually use day 1
Marcus: the angle on focus needs to be more specific - "better focus" is not a hook
Jake: also compliance flagged two scripts last week, we need guardrails upfront
Priya: agreed, and can we please include the NSF cert somehow? creators don't know we have it
""")

# 13. Team notes on target audience (messy, contradictory)
with open(os.path.join(BASE, "team_notes/audience_notes_mixed.txt"), "w") as f:
    f.write("""Audience Notes - mixed from multiple sources:

From growth:
  - primary: 28-42 year old professionals
  - secondary: students and remote workers
  - pain point: afternoon energy crash, inability to focus during deep work
  - they distrust "supplement bro" culture - want evidence

From brand:
  - "Our customer is someone who optimizes everything - sleep, diet, workouts - but still loses focus at 2pm"
  - They have tried coffee, they know caffeine is not the answer

From customer support (top complaints in reviews):
  - "Takes 2-3 weeks to feel it, wish I knew"
  - "Love that it's not stimulant-based"
  - "NSF certified gave me confidence to try it"
  - "Wish the capsules were smaller"

Note: some team members suggested targeting 45-60 but growth rejected this - stick with 28-42.
""")

# 14. Campaign goal doc (messy, contains contradictions and noise)
with open(os.path.join(BASE, "team_notes/campaign_goal_q3_draft.txt"), "w") as f:
    f.write("""Campaign Goal Brainstorm - Q3 Draft (NOT FINAL)

Objective options discussed:
1. Drive first-time purchases of Clarity Plus 60-cap SKU
2. Build brand awareness for the nootropic line (Marcus prefers this)
3. Retargeting warm audiences from Q2 (separate campaign - do not mix)

DECISION (from Priya, Aug 10): GO WITH OPTION 1. First purchase conversion.
Primary metric: Checkout initiations / Purchase CVR
Secondary: CPM efficiency on Meta Reels

Budget note: $22k for creative production + paid, split TBD.
Launch: September campaign. Creatives needed by Aug 28.
""")

# 15. Offer and pricing notes (messy)
with open(os.path.join(BASE, "team_notes/offer_notes.txt"), "w") as f:
    f.write("""Offer for September Campaign:

Option A: 20% off first order with code CLARITY20
Option B: Buy 2 get 1 free
Option C: Free shipping on orders over $50

CONFIRMED: Option A is live. Code CLARITY20. Expires Sept 30.
Landing page: /clarity-plus (not yet updated with new offer, engineering ticket open)
Note: Do NOT promise "lowest price" - competitor parity claim, legally risky.
""")

# 16. Forbidden claims doc (critical - agent must surface this)
with open(os.path.join(BASE, "compliance/legal_review/forbidden_claims_active.txt"), "w") as f:
    f.write("""ACTIVE FORBIDDEN CLAIMS - Clarity Plus (Updated Aug 2024)
Approved by: Legal (Dana K.)

DO NOT USE in any ad, script, caption, or brief:
1. Any claim that the product treats, cures, prevents, or reverses cognitive disease or disorder.
2. "FDA approved" or "FDA cleared" - product is a dietary supplement, not a drug.
3. "Clinically proven" without citing the specific study and its limitations.
4. Before/after cognitive claims with specific quantified improvement (e.g., "50% better focus").
5. Guaranteed outcome language: "will", "guaranteed", "proven to work for everyone".
6. Testimonials presented without "Individual results may vary."

ALLOWED (pre-approved language):
- "Supports focus and mental clarity*" with asterisk footnote: "*These statements have not been evaluated by the FDA. This product is not intended to diagnose, treat, cure, or prevent any disease."
- "NSF Certified for Sport® - third-party tested for purity and potency."
- "Non-stimulant formula."
- "Used by [role descriptor] professionals." (no celebrity or credential implied endorsement without contract)
""")

# 17. References output template placeholder (should exist as referenced in SKILL.md)
os.makedirs(os.path.join(BASE, "references"), exist_ok=True)
with open(os.path.join(BASE, "references/output-template.md"), "w") as f:
    f.write("""# Ad Creative Brief Template

## 1. Campaign Objective Summary
[One clear paragraph: who, what action, what metric, what channel, what timeframe]

## 2. Core Angle & Message Hierarchy
[Primary angle: the single strongest commercial hook]
[Message hierarchy: what to say first, second, third]

## 3. Hook / Scene / Proof Guidance
[Opening hook options]
[Scene or format direction]
[Proof points to feature - specific, not generic]

## 4. CTA & Offer Note
[Primary CTA]
[Offer detail and urgency framing]
[Landing page note if relevant]

## 5. Guardrails & Risk Notes
[Explicit forbidden language or claims]
[Compliance requirements]
[Brand safety notes]
""")

# 18. A half-written draft brief (wrong format, incomplete - distractor)
with open(os.path.join(BASE, "campaign_assets/briefs/drafts/brief_attempt_v0.txt"), "w") as f:
    f.write("""DRAFT - DO NOT SEND
Clarity Plus Brief Attempt

Product: Focus supplement
Audience: Professionals
Goal: Sell more
Hook: Feel focused
CTA: Buy now

[INCOMPLETE - Jake said this is too vague, needs a real brief before Aug 28]
""")

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(BASE):
    for fname in files:
        fpath = os.path.join(root, fname)
        print(f"  {fpath}")