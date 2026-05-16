#!/bin/bash
set -e

# Make SDK scripts executable
chmod +x /workspace/identity_sdk/generate_did.py
chmod +x /workspace/identity_sdk/sign_mandate.py
chmod +x /workspace/identity_sdk/present_sd_jwt.py
chmod +x /workspace/identity_sdk/identity_check.py

# Ensure workspace permissions
chmod -R 755 /workspace/

echo "Setup complete. Identity SDK tools are ready."
echo "Partner challenges are in /workspace/partner_challenges/"
echo "Identity SDK is in /workspace/identity_sdk/"