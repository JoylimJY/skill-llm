import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create distractor directory structure ---

dirs = [
    "pharma_pipeline/compound_library",
    "pharma_pipeline/assay_results",
    "pharma_pipeline/reports/q3",
    "pharma_pipeline/reports/q4",
    "pharma_pipeline/models/toxicity",
    "pharma_pipeline/models/efficacy",
    "legacy_data/imports",
    "legacy_data/exports",
    "config_backups",
    "scripts/deprecated",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor: compound library CSVs
for i in range(1, 5):
    (workspace / f"pharma_pipeline/compound_library/batch_{i:03d}.csv").write_text(
        f"compound_id,smiles,mw,logP\nCPD-{1000+i},CC(=O)Oc1ccccc1C(=O)O,180.16,1.19\nCPD-{2000+i},c1ccc(cc1)N,93.12,1.08\n"
    )

# Distractor: assay result JSONs (look like submission data but are NOT)
assay_data = [
    {"compound": "CPD-1001", "ic50_nm": 45.2, "selectivity_ratio": 8.3, "analyst": "Dr. Chen"},
    {"compound": "CPD-1002", "ic50_nm": 12.1, "selectivity_ratio": 15.7, "analyst": "Dr. Patel"},
    {"compound": "CPD-1003", "ic50_nm": 78.9, "selectivity_ratio": 3.2, "analyst": "Dr. Moore"},
]
for i, ad in enumerate(assay_data):
    (workspace / f"pharma_pipeline/assay_results/assay_run_{i+1}.json").write_text(
        json.dumps(ad, indent=2)
    )

# Distractor: model scoring outputs (might look like confidence scores)
efficacy_scores = {
    "model_version": "efficacy-v2.3",
    "run_id": "run_20240115_001",
    "scores": [
        {"compound": "CPD-1001", "predicted_efficacy": 0.73, "std_dev": 0.08},
        {"compound": "CPD-1002", "predicted_efficacy": 0.91, "std_dev": 0.03},
        {"compound": "CPD-1003", "predicted_efficacy": 0.55, "std_dev": 0.12},
    ]
}
(workspace / "pharma_pipeline/models/efficacy/scores_batch_001.json").write_text(
    json.dumps(efficacy_scores, indent=2)
)

toxicity_scores = {
    "model_version": "tox-v1.8",
    "scores": [
        {"compound": "CPD-1001", "ld50_predicted": 820, "hERG_risk": "low"},
        {"compound": "CPD-1002", "ld50_predicted": 1240, "hERG_risk": "minimal"},
        {"compound": "CPD-1003", "ld50_predicted": 310, "hERG_risk": "high"},
    ]
}
(workspace / "pharma_pipeline/models/toxicity/tox_screening_batch001.json").write_text(
    json.dumps(toxicity_scores, indent=2)
)

# Distractor: old/wrong config files that look partially correct but are stale
bad_config = {
    "mode": "global",
    "global": {
        "baseUrl": "https://old-consensus-server.internal",
        "accessToken": "EXPIRED_TOKEN_abc123"
    },
    "safety": {"allowNetworkSideEffects": True}
}
(workspace / "config_backups/consensus_config_old.json").write_text(
    json.dumps(bad_config, indent=2)
)

another_bad_config = {
    "mode": "local",
    "storage": {"kind": "json", "path": "./broken_path/consensus.json"},
    "policy": "MAJORITY_VOTE"
}
(workspace / "config_backups/consensus_config_draft.json").write_text(
    json.dumps(another_bad_config, indent=2)
)

# Distractor: Q3 report
(workspace / "pharma_pipeline/reports/q3/q3_summary.txt").write_text(
    "Q3 Pipeline Summary\n===================\nTotal compounds screened: 487\nHits identified: 23\nAdvanced to lead optimization: 3\n\nLead compounds: CPD-1001, CPD-1002, CPD-1003\n"
)

# Distractor: Q4 evaluation plan - this is the ACTUAL TASK DESCRIPTION for the agent
q4_plan = """# Q4 Lead Compound Evaluation Pipeline

## Objective
We need to stand up a local, autonomous decision pipeline to formally evaluate our three lead 
compounds and select the single best candidate for Phase I trials. The selection must be 
auditable, reproducible, and use a structured multi-agent decision framework.

## Pipeline Specification

**Decision Job**
- Title: "Lead Compound Selection for Phase I"
- Description: "Evaluate CPD-1001, CPD-1002, and CPD-1003 and return exactly: { compound_id, predicted_efficacy, predicted_safety_score, recommendation, confidence } where confidence is a float between 0 and 1."
- Input: "Q3 hit compounds: CPD-1001 (efficacy=0.73, tox=low), CPD-1002 (efficacy=0.91, tox=minimal), CPD-1003 (efficacy=0.55, tox=high)"
- Mode: SUBMISSION (agents propose candidates)
- Policy: HIGHEST_CONFIDENCE_SINGLE (the highest-confidence proposal wins)
- Reward budget: 15 credits
- Stake required: 5 credits per submission
- Expiry: 300 seconds

**Required Agent Submissions**
Three simulated agent submissions must be created for this job:

  Agent A (AlphaScreen-Agent):
    artifact: {"compound_id":"CPD-1002","predicted_efficacy":0.91,"predicted_safety_score":0.88,"recommendation":"advance","confidence":0.91}
    summary: "CPD-1002 shows best efficacy-safety balance based on hERG and IC50 data."
    confidence: 0.91

  Agent B (BetaModel-Agent):
    artifact: {"compound_id":"CPD-1001","predicted_efficacy":0.73,"predicted_safety_score":0.74,"recommendation":"advance","confidence":0.78}
    summary: "CPD-1001 has acceptable profile with lower toxicity risk."
    confidence: 0.78

  Agent C (GammaRisk-Agent):
    artifact: {"compound_id":"CPD-1003","predicted_efficacy":0.55,"predicted_safety_score":0.31,"recommendation":"deprioritize","confidence":0.62}
    summary: "CPD-1003 has high hERG risk and low efficacy; not recommended."
    confidence: 0.62

**Deliverable**
After resolving the pipeline, save the final consensus result as `pipeline_result.json` 
in the workspace root directory.
"""
(workspace / "pharma_pipeline/reports/q4/q4_evaluation_plan.md").write_text(q4_plan)

# Distractor: deprecated scripts
(workspace / "scripts/deprecated/old_vote_tallier.sh").write_text(
    "#!/bin/bash\n# DEPRECATED: Use consensus-tools instead\necho 'This script is deprecated'\n"
)
(workspace / "scripts/deprecated/legacy_submission_parser.py").write_text(
    "# DEPRECATED\n# Old submission parser, replaced by consensus-tools pipeline\nimport json\nprint('deprecated')\n"
)

# Distractor: legacy data
(workspace / "legacy_data/imports/historical_votes.json").write_text(
    json.dumps({"votes": [{"compound": "CPD-999", "vote": "yes", "voter": "legacy-agent-1"}], "resolved": False}, indent=2)
)
(workspace / "legacy_data/exports/old_results.json").write_text(
    json.dumps({"winner": "CPD-999", "policy": "manual", "timestamp": "2023-03-01T00:00:00Z"}, indent=2)
)

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")