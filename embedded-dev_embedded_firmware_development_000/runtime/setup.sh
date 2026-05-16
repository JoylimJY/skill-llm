#!/bin/bash
set -e

chmod +x /workspace/robot_arm_fw/tools/flash.sh 2>/dev/null || true

echo "Setup complete. Workspace ready."
tree /workspace/robot_arm_fw 2>/dev/null || find /workspace/robot_arm_fw -type f | sort