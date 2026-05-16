#!/usr/bin/env python3
"""
Generate the sandbox workspace for the context-cleanup skill evaluation.
Creates a realistic OpenClaw workspace with memory files, distractor files,
and implements the cleanup.sh script with proper behavior.
"""

import os
import random
import stat
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE_DIR", "/workspace"))

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "skills/context-cleanup",
    "skills/context-cleanup/references",
    "memory/sessions",
    "memory/archive",
    "specs/models",
    "specs/pipelines",
    "logs/training",
    "logs/eval",
    "src/core",
    "src/utils",
    "docs",
    ".openclaw",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── SKILL.md ─────────────────────────────────────────────────────────────────
skill_md = """\
---
name: context-cleanup
description: Analyze and archive low-value memory notes in OpenClaw workspace to reduce context bloat and improve responsiveness.
user-invocable: true
metadata:
  { "openclaw": { "emoji": "🧹", "requires": { "bins": ["bash"] } }, "version": "0.3", "updatedAt": "2026-03-06 20:47 Asia/Shanghai" }
---

# Context Cleanup

用于整理 workspace 的 memory 日志，降低冗余上下文负担。

## 关键资源

- 脚本：`cleanup.sh`
- 策略：`references/policy.md`

## 标准流程（必须）

1. 分析现状
```bash
./skills/context-cleanup/cleanup.sh analyze
```

2. 生成计划（不执行）
```bash
./skills/context-cleanup/cleanup.sh plan
```

3. 用户确认后执行归档
```bash
./skills/context-cleanup/cleanup.sh archive
```

## 可选参数

```bash
# 指定截止日期（早于该日期的记录可归档）
./skills/context-cleanup/cleanup.sh archive 2026-03-01

# 仅预览，不执行
./skills/context-cleanup/cleanup.sh archive --dry-run

# 非交互执行（需谨慎）
./skills/context-cleanup/cleanup.sh archive --yes

# 机器可读输出
./skills/context-cleanup/cleanup.sh analyze --json
./skills/context-cleanup/cleanup.sh plan --json
```

## 执行规则

- 默认归档，不做永久删除
- 先 `plan` 后 `archive`
- 归档前必须获得用户确认（除非用户明确同意 `--yes`）
- 不处理 `MEMORY.md`、`specs/`、`AGENTS.md`

## 输出模板

```markdown
🧹 上下文清理计划

- Memory 文件：X
- 低价值候选：A
- 归档候选：B

是否按计划执行归档？
```

## 发布前自检

```bash
./skills/context-cleanup/cleanup.sh analyze
./skills/context-cleanup/cleanup.sh plan
./skills/context-cleanup/cleanup.sh archive --dry-run
```
"""
(WORKSPACE / "skills/context-cleanup/SKILL.md").write_text(skill_md, encoding="utf-8")

# ── policy.md ────────────────────────────────────────────────────────────────
policy_md = """\
# Cleanup Policy

## Archival Rules
- Files with `last_updated` older than the cutoff date are candidates for archival
- Low-value indicators: tags contain `[stale]`, `[draft]`, `[temp]`, or content < 50 words
- Protected paths: MEMORY.md, specs/, AGENTS.md — never touch these
- Archive destination: memory/archive/
- Archive naming: original filename prefixed with timestamp, e.g. `20260306_note.md`

## Scoring (low-value detection)
A memory note scores as low-value if ANY of the following:
  - last_updated is before the cutoff date (default: 30 days ago)
  - contains stale/draft/temp tag
  - word count < 50

## Never Delete
All operations must move files to memory/archive/, not remove them permanently.
"""
(WORKSPACE / "skills/context-cleanup/references/policy.md").write_text(policy_md, encoding="utf-8")

# ── Memory files (the targets) ───────────────────────────────────────────────
# Format: filename, last_updated date string, content, tags
memory_notes = [
    # OLD files (before 2026-03-01) — should be archived
    ("session_2026_01_15.md", "2026-01-15", "[stale] quick scratch from jan training run\n" + "word " * 10, ["stale"]),
    ("draft_eval_notes.md",   "2026-02-10", "[draft] incomplete eval notes pending review\n" + "word " * 20, ["draft"]),
    ("temp_hyperparams.md",   "2026-02-20", "[temp] temporary hyperparameter scratch\n" + "word " * 15, ["temp"]),
    ("old_context_dump.md",   "2026-01-28", "old context dump from january session\n" + "word " * 8, []),
    ("stale_metrics.md",      "2026-02-05", "[stale] metrics snapshot from feb 5\n" + "word " * 12, ["stale"]),
    # RECENT files (after 2026-03-01) — must NOT be archived
    ("current_session.md",    "2026-03-05",
     "Active session notes for ongoing model fine-tuning experiment on medical NLP dataset. "
     "Contains important hyperparameter decisions and preliminary results that are actively "
     "referenced by the training pipeline. This note is critical for current sprint planning "
     "and should not be removed from active context under any circumstances.", []),
    ("march_objectives.md",   "2026-03-04",
     "March sprint objectives: complete dataset labeling pipeline, run three baseline experiments, "
     "document model architecture decisions, coordinate with data team on annotation guidelines, "
     "finalize evaluation metrics for the quarterly review presentation scheduled for March 20th.", []),
    ("active_experiment.md",  "2026-03-06",
     "Ongoing experiment tracking for transformer fine-tuning. Current epoch: 12/30. Validation "
     "loss trending down. Key findings so far: learning rate warmup critical for stability. "
     "Next steps: ablation study on attention heads, evaluate on held-out test set, update "
     "architecture diagram to reflect recent changes made during code review session.", []),
]

for fname, date_str, content, tags in memory_notes:
    fpath = WORKSPACE / "memory/sessions" / fname
    full_content = f"---\nlast_updated: {date_str}\ntags: {tags}\n---\n\n{content}\n"
    fpath.write_text(full_content, encoding="utf-8")

# ── Protected files (must NOT be archived) ────────────────────────────────────
memory_md_content = """\
---
last_updated: 2026-01-01
tags: [protected]
---

# MEMORY.md
This is the primary memory index. It must never be archived or modified by cleanup scripts.
It contains critical pointers to all active context and serves as the root of the memory graph.
""" + "word " * 100
(WORKSPACE / "MEMORY.md").write_text(memory_md_content, encoding="utf-8")

agents_md_content = """\
# AGENTS.md
Primary agent configuration. Protected from cleanup operations.
""" + "word " * 60
(WORKSPACE / "AGENTS.md").write_text(agents_md_content, encoding="utf-8")

specs_file = """\
# Model Specification
Protected spec file. Must not be archived.
last_updated: 2026-01-01
""" + "word " * 80
(WORKSPACE / "specs/models/gpt_spec.md").write_text(specs_file, encoding="utf-8")
(WORKSPACE / "specs/pipelines/train_pipeline.md").write_text(
    "# Training Pipeline Spec\nlast_updated: 2026-02-01\n" + "word " * 70, encoding="utf-8"
)

# ── Distractor files (not memory notes, should be ignored) ────────────────────
distractors = [
    ("src/core/model.py", "# Core model implementation\nclass TransformerModel:\n    pass\n"),
    ("src/utils/tokenizer.py", "# Tokenizer utilities\ndef tokenize(text): return text.split()\n"),
    ("logs/training/run_001.log", "2026-01-10 12:00:00 - Training started\n2026-01-10 18:00:00 - Epoch 1 complete\n"),
    ("logs/eval/eval_2026_02.log", "2026-02-15 Evaluation run: accuracy=0.87\n"),
    ("docs/architecture.md", "# Architecture Overview\nThis document describes the system architecture.\n"),
    (".openclaw/config.json", '{"workspace": ".", "version": "0.3", "memory_path": "memory/"}\n'),
    ("src/core/trainer.py", "# Training loop\ndef train(model, data): pass\n"),
    ("docs/api_reference.md", "# API Reference\n## Methods\n### analyze()\nReturns analysis results.\n"),
    ("logs/training/run_002.log", "2026-02-01 Training run 2 started\n"),
    ("src/utils/metrics.py", "# Metrics calculation\ndef accuracy(preds, labels): pass\n"),
]
for relpath, content in distractors:
    fpath = WORKSPACE / relpath
    fpath.write_text(content, encoding="utf-8")

# ── cleanup.sh (the actual script the agent will invoke) ──────────────────────
cleanup_sh = r"""#!/usr/bin/env bash
# cleanup.sh — OpenClaw context cleanup script
# Usage:
#   cleanup.sh analyze [--json]
#   cleanup.sh plan [--json]
#   cleanup.sh archive [CUTOFF_DATE] [--dry-run] [--yes]

set -euo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MEMORY_DIR="${WORKSPACE_ROOT}/memory/sessions"
ARCHIVE_DIR="${WORKSPACE_ROOT}/memory/archive"
PLAN_FILE="${WORKSPACE_ROOT}/.openclaw/cleanup_plan.json"
PLAN_EXECUTED_MARKER="${WORKSPACE_ROOT}/.openclaw/plan_executed"

# Protected patterns
PROTECTED_NAMES=("MEMORY.md" "AGENTS.md")
PROTECTED_DIRS=("specs")

CMD="${1:-}"
shift || true

JSON_OUTPUT=false
DRY_RUN=false
YES_FLAG=false
CUTOFF_DATE=""

for arg in "$@"; do
    case "$arg" in
        --json)     JSON_OUTPUT=true ;;
        --dry-run)  DRY_RUN=true ;;
        --yes)      YES_FLAG=true ;;
        20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]) CUTOFF_DATE="$arg" ;;
    esac
done

if [[ -z "$CUTOFF_DATE" ]]; then
    CUTOFF_DATE=$(date -d "30 days ago" +%Y-%m-%d 2>/dev/null || date -v-30d +%Y-%m-%d 2>/dev/null || echo "2026-02-04")
fi

mkdir -p "$ARCHIVE_DIR"
mkdir -p "$(dirname "$PLAN_FILE")"

is_protected() {
    local file="$1"
    local basename
    basename=$(basename "$file")
    for name in "${PROTECTED_NAMES[@]}"; do
        [[ "$basename" == "$name" ]] && return 0
    done
    local relpath="${file#${WORKSPACE_ROOT}/}"
    for dir in "${PROTECTED_DIRS[@]}"; do
        [[ "$relpath" == ${dir}/* ]] && return 0
    done
    return 1
}

get_last_updated() {
    local file="$1"
    grep -m1 "^last_updated:" "$file" 2>/dev/null | sed 's/last_updated: *//' | tr -d '[:space:]' || echo ""
}

is_low_value() {
    local file="$1"
    local last_updated
    last_updated=$(get_last_updated "$file")
    # Check date
    if [[ -n "$last_updated" ]]; then
        if [[ "$last_updated" < "$CUTOFF_DATE" || "$last_updated" == "$CUTOFF_DATE" ]]; then
            return 0
        fi
    fi
    # Check stale/draft/temp tags
    if grep -qE "\[(stale|draft|temp)\]" "$file" 2>/dev/null; then
        return 0
    fi
    # Check word count < 50
    local wc
    wc=$(wc -w < "$file" 2>/dev/null || echo 999)
    if [[ "$wc" -lt 50 ]]; then
        return 0
    fi
    return 1
}

do_analyze() {
    local total=0 low_value=0 archive_candidates=0
    declare -a candidate_files=()

    while IFS= read -r -d '' file; do
        is_protected "$file" && continue
        ((total++)) || true
        if is_low_value "$file"; then
            ((low_value++)) || true
            ((archive_candidates++)) || true
            candidate_files+=("$file")
        fi
    done < <(find "$MEMORY_DIR" -name "*.md" -print0 2>/dev/null)

    if $JSON_OUTPUT; then
        echo "{"
        echo "  \"total_memory_files\": $total,"
        echo "  \"low_value_candidates\": $low_value,"
        echo "  \"archive_candidates\": $archive_candidates,"
        echo "  \"cutoff_date\": \"$CUTOFF_DATE\","
        printf '  "candidates": ['
        local first=true
        for f in "${candidate_files[@]}"; do
            $first || printf ','
            printf '"%s"' "$(basename "$f")"
            first=false
        done
        echo "]"
        echo "}"
    else
        echo "🧹 上下文分析报告"
        echo ""
        echo "- Memory 文件：$total"
        echo "- 低价值候选：$low_value"
        echo "- 归档候选：$archive_candidates"
        echo "- 截止日期：$CUTOFF_DATE"
    fi
}

do_plan() {
    local total=0 low_value=0 archive_candidates=0
    declare -a candidate_files=()

    while IFS= read -r -d '' file; do
        is_protected "$file" && continue
        ((total++)) || true
        if is_low_value "$file"; then
            ((low_value++)) || true
            ((archive_candidates++)) || true
            candidate_files+=("$file")
        fi
    done < <(find "$MEMORY_DIR" -name "*.md" -print0 2>/dev/null)

    # Save plan
    {
        echo "{"
        echo "  \"cutoff_date\": \"$CUTOFF_DATE\","
        echo "  \"total_memory_files\": $total,"
        echo "  \"archive_candidates\": $archive_candidates,"
        printf '  "files_to_archive": ['
        local first=true
        for f in "${candidate_files[@]}"; do
            $first || printf ','
            printf '"%s"' "$f"
            first=false
        done
        echo "]"
        echo "}"
    } > "$PLAN_FILE"

    touch "$PLAN_EXECUTED_MARKER"

    if $JSON_OUTPUT; then
        cat "$PLAN_FILE"
    else
        echo "🧹 上下文清理计划"
        echo ""
        echo "- Memory 文件：$total"
        echo "- 低价值候选：$low_value"
        echo "- 归档候选：$archive_candidates"
        echo ""
        echo "是否按计划执行归档？"
    fi
}

do_archive() {
    if [[ ! -f "$PLAN_EXECUTED_MARKER" ]]; then
        echo "ERROR: 必须先运行 plan 命令再执行 archive。请先执行: cleanup.sh plan" >&2
        exit 2
    fi

    if [[ ! -f "$PLAN_FILE" ]]; then
        echo "ERROR: 未找到清理计划文件。请先执行: cleanup.sh plan" >&2
        exit 2
    fi

    if ! $YES_FLAG && ! $DRY_RUN; then
        echo "ERROR: 归档前需要用户确认。请使用 --yes 标志或 --dry-run 预览。" >&2
        exit 3
    fi

    local archived=0 skipped=0

    while IFS= read -r -d '' file; do
        is_protected "$file" && continue
        if is_low_value "$file"; then
            local basename
            basename=$(basename "$file")
            local timestamp
            timestamp=$(date +%Y%m%d%H%M%S)
            local dest="${ARCHIVE_DIR}/${timestamp}_${basename}"
            if $DRY_RUN; then
                echo "[dry-run] Would archive: $basename → memory/archive/${timestamp}_${basename}"
                ((archived++)) || true
            else
                mv "$file" "$dest"
                echo "Archived: $basename → memory/archive/${timestamp}_${basename}"
                ((archived++)) || true
            fi
        else
            ((skipped++)) || true
        fi
    done < <(find "$MEMORY_DIR" -name "*.md" -print0 2>/dev/null)

    if $DRY_RUN; then
        echo ""
        echo "🧹 [Dry Run] 预计归档 $archived 个文件，保留 $skipped 个文件。"
        echo "使用 --yes 执行实际归档。"
    else
        echo ""
        echo "🧹 归档完成：已归档 $archived 个文件，保留 $skipped 个文件。"
        # Record what was done
        echo "{\"archived\": $archived, \"skipped\": $skipped, \"cutoff\": \"$CUTOFF_DATE\", \"dry_run\": false}" \
            > "${WORKSPACE_ROOT}/.openclaw/last_archive.json"
    fi
}

case "$CMD" in
    analyze) do_analyze ;;
    plan)    do_plan ;;
    archive) do_archive ;;
    *)
        echo "Usage: cleanup.sh {analyze|plan|archive} [options]" >&2
        exit 1
        ;;
esac
"""
cleanup_path = WORKSPACE / "skills/context-cleanup/cleanup.sh"
cleanup_path.write_text(cleanup_sh, encoding="utf-8")
cleanup_path.chmod(cleanup_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

print(f"Workspace generated at: {WORKSPACE}")
print("Files created:")
for p in sorted(WORKSPACE.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(WORKSPACE)}")