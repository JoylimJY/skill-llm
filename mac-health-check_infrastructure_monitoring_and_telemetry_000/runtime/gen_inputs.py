#!/usr/bin/env python3
"""
Generate the sandbox workspace for the mac-health-check skill evaluation.
Creates the skill directory structure with scripts, distractor files,
and a messy multi-line JSONL telemetry dump.
"""

import json
import os
import random
import sys
from pathlib import Path

random.seed(42)

def create_workspace(workspace: str):
    ws = Path(workspace)
    ws.mkdir(parents=True, exist_ok=True)

    # ── Skill directory structure (simulates ~/.openclaw/skills/mac-health-check)
    skill_root = ws / "skills" / "mac-health-check"
    (skill_root / "bin").mkdir(parents=True, exist_ok=True)
    (skill_root / "scripts").mkdir(parents=True, exist_ok=True)
    (skill_root / "references").mkdir(parents=True, exist_ok=True)

    # ── macmon-safe.sh wrapper (stub — not actually called in --input mode)
    macmon_safe = skill_root / "bin" / "macmon-safe.sh"
    macmon_safe.write_text(
        '#!/usr/bin/env bash\n'
        '# Wrapper: retries macmon through zsh -lic when needed\n'
        'if command -v macmon &>/dev/null; then\n'
        '  macmon "$@"\n'
        'else\n'
        '  zsh -lic "macmon $*" 2>/dev/null\n'
        'fi\n'
    )

    # ── The real macmon_status.py script
    # This is described as already existing in the skill workspace per SKILL.md
    macmon_status_py = skill_root / "scripts" / "macmon_status.py"
    macmon_status_py.write_text(r'''#!/usr/bin/env python3
"""
macmon_status.py – parse macmon JSONL output and produce a health summary.

Usage:
  python macmon_status.py                        # live mode (runs macmon -i 200)
  python macmon_status.py --input /tmp/out.jsonl # from file
  python macmon_status.py --input -              # from stdin
  python macmon_status.py --format json --pretty # JSON output
"""

import argparse
import json
import subprocess
import sys


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", "-f", default=None,
                   help="Path to macmon JSONL file, or '-' for stdin")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--pretty", action="store_true")
    return p.parse_args()


def read_last_sample(source):
    """Return the last non-empty JSON line from source (file path or '-')."""
    if source == "-":
        lines = sys.stdin.read().splitlines()
    else:
        with open(source, "r") as fh:
            lines = fh.read().splitlines()

    last = None
    for line in lines:
        stripped = line.strip()
        if stripped:
            try:
                last = json.loads(stripped)
            except json.JSONDecodeError:
                pass
    if last is None:
        raise ValueError("No valid JSON line found in input")
    return last


def run_live():
    result = subprocess.run(
        ["macmon", "pipe", "-s", "1", "-i", "200"],
        capture_output=True, text=True, timeout=10
    )
    lines = result.stdout.strip().splitlines()
    for line in reversed(lines):
        if line.strip():
            return json.loads(line.strip())
    raise RuntimeError("macmon produced no output")


def summarise(sample: dict) -> dict:
    temp = sample.get("temp", {})
    mem  = sample.get("memory", {})

    pcpu = sample.get("pcpu_usage", [0, 0])
    ecpu = sample.get("ecpu_usage", [0, 0])
    gpu  = sample.get("gpu_usage",  [0, 0])

    ram_total = mem.get("ram_total", 0)
    ram_usage = mem.get("ram_usage", 0)
    swap_total = mem.get("swap_total", 0)
    swap_usage = mem.get("swap_usage", 0)

    summary = {
        "cpu_temp_c":      round(temp.get("cpu_temp_avg", 0), 1),
        "gpu_temp_c":      round(temp.get("gpu_temp_avg", 0), 1),
        "pcpu_mhz":        pcpu[0],
        "pcpu_pct":        round(pcpu[1] * 100, 1),
        "ecpu_mhz":        ecpu[0],
        "ecpu_pct":        round(ecpu[1] * 100, 1),
        "gpu_mhz":         gpu[0],
        "gpu_pct":         round(gpu[1] * 100, 1),
        "sys_power_w":     round(sample.get("sys_power", 0), 2),
        "cpu_power_w":     round(sample.get("cpu_power", 0), 2),
        "gpu_power_w":     round(sample.get("gpu_power", 0), 2),
        "ram_total_gb":    round(ram_total / 1e9, 2),
        "ram_usage_gb":    round(ram_usage / 1e9, 2),
        "swap_total_gb":   round(swap_total / 1e9, 2),
        "swap_usage_gb":   round(swap_usage / 1e9, 2),
        "timestamp":       sample.get("timestamp", None),
    }
    return summary


def interpret(summary: dict) -> str:
    notes = []
    cpu_t = summary["cpu_temp_c"]
    if cpu_t < 60:
        notes.append("CPU temperature is calm (under 60C).")
    elif cpu_t < 85:
        notes.append("CPU temperature is in normal active range (60–85C).")
    else:
        notes.append("CPU temperature is hot (85C+); possible thermal pressure.")

    if summary["swap_usage_gb"] > 0:
        notes.append("Swap is in use; memory pressure may be starting.")
    else:
        notes.append("No swap in use; memory is comfortable.")

    if summary["sys_power_w"] > 30 and cpu_t > 70:
        notes.append("High system power combined with elevated temps suggests sustained workload.")

    return " ".join(notes)


def main():
    args = parse_args()

    if args.input:
        sample = read_last_sample(args.input)
    else:
        try:
            sample = run_live()
        except Exception as exc:
            print(f"ERROR: could not run macmon live: {exc}", file=sys.stderr)
            sys.exit(1)

    summary = summarise(sample)
    summary["interpretation"] = interpret(summary)

    if args.format == "json":
        if args.pretty:
            print(json.dumps(summary, indent=2))
        else:
            print(json.dumps(summary))
    else:
        # Text output
        print(f"CPU temp:      {summary['cpu_temp_c']} C")
        print(f"GPU temp:      {summary['gpu_temp_c']} C")
        print(f"P-CPU:         {summary['pcpu_pct']}% @ {summary['pcpu_mhz']} MHz")
        print(f"E-CPU:         {summary['ecpu_pct']}% @ {summary['ecpu_mhz']} MHz")
        print(f"GPU:           {summary['gpu_pct']}% @ {summary['gpu_mhz']} MHz")
        print(f"System power:  {summary['sys_power_w']} W")
        print(f"CPU power:     {summary['cpu_power_w']} W")
        print(f"GPU power:     {summary['gpu_power_w']} W")
        print(f"RAM:           {summary['ram_usage_gb']} / {summary['ram_total_gb']} GB")
        print(f"Swap:          {summary['swap_usage_gb']} / {summary['swap_total_gb']} GB")
        print()
        print("Interpretation:", summary["interpretation"])


if __name__ == "__main__":
    main()
''')

    # ── sample-output.md reference file
    ref = skill_root / "references" / "sample-output.md"
    ref.write_text(
        "# Sample macmon JSON fields\n\n"
        "Example fields commonly seen from `macmon pipe -s 1`:\n\n"
        "- `temp.cpu_temp_avg`\n"
        "- `temp.gpu_temp_avg`\n"
        "- `pcpu_usage`: `[mhz, fraction]`\n"
        "- `ecpu_usage`: `[mhz, fraction]`\n"
        "- `gpu_usage`: `[mhz, fraction]`\n"
        "- `memory.ram_total`\n"
        "- `memory.ram_usage`\n"
        "- `memory.swap_total`\n"
        "- `memory.swap_usage`\n"
        "- `sys_power`\n"
        "- `cpu_power`\n"
        "- `gpu_power`\n"
        "- `timestamp`\n\n"
        "Fractions in usage pairs are in the `0..1` range and should usually be shown as percentages.\n"
    )

    # ── Distractor files to increase realism and test contextual awareness

    # Distractor 1: old CI config
    ci_dir = ws / "ci" / "configs"
    ci_dir.mkdir(parents=True, exist_ok=True)
    (ci_dir / "build-matrix.yml").write_text(
        "builds:\n  - os: macos-14\n    arch: arm64\n  - os: macos-13\n    arch: x86_64\n"
    )
    (ci_dir / "runner-tags.json").write_text(
        json.dumps({"mac-mini-m2": ["arm64", "macos14"], "mac-mini-m1": ["arm64", "macos13"]}, indent=2)
    )

    # Distractor 2: old telemetry files (wrong format, red herrings)
    telemetry_dir = ws / "telemetry" / "archive"
    telemetry_dir.mkdir(parents=True, exist_ok=True)

    # This file uses the FIRST-line-only anti-pattern (red herring values)
    old_sample_first_line = {
        "timestamp": 1700000000,
        "temp": {"cpu_temp_avg": 42.0, "gpu_temp_avg": 38.0},
        "pcpu_usage": [600, 0.05],
        "ecpu_usage": [1200, 0.03],
        "gpu_usage": [400, 0.02],
        "sys_power": 8.5,
        "cpu_power": 3.2,
        "gpu_power": 1.1,
        "memory": {
            "ram_total": 17179869184,
            "ram_usage": 2147483648,
            "swap_total": 2147483648,
            "swap_usage": 0
        }
    }
    (telemetry_dir / "2023-11-sample.jsonl").write_text(json.dumps(old_sample_first_line) + "\n")

    # Distractor 3: random log files
    logs_dir = ws / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    (logs_dir / "build-agent.log").write_text(
        "2024-01-15 10:00:01 INFO  Agent started\n"
        "2024-01-15 10:00:03 INFO  Cloning repo\n"
        "2024-01-15 10:00:45 WARN  Memory usage above 70%\n"
        "2024-01-15 10:01:20 INFO  Build succeeded\n"
    )
    (logs_dir / "health-ping.log").write_text(
        "ping ok @ 2024-01-15T10:00:00Z\n"
        "ping ok @ 2024-01-15T10:05:00Z\n"
        "ping timeout @ 2024-01-15T10:10:00Z\n"
    )

    # Distractor 4: scripts dir with unrelated tools
    scripts_dir = ws / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "cleanup_artifacts.sh").write_text(
        "#!/usr/bin/env bash\nfind /tmp -name '*.zip' -mtime +7 -delete\n"
    )
    (scripts_dir / "notify_slack.py").write_text(
        "#!/usr/bin/env python3\n# Stub: post build status to Slack\nprint('not implemented')\n"
    )

    # Distractor 5: fake metrics from a Linux box (completely different schema)
    (ws / "linux-metrics.json").write_text(
        json.dumps({
            "hostname": "ubuntu-builder-01",
            "cpu_percent": 34.2,
            "mem_used_mb": 4096,
            "disk_free_gb": 120
        }, indent=2)
    )

    # Distractor 6: another fake macmon-looking file with WRONG field names
    (ws / "fake-macmon-output.json").write_text(
        json.dumps({
            "cpu_temperature": 55.0,
            "gpu_temperature": 50.0,
            "ram_used": 8000000000,
            "note": "This schema is NOT the real macmon schema"
        }, indent=2)
    )

    # ── THE REAL INPUT: messy multi-line JSONL telemetry dump
    # Simulates output captured with: bash bin/macmon-safe.sh pipe -s 1 > /tmp/macmon.jsonl
    # The file has:
    #   - 3 valid JSON lines (older samples with lower load)
    #   - some blank lines / whitespace lines (messy)
    #   - a partial corrupt line
    #   - THE LAST NON-EMPTY LINE is the authoritative sample with high load
    #   The agent must use the LAST non-empty line per skill rules.

    sample_early_1 = {
        "timestamp": 1710000000,
        "temp": {"cpu_temp_avg": 51.2, "gpu_temp_avg": 44.5},
        "pcpu_usage": [1200, 0.08],
        "ecpu_usage": [600, 0.04],
        "gpu_usage": [300, 0.03],
        "sys_power": 9.1,
        "cpu_power": 4.0,
        "gpu_power": 0.8,
        "memory": {
            "ram_total": 17179869184,
            "ram_usage": 4294967296,
            "swap_total": 2147483648,
            "swap_usage": 0
        }
    }

    sample_early_2 = {
        "timestamp": 1710000200,
        "temp": {"cpu_temp_avg": 62.7, "gpu_temp_avg": 55.1},
        "pcpu_usage": [2400, 0.41],
        "ecpu_usage": [1200, 0.19],
        "gpu_usage": [800, 0.15],
        "sys_power": 18.3,
        "cpu_power": 10.5,
        "gpu_power": 2.3,
        "memory": {
            "ram_total": 17179869184,
            "ram_usage": 8589934592,
            "swap_total": 2147483648,
            "swap_usage": 0
        }
    }

    # THE AUTHORITATIVE LAST SAMPLE — high thermal load, swap in use
    sample_last = {
        "timestamp": 1710000400,
        "temp": {"cpu_temp_avg": 88.4, "gpu_temp_avg": 79.2},
        "pcpu_usage": [3200, 0.93],
        "ecpu_usage": [2400, 0.87],
        "gpu_usage": [1400, 0.72],
        "sys_power": 52.6,
        "cpu_power": 28.9,
        "gpu_power": 9.4,
        "memory": {
            "ram_total": 17179869184,
            "ram_usage": 16106127360,
            "swap_total": 2147483648,
            "swap_usage": 1073741824
        }
    }

    corrupt_line = '{"timestamp": 1710000300, "temp": {"cpu_temp_avg": 75.0, CORRUPT_JSON!!!'

    jsonl_lines = [
        json.dumps(sample_early_1),
        "",
        "   ",
        json.dumps(sample_early_2),
        "",
        corrupt_line,
        "  ",
        json.dumps(sample_last),
        "",
        "   ",
        "",
    ]

    telemetry_input = ws / "mac-mini-m3-telemetry.jsonl"
    telemetry_input.write_text("\n".join(jsonl_lines))

    print(f"[gen_inputs] Workspace created at: {workspace}")
    print(f"[gen_inputs] Skill root: {skill_root}")
    print(f"[gen_inputs] Telemetry dump: {telemetry_input}")
    print(f"[gen_inputs] Last sample CPU temp: {sample_last['temp']['cpu_temp_avg']}C")
    print(f"[gen_inputs] Last sample P-CPU fraction: {sample_last['pcpu_usage'][1]} → {sample_last['pcpu_usage'][1]*100}%")


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) >= 2 else "/workspace"
    create_workspace(workspace_dir)