import os
import random

random.seed(42)

BASE = "/workspace"

# --- Directory structure with distractors ---
dirs = [
    "market_research/raw_data",
    "market_research/competitors",
    "market_research/trends",
    "interviews/transcripts",
    "interviews/notes",
    "product/wireframes",
    "product/specs",
    "financials/projections",
    "financials/costs",
    "ops/legal",
    "ops/branding",
    "archive/old_ideas",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "market_research/raw_data/google_trends_export.csv": """keyword,week,interest
vet practice software,2024-01-07,45
vet practice software,2024-01-14,47
vet practice software,2024-01-21,44
veterinary scheduling tool,2024-01-07,30
veterinary scheduling tool,2024-01-14,33""",

    "market_research/competitors/competitor_matrix.txt": """VetPro: $299/mo, scheduling + billing
EasyVet: $199/mo, scheduling only
VetSuccess: $450/mo, full suite
PawTrack: $99/mo, basic records
-- all missing: automated post-visit follow-up sequences --""",

    "market_research/trends/industry_report_snippet.txt": """According to AVMA 2023 data, 68% of independent vet practices
still use paper or spreadsheets for post-visit follow-up tracking.
Client retention is the #1 pain point cited by practice owners.""",

    "product/specs/feature_list_draft.txt": """MVP Feature List (Draft v0.3)
- Automated post-visit SMS/email follow-up
- Vaccination reminder scheduler
- Client no-show tracking
- Revenue per visit dashboard
- SOAP note templates""",

    "product/wireframes/screen_flow.txt": """[Home] -> [Dashboard] -> [Client List] -> [Visit Log] -> [Follow-up Queue]
Wireframe notes: keep nav to 3 clicks max""",

    "financials/projections/revenue_model.csv": """month,new_customers,mrr
1,5,1495
2,9,2691
3,14,4186
6,35,10465
12,80,23920""",

    "financials/costs/startup_costs.txt": """Stripe: 2.9% + 30c per transaction
Hosting (AWS): ~$80/mo initially
Domain + SSL: $20/yr
Email (SendGrid): $20/mo
Total burn rate estimate: ~$150/mo at MVP stage""",

    "ops/legal/entity_notes.txt": """Considering LLC in Delaware. EIN needed before payment processing.
Consult accountant re: self-employment tax implications.""",

    "ops/branding/name_candidates.txt": """- FollowPaw
- VetLoop
- PetPulse
- RevisitVet
- TailWag CRM""",

    "archive/old_ideas/idea_graveyard.txt": """1. Generic appointment booking SaaS - killed, too crowded
2. Vet supply marketplace - killed, margin too thin
3. Pet insurance comparison tool - killed, requires insurer partnerships""",

    "market_research/competitors/g2_review_snippets.txt": """VetPro (3.8/5, 142 reviews):
"Great scheduling but zero follow-up automation. We lose clients between visits."
"Wish it could send reminders automatically after appointments."
"No way to track who hasn't come back in 6+ months. Have to export to Excel."

EasyVet (4.1/5, 89 reviews):
"Love the UI but follow-up is completely manual still."
"Missing: re-engagement campaigns for lapsed clients."

PawTrack (3.4/5, 44 reviews):
"Cheap but you get what you pay for. No automation at all." """,
}

for path, content in distractors.items():
    full_path = os.path.join(BASE, path)
    with open(full_path, "w") as f:
        f.write(content)

# --- PRIMARY INPUT: Raw messy interview notes (the real task input) ---
# 13 interviews. Agent must compute exact percentages.
# Pain confirmed without prompting: interviews 1,2,3,4,5,6,7,8,9,10,11 = 11/13 = 84.6%
# Willingness to pay: interviews 1,2,4,5,6,8,9,10,11 = 9/13 = 69.2%
# BOTH pain AND WTP: interviews 1,2,4,5,6,8,9,10,11 = 9/13 = 69.2%
# Kill check: >=60% confirm pain + WTP -> PASS

interview_notes_raw = """=== RAW CUSTOMER DISCOVERY NOTES ===
Conducted: January-February 2024
Idea: Automated post-visit follow-up & client re-engagement tool for independent vet practices
Interviewer: Jamie Chen

--- Interview #1 ---
Participant: Dr. Sarah M., sole-practitioner, 6 years in practice, ~900 active clients
Date: Jan 8

She immediately launched into how clients just "vanish" after a visit - she's constantly
losing track of who needs follow-ups for chronic conditions. Spends ~3 hrs/week manually
combing through records to call people. Her vet tech does it but forgets half the time.

When I described an automated follow-up tool (outcome framing): "Oh god, I would pay for
that in a heartbeat. I'd say $80-100/month easy if it actually works."

[Note: apply the 50% discount - real signal ~$40-50/mo]

Pain confirmed without prompting: YES
WTP stated: $80-100/mo

--- Interview #2 ---
Participant: Mark T., office manager, 3-vet group practice, suburban area
Date: Jan 9

Brought up the follow-up problem himself within 2 minutes. They have a "system" (sticky
notes + a shared Google Sheet) that breaks down constantly. Lost a major dental cleaning
client because nobody sent a 6-month reminder. Estimated $400 lost revenue from that alone.

WTP: "We'd budget $150-200/month for something solid." [discount to ~$75-100/mo]

Pain confirmed without prompting: YES
WTP stated: YES ($150-200/mo)

--- Interview #3 ---
Participant: Linda K., practice owner, rural area, 1100 clients
Date: Jan 10

Interesting one. She's actually pretty organized - uses VetPro and has a part-time admin
who handles follow-ups manually. She didn't mention the pain unprompted; I had to ask
leading questions. Once I described the problem she said "oh yeah that's kind of an issue
I guess" but didn't seem to feel it acutely.

On WTP: "I don't think I'd add another software subscription. VetPro already costs me $299."

Pain confirmed without prompting: NO
WTP: NO

--- Interview #4 ---
Participant: Dr. Kevin W., mixed practice (small + large animals), 14 years experience
Date: Jan 12

Before I even finished my intro he said "is this about following up with clients? Because
that is my biggest headache right now." Perfect. He tracks large animal farm clients
differently but the small animal side is chaos. Showed me a literal binder of handwritten
"to-call" lists.

"What would it be worth? Honestly if it saved my front desk 5 hours a week I'd pay $200
easily. Maybe more." [discount to ~$100/mo]

Pain confirmed without prompting: YES
WTP: YES ($200/mo stated)

--- Interview #5 ---
Participant: Priya S., practice manager, 2-vet urban clinic, high-volume
Date: Jan 15

Fast talker, super busy. She said upfront she was tired of losing clients to the big
corporate chains who have "real CRM systems." The independent vet just can't compete on
follow-up. Went into specific detail about losing a client who switched to Banfield because
"they got a text reminder and we didn't send one."

WTP: "$100/month is what I'd say to my boss. Might get approved at $80." [~$40-50 real]

Pain confirmed without prompting: YES
WTP: YES

--- Interview #6 ---
Participant: Dr. Alex R., new grad, opened practice 18 months ago, 400 active clients
Date: Jan 17

Growing practice, pain is real but slightly different - he's worried about retention as
he scales. "If I lose 20% of clients per year because of poor follow-up that's existential
for my business right now." Brought it up himself when I asked about his biggest worries.

"I'd pay $60-80/month. I'm bootstrapped so budget is tight but this feels like revenue
preservation." [~$30-40 real]

Pain confirmed without prompting: YES
WTP: YES

--- Interview #7 ---
Participant: Diane F., office manager at a 4-vet practice, 10+ years experience
Date: Jan 19

Pragmatic. Confirmed the follow-up chaos exists ("oh absolutely, everyone in this industry
has that problem") but her practice is currently hiring a dedicated client coordinator to
handle it manually. She didn't bring it up as a pain - more as a "solved problem" even
though the solution is expensive (new hire at $35k/yr).

On WTP: "We just hired someone, so spending more on software would be a hard sell right
now."

Pain confirmed without prompting: YES (confirmed it exists but treated as solved)
WTP: NO (actively chose human over software)

--- Interview #8 ---
Participant: Dr. Tom B., emergency/specialty practice, 3 vets + 8 support staff
Date: Jan 22

Specialty practices have a different dynamic but he surprised me. Post-specialist follow-up
with referring vets and pet owners is messy. He unprompted started describing how they lose
referral relationships because of poor communication. Close enough to our problem space.

"If this could handle our post-discharge follow-up, I'd try it at $120-150/month." [~$60-75 real]

Pain confirmed without prompting: YES
WTP: YES

--- Interview #9 ---
Participant: Rachel G., solo practitioner, feline-only practice, 7 years
Date: Jan 24

Niche practice. She's very relationship-focused, knows most clients by name, but admitted
her "system" is her own memory and a notes app. "I've definitely lost clients who I just
forgot to follow up with and they felt neglected." Brought this up when I asked about
workflow frustrations.

"I'd pay up to $70/month. Cat owners are loyal if you communicate well." [~$35 real]

Pain confirmed without prompting: YES
WTP: YES

--- Interview #10 ---
Participant: Brian H., practice administrator, corporate-affiliated but semi-autonomous
Date: Jan 28

This was an interesting edge case. His practice is part of a small regional chain (4 clinics)
that has corporate tools but they're "clunky and no one uses them." He described the exact
follow-up problem unprompted as "the thing that corporate has been promising to fix for 3
years and hasn't."

WTP: "I'd need to get approval but $200-250/month across our 4 clinics seems reasonable."
[~$100-125 real for the group]

Pain confirmed without prompting: YES
WTP: YES

--- Interview #11 ---
Participant: Dr. Natasha P., exotic animal specialist, 5 years
Date: Jan 30

Exotic practice has very specific follow-up needs (medication adjustments, exotic diet
checks). She described unprompted the nightmare of tracking which iguanas needed their
quarterly check-ins. Genuinely painful problem for her.

WTP: "Honestly? $50-60/month. My practice is small." [~$25-30 real]

Pain confirmed without prompting: YES
WTP: YES

--- Interview #12 ---
Participant: Michael C., veterinarian + owner, recently sold to private equity, now employed
Date: Feb 1

His practice is now owned by a PE firm. He has no purchasing authority anymore. Confirmed
the problem exists in principle but "any software decision goes through the regional ops
manager." He himself wouldn't pay because he can't.

Pain confirmed without prompting: NO (didn't bring it up - focused on PE transition stress)
WTP: NO (no authority)

--- Interview #13 ---
Participant: Yuki T., front desk coordinator, 3-vet practice
Date: Feb 3

She's not a decision-maker but has frontline experience. Confirmed the chaos is real and
daily ("I spend an hour every morning on follow-up calls, it's part of my job but I hate
it"). But no purchase authority.

Pain confirmed without prompting: YES (described it as daily operational chaos)
WTP: N/A - not a buyer. She said "my boss would probably pay for it if it freed me up."

NOTE TO SELF: Don't count Yuki's WTP as positive - she can't buy. Count her pain signal though.

=== END INTERVIEW NOTES ===
"""

with open(os.path.join(BASE, "interviews/notes/discovery_interviews_raw.txt"), "w") as f:
    f.write(interview_notes_raw)

# --- RAT Results ---
rat_results_raw = """=== RISKIEST ASSUMPTION TEST RESULTS ===
Date run: Feb 10 - Feb 21, 2024
Test designed by: Jamie Chen

ASSUMPTION BEING TESTED:
Independent vet practice owners/managers will pay for an automated post-visit
follow-up tool without needing a sales call — i.e., they'll convert from a
landing page alone.

TEST DESIGN:
- Built a simple landing page: "Never lose a vet client again — automated follow-up for
  independent practices"
- "Pre-order at $79/month — lock in founder pricing" button (Stripe payment form, real charge)
- Targeted Facebook/Instagram ads to: Practice owners, office managers, keywords: "veterinary
  practice management", "vet clinic software", geographic: US + Canada
- Ad spend: $180 total
- Traffic target: 200+ unique visitors

RESULTS (Feb 21):
Total unique visitors: 247
Button clicks ("Start pre-order"): 31
Completed payment (real Stripe charge, $79 collected): 9
Conversion rate (payments / visitors): 9 / 247 = 3.64%
Ad spend: $180
Cost per paying lead: $20.00

Notes:
- 3 of the 9 payments came from email referrals (not ads) — someone shared the page in a
  vet practice Facebook group
- Several people filled a "notify me" form instead of paying (14 additional emails collected)
- One payment was from a mobile groomer, not a vet practice — edge case, keeping in count
  for now but flagging

=== END RAT RESULTS ===
"""

with open(os.path.join(BASE, "market_research/raw_data/rat_test_results.txt"), "w") as f:
    f.write(rat_results_raw)

# --- Additional distractor: old scoring attempt (WRONG weights - trap for agent) ---
wrong_scorecard_attempt = """QUICK SCORING ATTEMPT (informal, equal weights)
Problem clarity: 4
Demand evidence: 4
Customer discovery: 4
Solution fit: 3
RAT: 4
Unfair advantage: 3
Average: 3.67 -> Looks like conditional go?

NOTE: This was done quickly and may not use the right methodology.
"""

with open(os.path.join(BASE, "archive/old_ideas/old_scorecard_attempt.txt"), "w") as f:
    f.write(wrong_scorecard_attempt)

# --- Distractor: partial demand signal notes ---
demand_notes = """DEMAND SIGNAL CHECK (partial notes)
Reddit: Found r/VetTech thread with 47 comments complaining about manual follow-ups
Google Trends: "veterinary client retention software" - stable volume 2022-2024
G2 reviews: Documented in competitor matrix - multiple reviews cite follow-up gap
Job postings: Found 12 "Veterinary Client Care Coordinator" postings on Indeed this month
Twitter/X: Several vet practice owners tweeting about losing clients - found ~8 threads

Signals found: 5 out of 5 checked -> strong demand signal
"""

with open(os.path.join(BASE, "market_research/raw_data/demand_signals_notes.txt"), "w") as f:
    f.write(demand_notes)

print("Workspace generated successfully.")
print(f"Files created in {BASE}")