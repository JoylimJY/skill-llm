import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "data/raw",
    "data/processed",
    "reports/q2",
    "reports/q3",
    "product/roadmap",
    "product/specs",
    "analytics/funnels",
    "analytics/cohorts",
    "engineering/backend",
    "engineering/infra",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── sample_size_calculator.py (the proprietary tool) ────────────────────────
sample_size_script = '''\
#!/usr/bin/env python3
"""
Sample size calculator for A/B experiments.
Usage:
  python3 scripts/sample_size_calculator.py \\
      --baseline-rate FLOAT \\
      --mde FLOAT \\
      --mde-type {absolute|relative} \\
      [--alpha FLOAT] \\
      [--power FLOAT]
"""
import argparse
import math
from scipy import stats

def compute_sample_size(baseline_rate, mde, mde_type, alpha=0.05, power=0.80):
    if mde_type == "relative":
        effect = baseline_rate * mde
    elif mde_type == "absolute":
        effect = mde
    else:
        raise ValueError(f"Unknown mde-type: {mde_type!r}. Must be 'absolute' or 'relative'.")

    treatment_rate = baseline_rate + effect

    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta  = stats.norm.ppf(power)

    p_bar = (baseline_rate + treatment_rate) / 2
    numerator   = (z_alpha * math.sqrt(2 * p_bar * (1 - p_bar))
                   + z_beta * math.sqrt(baseline_rate * (1 - baseline_rate)
                                        + treatment_rate * (1 - treatment_rate))) ** 2
    denominator = effect ** 2

    n_per_variant = math.ceil(numerator / denominator)
    n_total       = n_per_variant * 2

    print(f"Baseline rate    : {baseline_rate:.4f}")
    print(f"MDE ({mde_type:8s})  : {mde}")
    print(f"Effective delta  : {effect:.4f}")
    print(f"Alpha            : {alpha}")
    print(f"Power            : {power}")
    print(f"--- Results ---")
    print(f"Per-variant N    : {n_per_variant}")
    print(f"Total N          : {n_total}")
    return n_per_variant, n_total

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A/B test sample size calculator")
    parser.add_argument("--baseline-rate", type=float, required=True)
    parser.add_argument("--mde",           type=float, required=True)
    parser.add_argument("--mde-type",      type=str,   required=True,
                        choices=["absolute", "relative"])
    parser.add_argument("--alpha",         type=float, default=0.05)
    parser.add_argument("--power",         type=float, default=0.80)
    args = parser.parse_args()
    compute_sample_size(
        baseline_rate=args.baseline_rate,
        mde=args.mde,
        mde_type=args.mde_type,
        alpha=args.alpha,
        power=args.power,
    )
'''
with open(os.path.join(WORKSPACE, "scripts/sample_size_calculator.py"), "w") as f:
    f.write(sample_size_script)

# ── references/experiment-playbook.md ───────────────────────────────────────
playbook = """\
# Experiment Playbook

## Hypothesis Format
All hypotheses MUST follow the If/Then/Because structure:
- If we change [intervention]
- Then [metric] will change by [expected direction/magnitude]
- Because [behavioral mechanism]

## Metric Taxonomy
- PRIMARY metric: one single decision metric per experiment
- GUARDRAIL metrics: protect quality and avoid regressions
- SECONDARY metrics: diagnosis only, not for decisions

## ICE Scoring
Rank experiments using:
  ICE Score = (Impact * Confidence * Ease) / 10
Each dimension scored 1-10.

## Stopping Rules
- Pre-register sample size OR duration before launch.
- Do not stop on random interim spikes.

## Significance vs Practical Impact
- p < alpha is necessary but not sufficient for shipping.
- Assess confidence interval vs business threshold.
"""
with open(os.path.join(WORKSPACE, "references/experiment-playbook.md"), "w") as f:
    f.write(playbook)

# ── references/statistics-reference.md ──────────────────────────────────────
stats_ref = """\
# Statistics Reference

## Two-proportion z-test
Used for binary conversion metrics.
n = (z_alpha/2 * sqrt(2*p_bar*(1-p_bar)) + z_beta * sqrt(p1*(1-p1)+p2*(1-p2)))^2 / delta^2

## Confidence Intervals
95% CI: point_estimate +/- 1.96 * SE
If CI crosses zero: directional claim is uncertain.

## Power
Power = 1 - beta. Standard minimum: 0.80.
"""
with open(os.path.join(WORKSPACE, "references/statistics-reference.md"), "w") as f:
    f.write(stats_ref)

# ── distractor files ─────────────────────────────────────────────────────────

# Existing experiment results (messy, partial – distractors)
old_results = {
    "experiment_id": "EXP-2024-011",
    "name": "Homepage CTA Color Change",
    "p_value": 0.12,
    "lift": 0.008,
    "status": "inconclusive",
    "notes": "Ran only 5 days. Sample size TBD."
}
with open(os.path.join(WORKSPACE, "reports/q2/exp_011_results.json"), "w") as f:
    json.dump(old_results, f, indent=2)

# Old, incorrect ICE scoring sheet (uses wrong formula – no /10 divisor)
old_ice = """\
Experiment,Impact,Confidence,Ease,WRONG_ICE_Score
Simplified form,7,6,8,336
Progress bar,5,7,9,315
Autofill address,6,5,6,180
"""
with open(os.path.join(WORKSPACE, "reports/q2/old_ice_scoring_WRONG.csv"), "w") as f:
    f.write(old_ice)

# Product spec with raw experiment ideas (not yet planned)
spec = """\
# Loan Application Flow – Q3 Experiment Ideas

We have identified the following three hypotheses worth testing:

## Idea A: Simplified Income Disclosure Form
Remove 4 optional income-detail fields from the income disclosure step.
Team believes this could reduce drop-off on that step.
Rough scores: Impact=8, Confidence=7, Ease=6

## Idea B: Inline Progress Indicator
Add a persistent step-count progress bar (e.g., "Step 2 of 5") to every page.
Expected to improve completion by reassuring users.
Rough scores: Impact=6, Confidence=8, Ease=9

## Idea C: Pre-filled Employment Data via Open Banking
Auto-populate employer name and income from a connected bank feed.
High engineering cost; data quality concerns.
Rough scores: Impact=9, Confidence=5, Ease=3

## Baseline Metrics (from analytics, last 90 days)
- Application start-to-submit conversion: 18% (0.18)
- Median time-to-complete: 14 minutes
- Drop-off rate at income step: 34%

## Target Improvement for Prioritised Experiment
The growth team wants a minimum detectable effect of 2 percentage points absolute
on the start-to-submit conversion rate.
Standard statistical requirements apply (alpha=0.05, power=0.80).
"""
with open(os.path.join(WORKSPACE, "product/specs/q3_experiment_ideas.md"), "w") as f:
    f.write(spec)

# Funnel data CSV (distractor)
funnel_data = """\
step,visitors,dropoff_pct
landing,12400,5.2
eligibility_check,11756,8.1
income_disclosure,10804,34.0
document_upload,7131,11.3
review_submit,6334,2.5
confirmation,6175,0.0
"""
with open(os.path.join(WORKSPACE, "analytics/funnels/q3_funnel_data.csv"), "w") as f:
    f.write(funnel_data)

# Cohort CSV (distractor)
cohort_data = """\
cohort_month,n_applicants,approval_rate,avg_loan_size
2024-01,3200,0.61,12400
2024-02,3450,0.59,12800
2024-03,3100,0.63,11900
2024-04,3600,0.58,13200
"""
with open(os.path.join(WORKSPACE, "analytics/cohorts/approval_cohorts.csv"), "w") as f:
    f.write(cohort_data)

# Engineering notes (distractor)
eng_notes = """\
## Backend notes for income step refactor

- income_fields table: 12 columns, 4 marked optional (employed_since, secondary_income, bonus_pct, stock_value)
- Removing optional fields requires migration script: db/migrations/0042_remove_optional_income.sql
- Feature flag: FEATURE_SIMPLIFIED_INCOME_FORM (default: false)
- Owner: @jsmith
"""
with open(os.path.join(WORKSPACE, "engineering/backend/income_step_notes.md"), "w") as f:
    f.write(eng_notes)

# Roadmap (distractor)
roadmap = """\
# Product Roadmap Q3 2024
- [ ] Launch Open Banking integration (Q3 end)
- [ ] Simplify income form (experiment first, then ship if winner)
- [ ] Progress indicator on application flow
- [ ] Document upload UX overhaul (Q4)
"""
with open(os.path.join(WORKSPACE, "product/roadmap/q3_roadmap.md"), "w") as f:
    f.write(roadmap)

# Old AB test config YAML (distractor, wrong format)
ab_config = """\
# DEPRECATED - do not use
experiment: homepage_cta_v2
split: 50/50
metric: ctr
target_lift: 5%
duration_days: 14
launched: 2024-02-10
killed: 2024-02-15
reason: SRM detected
"""
with open(os.path.join(WORKSPACE, "data/raw/deprecated_ab_config.yaml"), "w") as f:
    f.write(ab_config)

# Analytics README stub (distractor – not a hint)
with open(os.path.join(WORKSPACE, "analytics/OWNERS"), "w") as f:
    f.write("analytics-team@lendfast.io\n")

# Infra placeholder
with open(os.path.join(WORKSPACE, "engineering/infra/deploy_notes.txt"), "w") as f:
    f.write("Feature flags managed via LaunchDarkly. Contact infra-team for prod toggles.\n")

# Q3 empty report placeholder
with open(os.path.join(WORKSPACE, "reports/q3/.gitkeep"), "w") as f:
    f.write("")

print("Workspace generated successfully.")
print(f"Files written to: {WORKSPACE}")