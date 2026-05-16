import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Create the agent-scripts skill reference tree (as if it pre-exists)
ref_dir = workspace / "agent-scripts" / "skills" / "create-cli" / "references"
ref_dir.mkdir(parents=True, exist_ok=True)

cli_guidelines = r"""# CLI Design Guidelines (Internal Reference)

## Core Principles
- Design for humans first, scripts second.
- Every CLI tool is a public API; treat it as such.
- Composability over completeness: do one thing well, play nicely with pipes.

## Arguments & Flags
- Positional args for the most common, obvious inputs.
- Long flags (--flag) required; short flags (-f) for common ones only.
- Flags that take values: use `--flag=value` or `--flag value` (both must work).
- Boolean flags: `--verbose` to enable, `--no-verbose` to disable.
- Never accept secrets via flags (visible in ps, shell history, logs).

## Help & Version
- `-h, --help` always shows help text and exits 0. Must work even with broken config.
  IMPORTANT: `-h/--help` ignores all other arguments — it always wins.
- `--version` prints `<name> <semver>` to stdout and exits 0.

## Output Streams
- Primary data (the "payload") → stdout.
- All diagnostics, progress, warnings, errors → stderr.
- Never mix payload and diagnostics on the same stream.

## Output Modes
- Default: human-readable, TTY-aware (colors, spinners when stdin is a TTY).
- `--json`: machine-readable JSON to stdout; disables colors/spinners.
- `--plain`: stable, line-oriented text (no colors, no spinners, no decoration). Suitable for grep/awk.
- `--quiet` / `-q`: suppress all non-essential output (warnings, progress). Errors still go to stderr.
- `--verbose` / `-v`: emit debug-level diagnostics to stderr.

## Exit Codes
- `0`: success
- `1`: generic runtime failure (I/O error, network timeout, unexpected condition)
- `2`: invalid usage — bad argument, unknown flag, failed validation, missing required arg
  (Do NOT use 2 for runtime errors; that is 1.)
- Tool-specific codes above 2 may be added when callers need to branch on specific failure modes.

## Interactivity & Prompts
- Prompts ONLY when stdin is a TTY (detect with isatty).
- `--no-input`: disables ALL prompts; fail with exit 2 if required info is missing.
  (Do NOT use --non-interactive, --batch, --headless, etc.)
- Confirmation prompts for destructive/irreversible operations: require user to type "yes" or press Enter.
- In non-interactive mode (no TTY or --no-input set), destructive operations MUST require `--force` to proceed; without it, abort with a clear error and exit 1.

## Safety / Destructive Operations
- `--dry-run`: simulate the operation; print what would happen; make zero state changes; exit 0.
- `--force`: bypass confirmation prompts (non-interactive use). Must be explicit; never default.
- Chaining rule: `--dry-run` always wins over `--force` (dry-run is never destructive).
- For operations that destroy data, display a summary of what will be deleted BEFORE asking for confirmation.

## Config & Environment Precedence
Highest priority wins. Exact order:
  1. CLI flags (highest)
  2. Environment variables
  3. Project-level config file (e.g., `.genpipe.yml` in the working directory)
  4. User-level config file (e.g., `~/.config/genpipe/config.yml`)
  5. System-level config file (e.g., `/etc/genpipe/config.yml`) (lowest)

Environment variable naming: `TOOLNAME_FLAG_NAME` in SCREAMING_SNAKE_CASE.
Example: `--cluster-url` → `GENPIPE_CLUSTER_URL`

## Color & Terminal
- Respect `NO_COLOR` environment variable (https://no-color.org/): if set (any value), disable colors.
- Respect `TERM=dumb`: disable colors and interactive elements.
- Provide `--no-color` flag as an explicit override.
- All three mechanisms must independently suppress color.

## Shell Completion
- Provide a `completion` subcommand that generates shell completion scripts.
- Support at minimum: bash, zsh, fish.
- Output the script to stdout; user pipes it to the appropriate file.
- Document installation in help text.

## Signal Handling
- Ctrl-C (SIGINT): exit quickly; bounded cleanup only (no indefinite waiting).
- Prefer crash-only design: assume the user can re-run.
- On Ctrl-C during a destructive operation that is partially complete, print a warning to stderr about partial state.

## Subcommand Design
- `<tool> help <subcommand>` and `<tool> <subcommand> --help` must both work.
- Each subcommand should be a noun or verb-noun pair.
- Global flags apply to all subcommands; subcommand flags are local.

## Examples Section (in help text)
- Show 5–10 realistic examples in help text, from simple to complex.
- Include at least one piped/stdin example.
- Comments in examples (# ...) are encouraged.

## Security
- Credentials/tokens: accept via env vars or config file only; never via positional args or flags.
- If a secret is found in a flag, warn and suggest the env var alternative.
"""

(ref_dir / "cli-guidelines.md").write_text(cli_guidelines)

# ── Distractor files: simulate an existing messy project

# 1. Old broken CLI spec draft (wrong format, wrong exit codes)
old_spec_dir = workspace / "docs" / "specs" / "legacy"
old_spec_dir.mkdir(parents=True, exist_ok=True)
(old_spec_dir / "genpipe_v0_draft.md").write_text("""# genpipe old design (ABANDONED)

Usage: genpipe [options] PIPELINE_NAME

Options:
  --dry          preview mode
  --no-confirm   skip confirmation  
  --batch        non-interactive mode
  --output-json  json output
  --loglevel     set log level (info/debug/warn)
  
Exit codes:
  0 = ok
  1 = all errors (args, runtime, everything)
  
Config: reads GENPIPE_CONFIG env var pointing to a yaml file.
""")

# 2. Partial requirements doc
reqs_dir = workspace / "docs" / "requirements"
reqs_dir.mkdir(parents=True, exist_ok=True)
(reqs_dir / "pipeline_deploy_requirements.md").write_text("""# Genomic Pipeline Deployment Tool — Business Requirements

## Background
The Bioinformatics Platform team needs a unified CLI tool called `genpipe` to replace
the current patchwork of shell scripts. The tool must:

1. Allow scientists to deploy named genomic pipelines to the HPC cluster interactively.
2. Allow CI/CD systems (Jenkins, GitHub Actions) to deploy pipelines in a fully automated
   way without any human in the loop.
3. Support destroying (tearing down) a running pipeline — this is irreversible and
   must have safeguards.
4. Let users preview what WOULD happen before committing to a deploy or destroy.
5. Never accept cluster credentials on the command line (security policy #42).
6. Support JSON output for downstream tooling (e.g., pipeline status → Slack bot).
7. Be configurable at the per-repo level (for project defaults) and per-user level.
8. Support `bash` and `zsh` shell completion for discoverability.
""")

# 3. Cluster config samples
cluster_dir = workspace / "config" / "cluster-profiles"
cluster_dir.mkdir(parents=True, exist_ok=True)
(cluster_dir / "prod.yml").write_text("""cluster_url: https://hpc.prod.biolab.internal
queue: high-mem
max_nodes: 200
""")
(cluster_dir / "staging.yml").write_text("""cluster_url: https://hpc.staging.biolab.internal
queue: default
max_nodes: 50
""")

# 4. Pipeline definition samples
pipelines_dir = workspace / "pipelines"
pipelines_dir.mkdir(parents=True, exist_ok=True)
for name in ["variant-calling", "rna-seq-quant", "methylation-array", "wgs-alignment"]:
    (pipelines_dir / f"{name}.yml").write_text(f"""name: {name}
version: 2.1.0
steps:
  - trim_adapters
  - align
  - call_variants
resources:
  cpus: 32
  memory_gb: 128
""")

# 5. Miscellaneous distractor files
src_dir = workspace / "src" / "genpipe"
src_dir.mkdir(parents=True, exist_ok=True)
(src_dir / "__init__.py").write_text("# placeholder\n")
(src_dir / "cluster.py").write_text("# cluster connection logic (stub)\n")
(src_dir / "pipeline.py").write_text("# pipeline model (stub)\n")
(src_dir / "auth.py").write_text("# auth module - reads GENPIPE_TOKEN from env\n")

tests_dir = workspace / "tests"
tests_dir.mkdir(parents=True, exist_ok=True)
(tests_dir / "test_deploy.py").write_text("# tests placeholder\n")
(tests_dir / "test_destroy.py").write_text("# tests placeholder\n")
(tests_dir / "conftest.py").write_text("# pytest conftest placeholder\n")

ci_dir = workspace / ".ci"
ci_dir.mkdir(parents=True, exist_ok=True)
(ci_dir / "jenkins_pipeline.groovy").write_text("""// CI uses genpipe in automated mode
// Must not require human input
// Must exit non-zero on any failure
""")

(workspace / "setup.py").write_text("# python package setup placeholder\n")
(workspace / "pyproject.toml").write_text("[build-system]\nrequires = ['setuptools']\n")
(workspace / ".gitignore").write_text("__pycache__/\n*.pyc\n.env\n")

# 6. Fake broken env file to show credentials should NOT be in flags
(workspace / ".env.example").write_text("""# Copy to .env and fill in
GENPIPE_TOKEN=your_cluster_api_token_here
GENPIPE_CLUSTER_URL=https://hpc.prod.biolab.internal
""")

# 7. Stale notes with wrong conventions (red herrings)
notes_dir = workspace / "docs" / "notes"
notes_dir.mkdir(parents=True, exist_ok=True)
(notes_dir / "cli_notes_scratch.txt").write_text("""rough notes - ignore
- maybe use --non-interactive for CI?
- exit code 2 for network errors?  
- --batch flag instead of prompts?
- config from GENPIPE_CONFIG env var?
- maybe --output=json instead of --json ?
""")

print("Workspace generated successfully.")
print("Files created:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")