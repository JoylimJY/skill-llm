#!/usr/bin/env python3
import os
import random

random.seed(42)

base = "/workspace"

# --- Deep distractor structure ---
dirs = [
    "research/interviews/raw",
    "research/interviews/processed",
    "research/surveys",
    "product/roadmap",
    "product/specs/v1",
    "product/specs/v2",
    "engineering/backend/auth",
    "engineering/backend/billing",
    "engineering/frontend",
    "analytics/dashboards",
    "analytics/exports",
    "ops/runbooks",
    "design/mockups/onboarding",
    "design/mockups/dashboard",
    "legal/contracts",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# --- Distractor files (irrelevant) ---
distractors = {
    "product/roadmap/q3_themes.txt": "Theme 1: Growth\nTheme 2: Retention\nTheme 3: Monetization\n",
    "product/specs/v1/auth_spec.md": "# Auth Spec v1\nBasic username/password only.\n",
    "product/specs/v2/auth_spec.md": "# Auth Spec v2\nAdds SSO support.\n",
    "engineering/backend/auth/jwt_notes.txt": "Use HS256. Expiry 24h.\n",
    "engineering/backend/billing/stripe_integration.txt": "Webhook endpoint: /hooks/stripe\n",
    "engineering/frontend/component_inventory.csv": "component,status\nButton,stable\nModal,beta\nToast,deprecated\n",
    "analytics/dashboards/weekly_metrics.json": '{"dau": 1200, "mau": 8400, "churn": 0.04}\n',
    "analytics/exports/june_cohort.csv": "user_id,signup_date,converted\n1001,2024-06-01,true\n1002,2024-06-03,false\n",
    "ops/runbooks/deploy_prod.sh": "#!/bin/bash\necho 'deploying...'\n",
    "design/mockups/onboarding/wireframe_notes.txt": "Step 1: Welcome screen. Step 2: Profile setup.\n",
    "design/mockups/dashboard/color_palette.txt": "Primary: #4A90E2\nSecondary: #7ED321\n",
    "legal/contracts/vendor_nda_template.txt": "This NDA is entered into between...\n",
    "research/surveys/q2_nps_raw.csv": "user_id,score,comment\n201,8,'Good but slow'\n202,3,'Very confusing'\n203,9,'Love it'\n",
    "research/interviews/processed/summary_old.txt": "Old summary from Q1 - superseded.\n",
}
for path, content in distractors.items():
    with open(os.path.join(base, path), "w") as f:
        f.write(content)

# --- REAL INPUT FILES the agent must ingest ---

# Interview transcript 1 — messy, realistic
interview_1 = """\
User Research Interview — Participant: Sarah K.
Date: 2024-07-08
Conducted by: Marcus T. (UX Researcher)
Source: https://notion.so/acme/interviews/sarah-k-july-2024
Platform: Google Meet recording + notes

--- TRANSCRIPT (lightly edited) ---

Marcus: Can you walk me through the first time you logged in?

Sarah: Sure. So I got the invite email, clicked the link, and then it dropped me onto this... dashboard? I think? 
But there was no explanation of what I was supposed to do. I clicked around for like ten minutes and honestly 
I almost just closed the tab.

Marcus: What made you stay?

Sarah: I found the "Getting Started" checklist thing on the left side. But it was hidden under a collapsed panel, 
I didn't even notice it at first. Once I found that, things started making sense.

Marcus: Were there any other friction points?

Sarah: The terminology is really confusing. Like, what's the difference between a "Workspace" and a "Project"?  
I had no idea. I ended up creating three workspaces thinking they were projects. Had to delete them later.

Marcus: On a scale of 1-10, how would you rate the initial onboarding experience?

Sarah: Maybe a 4? It gets better once you figure it out, but the first 20 minutes are rough.

--- END TRANSCRIPT ---
"""

# Interview transcript 2 — different participant, similar themes
interview_2 = """\
User Research Interview — Participant: Dev P.
Date: 2024-07-10
Conducted by: Priya N. (UX Researcher)
Source: https://notion.so/acme/interviews/dev-p-july-2024
Platform: Zoom call

--- NOTES ---

Key themes from Dev's session:

- First login experience: Dev was immediately lost. Quote: "I didn't know if I should start with a Project or 
  a Workspace. The naming is confusing." Echoes the confusion Sarah K. mentioned.

- The empty state: Dev noted the dashboard showed no guidance when empty. "There was just... nothing. 
  I thought the app was broken."

- Positive: Once Dev found the template library, they said the setup became "really fast and intuitive."

- Feature request: Dev wants an interactive walkthrough for the first login, similar to what Notion and 
  Figma do.

Rating: 3/10 for first-time experience, 8/10 once familiar.

--- END NOTES ---
"""

# Slack channel export snippet — about onboarding decision
slack_export = """\
#product-decisions — Slack Export
Date range: 2024-07-11
Source URL: https://acme.slack.com/archives/C01234567/p1720742400

[10:32 AM] Elena V. (Product Lead):
Quick update on the onboarding revamp decision: after reviewing the user research from last week's interviews,
we've decided to prioritize an interactive first-run walkthrough as our Q3 P0. This is directly driven by 
the feedback that new users are consistently lost during initial setup.

[10:35 AM] Raj M. (Engineering Lead):
Confirmed. We'll use Shepherd.js for the walkthrough implementation. Targeting the July 31st sprint for the 
first prototype.

[10:41 AM] Elena V. (Product Lead):
Also noting for the record: we explicitly chose NOT to do a video tutorial, because our data shows <15% of 
users watch embedded videos past the 30-second mark.

[10:44 AM] Marcus T. (UX):
The core confusion points we need to address in the walkthrough: (1) Workspace vs Project naming, 
(2) the hidden Getting Started checklist, (3) empty dashboard state.
"""

with open(os.path.join(base, "research/interviews/raw/sarah_k_interview_july2024.txt"), "w") as f:
    f.write(interview_1)

with open(os.path.join(base, "research/interviews/raw/dev_p_interview_july2024.txt"), "w") as f:
    f.write(interview_2)

with open(os.path.join(base, "research/interviews/raw/slack_product_decisions_july11.txt"), "w") as f:
    f.write(slack_export)

print("Workspace generated successfully.")
print("Files to process:")
print("  research/interviews/raw/sarah_k_interview_july2024.txt")
print("  research/interviews/raw/dev_p_interview_july2024.txt")
print("  research/interviews/raw/slack_product_decisions_july11.txt")