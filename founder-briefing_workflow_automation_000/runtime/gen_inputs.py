import os
import random

random.seed(42)

BASE = "/workspace"
os.makedirs(BASE, exist_ok=True)

# --- Distractor directory structure ---
dirs = [
    "crm_exports/archive/2024_q1",
    "crm_exports/archive/2024_q2",
    "crm_exports/pending",
    "open_house_events/westside/photos",
    "open_house_events/downtown",
    "marketing/flyers",
    "marketing/social_media/drafts",
    "templates/old",
    "templates/expired",
    "agent_notes/personal",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "crm_exports/archive/2024_q1/leads_jan.csv": "id,name,status\n1,Alice M.,Closed\n2,Bob T.,Lost\n",
    "crm_exports/archive/2024_q2/leads_apr.csv": "id,name,status\n10,Carol L.,Closed\n11,Dave K.,Lost\n",
    "crm_exports/pending/do_not_use.txt": "These leads are not yet verified. Hold for manager review.\n",
    "open_house_events/westside/photos/README.txt": "Photo folder - no text data here.\n",
    "open_house_events/downtown/parking_notes.txt": "Street parking available on Oak Ave after 2pm.\n",
    "marketing/flyers/spring_promo.txt": "Spring Open House Series - Join Us!\n",
    "marketing/social_media/drafts/ig_caption_draft.txt": "Beautiful 3BR in Maplewood - DM for details!\n",
    "templates/old/sms_template_v1.txt": "Hi [NAME], thanks for stopping by! Call us at 555-0100.\n",
    "templates/expired/email_blast_2023.txt": "Subject: Happy New Year from Sunrise Realty\nBody: ...\n",
    "agent_notes/personal/to_do_list.txt": "- Call contractor\n- Update MLS profile\n- Coffee with broker Thursday\n",
}
for rel_path, content in distractor_files.items():
    with open(os.path.join(BASE, rel_path), "w") as f:
        f.write(content)

# --- MAIN INPUT FILES (the messy real inputs the agent must process) ---

# 1. Open house sign-in sheet (messy, handwritten-style notes as text)
open_house_notes = """\
OPEN HOUSE SIGN-IN — 47 Birchwood Lane, Maplewood — Saturday, June 14

Arrivals & Notes (scribbled by showing assistant):

1. Marcus T. — came with wife, loved the backyard. Said they want to "move in before school starts" (August). 
   Pre-approved $620k with First Federal. Looking only in Maplewood or Riverside. Left number: 555-0181.
   Wife mentioned they also toured 22 Elm last week. Very enthusiastic. Wants to schedule private showing this week.

2. Priya S. — solo visit, seemed interested in layout. Said budget "maybe around 500k, not sure yet." 
   Timeline: "probably next few months." No financing info given. Email: priya.sharma88@freemail.net

3. Derek & Jess N. — couple. Derek said they're "just browsing" and rates feel too high right now.
   No budget given. No timeline. Said they'd "check back in the fall." No contact info left — Jess wrote her email on
   the sheet but it smudged. Could not recover.

4. Yolanda K. — cash buyer, very specific: 3BR min, Riverside District only, under $700k. 
   Said she needs to close within 60 days due to lease ending. Responded to our last SMS this morning.
   Phone: 555-0294. Mentioned she has toured 4 homes already and is ready to make offers.

5. Tom V. — retired, looking for "something smaller." No area preference, no budget, no timeline.
   Left business card: tom.v@vaultmail.com. Said his daughter is a realtor "elsewhere" and he's just exploring.

6. Amara J. — first-time buyer, nervous energy. Said she got pre-approved last month ($410k) and wants to stay
   in the Northside or Lakewood areas. Hoping to buy "in the next 6 weeks" and wants to do a tour this Thursday.
   Phone: 555-0377.
"""

with open(os.path.join(BASE, "open_house_events/westside/birchwood_open_house_notes.txt"), "w") as f:
    f.write(open_house_notes)

# 2. Inbound SMS/text inquiry thread (exported as plain text)
sms_thread = """\
INBOUND TEXT MESSAGES — Exported from Agency Phone 555-0100 — June 14-15

---
From: 555-0181 (Marcus T.)
[Sat 4:12pm] "Hey this is Marcus from the open house today. Awesome place. Can we do a private showing
maybe Tuesday or Wednesday? We're very motivated."

[Sat 6:30pm — Agent reply] "Hi Marcus! Absolutely, let's make it happen. I'll send you options first thing tomorrow."

[Sun 9:02am] "Great! Just FYI we are pre-approved and ready to move fast if the right place comes up."

---
From: 555-0294 (Yolanda K.)
[Sat 2:55pm] "Hi, I came to the open house on Birchwood. I'm a cash buyer looking in Riverside. Do you have
anything else in the area? Need to close by end of July."

[Sat 3:10pm — Agent reply] "Hi Yolanda! Yes, I have 2 more Riverside listings to show you. Want to connect Monday?"

[Sun 10:15am] "Yes Monday works. Send me the addresses and I'll drive by first."

---
From: 555-0377 (Amara J.)
[Sat 7:01pm] "Hi! I came to the open house. I'm a first time buyer, pre-approved for 410k. 
Are there homes in Northside under 400k right now?"

[No agent reply yet]

---
From: Unknown / No Name
[Sun 11:30am] "Hi, I heard about your listing. What's the price? Is it still available?"
[No agent reply yet]
"""

with open(os.path.join(BASE, "crm_exports/pending/sms_thread_june14_15.txt"), "w") as f:
    f.write(sms_thread)

# 3. Partial CRM export (CSV, some fields missing or messy)
crm_export = """\
lead_id,full_name,contact,source,budget,timeline,preapproved,area_pref,notes,last_contact
L001,Marcus T.,555-0181,Open House,620000,Before August,Yes - First Federal,Maplewood/Riverside,Wants private showing this week; very motivated,2024-06-15
L002,Priya S.,priya.sharma88@freemail.net,Open House,~500k?,next few months,,,"Seemed interested, solo visit",2024-06-14
L003,Derek N.,,Open House,,,,"","Just browsing, rates objection, no contact info recovered",2024-06-14
L004,Yolanda K.,555-0294,Open House,Under 700k,60 days / close by July,Cash,,Riverside only - 3BR min - toured 4 homes already,2024-06-15
L005,Tom V.,tom.v@vaultmail.com,Open House,,,,,"Retired, exploring, daughter is realtor",2024-06-14
L006,Amara J.,555-0377,Open House,410000,Next 6 weeks,Yes,Northside/Lakewood,First-time buyer wants Thursday tour,2024-06-14
"""

with open(os.path.join(BASE, "crm_exports/pending/crm_export_june14.csv"), "w") as f:
    f.write(crm_export)

print("Workspace initialized successfully.")
print(f"Files created under: {BASE}")