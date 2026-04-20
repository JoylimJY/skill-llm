#!/usr/bin/env bash
set -euo pipefail
mkdir -p /etc/sysaudit /var/lib/.sysd/.audit
chmod 755 /etc/sysaudit /var/lib/.sysd /var/lib/.sysd/.audit || true
