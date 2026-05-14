import os
import random
import stat

random.seed(42)

workspace = os.environ.get("WORKSPACE", "/workspace")

# Create deeply nested directory structure
dirs = [
    "pipeline/src",
    "pipeline/src/loaders",
    "pipeline/src/transforms",
    "pipeline/src/validators",
    "pipeline/tests",
    "pipeline/config",
    "pipeline/logs",
    "pipeline/output",
    "pipeline/docs",
    "pipeline/archive/2023",
    "pipeline/archive/2024",
    "infra/scripts",
    "infra/docker",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Core Python source files the watcher should monitor ---
src_files = {
    "pipeline/src/loaders/csv_loader.py": '''\
import csv

def load_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))
''',
    "pipeline/src/transforms/normalizer.py": '''\
def normalize(records):
    return [{k: v.strip().lower() for k, v in r.items()} for r in records]
''',
    "pipeline/src/validators/schema_check.py": '''\
REQUIRED_FIELDS = ["id", "value", "timestamp"]

def validate(records):
    for r in records:
        for field in REQUIRED_FIELDS:
            if field not in r:
                raise ValueError(f"Missing field: {field}")
    return True
''',
    "pipeline/src/aggregate.py": '''\
import sys
import json
import os

DATA = [
    {"id": "1", "value": "10", "timestamp": "2024-01-01"},
    {"id": "2", "value": "20", "timestamp": "2024-01-02"},
    {"id": "3", "value": "30", "timestamp": "2024-01-03"},
]

total = sum(int(r["value"]) for r in DATA)
result = {"total": total, "count": len(DATA), "status": "ok"}

output_path = os.path.join(os.path.dirname(__file__), "..", "output", "report.json")
output_path = os.path.normpath(output_path)
with open(output_path, "w") as f:
    json.dump(result, f)

print(f"Aggregation complete: total={total}, count={len(DATA)}")
''',
}

for relpath, content in src_files.items():
    full = os.path.join(workspace, relpath)
    with open(full, "w") as f:
        f.write(content)

# --- Distractor files ---
distractor_files = {
    "pipeline/tests/test_loader.py": '# TODO: write loader tests\n',
    "pipeline/tests/test_normalizer.py": '# TODO: write normalizer tests\n',
    "pipeline/config/settings.yaml": 'env: production\ndebug: false\n',
    "pipeline/docs/README.txt": 'Pipeline documentation placeholder.\n',
    "pipeline/archive/2023/old_aggregate.py": '# deprecated\n',
    "pipeline/archive/2024/aggregate_v2.py": '# deprecated v2\n',
    "infra/scripts/deploy.sh": '#!/bin/bash\necho "deploy"\n',
    "infra/docker/Dockerfile.prod": 'FROM python:3.11\n',
    "pipeline/src/loaders/json_loader.py": '''\
import json

def load_json(path):
    with open(path) as f:
        return json.load(f)
''',
    "pipeline/src/transforms/deduplicator.py": '''\
def deduplicate(records):
    seen = set()
    out = []
    for r in records:
        key = r.get("id")
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out
''',
    "pipeline/config/logging.yaml": 'level: INFO\nformat: "%(asctime)s %(message)s"\n',
    "pipeline/output/.gitkeep": '',
    "pipeline/logs/.gitkeep": '',
}

for relpath, content in distractor_files.items():
    full = os.path.join(workspace, relpath)
    with open(full, "w") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Source files to watch: pipeline/src/ (all .py files)")
print(f"Aggregation script: pipeline/src/aggregate.py")
print(f"Expected output: pipeline/output/report.json")