import os
import random
import json

random.seed(42)

workspace = "/workspace"

# Create deeply nested distractor structure
dirs = [
    "lab/proteomics/raw_data",
    "lab/proteomics/processed",
    "lab/genomics/alignments",
    "lab/genomics/variants",
    "lab/notes/meetings",
    "lab/notes/experiments",
    "lab/scripts/analysis",
    "lab/scripts/visualization",
    "lab/reports/2023",
    "lab/reports/2024",
    "config",
    "archive/old_notes",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "lab/proteomics/raw_data/sample_001.tsv": "protein_id\tintensity\nP12345\t1200.5\nQ98765\t340.2\n",
    "lab/proteomics/processed/normalized.csv": "sample,value\ns1,0.45\ns2,0.78\n",
    "lab/genomics/alignments/run42.bam.log": "Aligned reads: 15432112\nUnmapped: 234098\n",
    "lab/genomics/variants/snp_calls.vcf": "#CHROM\tPOS\tID\tREF\tALT\nchr1\t10345\t.\tA\tG\n",
    "lab/notes/meetings/2024_01_15.txt": "Discussed pipeline bottleneck. Need to optimize the alignment step.\n",
    "lab/notes/meetings/2024_03_22.txt": "Budget approved for new sequencer. Q3 delivery expected.\n",
    "lab/scripts/analysis/pipeline.sh": "#!/bin/bash\necho 'Running pipeline'\n",
    "lab/scripts/visualization/plot_pca.py": "import matplotlib.pyplot as plt\n# PCA plot stub\n",
    "lab/reports/2023/annual_summary.pdf.placeholder": "PDF binary placeholder\n",
    "lab/reports/2024/q1_metrics.json": json.dumps({"samples": 120, "success_rate": 0.94}),
    "config/db_config.yaml": "host: localhost\nport: 5432\ndb: labdb\n",
    "archive/old_notes/legacy_protocol.txt": "Old HPLC protocol from 2019. Deprecated.\n",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# THE PROBLEM: raw research notes that must be ingested into the memory system
# These notes mix different categories and importances
research_notes = [
    {
        "id": 1,
        "text": "CRISPR-Cas9 editing efficiency drops below 30% when GC content of guide RNA exceeds 70%.",
        "category": "fact",
        "importance": 0.9
    },
    {
        "id": 2,
        "text": "We learned that pre-warming the enzyme mix at 37C for 5 minutes before adding DNA significantly reduces off-target edits.",
        "category": "lesson",
        "importance": 0.85
    },
    {
        "id": 3,
        "text": "The PI prefers tabular output formats over heatmaps for presenting variant frequency data in weekly reports.",
        "category": "preference",
        "importance": 0.7
    },
    {
        "id": 4,
        "text": "Ran the full exome sequencing pipeline on cohort B (n=48). 94% mapping rate. SNP density: 3.2 per kbp.",
        "category": "experience",
        "importance": 0.75
    },
    {
        "id": 5,
        "text": "Proficient in using Bowtie2 with local alignment mode for short-read RNA-seq data against custom transcriptomes.",
        "category": "skill",
        "importance": 0.8
    },
    {
        "id": 6,
        "text": "PCR contamination was identified as the main source of false positives in the April sequencing run.",
        "category": "experience",
        "importance": 0.88
    },
    {
        "id": 7,
        "text": "Optimal annealing temperature for primer pair ALK-F/R is 58°C based on gradient PCR results.",
        "category": "fact",
        "importance": 0.82
    },
    {
        "id": 8,
        "text": "Team prefers Conda over pip for managing bioinformatics tool dependencies to avoid conflicts.",
        "category": "preference",
        "importance": 0.65
    },
    {
        "id": 9,
        "text": "Always validate reference genome chromosome naming convention (chr1 vs 1) before running GATK HaplotypeCaller.",
        "category": "lesson",
        "importance": 0.9
    },
    {
        "id": 10,
        "text": "Capable of designing multiplex PCR panels targeting up to 96 amplicons simultaneously with balanced primer concentrations.",
        "category": "skill",
        "importance": 0.77
    },
]

notes_path = os.path.join(workspace, "lab/notes/experiments/research_notes.json")
with open(notes_path, "w") as f:
    json.dump(research_notes, f, indent=2)

# Search queries that the agent must run
search_queries = [
    "PCR contamination and sequencing errors",
    "CRISPR editing efficiency",
    "user preferences for data presentation"
]

queries_path = os.path.join(workspace, "lab/notes/experiments/search_queries.txt")
with open(queries_path, "w") as f:
    for q in search_queries:
        f.write(q + "\n")

print("Workspace generated successfully.")
print(f"Research notes: {notes_path}")
print(f"Search queries: {queries_path}")