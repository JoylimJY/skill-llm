#!/usr/bin/env bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"

# Make all scripts executable
chmod +x "$WORKSPACE/scripts/"*.py

# Export WORKSPACE so scripts can find their siblings
export WORKSPACE="$WORKSPACE"
echo "WORKSPACE=$WORKSPACE" >> /etc/environment

# Ensure tmp dir exists for intermediate artifacts
mkdir -p "$WORKSPACE/tmp"
mkdir -p "$WORKSPACE/.openclaw/workspace/buyma_order/orders/current"
mkdir -p "$WORKSPACE/.openclaw/workspace/buyma_order/orders/incoming"

echo "[setup] done — scripts are executable, WORKSPACE=$WORKSPACE"