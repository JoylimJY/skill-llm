import os
import random
import csv
import json

random.seed(42)

WORKSPACE = "/workspace"

# --- Directory Structure ---
dirs = [
    "business/financials",
    "business/client_files",
    "business/raw_notes",
    "ops/task_logs",
    "ops/email_drafts",
    "ops/misc",
    "marketing/campaigns",
    "marketing/assets",
    "personal/ideas",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor Files ---

# Financial summary (distractor - partial, messy)
with open(os.path.join(WORKSPACE, "business/financials/q1_revenue.txt"), "w") as f:
    f.write("Q1 Revenue Summary\n")
    f.write("January: $8,400\n")
    f.write("February: $9,100\n")
    f.write("March: $8,800\n")
    f.write("Total Q1: $26,300\n")
    f.write("Note: 3 projects declined due to capacity\n")

with open(os.path.join(WORKSPACE, "business/financials/expenses_q1.csv"), "w") as f:
    f.write("month,category,amount\n")
    f.write("January,software,320\n")
    f.write("January,equipment,1200\n")
    f.write("February,software,320\n")
    f.write("March,software,320\n")
    f.write("March,freelance_help,800\n")

with open(os.path.join(WORKSPACE, "business/client_files/client_roster.txt"), "w") as f:
    f.write("Active Clients:\n")
    f.write("1. TechTalkTV - 4 videos/month - $2,200/mo\n")
    f.write("2. FitnessWith_Dana - 6 videos/month - $2,800/mo\n")
    f.write("3. GamersUnite_Channel - 3 videos/month - $1,500/mo\n")
    f.write("4. CookingWithMaria - 2 videos/month - $900/mo\n")
    f.write("\nDeclined (capacity full):\n")
    f.write("- StartupEdge: Offered $2,400/mo - DECLINED - no bandwidth\n")
    f.write("- DailyDevTips: Offered $1,800/mo - DECLINED - no bandwidth\n")

with open(os.path.join(WORKSPACE, "business/raw_notes/owner_notes.txt"), "w") as f:
    f.write("Random notes - March\n")
    f.write("====================\n")
    f.write("- Working until midnight almost every day this week\n")
    f.write("- Had to push back TechTalkTV deadline by 2 days\n")
    f.write("- Cannot take on more clients. Physically impossible.\n")
    f.write("- Thinking about hiring someone but not sure if I can afford it\n")
    f.write("- The thumbnail creation thing takes FOREVER every time\n")
    f.write("- Should I raise prices? Maybe.\n")
    f.write("- Leads are coming in fine from referrals, that's not the issue\n")
    f.write("- Issue is I literally can't deliver more even if I wanted to\n")

with open(os.path.join(WORKSPACE, "ops/email_drafts/new_client_template.txt"), "w") as f:
    f.write("Subject: Welcome to [Your Name] Video Production!\n\n")
    f.write("Hi [Client Name],\n\n")
    f.write("So excited to work with you! Here's what happens next...\n")
    f.write("[INCOMPLETE - never finished this template]\n")

with open(os.path.join(WORKSPACE, "ops/misc/tool_subscriptions.txt"), "w") as f:
    f.write("Monthly Tools:\n")
    f.write("- Adobe Creative Cloud: $55/mo\n")
    f.write("- Frame.io: $15/mo\n")
    f.write("- Descript: $24/mo\n")
    f.write("- Notion: $8/mo\n")
    f.write("- Rev.com (transcription): ~$80/mo avg\n")
    f.write("- Calendly: $10/mo\n")

with open(os.path.join(WORKSPACE, "marketing/campaigns/referral_notes.txt"), "w") as f:
    f.write("Referral campaign notes:\n")
    f.write("- 5 referrals received in Q1\n")
    f.write("- Close rate on referrals: ~80%\n")
    f.write("- Not the bottleneck - leads are fine\n")

with open(os.path.join(WORKSPACE, "marketing/assets/brand_colors.txt"), "w") as f:
    f.write("Primary: #1A1A2E\nSecondary: #E94560\nAccent: #0F3460\n")

with open(os.path.join(WORKSPACE, "personal/ideas/future_ideas.txt"), "w") as f:
    f.write("Ideas to explore later:\n")
    f.write("- Video editing course\n")
    f.write("- YouTube channel about filmmaking\n")
    f.write("- Preset packs for DaVinci Resolve\n")

with open(os.path.join(WORKSPACE, "ops/misc/passwords_DONOTEDIT.txt"), "w") as f:
    f.write("DO NOT SHARE\n")
    f.write("Frame.io: see 1password\n")
    f.write("Adobe: see 1password\n")

# --- CORE PROBLEM FILES ---

# 1. Business Metrics CSV - leads, pipeline, capacity
with open(os.path.join(WORKSPACE, "business/metrics_q1.csv"), "w", newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["month", "new_leads", "leads_converted", "projects_declined_capacity",
                     "hours_worked_owner", "revenue_usd", "support_tickets", "avg_delivery_days"])
    writer.writerow(["January",  18, 14, 1, 68, 8400,  4, 5])
    writer.writerow(["February", 21, 15, 2, 72, 9100,  3, 6])
    writer.writerow(["March",    19, 13, 3, 76, 8800,  5, 7])

# 2. Task log - recurring tasks with time and frequency data
with open(os.path.join(WORKSPACE, "ops/task_logs/recurring_tasks.csv"), "w", newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["task_name", "avg_minutes_per_occurrence", "occurrences_per_month",
                     "requires_judgment", "notes"])
    # Should be automated (>15min, >10x/month)
    writer.writerow(["thumbnail_creation",       25, 15, "no",  "Same template every time, just swap text/image"])
    writer.writerow(["send_invoice",              20, 15, "no",  "Repeated for each project completion"])
    writer.writerow(["upload_and_tag_video",      18, 15, "no",  "Upload to Frame.io, add tags, notify client"])
    # Edge case: meets time but NOT frequency (only 6x/month) -> should NOT be automated per rule
    writer.writerow(["client_strategy_call_prep", 30,  6, "yes", "Requires custom research per client"])
    # Edge case: meets frequency but NOT time (only 10min) -> should NOT be automated per rule
    writer.writerow(["reply_to_client_slack",     10, 40, "no",  "Quick messages, not worth automating"])
    # Should delegate (judgment-based, high time)
    writer.writerow(["rough_cut_editing",         180, 15, "yes", "Creative decisions required"])
    # Another automation candidate
    writer.writerow(["weekly_revenue_report",     20, 4, "no", "Pull numbers from stripe and make spreadsheet"])

# 3. Hiring consideration note
with open(os.path.join(WORKSPACE, "ops/task_logs/hiring_consideration.txt"), "w") as f:
    f.write("Hiring Consideration Notes (rough)\n")
    f.write("=====================================\n")
    f.write("Tasks I want to offload:\n")
    f.write("- Rough cut editing: ~45 hrs/month (15 videos x ~3hrs each)\n")
    f.write("  This is the main thing. I'd still do final cut and color.\n")
    f.write("- Thumbnail creation: already in task log\n")
    f.write("- Invoice sending: already in task log\n")
    f.write("\n")
    f.write("Question: should I hire a contractor or a full employee for editing help?\n")
    f.write("The editing work is about 45 hours per month consistently.\n")
    f.write("Not sure how to decide.\n")

# 4. Process notes for the most frequent task (thumbnail creation - candidate for SOP)
with open(os.path.join(WORKSPACE, "ops/task_logs/thumbnail_process_messy_notes.txt"), "w") as f:
    f.write("How I do thumbnails (brain dump):\n")
    f.write("-----------------------------------\n")
    f.write("open photoshop, load the base template from /Templates/thumb_base.psd\n")
    f.write("drag in the best still frame from the video render folder\n")
    f.write("change the title text to match the video title\n")
    f.write("adjust contrast if the image looks washed out\n")
    f.write("export as JPG 1280x720 to the client's Google Drive folder\n")
    f.write("ping client on Slack that thumbnail is ready for review\n")
    f.write("sometimes client asks for changes - go back and redo text color or image\n")
    f.write("common problem: wrong aspect ratio if you forget to check canvas settings\n")
    f.write("solution to that: always check Image > Canvas Size first\n")
    f.write("another issue: client cant find file - make sure shared Drive folder is correct\n")
    f.write("tools needed: Photoshop CC, access to client Google Drive, video render files\n")

print("Workspace generated successfully.")
print(f"Files created in: {WORKSPACE}")