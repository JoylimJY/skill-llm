import os
import random
import json

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Directory structure ---
dirs = [
    "references",
    "sessions/raw",
    "sessions/processed",
    "campaigns/past",
    "campaigns/drafts",
    "catalog/tents",
    "catalog/footwear",
    "catalog/accessories",
    "analytics/weekly",
    "analytics/monthly",
    "legal",
    "ops/discount_codes",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- CRITICAL: cold_start_playbook.md (agent MUST read this) ---
playbook = """# TrailForge Cold-Start Playbook

## Segment → Offer → Trigger Map

### Segments

| Segment Label        | Path Signal                                              | Confidence Threshold |
|----------------------|----------------------------------------------------------|----------------------|
| Category Intent      | 3+ PDPs in same category within one session              | High                 |
| Price Sensitive      | Visited sale/clearance page OR sorted by price-low-high  | High                 |
| Shipping Sensitive   | Visited cart + shipping info page without checkout       | Medium               |
| Single SKU Deep Dive | 2+ return visits to same PDP; >90s dwell on one product  | High                 |
| Bouncer              | <30s session, 1–2 pages, no PDP                          | Low                  |

### Offer Rules by Segment

| Segment Label        | Offer Type       | Discount Value | Min Order (USD) | Exclusions                          |
|----------------------|------------------|----------------|-----------------|-------------------------------------|
| Category Intent      | % off            | 12%            | $85             | Full-price tents >$400              |
| Price Sensitive      | Fixed amount off | $15 off        | $60             | Already-discounted clearance items  |
| Shipping Sensitive   | Free shipping    | Free ship      | $50             | Oversized items (>10 lbs shipped)   |
| Single SKU Deep Dive | Gift with order  | Free accessory | $120            | None                                |
| Bouncer              | % off            | 8%             | $40             | None                                |

### Margin Safety Bands
- Tents (high-ticket): max 10% discount; gift offers preferred
- Footwear: max 15% discount
- Accessories: max 20% discount
- Clearance: NO additional discount stacking allowed

### Trigger Sequence (mandatory order)
1. EXIT INTENT — always primary; fires on mouse-leave-viewport (desktop) or back-button proxy (mobile)
2. Backup 1 — time on PDP: fires after 25 seconds dwell on any single product page
3. Backup 2 — second collection/category view: fires when visitor opens a second distinct category listing

### Stack Rules
- Max one active first-order offer per session
- Cannot stack with: WELCOME15, EARLYBIRD, influencer codes
- New-customer definition: no prior purchase in system (email or cookie match)

### Consent
- Popup allowed: users who have not opted out of marketing on cookie consent banner
- Email capture on modal is optional, not required for offer delivery
"""

with open(os.path.join(workspace, "references/cold_start_playbook.md"), "w") as f:
    f.write(playbook)

# --- Raw visitor session log (messy, agent must interpret) ---
session_log = """
=== TrailForge Visitor Session Export ===
Generated: 2024-06-10T08:00:00Z
Period: 2024-06-07 to 2024-06-09
Segment: NEW VISITORS ONLY (no prior purchase record)

--- SESSION A ---
Visitor ID: anon-7f3a
Pages visited (in order):
  1. /catalog/tents/ultralight-bivy  [dwell: 45s]
  2. /catalog/tents/2p-backpacking-dome  [dwell: 112s]
  3. /catalog/tents/4p-family-dome  [dwell: 38s]
  4. /cart  [dwell: 12s]
Cart contents: 2p-backpacking-dome ($289)
No checkout initiated.
Mobile device: No

--- SESSION B ---
Visitor ID: anon-2c91
Pages visited (in order):
  1. /home
  2. /sale-clearance  [dwell: 67s]
  3. /catalog/footwear/trail-runners-x2  [sorted by: price low to high, dwell: 34s]
  4. /catalog/footwear/sandals-sport  [dwell: 20s]
Mobile device: Yes

--- SESSION C ---
Visitor ID: anon-b804
Pages visited (in order):
  1. /catalog/accessories/trekking-poles-pro  [dwell: 98s]
  2. /cart  [dwell: 25s]
  3. /shipping-info  [dwell: 53s]
No checkout initiated.
Mobile device: No

--- SESSION D ---
Visitor ID: anon-44ef
Pages visited (in order):
  1. /catalog/sleeping-bags/ultralight-20f  [dwell: 145s]
  2. /home
  3. /catalog/sleeping-bags/ultralight-20f  [dwell: 210s]
Cart: empty
Mobile device: Yes

--- SESSION E ---
Visitor ID: anon-9901
Pages visited (in order):
  1. /home  [dwell: 8s]
  2. /blog/best-tents-2024  [dwell: 18s]
Mobile device: No

=== END OF EXPORT ===
"""

with open(os.path.join(workspace, "sessions/raw/june_new_visitors.txt"), "w") as f:
    f.write(session_log)

# --- Distractor files ---

# Past campaign (irrelevant - loyalty win-back)
with open(os.path.join(workspace, "campaigns/past/loyalty_winback_q1.md"), "w") as f:
    f.write("""# Q1 Loyalty Win-Back Campaign
For customers with 90+ day lapse. Offer: 20% off next order. 
This is NOT a cold-start campaign. Do not apply these rules to new visitors.
""")

# Draft campaign for post-purchase (irrelevant)
with open(os.path.join(workspace, "campaigns/drafts/post_purchase_upsell.md"), "w") as f:
    f.write("""# Post-Purchase Upsell Flow
Trigger after confirmed order. Send accessory bundle offer 48h post-ship.
""")

# Old discount codes (distractors)
with open(os.path.join(workspace, "ops/discount_codes/active_codes.txt"), "w") as f:
    f.write("""WELCOME15 - 15% off, all items, no min (BLOCKED from stacking)
EARLYBIRD - $10 off $50+ (BLOCKED from stacking)
INFLUENCER_JUNE - 20% (BLOCKED from stacking)
TRAILBLAZE10 - 10% tents only, $100 min
""")

# Weekly analytics (distractor)
with open(os.path.join(workspace, "analytics/weekly/week23_summary.csv"), "w") as f:
    f.write("""date,sessions,new_visitors,bounce_rate,conversion_rate
2024-06-03,1240,830,0.58,0.021
2024-06-04,1389,912,0.61,0.019
""")

# Legal note (distractor but contains true info agent should not confuse)
with open(os.path.join(workspace, "legal/popup_consent_policy.txt"), "w") as f:
    f.write("""Popup consent: only show to users who have not opted out via cookie banner.
Email capture on popup is optional per GDPR Article 7 — do not require email to receive offer.
""")

# Catalog margin sheet (distractor / supports playbook)
with open(os.path.join(workspace, "catalog/tents/margin_notes.txt"), "w") as f:
    f.write("""Tent margin notes:
- Ultralight bivy: 38% margin
- 2p backpacking dome: 31% margin (high ticket >$400 threshold not met at $289)
- 4p family dome: 29% margin
Max safe discount on tents: 10% (see cold_start_playbook.md)
""")

with open(os.path.join(workspace, "catalog/accessories/margin_notes.txt"), "w") as f:
    f.write("""Accessories margin: avg 47%
Max safe discount: 20%
""")

with open(os.path.join(workspace, "catalog/footwear/margin_notes.txt"), "w") as f:
    f.write("""Footwear margin: avg 42%
Max safe discount: 15%
""")

# Fake old playbook version (distractor - agent should use references/cold_start_playbook.md)
with open(os.path.join(workspace, "campaigns/past/old_coldstart_notes_2023.txt"), "w") as f:
    f.write("""2023 cold start notes (OUTDATED - do not use):
- Offer 10% to everyone
- Popup on page load after 5s
- No segment targeting
These rules are superseded by references/cold_start_playbook.md
""")

# Monthly analytics (distractor)
with open(os.path.join(workspace, "analytics/monthly/may_cohort.json"), "w") as f:
    json.dump({"month": "May-2024", "new_visitor_conversion": 0.023, "avg_first_order": 94.50}, f, indent=2)

# Sleeping bags category (distractor)
with open(os.path.join(workspace, "catalog/sleeping_bags_info.txt"), "w") as f:
    f.write("""Sleeping bags: margin 35-40%. Treat as accessories for discount banding purposes.
""")

print("Workspace generated successfully.")