import os
import random
import yaml

random.seed(42)

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "data",
    "data/archive",
    "docs",
    "docs/internal",
    "logs",
    "scripts",
    "configs",
    "reports",
    "reports/2024",
    "reports/2025",
    "team/research",
    "team/infra",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────
distractor_files = {
    "docs/internal/model_glossary.md": "# Model Glossary\nThis document lists all internal model aliases used by the team.\n- alpha → gpt-4o\n- beta → gemini-pro\n- gamma → claude-3-haiku\n",
    "docs/provider_setup.md": "# Provider Setup\nSee confluence for provider API key configuration instructions.\n",
    "configs/routing_rules.yaml": "routing:\n  default: balanced\n  override_on_length: true\n",
    "configs/team_prefs.json": '{"default_effort": "balanced", "preferred_provider": "anthropic", "cost_limit_usd": 50}',
    "logs/session_2025-01-15.log": "2025-01-15 09:00:01 INFO session started model=claude-sonnet\n2025-01-15 09:15:22 INFO task=code_review tokens=4200\n",
    "logs/session_2025-01-20.log": "2025-01-20 11:30:00 INFO session started model=gpt-4o\n2025-01-20 11:45:00 WARN token_limit_approaching\n",
    "scripts/rotate_keys.sh": "#!/bin/bash\necho 'Rotating provider API keys...'\n# placeholder\n",
    "reports/2024/q4_usage_report.csv": "model,requests,tokens_M,cost_usd\nclaude-haiku-4-5,12000,45.2,18.50\ngpt-4o,4500,22.8,68.40\nclaude-sonnet,7200,33.1,49.65\n",
    "reports/2025/q1_budget_projection.md": "# Q1 2025 Budget\nProjected AI API spend: $4,200\nBased on Q4 2024 usage patterns.\n",
    "team/research/active_projects.md": "## Active Research Projects\n1. Number Theory Conjecture Verification (Lead: Dr. Chen)\n2. Protein Folding QA System\n3. Automated Theorem Proving\n",
    "team/infra/deployment_checklist.md": "## Deployment Checklist\n- [ ] Update model endpoints\n- [ ] Test fallback logic\n- [ ] Verify rate limits\n",
    "data/archive/benchmarks_v1_deprecated.yaml": "# DEPRECATED - do not use\nbenchmarks:\n  - name: OldEval\n    score: 72.1\n",
}

for path, content in distractor_files.items():
    with open(path, "w") as f:
        f.write(content)

# ── CORE DATA: data/benchmarks.yaml ─────────────────────────────────────────
benchmarks = {
    "benchmarks": [
        {
            "name": "HumanEval",
            "description": "Code generation accuracy on Python functions",
            "task_domains": ["code", "engineering"],
            "leaders": ["claude-opus-4-6", "gpt-4o", "gemini-ultra"],
            "scores": {"claude-opus-4-6": 92.1, "gpt-4o": 90.2, "gemini-ultra": 89.5},
        },
        {
            "name": "SWE-bench",
            "description": "Real-world software engineering bug resolution",
            "task_domains": ["code", "debugging", "engineering"],
            "leaders": ["claude-opus-4-6", "o3", "gpt-4o"],
            "scores": {"claude-opus-4-6": 72.5, "o3": 71.8, "gpt-4o": 54.3},
        },
        {
            "name": "GPQA",
            "description": "Graduate-level science questions requiring deep domain knowledge",
            "task_domains": ["research", "science", "reasoning"],
            "leaders": ["o3", "claude-opus-4-6", "gemini-ultra"],
            "scores": {"o3": 87.7, "claude-opus-4-6": 84.2, "gemini-ultra": 80.1},
        },
        {
            "name": "MATH",
            "description": "Competition mathematics problems (AMC/AIME difficulty)",
            "task_domains": ["math", "reasoning"],
            "leaders": ["o3", "claude-opus-4-6", "gpt-4o"],
            "scores": {"o3": 97.3, "claude-opus-4-6": 89.4, "gpt-4o": 76.6},
        },
        {
            "name": "AIME",
            "description": "American Invitational Mathematics Examination — hard olympiad-style problems",
            "task_domains": ["math", "research", "reasoning"],
            "leaders": ["o3", "claude-opus-4-6"],
            "scores": {"o3": 91.6, "claude-opus-4-6": 74.3},
        },
        {
            "name": "MMLU",
            "description": "Multitask language understanding across 57 subjects",
            "task_domains": ["general", "knowledge", "dialogue"],
            "leaders": ["gpt-4o", "claude-opus-4-6", "gemini-ultra"],
            "scores": {"gpt-4o": 88.7, "claude-opus-4-6": 87.9, "gemini-ultra": 87.0},
        },
        {
            "name": "Needle-in-Haystack",
            "description": "Long-context retrieval accuracy",
            "task_domains": ["document_analysis", "long_context"],
            "leaders": ["claude-opus-4-6", "gemini-ultra", "gpt-4o"],
            "scores": {"claude-opus-4-6": 99.1, "gemini-ultra": 98.7, "gpt-4o": 96.3},
        },
        {
            "name": "MT-Bench",
            "description": "Multi-turn dialogue and instruction following quality",
            "task_domains": ["dialogue", "writing"],
            "leaders": ["gpt-4o", "claude-sonnet", "gemini-ultra"],
            "scores": {"gpt-4o": 9.2, "claude-sonnet": 9.0, "gemini-ultra": 8.9},
        },
        {
            "name": "BBH",
            "description": "Big-Bench Hard — complex multi-step logical reasoning",
            "task_domains": ["reasoning", "logic", "math"],
            "leaders": ["o3", "claude-opus-4-6", "gpt-4o"],
            "scores": {"o3": 93.2, "claude-opus-4-6": 86.7, "gpt-4o": 83.1},
        },
    ]
}

with open("data/benchmarks.yaml", "w") as f:
    yaml.dump(benchmarks, f, default_flow_style=False, sort_keys=False)

# ── CORE DATA: data/models.yaml ──────────────────────────────────────────────
models = {
    "models": [
        {
            "id": "claude-opus-4-6",
            "provider": "anthropic",
            "tier": "deep",
            "context_window": "200K",
            "supports_thinking": True,
            "thinking_levels": ["low", "medium", "high"],
            "cost_per_million_tokens": {"input": 15.0, "output": 75.0},
            "strengths": ["code", "math", "reasoning", "long_context"],
        },
        {
            "id": "claude-sonnet",
            "provider": "anthropic",
            "tier": "balanced",
            "context_window": "200K",
            "supports_thinking": False,
            "cost_per_million_tokens": {"input": 3.0, "output": 15.0},
            "strengths": ["writing", "code", "dialogue"],
        },
        {
            "id": "claude-haiku-4-5",
            "provider": "anthropic",
            "tier": "quick",
            "context_window": "200K",
            "supports_thinking": False,
            "cost_per_million_tokens": {"input": 0.25, "output": 1.25},
            "strengths": ["dialogue", "summarization", "quick_tasks"],
        },
        {
            "id": "o3",
            "provider": "openai",
            "tier": "research",
            "context_window": "128K",
            "supports_thinking": True,
            "thinking_levels": ["low", "medium", "high"],
            "cost_per_million_tokens": {"input": 10.0, "output": 40.0},
            "strengths": ["math", "research", "reasoning", "science"],
        },
        {
            "id": "gpt-4o",
            "provider": "openai",
            "tier": "balanced",
            "context_window": "128K",
            "supports_thinking": False,
            "cost_per_million_tokens": {"input": 2.5, "output": 10.0},
            "strengths": ["general", "code", "dialogue", "writing"],
        },
        {
            "id": "gemini-ultra",
            "provider": "google",
            "tier": "deep",
            "context_window": "1M",
            "supports_thinking": False,
            "cost_per_million_tokens": {"input": 7.0, "output": 21.0},
            "strengths": ["multimodal", "long_context", "research"],
        },
        {
            "id": "gemini-flash",
            "provider": "google",
            "tier": "quick",
            "context_window": "1M",
            "supports_thinking": False,
            "cost_per_million_tokens": {"input": 0.075, "output": 0.30},
            "strengths": ["quick_tasks", "summarization"],
        },
    ]
}

with open("data/models.yaml", "w") as f:
    yaml.dump(models, f, default_flow_style=False, sort_keys=False)

# ── mock openclaw CLI stub (intentionally incomplete — agent must not hardcode)
# The real mock is set up in setup_script.sh with controlled output
os.makedirs("bin", exist_ok=True)
# Placeholder — setup_script will write the actual executable

print("Workspace initialized successfully.")
print("Files created:")
for root, dirs_list, files in os.walk("."):
    for fname in files:
        fpath = os.path.join(root, fname)
        print(f"  {fpath}")