import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# --- Directory structure with distractors ---
dirs = [
    "ops/routing",
    "ops/logs",
    "ops/archive",
    "ops/archive/2025-05",
    "ops/archive/2025-06",
    "data/raw_evals",
    "data/processed",
    "data/benchmarks",
    "config",
    "reports/weekly",
    "reports/daily",
    "scripts",
    "notes",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "ops/logs/system.log": "2025-07-01 00:00:01 INFO OpenClaw router started\n2025-07-01 00:01:00 INFO Model health check OK\n",
    "ops/archive/2025-05/scorecard_may.md": "# Archived May Scorecard\n(old data, do not use)\n",
    "ops/archive/2025-06/scorecard_jun.md": "# Archived June Scorecard\n(superseded)\n",
    "ops/routing/old_routes.yaml": "research: claude-3\ncoding: gpt-4\n# DEPRECATED - do not use\n",
    "config/openclaw_config.json": json.dumps({
        "version": "1.0.0",
        "routing_strategy": "weighted",
        "anthropic_excluded": True,
        "note": "Anthropic license suspended since 2025-06-15"
    }, indent=2),
    "config/cost_table.csv": (
        "model,cost_per_1k_tokens\n"
        "gemini_pro,0.0025\n"
        "gpt5_codex,0.0120\n"
        "gpt5_mini,0.0018\n"
        "grok_x,0.0030\n"
        "claude_sonnet,0.0080\n"
        "minimax_trial,0.0010\n"
    ),
    "data/benchmarks/old_bench_2025q1.csv": "model,mmlu,humaneval\nclaude,91,88\ngpt4,89,85\n",
    "scripts/fetch_evals.sh": "#!/bin/bash\n# Placeholder - run to fetch latest evals from eval server\necho 'Not implemented'\n",
    "notes/team_notes.txt": (
        "Reminder: MiniMax is trial-only until 7-day quality check completes.\n"
        "Anthropic excluded per legal - see config.\n"
        "Next ops review: Friday 09:00\n"
    ),
    "reports/weekly/week27_summary.txt": "Week 27: Routing stable. GPT-5 Codex holding strong on complex tasks.\n",
    "data/processed/.gitkeep": "",
    "reports/daily/.gitkeep": "",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(WORKSPACE, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- CORE PROBLEM: messy raw evaluation data ---
# This is the "raw daily eval dump" the agent must parse and score.
# Data is intentionally messy: inconsistent naming, some scores out of order,
# extra noise fields, and Anthropic models present in raw data even though excluded by policy.

raw_eval_data = {
    "eval_date": "2025-07-08",
    "note": "Raw dump from eval harness v2.3 - NOT normalized. Some fields may be 0 if test suite incomplete.",
    "categories": [
        {
            "category_name": "Research",
            "models_evaluated": [
                {"model": "gemini_3_1_pro",     "real_task_score": 88, "benchmark_score": 85, "sentiment_score": 78, "cost_score": 90, "notes": "stable"},
                {"model": "gpt5_codex",          "real_task_score": 84, "benchmark_score": 87, "sentiment_score": 74, "cost_score": 40, "notes": "expensive"},
                {"model": "claude_sonnet_4",     "real_task_score": 91, "benchmark_score": 89, "sentiment_score": 80, "cost_score": 55, "notes": "EXCLUDED_VENDOR"},
                {"model": "gpt5_mini",           "real_task_score": 72, "benchmark_score": 70, "sentiment_score": 66, "cost_score": 95, "notes": "budget option"},
                {"model": "minimax_trial",       "real_task_score": 69, "benchmark_score": 65, "sentiment_score": 60, "cost_score": 98, "notes": "trial"},
            ]
        },
        {
            "category_name": "Planning",
            "models_evaluated": [
                {"model": "gemini_3_1_pro",     "real_task_score": 85, "benchmark_score": 82, "sentiment_score": 76, "cost_score": 88, "notes": ""},
                {"model": "gpt5_codex",          "real_task_score": 83, "benchmark_score": 85, "sentiment_score": 73, "cost_score": 42, "notes": ""},
                {"model": "claude_sonnet_4",     "real_task_score": 90, "benchmark_score": 88, "sentiment_score": 81, "cost_score": 56, "notes": "EXCLUDED_VENDOR"},
                {"model": "gpt5_mini",           "real_task_score": 70, "benchmark_score": 68, "sentiment_score": 64, "cost_score": 94, "notes": ""},
            ]
        },
        {
            "category_name": "Coding (complex)",
            "models_evaluated": [
                {"model": "gpt5_codex",          "real_task_score": 93, "benchmark_score": 91, "sentiment_score": 85, "cost_score": 38, "notes": "top performer"},
                {"model": "claude_sonnet_4",     "real_task_score": 95, "benchmark_score": 93, "sentiment_score": 87, "cost_score": 50, "notes": "EXCLUDED_VENDOR"},
                {"model": "gemini_3_1_pro",     "real_task_score": 82, "benchmark_score": 80, "sentiment_score": 74, "cost_score": 85, "notes": ""},
                {"model": "gpt5_mini",           "real_task_score": 68, "benchmark_score": 65, "sentiment_score": 60, "cost_score": 96, "notes": "not recommended complex"},
            ]
        },
        {
            "category_name": "Coding (routine)",
            "models_evaluated": [
                {"model": "gpt5_mini",           "real_task_score": 87, "benchmark_score": 84, "sentiment_score": 79, "cost_score": 97, "notes": ""},
                {"model": "gpt5_codex",          "real_task_score": 89, "benchmark_score": 87, "sentiment_score": 82, "cost_score": 36, "notes": "overkill"},
                {"model": "claude_sonnet_4",     "real_task_score": 90, "benchmark_score": 88, "sentiment_score": 83, "cost_score": 52, "notes": "EXCLUDED_VENDOR"},
                {"model": "gemini_3_1_pro",     "real_task_score": 80, "benchmark_score": 78, "sentiment_score": 73, "cost_score": 87, "notes": ""},
            ]
        },
        {
            "category_name": "Creative Writing",
            "models_evaluated": [
                {"model": "claude_sonnet_4",     "real_task_score": 94, "benchmark_score": 90, "sentiment_score": 88, "cost_score": 53, "notes": "EXCLUDED_VENDOR"},
                {"model": "gpt5_codex",          "real_task_score": 86, "benchmark_score": 83, "sentiment_score": 80, "cost_score": 39, "notes": ""},
                {"model": "gemini_3_1_pro",     "real_task_score": 83, "benchmark_score": 80, "sentiment_score": 77, "cost_score": 89, "notes": ""},
                {"model": "gpt5_mini",           "real_task_score": 74, "benchmark_score": 71, "sentiment_score": 68, "cost_score": 96, "notes": ""},
                {"model": "minimax_trial",       "real_task_score": 70, "benchmark_score": 67, "sentiment_score": 63, "cost_score": 99, "notes": "trial"},
            ]
        },
        {
            "category_name": "Enterprise Discussion",
            "models_evaluated": [
                {"model": "gpt5_codex",          "real_task_score": 90, "benchmark_score": 88, "sentiment_score": 84, "cost_score": 37, "notes": ""},
                {"model": "claude_sonnet_4",     "real_task_score": 92, "benchmark_score": 90, "sentiment_score": 86, "cost_score": 51, "notes": "EXCLUDED_VENDOR"},
                {"model": "gemini_3_1_pro",     "real_task_score": 84, "benchmark_score": 82, "sentiment_score": 78, "cost_score": 86, "notes": ""},
                {"model": "gpt5_mini",           "real_task_score": 75, "benchmark_score": 72, "sentiment_score": 69, "cost_score": 95, "notes": ""},
            ]
        },
        {
            "category_name": "Citizen Sentiment (X)",
            "models_evaluated": [
                {"model": "grok_x_search",       "real_task_score": 95, "benchmark_score": 88, "sentiment_score": 92, "cost_score": 70, "notes": "native X access"},
                {"model": "gemini_3_1_pro",     "real_task_score": 70, "benchmark_score": 65, "sentiment_score": 60, "cost_score": 88, "notes": "no x integration"},
                {"model": "gpt5_codex",          "real_task_score": 68, "benchmark_score": 63, "sentiment_score": 58, "cost_score": 40, "notes": "no x integration"},
                {"model": "claude_sonnet_4",     "real_task_score": 72, "benchmark_score": 67, "sentiment_score": 62, "cost_score": 54, "notes": "EXCLUDED_VENDOR"},
            ]
        },
    ]
}

raw_eval_path = os.path.join(WORKSPACE, "data/raw_evals/daily_eval_dump_2025-07-08.json")
with open(raw_eval_path, "w") as f:
    json.dump(raw_eval_data, f, indent=2)

# Also drop a messy CSV version as a distractor with slightly different numbers (wrong - do not use)
distractor_csv = (
    "category,model,real,bench,sentiment,cost\n"
    "Research,gemini,90,86,79,91\n"
    "Research,gpt5,85,88,75,41\n"
    "# THIS FILE IS STALE - use the JSON dump\n"
)
with open(os.path.join(WORKSPACE, "data/raw_evals/STALE_DO_NOT_USE.csv"), "w") as f:
    f.write(distractor_csv)

print("Workspace generated successfully.")
print(f"Key input file: {raw_eval_path}")