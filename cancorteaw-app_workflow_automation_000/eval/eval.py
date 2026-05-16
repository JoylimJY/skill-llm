#!/usr/bin/env python3
"""
Evaluation script for the cancorteaw-app skill task.

Checks:
  1. App directory /home/patron/apps/patientview exists.
  2. Screen file /home/patron/apps/patientview/app/Records.tsx exists and
     contains the title "Patient Records".
  3. Port file /home/patron/apps/_state/patientview.port exists and
     contains 19100 (the custom port, NOT the default 19006).
  4. PID file /home/patron/apps/_state/patientview.pid exists.
  5. The PID recorded is a live process (preview is actually running).
"""

import json
import os
import signal
import sys
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/home/patron/apps"

APPS_ROOT   = Path("/home/patron/apps")
APP_NAME    = "patientview"
SCREEN_NAME = "Records"
EXPECTED_TITLE = "Patient Records"
EXPECTED_PORT  = "19100"

checks = []

def add(name: str, passed: bool, detail: str):
    checks.append({"name": name, "passed": passed, "detail": detail})


# ── Check 1: App directory created ────────────────────────────────────────────
try:
    app_dir = APPS_ROOT / APP_NAME
    exists = app_dir.is_dir()
    add("app_directory_exists",
        exists,
        f"{app_dir} {'exists' if exists else 'NOT FOUND'}")
except Exception as e:
    add("app_directory_exists", False, f"Exception: {e}")


# ── Check 2: Screen file content ──────────────────────────────────────────────
try:
    screen_file = APPS_ROOT / APP_NAME / "app" / f"{SCREEN_NAME}.tsx"
    if not screen_file.is_file():
        add("screen_file_exists", False, f"{screen_file} NOT FOUND")
        add("screen_file_title",  False, "Cannot check title — file missing")
    else:
        content = screen_file.read_text(encoding="utf-8")
        add("screen_file_exists", True, f"{screen_file} exists")
        title_ok = EXPECTED_TITLE in content
        add("screen_file_title",
            title_ok,
            f"Title '{EXPECTED_TITLE}' {'found' if title_ok else 'NOT FOUND'} in Records.tsx")
except Exception as e:
    add("screen_file_exists", False, f"Exception: {e}")
    add("screen_file_title",  False, f"Exception: {e}")


# ── Check 3: Port file contains custom port (19100, not default 19006) ────────
try:
    port_file = APPS_ROOT / "_state" / f"{APP_NAME}.port"
    if not port_file.is_file():
        add("custom_port_file", False, f"{port_file} NOT FOUND")
    else:
        recorded_port = port_file.read_text(encoding="utf-8").strip()
        ok = recorded_port == EXPECTED_PORT
        add("custom_port_file",
            ok,
            f"Port file contains '{recorded_port}', expected '{EXPECTED_PORT}'")
except Exception as e:
    add("custom_port_file", False, f"Exception: {e}")


# ── Check 4: PID file exists ───────────────────────────────────────────────────
try:
    pid_file = APPS_ROOT / "_state" / f"{APP_NAME}.pid"
    if not pid_file.is_file():
        add("pid_file_exists", False, f"{pid_file} NOT FOUND")
        add("preview_process_running", False, "Cannot check process — pid file missing")
    else:
        raw_pid = pid_file.read_text(encoding="utf-8").strip()
        add("pid_file_exists", True, f"PID file exists, contains '{raw_pid}'")

        # ── Check 5: Process is alive ──────────────────────────────────────────
        try:
            pid = int(raw_pid)
            # signal 0 = check existence without sending a signal
            os.kill(pid, 0)
            add("preview_process_running", True, f"Process {pid} is alive")
        except ProcessLookupError:
            add("preview_process_running", False,
                f"Process {raw_pid} does NOT exist (preview not running)")
        except PermissionError:
            # process exists but we can't signal it — still counts as running
            add("preview_process_running", True,
                f"Process {raw_pid} exists (permission-denied on signal 0 → alive)")
        except ValueError:
            add("preview_process_running", False,
                f"PID file content '{raw_pid}' is not a valid integer")
except Exception as e:
    add("pid_file_exists", False, f"Exception: {e}")
    add("preview_process_running", False, f"Exception: {e}")


# ── Aggregate ─────────────────────────────────────────────────────────────────
total  = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score  = round(passed_count / total, 4) if total else 0.0
passed = all(c["passed"] for c in checks)

result = {"passed": passed, "score": score, "checks": checks}
print(json.dumps(result, indent=2))