# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

SkillLLM is a data generation framework that automatically synthesizes evaluation tasks from skill definitions (in `anthropic-skills/`), runs them in Docker sandboxes, and evaluates agent performance. Claude API reads a SKILL.md file, generates a complete task instance (prompt + Dockerfile + input generator + eval script), and writes it to disk as a self-contained sandbox.

## Commands

```bash
# Run the CLI (module is src/, invoked as src.run)
python -m src.run synthesize --skill-dir anthropic-skills/pdf --num 6
python -m src.run build --instance instances/pdf_merge_easy_000
python -m src.run filter --api-base http://localhost:8200/v1 --model Qwen3.5-27B
python -m src.run filter --instance instances/pdf_merge_easy_000 --api-base http://localhost:8200/v1 --model Qwen3.5-27B
python -m src.run evaluate --instance instances/pdf_merge_easy_000 --run-dir results/my_run
python -m src.run evaluate --instance instances/pdf_merge_easy_000 --workspace /path/to/workspace
python -m src.run destroy --instance instances/pdf_merge_easy_000
python -m src.run all --skill-dir anthropic-skills/pdf --num 6 --run-dir results/my_run
python -m src.run all --skill-dir anthropic-skills/pdf --num 6 --run-dir results/my_run \
    --filter-api-base http://localhost:8200/v1 --filter-model Qwen3.5-27B

# Agent runner (results saved to results/{run_name}/)
python agent_runner.py --instance instances/pdf_merge_easy_000 \
    --api-base http://localhost:8100/v1 --model Qwen/Qwen3-8B \
    --run-dir results/Qwen3-8B_exp1
```

## Architecture

**Pipeline**: `load_skill → synthesize_instance (Claude API) → write_instance_dir → Docker build/run → filter (pass@16) → evaluate`

- `src/synthesizer.py`: Core logic. `load_skill()` reads SKILL.md + referenced sub-files (case-insensitive matching). `synthesize_instance()` calls Claude API (`claude-sonnet-4-20250514`) with a synthesis prompt that produces JSON containing all instance artifacts. `write_instance_dir()` writes the structured instance directory.
- `src/sandbox.py`: `Sandbox` class wraps Docker CLI (`docker build/run/exec/cp/stop/rm`). `create()` copies workspace files, runs `gen_inputs.py` and `setup.sh` inside the container.
- `src/evaluator.py`: `evaluate()` runs eval locally; `evaluate_in_container()` copies eval.py into a running container and runs it there. Both parse JSON output `{passed, score, checks}`.
- `src/filter.py`: Task quality filtering. Runs a model (e.g. Qwen3.5-27B) 16 times on each instance. Discards tasks where ALL trials pass (too easy) or NONE pass (unsolvable). Writes `filter_status` to task.json.
- `src/agent_runner_lib.py`: Library version of agent_runner for use by filter.py. Contains the core agent loop logic.
- `src/schema.py`: `InstanceSpec` (task definition), `EvalResult` (evaluation output), `FilterResult` (filter verdict), and `RunSummary` (per-run aggregate stats) dataclasses.
- `src/run.py`: CLI with argparse subcommands. `evaluate` and `all` accept `--run-dir` to save results separately from instances. `filter` runs pass@16 quality filtering.

## Directory Structure

Task definitions and evaluation results are separated:

```
instances/{instance_id}/          # Immutable task definitions
├── task.json                     # Metadata: instance_id, skill_name, prompt, difficulty, category
│                                 #   build_status: success/failed
│                                 #   filter_status: kept/too_easy/unsolvable (after filtering)
│                                 #   filter_details: {num_trials, num_passed, pass_rate, trial_scores, model}
├── runtime/
│   ├── Dockerfile                # All deps for task + eval
│   ├── gen_inputs.py             # Deterministic input file generator (fixed seeds, marker content)
│   ├── setup.sh                  # Post-container-start initialization
│   └── workspace/                # Input files (populated by gen_inputs.py)
└── eval/
    ├── eval.py                   # Checks task completion, prints JSON to stdout
    └── expected.json             # Expected output metadata

results/{run_name}/               # Evaluation results, one dir per run
├── summary.json                  # Aggregate stats: run_name, model, total, passed, avg_score, per-instance scores
├── {instance_id}/
│   ├── result.json               # EvalResult: passed, score, checks
│   └── conversation.json         # Full agent interaction trajectory
└── ...
```

`run_name` defaults to `{model}_{timestamp}`, overridable via `--run-dir`.

## Key Dependencies

- `anthropic` Python SDK (for Claude API calls in synthesizer)
- Docker CLI (for sandbox management)
- Task-specific packages are installed inside each container's Dockerfile

## Environment
- Skills are in `anthropic-skills/` with 18 skill definitions; each has a `SKILL.md` entry point
- The synthesis prompt instructs Claude to generate Dockerfiles based on `python:3.11-slim` or `node:20-slim`
- Skill loading uses case-insensitive file matching (SKILL.md may reference `REFERENCE.md` but actual file is `reference.md`)
- Dependencies managed with `uv` (see `pyproject.toml`); run commands via `uv run python ...`
