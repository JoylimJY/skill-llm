#!/usr/bin/env python3
"""
Generate a realistic compliance-agent workspace that simulates the dr-context-pipeline
skill environment, but with intentional gaps/messiness the agent must navigate.
"""
import os
import json
import yaml
import random
import hashlib
from pathlib import Path
from datetime import datetime, timezone

random.seed(42)

WORKSPACE = Path("/workspace")

# ──────────────────────────────────────────────
# 1. Distractor directory tree (10+ files)
# ──────────────────────────────────────────────
distractor_dirs = [
    "logs/2024/q1",
    "logs/2024/q2",
    "reports/internal",
    "reports/external",
    "archive/legacy_policies",
    "tools/scripts",
    "config/env",
    "data/raw",
    "data/processed",
    "notebooks",
]
for d in distractor_dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

distractor_files = {
    "logs/2024/q1/audit_run_001.log": "INFO 2024-01-15 pipeline started\nINFO 2024-01-15 10 records processed\nWARN deprecated flag used\n",
    "logs/2024/q2/audit_run_042.log": "INFO 2024-04-03 pipeline started\nERROR memory watchdog timeout\n",
    "reports/internal/q1_summary.txt": "Q1 compliance checks: 142 passed, 3 flagged.\nSee audit_run_001 for details.\n",
    "reports/external/regulator_export.csv": "id,status,date\n1,ok,2024-01-20\n2,flagged,2024-02-11\n",
    "archive/legacy_policies/old_aml_policy_v1.md": "# AML Policy v1 (DEPRECATED)\nDo not use. Superseded by v3.\n",
    "archive/legacy_policies/sanctions_list_2021.txt": "Entity A\nEntity B\nEntity C\n",
    "tools/scripts/migrate_legacy.py": "# migration stub\nprint('legacy migration not implemented')\n",
    "config/env/dev.env": "LOG_LEVEL=DEBUG\nMEMORY_PATH=./memory\nMAX_SNIPPETS=5\n",
    "config/env/prod.env": "LOG_LEVEL=WARN\nMEMORY_PATH=/mnt/memory\nMAX_SNIPPETS=10\n",
    "data/raw/transactions_sample.jsonl": '{"id":"T001","amount":50000,"flag":false}\n{"id":"T002","amount":1200000,"flag":true}\n',
    "data/processed/transactions_clean.jsonl": '{"id":"T001","amount":50000,"risk":"low"}\n{"id":"T002","amount":1200000,"risk":"high"}\n',
    "notebooks/exploration.py": "# scratch exploration\nimport json\nprint('placeholder')\n",
}
for rel_path, content in distractor_files.items():
    p = WORKSPACE / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

# ──────────────────────────────────────────────
# 2. Memory foundation (dr-memory-foundation compatible)
# ──────────────────────────────────────────────
memory_dir = WORKSPACE / "memory"
topics_dir = memory_dir / "topics"
topics_dir.mkdir(parents=True, exist_ok=True)

# always_on.md — policy header + topic catalog
always_on_content = """# Always-On Policy Header
version: 3.1
effective_date: 2024-03-01
jurisdiction: EU/US

## Invariants
- All agent outputs must be auditable.
- No PII in context packs.
- Cite sources as snippet IDs only.

## Topic Catalog
- aml: Anti-Money Laundering procedures and thresholds
- sanctions: Sanctions screening rules and list maintenance
- kyc: Know-Your-Customer onboarding requirements
- reporting: Regulatory reporting timelines and formats
- data_retention: Data retention schedules and deletion policies
"""
(memory_dir / "always_on.md").write_text(always_on_content)

# Topic files with realistic compliance content
topic_files = {
    "aml.md": """# Anti-Money Laundering (AML)
## Snippet: transaction_threshold
Large cash transactions above $10,000 must be reported via CTR within 15 days. Structuring to avoid this threshold is itself an offense.

## Snippet: suspicious_activity
SAR filings are required within 30 calendar days of detecting suspicious activity. Extended to 60 days when law enforcement is involved.

## Snippet: aml_training
All front-office staff must complete annual AML training. Records must be retained for 5 years.
""",
    "sanctions.md": """# Sanctions Screening
## Snippet: ofac_primary
All counterparties must be screened against the OFAC SDN list before any transaction. Blocked transactions must be reported within 10 business days.

## Snippet: list_refresh
Sanctions lists must be refreshed at minimum every 24 hours. Any gap in refresh longer than 48 hours requires incident reporting.

## Snippet: false_positive_handling
False positive matches must be documented with analyst sign-off within 3 business days. Documentation is retained for 7 years.
""",
    "kyc.md": """# Know Your Customer (KYC)
## Snippet: onboarding_docs
Required onboarding documents: government-issued ID, proof of address (< 90 days old), source-of-funds declaration for accounts over $50,000.

## Snippet: enhanced_due_diligence
Politically Exposed Persons (PEPs) and high-risk jurisdictions require Enhanced Due Diligence (EDD): senior management approval + annual review.

## Snippet: kyc_refresh
Standard KYC refresh cycle is 3 years for low-risk, 1 year for medium-risk, and 6 months for high-risk customers.
""",
    "reporting.md": """# Regulatory Reporting
## Snippet: ctr_filing
Currency Transaction Reports (CTR) must be filed electronically via FinCEN BSA E-Filing. Deadline: 15 calendar days after the transaction date.

## Snippet: sar_filing
Suspicious Activity Reports (SAR) filed with FinCEN. Confidentiality must be maintained; do not tip-off the subject.

## Snippet: mifid_reporting
MiFID II trade reports must be submitted by T+1. Late submissions incur escalating penalties starting at €5,000/day.
""",
    "data_retention.md": """# Data Retention
## Snippet: transaction_records
All transaction records must be retained for a minimum of 5 years from the transaction date (7 years for flagged/SAR-related records).

## Snippet: kyc_records
KYC documentation must be retained for 5 years after the end of the customer relationship.

## Snippet: deletion_policy
Upon reaching retention limits, records must be securely deleted and a deletion certificate issued within 30 days.
""",
}
for fname, content in topic_files.items():
    (topics_dir / fname).write_text(content)

# ──────────────────────────────────────────────
# 3. Pipeline reference files (skills structure)
# ──────────────────────────────────────────────
skills_dir = WORKSPACE / "skills" / "dr-context-pipeline"
refs_dir = skills_dir / "references"
schemas_dir = refs_dir / "schemas"
tests_dir = refs_dir / "tests"
scripts_dir = skills_dir / "scripts"
assets_dir = skills_dir / "assets" / "context_pipeline"

for d in [refs_dir, schemas_dir, tests_dir, scripts_dir, assets_dir]:
    d.mkdir(parents=True, exist_ok=True)

# router.yml — deterministic routing table
router_content = {
    "version": "1.2",
    "routes": [
        {
            "task_type": "transaction_review",
            "keywords": ["transaction", "transfer", "wire", "payment", "CTR", "cash"],
            "caps": ["aml", "reporting"],
            "max_snippets": 4,
        },
        {
            "task_type": "sanctions_check",
            "keywords": ["sanctions", "OFAC", "SDN", "blocked", "screening"],
            "caps": ["sanctions"],
            "max_snippets": 3,
        },
        {
            "task_type": "customer_onboarding",
            "keywords": ["onboarding", "KYC", "customer", "PEP", "due diligence", "account"],
            "caps": ["kyc", "aml"],
            "max_snippets": 4,
        },
        {
            "task_type": "regulatory_filing",
            "keywords": ["filing", "report", "SAR", "MiFID", "FinCEN", "deadline"],
            "caps": ["reporting", "aml"],
            "max_snippets": 4,
        },
        {
            "task_type": "data_governance",
            "keywords": ["retention", "deletion", "archive", "purge", "GDPR"],
            "caps": ["data_retention"],
            "max_snippets": 3,
        },
        {
            "task_type": "general",
            "keywords": [],
            "caps": ["aml", "sanctions", "kyc", "reporting", "data_retention"],
            "max_snippets": 3,
        },
    ],
}
(refs_dir / "router.yml").write_text(yaml.dump(router_content, default_flow_style=False))

# retrieval_bundle.schema.json
retrieval_bundle_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "RetrievalBundle",
    "type": "object",
    "required": ["query", "task_type", "caps", "snippets", "timestamp"],
    "properties": {
        "query": {"type": "string", "minLength": 1},
        "task_type": {"type": "string"},
        "caps": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "snippets": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["id", "source_file", "snippet_key", "text"],
                "properties": {
                    "id": {
                        "type": "string",
                        "pattern": "^S[0-9]+$",
                        "description": "Stable sequential ID: S1, S2, S3 etc., assigned by deterministic ordering (source_file asc, then snippet_key asc)."
                    },
                    "source_file": {"type": "string"},
                    "snippet_key": {"type": "string"},
                    "text": {"type": "string", "minLength": 10},
                },
                "additionalProperties": False,
            },
        },
        "timestamp": {"type": "string", "format": "date-time"},
    },
    "additionalProperties": False,
}
(schemas_dir / "retrieval_bundle.schema.json").write_text(
    json.dumps(retrieval_bundle_schema, indent=2)
)

# context_pack.schema.json
context_pack_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "ContextPack",
    "type": "object",
    "required": ["query", "task_type", "summary", "sources", "token_estimate", "lint_passed", "timestamp"],
    "properties": {
        "query": {"type": "string", "minLength": 1},
        "task_type": {"type": "string"},
        "summary": {"type": "string", "minLength": 20},
        "sources": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "string",
                "pattern": "^S[0-9]+$",
                "description": "MUST be snippet IDs only (S1, S2, …). NOT filenames, topic names, or free text."
            },
        },
        "token_estimate": {"type": "integer", "minimum": 1},
        "lint_passed": {"type": "boolean"},
        "fallback_to_raw": {"type": "boolean"},
        "timestamp": {"type": "string", "format": "date-time"},
    },
    "additionalProperties": False,
}
(schemas_dir / "context_pack.schema.json").write_text(
    json.dumps(context_pack_schema, indent=2)
)

# deterministic_ids.md
deterministic_ids_content = """# Deterministic Snippet ID Assignment

To ensure stable, reproducible IDs across runs:

1. Collect all candidate snippets from the retrieved topic files.
2. Sort them **first by `source_file` (ascending, lexicographic)**, then by **`snippet_key` (ascending, lexicographic)** within the same file.
3. Assign IDs sequentially: the first snippet after sorting gets `S1`, the second gets `S2`, and so on.
4. IDs must never be re-used within a single Retrieval Bundle.

Example: if retrieving from `aml.md` (snippets: `suspicious_activity`, `transaction_threshold`) and `reporting.md` (snippet: `ctr_filing`), the sorted order is:
- aml.md / suspicious_activity → S1
- aml.md / transaction_threshold → S2
- reporting.md / ctr_filing → S3
"""
(refs_dir / "deterministic_ids.md").write_text(deterministic_ids_content)

# compressor_prompt.txt
compressor_content = """# Compressor Prompt

You are a compression agent. Given a Retrieval Bundle JSON, produce a Context Pack JSON.

Rules:
1. Write a concise `summary` (3-5 sentences) covering the key facts from ALL retrieved snippets.
2. The `sources` array MUST contain ONLY the snippet IDs (e.g., "S1", "S2") — never filenames, paths, or topic names.
3. Estimate `token_estimate` as approximately len(summary.split()) * 1.3 rounded to nearest integer.
4. Set `lint_passed` to true if all sources are valid snippet IDs from the bundle.
5. If any source is not a valid snippet ID, set `lint_passed` to false and set `fallback_to_raw` to true.
6. Copy `query`, `task_type`, and `timestamp` from the Retrieval Bundle.
"""
(refs_dir / "compressor_prompt.txt").write_text(compressor_content)

# RUNTIME_CHECKLIST.md
checklist_content = """# Runtime Evidence Checklist

For EVERY task execution, the agent MUST:

- [ ] Load `memory/always_on.md` policy header.
- [ ] Route the user message using `references/router.yml` → determine `task_type` and `caps`.
- [ ] Retrieve top snippets from topic files matching the `caps`.
- [ ] Emit a **Retrieval Bundle JSON** that validates against `references/schemas/retrieval_bundle.schema.json`.
- [ ] Compress the bundle → emit a **Context Pack JSON** that validates against `references/schemas/context_pack.schema.json`.
  - `sources` MUST be snippet IDs only (`S1`, `S2`, …).
- [ ] Lint the Context Pack. If lint fails, set `fallback_to_raw: true`.
- [ ] State which snippet IDs are being passed forward.
- [ ] Provide the final user-facing answer.

If any step fails: reply `NOT EXECUTED: <reason>` and stop.
"""
(refs_dir / "RUNTIME_CHECKLIST.md").write_text(checklist_content)

# golden.json — regression tests
golden_tests = {
    "version": "1.0",
    "tests": [
        {
            "id": "golden_001",
            "query": "What are the CTR filing requirements for large cash transactions?",
            "expected_task_type": "transaction_review",
            "expected_caps": ["aml", "reporting"],
            "expected_snippet_ids_include": ["S1"],
        },
        {
            "id": "golden_002",
            "query": "How often must sanctions lists be refreshed?",
            "expected_task_type": "sanctions_check",
            "expected_caps": ["sanctions"],
            "expected_snippet_ids_include": ["S1"],
        },
    ],
}
(tests_dir / "golden.json").write_text(json.dumps(golden_tests, indent=2))

# ──────────────────────────────────────────────
# 4. Pipeline scripts (stub — agent must NOT modify these,
#    they are provided as-is per SKILL.md: "scripts already exist")
# ──────────────────────────────────────────────

install_pipeline_script = '''#!/usr/bin/env python3
"""install_pipeline.py — copies assets into target directory."""
import argparse, shutil, hashlib
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    args = parser.parse_args()

    src = Path(__file__).parent.parent / "assets" / "context_pipeline"
    dst = Path(args.target)
    dst.mkdir(parents=True, exist_ok=True)

    count = 0
    hashes = []
    for f in sorted(src.rglob("*")):
        if f.is_file():
            rel = f.relative_to(src)
            out = dst / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, out)
            h = hashlib.md5(f.read_bytes()).hexdigest()
            hashes.append(f"{rel}: {h}")
            count += 1

    print(f"install_pipeline: {count} file(s) installed to {dst}")
    for h in hashes:
        print(f"  {h}")

if __name__ == "__main__":
    main()
'''
(scripts_dir / "install_pipeline.py").write_text(install_pipeline_script)

validate_pipeline_script = '''#!/usr/bin/env python3
"""validate_pipeline.py — checks required files exist and schemas are valid JSON."""
import argparse, json, sys
from pathlib import Path

REQUIRED = [
    "schemas/retrieval_bundle.schema.json",
    "schemas/context_pack.schema.json",
    "router.yml",
    "compressor_prompt.txt",
    "RUNTIME_CHECKLIST.md",
    "deterministic_ids.md",
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context-root", required=True)
    args = parser.parse_args()

    root = Path(args.context_root)
    # The installed context_pipeline mirrors the skills references directory
    ref_root = root / "references"

    failures = []
    for rel in REQUIRED:
        p = ref_root / rel
        if not p.exists():
            failures.append(f"MISSING: {p}")
        elif rel.endswith(".json"):
            try:
                json.loads(p.read_text())
            except Exception as e:
                failures.append(f"INVALID JSON: {p} — {e}")

    if failures:
        print("FAIL")
        for f in failures:
            print(f"  {f}")
        sys.exit(1)
    else:
        print("PASS — all required pipeline files present and valid")

if __name__ == "__main__":
    main()
'''
(scripts_dir / "validate_pipeline.py").write_text(validate_pipeline_script)

watchdog_script = '''#!/usr/bin/env python3
"""memory_watchdog.py — checks memory files for freshness and minimum size."""
import argparse, json, os, sys
from pathlib import Path
from datetime import datetime, timezone

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--freshness-minutes", type=int, default=240)
    parser.add_argument("--min-bytes", type=int, default=200)
    parser.add_argument("--memory-path", default="memory")
    args = parser.parse_args()

    memory_path = Path(args.memory_path)
    issues = []
    checked = []

    always_on = memory_path / "always_on.md"
    if not always_on.exists():
        issues.append("always_on.md missing")
    else:
        size = always_on.stat().st_size
        mtime = datetime.fromtimestamp(always_on.stat().st_mtime, tz=timezone.utc)
        age_min = (datetime.now(tz=timezone.utc) - mtime).total_seconds() / 60
        checked.append(str(always_on))
        if size < args.min_bytes:
            issues.append(f"always_on.md too small: {size} < {args.min_bytes} bytes")

    topics = list((memory_path / "topics").glob("*.md")) if (memory_path / "topics").exists() else []
    if not topics:
        issues.append("no topic files found under memory/topics/")
    for t in topics:
        size = t.stat().st_size
        if size < args.min_bytes:
            issues.append(f"{t.name} too small: {size} < {args.min_bytes} bytes")
        checked.append(str(t))

    result = {
        "status": "OK" if not issues else "FAIL",
        "checked": checked,
        "issues": issues,
        "freshness_minutes": args.freshness_minutes,
        "min_bytes": args.min_bytes,
    }
    print(json.dumps(result, indent=2))
    if issues:
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
(scripts_dir / "memory_watchdog.py").write_text(watchdog_script)

# ──────────────────────────────────────────────
# 5. Assets directory — what install_pipeline.py copies
# ──────────────────────────────────────────────
asset_refs_dir = assets_dir / "references"
asset_schemas_dir = asset_refs_dir / "schemas"
asset_tests_dir = asset_refs_dir / "tests"
for d in [asset_refs_dir, asset_schemas_dir, asset_tests_dir]:
    d.mkdir(parents=True, exist_ok=True)

# Copy schema files into assets too (so install_pipeline works)
import shutil
for fname in ["retrieval_bundle.schema.json", "context_pack.schema.json"]:
    shutil.copy2(schemas_dir / fname, asset_schemas_dir / fname)
for fname in ["router.yml", "compressor_prompt.txt", "RUNTIME_CHECKLIST.md", "deterministic_ids.md"]:
    shutil.copy2(refs_dir / fname, asset_refs_dir / fname)
shutil.copy2(tests_dir / "golden.json", asset_tests_dir / "golden.json")

# ──────────────────────────────────────────────
# 6. AGENTS.md — pre-existing stub (agent must patch it)
# ──────────────────────────────────────────────
agents_md_content = """# AGENTS.md
## General Guidelines
- Always be helpful and concise.
- Follow compliance protocols.

## Tools Available
- Memory retrieval pipeline (see context_pipeline/ for configuration)
- Transaction screening module
- Regulatory calendar

## Known Limitations
- No access to live OFAC feeds; use cached lists only.
"""
(WORKSPACE / "AGENTS.md").write_text(agents_md_content)

# ──────────────────────────────────────────────
# 7. The task input: a compliance query batch
# ──────────────────────────────────────────────
# This is the "messy input" the agent must process.
# It's a plaintext file with 2 queries — messy, no structure hinted.
compliance_queries = """COMPLIANCE QUERY BATCH — Q2 2024
Submitted by: Risk Operations Team
Date: 2024-06-10

--- QUERY 1 ---
Our back-office team flagged a wire transfer of $1,350,000 from a new corporate client.
We need to know what AML thresholds apply, what filings are required, and the exact deadlines.
Please produce the full memory context record for this query so we can attach it to the audit trail.

--- QUERY 2 ---
We are onboarding a new customer identified as a Politically Exposed Person (PEP)
domiciled in a high-risk jurisdiction. What are the enhanced due diligence requirements,
and how frequently must their KYC be refreshed? Again, we need the full memory context record.

END OF BATCH
"""
(WORKSPACE / "data" / "raw" / "compliance_query_batch.txt").write_text(compliance_queries)

# ──────────────────────────────────────────────
# 8. git init (required for git-based steps)
# ──────────────────────────────────────────────
import subprocess
subprocess.run(["git", "init"], cwd=WORKSPACE, capture_output=True)
subprocess.run(["git", "config", "user.email", "test@benchmark.local"], cwd=WORKSPACE, capture_output=True)
subprocess.run(["git", "config", "user.name", "Benchmark"], cwd=WORKSPACE, capture_output=True)
subprocess.run(["git", "add", "-A"], cwd=WORKSPACE, capture_output=True)
subprocess.run(
    ["git", "commit", "-m", "initial workspace setup"],
    cwd=WORKSPACE,
    capture_output=True,
)

print("Workspace generation complete.")
print(f"Files created under {WORKSPACE}")