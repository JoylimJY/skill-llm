#!/bin/bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"

echo "[setup] Workspace initialized."
echo "[setup] Verifying raw observation file exists..."
ls "$WORKSPACE/raw_engineering_log.txt"
echo "[setup] Ready."