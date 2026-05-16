import os
import random
import stat

random.seed(42)

workspace = os.environ.get("WORKSPACE", "/workspace")
os.makedirs(workspace, exist_ok=True)

# --- Create the bundle skill scripts directory structure ---
scripts_dir = os.path.join(workspace, "scripts")
os.makedirs(scripts_dir, exist_ok=True)

# Write the actual script.sh implementing the bundle skill
script_content = r"""#!/usr/bin/env bash
set -euo pipefail

STORE="$HOME/.local/share/bundle"
mkdir -p "$STORE"

CMD="${1:-}"
shift || true

case "$CMD" in
  create)
    DIR="${1:-}"
    OUTPUT="${2:-}"
    if [[ -z "$DIR" || -z "$OUTPUT" ]]; then
      echo "Usage: script.sh create <dir> <output>" >&2
      exit 1
    fi
    if [[ ! -d "$DIR" ]]; then
      echo "Error: '$DIR' is not a directory" >&2
      exit 1
    fi
    mkdir -p "$(dirname "$OUTPUT")"
    BUNDLE_NAME="$(basename "$OUTPUT")"
    BUNDLE_PATH="${OUTPUT}.bundle.tar.gz"
    MANIFEST_FILE="$STORE/${BUNDLE_NAME}.manifest"

    # Build manifest
    find "$DIR" -type f | sort | while read -r f; do
      REL="${f#$DIR/}"
      SUM="$(sha256sum "$f" | awk '{print $1}')"
      echo "$REL $SUM"
    done > "$MANIFEST_FILE"

    # Pack
    tar -czf "$BUNDLE_PATH" -C "$(dirname "$DIR")" "$(basename "$DIR")" 2>/dev/null
    
    # Append manifest checksum into bundle metadata
    META_CHECKSUM="$(sha256sum "$MANIFEST_FILE" | awk '{print $1}')"
    echo "$META_CHECKSUM" > "$STORE/${BUNDLE_NAME}.meta"

    echo "Bundle created: $BUNDLE_PATH"
    echo "Manifest: $MANIFEST_FILE"
    ;;

  manifest)
    DIR="${1:-}"
    if [[ -z "$DIR" || ! -d "$DIR" ]]; then
      echo "Error: '$DIR' is not a directory" >&2
      exit 1
    fi
    find "$DIR" -type f | sort | while read -r f; do
      REL="${f#$DIR/}"
      SUM="$(sha256sum "$f" | awk '{print $1}')"
      echo "$REL $SUM"
    done
    ;;

  verify)
    BUNDLE="${1:-}"
    if [[ -z "$BUNDLE" ]]; then
      echo "Usage: script.sh verify <bundle>" >&2
      exit 1
    fi
    # Accept with or without .bundle.tar.gz suffix
    if [[ "$BUNDLE" != *.bundle.tar.gz ]]; then
      BUNDLE="${BUNDLE}.bundle.tar.gz"
    fi
    if [[ ! -f "$BUNDLE" ]]; then
      echo "Error: bundle '$BUNDLE' not found" >&2
      exit 1
    fi
    BUNDLE_NAME="$(basename "$BUNDLE" .bundle.tar.gz)"
    MANIFEST_FILE="$STORE/${BUNDLE_NAME}.manifest"
    META_FILE="$STORE/${BUNDLE_NAME}.meta"
    if [[ ! -f "$MANIFEST_FILE" ]]; then
      echo "FAIL: manifest not found for bundle '$BUNDLE_NAME'" >&2
      exit 1
    fi
    EXPECTED="$(cat "$META_FILE")"
    ACTUAL="$(sha256sum "$MANIFEST_FILE" | awk '{print $1}')"
    if [[ "$EXPECTED" == "$ACTUAL" ]]; then
      echo "OK: bundle integrity verified"
    else
      echo "FAIL: manifest checksum mismatch"
      exit 1
    fi
    ;;

  size)
    DIR="${1:-}"
    if [[ -z "$DIR" || ! -d "$DIR" ]]; then
      echo "Error: '$DIR' is not a directory" >&2
      exit 1
    fi
    du -sh "$DIR" | awk '{print $1}'
    ;;

  list)
    BUNDLE="${1:-}"
    if [[ "$BUNDLE" != *.bundle.tar.gz ]]; then
      BUNDLE="${BUNDLE}.bundle.tar.gz"
    fi
    if [[ ! -f "$BUNDLE" ]]; then
      echo "Error: bundle '$BUNDLE' not found" >&2
      exit 1
    fi
    tar -tzf "$BUNDLE"
    ;;

  extract)
    BUNDLE="${1:-}"
    DEST="${2:-}"
    if [[ -z "$BUNDLE" || -z "$DEST" ]]; then
      echo "Usage: script.sh extract <bundle> <dir>" >&2
      exit 1
    fi
    if [[ "$BUNDLE" != *.bundle.tar.gz ]]; then
      BUNDLE="${BUNDLE}.bundle.tar.gz"
    fi
    if [[ ! -f "$BUNDLE" ]]; then
      echo "Error: bundle '$BUNDLE' not found" >&2
      exit 1
    fi
    mkdir -p "$DEST"
    tar -xzf "$BUNDLE" -C "$DEST"
    echo "Extracted to: $DEST"
    ;;

  *)
    echo "Unknown command: $CMD" >&2
    echo "Commands: create, manifest, verify, size, list, extract" >&2
    exit 1
    ;;
esac
"""

script_path = os.path.join(scripts_dir, "script.sh")
with open(script_path, "w") as f:
    f.write(script_content)
os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# --- Create a realistic bioinformatics pipeline source directory ---
pipeline_dir = os.path.join(workspace, "genomics_pipeline_v2")
subdirs = [
    "bin",
    "lib/parsers",
    "lib/utils",
    "config",
    "data/reference",
    "data/samples",
    "tests/unit",
    "tests/integration",
    "docs",
]
for sd in subdirs:
    os.makedirs(os.path.join(pipeline_dir, sd), exist_ok=True)

files = {
    "bin/align.sh": "#!/bin/bash\n# Align reads to reference genome\nbwa mem $REF $READS | samtools sort -o aligned.bam\n",
    "bin/call_variants.sh": "#!/bin/bash\n# Call variants using GATK\ngatk HaplotypeCaller -R $REF -I $BAM -O variants.vcf\n",
    "bin/qc_check.py": "#!/usr/bin/env python3\nimport sys\n\ndef check_quality(fastq):\n    # placeholder QC logic\n    return True\n\nif __name__ == '__main__':\n    print(check_quality(sys.argv[1]))\n",
    "lib/parsers/vcf_parser.py": "# VCF parser module\ndef parse_vcf(path):\n    with open(path) as f:\n        return [l for l in f if not l.startswith('#')]\n",
    "lib/parsers/fastq_parser.py": "# FASTQ parser\ndef read_fastq(path):\n    records = []\n    with open(path) as f:\n        while True:\n            header = f.readline().strip()\n            if not header: break\n            seq = f.readline().strip()\n            plus = f.readline().strip()\n            qual = f.readline().strip()\n            records.append((header, seq, qual))\n    return records\n",
    "lib/utils/logger.py": "import logging\nlogging.basicConfig(level=logging.INFO)\nlogger = logging.getLogger('pipeline')\n",
    "lib/utils/file_utils.py": "import os\ndef ensure_dir(d):\n    os.makedirs(d, exist_ok=True)\n",
    "config/pipeline.yaml": "pipeline:\n  name: genomics_v2\n  version: 2.3.1\n  reference: hg38\n  threads: 8\n  quality_threshold: 30\n",
    "config/samples.tsv": "sample_id\tpath\ttype\nSAMPLE001\t/data/samples/s001.fastq\ttumor\nSAMPLE002\t/data/samples/s002.fastq\tnormal\n",
    "data/reference/hg38.fa.fai": ">chr1\t248956422\n>chr2\t242193529\n>chrX\t156040895\n",
    "data/samples/sample_manifest.csv": "sample_id,batch,qc_pass\nSAMPLE001,batch_01,true\nSAMPLE002,batch_01,true\nSAMPLE003,batch_02,false\n",
    "tests/unit/test_parsers.py": "import pytest\nfrom lib.parsers.vcf_parser import parse_vcf\n\ndef test_parse_empty():\n    assert parse_vcf('/dev/null') == []\n",
    "tests/integration/test_pipeline.py": "# Integration tests for full pipeline run\ndef test_full_run():\n    # placeholder\n    pass\n",
    "docs/usage.md": "# Genomics Pipeline v2\n\n## Usage\nRun bin/align.sh with appropriate parameters.\n\n## Requirements\n- BWA 0.7+\n- GATK 4.0+\n- Python 3.8+\n",
}

for rel_path, content in files.items():
    abs_path = os.path.join(pipeline_dir, rel_path)
    with open(abs_path, "w") as f:
        f.write(content)

# --- Create distractor files in workspace root ---
distractor_files = {
    "old_pipeline_v1.tar.gz.bak": "binary backup - do not use",
    "scratch_notes.txt": "TODO: remember to update config before release\n- check threads param\n- validate sample paths\n",
    "temp_bundle_attempt.txt": "failed attempt log\nerror: wrong arguments\n",
    "archive/deprecated_align.sh": "#!/bin/bash\n# OLD VERSION - DEPRECATED\nbwa aln $REF $READS > aligned.sai\n",
    "archive/old_config.yaml": "pipeline:\n  version: 1.0.0\n  reference: hg19\n",
    "logs/build_20240101.log": "[2024-01-01] Build failed: missing manifest\n[2024-01-01] Retry...\n",
    "logs/build_20240102.log": "[2024-01-02] Build succeeded\n",
    ".hidden_cache/tmp_manifest": "corrupt data\n\x00\x01\x02",
}

for rel_path, content in distractor_files.items():
    abs_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", errors="replace") as f:
        f.write(content)

# --- Create a staging directory (empty, for extraction destination) ---
staging_dir = os.path.join(workspace, "staging")
os.makedirs(staging_dir, exist_ok=True)

print(f"Workspace prepared at: {workspace}")
print(f"Pipeline source dir: {pipeline_dir}")
print(f"Staging dir: {staging_dir}")
print(f"Script: {script_path}")