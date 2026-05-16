import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── distractor directory structure ──────────────────────────────────────────
dirs = [
    "patient_records/archive/2022",
    "patient_records/archive/2023",
    "patient_records/current",
    "lab_results/genomics/raw",
    "lab_results/genomics/processed",
    "lab_results/blood_panel",
    "reports/draft",
    "reports/final",
    "configs/pipeline",
    "configs/legacy",
    "scripts/deprecated",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "patient_records/archive/2022/patient_001_blood.csv": "sample_id,hemoglobin,glucose\nPT001,14.2,95\nPT002,13.8,102\n",
    "patient_records/archive/2022/patient_002_notes.txt": "Patient exhibits normal metabolizer profile for warfarin based on clinical observation.\n",
    "patient_records/archive/2023/genotype_summary_OLD.txt": "DEPRECATED FORMAT - DO NOT USE\nrsid\tchr\tpos\tgenotype\n",
    "patient_records/current/intake_form.txt": "Name: Jane Doe\nDOB: 1985-03-21\nConsent: YES\nTest: AncestryDNA\n",
    "lab_results/genomics/raw/sequencing_run_20240101.log": "Run ID: SR-2024-001\nStatus: COMPLETE\nSNPs called: 700000\nQuality: PASS\n",
    "lab_results/genomics/raw/README_IGNORE.txt": "Raw files in this directory are FASTQ. Use bcftools for processing.\n",
    "lab_results/genomics/processed/variant_calls.vcf": "##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n1\t12345\trs1234\tA\tG\t99\tPASS\t.\n",
    "lab_results/blood_panel/cbc_results.json": '{"WBC": 6.2, "RBC": 4.8, "HGB": 14.1, "HCT": 42.3, "PLT": 250}\n',
    "reports/draft/annual_summary_2023.md": "# Annual Genomics Summary 2023\n\nTotal samples processed: 1,247\nPharmacogenomic reports issued: 389\n",
    "reports/final/QC_checklist.txt": "[ ] Verify SNP coverage\n[ ] Check format compliance\n[ ] Review star allele calls\n[ ] Sign off by clinical pharmacist\n",
    "configs/pipeline/settings.yaml": "pipeline:\n  version: 2.1\n  input_format: auto\n  output_dir: reports/\n  log_level: INFO\n",
    "configs/legacy/old_pipeline_config.ini": "[settings]\nformat=23andme_v3\noutput=txt\ndeprecated=true\n",
    "scripts/deprecated/convert_v2_to_v3.py": "#!/usr/bin/env python3\n# DEPRECATED: use pharmgx_reporter.py instead\nprint('This script is no longer supported.')\n",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── The actual 23andMe raw data file ─────────────────────────────────────────
# 23andMe format: header lines starting with '#', then tab-separated columns:
#   rsid  chromosome  position  genotype
#
# We include the exact pharmacogenomic SNPs that pharmgx_reporter.py looks for.
# These 31 SNPs span the 12 genes listed in SKILL.md.
# Source: well-known CPIC SNPs for each gene.

snp_data = [
    # CYP2C19 - key SNPs
    ("rs4244285",  "10", "96541616", "AG"),   # CYP2C19*2 (het) -> intermediate metabolizer
    ("rs4986893",  "10", "96540410", "GG"),   # CYP2C19*3 wildtype
    ("rs28399504", "10", "96522463", "AA"),   # CYP2C19*4 wildtype ref
    ("rs56337013", "10", "96535753", "CC"),   # CYP2C19*5 wildtype
    ("rs72552267", "10", "96527825", "GG"),   # CYP2C19*6 wildtype
    ("rs12248560", "10", "96521657", "CT"),   # CYP2C19*17 (het) -> rapid
    # CYP2D6 - key SNPs
    ("rs3892097",  "22", "42524947", "AG"),   # CYP2D6*4 het
    ("rs5030655",  "22", "42522613", "AA"),   # CYP2D6*6 wildtype
    ("rs16947",    "22", "42523805", "AG"),   # CYP2D6*2 het
    ("rs1065852",  "22", "42524175", "AG"),   # CYP2D6*10 het
    # CYP2C9 - key SNPs
    ("rs1799853",  "10", "96702047", "CT"),   # CYP2C9*2 het
    ("rs1057910",  "10", "96741053", "AC"),   # CYP2C9*3 het
    # VKORC1
    ("rs9923231",  "16",  "31096368", "AG"),  # VKORC1 -1639G>A het
    ("rs9934438",  "16",  "31094050", "AG"),  # VKORC1 het
    # SLCO1B1
    ("rs4149056",  "12",  "21178615", "TC"),  # SLCO1B1 *5 het
    ("rs2306283",  "12",  "21110994", "AG"),  # SLCO1B1 het
    # DPYD - key SNPs
    ("rs3918290",  "1",  "97981395", "GG"),   # DPYD *2A wildtype
    ("rs55886062", "1",  "97915614", "AA"),   # DPYD wildtype
    ("rs67376798", "1",  "97450058", "TT"),   # DPYD wildtype
    ("rs75017182", "1",  "98039419", "GG"),   # DPYD wildtype
    # TPMT - key SNPs
    ("rs1800462",  "6",  "18143955", "CC"),   # TPMT *2 wildtype
    ("rs1800460",  "6",  "18144013", "CT"),   # TPMT *3B het
    ("rs1142345",  "6",  "18128547", "TC"),   # TPMT *3C het
    # UGT1A1
    ("rs8175347",  "2",  "234668880", "TA/TA"),  # UGT1A1 *28 homo - Gilbert
    # CYP3A5
    ("rs776746",   "7",  "99245176", "AG"),   # CYP3A5 *3 het
    # CYP2B6
    ("rs3745274",  "19", "41512841", "GT"),   # CYP2B6 *6 het
    ("rs2279343",  "19", "41522715", "AA"),   # CYP2B6 wildtype
    # NUDT15
    ("rs116855232","13", "48037826", "CC"),   # NUDT15 wildtype
    # CYP1A2
    ("rs762551",   "15", "75041917", "AC"),   # CYP1A2 *1F het
    # Additional SNPs to reach 31
    ("rs28371725", "22", "42524175", "GG"),   # CYP2D6 region
    ("rs4986782",  "10", "96702047", "GG"),   # CYP2C9 region
]

header = (
    "# This data file generated by 23andMe at: Mon Jan 15 09:30:00 2024\n"
    "#\n"
    "# Below is a text version of your data. Fields are TAB-separated\n"
    "# Each line corresponds to a single SNP. For each SNP, we provide its identifier\n"
    "# (an rsid or an internal id), its location on the reference human genome, and the\n"
    "# genotype call oriented with respect to the plus strand on the human reference sequence.\n"
    "#\n"
    "# rsid\tchromosome\tposition\tgenotype\n"
)

# Write the 23andMe format file to a plausible-looking but non-obvious location
raw_data_path = os.path.join(workspace, "lab_results/genomics/raw/sample_GX_PT2024_042.txt")
with open(raw_data_path, "w") as f:
    f.write(header)
    for rsid, chrom, pos, geno in snp_data:
        f.write(f"{rsid}\t{chrom}\t{pos}\t{geno}\n")

print(f"[gen_inputs] Created 23andMe input file: {raw_data_path}")
print(f"[gen_inputs] Created {len(distractors)} distractor files across {len(dirs)} directories")
print("[gen_inputs] Workspace ready.")