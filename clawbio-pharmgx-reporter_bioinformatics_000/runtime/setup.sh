#!/bin/bash
set -e

echo "[setup] Setting up ClawBio pharmgx_reporter.py..."

# Since GitHub is not accessible, create a functional pharmgx_reporter.py locally
cat > /opt/clawbio/pharmgx_reporter.py << 'PYEOF'
#!/usr/bin/env python3
"""
pharmgx_reporter.py - Pharmacogenomics reporter for 23andMe raw data files.
Analyzes key pharmacogenomic SNPs and generates a clinical report.
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Key pharmacogenomic SNPs and their interpretations
PHARMGX_SNPS = {
    # CYP2C19
    "rs4244285":  {"gene": "CYP2C19", "variant": "*2",   "risk_allele": "A", "effect": "Loss of function"},
    "rs4986893":  {"gene": "CYP2C19", "variant": "*3",   "risk_allele": "A", "effect": "Loss of function"},
    "rs28399504": {"gene": "CYP2C19", "variant": "*4",   "risk_allele": "T", "effect": "Loss of function"},
    "rs56337013": {"gene": "CYP2C19", "variant": "*5",   "risk_allele": "T", "effect": "Loss of function"},
    "rs72552267": {"gene": "CYP2C19", "variant": "*6",   "risk_allele": "A", "effect": "Loss of function"},
    "rs12248560": {"gene": "CYP2C19", "variant": "*17",  "risk_allele": "T", "effect": "Increased function"},
    # CYP2D6
    "rs3892097":  {"gene": "CYP2D6",  "variant": "*4",   "risk_allele": "A", "effect": "Loss of function"},
    "rs5030655":  {"gene": "CYP2D6",  "variant": "*6",   "risk_allele": "del","effect": "Loss of function"},
    "rs16947":    {"gene": "CYP2D6",  "variant": "*2",   "risk_allele": "A", "effect": "Reduced function"},
    "rs1065852":  {"gene": "CYP2D6",  "variant": "*10",  "risk_allele": "T", "effect": "Reduced function"},
    # CYP2C9
    "rs1799853":  {"gene": "CYP2C9",  "variant": "*2",   "risk_allele": "T", "effect": "Reduced function"},
    "rs1057910":  {"gene": "CYP2C9",  "variant": "*3",   "risk_allele": "C", "effect": "Loss of function"},
    # VKORC1
    "rs9923231":  {"gene": "VKORC1",  "variant": "-1639G>A", "risk_allele": "A", "effect": "Warfarin sensitivity"},
    "rs9934438":  {"gene": "VKORC1",  "variant": "1173C>T",  "risk_allele": "A", "effect": "Warfarin sensitivity"},
    # SLCO1B1
    "rs4149056":  {"gene": "SLCO1B1", "variant": "*5",   "risk_allele": "C", "effect": "Reduced transport - statin risk"},
    "rs2306283":  {"gene": "SLCO1B1", "variant": "*1b",  "risk_allele": "G", "effect": "Increased transport"},
    # DPYD
    "rs3918290":  {"gene": "DPYD",    "variant": "*2A",  "risk_allele": "A", "effect": "Loss of function - fluoropyrimidine toxicity"},
    "rs55886062": {"gene": "DPYD",    "variant": "*13",  "risk_allele": "C", "effect": "Loss of function"},
    "rs67376798": {"gene": "DPYD",    "variant": "D949V","risk_allele": "A", "effect": "Reduced function"},
    "rs75017182": {"gene": "DPYD",    "variant": "HapB3","risk_allele": "A", "effect": "Reduced function"},
    # TPMT
    "rs1800462":  {"gene": "TPMT",    "variant": "*2",   "risk_allele": "A", "effect": "Loss of function - thiopurine toxicity"},
    "rs1800460":  {"gene": "TPMT",    "variant": "*3B",  "risk_allele": "A", "effect": "Loss of function"},
    "rs1142345":  {"gene": "TPMT",    "variant": "*3C",  "risk_allele": "C", "effect": "Loss of function"},
    # UGT1A1
    "rs8175347":  {"gene": "UGT1A1",  "variant": "*28",  "risk_allele": "TA","effect": "Reduced function - irinotecan toxicity"},
    # CYP3A5
    "rs776746":   {"gene": "CYP3A5",  "variant": "*3",   "risk_allele": "A", "effect": "Loss of function - non-expresser"},
    # CYP2B6
    "rs3745274":  {"gene": "CYP2B6",  "variant": "*6",   "risk_allele": "T", "effect": "Reduced function"},
    "rs2279343":  {"gene": "CYP2B6",  "variant": "*4",   "risk_allele": "A", "effect": "Increased function"},
    # NUDT15
    "rs116855232":{"gene": "NUDT15",  "variant": "*3",   "risk_allele": "A", "effect": "Loss of function - thiopurine toxicity"},
    # CYP1A2
    "rs762551":   {"gene": "CYP1A2",  "variant": "*1F",  "risk_allele": "A", "effect": "Increased inducibility"},
}

DRUG_GENE_MAP = {
    "CYP2C19": ["clopidogrel", "omeprazole", "escitalopram", "sertraline", "voriconazole"],
    "CYP2D6":  ["codeine", "tamoxifen", "fluoxetine", "amitriptyline", "metoprolol"],
    "CYP2C9":  ["warfarin", "phenytoin", "ibuprofen", "celecoxib"],
    "VKORC1":  ["warfarin"],
    "SLCO1B1": ["simvastatin", "atorvastatin", "rosuvastatin"],
    "DPYD":    ["fluorouracil", "capecitabine"],
    "TPMT":    ["azathioprine", "mercaptopurine", "thioguanine"],
    "UGT1A1":  ["irinotecan", "atazanavir"],
    "CYP3A5":  ["tacrolimus", "cyclosporine"],
    "CYP2B6":  ["efavirenz", "methadone", "bupropion"],
    "NUDT15":  ["azathioprine", "mercaptopurine"],
    "CYP1A2":  ["caffeine", "clozapine", "theophylline"],
}


def parse_23andme(filepath):
    """Parse a 23andMe raw data file."""
    rows = []
    with open(filepath, "r") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 4:
                rows.append({
                    "rsid": parts[0],
                    "chromosome": parts[1],
                    "position": parts[2],
                    "genotype": parts[3],
                })
    return pd.DataFrame(rows)


def analyze_snps(df):
    """Cross-reference genotypes against known pharmacogenomic SNPs."""
    findings = []
    snp_lookup = {row["rsid"]: row["genotype"] for _, row in df.iterrows()}

    for rsid, info in PHARMGX_SNPS.items():
        genotype = snp_lookup.get(rsid, "NOT_FOUND")
        risk_allele = info["risk_allele"]
        copies = 0
        if genotype != "NOT_FOUND":
            copies = genotype.count(risk_allele)
        status = "wildtype"
        if copies == 1:
            status = "heterozygous"
        elif copies >= 2:
            status = "homozygous"

        findings.append({
            "rsid": rsid,
            "gene": info["gene"],
            "variant": info["variant"],
            "genotype": genotype,
            "risk_allele": risk_allele,
            "copies": copies,
            "status": status,
            "effect": info["effect"] if copies > 0 and genotype != "NOT_FOUND" else "No effect",
        })
    return pd.DataFrame(findings)


def generate_report(findings_df, input_file):
    """Generate a pharmacogenomics report."""
    lines = []
    lines.append("=" * 70)
    lines.append("PHARMACOGENOMICS REPORT")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Input file: {input_file}")
    lines.append("=" * 70)
    lines.append("")

    # Summary by gene
    lines.append("GENE SUMMARY")
    lines.append("-" * 40)
    genes = findings_df["gene"].unique()
    for gene in sorted(genes):
        gene_df = findings_df[findings_df["gene"] == gene]
        actionable = gene_df[gene_df["copies"] > 0]
        drugs = ", ".join(DRUG_GENE_MAP.get(gene, ["N/A"]))
        if len(actionable) > 0:
            lines.append(f"  {gene}: {len(actionable)} actionable variant(s) found")
            for _, row in actionable.iterrows():
                lines.append(f"    - {row['variant']} ({row['rsid']}): {row['status']} | {row['effect']}")
        else:
            lines.append(f"  {gene}: No actionable variants detected")
        lines.append(f"    Relevant drugs: {drugs}")
        lines.append("")

    # Actionable findings
    actionable_all = findings_df[findings_df["copies"] > 0]
    lines.append("")
    lines.append("ACTIONABLE FINDINGS")
    lines.append("-" * 40)
    if len(actionable_all) == 0:
        lines.append("  No actionable pharmacogenomic variants detected.")
    else:
        lines.append(f"  {len(actionable_all)} actionable variant(s) identified:")
        lines.append("")
        for _, row in actionable_all.iterrows():
            lines.append(f"  Gene: {row['gene']}  Variant: {row['variant']}  ({row['rsid']})")
            lines.append(f"    Genotype: {row['genotype']}  Status: {row['status']}")
            lines.append(f"    Effect: {row['effect']}")
            drugs = ", ".join(DRUG_GENE_MAP.get(row['gene'], ["N/A"]))
            lines.append(f"    Relevant drugs: {drugs}")
            lines.append("")

    lines.append("=" * 70)
    lines.append("DISCLAIMER: This report is for research purposes only.")
    lines.append("Clinical decisions should be made by qualified healthcare professionals.")
    lines.append("=" * 70)

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: pharmgx_reporter.py <23andme_raw_data_file> [output_report_file]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) >= 3 else None

    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    print(f"[pharmgx_reporter] Parsing 23andMe data: {input_file}")
    df = parse_23andme(input_file)
    print(f"[pharmgx_reporter] Loaded {len(df)} SNP records.")

    print("[pharmgx_reporter] Analyzing pharmacogenomic variants...")
    findings = analyze_snps(df)

    report = generate_report(findings, input_file)

    if output_file:
        with open(output_file, "w") as fh:
            fh.write(report)
        print(f"[pharmgx_reporter] Report written to: {output_file}")
    else:
        print(report)


if __name__ == "__main__":
    main()
PYEOF

chmod +x /opt/clawbio/pharmgx_reporter.py
echo "[setup] pharmgx_reporter.py created and made executable."

# Symlink the script into workspace so agent can easily find it
ln -sf /opt/clawbio/pharmgx_reporter.py /workspace/pharmgx_reporter.py
echo "[setup] Symlinked pharmgx_reporter.py to /workspace/"

echo "[setup] Setup complete. Workspace contents:"
ls /workspace/