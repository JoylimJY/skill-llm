import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Deep nested distractor file structure ---
dirs = [
    "research_pipeline/raw_data/biology",
    "research_pipeline/raw_data/chemistry",
    "research_pipeline/processed/reports",
    "research_pipeline/processed/summaries",
    "research_pipeline/archives/2022",
    "research_pipeline/archives/2023",
    "config/database",
    "config/api",
    "logs/ingestion",
    "logs/processing",
    "scripts/deprecated",
    "scripts/utils",
    "outputs/pending",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "research_pipeline/raw_data/biology/gene_expression_data.csv": (
        "gene_id,sample_1,sample_2,sample_3\n"
        "BRCA1,1.23,4.56,7.89\n"
        "TP53,0.45,1.23,2.34\n"
        "EGFR,3.21,6.54,9.87\n"
    ),
    "research_pipeline/raw_data/chemistry/compound_library.tsv": (
        "compound_id\tsmiles\tIC50\n"
        "CPD001\tCC(=O)Oc1ccccc1C(=O)O\t12.3\n"
        "CPD002\tCCCCCCCCCCCCCCCC\t45.6\n"
    ),
    "research_pipeline/processed/reports/quarterly_summary_Q3.txt": (
        "Q3 Research Summary\n"
        "====================\n"
        "Total papers reviewed: 142\n"
        "Relevant hits: 23\n"
        "Priority targets identified: 5\n"
    ),
    "research_pipeline/processed/summaries/protein_folding_notes.md": (
        "# Protein Folding Research Notes\n\n"
        "AlphaFold2 has revolutionized structural biology.\n"
        "Key papers to review in Q4 include advances in multimer prediction.\n"
    ),
    "research_pipeline/archives/2022/batch_001_metadata.json": json.dumps({
        "batch_id": "batch_001",
        "year": 2022,
        "source": "manual_curation",
        "paper_count": 34,
        "topics": ["CRISPR", "gene therapy", "RNA sequencing"]
    }, indent=2),
    "research_pipeline/archives/2023/batch_017_metadata.json": json.dumps({
        "batch_id": "batch_017",
        "year": 2023,
        "source": "automated_search",
        "paper_count": 67,
        "topics": ["deep learning", "genomics", "drug discovery"]
    }, indent=2),
    "config/database/db_config.ini": (
        "[database]\n"
        "host=localhost\n"
        "port=5432\n"
        "name=research_db\n"
        "user=pipeline_user\n"
    ),
    "config/api/endpoints.yaml": (
        "endpoints:\n"
        "  pubmed: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/\n"
        "  chembl: https://www.ebi.ac.uk/chembl/api/data/\n"
        "  uniprot: https://rest.uniprot.org/uniprotkb/\n"
    ),
    "logs/ingestion/ingest_2024_01_15.log": (
        "[2024-01-15 08:00:01] INFO  Pipeline started\n"
        "[2024-01-15 08:00:45] INFO  Fetched 200 records from source A\n"
        "[2024-01-15 08:02:10] WARN  Duplicate detected: record_id=9921\n"
        "[2024-01-15 08:05:00] INFO  Pipeline complete. 198 records ingested.\n"
    ),
    "logs/processing/process_2024_01_15.log": (
        "[2024-01-15 09:00:00] INFO  Processing batch batch_017\n"
        "[2024-01-15 09:03:22] ERROR Filter threshold exceeded for 3 records\n"
        "[2024-01-15 09:07:45] INFO  Processing complete.\n"
    ),
    "scripts/deprecated/old_search.py": (
        "# DEPRECATED - Do not use\n"
        "# This script used to query PubMed directly\n"
        "import requests\n"
        "def old_pubmed_search(query):\n"
        "    # This no longer works\n"
        "    pass\n"
    ),
    "scripts/utils/text_cleaner.py": (
        "import re\n\n"
        "def clean_abstract(text):\n"
        "    text = re.sub(r'\\s+', ' ', text)\n"
        "    return text.strip()\n"
    ),
    "outputs/pending/processing_queue.txt": (
        "Paper queue for manual review:\n"
        "- Review protein interaction networks paper\n"
        "- Check citation count for transformer biology paper\n"
        "- Validate gene regulatory network data\n"
    ),
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# --- The actual task input: a requirements specification file ---
# This is the "messy" input the agent must read and act upon
task_spec = {
    "project": "BioML Intelligence Sweep - Q1 2024",
    "requestor": "Dr. Elena Vasquez, Head of Computational Biology",
    "date_issued": "2024-01-20",
    "objective": (
        "Identify and catalog recent preprints at the intersection of "
        "machine learning and protein structure prediction. "
        "Focus exclusively on quantitative biology preprints."
    ),
    "search_parameters": {
        "primary_query": "protein structure prediction transformer",
        "discipline_filter": "q-bio",
        "result_limit": 5
    },
    "deliverables": [
        {
            "id": "D1",
            "description": "A JSON file named 'qbio_ml_papers.json' in the outputs/pending/ directory containing an array of paper objects. Each object must include: 'title', 'pdf_url', and 'arxiv_id' (extracted from the pdf_url or entry_id). Array must be sorted alphabetically by title."
        },
        {
            "id": "D2",
            "description": (
                "Download the PDF of the FIRST paper in the sorted list "
                "(alphabetically by title) to the directory 'research_pipeline/raw_data/biology/'. "
                "The file should retain whatever filename the download function assigns."
            )
        }
    ],
    "notes": (
        "Use the preprint repository system available via the internal toolchain. "
        "The category system uses short codes: 'q-bio' covers quantitative biology. "
        "Do not use PubMed or any other database."
    )
}

task_spec_path = workspace / "task_specification.json"
task_spec_path.write_text(json.dumps(task_spec, indent=2))

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 1}")