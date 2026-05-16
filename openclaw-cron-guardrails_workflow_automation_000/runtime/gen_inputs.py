import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "logs/runs",
    "logs/errors",
    "jobs/archived",
    "jobs/drafts",
    "config/channels",
    "config/agents",
    "reports/daily",
    "reports/weekly",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────

# 1. old broken cron spec (wrong pattern)
old_spec = {
    "id": "job-001",
    "schedule": "0 9 * * *",
    "taskType": "main",
    "sessionTarget": "current",
    "delivery": {
        "mode": "systemEvent",
        "channel": "last",
    },
    "timeoutSeconds": 30,
    "note": "morning summary - DO NOT USE, archived"
}
(workspace / "jobs/archived/old_morning_spec.json").write_text(json.dumps(old_spec, indent=2))

# 2. another broken draft
draft_spec = {
    "schedule": "0 8 * * MON-FRI",
    "taskType": "main",
    "payload": {"prompt": "Post weekly KPI summary"},
    "delivery": {"channel": "last"},
    "timeoutSeconds": 60,
}
(workspace / "jobs/drafts/weekly_kpi_draft.json").write_text(json.dumps(draft_spec, indent=2))

# 3. run logs
for i in range(5):
    log = {
        "runId": f"run-{1000+i}",
        "jobId": "job-001",
        "status": "failed",
        "error": "delivery target unresolved: channel=last in multi-channel context",
        "ts": f"2024-05-{10+i:02d}T09:00:00Z"
    }
    (workspace / f"logs/runs/run-{1000+i}.json").write_text(json.dumps(log, indent=2))

# 4. error log
error_log = "\n".join([
    "[ERROR] 2024-05-14T09:00:01Z job-001 delivery-target-ambiguity channel=last resolved to feishu instead of discord",
    "[ERROR] 2024-05-13T09:00:02Z job-001 timeout: job exceeded 30s limit",
    "[WARN]  2024-05-12T09:00:00Z job-001 no explicit 'to' field; skipping delivery",
])
(workspace / "logs/errors/job-001-errors.log").write_text(error_log)

# 5. channel config
discord_channel = {"name": "discord", "id": "discord-primary", "webhook": "https://discord.example.internal/hook/abc123", "type": "discord"}
feishu_channel = {"name": "feishu", "id": "feishu-ops", "webhook": "https://feishu.example.internal/hook/xyz789", "type": "feishu"}
(workspace / "config/channels/discord.json").write_text(json.dumps(discord_channel, indent=2))
(workspace / "config/channels/feishu.json").write_text(json.dumps(feishu_channel, indent=2))

# 6. agent config
agent_cfg = {"agentId": "sre-monitor-agent", "defaultSession": "main", "channels": ["discord", "feishu"]}
(workspace / "config/agents/sre_monitor.json").write_text(json.dumps(agent_cfg, indent=2))

# 7. old reports
for day in ["2024-05-13", "2024-05-14", "2024-05-15"]:
    (workspace / f"reports/daily/summary_{day}.txt").write_text(
        f"Daily SRE report for {day}\nP99 latency: {random.randint(80,200)}ms\nError rate: {random.uniform(0,2):.2f}%\n"
    )

# 8. partial intent file that the agent must recognize as wrong / incomplete
# This is the KEY messy input: a broken normalized intent that uses wrong defaults
broken_intent = {
    "raw": "Every day at 9am post the daily infra health summary to the Discord #sre-alerts channel",
    "parsed": {
        "schedule_nl": "every day at 9am",
        "schedule_cron": "0 9 * * *",
        "tz": "",                        # TRAP: missing timezone
        "task_type": "main",             # TRAP: should be isolated for visible delivery
        "sessionTarget": "current",      # TRAP: wrong for isolated background job
        "payload": {
            "prompt": "Summarize today's infra health and post to SRE alerts"
        },
        "delivery": {
            "mode": "systemEvent",       # TRAP: should be explicit channel delivery
            "channel": "last",           # TRAP: must NOT use 'last' in multi-channel
            "to": ""                     # TRAP: missing explicit destination
        },
        "timeoutSeconds": 45,            # TRAP: too short for non-trivial task
        "label": "daily-infra-summary"
    }
}
(workspace / "jobs/drafts/broken_intent.json").write_text(json.dumps(broken_intent, indent=2))

# 9. a reference note (distractor, not a hint)
(workspace / "references/old_notes.txt").write_text(
    "Various notes from the team:\n"
    "- We moved from single-channel to Discord+Feishu hybrid in Q1 2024\n"
    "- Several jobs broke after the migration\n"
    "- Need to standardize cron job creation process\n"
    "- TODO: fix job-001 and create proper daily summary job\n"
)

# 10. weekly distractor report
(workspace / "reports/weekly/week_20_summary.txt").write_text(
    "Week 20 summary\nTotal incidents: 3\nMTTR: 42 minutes\nOn-call: alice, bob\n"
)

# ── The core skill scripts (mocked as real executables) ──────────────────────
# parse_nl_intent.py
parse_script = '''\
#!/usr/bin/env python3
"""
parse_nl_intent.py - Parses a natural-language cron intent description.

Usage:
    python scripts/parse_nl_intent.py --input <path_to_raw_or_intent_json> --output <output_path>

Reads either:
  - a plain text file containing a natural-language request
  - a JSON file with a "raw" field (natural-language string)

Writes a normalized intent JSON to --output.

The normalized intent schema:
{
  "raw": str,
  "parsed": {
    "schedule_nl": str,
    "schedule_cron": str,   // standard cron expression
    "tz": str,              // IANA timezone string, e.g. "America/New_York"
    "task_type": str,       // "main" or "isolated"
    "sessionTarget": str,   // "current" | "none" | explicit session id
    "payload": {
      "prompt": str
    },
    "delivery": {
      "mode": str,          // "systemEvent" | "channel" | "none"
      "channel": str,       // explicit channel name, NOT "last"
      "to": str             // explicit destination id/address
    },
    "timeoutSeconds": int,
    "label": str
  }
}

Classification rules applied by this parser:
- If the raw text mentions posting/publishing/delivering to a named channel → task_type=isolated, delivery.mode=channel
- If the raw text is a reminder → task_type=main, delivery.mode=systemEvent
- If the raw text is a background worker/scan → task_type=isolated, delivery.mode=none
- Never sets channel="last" in output
- Always attempts to extract timezone; leaves tz="" if not detected (caller must fill)
- timeoutSeconds defaults to 180 for non-trivial tasks, 60 for simple reminders
'''

parse_nl_code = '''\
#!/usr/bin/env python3
import argparse
import json
import sys
import re
from pathlib import Path

def parse_nl(raw_text: str) -> dict:
    raw = raw_text.strip()
    lower = raw.lower()

    # Detect task classification
    is_visible_delivery = any(w in lower for w in [
        "post", "publish", "send", "deliver", "announce", "share",
        "discord", "feishu", "slack", "teams", "telegram", "channel"
    ])
    is_reminder = any(w in lower for w in ["remind", "reminder", "nudge", "alert me", "notify me"])
    is_worker = any(w in lower for w in ["scan", "nightly", "background", "worker", "maintenance", "sweep"])

    # Schedule extraction (simple heuristics)
    schedule_cron = ""
    schedule_nl = ""
    tz = ""

    if "every day at 9" in lower or "daily at 9" in lower or "9am" in lower:
        schedule_cron = "0 9 * * *"
        schedule_nl = "every day at 9am"
    elif "every day at 8" in lower or "8am" in lower:
        schedule_cron = "0 8 * * *"
        schedule_nl = "every day at 8am"
    elif "every hour" in lower:
        schedule_cron = "0 * * * *"
        schedule_nl = "every hour"
    elif "every 10 minutes" in lower:
        schedule_cron = "*/10 * * * *"
        schedule_nl = "every 10 minutes"
    elif "nightly" in lower or "midnight" in lower:
        schedule_cron = "0 0 * * *"
        schedule_nl = "nightly at midnight"
    elif "every morning" in lower:
        schedule_cron = "0 9 * * *"
        schedule_nl = "every morning"

    # Timezone detection
    tz_patterns = [
        (r"\\butc\\b", "UTC"),
        (r"america/new_york|new york|eastern|est|edt", "America/New_York"),
        (r"america/los_angeles|pacific|pst|pdt|los angeles", "America/Los_Angeles"),
        (r"europe/london|london|bst|gmt", "Europe/London"),
        (r"asia/shanghai|shanghai|cst|beijing|china", "Asia/Shanghai"),
        (r"asia/tokyo|tokyo|jst|japan", "Asia/Tokyo"),
    ]
    for pattern, tzname in tz_patterns:
        if re.search(pattern, lower):
            tz = tzname
            break

    # Channel extraction
    channel = ""
    to_dest = ""
    if "discord" in lower:
        channel = "discord"
        # Extract #channel-name if present
        match = re.search(r"#([\w-]+)", raw)
        if match:
            to_dest = match.group(1)
    elif "feishu" in lower:
        channel = "feishu"
    elif "slack" in lower:
        channel = "slack"

    # Delivery mode
    if is_visible_delivery:
        delivery_mode = "channel"
        task_type = "isolated"
        session_target = "none"
        timeout = 180
    elif is_worker:
        delivery_mode = "none"
        task_type = "isolated"
        session_target = "none"
        timeout = 300
    else:
        delivery_mode = "systemEvent"
        task_type = "main"
        session_target = "current"
        timeout = 60

    # Extract label
    label_words = [w for w in lower.split() if len(w) > 4 and w not in
                   ("every", "daily", "remind", "please", "could", "should", "would", "about", "after", "before")]
    label = "-".join(label_words[:4]) if label_words else "scheduled-job"

    # Extract prompt from raw
    prompt = raw

    return {
        "raw": raw,
        "parsed": {
            "schedule_nl": schedule_nl,
            "schedule_cron": schedule_cron,
            "tz": tz,
            "task_type": task_type,
            "sessionTarget": session_target,
            "payload": {"prompt": prompt},
            "delivery": {
                "mode": delivery_mode,
                "channel": channel,
                "to": to_dest,
            },
            "timeoutSeconds": timeout,
            "label": label,
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Parse natural-language cron intent")
    parser.add_argument("--input", required=True, help="Path to raw text or intent JSON file")
    parser.add_argument("--output", required=True, help="Path to write normalized intent JSON")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    content = input_path.read_text().strip()

    # Try JSON first
    try:
        data = json.loads(content)
        if "raw" in data:
            raw_text = data["raw"]
        elif "parsed" in data:
            # Already parsed, just re-emit
            result = data
            Path(args.output).write_text(json.dumps(result, indent=2))
            print(f"OK intent written to {args.output}")
            return
        else:
            raw_text = content
    except json.JSONDecodeError:
        raw_text = content

    result = parse_nl(raw_text)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2))
    print(f"OK intent written to {args.output}")


if __name__ == "__main__":
    main()
'''

(workspace / "scripts/parse_nl_intent.py").write_text(parse_nl_code)

# intent_to_cron_spec.py
intent_to_spec_code = '''\
#!/usr/bin/env python3
"""
intent_to_cron_spec.py - Converts a normalized intent JSON to a full cron spec JSON.

Usage:
    python scripts/intent_to_cron_spec.py --input <normalized_intent.json> --output <cron_spec.json>

Input: normalized intent JSON (output of parse_nl_intent.py or hand-edited)
Output: cron spec JSON

Cron spec schema:
{
  "version": "1",
  "id": str,              // generated from label + hash
  "label": str,
  "schedule": {
    "cron": str,          // standard cron expression
    "tz": str             // IANA timezone, REQUIRED for wall-clock schedules
  },
  "runtime": {
    "taskType": str,      // "main" | "isolated"
    "sessionTarget": str, // "current" | "none" | explicit session id
    "timeoutSeconds": int
  },
  "payload": {
    "kind": str,          // "prompt"
    "prompt": str
  },
  "delivery": {
    "mode": str,          // "systemEvent" | "channel" | "none"
    "channel": str,       // required if mode=channel; must NOT be "last"
    "to": str             // required if mode=channel
  }
}

Validation rules enforced:
- if delivery.mode == "channel": channel must not be empty or "last", to must not be empty
- if taskType == "isolated" and delivery.mode == "channel": sessionTarget must be "none"
- timeoutSeconds must be >= 180 for non-trivial tasks (taskType=isolated or complex prompts)
- tz must not be empty for wall-clock schedules (any cron with fixed hour)
- version must be "1"
"""

import argparse
import json
import hashlib
import sys
from pathlib import Path


def intent_to_spec(intent: dict) -> dict:
    parsed = intent.get("parsed", intent)

    label = parsed.get("label", "scheduled-job")
    hash_suffix = hashlib.md5(label.encode()).hexdigest()[:6]
    job_id = f"job-{label[:20].replace(' ', '-')}-{hash_suffix}"

    schedule_cron = parsed.get("schedule_cron", "")
    tz = parsed.get("tz", "")

    task_type = parsed.get("task_type", "isolated")
    session_target = parsed.get("sessionTarget", "none")
    timeout = parsed.get("timeoutSeconds", 180)

    payload = parsed.get("payload", {})
    prompt = payload.get("prompt", "") if isinstance(payload, dict) else str(payload)

    delivery = parsed.get("delivery", {})
    delivery_mode = delivery.get("mode", "none")
    delivery_channel = delivery.get("channel", "")
    delivery_to = delivery.get("to", "")

    spec = {
        "version": "1",
        "id": job_id,
        "label": label,
        "schedule": {
            "cron": schedule_cron,
            "tz": tz,
        },
        "runtime": {
            "taskType": task_type,
            "sessionTarget": session_target,
            "timeoutSeconds": timeout,
        },
        "payload": {
            "kind": "prompt",
            "prompt": prompt,
        },
        "delivery": {
            "mode": delivery_mode,
            "channel": delivery_channel,
            "to": delivery_to,
        }
    }

    return spec


def main():
    parser = argparse.ArgumentParser(description="Convert normalized intent to cron spec")
    parser.add_argument("--input", required=True, help="Path to normalized intent JSON")
    parser.add_argument("--output", required=True, help="Path to write cron spec JSON")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    intent = json.loads(input_path.read_text())
    spec = intent_to_spec(intent)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(spec, indent=2))
    print(f"OK spec written to {args.output}")


if __name__ == "__main__":
    main()
'''

(workspace / "scripts/intent_to_cron_spec.py").write_text(intent_to_spec_code)

# validate_cron_spec.py
validate_code = '''\
#!/usr/bin/env python3
"""
validate_cron_spec.py - Validates a cron spec JSON against OpenClaw guardrail rules.

Usage:
    python scripts/validate_cron_spec.py --spec <cron_spec.json> [--report <report.json>]

Exit codes:
    0 = valid
    1 = invalid (prints errors)
    2 = file not found or parse error

Validation rules:
1. version must be "1"
2. schedule.cron must not be empty
3. schedule.tz must not be empty (required for wall-clock schedules with fixed hour)
4. runtime.taskType must be "main" or "isolated"
5. runtime.timeoutSeconds must be >= 180 for taskType=isolated, >= 60 for taskType=main
6. if delivery.mode == "channel":
   a. delivery.channel must not be empty and must not be "last"
   b. delivery.to must not be empty
   c. runtime.sessionTarget must be "none" (isolated jobs must not use current session)
7. if delivery.mode == "systemEvent":
   a. runtime.taskType must be "main"
8. if delivery.mode == "none":
   a. runtime.taskType must be "isolated"
9. payload.kind must be "prompt"
10. payload.prompt must not be empty
"""

import argparse
import json
import sys
from pathlib import Path


def validate(spec: dict) -> list:
    errors = []

    # Rule 1
    if spec.get("version") != "1":
        errors.append("version must be \\"1\\"")

    # Rule 2
    sched = spec.get("schedule", {})
    if not sched.get("cron", "").strip():
        errors.append("schedule.cron must not be empty")

    # Rule 3: tz required for wall-clock cron
    cron_expr = sched.get("cron", "")
    tz = sched.get("tz", "").strip()
    if cron_expr:
        parts = cron_expr.split()
        if len(parts) >= 2 and parts[1].isdigit():
            if not tz:
                errors.append("schedule.tz must not be empty for wall-clock schedules (cron has fixed hour)")

    runtime = spec.get("runtime", {})
    task_type = runtime.get("taskType", "")
    session_target = runtime.get("sessionTarget", "")
    timeout = runtime.get("timeoutSeconds", 0)

    # Rule 4
    if task_type not in ("main", "isolated"):
        errors.append(f"runtime.taskType must be \\"main\\" or \\"isolated\\", got: {task_type!r}")

    # Rule 5
    if task_type == "isolated" and timeout < 180:
        errors.append(f"runtime.timeoutSeconds must be >= 180 for isolated tasks, got: {timeout}")
    elif task_type == "main" and timeout < 60:
        errors.append(f"runtime.timeoutSeconds must be >= 60 for main tasks, got: {timeout}")

    delivery = spec.get("delivery", {})
    mode = delivery.get("mode", "")
    channel = delivery.get("channel", "")
    to_dest = delivery.get("to", "")

    # Rule 6
    if mode == "channel":
        if not channel or channel == "last":
            errors.append("delivery.channel must not be empty or \\"last\\" when mode=channel")
        if not to_dest:
            errors.append("delivery.to must not be empty when mode=channel")
        if session_target != "none":
            errors.append(f"runtime.sessionTarget must be \\"none\\" for isolated channel delivery, got: {session_target!r}")

    # Rule 7
    if mode == "systemEvent" and task_type != "main":
        errors.append("delivery.mode=systemEvent requires runtime.taskType=\\"main\\"")

    # Rule 8
    if mode == "none" and task_type != "isolated":
        errors.append("delivery.mode=none requires runtime.taskType=\\"isolated\\"")

    # Rule 9
    payload = spec.get("payload", {})
    if payload.get("kind") != "prompt":
        errors.append("payload.kind must be \\"prompt\\"")

    # Rule 10
    if not payload.get("prompt", "").strip():
        errors.append("payload.prompt must not be empty")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate cron spec JSON")
    parser.add_argument("--spec", required=True, help="Path to cron spec JSON")
    parser.add_argument("--report", default="", help="Optional: path to write validation report JSON")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"ERROR: spec file not found: {spec_path}", file=sys.stderr)
        sys.exit(2)

    try:
        spec = json.loads(spec_path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
        sys.exit(2)

    errors = validate(spec)

    report = {
        "spec_path": str(spec_path),
        "valid": len(errors) == 0,
        "errors": errors,
    }

    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(report, indent=2))

    if errors:
        print("INVALID spec:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("OK spec is valid")
        sys.exit(0)


if __name__ == "__main__":
    main()
'''

(workspace / "scripts/validate_cron_spec.py").write_text(validate_code)

# render_cron_command.py
render_code = '''\
#!/usr/bin/env python3
"""
render_cron_command.py - Renders a validated cron spec into the openclaw CLI command string.

Usage:
    python scripts/render_cron_command.py --spec <cron_spec.json> [--output <command.txt>]

Output: openclaw cron add command string.

Rendering rules:
- always include --tz
- always include --task-type
- always include --timeout
- if delivery.mode == channel: include --delivery-channel and --delivery-to
- if delivery.mode == systemEvent: include --delivery systemEvent
- if delivery.mode == none: include --delivery none
- always include --session-target
- always include --label
"""

import argparse
import json
import sys
import shlex
from pathlib import Path


def render(spec: dict) -> str:
    sched = spec.get("schedule", {})
    runtime = spec.get("runtime", {})
    payload = spec.get("payload", {})
    delivery = spec.get("delivery", {})

    parts = ["openclaw cron add"]

    parts.append(f"--label {shlex.quote(spec.get(\\'label\\', \\'job\\'))}")
    parts.append(f"--cron {shlex.quote(sched.get(\\'cron\\', \\'\\'))}")
    parts.append(f"--tz {shlex.quote(sched.get(\\'tz\\', \\'UTC\\'))}")
    parts.append(f"--task-type {shlex.quote(runtime.get(\\'taskType\\', \\'isolated\\'))}")
    parts.append(f"--session-target {shlex.quote(runtime.get(\\'sessionTarget\\', \\'none\\'))}")
    parts.append(f"--timeout {runtime.get(\\'timeoutSeconds\\', 180)}")

    mode = delivery.get("mode", "none")
    if mode == "channel":
        parts.append(f"--delivery channel")
        parts.append(f"--delivery-channel {shlex.quote(delivery.get(\\'channel\\', \\'\\'))}")
        parts.append(f"--delivery-to {shlex.quote(delivery.get(\\'to\\', \\'\\'))}")
    elif mode == "systemEvent":
        parts.append("--delivery systemEvent")
    else:
        parts.append("--delivery none")

    parts.append(f"--prompt {shlex.quote(payload.get(\\'prompt\\', \\'\\'))}")

    return " ".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Render cron spec to openclaw command")
    parser.add_argument("--spec", required=True, help="Path to validated cron spec JSON")
    parser.add_argument("--output", default="", help="Optional: path to write rendered command")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"ERROR: spec file not found: {spec_path}", file=sys.stderr)
        sys.exit(1)

    spec = json.loads(spec_path.read_text())
    cmd = render(spec)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(cmd + "\\n")
        print(f"OK command written to {args.output}")
    else:
        print(cmd)


if __name__ == "__main__":
    main()
'''

# Fix the escaped quotes issue in render_code
render_code_fixed = '''\
#!/usr/bin/env python3
"""
render_cron_command.py - Renders a validated cron spec into the openclaw CLI command string.

Usage:
    python scripts/render_cron_command.py --spec <cron_spec.json> [--output <command.txt>]

Output: openclaw cron add command string.
"""

import argparse
import json
import sys
import shlex
from pathlib import Path


def render(spec: dict) -> str:
    sched = spec.get("schedule", {})
    runtime = spec.get("runtime", {})
    payload = spec.get("payload", {})
    delivery = spec.get("delivery", {})

    parts = ["openclaw cron add"]
    parts.append("--label " + shlex.quote(spec.get("label", "job")))
    parts.append("--cron " + shlex.quote(sched.get("cron", "")))
    parts.append("--tz " + shlex.quote(sched.get("tz", "UTC")))
    parts.append("--task-type " + shlex.quote(runtime.get("taskType", "isolated")))
    parts.append("--session-target " + shlex.quote(runtime.get("sessionTarget", "none")))
    parts.append("--timeout " + str(runtime.get("timeoutSeconds", 180)))

    mode = delivery.get("mode", "none")
    if mode == "channel":
        parts.append("--delivery channel")
        parts.append("--delivery-channel " + shlex.quote(delivery.get("channel", "")))
        parts.append("--delivery-to " + shlex.quote(delivery.get("to", "")))
    elif mode == "systemEvent":
        parts.append("--delivery systemEvent")
    else:
        parts.append("--delivery none")

    parts.append("--prompt " + shlex.quote(payload.get("prompt", "")))
    return " ".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Render cron spec to openclaw command")
    parser.add_argument("--spec", required=True, help="Path to validated cron spec JSON")
    parser.add_argument("--output", default="", help="Optional: path to write rendered command")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"ERROR: spec file not found: {spec_path}", file=sys.stderr)
        sys.exit(1)

    spec = json.loads(spec_path.read_text())
    cmd = render(spec)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(cmd + "\\n")
        print(f"OK command written to {args.output}")
    else:
        print(cmd)


if __name__ == "__main__":
    main()
'''

(workspace / "scripts/render_cron_command.py").write_text(render_code_fixed)

# create_cron.py (stub - simulates creation)
create_code = '''\
#!/usr/bin/env python3
"""
create_cron.py - Simulates submitting a validated cron spec to OpenClaw.

Usage:
    python scripts/create_cron.py --spec <validated_cron_spec.json> [--dry-run]

With --dry-run: prints what would be submitted, does not create.
Without --dry-run: writes a simulated job record to jobs/created/<id>.json

Exit codes:
    0 = success
    1 = validation failed or spec error
"""

import argparse
import json
import sys
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description="Submit cron spec to OpenClaw")
    parser.add_argument("--spec", required=True, help="Path to validated cron spec JSON")
    parser.add_argument("--dry-run", action="store_true", help="Print without creating")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"ERROR: spec file not found: {spec_path}", file=sys.stderr)
        sys.exit(1)

    try:
        spec = json.loads(spec_path.read_text())
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate first
    val_result = subprocess.run(
        ["python3", "scripts/validate_cron_spec.py", "--spec", str(spec_path)],
        capture_output=True, text=True
    )
    if val_result.returncode != 0:
        print("ERROR: spec failed validation:")
        print(val_result.stdout)
        sys.exit(1)

    if args.dry_run:
        print("DRY RUN - would submit:")
        print(json.dumps(spec, indent=2))
        return

    job_id = spec.get("id", "unknown")
    out_dir = Path("jobs/created")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{job_id}.json"

    record = {**spec, "_status": "created", "_simulated": True}
    out_file.write_text(json.dumps(record, indent=2))
    print(f"OK job created: {job_id}")
    print(f"   record written to {out_file}")


if __name__ == "__main__":
    main()
'''
(workspace / "scripts/create_cron.py").write_text(create_code)

# lint_existing_crons.py
lint_code = '''\
#!/usr/bin/env python3
"""
lint_existing_crons.py - Scans a directory for cron spec JSON files and reports issues.

Usage:
    python scripts/lint_existing_crons.py --dir <directory> [--report <report.json>]
"""

import argparse
import json
import sys
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True)
    parser.add_argument("--report", default="")
    args = parser.parse_args()

    scan_dir = Path(args.dir)
    results = []

    for spec_file in scan_dir.rglob("*.json"):
        try:
            spec = json.loads(spec_file.read_text())
        except Exception:
            results.append({"file": str(spec_file), "valid": False, "errors": ["invalid JSON"]})
            continue

        val = subprocess.run(
            ["python3", "scripts/validate_cron_spec.py", "--spec", str(spec_file)],
            capture_output=True, text=True
        )
        valid = val.returncode == 0
        errors = [line.strip() for line in val.stdout.splitlines() if line.strip().startswith("-")]
        results.append({"file": str(spec_file), "valid": valid, "errors": errors})

    report = {"scanned": len(results), "results": results}

    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(report, indent=2))

    for r in results:
        status = "OK" if r["valid"] else "FAIL"
        print(f"[{status}] {r[\\'file\\']}")
        for e in r.get("errors", []):
            print(f"       {e}")


if __name__ == "__main__":
    main()
'''

lint_code_fixed = '''\
#!/usr/bin/env python3
"""
lint_existing_crons.py - Scans a directory for cron spec JSON files and reports issues.

Usage:
    python scripts/lint_existing_crons.py --dir <directory> [--report <report.json>]
"""

import argparse
import json
import sys
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True)
    parser.add_argument("--report", default="")
    args = parser.parse_args()

    scan_dir = Path(args.dir)
    results = []

    for spec_file in scan_dir.rglob("*.json"):
        try:
            spec = json.loads(spec_file.read_text())
        except Exception:
            results.append({"file": str(spec_file), "valid": False, "errors": ["invalid JSON"]})
            continue

        val = subprocess.run(
            ["python3", "scripts/validate_cron_spec.py", "--spec", str(spec_file)],
            capture_output=True, text=True
        )
        valid = val.returncode == 0
        errors = [line.strip() for line in val.stdout.splitlines() if line.strip().startswith("-")]
        results.append({"file": str(spec_file), "valid": valid, "errors": errors})

    report = {"scanned": len(results), "results": results}

    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(report, indent=2))

    for r in results:
        status = "OK" if r["valid"] else "FAIL"
        print(f"[{status}] {r['file']}")
        for e in r.get("errors", []):
            print(f"       {e}")


if __name__ == "__main__":
    main()
'''
(workspace / "scripts/lint_existing_crons.py").write_text(lint_code_fixed)

# cron_doctor.py
doctor_code = '''\
#!/usr/bin/env python3
"""
cron_doctor.py - Diagnoses a cron spec file and suggests fixes.

Usage:
    python scripts/cron_doctor.py --spec <cron_spec.json> [--fix] [--output <fixed_spec.json>]

With --fix: attempts to auto-repair common issues and writes fixed spec to --output.

Repair rules:
- If delivery.channel == "last" or empty and mode == "channel": flag as needs-manual-fix
- If timeoutSeconds < 180 and taskType == "isolated": set to 180
- If tz is empty and cron has fixed hour: flag as needs-manual-fix
- If sessionTarget != "none" and taskType == "isolated" and mode == "channel": set sessionTarget="none"
- If mode == "systemEvent" and taskType != "main": set taskType="main"
- If mode == "none" and taskType != "isolated": set taskType="isolated"
"""

import argparse
import json
import copy
from pathlib import Path


FIXABLE = []
MANUAL = []


def doctor(spec: dict, auto_fix: bool = False) -> tuple:
    fixed = copy.deepcopy(spec)
    issues = []
    fixed_items = []
    manual_items = []

    runtime = fixed.get("runtime", {})
    delivery = fixed.get("delivery", {})
    sched = fixed.get("schedule", {})

    # timeout fix
    if runtime.get("taskType") == "isolated" and runtime.get("timeoutSeconds", 0) < 180:
        old = runtime["timeoutSeconds"]
        if auto_fix:
            fixed["runtime"]["timeoutSeconds"] = 180
            fixed_items.append(f"timeoutSeconds: {old} -> 180")
        else:
            issues.append(f"timeoutSeconds too short ({old}) for isolated task")

    # sessionTarget fix
    if (runtime.get("taskType") == "isolated"
            and delivery.get("mode") == "channel"
            and runtime.get("sessionTarget") != "none"):
        old = runtime["sessionTarget"]
        if auto_fix:
            fixed["runtime"]["sessionTarget"] = "none"
            fixed_items.append(f"sessionTarget: {old!r} -> 'none'")
        else:
            issues.append(f"sessionTarget={old!r} must be 'none' for isolated channel delivery")

    # channel=last fix (needs manual)
    if delivery.get("mode") == "channel" and delivery.get("channel") in ("last", "", None):
        manual_items.append("delivery.channel is 'last' or empty: must be set to explicit channel name")

    # to empty (needs manual)
    if delivery.get("mode") == "channel" and not delivery.get("to", "").strip():
        manual_items.append("delivery.to is empty: must be set to explicit destination")

    # tz empty
    cron_expr = sched.get("cron", "")
    tz = sched.get("tz", "")
    if cron_expr:
        parts = cron_expr.split()
        if len(parts) >= 2 and parts[1].isdigit() and not tz.strip():
            manual_items.append("schedule.tz is empty: must set explicit IANA timezone for wall-clock schedule")

    # mode/taskType consistency
    mode = delivery.get("mode", "")
    task_type = runtime.get("taskType", "")
    if mode == "systemEvent" and task_type != "main":
        if auto_fix:
            fixed["runtime"]["taskType"] = "main"
            fixed_items.append(f"taskType: {task_type!r} -> 'main' (systemEvent requires main)")
        else:
            issues.append("systemEvent delivery requires taskType=main")

    if mode == "none" and task_type != "isolated":
        if auto_fix:
            fixed["runtime"]["taskType"] = "isolated"
            fixed_items.append(f"taskType: {task_type!r} -> 'isolated' (no-deliver requires isolated)")
        else:
            issues.append("delivery=none requires taskType=isolated")

    return fixed, issues, fixed_items, manual_items


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    spec = json.loads(spec_path.read_text())

    fixed, issues, fixed_items, manual_items = doctor(spec, auto_fix=args.fix)

    if issues:
        print("ISSUES FOUND:")
        for i in issues:
            print(f"  - {i}")

    if fixed_items:
        print("AUTO-FIXED:")
        for f in fixed_items:
            print(f"  + {f}")

    if manual_items:
        print("NEEDS MANUAL FIX:")
        for m in manual_items:
            print(f"  ! {m}")

    if not issues and not fixed_items and not manual_items:
        print("OK no issues found")

    if args.fix and args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(fixed, indent=2))
        print(f"Fixed spec written to {args.output}")


if __name__ == "__main__":
    main()
'''
(workspace / "scripts/cron_doctor.py").write_text(doctor_code)

# cron_fix.py
fix_code = '''\
#!/usr/bin/env python3
"""
cron_fix.py - Interactive repair for a broken cron spec.

Usage:
    python scripts/cron_fix.py --spec <broken_spec.json> --output <fixed_spec.json> [--channel <name>] [--to <dest>] [--tz <iana_tz>]

Applies targeted fixes:
- --channel: sets delivery.channel (replaces "last" or empty)
- --to: sets delivery.to
- --tz: sets schedule.tz
- Always sets delivery.mode="channel" if channel is provided
- Always sets runtime.taskType="isolated" if delivery.mode="channel"
- Always sets runtime.sessionTarget="none" if delivery.mode="channel"
- Ensures timeoutSeconds >= 180 for isolated tasks
"""

import argparse
import json
import copy
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--channel", default="")
    parser.add_argument("--to", default="")
    parser.add_argument("--tz", default="")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    spec = json.loads(spec_path.read_text())
    fixed = copy.deepcopy(spec)

    if args.tz:
        fixed.setdefault("schedule", {})["tz"] = args.tz

    if args.channel:
        fixed.setdefault("delivery", {})["channel"] = args.channel
        fixed["delivery"]["mode"] = "channel"
        fixed.setdefault("runtime", {})["taskType"] = "isolated"
        fixed["runtime"]["sessionTarget"] = "none"
        if fixed["runtime"].get("timeoutSeconds", 0) < 180:
            fixed["runtime"]["timeoutSeconds"] = 180

    if args.to:
        fixed.setdefault("delivery", {})["to"] = args.to

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(fixed, indent=2))
    print(f"OK fixed spec written to {args.output}")


if __name__ == "__main__":
    main()
'''
(workspace / "scripts/cron_fix.py").write_text(fix_code)

# Make all scripts executable markers
for f in (workspace / "scripts").iterdir():
    print(f"Created script: {f}")

print("Workspace generation complete.")
print(f"Key test input: {workspace}/jobs/drafts/broken_intent.json")