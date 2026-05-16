#!/usr/bin/env bash
set -e
echo "[setup] Verifying pywayne installation..."
python -c "from pywayne.ahrs.tools import quaternion_decompose, quaternion_roll_pitch_compensate; print('[setup] pywayne.ahrs.tools OK')"
echo "[setup] Done."