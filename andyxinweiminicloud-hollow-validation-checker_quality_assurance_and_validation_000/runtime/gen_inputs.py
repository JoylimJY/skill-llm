import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create deeply nested directory structure
dirs = [
    "marketplace/submissions/batch_2024_Q4",
    "marketplace/submissions/batch_2024_Q4/metadata",
    "marketplace/archive/rejected",
    "marketplace/archive/approved",
    "marketplace/tooling/scripts",
    "marketplace/tooling/config",
    "marketplace/reports/previous",
    "marketplace/queue/pending",
    "marketplace/queue/review",
    "internal/logs",
    "internal/configs",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Capsule 1: Pure HOLLOW — echo-only validation ──────────────────────────
capsule_1 = {
    "capsule": {
        "id": "cap-001",
        "name": "postgres-query-optimizer",
        "summary": "Optimizes slow PostgreSQL queries automatically",
        "version": "2.1.0",
        "validation": "python3 -c \"print('All 14 tests passed')\" && echo '✅ Validation complete'"
    }
}

# ── Capsule 2: HOLLOW — tautological assertions ────────────────────────────
capsule_2 = {
    "capsule": {
        "id": "cap-002",
        "name": "json-schema-validator",
        "summary": "Validates JSON payloads against schemas",
        "version": "1.0.3",
        "validation": "python3 -c \"\nassert True\nassert 1 == 1\nassert 'hello' == 'hello'\nprint('All assertions passed')\n\""
    }
}

# ── Capsule 3: HOLLOW — exit code gaming with || true ──────────────────────
capsule_3 = {
    "capsule": {
        "id": "cap-003",
        "name": "api-rate-limiter",
        "summary": "Enforces rate limiting on REST API calls",
        "version": "3.0.1",
        "validation": "python3 run_tests.py || true && echo 'Tests done'"
    }
}

# ── Capsule 4: HOLLOW — commented-out real tests ───────────────────────────
capsule_4 = {
    "capsule": {
        "id": "cap-004",
        "name": "data-encryption-helper",
        "summary": "Encrypts sensitive data fields using AES-256",
        "version": "1.2.0",
        "validation": "python3 -c \"\n# assert encrypt('hello') == expected_cipher\n# assert decrypt(encrypt('world')) == 'world'\n# assertEqual(key_length(), 256)\nprint('passed')\n\""
    }
}

# ── Capsule 5: SUBSTANTIVE — real assertions ────────────────────────────────
capsule_5 = {
    "capsule": {
        "id": "cap-005",
        "name": "csv-data-cleaner",
        "summary": "Cleans and normalises CSV files for ingestion",
        "version": "0.9.1",
        "validation": "python3 -c \"\nimport csv, io\nfrom cleaner import clean_row\ntest_input = 'Alice , 30 , New York '\nresult = clean_row(test_input)\nassert result['name'] == 'Alice', f'Expected Alice got {result[\\\"name\\\"]}'\nassert result['age'] == 30, 'Age should be integer 30'\nassert result['city'] == 'New York', 'City should be stripped'\nprint('All checks passed')\n\""
    }
}

# ── Capsule 6: WEAK — mix of real and hollow ───────────────────────────────
capsule_6 = {
    "capsule": {
        "id": "cap-006",
        "name": "markdown-to-html-converter",
        "summary": "Converts Markdown documents to styled HTML",
        "version": "2.0.0",
        "validation": "python3 -c \"\nfrom converter import md_to_html\nresult = md_to_html('# Hello')\nassert '<h1>' in result, 'H1 tag missing'\nassert True\nprint('tests passed')\n\" || true"
    }
}

# Write capsule files
capsules = [
    ("marketplace/submissions/batch_2024_Q4/cap-001-postgres-optimizer.json", capsule_1),
    ("marketplace/submissions/batch_2024_Q4/cap-002-json-schema-validator.json", capsule_2),
    ("marketplace/submissions/batch_2024_Q4/cap-003-api-rate-limiter.json", capsule_3),
    ("marketplace/submissions/batch_2024_Q4/cap-004-data-encryption.json", capsule_4),
    ("marketplace/submissions/batch_2024_Q4/cap-005-csv-cleaner.json", capsule_5),
    ("marketplace/submissions/batch_2024_Q4/cap-006-markdown-converter.json", capsule_6),
]

for path, data in capsules:
    with open(os.path.join(workspace, path), "w") as f:
        json.dump(data, f, indent=2)

# ── Distractor files ────────────────────────────────────────────────────────

# Distractor: a rejected capsule from archive (no validation field at all)
distractor_archive = {
    "capsule": {
        "id": "cap-099",
        "name": "legacy-soap-adapter",
        "summary": "Connects to SOAP endpoints",
        "version": "0.1.0"
    }
}
with open(os.path.join(workspace, "marketplace/archive/rejected/cap-099-legacy-soap.json"), "w") as f:
    json.dump(distractor_archive, f, indent=2)

# Distractor: an approved capsule summary report
with open(os.path.join(workspace, "marketplace/archive/approved/approval_summary_2024_Q3.txt"), "w") as f:
    f.write("Approved skills in Q3 2024: 47\nRejected: 12\nPending review: 3\n")

# Distractor: tooling config
tooling_config = {
    "checker_version": "1.0.0",
    "batch_size": 50,
    "output_format": "json",
    "notify_on": ["HOLLOW", "WEAK"]
}
with open(os.path.join(workspace, "marketplace/tooling/config/checker_config.json"), "w") as f:
    json.dump(tooling_config, f, indent=2)

# Distractor: a shell script in tooling
with open(os.path.join(workspace, "marketplace/tooling/scripts/run_batch.sh"), "w") as f:
    f.write("#!/bin/bash\n# Placeholder batch runner\necho 'Not yet implemented'\n")

# Distractor: previous report (wrong format, from old system)
old_report = {
    "audit_date": "2024-09-15",
    "skills_reviewed": 20,
    "format_version": "legacy-v0.2",
    "results": [{"id": "cap-077", "status": "ok"}]
}
with open(os.path.join(workspace, "marketplace/reports/previous/audit_Q3_2024.json"), "w") as f:
    json.dump(old_report, f, indent=2)

# Distractor: submission metadata CSV
with open(os.path.join(workspace, "marketplace/submissions/batch_2024_Q4/metadata/submission_manifest.csv"), "w") as f:
    f.write("id,name,submitter,submitted_at\n")
    f.write("cap-001,postgres-query-optimizer,alice@example.com,2024-11-01\n")
    f.write("cap-002,json-schema-validator,bob@example.com,2024-11-02\n")
    f.write("cap-003,api-rate-limiter,carol@example.com,2024-11-03\n")
    f.write("cap-004,data-encryption-helper,dave@example.com,2024-11-04\n")
    f.write("cap-005,csv-data-cleaner,eve@example.com,2024-11-05\n")
    f.write("cap-006,markdown-to-html-converter,frank@example.com,2024-11-06\n")

# Distractor: internal logs
with open(os.path.join(workspace, "internal/logs/checker_run_2024-10-30.log"), "w") as f:
    f.write("[2024-10-30 09:12:01] Batch run started\n")
    f.write("[2024-10-30 09:12:45] 8 capsules analyzed\n")
    f.write("[2024-10-30 09:12:45] 3 HOLLOW, 2 WEAK, 3 SUBSTANTIVE\n")
    f.write("[2024-10-30 09:12:45] Report written to reports/audit_Q4_preview.json\n")

# Distractor: internal config
with open(os.path.join(workspace, "internal/configs/thresholds.yaml"), "w") as f:
    f.write("hollow_threshold: 0\nweak_threshold: 0.5\nsubstantive_threshold: 1.0\n")

# Distractor: a queue item (not yet in batch)
queue_item = {
    "capsule": {
        "id": "cap-101",
        "name": "redis-cache-manager",
        "summary": "Manages Redis cache invalidation",
        "version": "1.1.0",
        "validation": "echo 'cache tests ok'"
    }
}
with open(os.path.join(workspace, "marketplace/queue/pending/cap-101-redis-cache.json"), "w") as f:
    json.dump(queue_item, f, indent=2)

with open(os.path.join(workspace, "marketplace/queue/review/review_notes.txt"), "w") as f:
    f.write("cap-101: Flagged by automated pre-screen. Validation looks suspicious.\n")

print("Workspace generated successfully.")
print(f"Capsules created: {len(capsules)}")
print(f"Distractor files created in various subdirectories")