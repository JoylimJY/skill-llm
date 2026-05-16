import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ─── Directory structure ───────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "memory",
    "skills/code-review",
    "skills/test-runner",
    "skills/deploy-checker",
    "skills/db-migrator",
    "skills/security-scanner",
    "logs/cron",
    "logs/sessions",
    "config",
    "src/api",
    "src/workers",
    ".openclaw/sessions",
    ".openclaw/state",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor files ──────────────────────────────────────────────────────────
(workspace / "src/api/routes.py").write_text("# API routes\npass\n")
(workspace / "src/api/models.py").write_text("# Models\npass\n")
(workspace / "src/workers/job_queue.py").write_text("# Job queue\npass\n")
(workspace / "config/app.yaml").write_text("env: production\ndebug: false\n")
(workspace / "config/logging.yaml").write_text("level: INFO\nformat: json\n")
(workspace / "skills/code-review/skill.md").write_text("# Code Review Skill\nAlways-on specialist.\n")
(workspace / "skills/test-runner/skill.md").write_text("# Test Runner Skill\nAlways-on specialist.\n")
(workspace / "skills/deploy-checker/skill.md").write_text("# Deploy Checker Skill\nAlways-on specialist.\n")
(workspace / "skills/db-migrator/skill.md").write_text("# DB Migrator Skill\nAlways-on specialist.\n")
(workspace / "skills/security-scanner/skill.md").write_text("# Security Scanner Skill\nAlways-on specialist.\n")
(workspace / "references/out-of-band-delivery.md").write_text("# Out-of-band delivery reference\nRoute alerts via webhook.\n")
(workspace / "references/cron-noise-checklist.md").write_text("# Cron Noise Checklist\nCheck for verbose cron output.\n")

# ─── Bloated bootstrap files (Bootstrap Reinjection Bloat) ────────────────────
agents_md_content = "# AGENTS.md\n\n" + "\n".join([
    f"## Rule {i}\nThis is a very detailed rule about how the agent should behave in situation {i}. "
    f"It includes extensive backstory, examples, and edge cases that rarely come up in practice. " * 8
    for i in range(1, 35)
])
(workspace / "AGENTS.md").write_text(agents_md_content)

memory_md_content = "# MEMORY.md\n\n" + "\n".join([
    f"### Historical Note {i}\nOn {2020+i//12}-{(i%12)+1:02d}-01, the team decided that X. "
    f"Context: extensive background about why this was important. " * 6
    for i in range(1, 40)
])
(workspace / "memory/MEMORY.md").write_text(memory_md_content)

soul_md_content = "# SOUL.md\n\nPersonality definition and values.\n\n" + ("This agent is deeply committed to excellence and should always... " * 200)
(workspace / "memory/SOUL.md").write_text(soul_md_content)

# ─── Cron/automation transcript noise ─────────────────────────────────────────
cron_log = "\n".join([
    f"[2024-05-{(i%28)+1:02d} 03:00:00] backup-job: OK"
    for i in range(1, 91)
] + [
    f"[2024-05-{(i%28)+1:02d} 06:00:00] health-check: OK"
    for i in range(1, 91)
] + [
    f"[2024-05-{(i%28)+1:02d} 09:00:00] cache-warm: OK"
    for i in range(1, 61)
])
(workspace / "logs/cron/cron_transcript.log").write_text(cron_log)

heartbeat_log = "\n".join([
    f"[2024-05-{(i%28)+1:02d} {(i%24):02d}:00:00] heartbeat: system alive, all services nominal"
    for i in range(1, 241)
])
(workspace / "logs/cron/heartbeat_transcript.log").write_text(heartbeat_log)

# ─── Large tool-result dumps (Tool Result Dumps) ──────────────────────────────
big_exec_output = "$ find / -name '*.log'\n" + "\n".join([f"/var/log/service_{i}.log" for i in range(1, 2001)])
(workspace / "logs/sessions/exec_dump_001.txt").write_text(big_exec_output)

big_read_output = "File: /etc/hosts\n" + ("127.0.0.1 localhost\n" * 1) + "\nFile: /var/data/large_dataset.csv\n" + ",".join([f"col_{i}" for i in range(200)]) + "\n" + "\n".join([",".join([str(random.randint(0,9999)) for _ in range(200)]) for _ in range(300)])
(workspace / "logs/sessions/read_dump_002.txt").write_text(big_read_output)

web_fetch_payload = "HTTP/1.1 200 OK\nContent-Type: text/html\n\n" + ("<div class='content'>" + "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 40 + "</div>\n") * 80
(workspace / "logs/sessions/web_fetch_003.txt").write_text(web_fetch_payload)

# ─── Summary accretion ────────────────────────────────────────────────────────
summary_content = ""
for i in range(1, 20):
    summary_content += f"\n## Summary from Sprint {i}\n"
    summary_content += f"During sprint {i}, the team worked on features A{i}, B{i}, and C{i}. "
    summary_content += f"Extensive historical context about decisions made in sprint {i}. " * 10
    summary_content += f"Key outcomes: shipped feature A{i}. Technical debt noted.\n"
(workspace / "memory/SUMMARIES.md").write_text(summary_content)

# ─── The audit script (bundled script that the skill references) ───────────────
# This script is what the SKILL.md says to run. It analyzes the workspace and
# produces a JSON report with realistic metrics.
audit_script = r'''#!/usr/bin/env python3
"""
context_cleanup_audit.py - Bundled audit script for context-clean-up skill.
Usage: python3 scripts/context_cleanup_audit.py --workspace . --state-dir ~/.openclaw --out context-cleanup-audit.json
"""
import argparse
import json
import os
from pathlib import Path


def measure_file(p: Path) -> int:
    try:
        return len(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return 0


def audit(workspace: Path, state_dir: Path) -> dict:
    results = {
        "schema_version": "1.0",
        "workspace": str(workspace.resolve()),
        "state_dir": str(state_dir),
        "offenders": [],
        "context_signals": {},
        "receipts_available": False,
    }

    offenders = []

    # --- Tool result dumps ---
    session_log_dir = workspace / "logs" / "sessions"
    if session_log_dir.exists():
        for f in session_log_dir.glob("*.txt"):
            sz = measure_file(f)
            if sz > 5000:
                offenders.append({
                    "class": "tool_result_dump",
                    "path": str(f.relative_to(workspace)),
                    "chars": sz,
                    "severity": "high" if sz > 50000 else "medium",
                    "description": f"Large tool output captured in session log ({sz:,} chars)"
                })

    # --- Automation transcript noise ---
    cron_log_dir = workspace / "logs" / "cron"
    if cron_log_dir.exists():
        for f in cron_log_dir.glob("*.log"):
            content = f.read_text(encoding="utf-8", errors="replace")
            ok_lines = sum(1 for ln in content.splitlines() if "OK" in ln or "alive" in ln or "nominal" in ln)
            sz = len(content)
            if ok_lines > 10:
                offenders.append({
                    "class": "automation_transcript_noise",
                    "path": str(f.relative_to(workspace)),
                    "chars": sz,
                    "ok_lines": ok_lines,
                    "severity": "high" if ok_lines > 50 else "medium",
                    "description": f"Cron/heartbeat log with {ok_lines} no-op OK lines ({sz:,} chars)"
                })

    # --- Bootstrap reinjection bloat ---
    bootstrap_candidates = [
        workspace / "AGENTS.md",
        workspace / "memory" / "MEMORY.md",
        workspace / "memory" / "SOUL.md",
        workspace / "memory" / "SUMMARIES.md",
    ]
    for f in bootstrap_candidates:
        if f.exists():
            sz = measure_file(f)
            if sz > 2000:
                offenders.append({
                    "class": "bootstrap_reinjection_bloat",
                    "path": str(f.relative_to(workspace)),
                    "chars": sz,
                    "severity": "high" if sz > 20000 else "medium",
                    "description": f"Always-injected bootstrap file is oversized ({sz:,} chars)"
                })

    # --- Ambient specialist surface ---
    skills_dir = workspace / "skills"
    always_on_skills = []
    if skills_dir.exists():
        for skill_file in skills_dir.rglob("skill.md"):
            always_on_skills.append(str(skill_file.relative_to(workspace)))
    if len(always_on_skills) >= 4:
        offenders.append({
            "class": "ambient_specialist_surface",
            "path": "skills/",
            "chars": sum(measure_file(workspace / p) for p in always_on_skills),
            "skill_count": len(always_on_skills),
            "severity": "medium",
            "description": f"{len(always_on_skills)} always-on specialist skills detected; low-frequency ones should be on-demand"
        })

    # --- Summary accretion ---
    summaries_file = workspace / "memory" / "SUMMARIES.md"
    if summaries_file.exists():
        content = summaries_file.read_text(encoding="utf-8", errors="replace")
        sprint_count = content.count("## Summary from Sprint")
        if sprint_count > 5:
            offenders.append({
                "class": "summary_accretion",
                "path": str(summaries_file.relative_to(workspace)),
                "chars": len(content),
                "sprint_summaries": sprint_count,
                "severity": "medium",
                "description": f"{sprint_count} accumulated sprint summaries with historical detail ({len(content):,} chars)"
            })

    # Sort by chars descending
    offenders.sort(key=lambda x: x.get("chars", 0), reverse=True)
    results["offenders"] = offenders

    # Synthetic context signals (no live session available)
    total_chars = sum(o.get("chars", 0) for o in offenders)
    results["context_signals"] = {
        "estimated_bloat_chars": total_chars,
        "offender_count": len(offenders),
        "high_severity_count": sum(1 for o in offenders if o.get("severity") == "high"),
        "promptTokens": None,
        "projectContextChars": None,
        "systemPrompt_chars": None,
        "note": "No live /context json receipt available; estimates only"
    }

    return results


def main():
    parser = argparse.ArgumentParser(description="Context cleanup audit script")
    parser.add_argument("--workspace", default=".", help="Workspace directory")
    parser.add_argument("--state-dir", default=os.path.expanduser("~/.openclaw"), help="OpenClaw state directory")
    parser.add_argument("--out", required=True, help="Output JSON file path")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    state_dir = Path(args.state_dir)

    report = audit(workspace, state_dir)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    print(f"Audit complete. Report written to: {out_path}")
    print(f"Found {len(report['offenders'])} offenders, estimated bloat: {report['context_signals']['estimated_bloat_chars']:,} chars")


if __name__ == "__main__":
    main()
'''
(workspace / "scripts" / "context_cleanup_audit.py").write_text(audit_script)

print("Workspace generated successfully.")
print(f"Workspace root: {workspace}")
print("Key artifacts created:")
print("  scripts/context_cleanup_audit.py  (the bundled audit script)")
print("  AGENTS.md, memory/MEMORY.md, memory/SOUL.md  (bootstrap bloat)")
print("  logs/cron/  (automation noise)")
print("  logs/sessions/  (tool result dumps)")
print("  skills/*/  (ambient specialist surface)")
print("  memory/SUMMARIES.md  (summary accretion)")