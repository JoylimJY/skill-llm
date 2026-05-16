import os
import csv
import random

random.seed(42)

# ── directory skeleton (distractors) ──────────────────────────────────────────
dirs = [
    "papers",
    "papers/raw_pdfs",
    "papers/notes",
    "analysis/scripts",
    "analysis/figures",
    "analysis/drafts",
    "admin/ethics",
    "admin/funding",
    "references/endnote",
    "logs",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── distractor files ──────────────────────────────────────────────────────────
distractors = {
    "papers/raw_pdfs/smith2018.pdf.txt": "Placeholder text for Smith 2018 PDF.",
    "papers/raw_pdfs/jones2020.pdf.txt": "Placeholder text for Jones 2020 PDF.",
    "papers/notes/meeting_notes_2024-01-15.txt": "Discussed inclusion criteria. Decided to include RCTs only.",
    "papers/notes/protocol_v2.txt": "Protocol version 2. Intervention: ACE inhibitors. Comparator: placebo.",
    "analysis/scripts/forest_plot.py": "# forest plot script\nimport matplotlib.pyplot as plt\n# TODO",
    "analysis/scripts/meta_analysis.R": "# meta-analysis R script\nlibrary(meta)\n",
    "analysis/figures/figure1_draft.txt": "Draft figure 1 description: forest plot of primary outcome.",
    "analysis/drafts/discussion_v1.txt": "Discussion draft v1. We found heterogeneity in study designs.",
    "admin/ethics/ethics_approval.txt": "Ethics approval ID: EC-2024-0042. Approved 2024-03-01.",
    "admin/funding/grant_summary.txt": "Grant: NIHR-2023-HYP. Title: Hypertension pharmacotherapy review.",
    "references/endnote/library_export.txt": "Exported 847 records. Deduplicated to 412. Screened: 82. Included: 8.",
    "logs/screening_log.txt": "Screener A and B agreed on 78/82 records. Cohen's kappa = 0.91.",
}
for path, content in distractors.items():
    with open(path, "w") as f:
        f.write(content)

# ── messy extraction_table.csv ────────────────────────────────────────────────
# Intentional messiness:
#  - Some RoB columns present but with wrong / inconsistent names:
#    "Risk_Selection", "rob_Measurement", "RoB_overall" (will need normalization)
#  - One paper has a partially-filled row with "Unclear" (wrong case)
#  - rob_notes column missing entirely
#  - rob_confounding and rob_reporting columns missing entirely

fieldnames = [
    "study_id",
    "first_author",
    "year",
    "country",
    "study_design",
    "sample_size",
    "intervention",
    "comparator",
    "primary_outcome",
    "followup_months",
    "blinding",
    "allocation_concealment",
    "attrition_rate_pct",
    "selective_reporting_flag",
    # ← partial/badly-named RoB columns (need normalization)
    "Risk_Selection",
    "rob_Measurement",
    "RoB_overall",
]

rows = [
    {
        "study_id": "S01",
        "first_author": "Alvarez",
        "year": 2015,
        "country": "Spain",
        "study_design": "RCT",
        "sample_size": 320,
        "intervention": "Lisinopril 10mg",
        "comparator": "Placebo",
        "primary_outcome": "SBP reduction at 6 months",
        "followup_months": 6,
        "blinding": "double-blind",
        "allocation_concealment": "adequate",
        "attrition_rate_pct": 4,
        "selective_reporting_flag": "no",
        # well-reported RCT → low selection, low measurement
        "Risk_Selection": "low",
        "rob_Measurement": "low",
        "RoB_overall": "",  # needs recomputation
    },
    {
        "study_id": "S02",
        "first_author": "Chen",
        "year": 2017,
        "country": "China",
        "study_design": "RCT",
        "sample_size": 180,
        "intervention": "Amlodipine 5mg",
        "comparator": "Placebo",
        "primary_outcome": "DBP reduction at 12 months",
        "followup_months": 12,
        "blinding": "open-label",          # no blinding → high measurement
        "allocation_concealment": "unclear",
        "attrition_rate_pct": 18,           # high attrition → high
        "selective_reporting_flag": "no",
        "Risk_Selection": "unclear",
        "rob_Measurement": "Unclear",       # wrong case
        "RoB_overall": "",
    },
    {
        "study_id": "S03",
        "first_author": "Müller",
        "year": 2019,
        "country": "Germany",
        "study_design": "cohort",           # observational → confounding risk
        "sample_size": 540,
        "intervention": "Ramipril 5mg",
        "comparator": "No treatment",
        "primary_outcome": "CV events at 24 months",
        "followup_months": 24,
        "blinding": "none",
        "allocation_concealment": "not applicable",
        "attrition_rate_pct": 9,
        "selective_reporting_flag": "yes",  # selective reporting flag
        "Risk_Selection": "unclear",
        "rob_Measurement": "high",
        "RoB_overall": "",
    },
    {
        "study_id": "S04",
        "first_author": "Okafor",
        "year": 2020,
        "country": "Nigeria",
        "study_design": "RCT",
        "sample_size": 95,                  # small sample
        "intervention": "Hydrochlorothiazide 25mg",
        "comparator": "Placebo",
        "primary_outcome": "SBP reduction at 3 months",
        "followup_months": 3,
        "blinding": "single-blind",
        "allocation_concealment": "unclear",
        "attrition_rate_pct": 12,
        "selective_reporting_flag": "unclear",
        "Risk_Selection": "",               # missing
        "rob_Measurement": "",              # missing
        "RoB_overall": "",
    },
    {
        "study_id": "S05",
        "first_author": "Patel",
        "year": 2021,
        "country": "India",
        "study_design": "RCT",
        "sample_size": 410,
        "intervention": "Valsartan 80mg",
        "comparator": "Atenolol 50mg",
        "primary_outcome": "SBP/DBP reduction at 6 months",
        "followup_months": 6,
        "blinding": "double-blind",
        "allocation_concealment": "adequate",
        "attrition_rate_pct": 3,
        "selective_reporting_flag": "no",
        "Risk_Selection": "low",
        "rob_Measurement": "low",
        "RoB_overall": "Low",              # wrong case
    },
    {
        "study_id": "S06",
        "first_author": "Fernandez",
        "year": 2022,
        "country": "Mexico",
        "study_design": "cross-sectional",  # design not suitable for causal inference
        "sample_size": 200,
        "intervention": "Enalapril 10mg",
        "comparator": "Usual care",
        "primary_outcome": "BP control rate",
        "followup_months": 0,
        "blinding": "none",
        "allocation_concealment": "not applicable",
        "attrition_rate_pct": 0,
        "selective_reporting_flag": "unclear",
        "Risk_Selection": "high",
        "rob_Measurement": "unclear",
        "RoB_overall": "",
    },
    {
        "study_id": "S07",
        "first_author": "Kim",
        "year": 2023,
        "country": "South Korea",
        "study_design": "RCT",
        "sample_size": 600,
        "intervention": "Telmisartan 40mg",
        "comparator": "Placebo",
        "primary_outcome": "SBP reduction at 12 months",
        "followup_months": 12,
        "blinding": "double-blind",
        "allocation_concealment": "adequate",
        "attrition_rate_pct": 5,
        "selective_reporting_flag": "no",
        "Risk_Selection": "low",
        "rob_Measurement": "low",
        "RoB_overall": "",
    },
    {
        "study_id": "S08",
        "first_author": "Nguyen",
        "year": 2023,
        "country": "Vietnam",
        "study_design": "RCT",
        "sample_size": 150,
        "intervention": "Perindopril 4mg",
        "comparator": "Placebo",
        "primary_outcome": "DBP reduction at 6 months",
        "followup_months": 6,
        "blinding": "unclear",             # blinding method not described
        "allocation_concealment": "unclear",
        "attrition_rate_pct": 7,
        "selective_reporting_flag": "unclear",
        "Risk_Selection": "",
        "rob_Measurement": "",
        "RoB_overall": "",
    },
]

with open("papers/extraction_table.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("Workspace generated successfully.")
print(f"  papers/extraction_table.csv  ({len(rows)} study rows, intentionally messy RoB columns)")