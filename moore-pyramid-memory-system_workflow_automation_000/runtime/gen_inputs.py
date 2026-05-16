import os
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# Create the full pyramid directory structure
(workspace / "memory" / "monthly").mkdir(parents=True, exist_ok=True)
(workspace / "memory" / "weekly").mkdir(parents=True, exist_ok=True)
(workspace / "scripts").mkdir(parents=True, exist_ok=True)

# --- Distractor files to simulate a real, messy workspace ---

# Distractor 1: Old partial MEMORY.md with wrong/incomplete content
(workspace / "MEMORY.md").write_text(
    "# Moore Memory\n\nThis file needs to be updated.\n\n- TODO: fill in essence\n",
    encoding="utf-8"
)

# Distractor 2: A broken/empty .todos.md with wrong format
(workspace / ".todos.md").write_text(
    "# Todos\n\n- [ ] buy milk\n- [ ] fix bug #123\n",
    encoding="utf-8"
)

# Distractor 3: Some old diary entries (>14 days ago — should be ignored by agent logic but present as distractors)
old_dates = [
    (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
    (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d"),
    (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
]
for d in old_dates:
    (workspace / "memory" / f"{d}.md").write_text(
        f"# Diary {d}\n\nOld conversation about unrelated things.\n",
        encoding="utf-8"
    )

# Distractor 4: Old weekly reviews
for i in range(1, 4):
    week_label = f"2026-W{10+i}"
    (workspace / "memory" / "weekly" / f"weekly-review-{week_label}.md").write_text(
        f"# Weekly Review {week_label}\n\nSummary of week {10+i}.\n",
        encoding="utf-8"
    )

# Distractor 5: Old monthly summaries
for month in ["2026-01", "2026-02"]:
    (workspace / "memory" / "monthly" / f"{month}-summary.md").write_text(
        f"# Monthly Summary {month}\n\nOld monthly notes.\n",
        encoding="utf-8"
    )

# Distractor 6: Stub scripts (they exist but are stubs — agent must NOT call them, just create files)
(workspace / "scripts" / "startup-read.js").write_text(
    "// startup-read.js stub\nconsole.log('Loading 5 memory layers...');\n",
    encoding="utf-8"
)
(workspace / "scripts" / "weekly-archive.js").write_text(
    "// weekly-archive.js stub\nconsole.log('Generating weekly summary...');\n",
    encoding="utf-8"
)
(workspace / "scripts" / "monthly-archive.js").write_text(
    "// monthly-archive.js stub\nconsole.log('Generating monthly summary...');\n",
    encoding="utf-8"
)

# Distractor 7: Random project files to simulate a real workspace
(workspace / "package.json").write_text(
    '{\n  "name": "moore-workspace",\n  "version": "1.0.0",\n  "scripts": {"start": "node scripts/startup-read.js"}\n}\n',
    encoding="utf-8"
)
(workspace / "README_DO_NOT_EDIT.txt").write_text(
    "System workspace. Do not manually edit memory files without following the protocol.\n",
    encoding="utf-8"
)
(workspace / ".gitignore").write_text(
    "node_modules/\n.DS_Store\n*.log\n",
    encoding="utf-8"
)

# Distractor 8: A confusingly named file that looks like a todo but isn't part of the system
(workspace / "memory" / "temp-notes.txt").write_text(
    "Random scratchpad:\n- discuss API rate limits\n- consider Redis caching\n",
    encoding="utf-8"
)

# Distractor 9: A wrongly formatted existing diary for today (with wrong structure — agent must overwrite or fix)
today = datetime.now().strftime("%Y-%m-%d")
(workspace / "memory" / f"{today}.md").write_text(
    f"# {today}\n\nJust some quick notes, nothing structured.\n\nWe talked about stuff.\n",
    encoding="utf-8"
)

# Distractor 10: A config file with cron-like content to mislead
(workspace / "cron.config").write_text(
    "# Cron jobs\n0 9 * * 1 node scripts/weekly-archive.js\n0 10 L * * node scripts/monthly-archive.js\n",
    encoding="utf-8"
)

# Write a SCENARIO file that the agent will read as context (this is NOT a hint file — it's the raw conversation transcript the agent must process)
scenario_text = """CONVERSATION TRANSCRIPT — Raw notes (unstructured)
===========================================================
Date: {today}
Participants: Masone, AI Assistant

[Start of conversation]
Masone: Hey, I want to start a new data pipeline project. It'll ingest logs from our 
three microservices (auth-service, payment-service, order-service) and push them to 
a central ClickHouse cluster. I need you to help me plan the architecture.

AI: Sure! Here's what I'm thinking: we use Kafka as the message bus, Flink for 
stream processing, and ClickHouse for the analytical layer. We'll need three Kafka 
topics, one per service.

Masone: I like Kafka but I'm worried about schema evolution. Can we use Avro?

AI: Absolutely. I'll add Confluent Schema Registry to the plan.

Masone: Good. Also, I don't want to use Flink — it's too heavy. Let's use Kafka 
Streams instead.

AI: Noted. Kafka Streams is lighter and fits better for this scale. I'll revise.

Masone: Perfect. One more thing — we need to wait for the DevOps team to provision 
the ClickHouse cluster before we can finalize the sink connector config. That's 
blocked until next week.

AI: Understood. I'll keep that as a pending item.

Masone: Also, we agreed that I'll send you the exact table schemas for ClickHouse 
by Thursday. You'll need those to finalize the Kafka Streams topology.

AI: Got it. I'll wait for your schema input on Thursday before proceeding.

Masone: 好的，就这样。

[End of conversation]
===========================================================
""".format(today=today)

(workspace / "conversation_transcript.txt").write_text(scenario_text, encoding="utf-8")

print(f"Workspace generated. Today's date: {today}")
print(f"Files created in {workspace}")