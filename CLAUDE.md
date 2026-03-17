# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

SkillLLM is a data generation framework that automatically synthesizes evaluation tasks from skill definitions (in `anthropic-skills/`), runs them in Docker sandboxes, and evaluates agent performance. Claude API reads a SKILL.md file, generates a complete task instance (prompt + Dockerfile + input generator + eval script), and writes it to disk as a self-contained sandbox.

## Commands

```bash
# Run the CLI (module is src/, invoked as src.run)
python -m src.run synthesize --skill-dir anthropic-skills/pdf --num 6
python -m src.run build --instance instances/pdf_merge_easy_000
python -m src.run evaluate --instance instances/pdf_merge_easy_000
python -m src.run evaluate --instance instances/pdf_merge_easy_000 --workspace /path/to/workspace
python -m src.run destroy --instance instances/pdf_merge_easy_000
python -m src.run all --skill-dir anthropic-skills/pdf --num 6
```

## Architecture

**Pipeline**: `load_skill → synthesize_instance (Claude API) → write_instance_dir → Docker build/run → evaluate`

- `src/synthesizer.py`: Core logic. `load_skill()` reads SKILL.md + referenced sub-files (case-insensitive matching). `synthesize_instance()` calls Claude API (`claude-sonnet-4-20250514`) with a synthesis prompt that produces JSON containing all instance artifacts. `write_instance_dir()` writes the structured instance directory.
- `src/sandbox.py`: `Sandbox` class wraps Docker CLI (`docker build/run/exec/cp/stop/rm`). `create()` copies workspace files, runs `gen_inputs.py` and `setup.sh` inside the container.
- `src/evaluator.py`: `evaluate()` runs eval locally; `evaluate_in_container()` copies eval.py into a running container and runs it there. Both parse JSON output `{passed, score, checks}`.
- `src/schema.py`: `InstanceSpec` (task definition) and `EvalResult` (evaluation output) dataclasses.
- `src/run.py`: CLI with argparse subcommands.

## Instance Directory Structure

Each generated instance follows this layout:
```
instances/{instance_id}/
├── task.json            # Metadata: instance_id, skill_name, prompt, difficulty, category
├── runtime/
│   ├── Dockerfile       # All deps for task + eval
│   ├── gen_inputs.py    # Deterministic input file generator (fixed seeds, marker content)
│   ├── setup.sh         # Post-container-start initialization
│   └── workspace/       # Input files (populated by gen_inputs.py)
└── eval/
    ├── eval.py          # Checks task completion, prints JSON to stdout
    └── expected.json    # Expected output metadata
```

## Key Dependencies

- `anthropic` Python SDK (for Claude API calls in synthesizer)
- Docker CLI (for sandbox management)
- Task-specific packages are installed inside each container's Dockerfile

## Environment
- Skills are in `anthropic-skills/` with 18 skill definitions; each has a `SKILL.md` entry point
- The synthesis prompt instructs Claude to generate Dockerfiles based on `python:3.11-slim` or `node:20-slim`
- Skill loading uses case-insensitive file matching (SKILL.md may reference `REFERENCE.md` but actual file is `reference.md`)
