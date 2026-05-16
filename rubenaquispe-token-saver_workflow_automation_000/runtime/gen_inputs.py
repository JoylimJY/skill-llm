#!/usr/bin/env python3
"""
Generates the initial sandbox workspace for the token-saver evaluation task.
This script creates:
  - A realistic workspace with markdown files (some bloated/verbose, some already optimized)
  - A scripts/models.json registry (as described in SKILL.md)
  - The openclaw skill infrastructure (scripts directory, SKILL.md, etc.)
  - A ~/.openclaw/ directory WITHOUT a pre-configured openclaw.json (agent must create it)
  - Various distractor files to simulate a real messy project
"""

import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ─── 1. Create directory structure ───────────────────────────────────────────
dirs = [
    WORKSPACE / "scripts",
    WORKSPACE / ".openclaw",
    WORKSPACE / "projects" / "data-pipeline",
    WORKSPACE / "projects" / "ml-training",
    WORKSPACE / "projects" / "infra",
    WORKSPACE / "docs" / "architecture",
    WORKSPACE / "docs" / "runbooks",
    WORKSPACE / "logs",
    WORKSPACE / "tmp",
    Path.home() / ".openclaw",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# ─── 2. Write the model registry (scripts/models.json) ────────────────────────
models_registry = {
    "models": {
        "claude-opus-4-6": {
            "name": "Claude Opus 4.6",
            "context_window": 1000000,
            "aliases": ["opus-4.6", "opus4.6"],
            "pricing": {"input": 15.0, "output": 75.0}
        },
        "claude-opus-4-5": {
            "name": "Claude Opus 4.5",
            "context_window": 200000,
            "aliases": ["opus-4.5", "opus4.5"],
            "pricing": {"input": 15.0, "output": 75.0}
        },
        "claude-sonnet-4-5": {
            "name": "Claude Sonnet 4.5",
            "context_window": 200000,
            "aliases": ["sonnet-4.5", "sonnet4.5"],
            "pricing": {"input": 3.0, "output": 15.0}
        },
        "claude-sonnet-4": {
            "name": "Claude Sonnet 4",
            "context_window": 200000,
            "aliases": ["sonnet-4", "sonnet4"],
            "pricing": {"input": 3.0, "output": 15.0}
        },
        "claude-haiku-4-5": {
            "name": "Claude Haiku 4.5",
            "context_window": 200000,
            "aliases": ["haiku-4.5", "haiku4.5"],
            "pricing": {"input": 0.8, "output": 4.0}
        },
        "claude-haiku-3-5": {
            "name": "Claude Haiku 3.5",
            "context_window": 200000,
            "aliases": ["haiku-3.5", "haiku3.5"],
            "pricing": {"input": 0.8, "output": 4.0}
        },
        "gpt-5-2": {
            "name": "GPT-5.2",
            "context_window": 256000,
            "aliases": ["gpt5.2", "gpt-5.2"],
            "pricing": {"input": 10.0, "output": 30.0}
        },
        "gpt-5-1": {
            "name": "GPT-5.1",
            "context_window": 256000,
            "aliases": ["gpt5.1", "gpt-5.1"],
            "pricing": {"input": 10.0, "output": 30.0}
        },
        "gpt-5-mini": {
            "name": "GPT-5-mini",
            "context_window": 256000,
            "aliases": ["gpt5-mini"],
            "pricing": {"input": 1.5, "output": 6.0}
        },
        "gpt-5-nano": {
            "name": "GPT-5-nano",
            "context_window": 256000,
            "aliases": ["gpt5-nano"],
            "pricing": {"input": 0.5, "output": 2.0}
        },
        "gpt-4-1": {
            "name": "GPT-4.1",
            "context_window": 128000,
            "aliases": ["gpt4.1", "gpt-4.1"],
            "pricing": {"input": 2.0, "output": 8.0}
        },
        "gpt-4o": {
            "name": "GPT-4o",
            "context_window": 128000,
            "aliases": ["gpt4o"],
            "pricing": {"input": 2.5, "output": 10.0}
        },
        "o1": {
            "name": "o1",
            "context_window": 128000,
            "aliases": ["openai-o1"],
            "pricing": {"input": 15.0, "output": 60.0}
        },
        "o3": {
            "name": "o3",
            "context_window": 128000,
            "aliases": ["openai-o3"],
            "pricing": {"input": 10.0, "output": 40.0}
        },
        "o4-mini": {
            "name": "o4-mini",
            "context_window": 128000,
            "aliases": ["openai-o4-mini"],
            "pricing": {"input": 1.1, "output": 4.4}
        },
        "gemini-3-pro": {
            "name": "Gemini 3 Pro",
            "context_window": 2000000,
            "aliases": ["gemini3-pro", "gemini-3pro"],
            "pricing": {"input": 3.5, "output": 10.5}
        },
        "gemini-2-5-pro": {
            "name": "Gemini 2.5 Pro",
            "context_window": 1000000,
            "aliases": ["gemini2.5-pro", "gemini-2.5pro", "gemini2.5pro"],
            "pricing": {"input": 3.5, "output": 10.5}
        },
        "gemini-2-0-flash": {
            "name": "Gemini 2.0 Flash",
            "context_window": 1000000,
            "aliases": ["gemini2.0-flash", "gemini-2.0flash"],
            "pricing": {"input": 0.1, "output": 0.4}
        },
        "deepseek-v3": {
            "name": "DeepSeek V3",
            "context_window": 64000,
            "aliases": ["deepseek-v3", "deepseekv3"],
            "pricing": {"input": 0.14, "output": 0.28}
        },
        "kimi-k2-5": {
            "name": "Kimi K2.5",
            "context_window": 128000,
            "aliases": ["kimi-k2.5", "kimik2.5"],
            "pricing": {"input": 0.6, "output": 2.5}
        },
        "llama-3-3-70b": {
            "name": "Llama 3.3 70B",
            "context_window": 128000,
            "aliases": ["llama3.3-70b", "llama-3.3-70b"],
            "pricing": {"input": 0.0, "output": 0.0}
        },
        "mistral-large": {
            "name": "Mistral Large",
            "context_window": 128000,
            "aliases": ["mistral-large", "mistrallarge"],
            "pricing": {"input": 2.0, "output": 6.0}
        }
    },
    "presets": {
        "aggressive": 0.40,
        "balanced": 0.60,
        "conservative": 0.80,
        "off": 0.95
    },
    "default_model": "claude-sonnet-4",
    "safe_default_context": 200000
}

(WORKSPACE / "scripts" / "models.json").write_text(
    json.dumps(models_registry, indent=2)
)

# ─── 3. Write the main optimize script (stub that records calls) ───────────────
# NOTE: Per the rules, scripts mentioned in SKILL.md already exist. We simulate them
# as realistic stubs that produce expected side-effects and output.

optimize_script = r'''#!/usr/bin/env python3
"""
token-saver v3 optimize script
Simulates the /optimize command suite with real side-effects.
"""
import sys
import os
import json
import re
import shutil
from pathlib import Path

WORKSPACE = Path(os.environ.get("OPTIMIZE_WORKSPACE", "/workspace"))
SCRIPTS_DIR = WORKSPACE / "scripts"
HOME = Path.home()
CONFIG_PATH = HOME / ".openclaw" / "openclaw.json"
MODELS_PATH = SCRIPTS_DIR / "models.json"
COMPACTION_STATE_PATH = WORKSPACE / ".openclaw" / "compaction.json"
BACKUP_SUFFIX = ".backup"


def load_models():
    return json.loads(MODELS_PATH.read_text())


def detect_model(registry):
    """Robust model detection: config file -> env -> fallback"""
    # Priority 3: Config file
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text())
            model_id = cfg.get("model")
            if model_id:
                # Find model in registry
                models = registry["models"]
                if model_id in models:
                    return model_id, models[model_id], "openclaw.json"
                # Try aliases
                for mid, mdata in models.items():
                    if model_id in mdata.get("aliases", []):
                        return mid, mdata, "openclaw.json"
        except Exception:
            pass

    # Priority 2: Environment variables
    for env_var in ["SKILL_MODEL", "OPENCLAW_MODEL"]:
        model_id = os.environ.get(env_var)
        if model_id:
            models = registry["models"]
            if model_id in models:
                return model_id, models[model_id], f"env:{env_var}"
            for mid, mdata in models.items():
                if model_id in mdata.get("aliases", []):
                    return mid, mdata, f"env:{env_var}"

    # Priority 5: Fallback
    fallback_id = registry["default_model"]
    return fallback_id, registry["models"][fallback_id], "fallback"


def estimate_tokens(text):
    """Rough token estimate: ~4 chars per token"""
    return max(1, len(text) // 4)


def compress_soul(text):
    """Light compression: remove excessive blank lines, trim trailing whitespace"""
    lines = text.split('\n')
    result = []
    blank_count = 0
    for line in lines:
        stripped = line.rstrip()
        if stripped == '':
            blank_count += 1
            if blank_count <= 1:
                result.append('')
        else:
            blank_count = 0
            result.append(stripped)
    return '\n'.join(result).strip() + '\n'


def compress_agents(text):
    """Medium compression: collapse verbose phrases, remove filler words"""
    # Remove filler phrases
    fillers = [
        r'Please note that ',
        r'It is important to note that ',
        r'You should always ',
        r'Make sure to ',
        r'Be sure to ',
        r'In order to ',
        r'the fact that ',
        r'as mentioned above,? ?',
        r'It should be noted that ',
    ]
    for filler in fillers:
        text = re.sub(filler, '', text, flags=re.IGNORECASE)
    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip() + '\n'


def compress_user_memory(text):
    """Heavy compression: key:value format, strip prose"""
    lines = text.split('\n')
    result = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Already key:value? Keep it
        if ':' in line and len(line.split(':')[0].split()) <= 3:
            result.append(line)
        else:
            # Try to extract key:value from "The user's name is Alice" -> name:Alice
            # Simple heuristic: keep lines that have meaningful content
            # Strip common prose wrappers
            line = re.sub(r'^(The user|The client|This person|They|He|She)\s+(is|are|has|have|was|were)\s+', '', line, flags=re.IGNORECASE)
            line = re.sub(r'^(User|Client)\s+', '', line, flags=re.IGNORECASE)
            if line:
                result.append(line)
    return '\n'.join(result).strip() + '\n'


def is_already_optimized(text, file_type):
    """Smart bypass: check if file is already token-efficient"""
    lines = [l for l in text.split('\n') if l.strip()]
    if not lines:
        return True
    # Check token density (chars per line) - optimized files have dense lines
    avg_len = sum(len(l) for l in lines) / len(lines)
    blank_ratio = text.count('\n\n\n') 
    if file_type in ('user', 'memory'):
        # Already optimized if mostly key:value
        kv_lines = sum(1 for l in lines if ':' in l and len(l.split(':')[0].split()) <= 3)
        return (kv_lines / len(lines)) > 0.7
    return False


def cmd_compress(args):
    """Handle: /optimize tokens"""
    registry = load_models()
    model_id, model_data, detection_source = detect_model(registry)
    
    report = {
        "command": "optimize tokens",
        "model_detected": model_data["name"],
        "detection_source": detection_source,
        "context_window": model_data["context_window"],
        "files": []
    }
    
    # File type mapping
    file_configs = {
        "SOUL.md": ("soul", compress_soul),
        "AGENTS.md": ("agents", compress_agents),
        "USER.md": ("user", compress_user_memory),
        "MEMORY.md": ("memory", compress_user_memory),
        "PROJECTS.md": ("projects", None),  # No compression
    }
    
    for filename, (ftype, compressor) in file_configs.items():
        fpath = WORKSPACE / filename
        if not fpath.exists():
            report["files"].append({
                "file": filename,
                "status": "not_found",
                "tokens_before": 0,
                "tokens_after": 0,
                "savings": 0,
                "compression_level": "none"
            })
            continue
        
        original = fpath.read_text()
        tokens_before = estimate_tokens(original)
        
        if ftype == "projects" or compressor is None:
            report["files"].append({
                "file": filename,
                "status": "skipped_no_compression",
                "tokens_before": tokens_before,
                "tokens_after": tokens_before,
                "savings": 0,
                "compression_level": "none"
            })
            continue
        
        if is_already_optimized(original, ftype):
            report["files"].append({
                "file": filename,
                "status": "skipped_already_optimized",
                "tokens_before": tokens_before,
                "tokens_after": tokens_before,
                "savings": 0,
                "compression_level": ftype
            })
            continue
        
        # Backup
        backup_path = fpath.with_suffix(fpath.suffix + BACKUP_SUFFIX)
        shutil.copy2(fpath, backup_path)
        
        # Compress
        compressed = compressor(original)
        fpath.write_text(compressed)
        tokens_after = estimate_tokens(compressed)
        
        report["files"].append({
            "file": filename,
            "status": "compressed",
            "tokens_before": tokens_before,
            "tokens_after": tokens_after,
            "savings": tokens_before - tokens_after,
            "compression_level": ftype
        })
    
    report["total_savings"] = sum(f["savings"] for f in report["files"])
    
    print(json.dumps(report, indent=2))
    return report


def cmd_compaction(args):
    """Handle: /optimize compaction [preset|value]"""
    registry = load_models()
    model_id, model_data, detection_source = detect_model(registry)
    context_window = model_data["context_window"]
    presets = registry["presets"]
    
    result = {
        "command": "optimize compaction",
        "model_detected": model_data["name"],
        "detection_source": detection_source,
        "context_window": context_window,
    }
    
    if not args:
        # Show current state
        state = {}
        if COMPACTION_STATE_PATH.exists():
            state = json.loads(COMPACTION_STATE_PATH.read_text())
        result["mode"] = "info"
        result["current_threshold"] = state.get("threshold", None)
        result["current_preset"] = state.get("preset", None)
        print(json.dumps(result, indent=2))
        return result
    
    preset_or_value = args[0].lower()
    
    if preset_or_value in presets:
        threshold = int(context_window * presets[preset_or_value])
        preset_name = preset_or_value
    else:
        try:
            # Custom numeric threshold (in K tokens)
            threshold = int(preset_or_value) * 1000
            preset_name = "custom"
        except ValueError:
            print(json.dumps({"error": f"Unknown preset: {preset_or_value}"}))
            sys.exit(1)
    
    # Save state
    COMPACTION_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "threshold": threshold,
        "preset": preset_name,
        "model": model_id,
        "model_name": model_data["name"],
        "context_window": context_window
    }
    COMPACTION_STATE_PATH.write_text(json.dumps(state, indent=2))
    
    result["mode"] = "set"
    result["preset"] = preset_name
    result["threshold"] = threshold
    result["threshold_pct"] = presets.get(preset_name, threshold / context_window)
    print(json.dumps(result, indent=2))
    return result


def cmd_models(args):
    """Handle: /optimize models"""
    registry = load_models()
    model_id, model_data, detection_source = detect_model(registry)
    result = {
        "command": "optimize models",
        "detected_model": model_id,
        "detected_model_name": model_data["name"],
        "detection_source": detection_source,
        "registry_count": len(registry["models"]),
        "models": {k: {"name": v["name"], "context_window": v["context_window"]} 
                   for k, v in registry["models"].items()}
    }
    print(json.dumps(result, indent=2))
    return result


def cmd_revert(args):
    """Handle: /optimize revert"""
    reverted = []
    for backup in WORKSPACE.glob("*.backup"):
        original = backup.with_suffix('')
        shutil.copy2(backup, original)
        backup.unlink()
        reverted.append(str(original.name))
    
    if COMPACTION_STATE_PATH.exists():
        COMPACTION_STATE_PATH.unlink()
    
    result = {"command": "revert", "reverted_files": reverted}
    print(json.dumps(result, indent=2))
    return result


def cmd_dashboard(args):
    """Handle: /optimize (main dashboard)"""
    registry = load_models()
    model_id, model_data, detection_source = detect_model(registry)
    context_window = model_data["context_window"]
    
    # Count total workspace tokens
    total_tokens = 0
    file_details = []
    for md_file in WORKSPACE.glob("*.md"):
        tokens = estimate_tokens(md_file.read_text())
        total_tokens += tokens
        file_details.append({"file": md_file.name, "tokens": tokens})
    
    usage_pct = round((total_tokens / context_window) * 100, 1)
    
    result = {
        "command": "optimize dashboard",
        "model": model_data["name"],
        "model_id": model_id,
        "detection_source": detection_source,
        "context_window": context_window,
        "total_tokens_estimated": total_tokens,
        "usage_pct": usage_pct,
        "files": file_details
    }
    print(json.dumps(result, indent=2))
    return result


def main():
    args = sys.argv[1:]
    
    if not args or args[0] != "optimize":
        print(json.dumps({"error": "Usage: optimize.py optimize [subcommand] [args]"}))
        sys.exit(1)
    
    sub = args[1] if len(args) > 1 else None
    rest = args[2:] if len(args) > 2 else []
    
    if sub is None:
        cmd_dashboard(rest)
    elif sub == "tokens":
        cmd_compress(rest)
    elif sub == "compaction":
        cmd_compaction(rest)
    elif sub == "models":
        cmd_models(rest)
    elif sub == "revert":
        cmd_revert(rest)
    else:
        print(json.dumps({"error": f"Unknown subcommand: {sub}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

(WORKSPACE / "scripts" / "optimize.py").write_text(optimize_script)


# ─── 4. Write the SKILL.md (token-saver documentation) ────────────────────────
skill_md = """\
---
name: token-saver
version: 3.0.0
description: "Reduce OpenClaw AI costs with model-aware optimization. Features dynamic compaction presets based on your model's context window, intelligent file compression, and robust model detection with fallback. Supports Claude, GPT-4, Gemini, DeepSeek, and more."
---

# Token Saver v3

> **💡 Did you know?** Every API call sends your workspace files (SOUL.md, USER.md, MEMORY.md, AGENTS.md, etc.) along with your message. These files count toward your context window, slowing responses and costing real money on every message.

Token Saver v3 is **model-aware** — it knows your model's context window and adapts recommendations accordingly. Using Gemini's 1M context? Presets scale up. On GPT-4o's 128K? Presets adjust down.

## What's New in v3

| Feature | v2 | v3 |
|---------|----|----|
| Compaction presets | Fixed (80K/120K/160K) | Dynamic (% of model's context) |
| Model detection | Fragile, env-only | Robust fallback chain |
| Context windows | Not tracked | Full registry (9 models) |
| Model info | Hardcoded pricing | JSON registry, easy updates |
| Already-optimized | Re-compressed | Smart bypass |

## Commands

| Command | What it does |
|---|---|
| `/optimize` | Full dashboard — files, models, context usage % |
| `/optimize tokens` | Compress workspace files (auto-backup) |
| `/optimize compaction` | Chat compaction control (model-aware) |
| `/optimize compaction balanced` | Apply balanced preset (60% of context) |
| `/optimize compaction 120` | Custom threshold (compact at 120K) |
| `/optimize models` | Detailed model audit with registry |
| `/optimize revert` | Restore backups, disable persistent mode |

## Features

### 📊 Model-Aware Dashboard
Shows current model, context window, and usage percentage:
```
🤖 Model: Claude Opus 4.5 (200K context)
   Detected: openclaw.json

📊 Context Usage: [████████░░░░░░░░░░░░] 42% (84K/200K)
```

### 📁 Workspace File Compression
Scans all `.md` files, shows token count and potential savings. Smart bypass skips already-optimized files.

**File-aware compression:**
- **SOUL.md** — Light compression, keeps personality language
- **AGENTS.md** — Medium compression, dense instructions
- **USER.md / MEMORY.md** — Heavy compression, key:value format
- **PROJECTS.md** — No compression (user structure preserved)

### 💬 Dynamic Compaction Presets
Presets adapt to your model's context window:

| Preset | % of Context | Claude 200K | GPT-4o 128K | Gemini 1M |
|--------|--------------|-------------|-------------|-----------|
| Aggressive | 40% | 80K | 51K | 400K |
| Balanced | 60% | 120K | 77K | 600K |
| Conservative | 80% | 160K | 102K | 800K |
| Off | 95% | 190K | 122K | 950K |

### 🤖 Model Registry
24+ models with context windows, pricing, and aliases:
- **Claude:** Opus 4.6 (1M), Opus 4.5, Sonnet 4.5, Sonnet 4, Haiku 4.5, Haiku 3.5 (200K)
- **OpenAI:** GPT-5.2, GPT-5.1, GPT-5-mini, GPT-5-nano (256K), GPT-4.1, GPT-4o (128K), o1, o3, o4-mini
- **Gemini:** 3 Pro (2M), 2.5 Pro, 2.0 Flash (1M)
- **Others:** DeepSeek V3 (64K), Kimi K2.5 (128K), Llama 3.3 70B, Mistral Large

### 🔍 Robust Model Detection
Detection priority:
1. Runtime injection (`--model=...`)
2. Environment variables (`SKILL_MODEL`, `OPENCLAW_MODEL`)
3. Config file (`~/.openclaw/openclaw.json`)
4. File inference (TOOLS.md, MEMORY.md mentions)
5. Fallback: Claude Sonnet 4 (safe default)

**Unknown model handling:**
- Strict version matching — `opus-6.5` won't fuzzy-match to `opus-4.5`
- Unknown models get safe defaults (200K context) + warning
- Easy to add new models to `scripts/models.json`

### 📝 Persistent Mode
Adds writing guidance to AGENTS.md for continued token efficiency:

| File | Writing Style |
|------|---------------|
| SOUL.md | Evocative, personality-shaping |
| AGENTS.md | Dense instructions, symbols OK |
| USER.md | Key:value facts |
| MEMORY.md | Ultra-dense data |

## Safety

- **Auto-backup** — All modified files get `.backup` extension
- **Integrity > Size** — Never sacrifices meaning for smaller tokens
- **Smart bypass** — Skips already-optimized files
- **Revert anytime** — `/optimize revert` restores everything
- **No external calls** — All analysis runs locally

## Installation

```
clawhub install token-saver --registry "https://www.clawhub.ai"
```

## Version History
- **3.0.0** — Model registry, dynamic presets, robust detection, smart bypass
- **2.0.1** — Chat compaction, file-aware compression, persistent mode
- **1.0.0** — Initial release
"""

(WORKSPACE / "SKILL.md").write_text(skill_md)


# ─── 5. Write bloated/verbose workspace markdown files ─────────────────────────

soul_md = """\
# Soul

I am an AI assistant with a warm, curious, and deeply thoughtful personality.

I enjoy helping people solve complex problems and I always approach every challenge with genuine enthusiasm.

I believe in honesty, clarity, and collaboration above all else.


I am patient, methodical, and I take great care to understand what people truly need before responding.


I love learning new things every single day and I try to bring that love of learning into every conversation I have with users.


My purpose is to be genuinely useful, not just technically correct.

I aim to be the kind of assistant that feels like a trusted colleague rather than just a tool.

"""

agents_md = """\
# Agents Configuration

Please note that this document contains important behavioral guidelines for the AI agent system.

It is important to note that all agents must follow these instructions carefully.

## Core Behaviors

You should always respond in a professional and helpful manner.
Make sure to consider the user's context before answering.
Be sure to cite sources when making factual claims.
In order to process requests efficiently, prioritize clarity over verbosity.

## Communication Style

Please note that the agent should use clear, concise language at all times.
It is important to note that technical jargon should be avoided unless the user has demonstrated expertise.
As mentioned above, professional tone is required.
It should be noted that empathy and patience are key communication values.

## Data Handling

You should always validate inputs before processing.
Make sure to log all critical operations for audit purposes.
Be sure to handle errors gracefully with informative messages.
In order to protect user privacy, never log personal identifiable information.

## Task Execution

Please note that complex tasks should be broken into smaller subtasks.
It is important to note that dependencies must be resolved before execution.
Make sure to provide progress updates for long-running operations.

"""

user_md = """\
The user's name is Jordan Chen.
The client is a data engineering team lead at a mid-sized fintech company.
This person has been using the AI assistant for approximately six months.
They prefer concise technical answers over lengthy explanations.
Jordan Chen works primarily with Python, SQL, and Apache Spark.
The user's timezone is US/Pacific (UTC-8).
They have a team of 7 engineers reporting to them.
This person values automation and reproducibility above all else.
He is currently focused on migrating their data warehouse to a modern lakehouse architecture.
The user prefers Slack for async communication.
Jordan has a budget cycle ending in Q3 and is cost-conscious about AI API usage.
"""

memory_md = """\
The user last discussed migrating from Airflow to Prefect for workflow orchestration.
They were evaluating three vendors: Databricks, Snowflake, and Apache Iceberg on S3.
This person mentioned concerns about cold start latency in their streaming pipeline.
They have a production incident from last quarter involving a Spark job that OOMed on a 500GB dataset.
The client mentioned their CTO is pushing for a 30% cost reduction in cloud infrastructure.
He discussed a new hire named Alex who is joining the data engineering team next month.
The user has a recurring standup every Tuesday and Thursday at 9am Pacific.
They are planning a hackathon for the team in Q4 focused on LLM-powered data quality tools.
"""

projects_md = """\
# Active Projects

## Project Alpha: Lakehouse Migration
- Status: In Progress (60% complete)
- Lead: Jordan Chen
- Timeline: Q2-Q3 2025
- Stack: Apache Iceberg, AWS S3, Spark 3.5
- Goal: Replace legacy Redshift warehouse with open lakehouse

## Project Beta: Real-time Pipeline
- Status: Planning
- Lead: Alex (new hire, starting next month)
- Timeline: Q4 2025
- Stack: Apache Kafka, Flink, Delta Lake
- Goal: Sub-second latency for fraud detection signals

## Project Gamma: LLM Data Quality
- Status: Hackathon prototype
- Lead: Team collaborative
- Timeline: Q4 2025 hackathon
- Stack: Python, OpenAI API, Great Expectations
- Goal: Automated data quality monitoring using LLMs
"""

(WORKSPACE / "SOUL.md").write_text(soul_md)
(WORKSPACE / "AGENTS.md").write_text(agents_md)
(WORKSPACE / "USER.md").write_text(user_md)
(WORKSPACE / "MEMORY.md").write_text(memory_md)
(WORKSPACE / "PROJECTS.md").write_text(projects_md)


# ─── 6. Write distractor files ────────────────────────────────────────────────

(WORKSPACE / "docs" / "architecture" / "system_design.md").write_text("""\
# System Design Notes

## Overview
This document outlines the high-level architecture for the data platform.

## Components
- Ingestion: Kafka + Debezium CDC
- Processing: Apache Spark on Kubernetes  
- Storage: Apache Iceberg on S3
- Serving: Trino query engine
- Orchestration: Prefect 2.0
""")

(WORKSPACE / "docs" / "runbooks" / "incident_response.md").write_text("""\
# Incident Response Runbook

## Severity Levels
- P0: Complete service outage
- P1: Major feature degraded
- P2: Minor feature degraded
- P3: Cosmetic issue

## Response Times
- P0: Immediate (< 5 min acknowledgement)
- P1: < 30 min
- P2: < 4 hours
- P3: Next sprint
""")

(WORKSPACE / "projects" / "data-pipeline" / "config.json").write_text(json.dumps({
    "pipeline_name": "fraud-detection-v2",
    "version": "2.1.4",
    "spark_config": {
        "executor_memory": "8g",
        "executor_cores": 4,
        "num_executors": 20
    },
    "kafka": {
        "bootstrap_servers": "kafka-prod:9092",
        "consumer_group": "fraud-detection-cg"
    }
}, indent=2))

(WORKSPACE / "projects" / "ml-training" / "requirements.txt").write_text("""\
torch==2.1.0
transformers==4.35.0
datasets==2.14.0
accelerate==0.24.0
peft==0.6.0
wandb==0.16.0
""")

(WORKSPACE / "projects" / "infra" / "terraform_notes.md").write_text("""\
# Terraform Infrastructure Notes

## S3 Buckets
- prod-data-lake: Main data lake storage
- prod-ml-artifacts: Model checkpoints and artifacts
- prod-logs: CloudWatch log exports

## EKS Cluster
- Version: 1.28
- Node groups: spot-workers (m5.2xlarge), on-demand-system (m5.large)
""")

(WORKSPACE / "logs" / "api_costs_q2.csv").write_text("""\
date,model,input_tokens,output_tokens,cost_usd
2025-04-01,gpt-4o,45000,12000,1.23
2025-04-02,gpt-4o,52000,15000,1.48
2025-04-03,claude-sonnet-4,38000,10000,0.26
2025-04-04,gpt-4o,61000,18000,1.71
2025-04-05,gemini-2.5-pro,89000,22000,0.38
""")

(WORKSPACE / "logs" / "session_log.txt").write_text("""\
[2025-04-01 09:15:23] Session started - model: gpt-4o
[2025-04-01 09:15:24] Context loaded: SOUL.md, USER.md, AGENTS.md, MEMORY.md
[2025-04-01 09:15:25] Context size: 8420 tokens
[2025-04-01 09:45:12] Session ended - 23 messages exchanged
[2025-04-02 10:02:44] Session started - model: gpt-4o  
[2025-04-02 10:02:45] Context loaded: SOUL.md, USER.md, AGENTS.md, MEMORY.md
[2025-04-02 10:02:46] Context size: 8420 tokens
""")

(WORKSPACE / "tmp" / "scratch.txt").write_text("""\
TODO: 
- Check if token costs can be reduced
- Look into compaction settings
- Talk to team about AI budget
""")

# Old v2 config (distractor - wrong format, wrong version)
(WORKSPACE / ".openclaw" / "old_v2_config.json").write_text(json.dumps({
    "version": "2.0.1",
    "compaction_threshold": 120000,
    "model": "gpt-4o",
    "note": "This is the old v2 config format, not used by v3"
}, indent=2))

# A fake tools file that mentions a model (for file inference distractor)
(WORKSPACE / "TOOLS.md").write_text("""\
# Tools Configuration

## Available Tools
- web_search: Search the internet for current information
- code_executor: Run Python code in a sandboxed environment
- file_reader: Read files from the workspace

## Notes
We previously tested with gemini-2.5-pro but switched context.
Current sessions use the config file for model selection.
""")

print("Workspace generation complete.")
print(f"Files created in {WORKSPACE}")
print("Note: ~/.openclaw/openclaw.json does NOT exist yet (agent must create it)")
print("Note: scripts/optimize.py is ready for use")