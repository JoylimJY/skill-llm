import os
import json
import textwrap

workspace = "/workspace"

# ── Directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "assets",
    "references",
    "data/raw",
    "data/processed",
    "docs/internal",
    "docs/legal",
    "configs",
    "logs",
    "archive/2023",
    "archive/2024",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── The actual skill script (already exists in workspace per spec) ──────────
revenue_calc = textwrap.dedent("""\
    #!/usr/bin/env python3
    import sys
    import json

    def calculate_revenue(strategy, users, price, conv=0.8, churn=0.1, costs=0.2):
        monthly_gross = users * price * conv
        annual_gross = monthly_gross * 12
        annual_net = annual_gross * (1 - churn) * (1 - costs)
        return {
            'strategy': strategy,
            'monthly_gross': round(monthly_gross, 2),
            'annual_gross': round(annual_gross, 2),
            'annual_net': round(annual_net, 2),
            'break_even_users': round(price * conv * 12 * (1 - costs) / price, 0)
        }

    if __name__ == '__main__':
        data = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {'strategy':2, 'users':100, 'price':10}
        result = calculate_revenue(**data)
        print(json.dumps(result, indent=2))
""")
with open(os.path.join(workspace, "scripts/revenue-calc.py"), "w") as f:
    f.write(revenue_calc)

# ── Report template ─────────────────────────────────────────────────────────
report_template = textwrap.dedent("""\
    # Revenue Projection Report

    ## Strategy Overview
    <!-- FILL: strategy name, key parameters -->

    ## Base Case Results
    | Metric | Value |
    |--------|-------|
    <!-- FILL: monthly_gross, annual_gross, annual_net, break_even_users -->

    ## Sensitivity Analysis (±20% Users)
    | Scenario | Users | Monthly Gross | Annual Gross | Annual Net |
    |----------|-------|---------------|--------------|------------|
    <!-- FILL: low (-20%), base, high (+20%) rows -->

    ## Next Steps
    <!-- FILL: recommended actions -->
""")
with open(os.path.join(workspace, "assets/report-template.md"), "w") as f:
    f.write(report_template)

# ── Pricing models reference ────────────────────────────────────────────────
pricing_models = textwrap.dedent("""\
    # Pricing Models Reference

    ## Strategy 1 – API Sales
    Flat monthly access. Typical: $9–$49/mo per seat.

    ## Strategy 2 – Marketplace
    Revenue share / subscription. Typical: $9–$99/mo.
    Default conv=0.80, churn=0.10, costs=0.20.

    ## Strategy 3 – White-label
    Enterprise licensing. Typical: $500–$5000/mo per client.

    ## Strategy 4 – Affiliates
    Commission on referral. Typical: 5–20% of referred revenue.

    ## Notes
    - All rates are monthly unless stated otherwise.
    - Sensitivity standard: ±20% on user base.
""")
with open(os.path.join(workspace, "references/pricing-models.md"), "w") as f:
    f.write(pricing_models)

# ── Distractor files ────────────────────────────────────────────────────────
distractors = {
    "data/raw/user_survey_2024.csv": "user_id,score,plan\n1,4.2,basic\n2,3.8,pro\n3,4.9,basic\n",
    "data/processed/cleaned_users.json": json.dumps({"total": 250, "active": 210, "churned": 40}),
    "configs/app_config.yaml": "env: production\ndebug: false\nmax_retries: 3\n",
    "configs/feature_flags.json": json.dumps({"new_dashboard": True, "beta_pricing": False}),
    "logs/server.log": "2024-01-15 10:23:11 INFO  startup complete\n2024-01-15 10:23:12 INFO  listening on :8080\n",
    "docs/internal/onboarding.md": "# Onboarding\nWelcome to the team. Please read the handbook.\n",
    "docs/legal/terms.txt": "Terms of Service v2.1 — All rights reserved.\n",
    "archive/2023/q4_summary.txt": "Q4 2023: 80 customers, ARR $72,000\n",
    "archive/2024/roadmap_draft.md": "# 2024 Roadmap Draft\n- Launch marketplace\n- Expand API tier\n",
    "scripts/db_migrate.py": "# placeholder migration script\nprint('no-op')\n",
    "assets/logo_placeholder.txt": "LOGO ASSET — replace with actual image file\n",
    "data/raw/pricing_experiment_raw.csv": "tier,price,signups\nbasic,9,120\npro,29,45\nenterprise,99,8\n",
}
for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── The messy "brief" the agent must interpret ──────────────────────────────
# This is the raw, unstructured business brief — not a config, not hints.
brief = textwrap.dedent("""\
    INTERNAL MEMO — Q1 Planning
    Date: 2025-01-08
    From: Head of Growth
    To: Analytics Team

    We're preparing the investor pitch deck for our AI agent marketplace (OpenClaw).
    Please model out the financials for the following scenario and drop the output
    in a file called revenue_projection.md.

    Scenario parameters:
      - Monetization approach: Marketplace (subscription-based)
      - Starting user base: 250 paying subscribers
      - Monthly subscription price: $29 per user
      - Expected conversion rate: 75%
      - Monthly churn: 8%
      - Compute/infrastructure costs: 25% of revenue

    We need:
      1. The base-case monthly and annual numbers.
      2. A quick stress-test showing what happens if we get 20% fewer users
         than expected AND if we get 20% more than expected.
      3. Everything neatly formatted so we can paste it straight into the deck.

    Use the standard company template if there is one.
    — HoG
""")
with open(os.path.join(workspace, "data/raw/planning_brief.txt"), "w") as f:
    f.write(brief)

print("Workspace initialized.")