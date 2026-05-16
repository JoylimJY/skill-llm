#!/usr/bin/env bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"
SKILL_BASE="${WORKSPACE}/skill-case-study-factory"

chmod +x "${SKILL_BASE}/scripts/run.py"

echo "[setup] Skill base: ${SKILL_BASE}"
echo "[setup] run.py is executable."
echo "[setup] Ready."