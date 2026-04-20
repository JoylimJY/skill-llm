#!/bin/bash
set -euo pipefail
# Minimal runtime setup tasks; no apt-get/pip installs here per constraints
mkdir -p /task
chmod -R 755 /task
