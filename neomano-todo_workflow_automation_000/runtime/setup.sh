#!/usr/bin/env bash
set -e

WORKSPACE_DIR="${WORKSPACE_DIR:-/workspace}"

# Ensure the todo.py script is executable
chmod +x "$WORKSPACE_DIR/skills/neomano-todo/scripts/todo.py"

# Export the DB path so the agent can discover it via the env
DB_PATH="$WORKSPACE_DIR/.openclaw/workspace/data/neomano-todo.sqlite3"
export NEOMANO_TODO_DB_PATH="$DB_PATH"

# Persist the env var into a .env file that the agent can source / read
mkdir -p "$WORKSPACE_DIR/.openclaw"
cat > "$WORKSPACE_DIR/.openclaw/.env" <<EOF
NEOMANO_TODO_DB_PATH=$DB_PATH
NEOMANO_TODO_DEFAULT_CHANNEL=whatsapp
NEOMANO_TODO_DEFAULT_TARGET=+593987233203
NEOMANO_TODO_TZ=America/Guayaquil
EOF

echo "Setup complete. DB at $DB_PATH"