#!/bin/bash
set -e

echo "[setup] Workspace ready."
ls /workspace/

echo "[setup] Verifying raw data exports exist..."
for f in \
    /workspace/media_ops/raw_exports/meta/meta_raw_export_wk27.csv \
    /workspace/media_ops/raw_exports/google/google_raw_export_wk27.csv \
    /workspace/media_ops/raw_exports/amazon/amazon_raw_export_wk27.csv \
    /workspace/weekly_brief_request.txt; do
    if [ -f "$f" ]; then
        echo "  [OK] $f"
    else
        echo "  [MISSING] $f"
    fi
done

echo "[setup] Done."