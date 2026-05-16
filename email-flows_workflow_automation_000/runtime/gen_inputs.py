import os
import random

random.seed(42)

workspace = "/workspace"

# --- Create deeply nested distractor structure ---
dirs = [
    "internal/marketing/campaigns/q4_2024",
    "internal/marketing/campaigns/q3_2024",
    "internal/marketing/assets/templates",
    "internal/product/roadmap",
    "internal/product/specs/v2",
    "internal/engineering/infra",
    "internal/sales/crm_exports",
    "internal/finance/reports",
    "docs/user_guides",
    "docs/api_reference",
    "scratch/old_ideas",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "internal/marketing/campaigns/q4_2024/campaign_brief.txt": (
        "Q4 2024 Campaign: Push for enterprise tier upgrade.\n"
        "Target: users on Pro plan > 6 months.\n"
        "Channel: LinkedIn + cold email.\n"
        "Budget: $12,000\n"
    ),
    "internal/marketing/campaigns/q3_2024/results_summary.csv": (
        "campaign,sent,opened,clicked,converted\n"
        "welcome_seq,4200,2100,840,180\n"
        "trial_nudge,1800,720,216,54\n"
        "churn_winback,600,150,30,8\n"
    ),
    "internal/marketing/assets/templates/generic_newsletter.html": (
        "<html><body><h1>{{product_name}} Newsletter</h1>"
        "<p>Hi {{first_name}}, here's what's new this month...</p></body></html>\n"
    ),
    "internal/product/roadmap/2025_themes.md": (
        "# 2025 Product Themes\n"
        "1. AI-assisted task prioritization\n"
        "2. Deep Slack/Teams integrations\n"
        "3. Advanced reporting dashboard\n"
        "4. Mobile app revamp\n"
    ),
    "internal/product/specs/v2/activation_events.json": (
        '{\n'
        '  "tier1": ["signup_complete", "first_project_created"],\n'
        '  "tier2": ["first_team_member_invited", "first_task_assigned"],\n'
        '  "tier3": ["first_report_viewed", "integration_connected"]\n'
        '}\n'
    ),
    "internal/engineering/infra/sendgrid_config_old.yaml": (
        "provider: sendgrid\n"
        "api_key: SG.REDACTED\n"
        "from_email: noreply@taskflow.io\n"
        "ip_pool: shared\n"
        "tracking: true\n"
    ),
    "internal/sales/crm_exports/leads_oct2024.csv": (
        "email,company,plan,days_since_signup\n"
        "alice@acme.com,Acme Corp,free_trial,3\n"
        "bob@widgets.io,Widgets Inc,free_trial,12\n"
        "carol@startup.vc,Startup VC,freemium,45\n"
    ),
    "internal/finance/reports/mrr_nov2024.txt": (
        "MRR: $48,200\n"
        "New MRR: $6,100\n"
        "Churned MRR: $2,300\n"
        "Expansion MRR: $1,400\n"
        "Net New MRR: $5,200\n"
    ),
    "docs/user_guides/getting_started.md": (
        "# Getting Started with TaskFlow\n\n"
        "## Step 1: Create your first project\n"
        "Click 'New Project' from the dashboard...\n\n"
        "## Step 2: Invite your team\n"
        "Go to Settings > Team Members...\n\n"
        "## Step 3: Assign your first task\n"
        "Inside your project, click 'Add Task'...\n"
    ),
    "docs/api_reference/webhooks.md": (
        "# Webhook Events\n\n"
        "| Event | Payload |\n"
        "|---|---|\n"
        "| user.signup | {user_id, email, plan} |\n"
        "| project.created | {project_id, user_id} |\n"
        "| task.assigned | {task_id, assignee_id} |\n"
        "| trial.expiring | {user_id, days_left} |\n"
        "| subscription.upgraded | {user_id, new_plan} |\n"
    ),
    "scratch/old_ideas/email_ideas_2023.txt": (
        "- Maybe send a weekly digest?\n"
        "- Ask users why they didn't upgrade\n"
        "- Highlight power users' workflows\n"
        "- A/B test plain text vs. HTML\n"
        "NOTE: These were never implemented. Just brainstorming.\n"
    ),
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE CORE INPUT FILE: Discovery Brief ---
context_brief = """\
TASKFLOW - EMAIL AUTOMATION DISCOVERY BRIEF
===========================================
Prepared by: Maya Chen, Head of Growth
Date: 2024-11-15

DISCOVERY ANSWERS
-----------------

Q1: PRODUCT & USER JOURNEY
Product: TaskFlow - a B2B SaaS project management tool for small engineering teams (5-50 people).
User journey:
  - Signup (free 14-day trial, no credit card required)
  - Onboarding: User creates their first project, invites team members, assigns tasks
  - Activation: Team completes their first sprint (all tasks in a project marked done)
  - Paid conversion: Upgrade to Pro ($29/user/mo) or Business ($59/user/mo)
  - Long-term retention: Daily active use, integrations with Jira/GitHub/Slack

Q2: BUSINESS MODEL
Reverse trial: Users get full Pro features for 14 days, then drop to a limited free tier
if they don't upgrade. Free tier is intentionally limited (max 2 projects, no integrations).

Q3: KEY ACTIVATION MILESTONES
1. First project created (within 24h of signup) - strongest predictor of 7-day retention
2. First team member invited (within 48h) - 2.3x higher trial conversion
3. First task assigned to another user (within 72h) - correlates with sprint completion
4. First sprint completed (all tasks marked done in a project) - 78% paid conversion rate
5. First integration connected (GitHub, Jira, or Slack) - highest LTV segment

Q4: CURRENT EMAIL AUTOMATION
We have one automated email: a basic welcome email that fires on signup. It just says
"Welcome to TaskFlow!" with a link to our docs. Open rate is 58%, but click-through
is only 4% and almost nobody completes onboarding after receiving it. That's it.
No other automated emails exist.

Q5: EMAIL TOOL
We are using Customer.io. We have behavioral event tracking set up via Segment.
All the webhook events (project.created, task.assigned, trial.expiring_soon,
subscription.upgraded, user.inactive_7d, user.inactive_30d) are already firing.

Q6: BIGGEST EMAIL CHALLENGE
Our trial-to-paid conversion rate is 8%. Industry benchmark for our segment is 18-22%.
We suspect users aren't reaching the "first sprint completed" milestone before the trial
ends. Secondary challenge: 40% of our free-tier users go completely inactive within
30 days of downgrade, and we have nothing to bring them back.
"""

brief_path = os.path.join(workspace, "context_brief.txt")
with open(brief_path, "w") as f:
    f.write(context_brief)

print("Workspace generated successfully.")
print(f"Files created: {len(distractors) + 1} files across {len(dirs)} directories.")