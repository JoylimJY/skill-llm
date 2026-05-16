#!/bin/bash
set -e

echo "[setup] Building clauditor binary..."
cd /opt/clauditor
export PATH="/root/.cargo/bin:$PATH"
cargo build --release 2>&1 | tail -5
echo "[setup] clauditor binary built."

echo "[setup] Running installation wizard steps (simulating sysaudit environment)..."

# Step 1: Create sysaudit system user
useradd --system --shell /usr/sbin/nologin --no-create-home sysaudit 2>/dev/null || true

# Step 2: Create config directory and key
mkdir -p /etc/sysaudit
# Generate a deterministic HMAC key for reproducibility
echo -n "clauditor-hmac-seed-42-healthcare-audit" | sha256sum | awk '{print $1}' > /etc/sysaudit/key
chmod 600 /etc/sysaudit/key
chown sysaudit:sysaudit /etc/sysaudit/key 2>/dev/null || true

# Step 3: Create log directory and seed with realistic audit events
mkdir -p /var/lib/.sysd/.audit
chmod 750 /var/lib/.sysd/.audit

# Seed audit log with realistic healthcare system events
cat > /var/lib/.sysd/.audit/events.log << 'LOGEOF'
{"ts":"2024-09-15T00:01:12Z","event":"file_read","path":"/etc/passwd","uid":0,"hmac":"a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"}
{"ts":"2024-09-15T00:02:44Z","event":"file_write","path":"/etc/shadow","uid":0,"hmac":"b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3"}
{"ts":"2024-09-15T00:05:33Z","event":"file_exec","path":"/usr/bin/python3","uid":1001,"hmac":"c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"}
{"ts":"2024-09-15T00:08:19Z","event":"file_delete","path":"/tmp/sess_9f3a","uid":33,"hmac":"d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5"}
{"ts":"2024-09-15T01:15:02Z","event":"file_read","path":"/var/lib/patient_records/rec_00447.enc","uid":2001,"hmac":"e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6"}
{"ts":"2024-09-15T02:30:45Z","event":"file_write","path":"/var/lib/patient_records/rec_00448.enc","uid":2001,"hmac":"f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1"}
{"ts":"2024-09-15T03:22:11Z","event":"file_exec","path":"/usr/sbin/useradd","uid":0,"hmac":"a1f6b2e3c4d5a1f6b2e3c4d5a1f6b2e3c4d5a1f6b2e3c4d5a1f6b2e3c4d5a1f6"}
LOGEOF

chown sysaudit:sysaudit /var/lib/.sysd/.audit/events.log 2>/dev/null || true
chmod 640 /var/lib/.sysd/.audit/events.log

# Step 4: Create config file
cat > /etc/sysaudit/config.toml << 'CONFEOF'
[watchdog]
watch_paths = ["/etc", "/var/lib/patient_records", "/usr/sbin"]
target_uid = 0
log_path = "/var/lib/.sysd/.audit/events.log"
key_path = "/etc/sysaudit/key"

[service]
user = "sysaudit"
CONFEOF
chmod 644 /etc/sysaudit/config.toml

echo "[setup] Sysaudit environment configured."
echo "[setup] Key at: /etc/sysaudit/key"
echo "[setup] Log at: /var/lib/.sysd/.audit/events.log"
echo "[setup] Setup complete."