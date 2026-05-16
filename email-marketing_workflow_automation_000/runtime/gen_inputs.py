import os
import csv
import random
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = "/workspace"

# --- Directory structure ---
dirs = [
    "codepulse/marketing/campaigns",
    "codepulse/marketing/templates",
    "codepulse/marketing/reports",
    "codepulse/marketing/assets",
    "codepulse/engineering/docs",
    "codepulse/engineering/configs",
    "codepulse/sales/crm_exports",
    "codepulse/sales/pipeline",
    "codepulse/product/roadmap",
    "codepulse/product/feedback",
    "codepulse/legal/compliance",
    "codepulse/ops/infra",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "codepulse/marketing/campaigns/q3_social_plan.txt": "Instagram: 3x/week\nLinkedIn: daily\nTwitter: 5x/week\nBudget: $5000",
    "codepulse/marketing/templates/newsletter_template_v2.html": "<html><body><h1>{{title}}</h1><p>{{body}}</p></body></html>",
    "codepulse/marketing/assets/brand_colors.txt": "Primary: #2D6BE4\nSecondary: #1A1A2E\nAccent: #FF6B35",
    "codepulse/engineering/docs/api_reference.md": "# CodePulse API\n## /review endpoint\nPOST /api/v1/review\nAuth: Bearer token",
    "codepulse/engineering/configs/staging.env": "DB_HOST=staging-db.internal\nREDIS_URL=redis://staging-cache:6379\nDEBUG=true",
    "codepulse/sales/pipeline/q4_targets.csv": "rep,quota,current\nAlice,100000,42000\nBob,80000,71000\nCarol,120000,95000",
    "codepulse/sales/crm_exports/deals_oct.json": '{"deals":[{"id":1,"value":15000,"stage":"proposal"},{"id":2,"value":8500,"stage":"closed"}]}',
    "codepulse/product/roadmap/2024_features.txt": "Q1: Git integration\nQ2: Slack notifications\nQ3: JIRA sync\nQ4: AI suggestions",
    "codepulse/product/feedback/user_interviews.txt": "User 1: Wants faster CI integration\nUser 2: Needs better diff view\nUser 3: Price point concern",
    "codepulse/legal/compliance/gdpr_checklist.txt": "[ ] Data processing agreement\n[ ] Cookie consent\n[ ] Right to erasure workflow",
    "codepulse/ops/infra/monitoring_alerts.txt": "Alert: CPU > 80% -> PagerDuty\nAlert: Error rate > 1% -> Slack #ops",
    "codepulse/marketing/reports/old_campaign_stats_2023.txt": "Campaign: DevSummit 2023\nSent: 4200\nOpens: 1050\nClicks: 189\nNote: outdated metrics, do not use",
}
for path, content in distractors.items():
    with open(os.path.join(WORKSPACE, path), "w") as f:
        f.write(content)

# --- Main input: messy subscriber CSV ---
# We'll generate ~2000 subscribers with various states
now = datetime.now()

def rand_date_within(days_ago_min, days_ago_max):
    delta = random.randint(days_ago_min, days_ago_max)
    return (now - timedelta(days=delta)).strftime("%Y-%m-%d")

def rand_date_subscribed(days_ago):
    delta = random.randint(days_ago - 5, days_ago + 5)
    return (now - timedelta(days=delta)).strftime("%Y-%m-%d")

rows = []
# Segment composition (to engineer specific metric outcomes):
# Total = 2000 emails sent in last campaign
# Bounces: 90 hard bounces = 4.5% bounce rate (WARNING zone)
# Unsubscribes: 18 = 0.9% (WARNING zone)
# Spam complaints: 5 = 0.25% (WARNING zone, near critical)
# Opens: 380 = 19% (WARNING zone)
# Clicks: 36 = 1.8% (WARNING zone)

subscriber_id = 1

# 1. Engaged subscribers (opened within 30 days) - 380 openers from 1800 active
engaged_count = 380
for i in range(engaged_count):
    rows.append({
        "id": subscriber_id,
        "email": f"engaged_user_{i}@devteam.io",
        "first_name": random.choice(["Alex", "Sam", "Jordan", "Taylor", "Morgan", "Casey"]),
        "last_name": random.choice(["Smith", "Chen", "Patel", "Kim", "Williams"]),
        "subscribed_date": rand_date_subscribed(random.randint(10, 200)),
        "last_opened_date": rand_date_within(1, 29),
        "last_clicked_date": rand_date_within(1, 29) if i < 36 else "",
        "status": "active",
        "is_customer": "true" if i < 80 else "false",
        "tags": "opened_pricing_page" if i < 36 else "",
        "hard_bounce": "false",
        "unsubscribed": "false",
        "spam_complaint": "false",
        "emails_sent": "1",
    })
    subscriber_id += 1

# 2. Unengaged (no open in 30-89 days) - 550 subscribers
for i in range(550):
    rows.append({
        "id": subscriber_id,
        "email": f"warm_user_{i}@company.com",
        "first_name": random.choice(["Drew", "Robin", "Blake", "Reese"]),
        "last_name": random.choice(["Johnson", "Brown", "Davis", "Miller"]),
        "subscribed_date": rand_date_subscribed(random.randint(60, 300)),
        "last_opened_date": rand_date_within(31, 89),
        "last_clicked_date": "",
        "status": "active",
        "is_customer": "false",
        "tags": "",
        "hard_bounce": "false",
        "unsubscribed": "false",
        "spam_complaint": "false",
        "emails_sent": "1",
    })
    subscriber_id += 1

# 3. Sunset candidates (no open in 90+ days) - 572 subscribers
for i in range(572):
    rows.append({
        "id": subscriber_id,
        "email": f"cold_user_{i}@oldco.net",
        "first_name": random.choice(["Pat", "Quinn", "Skyler", "Avery"]),
        "last_name": random.choice(["Wilson", "Moore", "Taylor", "Anderson"]),
        "subscribed_date": rand_date_subscribed(random.randint(100, 500)),
        "last_opened_date": rand_date_within(91, 365),
        "last_clicked_date": "",
        "status": "active",
        "is_customer": "false",
        "tags": "",
        "hard_bounce": "false",
        "unsubscribed": "false",
        "spam_complaint": "false",
        "emails_sent": "1",
    })
    subscriber_id += 1

# 4. New subscribers (subscribed within last 7 days, no open history)
for i in range(80):
    rows.append({
        "id": subscriber_id,
        "email": f"new_signup_{i}@startup.io",
        "first_name": random.choice(["Jamie", "Lee", "Kai", "Phoenix"]),
        "last_name": random.choice(["Thomas", "Jackson", "White", "Harris"]),
        "subscribed_date": rand_date_subscribed(random.randint(0, 7)),
        "last_opened_date": "",
        "last_clicked_date": "",
        "status": "active",
        "is_customer": "false",
        "tags": "",
        "hard_bounce": "false",
        "unsubscribed": "false",
        "spam_complaint": "false",
        "emails_sent": "0",
    })
    subscriber_id += 1

# 5. Hard bounces - 90 subscribers
for i in range(90):
    rows.append({
        "id": subscriber_id,
        "email": f"bounce_{i}@nonexistent-domain-xyz.com",
        "first_name": "Unknown",
        "last_name": "User",
        "subscribed_date": rand_date_subscribed(random.randint(30, 400)),
        "last_opened_date": "",
        "last_clicked_date": "",
        "status": "bounced",
        "is_customer": "false",
        "tags": "",
        "hard_bounce": "true",
        "unsubscribed": "false",
        "spam_complaint": "false",
        "emails_sent": "1",
    })
    subscriber_id += 1

# 6. Unsubscribed - 18
for i in range(18):
    rows.append({
        "id": subscriber_id,
        "email": f"unsub_{i}@example.org",
        "first_name": random.choice(["Dana", "Erin"]),
        "last_name": random.choice(["Lewis", "Walker"]),
        "subscribed_date": rand_date_subscribed(random.randint(20, 200)),
        "last_opened_date": rand_date_within(30, 180),
        "last_clicked_date": "",
        "status": "unsubscribed",
        "is_customer": "false",
        "tags": "",
        "hard_bounce": "false",
        "unsubscribed": "true",
        "spam_complaint": "false",
        "emails_sent": "1",
    })
    subscriber_id += 1

# 7. Spam complaints - 5
for i in range(5):
    rows.append({
        "id": subscriber_id,
        "email": f"spam_complaint_{i}@isp.net",
        "first_name": "Complaint",
        "last_name": "User",
        "subscribed_date": rand_date_subscribed(random.randint(30, 200)),
        "last_opened_date": rand_date_within(60, 180),
        "last_clicked_date": "",
        "status": "complaint",
        "is_customer": "false",
        "tags": "",
        "hard_bounce": "false",
        "unsubscribed": "false",
        "spam_complaint": "true",
        "emails_sent": "1",
    })
    subscriber_id += 1

# 8. VIP (customers who opened in last 30 days, tagged - these are the 80 from engaged)
# Already included above — ensure they're flagged properly
# Add a few more explicit VIPs who are customers with high engagement
for i in range(25):
    rows.append({
        "id": subscriber_id,
        "email": f"vip_customer_{i}@enterprise.com",
        "first_name": random.choice(["Chris", "Andrea", "Marcus"]),
        "last_name": random.choice(["Roberts", "Scott", "Turner"]),
        "subscribed_date": rand_date_subscribed(random.randint(30, 365)),
        "last_opened_date": rand_date_within(1, 14),
        "last_clicked_date": rand_date_within(1, 14),
        "status": "active",
        "is_customer": "true",
        "tags": "opened_pricing_page,clicked_upgrade",
        "hard_bounce": "false",
        "unsubscribed": "false",
        "spam_complaint": "false",
        "emails_sent": "1",
    })
    subscriber_id += 1

# Shuffle to make it messy
random.shuffle(rows)

# Inject some messy data: missing fields, inconsistent casing, extra whitespace
messy_indices = random.sample(range(len(rows)), 40)
for idx in messy_indices:
    field = random.choice(["last_opened_date", "tags", "first_name"])
    if field == "last_opened_date" and rows[idx]["last_opened_date"]:
        rows[idx]["last_opened_date"] = rows[idx]["last_opened_date"].replace("-", "/")  # wrong format
    elif field == "first_name":
        rows[idx]["first_name"] = rows[idx]["first_name"].upper()  # ALL CAPS name

csv_path = os.path.join(WORKSPACE, "codepulse/sales/crm_exports/subscribers_raw.csv")
fieldnames = ["id", "email", "first_name", "last_name", "subscribed_date",
              "last_opened_date", "last_clicked_date", "status",
              "is_customer", "tags", "hard_bounce", "unsubscribed",
              "spam_complaint", "emails_sent"]

with open(csv_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} subscriber records.")
print(f"Breakdown: {engaged_count} engaged, 550 warm, 572 cold/sunset, 80 new, 90 bounced, 18 unsub, 5 complaint, 25 VIP customers")

# --- Campaign brief ---
brief_path = os.path.join(WORKSPACE, "codepulse/marketing/campaigns/launch_brief.txt")
with open(brief_path, "w") as f:
    f.write("""CodePulse v2.0 Launch Campaign Brief
======================================
Product: CodePulse v2.0 - AI-powered code review automation
Launch Date: 2 weeks from today
Target: All active subscribers

Goals:
- Re-activate cold subscribers before launch
- Welcome new sign-ups with proper onboarding
- Reward loyal customers with early access
- Understand current list health before sending

Questions from Head of Marketing:
1. Is our list healthy enough to run this campaign? What are our risk areas?
2. How should we group/organize our subscribers for this launch?
3. What should the new subscriber welcome schedule look like (day-by-day plan)?

Deliverable: A JSON report covering all three questions.
Filename: campaign_readiness_report.json
Location: codepulse/marketing/reports/
""")

print("Setup complete.")