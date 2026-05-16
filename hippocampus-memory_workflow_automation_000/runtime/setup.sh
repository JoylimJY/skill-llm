#!/usr/bin/env bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

# Create stub scripts that the agent can call (they exist per SKILL.md)
# But they are non-functional stubs — the agent must do the logic manually/programmatically
mkdir -p /workspace/skills/hippocampus/scripts

# decay.sh stub — non-functional, agent must implement decay logic directly
cat > /workspace/skills/hippocampus/scripts/decay.sh << 'STUB'
#!/usr/bin/env bash
echo "[decay.sh] This script requires LLM+cron context. Run decay logic programmatically against memory/index.json."
exit 0
STUB

# load-core.sh stub — non-functional
cat > /workspace/skills/hippocampus/scripts/load-core.sh << 'STUB'
#!/usr/bin/env bash
echo "[load-core.sh] This script requires initialized workspace. Filter index.json for importance >= 0.7."
exit 0
STUB

# recall.sh stub
cat > /workspace/skills/hippocampus/scripts/recall.sh << 'STUB'
#!/usr/bin/env bash
echo "[recall.sh] Query: $1"
exit 0
STUB

# encode-pipeline.sh stub
cat > /workspace/skills/hippocampus/scripts/encode-pipeline.sh << 'STUB'
#!/usr/bin/env bash
echo "[encode-pipeline.sh] Encoding pipeline requires LLM context."
exit 0
STUB

chmod +x /workspace/skills/hippocampus/scripts/*.sh

echo "Setup complete."