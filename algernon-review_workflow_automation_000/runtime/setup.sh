#!/usr/bin/env bash
set -e

WORKSPACE="/workspace"
ALGERNON_HOME="${WORKSPACE}/algernon_home"

# Export environment variables so the agent can find the database
echo "export ALGERNON_HOME=\"${ALGERNON_HOME}\"" >> /etc/environment
echo "export DB=\"${ALGERNON_HOME}/data/study.db\"" >> /etc/environment

# Also make them available in the current shell profile
echo "export ALGERNON_HOME=\"${ALGERNON_HOME}\"" >> /root/.bashrc
echo "export DB=\"${ALGERNON_HOME}/data/study.db\"" >> /root/.bashrc

# Ensure scripts directory is executable
chmod +x "${WORKSPACE}/scripts/migrate.sh" 2>/dev/null || true

# Ensure memory/conversations directory exists with correct permissions
mkdir -p "${ALGERNON_HOME}/memory/conversations"
chmod -R 755 "${ALGERNON_HOME}"

# Verify the database was created and is accessible
if [ -f "${ALGERNON_HOME}/data/study.db" ]; then
    echo "Database verified: $(sqlite3 "${ALGERNON_HOME}/data/study.db" 'SELECT COUNT(*) FROM cards;') cards"
else
    echo "ERROR: Database not found!"
    exit 1
fi

echo "Setup complete. ALGERNON_HOME=${ALGERNON_HOME}"