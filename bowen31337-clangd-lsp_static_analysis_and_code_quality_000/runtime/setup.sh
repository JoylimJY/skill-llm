#!/usr/bin/env bash
set -e

chmod +x /workspace/ecu_firmware/scripts/flash.sh
chmod +x /workspace/ecu_firmware/scripts/run_tests.sh

echo "Setup complete. Workspace ready at /workspace/ecu_firmware"
echo "Installed tools:"
clangd --version 2>&1 | head -1
clang-format --version 2>&1 | head -1
clang-tidy --version 2>&1 | head -1
g++ --version 2>&1 | head -1