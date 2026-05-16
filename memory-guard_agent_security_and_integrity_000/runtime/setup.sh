#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------
# Install the 'memory-guard' CLI tool into /usr/local/bin
# This implements the full memory-guard specification from SKILL.md
# -----------------------------------------------------------------------

cat > /usr/local/bin/memory-guard << 'MGSCRIPT'
#!/usr/bin/env python3
"""
memory-guard - Agent Memory Integrity & Security Tool
Implements: init, verify, audit, stamp, watch commands
"""
import sys
import os
import json
import hashlib
import datetime
import subprocess
import time
from pathlib import Path

GUARD_DIR = ".memory-guard"
HASHES_FILE = ".memory-guard/hashes.json"
TRACKED_FILES = ["SOUL.md", "AGENTS.md", "IDENTITY.md"]
ACTIONS_LOG = "actions.log"
REJECTIONS_LOG = "rejections.log"
HANDOFFS_LOG = "handoffs.log"


def get_workspace():
    return Path(os.getcwd())


def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_registry():
    ws = get_workspace()
    hf = ws / HASHES_FILE
    if not hf.exists():
        return {}
    with open(hf) as f:
        return json.load(f)


def save_registry(registry):
    ws = get_workspace()
    guard_dir = ws / GUARD_DIR
    guard_dir.mkdir(exist_ok=True)
    hf = ws / HASHES_FILE
    with open(hf, "w") as f:
        json.dump(registry, f, indent=2)


def append_log(logfile, entry):
    ws = get_workspace()
    lf = ws / logfile
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    with open(lf, "a") as f:
        f.write(f"[{timestamp}] {entry}\n")


def cmd_init(args):
    ws = get_workspace()
    registry = {}
    initialized = []
    missing = []

    for fname in TRACKED_FILES:
        fp = ws / fname
        if fp.exists():
            h = sha256_file(fp)
            registry[fname] = {
                "hash": h,
                "initialized_at": datetime.datetime.utcnow().isoformat() + "Z",
                "size": fp.stat().st_size
            }
            initialized.append(fname)
        else:
            missing.append(fname)

    save_registry(registry)

    # Ensure three-log pattern files exist
    for log in [ACTIONS_LOG, REJECTIONS_LOG, HANDOFFS_LOG]:
        lf = ws / log
        if not lf.exists():
            lf.touch()

    print(f"[memory-guard] Initialized integrity tracking.")
    print(f"  Tracked: {', '.join(initialized)}")
    if missing:
        print(f"  Missing (skipped): {', '.join(missing)}")
    print(f"  Registry: {HASHES_FILE}")
    print(f"  Logs: {ACTIONS_LOG}, {REJECTIONS_LOG}, {HANDOFFS_LOG}")
    append_log(ACTIONS_LOG, f"memory-guard init completed. Tracked: {initialized}")
    return 0


def cmd_verify(args):
    ws = get_workspace()
    registry = load_registry()

    if not registry:
        print("[memory-guard] ERROR: No registry found. Run 'memory-guard init' first.")
        append_log(REJECTIONS_LOG, "verify failed: no registry found")
        return 1

    results = {}
    all_ok = True

    for fname, meta in registry.items():
        fp = ws / fname
        if not fp.exists():
            results[fname] = {"status": "MISSING", "expected": meta["hash"], "actual": None}
            all_ok = False
            append_log(REJECTIONS_LOG, f"TAMPERING DETECTED: {fname} is MISSING")
        else:
            current_hash = sha256_file(fp)
            if current_hash == meta["hash"]:
                results[fname] = {"status": "OK", "hash": current_hash}
            else:
                results[fname] = {
                    "status": "TAMPERED",
                    "expected": meta["hash"],
                    "actual": current_hash
                }
                all_ok = False
                append_log(REJECTIONS_LOG, f"TAMPERING DETECTED: {fname} hash mismatch")

    print("[memory-guard] Verification Report:")
    for fname, r in results.items():
        status = r["status"]
        if status == "OK":
            print(f"  ✓ {fname}: OK")
        elif status == "TAMPERED":
            print(f"  ✗ {fname}: TAMPERED (expected={r['expected'][:16]}... actual={r['actual'][:16]}...)")
        else:
            print(f"  ✗ {fname}: MISSING")

    if all_ok:
        msg = "verify passed: all files intact"
        print("[memory-guard] All files intact. No tampering detected.")
        append_log(ACTIONS_LOG, msg)
    else:
        msg = "verify FAILED: tampering detected in one or more files"
        print("[memory-guard] ALERT: Tampering detected! Alert human immediately.")
        append_log(REJECTIONS_LOG, msg)

    return 0 if all_ok else 2


def cmd_audit(args):
    ws = get_workspace()
    registry = load_registry()

    if not registry:
        print("[memory-guard] ERROR: No registry found. Run 'memory-guard init' first.")
        return 1

    print("[memory-guard] Full Audit Report")
    print("=" * 60)
    print(f"Workspace: {ws}")
    print(f"Generated: {datetime.datetime.utcnow().isoformat()}Z")
    print()

    for fname, meta in registry.items():
        fp = ws / fname
        print(f"File: {fname}")
        print(f"  Registered hash : {meta['hash']}")
        print(f"  Registered at   : {meta.get('initialized_at', 'unknown')}")
        if fp.exists():
            current_hash = sha256_file(fp)
            status = "OK" if current_hash == meta["hash"] else "TAMPERED"
            print(f"  Current hash    : {current_hash}")
            print(f"  Status          : {status}")
            # Try git log for who changed it
            try:
                result = subprocess.run(
                    ["git", "log", "--oneline", "-3", "--", fname],
                    capture_output=True, text=True, cwd=str(ws), timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    print(f"  Git history     :")
                    for line in result.stdout.strip().split("\n"):
                        print(f"    {line}")
                else:
                    print(f"  Git history     : (not a git repo or no commits)")
            except Exception:
                print(f"  Git history     : (git unavailable)")
        else:
            print(f"  Status          : MISSING")
        print()

    # Print log summaries
    for log in [ACTIONS_LOG, REJECTIONS_LOG, HANDOFFS_LOG]:
        lf = ws / log
        print(f"--- {log} ---")
        if lf.exists() and lf.stat().st_size > 0:
            with open(lf) as f:
                lines = f.readlines()
            for line in lines[-10:]:
                print(f"  {line.rstrip()}")
        else:
            print("  (empty)")
        print()

    append_log(ACTIONS_LOG, "memory-guard audit completed")
    return 0


def cmd_stamp(args):
    if len(args) < 1:
        print("Usage: memory-guard stamp <file>")
        return 1

    filepath = args[0]
    ws = get_workspace()
    fp = ws / filepath
    if not fp.exists():
        fp_abs = Path(filepath)
        if not fp_abs.exists():
            print(f"[memory-guard] ERROR: File not found: {filepath}")
            append_log(REJECTIONS_LOG, f"stamp failed: file not found: {filepath}")
            return 1
        fp = fp_abs

    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    agent_name = os.environ.get("MEMORY_GUARD_AGENT", "unknown-agent")
    confidence = os.environ.get("MEMORY_GUARD_CONFIDENCE", "MEDIUM")
    rationale = os.environ.get("MEMORY_GUARD_RATIONALE", "routine-stamp")

    stamp = f"[{agent_name}|{timestamp}|{confidence}|{rationale}]\n"

    original = fp.read_text()
    fp.write_text(stamp + original)

    print(f"[memory-guard] Provenance stamp added to {filepath}")
    print(f"  Stamp: {stamp.strip()}")
    append_log(ACTIONS_LOG, f"stamp applied to {filepath}: {stamp.strip()}")
    return 0


def cmd_watch(args):
    print("[memory-guard] Starting continuous monitoring mode (Ctrl+C to stop)...")
    try:
        while True:
            cmd_verify([])
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n[memory-guard] Watch mode stopped.")
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: memory-guard <command> [args]")
        print("Commands: init, verify, audit, stamp <file>, watch")
        return 1

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "init": cmd_init,
        "verify": cmd_verify,
        "audit": cmd_audit,
        "stamp": cmd_stamp,
        "watch": cmd_watch,
    }

    if command not in commands:
        print(f"[memory-guard] Unknown command: {command}")
        return 1

    return commands[command](args)


if __name__ == "__main__":
    sys.exit(main())
MGSCRIPT

chmod +x /usr/local/bin/memory-guard

# Also install a 'clawhub' stub so agents that try to install via clawhub get a message
cat > /usr/local/bin/clawhub << 'CLAWHUB'
#!/usr/bin/env bash
echo "[clawhub] memory-guard is already installed at /usr/local/bin/memory-guard"
CLAWHUB
chmod +x /usr/local/bin/clawhub

echo "[setup] memory-guard CLI installed at /usr/local/bin/memory-guard"
echo "[setup] clawhub stub installed at /usr/local/bin/clawhub"
memory-guard --help || true