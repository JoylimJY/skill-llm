#!/usr/bin/env python3
"""
Generate the sandbox workspace for the clinical trial data ingestion task.
"""
import os
import json
import csv
import random

random.seed(42)

BASE = "/workspace"

# ── directory structure ────────────────────────────────────────────────────────
dirs = [
    "scripts",
    "data/raw",
    "data/processed",
    "data/archive",
    "reports",
    "config",
    "logs",
    "notebooks",
    "pipeline/etl",
    "pipeline/validation",
    "docs",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ── distractor files ───────────────────────────────────────────────────────────
distractors = {
    "config/db_config.yaml": "host: localhost\nport: 5432\ndb: trials\n",
    "config/pipeline.json": json.dumps({"version": "2.1", "retry": 3, "timeout": 30}),
    "logs/etl_run_2024_01.log": "2024-01-10 08:00:01 INFO Pipeline started\n2024-01-10 08:05:23 INFO 120 records processed\n2024-01-10 08:05:24 INFO Pipeline finished\n",
    "logs/validation_errors.log": "2024-01-10 08:05:01 WARN Missing score for participant P0034\n2024-01-10 08:05:02 WARN Duplicate entry for P0091\n",
    "data/archive/participants_2023.csv": "participant_id,name,score,site\nP0001,Alice Nguyen,88,SiteA\nP0002,Bob Chen,74,SiteB\n",
    "data/processed/cleaned_batch1.json": json.dumps([{"id": "P0001", "score": 88}, {"id": "P0002", "score": 74}]),
    "pipeline/etl/transform.py": "# ETL transform stub\ndef normalize(row):\n    return row\n",
    "pipeline/validation/schema_check.py": "# Schema validation stub\ndef validate(schema, row):\n    return True\n",
    "notebooks/exploratory_analysis.ipynb": json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    "docs/data_dictionary.md": "# Data Dictionary\n\n## participants\n- participant_id: string\n- name: string\n- score: numeric\n- visit: string\n- site: string\n",
    "reports/.gitkeep": "",
    "data/raw/.gitkeep": "",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(BASE, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── MAIN PROBLEM FILE: messy CSV with mixed types ─────────────────────────────
# The score column is intentionally messy:
#   - Some rows have integer-looking values (no quotes in CSV source)
#   - Some rows have string values
# When read by a naive script, the first row's score is "91" (string in CSV),
# but a naive agent might try to cast later rows differently.
#
# The key row that needs updating after ingestion is P0007 (wrong site "SiteX").
# The agent must read back records, find P0007's _id, and update site to "SiteC".

csv_rows = [
    # participant_id, name,               score, visit,    site
    ["P0011", "Clara Mendes",    "91",   "Visit1", "SiteA"],
    ["P0012", "David Park",      "78",   "Visit1", "SiteB"],
    ["P0013", "Eva Torres",      "85",   "Visit1", "SiteA"],
    ["P0014", "Frank Liu",       "66",   "Visit2", "SiteC"],
    ["P0015", "Grace Kim",       "93",   "Visit1", "SiteB"],
    ["P0016", "Henry Osei",      "71",   "Visit2", "SiteA"],
    ["P0017", "Irene Novak",     "88",   "Visit1", "SiteX"],  # ← wrong site, must be corrected to SiteC
    ["P0018", "James Adebayo",   "55",   "Visit2", "SiteB"],
    ["P0019", "Karen Johansson", "79",   "Visit1", "SiteA"],
    ["P0020", "Leon Braun",      "82",   "Visit2", "SiteC"],
]

csv_path = os.path.join(BASE, "data/raw/trial_participants_batch2.csv")
with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["participant_id", "name", "score", "visit", "site"])
    writer.writerows(csv_rows)

# ── lance-store scripts scaffold ──────────────────────────────────────────────
# The command.py script is provided by the skill; we create a realistic
# wrapper that delegates to the real lance store infrastructure.
# Per the skill docs: scripts/command.py already exists — we must not mock it.
# We write it here as the "already exists in workspace" artifact.

command_py = r'''#!/usr/bin/env python3
"""
Lance Store CLI — command.py
Provided by the lance-store skill (v1.0.12).
"""
import sys
import json
import uuid
import os
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import lance
    import pandas as pd
    import pyarrow as pa
except ImportError as e:
    print(json.dumps({"skill": "lance", "operation": "import", "status": "error",
                      "data": None, "error": str(e)}))
    sys.exit(1)

METADATA_FILE = Path(".lance_metadata.json")
DATASETS_ROOT = Path(".")


def load_meta():
    if METADATA_FILE.exists():
        with open(METADATA_FILE) as f:
            return json.load(f)
    return {}


def save_meta(meta):
    with open(METADATA_FILE, "w") as f:
        json.dump(meta, f, indent=2)


def resp(operation, status, data=None, error=None):
    print(json.dumps({
        "skill": "lance",
        "operation": operation,
        "status": status,
        "data": data,
        "error": error
    }, default=str))


def dataset_path(name):
    return DATASETS_ROOT / f"{name}.lance"


def get_field_types(name):
    dp = dataset_path(name)
    if not dp.exists():
        return {}
    try:
        ds = lance.dataset(str(dp))
        schema = ds.schema
        return {field.name: str(field.type) for field in schema}
    except Exception:
        return {}


def get_record_count(name):
    dp = dataset_path(name)
    if not dp.exists():
        return 0
    try:
        ds = lance.dataset(str(dp))
        return ds.count_rows()
    except Exception:
        return 0


def cmd_list_datasets():
    meta = load_meta()
    resp("list_datasets", "success", data=list(meta.keys()))


def cmd_list_datasets_info():
    meta = load_meta()
    result = []
    for name, info in meta.items():
        ft = get_field_types(name)
        rc = get_record_count(name)
        dp = dataset_path(name)
        result.append({
            "dataset_name": name,
            "path": str(dp.resolve()),
            "fields": info.get("fields", []),
            "field_types": ft,
            "record_count": rc,
            "columns": list(ft.keys()) if ft else info.get("fields", []),
            "last_updated": info.get("last_updated", ""),
        })
    resp("list_datasets_info", "success", data=result)


def cmd_create_dataset(name, fields):
    meta = load_meta()
    if name in meta:
        resp("create_dataset", "error", error=f"Dataset '{name}' already exists")
        return
    meta[name] = {
        "fields": fields,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    save_meta(meta)
    resp("create_dataset", "success", data={"name": name, "fields": fields})


def _infer_pa_type(val):
    if isinstance(val, bool):
        return pa.bool_()
    if isinstance(val, int):
        return pa.int64()
    if isinstance(val, float):
        return pa.float64()
    return pa.large_utf8()


def cmd_append(name, values):
    meta = load_meta()
    if name not in meta:
        resp("append_to_dataset", "error", error=f"Dataset '{name}' not found")
        return
    fields = meta[name]["fields"]
    if len(values) != len(fields):
        resp("append_to_dataset", "error",
             error=f"Expected {len(fields)} values, got {len(values)}")
        return
    record = dict(zip(fields, values))
    record["_id"] = str(uuid.uuid4())
    record["_updated_at"] = datetime.now(timezone.utc)

    dp = dataset_path(name)
    try:
        if dp.exists():
            existing = lance.dataset(str(dp))
            existing_schema = existing.schema
            # Validate types
            for field in existing_schema:
                fname = field.name
                if fname in ("_id", "_updated_at"):
                    continue
                if fname not in record:
                    continue
                expected = field.type
                val = record[fname]
                inferred = _infer_pa_type(val)
                if inferred != expected:
                    resp("append_to_dataset", "error",
                         error=f"`{fname}` should have type {expected} but type was {inferred}")
                    return
            arrays = []
            schema_fields = []
            for field in existing_schema:
                fname = field.name
                arrays.append(pa.array([record[fname]], type=field.type))
                schema_fields.append(field)
            table = pa.table({f.name: arr for f, arr in zip(schema_fields, arrays)},
                             schema=existing_schema)
            lance.write_dataset(table, str(dp), mode="append")
        else:
            schema_fields = []
            arrays = []
            for k, v in record.items():
                if k == "_updated_at":
                    t = pa.timestamp("us", tz="UTC")
                    arrays.append(pa.array([v], type=t))
                    schema_fields.append(pa.field(k, t))
                elif k == "_id":
                    arrays.append(pa.array([v], type=pa.large_utf8()))
                    schema_fields.append(pa.field(k, pa.large_utf8()))
                else:
                    inferred = _infer_pa_type(v)
                    arrays.append(pa.array([v], type=inferred))
                    schema_fields.append(pa.field(k, inferred))
            schema = pa.schema(schema_fields)
            table = pa.table({f.name: arr for f, arr in zip(schema_fields, arrays)},
                             schema=schema)
            lance.write_dataset(table, str(dp), mode="create")
        meta[name]["last_updated"] = datetime.now(timezone.utc).isoformat()
        save_meta(meta)
        resp("append_to_dataset", "success", data={"appended": record})
    except Exception as e:
        resp("append_to_dataset", "error", error=str(e))


def cmd_batch_append(name, json_array_str):
    meta = load_meta()
    if name not in meta:
        resp("batch_append_to_dataset", "error", error=f"Dataset '{name}' not found")
        return
    try:
        rows = json.loads(json_array_str)
    except json.JSONDecodeError as e:
        resp("batch_append_to_dataset", "error", error=f"Invalid JSON: {e}")
        return
    fields = meta[name]["fields"]
    dp = dataset_path(name)
    
    records = []
    for row in rows:
        if len(row) != len(fields):
            resp("batch_append_to_dataset", "error",
                 error=f"Row {row} has wrong number of values")
            return
        r = dict(zip(fields, row))
        r["_id"] = str(uuid.uuid4())
        r["_updated_at"] = datetime.now(timezone.utc)
        records.append(r)

    try:
        if dp.exists():
            existing = lance.dataset(str(dp))
            existing_schema = existing.schema
            # Validate types of first row against schema
            for field in existing_schema:
                fname = field.name
                if fname in ("_id", "_updated_at"):
                    continue
                val = records[0].get(fname)
                if val is None:
                    continue
                inferred = _infer_pa_type(val)
                if inferred != field.type:
                    resp("batch_append_to_dataset", "error",
                         error=f"`{fname}` should have type {field.type} but type was {inferred}")
                    return
            arrays = {f.name: [] for f in existing_schema}
            for r in records:
                for f in existing_schema:
                    arrays[f.name].append(r[f.name])
            pa_arrays = [pa.array(arrays[f.name], type=f.type) for f in existing_schema]
            table = pa.table({f.name: arr for f, arr in zip(existing_schema, pa_arrays)},
                             schema=existing_schema)
            lance.write_dataset(table, str(dp), mode="append")
        else:
            # infer schema from first record
            schema_fields = []
            for k, v in records[0].items():
                if k == "_updated_at":
                    schema_fields.append(pa.field(k, pa.timestamp("us", tz="UTC")))
                elif k == "_id":
                    schema_fields.append(pa.field(k, pa.large_utf8()))
                else:
                    schema_fields.append(pa.field(k, _infer_pa_type(v)))
            schema = pa.schema(schema_fields)
            col_data = {f.name: [r[f.name] for r in records] for f in schema}
            pa_arrays = [pa.array(col_data[f.name], type=f.type) for f in schema]
            table = pa.table({f.name: arr for f, arr in zip(schema, pa_arrays)},
                             schema=schema)
            lance.write_dataset(table, str(dp), mode="create")
        meta[name]["last_updated"] = datetime.now(timezone.utc).isoformat()
        save_meta(meta)
        resp("batch_append_to_dataset", "success",
             data={"appended_count": len(records)})
    except Exception as e:
        resp("batch_append_to_dataset", "error", error=str(e))


def cmd_read_dataset(name):
    meta = load_meta()
    if name not in meta:
        resp("read_dataset", "error", error=f"Dataset '{name}' not found")
        return
    dp = dataset_path(name)
    if not dp.exists():
        resp("read_dataset", "success", data=[])
        return
    try:
        ds = lance.dataset(str(dp))
        df = ds.to_table().to_pandas()
        # Convert timestamps to strings for JSON serialization
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].astype(str)
        records = df.to_dict(orient="records")
        resp("read_dataset", "success", data=records)
    except Exception as e:
        resp("read_dataset", "error", error=str(e))


def cmd_get_dataset_info(name):
    meta = load_meta()
    if name not in meta:
        resp("get_dataset_info", "error", error=f"Dataset '{name}' not found")
        return
    ft = get_field_types(name)
    rc = get_record_count(name)
    resp("get_dataset_info", "success", data={
        "dataset_name": name,
        "fields": meta[name].get("fields", []),
        "field_types": ft,
        "record_count": rc,
        "last_updated": meta[name].get("last_updated", ""),
    })


def cmd_update_record(name, record_id, values):
    meta = load_meta()
    if name not in meta:
        resp("update_dataset_record", "error", error=f"Dataset '{name}' not found")
        return
    fields = meta[name]["fields"]
    if len(values) != len(fields):
        resp("update_dataset_record", "error",
             error=f"Expected {len(fields)} values, got {len(values)}")
        return
    dp = dataset_path(name)
    if not dp.exists():
        resp("update_dataset_record", "error", error="Dataset has no data")
        return
    try:
        ds = lance.dataset(str(dp))
        df = ds.to_table().to_pandas()
        mask = df["_id"] == record_id
        if not mask.any():
            resp("update_dataset_record", "error",
                 error=f"Record '{record_id}' not found")
            return
        for field, val in zip(fields, values):
            df.loc[mask, field] = val
        df.loc[mask, "_updated_at"] = pd.Timestamp.now(tz="UTC")
        schema = ds.schema
        pa_table = pa.Table.from_pandas(df, schema=schema, preserve_index=False)
        lance.write_dataset(pa_table, str(dp), mode="overwrite")
        meta[name]["last_updated"] = datetime.now(timezone.utc).isoformat()
        save_meta(meta)
        resp("update_dataset_record", "success",
             data={"updated_id": record_id})
    except Exception as e:
        resp("update_dataset_record", "error", error=str(e))


def cmd_delete_record(name, record_id):
    meta = load_meta()
    if name not in meta:
        resp("delete_dataset_record", "error", error=f"Dataset '{name}' not found")
        return
    dp = dataset_path(name)
    if not dp.exists():
        resp("delete_dataset_record", "error", error="Dataset has no data")
        return
    try:
        ds = lance.dataset(str(dp))
        df = ds.to_table().to_pandas()
        before = len(df)
        df = df[df["_id"] != record_id]
        if len(df) == before:
            resp("delete_dataset_record", "error",
                 error=f"Record '{record_id}' not found")
            return
        schema = ds.schema
        pa_table = pa.Table.from_pandas(df, schema=schema, preserve_index=False)
        lance.write_dataset(pa_table, str(dp), mode="overwrite")
        meta[name]["last_updated"] = datetime.now(timezone.utc).isoformat()
        save_meta(meta)
        resp("delete_dataset_record", "success", data={"deleted_id": record_id})
    except Exception as e:
        resp("delete_dataset_record", "error", error=str(e))


def cmd_count_records(name):
    meta = load_meta()
    if name not in meta:
        resp("count_records", "error", error=f"Dataset '{name}' not found")
        return
    resp("count_records", "success", data={"count": get_record_count(name)})


def cmd_list_records(name, limit=None, offset=0):
    meta = load_meta()
    if name not in meta:
        resp("list_records", "error", error=f"Dataset '{name}' not found")
        return
    dp = dataset_path(name)
    if not dp.exists():
        resp("list_records", "success", data=[])
        return
    try:
        ds = lance.dataset(str(dp))
        df = ds.to_table().to_pandas()
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].astype(str)
        df = df.iloc[offset:]
        if limit is not None:
            df = df.iloc[:limit]
        resp("list_records", "success", data=df.to_dict(orient="records"))
    except Exception as e:
        resp("list_records", "error", error=str(e))


def cmd_get_record(name, record_id):
    meta = load_meta()
    if name not in meta:
        resp("get_record", "error", error=f"Dataset '{name}' not found")
        return
    dp = dataset_path(name)
    if not dp.exists():
        resp("get_record", "error", error="Dataset has no data")
        return
    try:
        ds = lance.dataset(str(dp))
        df = ds.to_table().to_pandas()
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].astype(str)
        row = df[df["_id"] == record_id]
        if row.empty:
            resp("get_record", "error", error=f"Record '{record_id}' not found")
            return
        resp("get_record", "success", data=row.to_dict(orient="records")[0])
    except Exception as e:
        resp("get_record", "error", error=str(e))


def cmd_drop_dataset(name):
    meta = load_meta()
    if name not in meta:
        resp("drop_dataset", "error", error=f"Dataset '{name}' not found")
        return
    import shutil
    dp = dataset_path(name)
    if dp.exists():
        shutil.rmtree(str(dp))
    del meta[name]
    save_meta(meta)
    resp("drop_dataset", "success", data={"dropped": name})


def cmd_backup_dataset(name, backup_path):
    import shutil
    dp = dataset_path(name)
    if not dp.exists():
        resp("backup_dataset", "error", error="Dataset has no data to backup")
        return
    shutil.copytree(str(dp), backup_path)
    resp("backup_dataset", "success", data={"backup_path": backup_path})


def cmd_get_dataset_path_info(name):
    meta = load_meta()
    if name not in meta:
        resp("get_dataset_path_info", "error", error=f"Dataset '{name}' not found")
        return
    dp = dataset_path(name)
    resp("get_dataset_path_info", "success", data={
        "name": name,
        "path": str(dp.resolve()),
        "exists": dp.exists()
    })


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: command.py <command> [args...]")
        sys.exit(1)

    cmd = args[0]

    if cmd == "list-datasets":
        cmd_list_datasets()
    elif cmd == "list-datasets-info":
        cmd_list_datasets_info()
    elif cmd == "create-dataset":
        if len(args) < 3:
            resp(cmd, "error", error="Usage: create-dataset <name> <field1> ...")
            return
        cmd_create_dataset(args[1], args[2:])
    elif cmd == "append-to-dataset":
        if len(args) < 3:
            resp(cmd, "error", error="Usage: append-to-dataset <name> <val1> ...")
            return
        cmd_append(args[1], args[2:])
    elif cmd == "batch-append-to-dataset":
        if len(args) != 3:
            resp(cmd, "error", error="Usage: batch-append-to-dataset <name> '<json>'")
            return
        cmd_batch_append(args[1], args[2])
    elif cmd == "read-dataset":
        if len(args) < 2:
            resp(cmd, "error", error="Usage: read-dataset <name>")
            return
        cmd_read_dataset(args[1])
    elif cmd == "get-dataset-info":
        if len(args) < 2:
            resp(cmd, "error", error="Usage: get-dataset-info <name>")
            return
        cmd_get_dataset_info(args[1])
    elif cmd == "update-dataset-record":
        if len(args) < 4:
            resp(cmd, "error", error="Usage: update-dataset-record <name> <id> <val1> ...")
            return
        cmd_update_record(args[1], args[2], args[3:])
    elif cmd == "delete-dataset-record":
        if len(args) < 3:
            resp(cmd, "error", error="Usage: delete-dataset-record <name> <id>")
            return
        cmd_delete_record(args[1], args[2])
    elif cmd == "count-records":
        if len(args) < 2:
            resp(cmd, "error", error="Usage: count-records <name>")
            return
        cmd_count_records(args[1])
    elif cmd == "list-records":
        name = args[1] if len(args) > 1 else None
        if not name:
            resp(cmd, "error", error="Usage: list-records <name> [--limit N] [--offset M]")
            return
        limit = None
        offset = 0
        i = 2
        while i < len(args):
            if args[i] == "--limit" and i + 1 < len(args):
                limit = int(args[i+1]); i += 2
            elif args[i] == "--offset" and i + 1 < len(args):
                offset = int(args[i+1]); i += 2
            else:
                i += 1
        cmd_list_records(name, limit, offset)
    elif cmd == "get-record":
        if len(args) < 3:
            resp(cmd, "error", error="Usage: get-record <name> <record_id>")
            return
        cmd_get_record(args[1], args[2])
    elif cmd == "drop-dataset":
        if len(args) < 2:
            resp(cmd, "error", error="Usage: drop-dataset <name>")
            return
        cmd_drop_dataset(args[1])
    elif cmd == "backup-dataset":
        if len(args) < 3:
            resp(cmd, "error", error="Usage: backup-dataset <name> <backup_path>")
            return
        cmd_backup_dataset(args[1], args[2])
    elif cmd == "get-dataset-path-info":
        if len(args) < 2:
            resp(cmd, "error", error="Usage: get-dataset-path-info <name>")
            return
        cmd_get_dataset_path_info(args[1])
    else:
        print(json.dumps({"skill": "lance", "operation": cmd, "status": "error",
                          "data": None, "error": f"Unknown command: {cmd}"}))


if __name__ == "__main__":
    main()
'''

scripts_dir = os.path.join(BASE, "scripts")
os.makedirs(scripts_dir, exist_ok=True)
with open(os.path.join(scripts_dir, "command.py"), "w") as f:
    f.write(command_py)

# ── pre-existing dataset: "trial_sites" ───────────────────────────────────────
# The agent should discover this via list-datasets-info.
# It has fields: site_code, region, capacity
# This tests whether the agent correctly initializes by checking existing datasets.

import subprocess, sys

os.chdir(BASE)

# Initialize the trial_sites dataset
subprocess.run([sys.executable, "scripts/command.py", "create-dataset",
                "trial_sites", "site_code", "region", "capacity"], check=True)
subprocess.run([sys.executable, "scripts/command.py", "batch-append-to-dataset",
                "trial_sites",
                '[["SiteA", "Northeast", "50"], ["SiteB", "Southeast", "40"], ["SiteC", "Midwest", "60"]]'],
               check=True)

print("Workspace generation complete.")
print(f"  - Messy CSV: {csv_path}")
print(f"  - Pre-existing dataset: trial_sites (3 records)")