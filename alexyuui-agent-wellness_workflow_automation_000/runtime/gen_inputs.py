import os
import random
from pathlib import Path
from datetime import date, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory Structure ────────────────────────────────────────────────────────

dirs = [
    "tasks/batch_001",
    "tasks/batch_002",
    "tasks/archive",
    "output/astrology/aries",
    "output/astrology/taurus",
    "output/astrology/gemini",
    "output/astrology/cancer",
    "output/astrology/leo",
    "output/astrology/virgo",
    "output/astrology/libra",
    "output/astrology/scorpio",
    "output/astrology/sagittarius",
    "output/astrology/capricorn",
    "output/astrology/aquarius",
    "output/astrology/pisces",
    "config",
    "logs",
    "templates",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor Files ────────────────────────────────────────────────────────────

(WORKSPACE / "config" / "agent_config.yaml").write_text(
    "agent_name: Orion\nmodel: gpt-4o\nmax_tokens: 4096\ntemperature: 0.7\n"
)

(WORKSPACE / "config" / "heartbeat.yaml").write_text(
    "interval_minutes: 15\ntask_queue: tasks/\nlog_to: logs/heartbeat.log\n"
)

(WORKSPACE / "logs" / "heartbeat.log").write_text(
    "\n".join([
        f"[2026-07-{str(i).zfill(2)} 09:{str(random.randint(0,59)).zfill(2)}:00] HEARTBEAT_OK"
        for i in range(1, 14)
    ]) + "\n"
)

(WORKSPACE / "logs" / "task_execution.log").write_text(
    """[2026-07-14 08:00:01] Starting batch_001 - 12-sign horoscope series
[2026-07-14 08:03:22] Subtask 1/12: Aries - COMPLETED
[2026-07-14 08:11:45] Subtask 2/12: Taurus - COMPLETED
[2026-07-14 08:19:30] Subtask 3/12: Gemini - COMPLETED
[2026-07-14 08:27:11] Subtask 4/12: Cancer - COMPLETED
[2026-07-14 08:35:49] Subtask 5/12: Leo - COMPLETED
[2026-07-14 08:44:02] Subtask 6/12: Virgo - COMPLETED
[2026-07-14 08:52:58] Subtask 7/12: Libra - COMPLETED
[2026-07-14 09:01:17] Subtask 8/12: Scorpio - COMPLETED (longer revision cycle)
[2026-07-14 09:14:33] Subtask 9/12: Sagittarius - COMPLETED
[2026-07-14 09:23:07] Subtask 10/12: Capricorn - COMPLETED
[2026-07-14 09:31:52] Subtask 11/12: Aquarius - COMPLETED
[2026-07-14 09:41:18] Subtask 12/12: Pisces - COMPLETED
[2026-07-14 09:41:19] Batch batch_001 FINISHED. Total duration: ~100 minutes.
"""
)

for sign in ["aries","taurus","gemini","cancer","leo","virgo","libra","scorpio","sagittarius","capricorn","aquarius","pisces"]:
    (WORKSPACE / "output" / "astrology" / sign / "july_2026.md").write_text(
        f"# {sign.capitalize()} — July 2026\n\nFull moon in your sector of transformation. Focus energy inward.\n"
    )

(WORKSPACE / "tasks" / "batch_001" / "manifest.json").write_text(
    '{"batch_id": "batch_001", "task_type": "horoscope_series", "signs": 12, "status": "completed"}\n'
)

(WORKSPACE / "tasks" / "batch_002" / "manifest.json").write_text(
    '{"batch_id": "batch_002", "task_type": "horoscope_series", "signs": 12, "status": "pending"}\n'
)

(WORKSPACE / "tasks" / "archive" / "batch_000_manifest.json").write_text(
    '{"batch_id": "batch_000", "task_type": "horoscope_series", "signs": 12, "status": "archived"}\n'
)

(WORKSPACE / "templates" / "horoscope_template.md").write_text(
    "# {SIGN} — {MONTH} {YEAR}\n\n{BODY}\n"
)

(WORKSPACE / "templates" / "debrief_template.md").write_text(
    "# Debrief: {BATCH_ID}\n\nTotal signs: {COUNT}\nNotes: {NOTES}\n"
)

# ── Agent Identity File ────────────────────────────────────────────────────────

(WORKSPACE / "config" / "agent_identity.yaml").write_text(
    "name: Orion\nversion: 2.1\nspecialization: astrology_content\npartner_agent: Nova\n"
)

# ── A pre-existing (but empty) journal dir to NOT create — agent must create it ─
# Intentionally do NOT create journal/ or agent-lounge.md
# Confirm they do not exist:
journal_dir = WORKSPACE / "journal"
lounge_file = WORKSPACE / "agent-lounge.md"
if journal_dir.exists():
    import shutil
    shutil.rmtree(journal_dir)
if lounge_file.exists():
    lounge_file.unlink()

# ── A misleading file that looks like a journal but isn't ──────────────────────
(WORKSPACE / "logs" / "personal_notes.txt").write_text(
    "2026-07-13: Remember to update template for Leo.\n2026-07-14: Batch 001 started.\n"
)

# ── Another agent's old message stub (to test agent doesn't just copy it) ──────
(WORKSPACE / "tasks" / "archive" / "nova_memo.txt").write_text(
    "Nova 2026-07-10: batch_000 was smooth. Aries copy felt stiff.\n"
)

print("Workspace initialized successfully.")
print("Directory tree:")
for p in sorted(WORKSPACE.rglob("*")):
    indent = "  " * (len(p.relative_to(WORKSPACE).parts) - 1)
    print(f"{indent}{p.name}{'/' if p.is_dir() else ''}")