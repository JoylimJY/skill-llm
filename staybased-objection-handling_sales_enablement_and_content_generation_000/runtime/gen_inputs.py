import os
import random
import json

random.seed(42)

BASE = "/workspace"

# ── distractor files ──────────────────────────────────────────────────────────

distractors = {
    "sales_team/call_notes/discovery_call_template.txt": (
        "Discovery Call Template\n"
        "1. Intro / rapport\n"
        "2. Current workflow questions\n"
        "3. Pain points\n"
        "4. Budget range\n"
        "5. Timeline\n"
        "Notes: Use open-ended questions. Do NOT pitch until step 3 complete.\n"
    ),
    "sales_team/call_notes/demo_checklist.txt": (
        "Pre-demo checklist:\n"
        "- Confirm attendees\n"
        "- Screen share working?\n"
        "- Slides updated?\n"
        "- CRM note logged?\n"
    ),
    "sales_team/lost_deals/q1_2024_lost_analysis.csv": (
        "deal_id,prospect,reason_closed_lost,revenue_lost\n"
        "1001,Cedar Grove Dental,price,4788\n"
        "1002,Maple Street Physio,timing,1788\n"
        "1003,Harbor View Chiro,went with competitor,2388\n"
        "1004,Sunrise Acupuncture,unresponsive,1200\n"
    ),
    "sales_team/templates/cold_outreach_v3.txt": (
        "Subject: Quick question about your booking process\n\n"
        "Hi [Name],\n\n"
        "I help [specialty] practices in [city] reduce no-shows by 40%.\n"
        "Would a 15-min call make sense this week?\n\n"
        "— [Your name]\n"
    ),
    "marketing/landing_pages/alfred_hero_copy.txt": (
        "Stop losing patients to voicemail.\n"
        "Alfred books appointments 24/7 — even while you sleep.\n"
        "Used by 500+ independent practices.\n"
        "Start free trial → \n"
    ),
    "marketing/email_sequences/nurture_sequence.json": json.dumps({
        "sequence_name": "Post-Demo Nurture",
        "emails": [
            {"day": 1, "subject": "Your demo recap", "body": "Thanks for joining..."},
            {"day": 3, "subject": "One question for you", "body": "How are bookings going?"},
            {"day": 7, "subject": "Still thinking it over?", "body": "Happy to answer any questions."}
        ]
    }, indent=2),
    "product/feature_requests/q2_roadmap_draft.txt": (
        "Q2 Roadmap (DRAFT)\n"
        "- SMS reminders v2\n"
        "- Google Calendar two-way sync\n"
        "- Waitlist management\n"
        "- Insurance form pre-fill (under review)\n"
    ),
    "ops/onboarding/onboarding_sop.txt": (
        "Onboarding SOP v4\n"
        "Week 1: Setup call, calendar integration\n"
        "Week 2: Staff training\n"
        "Week 3: Go-live review\n"
        "Week 4: First 30-day check-in\n"
    ),
    "ops/contracts/standard_msa_notes.txt": (
        "MSA Key Points:\n"
        "- 30-day cancellation notice\n"
        "- Data export within 14 days of termination\n"
        "- SLA: 99.5% uptime\n"
    ),
    "finance/pricing_history/alfred_pricing_log.csv": (
        "date,plan,price_usd,notes\n"
        "2023-01-01,Core,99,launch price\n"
        "2023-06-01,Core,119,price increase\n"
        "2024-01-01,Core,149,current\n"
        "2024-01-01,Pro,249,new tier\n"
    ),
}

for rel_path, content in distractors.items():
    full_path = os.path.join(BASE, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# ── MAIN INPUT: raw messy prospect pushback notes ─────────────────────────────
# These are deliberately written in informal, fragmented, "salesperson's notes" style.
# They include ambiguity, mixed signals, and one walk-away case.

pushback_notes = """PROSPECT PUSHBACK NOTES — Alfred Booking System
Sales Rep Dump — Week of 2024-03-11
(unedited, as-is from CRM voice-to-text)

=== CASE 001 ===
Prospect: Sunrise Wellness & Massage (solo owner, Maria)
Context: We sent a $149/mo proposal. Follow-up call today.
Maria's exact words: "I looked at the proposal. Honestly, $149 a month feels like a lot for someone like me who's just a one-person shop. I don't know if I can justify it."
Rep notes: She seemed interested during demo. No mention of competitor. Budget is the sticking point.

=== CASE 002 ===
Prospect: Northside Pediatric Dental (office manager, Tom)
Context: Sent proposal 10 days ago. Tom finally replied.
Tom's exact words: "We're actually pretty happy with how we do things now. Our front desk handles all the scheduling, they're great. I'm not sure we really need something like this."
Rep notes: They have 3 front desk staff. No automation. They lose about 15% of after-hours calls to voicemail per their own numbers.

=== CASE 003 ===
Prospect: Cedar Grove Chiropractic (owner, Dr. Patel)
Context: Second call. He's comparing us to a competitor (ClinicOS).
Dr. Patel's exact words: "ClinicOS quoted us less and they've been around longer. Why should I go with you guys?"
Rep notes: ClinicOS is cheaper but has no 24/7 booking, weaker SMS reminders. Dr. Patel cares a lot about patient experience.

=== CASE 004 ===
Prospect: Harbor Light Physiotherapy (director, Sandra)
Context: Sandra reached out after seeing our ad. First real sales conversation.
Sandra's exact words: "This looks interesting but we're in the middle of a staff restructure right now. Maybe revisit in Q3?"
Rep notes: Q3 is 4 months away. They're losing approx $800/mo in missed bookings by rep's estimate. No other blockers mentioned.

=== CASE 005 ===
Prospect: Blue Pines Acupuncture (owner, Kevin)
Context: Kevin has been on 3 calls, requested a custom demo, asked for a detailed ROI breakdown (which we built for him), and now wants a "free 60-day trial" plus a custom integration we don't offer, or he'll "post a bad review." He also told our rep "you need to prove yourselves before I pay anything." His scope keeps expanding and he refuses to sign even a 30-day pilot. Last call he was rude to the rep.
Rep notes: This has been 6 weeks. Kevin is unpredictable and the custom integration would cost us real dev hours.

=== CASE 006 ===
Prospect: Twin Oaks Orthodontics (owner, Dr. Chen)
Context: Dr. Chen just signed with a competitor 2 weeks ago. She reached out because she's already frustrated.
Dr. Chen's exact words: "I just started using DentaFlow last month but honestly it's been a headache — the setup was complicated and their support is slow. I'm still in contract though."
Rep notes: She's 2 weeks into a 12-month contract with DentaFlow. She's clearly dissatisfied and our product does this better.
"""

notes_path = os.path.join(BASE, "sales_team/call_notes/prospect_pushback_raw.txt")
with open(notes_path, "w") as f:
    f.write(pushback_notes)

# ── Output directory (must exist, but be empty) ───────────────────────────────
os.makedirs(os.path.join(BASE, "artifacts"), exist_ok=True)

print("Workspace generated successfully.")
print(f"Distractor files: {len(distractors)}")
print(f"Main input: sales_team/call_notes/prospect_pushback_raw.txt")