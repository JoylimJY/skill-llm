import os
import random
import json
import yaml

random.seed(42)

workspace = "/workspace"

# ── distractor structure (≥10 files) ──────────────────────────────────────────
dirs = [
    "archive/old_reports/2022",
    "archive/old_reports/2023",
    "data/raw/market_data",
    "data/raw/specs",
    "data/processed",
    "internal/meeting_notes",
    "internal/finance",
    "templates_legacy",
    "scratch",
    "vendor_docs/lfp",
    "vendor_docs/nmc",
    "vendor_docs/sodium",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

distractors = {
    "archive/old_reports/2022/battery_overview_v1.txt": (
        "DRAFT - Battery overview 2022. Do not use. Numbers unverified."
    ),
    "archive/old_reports/2023/lfp_market_summary.txt": (
        "LFP market share: ~40% in 2022 (source unclear). NMC still dominant in EV. "
        "NOTE: figures may be outdated."
    ),
    "data/raw/market_data/blended_prices_2021.csv": (
        "year,chemistry,usd_per_kwh\n2021,LFP,112\n2021,NMC,130\n2021,NaIon,N/A\n"
    ),
    "data/raw/specs/nmc_spec_sheet_draft.txt": (
        "NMC energy density: 150-220 Wh/kg. Cycle life: 1000-2000. "
        "DRAFT - pending vendor confirmation."
    ),
    "data/raw/specs/lfp_spec_sheet_draft.txt": (
        "LFP energy density: 90-160 Wh/kg. Cycle life: 2000-6000. Thermal stability: High."
    ),
    "data/raw/specs/sodium_ion_notes.txt": (
        "Na-ion: CATL announced commercial production 2023. Wh/kg ~100-160. "
        "Cost target <$60/kWh long-term. Very early stage."
    ),
    "data/processed/rough_comparison_attempt.txt": (
        "INCOMPLETE COMPARISON - do not cite.\n"
        "LFP vs NMC vs Na-Ion - someone needs to normalize these numbers.\n"
        "Missing: cycle life under same test conditions, temperature range, calendar life."
    ),
    "internal/meeting_notes/kickoff_2024-01-15.txt": (
        "Meeting notes: Investment committee wants a rigorous, auditable report on grid-scale "
        "battery chemistries. Must be able to trace every claim back to a source. "
        "Deadline: end of quarter. Audience: non-technical investment partners."
    ),
    "internal/finance/capex_model_placeholder.xlsx.txt": (
        "PLACEHOLDER - real CAPEX model TBD. Do not reference in research output."
    ),
    "internal/meeting_notes/followup_2024-01-22.txt": (
        "Follow-up: PM confirmed scope = LFP, NMC, sodium-ion. "
        "Primary use case = grid-scale storage (not EV). Cutoff = 2024-06-30."
    ),
    "templates_legacy/old_report_template.txt": (
        "LEGACY TEMPLATE v0.1 - not used anymore. See current process documentation."
    ),
    "scratch/random_urls.txt": (
        "https://example-battery-news.com/article1\n"
        "https://example-research.org/sodium-ion-2023\n"
        "(unverified, unsaved, do not cite)"
    ),
    "vendor_docs/lfp/catl_lfp_product_page_notes.txt": (
        "CATL LFP: CTP3.0, energy density 160Wh/kg cell level, cycle life >10000, "
        "operating temp -20 to 60C. Pricing not public."
    ),
    "vendor_docs/nmc/panasonic_nmc_notes.txt": (
        "Panasonic NMC: ~250Wh/kg cell, used in Tesla Model S. "
        "Grid application less common due to thermal management cost."
    ),
    "vendor_docs/sodium/hina_sodium_notes.txt": (
        "HiNa Battery sodium-ion: ~145Wh/kg, announced grid pilot 2023 in China. "
        "Commercial scale uncertain."
    ),
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── messy raw brief (the agent's actual input) ────────────────────────────────
brief = {
    "project_title": "Grid-Scale Battery Chemistry Competitive Intelligence",
    "commissioned_by": "Clean Horizons Capital – Investment Committee",
    "analyst_note": (
        "We need a properly organized, source-traceable research deliverable comparing "
        "LFP, NMC, and sodium-ion batteries for grid-scale stationary storage. "
        "Every claim must be traceable. Numbers from 2021 in the archive are probably stale "
        "and should not be promoted unchecked. Audience = investment partners (non-technical). "
        "Research cutoff: 2024-06-30."
    ),
    "dimensions_of_interest": [
        "energy density (Wh/kg, cell level)",
        "cycle life (cycles to 80% capacity)",
        "cost (USD/kWh, pack level, 2023-2024 estimates)",
        "thermal safety",
        "commercial maturity for grid-scale",
        "supply chain risk",
    ],
    "warning": (
        "Do NOT reuse the blended_prices_2021.csv directly — those figures are unverified "
        "and from a different use-case context."
    ),
    "status": "RAW_BRIEF - requires proper research project setup before any writing",
}

with open(os.path.join(workspace, "project_brief.json"), "w") as f:
    json.dump(brief, f, indent=2)

print("Workspace scaffold created.")
print("Files created:")
for root, dirs_list, files in os.walk(workspace):
    for file in files:
        print(" ", os.path.join(root, file).replace(workspace, ""))