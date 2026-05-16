#!/bin/bash
set -e

echo "=== Setting up ZFS test environment ==="

# Ensure ZFS kernel module is loaded
modprobe zfs 2>/dev/null || true

# Create backing image files for test pools
echo "Creating backing image files..."
truncate -s 2G /tmp/disk_primary_a.img
truncate -s 2G /tmp/disk_primary_b.img
truncate -s 4G /tmp/disk_backup.img

# Try to set up loop devices, fall back to direct file use
LOOP_A=/tmp/disk_primary_a.img
LOOP_B=/tmp/disk_primary_b.img
LOOP_C=/tmp/disk_backup.img

if losetup -f &>/dev/null 2>&1; then
    LOOP_A=$(losetup -f --show /tmp/disk_primary_a.img 2>/dev/null) || LOOP_A=/tmp/disk_primary_a.img
    LOOP_B=$(losetup -f --show /tmp/disk_primary_b.img 2>/dev/null) || LOOP_B=/tmp/disk_primary_b.img
    LOOP_C=$(losetup -f --show /tmp/disk_backup.img 2>/dev/null) || LOOP_C=/tmp/disk_backup.img
fi

echo "Devices/files: $LOOP_A $LOOP_B $LOOP_C"

# Save device/file paths for the agent to reference
cat > /workspace/storage_project/configs/proposed/devices.json << EOF
{
  "primary_a": "$LOOP_A",
  "primary_b": "$LOOP_B",
  "backup": "$LOOP_C",
  "note": "These are the block devices available for pool creation in this test environment"
}
EOF

# Make old scripts executable (distractors)
chmod +x /workspace/storage_project/scripts/old_setup.sh
chmod +x /workspace/storage_project/monitoring/check_disk.sh

echo "=== Setup complete ==="
echo "Available block devices/files for ZFS:"
echo "  Primary A: $LOOP_A"
echo "  Primary B: $LOOP_B"
echo "  Backup:    $LOOP_C"