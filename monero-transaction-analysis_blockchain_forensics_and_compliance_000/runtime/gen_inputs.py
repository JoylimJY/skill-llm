import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create distractor directory structure ---
dirs = [
    "investigations/case_2024_001/raw",
    "investigations/case_2024_001/processed",
    "investigations/case_2024_002/raw",
    "investigations/archive/2023",
    "tools/parsers",
    "tools/validators",
    "reports/drafts",
    "reports/final",
    "data/blockchain/xmr",
    "data/blockchain/btc",
    "logs/audit",
    "config",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---

# Old partial report (incomplete, wrong format - distractor)
old_report = {
    "case": "2024-001",
    "note": "DRAFT - incomplete analysis",
    "transactions": []
}
with open(workspace / "reports/drafts/partial_report.json", "w") as f:
    json.dump(old_report, f, indent=2)

# Some hex-like distractor files
with open(workspace / "data/blockchain/xmr/old_tx.hex", "w") as f:
    f.write("0200010408fbf2a5e3d7c1b9a4e8f2d6c0b3a7e1f5d9c2b6a0e4f8d2c5b9a3e7f1d4c8b2a6e0f3d7c1b5a9e2f6d0c4b8a2e5f9d3c7b1a4e8f2d6\n")

with open(workspace / "data/blockchain/btc/sample.hex", "w") as f:
    f.write("01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff\n")

# Config files (distractors)
with open(workspace / "config/analysis_config.ini", "w") as f:
    f.write("[general]\nverbose=true\noutput_format=json\n\n[privacy]\nmin_ring_size=5\nwarning_threshold=8\n")

# Note: min_ring_size=5 here is a TRAP - the skill says 11+ is the correct threshold

with open(workspace / "config/tool_paths.conf", "w") as f:
    f.write("MONERO_EXPLORER=https://xmrchain.net\nMONERO_CLI=/usr/local/bin/monero-transaction\n")

# Audit log distractors
with open(workspace / "logs/audit/access_2024.log", "w") as f:
    f.write("2024-01-15 09:23:11 INFO  Session started\n")
    f.write("2024-01-15 09:23:45 INFO  Transaction lookup initiated\n")
    f.write("2024-01-15 09:24:02 WARN  High-value transaction detected\n")

# Old analysis scripts (distractors, wrong approach)
with open(workspace / "tools/parsers/old_parser.py", "w") as f:
    f.write("# Deprecated parser - do not use\n# This script uses the old API format\nimport json\n\ndef parse_tx(hex_data):\n    # TODO: update to new format\n    return {}\n")

with open(workspace / "tools/validators/ring_check.py", "w") as f:
    f.write("# Old validator - threshold may be outdated\nMIN_RING = 7  # CHECK THIS VALUE\n\ndef check_ring(size):\n    return size >= MIN_RING\n")

# Distractor: some txids text file (not the actual task file)
with open(workspace / "investigations/case_2024_001/raw/suspicious_addresses.txt", "w") as f:
    f.write("# Suspicious addresses flagged for review\n")
    f.write("48GbauUw5NHAp2Emzc5e8yZJMEGLJqPn5KdnLhrBPq4fLMZ9SopmFnSTMycjYbi4kahyve7JdHYvs9VDVhMSmBLSBDrdBbu\n")
    f.write("44AFFq5kSiGBoZ4NMDwYtN18obc8AemS33DBLWs3H7otXft3XjrpDtQGv7SqSsaBYBb98uNbr2VBBEt7f2wfn3RVGQBEP3A\n")

with open(workspace / "investigations/case_2024_002/raw/notes.txt", "w") as f:
    f.write("Investigation opened 2024-03-10\nSuspect used multiple addresses\nTransaction pattern: consolidation\n")

with open(workspace / "investigations/archive/2023/closed_cases.txt", "w") as f:
    f.write("Case 2023-001: Closed - insufficient evidence\nCase 2023-002: Closed - resolved\n")

# The actual task input: a list of transaction IDs to investigate
task_input = {
    "case_id": "CASE-2024-XMR-007",
    "description": "Compliance audit request: analyze the following Monero transactions for privacy adequacy and produce a structured forensic report.",
    "transactions": [
        "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
        "f0e1d2c3b4a5f6e7d8c9b0a1f2e3d4c5b6a7f8e9d0c1b2a3f4e5d6c7b8a9f0e1",
        "9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7"
    ],
    "instructions": "For each transaction ID above, run the full analysis pipeline and compile the results into a single file named forensic_report.json"
}
with open(workspace / "investigations/case_2024_001/txids_for_analysis.json", "w") as f:
    json.dump(task_input, f, indent=2)

# Additional distractors
with open(workspace / "tools/parsers/fee_estimator.sh", "w") as f:
    f.write("#!/bin/bash\n# Estimates fees based on ring size\n# Usage: ./fee_estimator.sh <ring_size>\necho \"Estimated fee: 0.0001 XMR\"\n")

with open(workspace / "reports/final/.gitkeep", "w") as f:
    f.write("")

print("Workspace generated successfully.")
print("Task file: /workspace/investigations/case_2024_001/txids_for_analysis.json")