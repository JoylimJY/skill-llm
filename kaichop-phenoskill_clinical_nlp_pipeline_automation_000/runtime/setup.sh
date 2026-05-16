#!/bin/bash
set -e

# Set HPO_OBO_PATH to the custom (non-default) location
# This must be persisted for the agent's shell session
echo 'export HPO_OBO_PATH=/workspace/data/hpo_custom/hp.obo' >> /etc/environment
echo 'export HPO_OBO_PATH=/workspace/data/hpo_custom/hp.obo' >> /root/.bashrc
echo 'export HPO_OBO_PATH=/workspace/data/hpo_custom/hp.obo' >> /root/.profile

# Export for the current session too
export HPO_OBO_PATH=/workspace/data/hpo_custom/hp.obo

# Ensure the default resources path does NOT have hp.obo (to force env var resolution)
mkdir -p /workspace/resources
# Explicitly ensure no hp.obo at default location
rm -f /workspace/resources/hp.obo

# Ensure the PhenoSnap directory does NOT pre-exist (agent must clone/download it)
rm -rf /workspace/PhenoSnap

echo "Setup complete."
echo "HPO_OBO_PATH is set to: $HPO_OBO_PATH"
echo "Custom hp.obo exists: $(test -f $HPO_OBO_PATH && echo YES || echo NO)"
echo "Default resources/hp.obo absent: $(test ! -f /workspace/resources/hp.obo && echo YES || echo NO)"
echo "PhenoSnap absent: $(test ! -d /workspace/PhenoSnap && echo YES || echo NO)"