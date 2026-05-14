import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a realistic deeply nested directory structure with distractor files
dirs = [
    "workspace/papers/raw",
    "workspace/papers/processed",
    "workspace/papers/archive/2022",
    "workspace/papers/archive/2023",
    "workspace/notes/drafts",
    "workspace/notes/final",
    "workspace/data/courts",
    "workspace/data/sentencing",
    "workspace/references/bibtex",
    "workspace/references/endnote",
    "workspace/scripts/analysis",
    "workspace/scripts/cleaning",
    "workspace/output/reports",
    "workspace/output/slides",
]

for d in dirs:
    os.makedirs(f"/{d}", exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "/workspace/papers/archive/2022/chen_2022_judicial.txt": "Chen, L. (2022). Judicial Discretion and Case Outcomes. Journal of Legal Studies, 51(2), 345-380.",
    "/workspace/papers/archive/2023/wang_2023_ml_law.txt": "Wang, Y. (2023). Machine Learning Applications in Legal Prediction. Review of Law & Economics.",
    "/workspace/notes/drafts/reading_notes_old.txt": "Old reading notes - NOT the current assignment. Ignore this file.",
    "/workspace/notes/drafts/todo.txt": "TODO:\n1. Finish lit review\n2. Run regressions\n3. Submit to journal",
    "/workspace/data/courts/court_codes.csv": "court_id,court_name,jurisdiction\n001,Northern District,Federal\n002,Southern District,Federal",
    "/workspace/data/sentencing/codebook.txt": "Variable definitions for sentencing dataset. OFFEND_TYPE: 1=violent, 2=property, 3=drug.",
    "/workspace/references/bibtex/main.bib": "@article{angrist1996,\n  author={Angrist, J. and Krueger, A.},\n  title={Instrumental Variables},\n  year={1996}\n}",
    "/workspace/references/endnote/library.enl": "Placeholder EndNote library file.",
    "/workspace/scripts/analysis/run_iv.do": "* Stata script for IV regressions\nivreg2 y x (z = instrument), robust",
    "/workspace/scripts/cleaning/clean_data.py": "import pandas as pd\ndf = pd.read_csv('raw.csv')\ndf.dropna(inplace=True)\ndf.to_csv('clean.csv')",
    "/workspace/output/reports/preliminary_summary.txt": "Preliminary findings - not finalized. Effect size approximately 0.3.",
    "/workspace/output/slides/presentation_notes.txt": "Talk at ALEA conference. Focus on identification strategy.",
    "/workspace/papers/processed/abstract_only.txt": "Abstract: This paper studies recidivism prediction tools in criminal sentencing. We find...",
    "/workspace/papers/archive/2023/template_analysis.md": "# Template\nThis is an old template, NOT the correct format. Do not use this structure.",
}

for path, content in distractor_files.items():
    with open(path, "w") as f:
        f.write(content)

# --- The main paper content (simulating a real empirical paper) ---
# A realistic paper on algorithmic risk assessment tools in bail decisions
paper_content = """
WORKING PAPER

Title: Racial Bias, Algorithmic Risk Assessment, and Bail Decisions: 
       Evidence from a Natural Experiment in Criminal Courts

Authors: Michael T. Harrison, Priya Sundaram, and James L. Whitfield

Journal: American Economic Review (Forthcoming, 2024)
DOI: 10.1257/aer.20231042

========================================================================

ABSTRACT

We study the causal effect of algorithmic risk assessment tools (RATs) on 
bail decisions and their disparate racial impact. Exploiting a staggered 
county-level rollout of a commercial RAT across 42 counties in a large 
US state between 2015 and 2020, we identify the effect of algorithmic 
adoption using a difference-in-differences (DID) design. Our dataset 
comprises 1.4 million criminal cases from court administrative records, 
linked to defendant-level demographic and criminal history information. 
We find that RAT adoption reduces pretrial detention rates by 12.3 
percentage points on average, but this effect masks substantial 
heterogeneity: the reduction is concentrated among White defendants 
(18.7 pp), while Black defendants experience only a 4.1 pp reduction, 
widening the racial gap in detention rates by approximately 14.6 
percentage points. We develop a novel decomposition method to 
distinguish between bias in the algorithm itself versus differential 
judicial compliance with algorithmic recommendations by race. Our 
estimates suggest that approximately 62% of the racial disparity in 
treatment effect is attributable to differential judicial override 
behavior rather than the algorithm's own predictions.

========================================================================

1. INTRODUCTION

The use of algorithmic risk assessment tools in criminal justice has 
expanded dramatically over the past decade, with proponents arguing 
that data-driven prediction can reduce human biases and improve the 
consistency of judicial decision-making. As of 2022, over 60% of US 
jurisdictions had adopted some form of RAT for bail or sentencing 
decisions. Despite their widespread adoption, empirical evidence on the 
causal effects of these tools remains scarce, and the question of 
whether they reduce or amplify racial disparities in the criminal 
justice system is deeply contested.

This paper addresses three interconnected questions: (1) Do RATs causally 
reduce pretrial detention rates? (2) Do the effects differ by defendant 
race? (3) What mechanisms drive any observed racial disparity in 
treatment effects?

The policy stakes are high. Pretrial detention has severe consequences 
for defendants: incarcerated individuals are more likely to lose 
employment, housing, and custody of children, and are more likely to 
accept plea bargains, even when innocent (Stevenson 2018; Leslie and 
Pope 2017). At the same time, pretrial release of high-risk defendants 
imposes costs on public safety. Understanding whether and how RATs affect 
these tradeoffs across demographic groups is essential for designing 
equitable algorithmic governance frameworks.

The economic intuition behind our research design is straightforward: 
if judges face uncertainty about defendant risk, and if algorithmic 
predictions provide a noisy but informative signal, rational Bayesian 
judges should update toward algorithmic recommendations weighted by 
their precision relative to private information. If judges' private 
information or their updating behavior varies by defendant race, we 
would expect heterogeneous compliance and thus heterogeneous treatment 
effects, even absent any algorithmic bias.

========================================================================

2. DATA AND INSTITUTIONAL BACKGROUND

2.1 Institutional Setting

Our study covers the state of Midland, which mandates that all felony 
bail hearings be conducted within 48 hours of arrest. The commercial RAT 
used in our sample (the Pretrial Assessment System, or PAS) generates a 
risk score from 1 to 10 based on criminal history, charge severity, 
age, and residential stability, and provides a categorical recommendation 
of "detain", "release", or "release with conditions". Crucially, the 
algorithm does NOT use race as an input variable. However, because race 
correlates with criminal history and residential stability—variables 
the algorithm does use—the algorithm's predictions may nonetheless 
exhibit racial disparities in outcomes.

2.2 Data Sources

Our primary dataset is constructed by linking three administrative sources:
(i) Court administrative records: All felony filings in Midland state 
courts, 2013-2022, containing charge information, bail decisions, 
pretrial detention status, and case dispositions.
(ii) Defendant demographic records: Race, age, gender, and zip code of 
residence for all defendants, obtained via a data-sharing agreement with 
the State Department of Corrections.
(iii) RAT adoption records: County-level rollout dates of the PAS system, 
obtained via public records requests.

Our final linked sample contains 1,423,891 felony cases across 42 counties, 
covering 2013–2022. We restrict to cases with non-missing demographic 
information and to defendant's first appearance hearings, yielding an 
analysis sample of 987,344 cases. Of these, 58.3% involve White defendants 
and 31.4% involve Black defendants.

2.3 Descriptive Statistics

Prior to RAT adoption, Black defendants faced a pretrial detention rate 
of 41.2% compared to 29.8% for White defendants—an unconditional gap 
of 11.4 percentage points. Judges in adopting counties received PAS 
training 6 months before the official rollout date.

========================================================================

3. EMPIRICAL CHALLENGES

3.1 Selective Adoption and Endogeneity of Rollout Timing

The most immediate empirical challenge is that RAT adoption is not 
random. Counties may adopt earlier if they face greater caseloads, 
more racial tension, or more progressive judicial leadership. If 
counties that adopted earlier were already on a different trend in 
detention rates—for example, counties where judges were already 
becoming more lenient—then naive comparisons of adopting versus 
non-adopting counties would confound the effect of the algorithm 
with pre-existing trends.

This is a classic selection-on-trends problem in the DID literature. 
The key identifying assumption for our DID is the parallel trends 
assumption: in the absence of RAT adoption, detention rates in 
adopting and non-adopting counties would have followed parallel trends. 
Violations of this assumption would bias our estimate of the average 
treatment effect on the treated (ATT).

3.2 The Selective Labels Problem

A more subtle challenge is the selective labels problem, well known in 
the fairness-in-ML literature (Lakkaraju et al. 2017; Kleinberg et al. 
2018). The outcome we can observe—recidivism or pretrial misconduct—is 
only defined for defendants who were released pretrial. We cannot observe 
whether detained defendants would have committed offenses if released. 
This creates a fundamental missing data problem: the "ground truth" 
labels used to train and evaluate the algorithm are a non-random 
function of past judicial decisions.

For our purposes, this problem affects both the validity of the 
algorithm's predictions and our ability to measure algorithmic bias 
using observed outcomes. If detained defendants are, on average, 
higher-risk than released defendants, and if detention propensity 
varies by race, then the algorithm's error rates (false positive and 
false negative rates) will not be comparable across racial groups 
even if measured on observed data.

3.3 Judges' Private Information and Compliance Heterogeneity

Even if the algorithm provides a valid prediction, we face a third 
challenge: judges may selectively comply with algorithmic recommendations, 
and compliance may be correlated with both defendant characteristics and 
outcomes. If judges override the algorithm more for Black defendants 
because they have private information that the algorithm does not capture, 
this compliance heterogeneity would not constitute bias in the traditional 
sense. But if overrides reflect judicial prejudice, the interpretation 
is different. Distinguishing these mechanisms requires additional 
identification assumptions or data.

========================================================================

4. IDENTIFICATION STRATEGY

4.1 Staggered Difference-in-Differences

Our primary identification strategy exploits the staggered rollout of 
the PAS system across 42 counties. The main estimating equation is:

  Y_{ict} = alpha + beta * (Post_{ct} x Treat_c) + X_{ict}' * gamma 
            + delta_c + lambda_t + epsilon_{ict}

where Y_{ict} is the pretrial detention indicator for defendant i in 
county c at time t; Post_{ct} is an indicator equal to 1 after county c 
adopts the PAS; Treat_c is an indicator for ever-adopting counties; 
X_{ict} is a vector of defendant and case covariates; delta_c are 
county fixed effects; and lambda_t are year-month fixed effects.

Given the staggered adoption, we use the heterogeneity-robust DID 
estimator of Callaway and Sant'Anna (2021) as our primary specification, 
which avoids the negative weighting problem identified by Goodman-Bacon 
(2021) in two-way fixed effects regressions with heterogeneous treatment 
effects across adoption cohorts.

4.2 Parallel Trends Validation

We validate the parallel trends assumption using an event-study 
specification:

  Y_{ict} = alpha + sum_{k=-24}^{24} beta_k * 1[t - T_c^* = k] 
            + delta_c + lambda_t + epsilon_{ict}

where T_c^* is the adoption date for county c. We find no evidence of 
pre-trends in detention rates for the four years prior to adoption, 
supporting the parallel trends assumption.

4.3 Decomposition of Racial Disparities

To decompose the racial disparity in treatment effects, we extend the 
Kitagawa-Oaxaca-Blinder decomposition to our DID setting. Let 
ATT_W and ATT_B denote the average treatment effect for White and 
Black defendants, respectively. We decompose:

  ATT_W - ATT_B = [E(algorithmic_rec_W) - E(algorithmic_rec_B)] * gamma_comply
                 + E(algorithmic_rec_B) * [gamma_comply_W - gamma_comply_B]
                 + residual

The first term captures the contribution of differential algorithmic 
recommendations; the second term captures differential judicial compliance 
by race, conditional on the same algorithmic recommendation; and the 
residual captures interactions.

4.4 Robustness Checks

We perform four sets of robustness checks:
(i) County-level clustering of standard errors versus two-way clustering.
(ii) Restricting to a 12-month bandwidth around adoption dates.
(iii) Excluding the largest 5 counties (to address concerns about influential 
observations).
(iv) Placebo tests using artificially shifted adoption dates.

All robustness checks yield estimates qualitatively consistent with 
our main findings.

========================================================================

5. MAIN FINDINGS

5.1 Average Treatment Effect

RAT adoption reduces pretrial detention rates by 12.3 percentage points 
(SE = 1.4 pp; 95% CI: [9.6, 15.1]), representing a 34% reduction 
relative to the pre-adoption mean of 35.7%.

5.2 Heterogeneous Effects by Race

The treatment effect for White defendants is 18.7 pp (SE = 1.9 pp), 
while for Black defendants it is only 4.1 pp (SE = 0.8 pp). The 
difference of 14.6 pp is statistically significant at the 1% level 
(p < 0.001). This implies that RAT adoption substantially widened the 
racial gap in pretrial detention, which was 11.4 pp before adoption 
and grew to approximately 26.0 pp post-adoption in treated counties.

5.3 Mechanism Decomposition

Our decomposition analysis attributes the 14.6 pp racial disparity in 
treatment effects as follows:
- Differential algorithmic recommendations: 38% (5.5 pp)
- Differential judicial compliance: 62% (9.1 pp)

This finding has important policy implications: even a perfectly unbiased 
algorithm would not eliminate the racial disparity in treatment effects 
if judges systematically override algorithmic recommendations differently 
for White versus Black defendants.

5.4 Robustness

Robustness checks confirm that our main estimates are stable across 
alternative clustering approaches, sample restrictions, and bandwidth 
choices. Placebo tests using artificially shifted adoption dates 
produce near-zero estimates with large standard errors, supporting 
the causal interpretation of our main results.

========================================================================

6. RELATED LITERATURE

Our paper contributes to three strands of literature:
(1) The empirical literature on algorithmic decision-making in criminal 
justice (Angwin et al. 2016; Dressel and Farid 2018; Stevenson 2018; 
Jung et al. 2020).
(2) The econometrics literature on staggered DID designs (Callaway and 
Sant'Anna 2021; Goodman-Bacon 2021; Sun and Abraham 2021).
(3) The fairness-in-ML literature, particularly on the selective labels 
problem (Lakkaraju et al. 2017; Kleinberg et al. 2018; Coston et al. 2020).

========================================================================

7. CONCLUSION

This paper provides the first quasi-experimental evidence on the causal 
effects of algorithmic risk assessment tool adoption on pretrial detention 
and racial disparities therein. Our staggered DID design, validated by 
event-study pre-trend tests, yields credible estimates that RAT adoption 
reduces overall detention rates but significantly widens the racial gap. 
Our decomposition analysis provides novel evidence that differential 
judicial compliance behavior—rather than algorithmic bias alone—is the 
dominant driver of the racial disparity in treatment effects, accounting 
for approximately 62% of the gap.

These findings have direct implications for the design of algorithmic 
governance frameworks: mandatory compliance requirements, judicial 
training on algorithmic outputs, and monitoring of override patterns 
by defendant demographics may be necessary complements to the deployment 
of technically sound algorithms in high-stakes settings.

========================================================================

REFERENCES

Angwin, J., Larson, J., Mattu, S., and Kirchner, L. (2016). Machine bias. 
ProPublica.

Callaway, B. and Sant'Anna, P.H.C. (2021). Difference-in-differences with 
multiple time periods. Journal of Econometrics, 225(2), 200-230.

Coston, A., Mishler, A., Kennedy, E.H., and Chouldechova, A. (2020). 
Counterfactual risk assessments, evaluation, and fairness. ACM FAccT.

Dressel, J. and Farid, H. (2018). The accuracy, fairness, and limits of 
predicting recidivism. Science Advances, 4(1).

Goodman-Bacon, A. (2021). Difference-in-differences with variation in 
treatment timing. Journal of Econometrics, 225(2), 254-277.

Jung, J., Concannon, C., Shroff, R., Goel, S., and Goldstein, D.G. (2020). 
Simple rules for complex decisions. Working Paper.

Kleinberg, J., Ludwig, J., Mullainathan, S., and Rambachan, A. (2018). 
Algorithmic fairness. AEA Papers and Proceedings, 108, 22-27.

Lakkaraju, H., Kleinberg, J., Leskovec, J., Ludwig, J., and Mullainathan, S. 
(2017). The selective labels problem. ACM KDD.

Leslie, E. and Pope, N.G. (2017). The unintended impact of pretrial 
detention on case outcomes. Journal of Law and Economics, 60(3), 4-49.

Stevenson, M. (2018). Assessing risk assessment in action. Minnesota 
Law Review, 103, 303-384.

Sun, L. and Abraham, S. (2021). Estimating dynamic treatment effects in 
event studies with heterogeneous treatment effect. Journal of Econometrics, 
225(2), 175-199.

========================================================================
END OF PAPER
"""

# Write the paper to the correct location
paper_path = "/workspace/papers/raw/harrison_sundaram_whitfield_2024.txt"
with open(paper_path, "w") as f:
    f.write(paper_content)

# Write a publication info file (separate from the paper itself)
pub_info_path = "/workspace/papers/raw/publication_info.txt"
with open(pub_info_path, "w") as f:
    f.write("""Publication Information:
Title: Racial Bias, Algorithmic Risk Assessment, and Bail Decisions: Evidence from a Natural Experiment in Criminal Courts
Authors: Michael T. Harrison, Priya Sundaram, James L. Whitfield
Journal: American Economic Review (Forthcoming)
Year: 2024
DOI: 10.1257/aer.20231042
""")

# A misleading template that uses English headers (a trap)
bad_template_path = "/workspace/notes/drafts/wrong_template.md"
with open(bad_template_path, "w") as f:
    f.write("""# Paper Analysis Template (DEPRECATED)

## Problem Statement
[Write here]

## Methodology
[Write here]

## Findings
[Write here]

## Conclusion
[Write here]

NOTE: This template is outdated. Do not use this format.
""")

# Another distractor: a correctly-titled but empty/wrong file
wrong_output = "/workspace/output/reports/analysis_draft.md"
with open(wrong_output, "w") as f:
    f.write("# Draft - Empty\n\nThis file is a placeholder. Not a completed analysis.\n")

print("Workspace setup complete.")
print(f"Paper placed at: {paper_path}")
print(f"Publication info at: {pub_info_path}")