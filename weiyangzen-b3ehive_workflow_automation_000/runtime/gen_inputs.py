import os
import random
import json

random.seed(42)

BASE = "/workspace"

# --- Create distractor files to simulate a real project environment ---
distractor_structure = {
    "legacy_code/dedup_v1.py": "# Old deduplication logic\n# DO NOT USE\ndef dedup(lst):\n    return list(set(lst))\n",
    "legacy_code/dedup_v2.py": "# Slightly newer version\nimport threading\nlock = threading.Lock()\ndef dedup_v2(cache, key):\n    with lock:\n        if key in cache:\n            return False\n        cache.add(key)\n        return True\n",
    "legacy_code/tests/test_old.py": "# Tests for old dedup\ndef test_basic():\n    from legacy_code.dedup_v1 import dedup\n    assert dedup([1,1,2]) == [1,2] or set(dedup([1,1,2])) == {1,2}\n",
    "docs/architecture.md": "# Architecture Notes\nThis system processes financial transactions.\nDeduplication is critical to avoid double-charges.\n",
    "docs/requirements.txt": "Thread-safe\nHigh throughput\nLow memory\nTTL-based expiry\n",
    "docs/meeting_notes_2024_01.txt": "Meeting with engineering: discussed need for better dedup cache.\nAgreed on TTL of 300 seconds.\nMust handle 10k TPS.\n",
    "config/settings.yaml": "dedup:\n  ttl_seconds: 300\n  max_cache_size: 100000\n  backend: memory\n",
    "config/old_settings.json": '{"dedup_ttl": 60, "use_redis": false, "version": "1.0"}',
    "scripts/benchmark.sh": "#!/bin/bash\n# Benchmark script placeholder\necho 'Run benchmarks here'\n",
    "scripts/deploy.sh": "#!/bin/bash\n# Deployment script\necho 'Deploy to production'\n",
    "tmp/scratch.py": "# scratch pad\nimport time\n# TODO: implement expiry\n",
    "tmp/notes.txt": "Agent A should focus on clean code.\nAgent B should focus on performance.\nAgent C should use locks everywhere.\n",
    "reports/old_report_2023.md": "# Old Competition Report\nThis was a previous run.\nWinner: Agent B (score 78)\n",
}

for rel_path, content in distractor_structure.items():
    full_path = os.path.join(BASE, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# --- Create the task specification file the agent must read ---
task_spec = {
    "task_id": "FINTECH-DEDUP-001",
    "task_description": (
        "Implement a thread-safe transaction deduplication cache in Python. "
        "The cache must: (1) accept a transaction_id string, (2) return True if it's a duplicate "
        "(seen before within TTL), False if it's new, (3) support a configurable TTL in seconds "
        "(default 300s), (4) be safe for concurrent use by multiple threads, "
        "(5) automatically expire old entries."
    ),
    "constraints": {
        "language": "python",
        "must_be_thread_safe": True,
        "ttl_seconds": 300,
        "max_lines_per_implementation": 150,
    },
    "evaluation_note": (
        "Three agents will each produce an implementation. "
        "Run the full multi-agent competition workflow and deliver the final winning solution."
    )
}

with open(os.path.join(BASE, "task_spec.json"), "w") as f:
    json.dump(task_spec, f, indent=2)

# --- Create a partial/broken workspace stub to signal intent but not solution ---
# These stubs are intentionally incomplete (no implementation, no scores)
for agent in ["a", "b", "c"]:
    agent_dir = os.path.join(BASE, f"run_{agent}")
    os.makedirs(os.path.join(agent_dir, "implementation"), exist_ok=True)
    os.makedirs(os.path.join(agent_dir, "evaluation"), exist_ok=True)

    # Incomplete checklist - agent must complete it properly
    with open(os.path.join(agent_dir, "Checklist.md"), "w") as f:
        f.write(f"# Agent {agent.upper()} Checklist\n\n")
        f.write("- [ ] Implementation code written\n")
        f.write("- [ ] Tests written and passing\n")
        f.write("- [ ] SUMMARY.md completed\n")
        f.write("- [ ] Code documented\n")
        f.write("- [ ] No TODOs remaining\n")

    # Empty SUMMARY placeholder
    with open(os.path.join(agent_dir, "SUMMARY.md"), "w") as f:
        f.write(f"# Agent {agent.upper()} Summary\n\n<!-- TODO: fill this in -->\n")

print("Workspace initialized with distractor files and incomplete stubs.")
print("Agent must complete all phases of the competition workflow.")