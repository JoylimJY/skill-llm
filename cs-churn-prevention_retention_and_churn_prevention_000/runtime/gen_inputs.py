import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# ── Directory structure (deep, realistic, distracting) ─────────────────────
dirs = [
    "internal/marketing/campaigns/q1",
    "internal/marketing/campaigns/q2",
    "internal/marketing/brand",
    "internal/product/roadmap",
    "internal/product/specs/payments",
    "internal/product/specs/onboarding",
    "internal/engineering/backend/billing",
    "internal/engineering/backend/notifications",
    "internal/engineering/frontend/settings",
    "internal/data/dashboards",
    "internal/data/exports",
    "internal/cs/playbooks",
    "internal/cs/escalations",
    "scripts",
    "references",
    "deliverables",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = {
    "internal/marketing/campaigns/q1/email_blast_march.txt": (
        "Q1 email blast targeting reactivation leads. Open rate: 14%. Click rate: 2.1%."
    ),
    "internal/marketing/campaigns/q2/pipeline_targets.csv": (
        "segment,target_mql,actual_mql\nEnterprise,120,98\nMid-market,300,312\nSMB,600,541"
    ),
    "internal/marketing/brand/tone_guide.md": (
        "# Brand Tone\nFriendly, direct, no jargon. Avoid 'leverage' and 'synergy'."
    ),
    "internal/product/roadmap/2026_themes.md": (
        "## Themes\n1. Collaboration\n2. Automation\n3. Reporting\n4. Mobile"
    ),
    "internal/product/specs/payments/stripe_integration_notes.md": (
        "# Stripe Integration\nWebhooks configured: invoice.created, charge.succeeded.\n"
        "Customer portal: not yet customized.\nSmart Retries: currently DISABLED."
    ),
    "internal/product/specs/onboarding/checklist.md": (
        "## Onboarding checklist\n- [ ] Connect calendar\n- [ ] Invite team\n- [ ] Create first project"
    ),
    "internal/engineering/backend/billing/subscription_model.py": (
        "class Subscription:\n    def cancel(self):\n        self.status = 'cancelled'\n        self.save()\n"
        "    # TODO: add cancel reason capture\n    # TODO: add retry logic\n"
    ),
    "internal/engineering/backend/notifications/email_service.py": (
        "def send_email(to, subject, body):\n    # TODO: implement\n    pass\n"
    ),
    "internal/engineering/frontend/settings/cancel_button.jsx": (
        "// Cancel button — currently calls DELETE /subscriptions/{id} directly\n"
        "// No confirmation dialog, no survey, no intercept\n"
        "<Button onClick={handleCancel}>Cancel Subscription</Button>\n"
    ),
    "internal/data/dashboards/kpis.json": json.dumps({
        "monthly_churn_rate": 0.062,
        "mrr": 148500,
        "active_customers": 990,
        "voluntary_churn_split": "unknown",
        "involuntary_churn_split": "unknown",
        "save_rate": None,
        "exit_survey_completion": None,
    }, indent=2),
    "internal/data/exports/churned_customers_feb.csv": (
        "customer_id,cancel_date,reason_captured\n"
        "C001,2026-02-03,\nC002,2026-02-07,\nC003,2026-02-11,\n"
        "C004,2026-02-14,\nC005,2026-02-19,too expensive\n"
    ),
    "internal/cs/playbooks/renewal_playbook.md": (
        "# Renewal Playbook\nFor accounts >$500/mo, CS to reach out 60 days before renewal.\n"
        "Offer multi-year discount if health score >7."
    ),
    "internal/cs/escalations/open_tickets.txt": (
        "Ticket #1042: User says cancel button not working\n"
        "Ticket #1051: User was charged after cancellation\n"
        "Ticket #1063: User wants refund — did not know account would continue\n"
    ),
    "scripts/mrr_forecast.py": (
        "# MRR Forecast tool\nimport sys\nprint('MRR forecast: not yet implemented')\n"
    ),
    "scripts/churn_impact_calculator.py": (
        "#!/usr/bin/env python3\n"
        "# Churn Impact Calculator\n"
        "import sys\n\n"
        "def main():\n"
        "    mrr = float(input('Current MRR ($): '))\n"
        "    churn_rate = float(input('Monthly churn rate (e.g. 0.05 for 5%): '))\n"
        "    save_rate = float(input('Target save rate (e.g. 0.20 for 20%): '))\n"
        "    recovery_rate = float(input('Target recovery rate (e.g. 0.30 for 30%): '))\n"
        "    involuntary_pct = float(input('Involuntary churn % of total (e.g. 0.30): '))\n\n"
        "    monthly_lost = mrr * churn_rate\n"
        "    voluntary_lost = monthly_lost * (1 - involuntary_pct)\n"
        "    involuntary_lost = monthly_lost * involuntary_pct\n"
        "    saved_voluntary = voluntary_lost * save_rate\n"
        "    recovered_involuntary = involuntary_lost * recovery_rate\n"
        "    total_monthly_saved = saved_voluntary + recovered_involuntary\n"
        "    annual_impact = total_monthly_saved * 12\n\n"
        "    print(f'\\nMonthly MRR saved: ${total_monthly_saved:,.2f}')\n"
        "    print(f'Annual impact: ${annual_impact:,.2f}')\n\n"
        "if __name__ == '__main__':\n"
        "    main()\n"
    ),
    "references/pricing_notes.md": (
        "# Pricing\nStarter: $99/mo, Pro: $149/mo, Business: $249/mo\n"
        "Annual discount: 20%\nAll plans monthly billing by default.\n"
    ),
}

for rel_path, content in distractors.items():
    full_path = os.path.join(WORKSPACE, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# ── THE PROBLEM: Existing broken cancel flow description ─────────────────────
# This is what the agent must audit using the scorecard
broken_flow = """# TaskFlow Pro — Current Cancel Flow Description

## How cancellation currently works (as of March 2026)

### Entry point
- The "Cancel plan" option is located inside Account > Settings > Billing > Advanced > Danger Zone.
- It is not visible from the main Settings page — the user must expand "Advanced" to see it.
- On mobile, this section is collapsed by default and frequently missed. We get ~3 support tickets/week from users who can't find how to cancel.

### What happens when the user clicks "Cancel plan"
- A modal appears asking: "Are you sure you want to cancel?"
- Two checkboxes appear (both pre-checked):
    [x] I understand my data will be deleted immediately.
    [x] I agree that no refund will be issued.
- A single "Confirm" button. No "Go back" option in the modal.

### Exit survey
- We show a 12-question form asking about feature satisfaction, NPS, likelihood to recommend, pricing feedback, support quality, onboarding experience, and open text for "anything else."
- Completion is optional — users can skip to the final "Confirm" button at any time.
- We collect this data but it is not routed to any offer or save attempt.

### Save offer
- After survey (if completed), we show a 20% discount for 1 month — same for every user regardless of their survey answers.
- The discount is presented with a 24-hour countdown timer that resets every time the user visits the page.

### Post-cancel experience
- No confirmation email is sent.
- Data is deleted immediately upon cancellation (not retained for 90 days).
- No re-engagement or win-back emails exist.

### Dunning
- When a payment fails, Stripe retries immediately (same day), then again 1 day later, then cancels.
- No dunning emails are sent.
- Smart Retries are disabled.
- Card Account Updater status: unknown / not verified.

### Metrics tracked
- We count total cancellations per month.
- No save rate, no exit survey completion rate, no payment recovery rate tracked.
"""

with open(os.path.join(WORKSPACE, "internal/cs/playbooks/current_cancel_flow.md"), "w") as f:
    f.write(broken_flow)

# ── Business context file ────────────────────────────────────────────────────
context = """# TaskFlow Pro — Business Context

## Company
- Product: B2B SaaS project management tool
- Model: Self-serve, monthly billing
- Payment processor: Stripe
- Current MRR: $148,500
- Active customers: ~990
- Average plan: $150/mo

## Churn situation
- Overall monthly churn rate: 6.2% (from kpis.json)
- Voluntary vs involuntary split: not tracked
- Exit reasons: rarely captured (see churned_customers_feb.csv)
- Save rate: not measured

## Goals
- Reduce total monthly churn to <2% voluntary, <1% involuntary
- Build a proper cancel flow with save offers
- Set up payment recovery for failed payments
- Understand why customers are leaving

## Constraints
- Engineering bandwidth: limited (1 backend dev, 1 frontend dev)
- No existing dunning tool — building on Stripe
- Platform rules: Stripe Customer Portal guidelines apply
"""

with open(os.path.join(WORKSPACE, "internal/marketing/brand/business_context.md"), "w") as f:
    f.write(context)

print("Workspace generated successfully.")
print(f"Files created: {len(distractors) + 2}")