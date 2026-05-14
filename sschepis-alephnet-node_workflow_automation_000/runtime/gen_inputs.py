import os
import json
import random
import string

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Create a realistic, deeply nested directory structure with distractor files ---

dirs = [
    "lab/crispr/experiments/2023",
    "lab/crispr/experiments/2024",
    "lab/crispr/protocols",
    "lab/genomics/sequencing",
    "lab/genomics/analysis",
    "lab/notes/drafts",
    "lab/notes/published",
    "lab/agents/configs",
    "lab/agents/logs",
    "lab/reports/quarterly",
    "lab/reports/annual",
    "admin/budgets",
    "admin/personnel",
    "data/raw/batch_001",
    "data/raw/batch_002",
    "data/processed",
    "data/archives",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files with plausible-but-irrelevant content

distractor_files = {
    "lab/crispr/experiments/2023/exp_001.txt": "Experiment 001: Cas9 delivery efficiency in HEK293 cells. Success rate: 73%.",
    "lab/crispr/experiments/2023/exp_002.txt": "Experiment 002: Off-target cleavage analysis. No significant off-target sites detected.",
    "lab/crispr/experiments/2024/exp_010.txt": "Experiment 010: HDR vs NHEJ repair pathway comparison in primary fibroblasts.",
    "lab/crispr/experiments/2024/exp_011.txt": "Experiment 011: Base editing with BE3 system for single nucleotide corrections.",
    "lab/crispr/protocols/cas9_delivery.md": "# Cas9 Delivery Protocol\n\nPrepare ribonucleoprotein (RNP) complexes at 1:2.5 molar ratio...",
    "lab/crispr/protocols/guide_rna_design.md": "# Guide RNA Design\n\nUse 20nt spacer sequence complementary to target...",
    "lab/genomics/sequencing/batch_seq_001.csv": "sample_id,coverage,quality\nS001,45.2,Q30\nS002,38.7,Q28\nS003,52.1,Q31",
    "lab/genomics/analysis/variant_calls.vcf": "##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\nChr1\t12345\t.\tA\tG",
    "lab/notes/drafts/hypothesis_v1.txt": "Hypothesis: CRISPR-Cas9 editing efficiency correlates with chromatin accessibility.",
    "lab/notes/drafts/hypothesis_v2.txt": "Revised hypothesis: Epigenetic state at target locus is the primary determinant of editing efficiency.",
    "lab/notes/published/nature_methods_2023.txt": "Published: 'Chromatin-aware CRISPR targeting improves specificity by 3.2-fold.'",
    "lab/agents/configs/analyst_v1.json": json.dumps({"name": "OldAnalyst", "version": "0.1", "deprecated": True}),
    "lab/agents/configs/analyst_v2.json": json.dumps({"name": "NewAnalyst", "version": "0.2", "status": "pending_setup"}),
    "lab/agents/logs/run_2024_01.log": "2024-01-15 09:12:33 INFO Agent started\n2024-01-15 09:45:11 INFO Analysis complete\n",
    "lab/reports/quarterly/Q1_2024.txt": "Q1 2024 Research Summary: 3 experiments completed, 1 paper submitted.",
    "lab/reports/annual/2023_annual.txt": "Annual Report 2023: Major breakthrough in HDR efficiency using modified donor templates.",
    "admin/budgets/2024_budget.csv": "category,allocated,spent\nReagents,50000,32450\nEquipment,120000,89000",
    "admin/personnel/team_roster.txt": "PI: Dr. Sarah Chen\nPostdoc: Dr. James Okafor\nGrad Student: Maria Santos",
    "data/raw/batch_001/reads_R1.fastq.gz.md5": "d41d8cd98f00b204e9800998ecf8427e  reads_R1.fastq.gz",
    "data/raw/batch_002/reads_R1.fastq.gz.md5": "a87ff679a2f3e71d9181a67b7542122c  reads_R1.fastq.gz",
    "data/processed/alignment_stats.txt": "Total reads: 45,231,887\nMapped: 44,198,332 (97.7%)\nUniquely mapped: 41,023,445 (90.7%)",
    "data/archives/legacy_data_2021.tar.gz.md5": "c4ca4238a0b923820dcc509a6f75849b  legacy_data_2021.tar.gz",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE CORE TASK INPUT FILE ---
# This file specifies the research findings the agent must persist, 
# and the analytical question the agent must investigate.
# It is intentionally written as a domain-expert memo, not a technical spec.

task_brief = {
    "task": "CRISPR Knowledge Base Setup and Autonomous Analysis",
    "memory_field": {
        "name": "CRISPR_Research_2024",
        "description": "Core CRISPR-Cas9 mechanistic findings for autonomous analysis",
        "consensus_threshold": 0.75,
        "knowledge_fragments": [
            {
                "content": "CRISPR-Cas9 creates double-strand breaks at genomic loci specified by guide RNA sequence complementarity",
                "significance": 0.95
            },
            {
                "content": "HDR (Homology-Directed Repair) enables precise gene correction but requires donor template and is cell-cycle dependent",
                "significance": 0.90
            },
            {
                "content": "NHEJ (Non-Homologous End Joining) is the dominant DSB repair pathway causing insertions and deletions",
                "significance": 0.85
            },
            {
                "content": "Cas9 off-target cleavage risk is inversely correlated with guide RNA specificity score",
                "significance": 0.88
            },
            {
                "content": "Chromatin accessibility at target locus strongly predicts editing efficiency across cell types",
                "significance": 0.92
            }
        ]
    },
    "agent": {
        "name": "CRISPRAnalyst",
        "template": "data-analyst",
        "initial_observation": "Analyze CRISPR-Cas9 double-strand break repair pathway competition between HDR and NHEJ"
    },
    "claims": {
        "primary": "HDR efficiency in CRISPR editing is fundamentally limited by cell-cycle phase availability of repair machinery",
        "supporting": "NHEJ dominance over HDR in post-mitotic cells is a major barrier to therapeutic gene correction"
    },
    "output_file": "pipeline_results.json"
}

with open(os.path.join(workspace, "task_brief.json"), "w") as f:
    json.dump(task_brief, f, indent=2)

print("Workspace generated successfully.")
print(f"Task brief written to: {workspace}/task_brief.json")
print(f"Total distractor files: {len(distractor_files)}")