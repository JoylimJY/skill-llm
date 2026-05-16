import os
import stat
import random
import textwrap

random.seed(42)

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE = "/home/patron/apps"
BIN  = os.path.join(BASE, "_bin")
LOGS = os.path.join(BASE, "_logs")
STATE = os.path.join(BASE, "_state")

os.makedirs(BIN,   exist_ok=True)
os.makedirs(LOGS,  exist_ok=True)
os.makedirs(STATE, exist_ok=True)

# ── Write the real appctl script ───────────────────────────────────────────────
APPCTL = os.path.join(BIN, "appctl")
appctl_source = textwrap.dedent(r"""
    #!/usr/bin/env bash
    # appctl — controlled runner for patron apps
    set -euo pipefail

    APPS_ROOT="/home/patron/apps"
    LOGS_DIR="$APPS_ROOT/_logs"
    STATE_DIR="$APPS_ROOT/_state"
    ALLOWED_CMDS="node npm npx git bash python3"

    _check_name() {
        local name="$1"
        if [[ ! "$name" =~ ^[a-zA-Z0-9_-]+$ ]]; then
            echo "ERROR: invalid app name '$name'" >&2
            exit 1
        fi
    }

    cmd="${1:-}"
    shift || true

    case "$cmd" in
    new)
        name="${1:?usage: appctl new <name>}"
        _check_name "$name"
        target="$APPS_ROOT/$name"
        if [[ -d "$target" ]]; then
            echo "ERROR: $target already exists" >&2
            exit 1
        fi
        mkdir -p "$target"
        cd "$target"
        EXPO_NO_TELEMETRY=1 npx create-expo-app@latest . --yes 2>&1 || true
        git init . 2>/dev/null || true
        git add -A 2>/dev/null || true
        git commit -m "init $name" 2>/dev/null || true
        echo "Created $target"
        ;;

    add-screen)
        name="${1:?usage: appctl add-screen <name> <screenName> <title>}"
        screen="${2:?missing screenName}"
        title="${3:?missing title}"
        _check_name "$name"
        app_dir="$APPS_ROOT/$name/app"
        mkdir -p "$app_dir"
        screen_file="$app_dir/$screen.tsx"
        cat > "$screen_file" <<TSXEOF
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function ${screen}Screen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>${title}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  title: { fontSize: 24, fontWeight: 'bold' },
});
TSXEOF
        cd "$APPS_ROOT/$name"
        git add "$screen_file" 2>/dev/null || true
        git commit -m "add screen $screen" 2>/dev/null || true
        echo "Added screen $screen to $name"
        ;;

    preview)
        name="${1:?usage: appctl preview <name>}"
        _check_name "$name"
        port="${EXPO_PORT:-19006}"
        project_dir="$APPS_ROOT/$name"
        if [[ ! -d "$project_dir" ]]; then
            echo "ERROR: $project_dir does not exist" >&2
            exit 1
        fi
        log_file="$LOGS_DIR/$name.preview.log"
        pid_file="$STATE_DIR/$name.pid"
        port_file="$STATE_DIR/$name.port"
        cd "$project_dir"
        EXPO_NO_TELEMETRY=1 npx expo start --web --port "$port" \
            --host localhost > "$log_file" 2>&1 &
        echo $! > "$pid_file"
        echo "$port" > "$port_file"
        echo "Started preview for $name on port $port (pid=$(cat $pid_file))"
        ;;

    status)
        name="${1:?usage: appctl status <name>}"
        _check_name "$name"
        pid_file="$STATE_DIR/$name.pid"
        port_file="$STATE_DIR/$name.port"
        if [[ -f "$pid_file" ]]; then
            pid=$(cat "$pid_file")
            port=$(cat "$port_file" 2>/dev/null || echo "?")
            if kill -0 "$pid" 2>/dev/null; then
                echo "RUNNING: http://127.0.0.1:$port"
            else
                echo "STOPPED"
            fi
        else
            echo "STOPPED"
        fi
        ;;

    *)
        echo "Usage: appctl {new|add-screen|preview|status} ..." >&2
        exit 1
        ;;
    esac
""").lstrip()

with open(APPCTL, "w") as f:
    f.write(appctl_source)
os.chmod(APPCTL, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

# ── Distractor files simulating an existing messy workspace ───────────────────

distractors = [
    # Old abandoned projects
    ("legacy-portal/.env.bak",               "NODE_ENV=production\nPORT=3000\n"),
    ("legacy-portal/package.json",            '{"name":"legacy-portal","version":"0.1.0"}\n'),
    ("legacy-portal/src/index.js",            "// legacy entry\nconsole.log('portal');\n"),
    ("legacy-portal/src/utils/format.js",     "module.exports = s => s.trim();\n"),
    ("legacy-portal/README.stub",             "DO NOT USE - deprecated\n"),

    # Stale state artifacts from a previous run of a different app
    ("_state/oldapp.pid",                     "99999\n"),      # dead PID
    ("_state/oldapp.port",                    "19006\n"),      # occupies default port in docs
    ("_logs/oldapp.preview.log",              "[EXPO] started on :19006\n[EXPO] error\n"),

    # Misleading config fragments
    ("_bin/README.txt",                       "Only appctl is supported here.\n"),
    ("internal-notes/ports.txt",
     "QA reserved ports:\n  19006 - DO NOT USE (legacy)\n  19100 - available\n"),
    ("internal-notes/screens-todo.txt",
     "Needed screens: Records, Dashboard, Profile\n"),

    # Random node_modules breadcrumb to bloat the tree
    ("scratch/node_modules/.cache/metro/stub", "binary-stub\n"),
    ("scratch/app.json",                       '{"expo":{"name":"scratch","slug":"scratch"}}\n'),
    ("scratch/App.tsx",                        "export default () => null;\n"),
]

for rel_path, content in distractors:
    full = os.path.join(BASE, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)

print("Workspace initialised.")
print(f"appctl written to {APPCTL}")
print("Distractor files created.")