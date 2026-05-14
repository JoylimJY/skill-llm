#!/bin/bash
set -e

echo "[setup] Making pipeline scripts executable..."
chmod +x /opt/skill-factory/scripts/pipeline.sh
chmod +x /opt/skill-factory/scripts/init_pipeline.py
chmod +x /opt/skill-factory/scripts/_run_stage.py

echo "[setup] Creating symlinks for convenient access..."
ln -sf /opt/skill-factory/scripts/pipeline.sh /usr/local/bin/pipeline.sh
ln -sf /opt/skill-factory/scripts/init_pipeline.py /usr/local/bin/init_pipeline.py

echo "[setup] Verifying workspace state..."
echo "--- /tmp/sf-csv-tool contents ---"
ls -la /tmp/sf-csv-tool/
echo ""
echo "--- .pipeline_state ---"
cat /tmp/sf-csv-tool/.pipeline_state
echo ""
echo "--- idea.md (first 5 lines) ---"
head -5 /tmp/sf-csv-tool/idea.md
echo ""

echo "[setup] Verifying no skill/ directory exists yet (builder not run)..."
if [ -d /tmp/sf-csv-tool/skill ]; then
    echo "[setup] WARNING: skill/ directory already exists - removing for clean test"
    rm -rf /tmp/sf-csv-tool/skill
fi

echo "[setup] Verifying no audit.md or pricing.md exists..."
rm -f /tmp/sf-csv-tool/audit.md /tmp/sf-csv-tool/pricing.md /tmp/sf-csv-tool/docs_review.md

echo "[setup] Setup complete. Pipeline ready."
echo ""
echo "Available commands:"
echo "  python3 /opt/skill-factory/scripts/init_pipeline.py <idea> --workspace <path>"
echo "  bash /opt/skill-factory/scripts/pipeline.sh --workspace <path> [--from <stage>] [--to <stage>]"
echo ""
echo "Stages: market | planner | arch | builder | auditor | docs | pricer"