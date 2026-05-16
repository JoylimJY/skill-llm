#!/usr/bin/env bash
set -e

WORKSPACE=/workspace

# Make tool stubs executable (they already "exist" per skill rules, we just ensure they're present as executable stubs)
mkdir -p "$WORKSPACE/tools/hk-stock-predictor"
mkdir -p "$WORKSPACE/tools/gougoubi-create-prediction"

cat > "$WORKSPACE/tools/hk-stock-predictor/run.sh" << 'EOF'
#!/usr/bin/env bash
# Stub: hk-stock-predictor
echo '{"predictionCandidates":[],"recommendedPrediction":null,"note":"stub - agent should use the analyst notes JSON"}'
EOF
chmod +x "$WORKSPACE/tools/hk-stock-predictor/run.sh"

cat > "$WORKSPACE/tools/gougoubi-create-prediction/run.sh" << 'EOF'
#!/usr/bin/env bash
# Stub: gougoubi-create-prediction
echo '{"ok":true,"txHash":"0xSTUB000","proposalAddress":"0xPROPSTUB"}'
EOF
chmod +x "$WORKSPACE/tools/gougoubi-create-prediction/run.sh"

echo "Setup complete. Stub tools ready."