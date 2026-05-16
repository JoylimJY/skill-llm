#!/bin/bash
set -e

WORKSPACE=/workspace

# ── Create mock tool scripts ────────────────────────────────────────────────
# Each script logs its invocation with a timestamp to tool_logs/invocations.jsonl
# then returns a plausible fake response.

# Helper function embedded in each script to log calls
LOGGER_CODE='
import sys, json, time, os
from datetime import datetime, timezone

log_path = "/workspace/tool_logs/invocations.jsonl"
tool_name = os.path.basename(sys.argv[0]).replace(".py","")
raw_args = sys.argv[1:]

# Parse args: support --key value and --key=value and positional JSON
parsed = {}
i = 0
while i < len(raw_args):
    arg = raw_args[i]
    if arg.startswith("--"):
        key = arg.lstrip("-")
        if "=" in key:
            k, v = key.split("=", 1)
            parsed[k] = v
        elif i + 1 < len(raw_args) and not raw_args[i+1].startswith("--"):
            parsed[key] = raw_args[i+1]
            i += 1
        else:
            parsed[key] = True
    i += 1

# Also try parsing first positional arg as JSON
for arg in raw_args:
    try:
        obj = json.loads(arg)
        if isinstance(obj, dict):
            parsed.update(obj)
    except Exception:
        pass

record = {
    "tool": tool_name,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "unix_ts": time.time(),
    "args": parsed,
    "raw_args": raw_args
}

with open(log_path, "a") as f:
    f.write(json.dumps(record) + "\n")
'

# ── memory_search ────────────────────────────────────────────────────────────
cat > /usr/local/bin/memory_search << 'PYEOF'
#!/usr/bin/env python3
import sys, json, time, os
from datetime import datetime, timezone

log_path = "/workspace/tool_logs/invocations.jsonl"
tool_name = "memory_search"
raw_args = sys.argv[1:]
parsed = {}
i = 0
while i < len(raw_args):
    arg = raw_args[i]
    if arg.startswith("--"):
        key = arg.lstrip("-")
        if "=" in key:
            k, v = key.split("=", 1)
            parsed[k] = v
        elif i + 1 < len(raw_args) and not raw_args[i+1].startswith("--"):
            parsed[key] = raw_args[i+1]
            i += 1
        else:
            parsed[key] = True
    i += 1
for arg in raw_args:
    try:
        obj = json.loads(arg)
        if isinstance(obj, dict):
            parsed.update(obj)
    except Exception:
        pass
record = {"tool": tool_name, "timestamp": datetime.now(timezone.utc).isoformat(), "unix_ts": time.time(), "args": parsed, "raw_args": raw_args}
with open(log_path, "a") as f:
    f.write(json.dumps(record) + "\n")

print(json.dumps({
    "results": [
        {"id": "mem_001", "content": "Previous TAD for SaaS platform: used Opus for writing, GLM for review. Took 8 minutes total.", "relevance": 0.91},
        {"id": "mem_002", "content": "Architecture documents should include: system overview, data flow diagrams, security posture.", "relevance": 0.87}
    ],
    "total": 2
}))
PYEOF
chmod +x /usr/local/bin/memory_search

# ── sessions_spawn ───────────────────────────────────────────────────────────
cat > /usr/local/bin/sessions_spawn << 'PYEOF'
#!/usr/bin/env python3
import sys, json, time, os, random, string
from datetime import datetime, timezone

log_path = "/workspace/tool_logs/invocations.jsonl"
tool_name = "sessions_spawn"
raw_args = sys.argv[1:]
parsed = {}
i = 0
while i < len(raw_args):
    arg = raw_args[i]
    if arg.startswith("--"):
        key = arg.lstrip("-")
        if "=" in key:
            k, v = key.split("=", 1)
            parsed[k] = v
        elif i + 1 < len(raw_args) and not raw_args[i+1].startswith("--"):
            parsed[key] = raw_args[i+1]
            i += 1
        else:
            parsed[key] = True
    i += 1
for arg in raw_args:
    try:
        obj = json.loads(arg)
        if isinstance(obj, dict):
            parsed.update(obj)
    except Exception:
        pass
record = {"tool": tool_name, "timestamp": datetime.now(timezone.utc).isoformat(), "unix_ts": time.time(), "args": parsed, "raw_args": raw_args}
with open(log_path, "a") as f:
    f.write(json.dumps(record) + "\n")

session_key = "sess_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
label = parsed.get("label", "unnamed")
print(json.dumps({
    "sessionKey": session_key,
    "label": label,
    "status": "spawned",
    "model": parsed.get("model", "unknown"),
    "message": f"Sub-agent '{label}' spawned successfully with key {session_key}"
}))
PYEOF
chmod +x /usr/local/bin/sessions_spawn

# ── sessions_list ────────────────────────────────────────────────────────────
cat > /usr/local/bin/sessions_list << 'PYEOF'
#!/usr/bin/env python3
import sys, json, time, os
from datetime import datetime, timezone

log_path = "/workspace/tool_logs/invocations.jsonl"
tool_name = "sessions_list"
raw_args = sys.argv[1:]
parsed = {}
i = 0
while i < len(raw_args):
    arg = raw_args[i]
    if arg.startswith("--"):
        key = arg.lstrip("-")
        if "=" in key:
            k, v = key.split("=", 1)
            parsed[k] = v
        elif i + 1 < len(raw_args) and not raw_args[i+1].startswith("--"):
            parsed[key] = raw_args[i+1]
            i += 1
        else:
            parsed[key] = True
    i += 1
for arg in raw_args:
    try:
        obj = json.loads(arg)
        if isinstance(obj, dict):
            parsed.update(obj)
    except Exception:
        pass
record = {"tool": tool_name, "timestamp": datetime.now(timezone.utc).isoformat(), "unix_ts": time.time(), "args": parsed, "raw_args": raw_args}
with open(log_path, "a") as f:
    f.write(json.dumps(record) + "\n")

print(json.dumps({
    "sessions": [
        {"sessionKey": "sess_abc123", "label": "tad-writer", "status": "completed", "lastMessage": "TAD document written and saved to deliverables/technical_architecture_document.md (2347 words)"},
    ],
    "total": 1
}))
PYEOF
chmod +x /usr/local/bin/sessions_list

# ── sessions_history ─────────────────────────────────────────────────────────
cat > /usr/local/bin/sessions_history << 'PYEOF'
#!/usr/bin/env python3
import sys, json, time, os
from datetime import datetime, timezone

log_path = "/workspace/tool_logs/invocations.jsonl"
tool_name = "sessions_history"
raw_args = sys.argv[1:]
parsed = {}
i = 0
while i < len(raw_args):
    arg = raw_args[i]
    if arg.startswith("--"):
        key = arg.lstrip("-")
        if "=" in key:
            k, v = key.split("=", 1)
            parsed[k] = v
        elif i + 1 < len(raw_args) and not raw_args[i+1].startswith("--"):
            parsed[key] = raw_args[i+1]
            i += 1
        else:
            parsed[key] = True
    i += 1
for arg in raw_args:
    try:
        obj = json.loads(arg)
        if isinstance(obj, dict):
            parsed.update(obj)
    except Exception:
        pass
record = {"tool": tool_name, "timestamp": datetime.now(timezone.utc).isoformat(), "unix_ts": time.time(), "args": parsed, "raw_args": raw_args}
with open(log_path, "a") as f:
    f.write(json.dumps(record) + "\n")

session_key = parsed.get("sessionKey", parsed.get("session_key", "unknown"))
print(json.dumps({
    "sessionKey": session_key,
    "history": [
        {"role": "assistant", "content": "Starting Technical Architecture Document...", "ts": time.time() - 300},
        {"role": "assistant", "content": "Writing system overview section (400 words)...", "ts": time.time() - 200},
        {"role": "assistant", "content": "Completed: document saved to deliverables/technical_architecture_document.md, 2347 words.", "ts": time.time() - 10}
    ]
}))
PYEOF
chmod +x /usr/local/bin/sessions_history

# ── Ensure tool_logs dir is writable ────────────────────────────────────────
chmod -R 777 /workspace/tool_logs

echo "Mock tools installed and workspace ready."