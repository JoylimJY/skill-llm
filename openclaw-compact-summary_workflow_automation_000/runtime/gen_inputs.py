import os
import json
import random

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")

# ── Directory structure with distractor files ──────────────────────────────
dirs = [
    "openclaw/runtime/src",
    "openclaw/tools/src",
    "openclaw/memory",
    "openclaw/config",
    "logs/sessions",
    "logs/errors",
    "scratch/tmp",
    "scratch/notes",
    "docs/api",
    "docs/internals",
    "tests/unit",
    "tests/integration",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# Distractor files
distractors = {
    "openclaw/runtime/src/compact.rs": "// Compaction logic\npub fn compact() {}\n",
    "openclaw/runtime/src/memory.rs": "// Memory management\npub struct Memory {}\n",
    "openclaw/tools/src/lib.rs": "pub fn exec() {}\npub fn read_file() {}\npub fn grep_search() {}\n",
    "openclaw/tools/src/exec.rs": "// exec tool\n",
    "openclaw/config/settings.toml": '[memory]\nmax_messages = 100\nflush_threshold = 80\n',
    "openclaw/config/tools.json": '{"tools": ["exec", "read_file", "grep_search", "write_file"]}\n',
    "openclaw/memory/archive.md": "# Old Archive\nSession from 2025-12-01\n",
    "logs/sessions/session_001.log": "raw log data\n",
    "logs/errors/error_001.log": "[ERROR] NullPointer at compact.rs:42\n",
    "scratch/tmp/draft.txt": "temporary notes\n",
    "scratch/notes/ideas.md": "# Ideas\n- Improve flush speed\n",
    "docs/api/memory_api.md": "## Memory API\nPOST /flush\nGET /status\n",
    "docs/internals/architecture.md": "# Architecture\nOpenClaw uses a layered memory model.\n",
    "tests/unit/test_compact.py": "def test_compact(): pass\n",
    "tests/integration/test_memory_flush.py": "def test_flush(): pass\n",
}
for rel, content in distractors.items():
    with open(os.path.join(WORKSPACE, rel), "w") as f:
        f.write(content)

# ── The MESSY raw conversation log the agent must process ──────────────────
# Stored as a JSON file with unstructured fields — the agent must parse this
# and produce a clean MEMORY.md according to the SKILL.md spec.

raw_session = {
    "session_id": "sess-2026-07-15-alpha",
    "recorded_at": "2026-07-15T14:37:00Z",
    "messages": [
        {
            "role": "user",
            "content": "I need you to analyze the OpenClaw memory flush pipeline and identify bottlenecks."
        },
        {
            "role": "assistant",
            "content": "Sure, I'll start by reading the compact.rs source file to understand the current flush logic."
        },
        {
            "role": "tool",
            "tool_name": "read_file",
            "content": "read_file path=$WORKSPACE/openclaw/runtime/src/compact.rs"
        },
        {
            "role": "tool_result",
            "content": "File content: pub fn compact() { /* 450 lines of flush logic */ }"
        },
        {
            "role": "tool",
            "tool_name": "grep_search",
            "content": "grep_search pattern=flush_threshold path=$WORKSPACE/openclaw/config/settings.toml"
        },
        {
            "role": "tool_result",
            "content": "1 match: flush_threshold = 80"
        },
        {
            "role": "assistant",
            "content": "The flush threshold is set to 80 messages. The bottleneck appears to be in the serialization step inside compact.rs."
        },
        {
            "role": "user",
            "content": "Can you also check the tools library to see which tools interact with memory directly?"
        },
        {
            "role": "tool",
            "tool_name": "exec",
            "content": "exec command=grep -rn 'memory' $WORKSPACE/openclaw/tools/src/"
        },
        {
            "role": "tool_result",
            "content": "3 matches in lib.rs: exec references memory state on lines 12, 45, 78"
        },
        {
            "role": "assistant",
            "content": "Three tools directly touch memory: exec (lines 12, 45, 78 in lib.rs). I recommend adding an async flush guard around each call."
        },
        {
            "role": "user",
            "content": "Great. Please draft a todo list for the P0 fixes needed and start working on the highest priority item."
        },
        {
            "role": "assistant",
            "content": "P0 todo list: 1) Add async flush guard in exec tool, 2) Reduce serialization overhead in compact.rs, 3) Write regression tests for memory flush. Starting on item 1 now."
        },
        {
            "role": "tool",
            "tool_name": "exec",
            "content": "exec command=cargo test --manifest-path $WORKSPACE/openclaw/Cargo.toml"
        },
        {
            "role": "tool_result",
            "content": "error: could not find Cargo.toml — skipping build"
        }
    ],
    "pending_todos": [
        "Add async flush guard in exec tool",
        "Reduce serialization overhead in compact.rs",
        "Write regression tests for memory flush"
    ],
    "key_files_touched": [
        "$WORKSPACE/openclaw/runtime/src/compact.rs",
        "$WORKSPACE/openclaw/config/settings.toml",
        "$WORKSPACE/openclaw/tools/src/lib.rs"
    ],
    "current_focus": "Implementing async flush guard in the exec tool (P0 priority)"
}

with open(os.path.join(WORKSPACE, "logs/sessions/raw_session_2026-07-15.json"), "w") as f:
    json.dump(raw_session, f, indent=2)

print("Workspace initialized successfully.")
print(f"Raw session log written to: {WORKSPACE}/logs/sessions/raw_session_2026-07-15.json")