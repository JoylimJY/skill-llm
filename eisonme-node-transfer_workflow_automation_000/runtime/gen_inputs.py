import os
import random
import json
import hashlib
import struct

random.seed(42)

workspace = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────

dirs = [
    "node-transfer/scripts",
    "node-transfer/docs",
    "source_data/raw",
    "source_data/processed",
    "received",
    "logs",
    "configs",
    "archive/2023",
    "archive/2024",
    "pipeline/stages",
    "pipeline/outputs",
    "tmp",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────

distractor_files = {
    "configs/pipeline.yaml": (
        "pipeline:\n"
        "  name: genome-batch-pipeline\n"
        "  version: 2.1.0\n"
        "  nodes:\n"
        "    - id: processor-A\n"
        "      role: source\n"
        "    - id: processor-B\n"
        "      role: destination\n"
        "  transfer:\n"
        "    method: streaming\n"
        "    max_retries: 3\n"
    ),
    "configs/old_transfer.conf": (
        "[transfer]\n"
        "method=base64\n"
        "timeout=900\n"
        "chunk_size=4096\n"
        "deprecated=true\n"
    ),
    "logs/transfer_2024_01_15.log": (
        "[2024-01-15 09:23:11] INFO  Starting transfer pipeline\n"
        "[2024-01-15 09:23:12] WARN  Base64 encoding overhead detected\n"
        "[2024-01-15 09:45:33] ERROR OOM - process killed\n"
        "[2024-01-15 09:45:33] FATAL Transfer failed after 22 minutes\n"
    ),
    "logs/transfer_2024_03_01.log": (
        "[2024-03-01 14:10:00] INFO  node-transfer v1.0.0 initializing\n"
        "[2024-03-01 14:10:01] INFO  Sender ready on port 54891\n"
        "[2024-03-01 14:10:09] INFO  Transfer complete: 1.2GB in 8.4s\n"
    ),
    "pipeline/stages/stage1_extract.sh": (
        "#!/bin/bash\n"
        "# Stage 1: Data extraction\n"
        "set -euo pipefail\n"
        "INPUT_DIR=${1:-/data/raw}\n"
        "OUTPUT_DIR=${2:-/data/processed}\n"
        "echo 'Extracting genomic sequences...'\n"
        "find $INPUT_DIR -name '*.fastq.gz' | xargs -I{} cp {} $OUTPUT_DIR/\n"
    ),
    "pipeline/stages/stage2_align.sh": (
        "#!/bin/bash\n"
        "# Stage 2: Sequence alignment (placeholder)\n"
        "echo 'Alignment stage - requires BWA-MEM2'\n"
        "exit 0\n"
    ),
    "pipeline/outputs/manifest_template.json": json.dumps({
        "pipeline": "genome-batch",
        "version": "2.1.0",
        "status": "template",
        "files": []
    }, indent=2),
    "archive/2023/batch_summary.txt": (
        "Batch: 2023-Q4\n"
        "Files processed: 142\n"
        "Total size: 847 GB\n"
        "Transfer method: FTP (deprecated)\n"
        "Average transfer time: 18 min/GB\n"
    ),
    "archive/2024/batch_summary.txt": (
        "Batch: 2024-Q1\n"
        "Files processed: 198\n"
        "Total size: 1.2 TB\n"
        "Transfer method: node-transfer v1.0.0\n"
        "Average transfer time: 8 sec/GB\n"
    ),
    "source_data/raw/sample_index.tsv": (
        "sample_id\tfile\tsize_bytes\tchecksum\n"
        "SMPL001\tgenome_batch_001.bin\t52428800\tpending\n"
        "SMPL002\tgenome_batch_002.bin\t104857600\tpending\n"
        "SMPL003\tgenome_batch_003.bin\t209715200\tpending\n"
    ),
    "source_data/processed/quality_report.json": json.dumps({
        "run_id": "QC-2024-0301",
        "samples": 3,
        "passed": 3,
        "failed": 0,
        "notes": "Awaiting transfer to processing node"
    }, indent=2),
    "tmp/stale_lock.pid": "48291\n",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── Generate the source binary file (deterministic, ~50MB) ──────────────────
# Genomic data simulator: repeating structured binary blocks

SOURCE_FILE = os.path.join(workspace, "source_data", "genome_batch_001.bin")
FILE_SIZE = 50 * 1024 * 1024  # 50 MB exactly

rng = random.Random(0xDEADBEEF)

BLOCK_SIZE = 65536  # 64KB blocks
with open(SOURCE_FILE, "wb") as f:
    written = 0
    block_num = 0
    while written < FILE_SIZE:
        to_write = min(BLOCK_SIZE, FILE_SIZE - written)
        # Each block: 8-byte header (block number + magic) + pseudo-random body
        header = struct.pack(">II", block_num, 0xCAFEBABE)
        body_len = to_write - 8
        if body_len > 0:
            body = bytes(rng.randint(0, 255) for _ in range(body_len))
            f.write(header + body)
        else:
            f.write(header[:to_write])
        written += to_write
        block_num += 1

# Record source checksum for eval
source_md5 = hashlib.md5()
with open(SOURCE_FILE, "rb") as f:
    for chunk in iter(lambda: f.read(65536), b""):
        source_md5.update(chunk)

source_checksum = source_md5.hexdigest()
source_size = os.path.getsize(SOURCE_FILE)

# Write ground-truth metadata (for eval script only — NOT visible to agent as a hint)
gt = {
    "source_file": SOURCE_FILE,
    "source_size": source_size,
    "source_md5": source_checksum,
    "expected_dest": os.path.join(workspace, "received", "genome_batch_001.bin"),
    "expected_manifest": os.path.join(workspace, "transfer_manifest.json"),
}
with open(os.path.join(workspace, ".eval_ground_truth.json"), "w") as f:
    json.dump(gt, f, indent=2)

print(f"Source file created: {SOURCE_FILE}")
print(f"  Size: {source_size} bytes")
print(f"  MD5:  {source_checksum}")
print("Workspace scaffold complete.")