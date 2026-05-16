#!/usr/bin/env python3
"""
Generate the sandbox environment for the neckr0ik-session-healer task.
Sets up the ~/.openclaw directory structure with realistic lock files,
session files, and distractor files. Also installs a mock neckr0ik-session-healer CLI.
"""
import os
import json
import random
import stat
import sys
import textwrap
from pathlib import Path

random.seed(42)

# ── Workspace & home dir ────────────────────────────────────────────────────
workspace = Path("/workspace")
home = Path.home()  # /root in Docker

# ── OpenClaw directory structure ────────────────────────────────────────────
agents_root = home / ".openclaw" / "agents"

# We create two agent namespaces: main and helpdesk
for agent in ["main", "helpdesk", "analytics"]:
    (agents_root / agent / "sessions").mkdir(parents=True, exist_ok=True)
    (agents_root / agent / "config").mkdir(parents=True, exist_ok=True)
    (agents_root / agent / "logs").mkdir(parents=True, exist_ok=True)

# ── Session IDs ──────────────────────────────────────────────────────────────
# Three locks total:
#   1. stale-dead-1  → PID that is definitely dead → should be healed
#   2. stale-dead-2  → PID that is definitely dead + corrupted JSONL → heal + recover
#   3. active-alive  → PID of a real alive process (we'll use PID 1) → must NOT be cleared

STALE_SESSION_1 = "c4fa26e6-20be-4843-9678-a2f328dd1844"
STALE_SESSION_2 = "7e3b9a12-ff01-4c88-bde0-98765dcba210"  # corrupted + locked
ACTIVE_SESSION  = "a1b2c3d4-5678-90ab-cdef-1234567890ab"

# Dead PIDs — choose numbers that are virtually impossible to be alive
DEAD_PID_1 = 99991
DEAD_PID_2 = 99992
ALIVE_PID  = 1       # PID 1 is always alive in a container

# ── Helper: write a valid JSONL session file ─────────────────────────────────
def make_valid_jsonl(path: Path, session_id: str, n_lines: int = 5):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for i in range(n_lines):
            line = {"seq": i, "session": session_id, "msg": f"log entry {i}", "ts": 1700000000 + i}
            f.write(json.dumps(line) + "\n")

# ── Helper: write a CORRUPTED JSONL (some lines are garbage) ────────────────
def make_corrupted_jsonl(path: Path, session_id: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        # good line
        f.write(json.dumps({"seq": 0, "session": session_id, "msg": "startup", "ts": 1700000000}) + "\n")
        # good line
        f.write(json.dumps({"seq": 1, "session": session_id, "msg": "processing request", "ts": 1700000001}) + "\n")
        # CORRUPT line (truncated JSON from a crash)
        f.write('{"seq": 2, "session": "' + session_id + '", "msg": "crash moment", "ts": 170\x00\x00\n')
        # another CORRUPT line
        f.write('}{broken json garbage here\n')
        # good line
        f.write(json.dumps({"seq": 3, "session": session_id, "msg": "post-crash orphan", "ts": 1700000003}) + "\n")

# ── Session 1: stale dead lock, clean JSONL ──────────────────────────────────
sess1_dir = agents_root / "main" / "sessions" / STALE_SESSION_1
sess1_jsonl = sess1_dir / f"{STALE_SESSION_1}.jsonl"
sess1_lock  = sess1_dir / f"{STALE_SESSION_1}.jsonl.lock"
make_valid_jsonl(sess1_jsonl, STALE_SESSION_1)
sess1_lock.write_text(json.dumps({"pid": DEAD_PID_1, "created": 1699990000, "host": "worker-node-7"}))

# ── Session 2: stale dead lock + corrupted JSONL ─────────────────────────────
sess2_dir = agents_root / "helpdesk" / "sessions" / STALE_SESSION_2
sess2_jsonl = sess2_dir / f"{STALE_SESSION_2}.jsonl"
sess2_lock  = sess2_dir / f"{STALE_SESSION_2}.jsonl.lock"
make_corrupted_jsonl(sess2_jsonl, STALE_SESSION_2)
sess2_lock.write_text(json.dumps({"pid": DEAD_PID_2, "created": 1699980000, "host": "worker-node-3"}))

# ── Session 3: ACTIVE lock (PID 1 is alive in the container) ─────────────────
sess3_dir = agents_root / "main" / "sessions" / ACTIVE_SESSION
sess3_jsonl = sess3_dir / f"{ACTIVE_SESSION}.jsonl"
sess3_lock  = sess3_dir / f"{ACTIVE_SESSION}.jsonl.lock"
make_valid_jsonl(sess3_jsonl, ACTIVE_SESSION, n_lines=12)
sess3_lock.write_text(json.dumps({"pid": ALIVE_PID, "created": 1700090000, "host": "worker-node-7"}))

# ── Config distractor files ──────────────────────────────────────────────────
for agent in ["main", "helpdesk", "analytics"]:
    cfg = agents_root / agent / "config" / "agent.json"
    cfg.write_text(json.dumps({
        "agent_id": agent,
        "model": "gpt-4o",
        "max_tokens": 8192,
        "timeout_ms": 10000,
        "session_dir": f"~/.openclaw/agents/{agent}/sessions"
    }, indent=2))

# ── Log distractor files ──────────────────────────────────────────────────────
log_messages = [
    "INFO: Agent started",
    "INFO: Session initialized",
    "WARN: High memory usage detected",
    "ERROR: session file locked (timeout 10000ms)",
    "ERROR: session file locked (timeout 10000ms)",
    "ERROR: session file locked (timeout 10000ms)",
    "INFO: Retrying...",
    "ERROR: All models fail - lock timeout",
]
for agent in ["main", "helpdesk"]:
    logfile = agents_root / agent / "logs" / "agent.log"
    logfile.write_text("\n".join(log_messages) + "\n")

# analytics has clean logs (distractor)
(agents_root / "analytics" / "logs" / "agent.log").write_text(
    "INFO: Agent started\nINFO: Session initialized\nINFO: All systems nominal\n"
)

# ── Distractor: orphaned .lock file with NO corresponding .jsonl ─────────────
orphan_dir = agents_root / "analytics" / "sessions" / "deadbeef-0000-0000-0000-000000000000"
orphan_dir.mkdir(parents=True, exist_ok=True)
(orphan_dir / "deadbeef-0000-0000-0000-000000000000.jsonl.lock").write_text(
    json.dumps({"pid": 99993, "created": 1699970000, "host": "worker-node-9"})
)

# ── Distractor: temp files in workspace ──────────────────────────────────────
(workspace / "crash_report_2024-11-15.txt").write_text(
    "System crashed at 03:14 UTC. Multiple OpenClaw agents affected.\n"
    "Sessions: c4fa26e6, 7e3b9a12 were writing at time of crash.\n"
    "Session a1b2c3d4 was idle and should be unaffected.\n"
)
(workspace / "maintenance_notes.txt").write_text(
    "Maintenance window: 02:00-04:00 UTC\n"
    "Actions needed: clear stale session locks, recover corrupted data\n"
    "Do NOT interrupt active session a1b2c3d4\n"
)
(workspace / "oncall_runbook.md").write_text(
    "# On-Call Runbook\n\n"
    "## Session Lock Errors\n"
    "When you see 'session file locked (timeout 10000ms)' in logs:\n"
    "1. Check which sessions are affected\n"
    "2. Clear stale locks from crashed processes\n"
    "3. Recover any corrupted session data\n"
    "4. Never interrupt sessions that are actively being written\n"
)
(workspace / "affected_sessions.txt").write_text(
    f"Stale sessions identified from crash report:\n"
    f"  - {STALE_SESSION_1} (agent: main)\n"
    f"  - {STALE_SESSION_2} (agent: helpdesk, possible data corruption)\n"
    f"\nActive sessions (DO NOT TOUCH):\n"
    f"  - {ACTIVE_SESSION} (agent: main)\n"
)

# ── Write the mock healer script ─────────────────────────────────────────────
# This is the actual implementation of neckr0ik-session-healer
# It must be written here because setup_script will chmod+x it
healer_script = r"""#!/usr/bin/env python3
"""
healer_src = textwrap.dedent('''\
#!/usr/bin/env python3
"""
neckr0ik-session-healer - Mock implementation for sandbox testing.
Implements: check, heal, unlock, recover
"""
import sys
import os
import json
import shutil
import glob
import time
from pathlib import Path
from datetime import datetime

HOME = Path.home()
AGENTS_ROOT = HOME / ".openclaw" / "agents"
LOCK_GLOB = str(AGENTS_ROOT / "*" / "sessions" / "*" / "*.jsonl.lock")
LOG_FILE = HOME / ".openclaw" / "healer-audit.log"

def audit(msg):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a") as f:
        f.write(f"[{datetime.utcnow().isoformat()}] {msg}\\n")

def is_alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ProcessLookupError):
        return False

def get_session_id_from_lock(lock_path):
    p = Path(lock_path)
    # filename: <session-id>.jsonl.lock
    return p.name.replace(".jsonl.lock", "")

def lock_age_str(created_ts):
    age_sec = int(time.time()) - int(created_ts)
    if age_sec < 60:
        return f"{age_sec} seconds"
    elif age_sec < 3600:
        return f"{age_sec // 60} minutes"
    else:
        h = age_sec // 3600
        m = (age_sec % 3600) // 60
        return f"{h} hours {m} minutes"

def cmd_check(args):
    verbose = "--verbose" in args
    lock_files = glob.glob(LOCK_GLOB)
    print("\\nChecking for locked sessions...")
    if not lock_files:
        print("No lock files found.")
        return
    print(f"Found {len(lock_files)} lock files:\\n")
    for lf in sorted(lock_files):
        sid = get_session_id_from_lock(lf)
        try:
            data = json.loads(Path(lf).read_text())
            pid = data.get("pid", "unknown")
            created = data.get("created", 0)
            alive = is_alive(pid)
            status_sym = "✓" if alive else "✗"
            pid_status = "ALIVE" if alive else "DEAD - process not running"
            lock_status = "ACTIVE - do not clear" if alive else "STALE - safe to clear"
            print(f"  {status_sym} session: {sid}")
            print(f"    Lock: {lf}")
            print(f"    PID: {pid} ({pid_status})")
            if verbose:
                print(f"    Created: {datetime.utcfromtimestamp(created).isoformat()}")
            print(f"    Age: {lock_age_str(created)}")
            print(f"    Status: {lock_status}")
            print()
        except Exception as e:
            print(f"  ? session: {sid}")
            print(f"    Lock: {lf}")
            print(f"    Error reading lock: {e}")
            print()

def cmd_heal(args):
    force = "--force" in args
    dry_run = "--dry-run" in args
    lock_files = glob.glob(LOCK_GLOB)
    print("\\nHealing stale locks...")
    healed = 0
    errors = 0
    for lf in sorted(lock_files):
        sid = get_session_id_from_lock(lf)
        try:
            data = json.loads(Path(lf).read_text())
            pid = data.get("pid", "unknown")
            alive = is_alive(pid)
            if alive and not force:
                print(f"[SKIPPED] {sid} (PID {pid} still alive)")
                audit(f"SKIP {sid} PID={pid} alive=True")
            else:
                reason = "was dead" if not alive else "force flag used"
                if dry_run:
                    print(f"[DRY-RUN] Would clear {sid} (PID {pid} {reason})")
                else:
                    os.remove(lf)
                    print(f"[CLEARED] {sid} (PID {pid} {reason})")
                    audit(f"CLEARED {sid} PID={pid} reason={reason}")
                    healed += 1
        except Exception as e:
            print(f"[ERROR] {sid}: {e}")
            errors += 1
    print(f"\\nHealed {healed} session(s). {errors} error(s).")

def cmd_unlock(args):
    if not args:
        print("Usage: neckr0ik-session-healer unlock <session-id>")
        sys.exit(1)
    sid = args[0]
    lock_files = glob.glob(LOCK_GLOB)
    for lf in lock_files:
        if get_session_id_from_lock(lf) == sid:
            try:
                os.remove(lf)
                print(f"[UNLOCKED] {sid}")
                audit(f"UNLOCKED {sid}")
                return
            except Exception as e:
                print(f"[ERROR] Could not unlock {sid}: {e}")
                return
    print(f"[NOT FOUND] No lock found for session {sid}")

def cmd_recover(args):
    if not args:
        print("Usage: neckr0ik-session-healer recover <session-id>")
        sys.exit(1)
    sid = args[0]
    # Find the .jsonl file for this session
    pattern = str(AGENTS_ROOT / "*" / "sessions" / sid / f"{sid}.jsonl")
    matches = glob.glob(pattern)
    if not matches:
        print(f"[NOT FOUND] No session file found for {sid}")
        sys.exit(1)
    jsonl_path = Path(matches[0])
    # Create backup
    backup_path = jsonl_path.with_suffix(".jsonl.bak")
    shutil.copy2(jsonl_path, backup_path)
    print(f"[BACKUP] Created {backup_path}")
    audit(f"BACKUP {jsonl_path} -> {backup_path}")
    # Validate and recover
    good_lines = []
    bad_count = 0
    with jsonl_path.open("rb") as f:
        for line in f:
            line_str = line.decode("utf-8", errors="replace").strip()
            if not line_str:
                continue
            try:
                json.loads(line_str)
                good_lines.append(line_str)
            except json.JSONDecodeError:
                bad_count += 1
                print(f"[REMOVED] Corrupted line: {line_str[:60]}...")
                audit(f"REMOVED corrupted line from {sid}")
    # Write recovered file
    with jsonl_path.open("w") as f:
        for gl in good_lines:
            f.write(gl + "\\n")
    print(f"[RECOVERED] {sid}: removed {bad_count} corrupted line(s), kept {len(good_lines)} valid line(s).")
    # Validate integrity
    ok = True
    with jsonl_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                json.loads(line)
            except Exception:
                ok = False
    if ok:
        print(f"[OK] Session file integrity validated.")
    else:
        print(f"[WARN] Some lines still invalid after recovery.")
    audit(f"RECOVERED {sid} bad_lines={bad_count}")

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: neckr0ik-session-healer <check|heal|unlock|recover> [options]")
        sys.exit(1)
    cmd = args[0]
    rest = args[1:]
    if cmd == "check":
        cmd_check(rest)
    elif cmd == "heal":
        cmd_heal(rest)
    elif cmd == "unlock":
        cmd_unlock(rest)
    elif cmd == "recover":
        cmd_recover(rest)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
''')

healer_bin = Path("/usr/local/bin/neckr0ik-session-healer")
healer_bin.write_text(healer_src)
healer_bin.chmod(0o755)

print("=== Sandbox generation complete ===")
print(f"Lock files created:")
print(f"  {sess1_lock}")
print(f"  {sess2_lock}")
print(f"  {sess3_lock}")
print(f"Session 2 JSONL is corrupted: {sess2_jsonl}")
print(f"Healer installed at: {healer_bin}")