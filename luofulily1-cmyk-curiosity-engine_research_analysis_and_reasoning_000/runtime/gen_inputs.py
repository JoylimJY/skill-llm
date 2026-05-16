import os
import random
import csv
import json

random.seed(42)

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "biotech_intel/raw_data",
    "biotech_intel/raw_data/archive/2019",
    "biotech_intel/raw_data/archive/2020",
    "biotech_intel/raw_data/archive/2021",
    "biotech_intel/raw_data/archive/2022",
    "biotech_intel/processed",
    "biotech_intel/scripts",
    "biotech_intel/reports/drafts",
    "biotech_intel/reports/final",
    "biotech_intel/notes",
    "biotech_intel/vendor_data",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── PRIMARY TASK FILE: messy antibiotic resistance dataset ──────────────────
main_csv_path = "biotech_intel/raw_data/resistance_surveillance_2018_2023.csv"
rows = [
    ["year", "pathogen", "antibiotic_class", "resistance_rate_pct", "sample_size", "region", "notes"],
    [2018, "E. coli",             "Fluoroquinolones", 18.2, 4200, "EU",  ""],
    [2018, "E. coli",             "Carbapenems",      2.1,  4200, "EU",  ""],
    [2018, "Klebsiella pneumoniae","Carbapenems",      8.4,  3100, "EU",  ""],
    [2018, "MRSA",                "Methicillin",      31.5, 5800, "EU",  ""],
    [2019, "E. coli",             "Fluoroquinolones", 17.9, 4350, "EU",  ""],
    [2019, "E. coli",             "Carbapenems",      2.3,  4350, "EU",  ""],
    [2019, "Klebsiella pneumoniae","Carbapenems",      8.9,  3200, "EU",  ""],
    [2019, "MRSA",                "Methicillin",      30.1, 5900, "EU",  ""],
    # 2020 E. coli MISSING — gap in data
    [2020, "Klebsiella pneumoniae","Carbapenems",      9.2,  2800, "EU",  "COVID-19 sampling disruptions noted"],
    [2020, "MRSA",                "Methicillin",      28.7, 4900, "EU",  "Reduced hospital admissions 2020"],
    [2021, "E. coli",             "Fluoroquinolones", 19.1, 4100, "EU",  ""],
    [2021, "E. coli",             "Carbapenems",      2.8,  4100, "EU",  ""],
    # ANOMALY: Klebsiella carbapenem resistance jumps from ~9% to 34% in 2021
    [2021, "Klebsiella pneumoniae","Carbapenems",      34.7, 3300, "EU",  "VERIFY — possible pipeline contamination flagged by Vendor B"],
    [2021, "MRSA",                "Methicillin",      27.3, 5200, "EU",  ""],
    [2022, "E. coli",             "Fluoroquinolones", 20.4, 4600, "EU",  ""],
    [2022, "E. coli",             "Carbapenems",      3.1,  4600, "EU",  ""],
    [2022, "Klebsiella pneumoniae","Carbapenems",      11.3, 3400, "EU",  "Post-audit corrected figure"],
    # CONTRADICTION: Two MRSA 2022 rows with different rates
    [2022, "MRSA",                "Methicillin",      26.8, 5500, "EU",  "Preliminary report"],
    [2022, "MRSA",                "Methicillin",      31.2, 5500, "EU",  "Revised report — includes private clinic data"],
    [2023, "E. coli",             "Fluoroquinolones", 21.0, 4700, "EU",  ""],
    [2023, "E. coli",             "Carbapenems",      3.4,  4700, "EU",  ""],
    [2023, "Klebsiella pneumoniae","Carbapenems",      12.1, 3500, "EU",  ""],
    [2023, "MRSA",                "Methicillin",      29.5, 5600, "EU",  ""],
]

with open(main_csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(rows)

# ── DISTRACTOR: old analysis script (Python) ───────────────────────────────
with open("biotech_intel/scripts/old_analysis_v1.py", "w") as f:
    f.write("""# Legacy resistance trend analysis — deprecated 2022
import csv
def load_data(path):
    with open(path) as f:
        return list(csv.DictReader(f))

def mean_resistance(data, pathogen):
    vals = [float(r['resistance_rate_pct']) for r in data if r['pathogen'] == pathogen]
    return sum(vals)/len(vals) if vals else 0

if __name__ == '__main__':
    data = load_data('../raw_data/resistance_surveillance_2018_2023.csv')
    for p in ['E. coli', 'Klebsiella pneumoniae', 'MRSA']:
        print(f'{p}: {mean_resistance(data, p):.1f}%')
""")

# ── DISTRACTOR: archived 2019 regional report ─────────────────────────────
with open("biotech_intel/raw_data/archive/2019/eu_amr_summary_2019.csv", "w") as f:
    f.write("region,pathogen,resistance_pct\n")
    f.write("EU,E. coli,17.9\n")
    f.write("EU,MRSA,30.1\n")
    f.write("US,E. coli,22.4\n")
    f.write("US,MRSA,33.8\n")

# ── DISTRACTOR: vendor metadata JSON ──────────────────────────────────────
vendor_meta = {
    "vendor_a": {"name": "BioRef Labs", "accredited": True, "last_audit": "2022-03-15"},
    "vendor_b": {"name": "EuroPath Diagnostics", "accredited": True, "last_audit": "2021-08-02",
                 "notes": "2021 Q3 batch contamination incident reported; data under review"},
    "vendor_c": {"name": "ClinSurv GmbH", "accredited": False, "last_audit": "2020-11-30"},
}
with open("biotech_intel/vendor_data/vendor_metadata.json", "w") as f:
    json.dump(vendor_meta, f, indent=2)

# ── DISTRACTOR: previous analyst notes ────────────────────────────────────
with open("biotech_intel/notes/analyst_notes_q3_2022.txt", "w") as f:
    f.write("""Q3 2022 Notes — AMR Surveillance Review
========================================
- MRSA data still inconsistent between preliminary and revised reports for 2022.
  Need to reconcile before presenting to leadership.
- Klebsiella 2021 spike still unexplained. Vendor B contamination theory not confirmed.
- COVID-19 impact on 2020 sampling: E. coli data incomplete for that year.
- EU carbapenem resistance in Klebsiella trending up long-term (pre-2021 spike).
- Action item: request Vendor B raw batch data for 2021 Q2-Q3.
""")

# ── DISTRACTOR: stale config YAML ─────────────────────────────────────────
with open("biotech_intel/scripts/pipeline_config.yaml", "w") as f:
    f.write("""pipeline:
  version: 1.3
  data_source: raw_data/resistance_surveillance_2018_2023.csv
  output_dir: processed/
  pathogens:
    - E. coli
    - Klebsiella pneumoniae
    - MRSA
  alert_threshold_pct: 15.0
  flagged_vendors:
    - vendor_b
""")

# ── DISTRACTOR: processed summary (outdated, doesn't mention anomaly) ─────
with open("biotech_intel/processed/summary_2018_2020.txt", "w") as f:
    f.write("""Processed Summary: 2018-2020
============================
E. coli Fluoroquinolone resistance: stable ~18%
Klebsiella Carbapenem resistance: mild increase 8.4% -> 9.2%
MRSA Methicillin resistance: slight decline 31.5% -> 28.7%
Note: 2020 data incomplete due to COVID-19 sampling reductions.
""")

# ── DISTRACTOR: draft report stub ─────────────────────────────────────────
with open("biotech_intel/reports/drafts/draft_report_2023.md", "w") as f:
    f.write("""# AMR Surveillance Draft Report 2023
**Status: DRAFT — DO NOT DISTRIBUTE**

## Executive Summary
TBD

## Key Findings
- [placeholder]

## Recommendations
- [placeholder]
""")

# ── DISTRACTOR: requirements file ─────────────────────────────────────────
with open("biotech_intel/scripts/requirements.txt", "w") as f:
    f.write("pandas>=1.3\nnumpy>=1.21\nscipy>=1.7\ntabulate>=0.8\n")

# ── DISTRACTOR: 2020 archive placeholder ──────────────────────────────────
with open("biotech_intel/raw_data/archive/2020/eu_amr_summary_2020.csv", "w") as f:
    f.write("region,pathogen,resistance_pct\n")
    f.write("EU,Klebsiella pneumoniae,9.2\n")
    f.write("EU,MRSA,28.7\n")
    f.write("# NOTE: E. coli data not available for 2020\n")

# ── DISTRACTOR: 2022 archive ──────────────────────────────────────────────
with open("biotech_intel/raw_data/archive/2022/eu_amr_summary_2022.csv", "w") as f:
    f.write("region,pathogen,resistance_pct,source\n")
    f.write("EU,E. coli,20.4,Vendor A\n")
    f.write("EU,Klebsiella pneumoniae,11.3,Vendor B (post-audit)\n")
    f.write("EU,MRSA,31.2,Vendor A+C combined\n")

print("Workspace generated successfully.")
print("Primary task file: biotech_intel/raw_data/resistance_surveillance_2018_2023.csv")