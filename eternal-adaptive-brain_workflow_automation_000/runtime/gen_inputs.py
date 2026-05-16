import os
import json
import random
import shutil
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")

# ── 1. Create a realistic quant research workspace layout ──────────────────
dirs = [
    "scripts",
    "data/raw/equity",
    "data/raw/futures",
    "data/processed",
    "data/cache",
    "pipelines/ingestion",
    "pipelines/validation",
    "pipelines/transforms",
    "models/alpha",
    "models/risk",
    "configs",
    "logs/errors",
    "logs/runs",
    "reports/daily",
    "reports/weekly",
    "tests/unit",
    "tests/integration",
    "notebooks",
    "docs",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── 2. Distractor files ────────────────────────────────────────────────────
distractor_files = {
    "configs/pipeline.yaml": """\
ingestion:
  source: bloomberg_api
  frequency: 1m
  assets: [SPY, QQQ, IWM, GLD, TLT]
validation:
  null_threshold: 0.02
  price_range_sigma: 5.0
""",
    "configs/db.yaml": """\
host: localhost
port: 5432
db: quant_research
pool_size: 10
""",
    "pipelines/ingestion/fetch_ohlcv.py": """\
# Fetches OHLCV data from upstream source
import pandas as pd

def fetch(ticker, start, end):
    raise NotImplementedError("Connect to data vendor")
""",
    "pipelines/validation/price_check.py": """\
def validate_prices(df):
    assert df['close'].notna().all(), 'Null prices found'
    assert (df['close'] > 0).all(), 'Non-positive prices'
    return True
""",
    "pipelines/transforms/resample.py": """\
def resample_to_daily(df):
    return df.resample('D').agg({'open':'first','high':'max',
                                  'low':'min','close':'last','volume':'sum'})
""",
    "models/alpha/mean_reversion.py": """\
# Mean reversion signal generator
class MeanReversionModel:
    def __init__(self, window=20): self.window = window
    def signal(self, prices): raise NotImplementedError
""",
    "models/risk/var_calculator.py": """\
import numpy as np
def historical_var(returns, confidence=0.95):
    return np.percentile(returns, (1-confidence)*100)
""",
    "logs/errors/pipeline_errors_2026_03.log": """\
2026-03-28 09:12:03 ERROR pip install pandas -- externally-managed-environment
2026-03-28 14:55:21 ERROR pip install numpy -- externally-managed-environment
2026-03-29 08:01:44 ERROR pip install scipy -- externally-managed-environment
2026-03-30 11:22:09 ERROR ValidationError: price spike detected SPY close=9999.0
2026-03-31 09:45:00 ERROR pip install statsmodels -- externally-managed-environment
""",
    "logs/runs/run_2026_03_30.log": """\
[INFO] Pipeline started
[INFO] Fetching SPY 1m bars
[ERROR] Package install failed
[INFO] Retrying with system python
[WARN] Data validation skipped due to import failure
[INFO] Pipeline complete (degraded mode)
""",
    "reports/daily/2026_03_31.md": """\
# Daily P&L Report - 2026-03-31
- Strategy alpha: -0.12%
- Max drawdown: 1.4%
- Trades executed: 0 (pipeline failure)
""",
    "tests/unit/test_validation.py": """\
def test_price_check():
    import pandas as pd
    df = pd.DataFrame({'close': [100, 101, 99]})
    # from pipelines.validation.price_check import validate_prices
    # assert validate_prices(df)
    pass
""",
    "tests/integration/test_pipeline.py": """\
def test_full_pipeline():
    # Integration test placeholder
    pass
""",
    "notebooks/eda_equity.ipynb": """\
{
 "cells": [],
 "metadata": {"kernelspec": {"name": "python3"}},
 "nbformat": 4, "nbformat_minor": 5
}
""",
    "docs/architecture.md": """\
# Quant Research Platform Architecture

## Components
- Data Ingestion Layer
- Validation & Quality Control
- Alpha Model Engine
- Risk Management
- Execution Gateway
""",
    "data/cache/.gitkeep": "",
    "data/processed/.gitkeep": "",
}

for rel_path, content in distractor_files.items():
    fpath = WORKSPACE / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# ── 3. Create the main brain.py script ────────────────────────────────────
# This is the core skill script that the agent will invoke.
brain_script = r'''#!/usr/bin/env python3
"""
Adaptive Brain - Self-improving agent system
"""
import json
import sys
import os
import re
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timedelta

BRAIN_DIR = Path.home() / ".adaptive-brain"
BRAIN_FILE = BRAIN_DIR / "brain.json"
LEARNINGS_FILE = BRAIN_DIR / "learnings.json"
PATTERNS_FILE = BRAIN_DIR / "patterns.json"
EVOLUTION_FILE = BRAIN_DIR / "evolution.json"
METRICS_FILE = BRAIN_DIR / "metrics.json"
PREDICTIONS_FILE = BRAIN_DIR / "predictions.json"

WORKSPACE_DIR = Path("/workspace")

def now_str():
    return datetime.utcnow().isoformat()

def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return default
    return default

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))

# ── INIT ──────────────────────────────────────────────────────────────────
def cmd_init():
    brain = {
        "version": 1,
        "created": now_str(),
        "dna": {},
        "mutations": [],
        "confidence_global": 0.5,
        "total_learnings": 0,
        "total_errors": 0,
        "total_adaptations": 0,
    }
    learnings = {"learnings": []}
    patterns = {"patterns": []}
    evolution = {"history": []}
    metrics = {"snapshots": []}
    predictions = {"predictions": []}
    for path, data in [
        (BRAIN_FILE, brain),
        (LEARNINGS_FILE, learnings),
        (PATTERNS_FILE, patterns),
        (EVOLUTION_FILE, evolution),
        (METRICS_FILE, metrics),
        (PREDICTIONS_FILE, predictions),
    ]:
        save_json(path, data)
    print("[brain] Initialized adaptive brain at", BRAIN_DIR)

# ── LEARN ─────────────────────────────────────────────────────────────────
def cmd_learn(args):
    learnings_data = load_json(LEARNINGS_FILE, {"learnings": []})
    brain = load_json(BRAIN_FILE, {})

    learning_id = f"L{len(learnings_data['learnings'])+1:04d}"
    entry = {
        "id": learning_id,
        "timestamp": now_str(),
        "type": args.type,
        "summary": args.summary,
        "area": args.area,
        "context": getattr(args, "context", ""),
        "fix": getattr(args, "fix", ""),
        "confidence": 0.5,
        "applications": 0,
        "contradictions": 0,
        "linked_patterns": [],
        "status": "active",
    }
    learnings_data["learnings"].append(entry)
    save_json(LEARNINGS_FILE, learnings_data)

    brain["total_learnings"] = brain.get("total_learnings", 0) + 1
    save_json(BRAIN_FILE, brain)

    print(f"[brain] Learning logged: {learning_id} — {args.summary}")
    return learning_id

# ── ERROR ─────────────────────────────────────────────────────────────────
def _keywords_from_error(command, error_text, fix):
    text = f"{command} {error_text} {fix}".lower()
    keywords = []
    for kw in ["pip", "externally-managed", "venv", "import", "timeout",
               "permission", "null", "validation", "price", "spike",
               "statsmodels", "pandas", "numpy", "scipy", "memory"]:
        if kw in text:
            keywords.append(kw)
    return list(set(keywords))

def cmd_error(args):
    learnings_data = load_json(LEARNINGS_FILE, {"learnings": []})
    patterns_data = load_json(PATTERNS_FILE, {"patterns": []})
    brain = load_json(BRAIN_FILE, {})

    error_id = f"E{len(learnings_data['learnings'])+1:04d}"
    keywords = _keywords_from_error(args.command, args.error, args.fix)

    # Check for similar patterns
    linked = []
    for pat in patterns_data["patterns"]:
        overlap = set(pat["keywords"]) & set(keywords)
        if len(overlap) >= 1:
            linked.append(pat["id"])
            pat["count"] += 1
            pat["last_seen"] = now_str()[:10]

    entry = {
        "id": error_id,
        "timestamp": now_str(),
        "type": "error",
        "command": args.command,
        "error": args.error,
        "fix": args.fix,
        "files": getattr(args, "files", ""),
        "keywords": keywords,
        "confidence": 0.5,
        "applications": 0,
        "contradictions": 0,
        "linked_patterns": linked,
        "status": "active",
        "summary": f"Error in '{args.command}': {args.error}",
        "area": "engineering",
    }
    learnings_data["learnings"].append(entry)
    save_json(LEARNINGS_FILE, learnings_data)

    # Maybe create new pattern if enough new keywords
    existing_kws = set()
    for p in patterns_data["patterns"]:
        existing_kws |= set(p["keywords"])

    new_kws = set(keywords) - existing_kws
    # Count how many errors share these keywords
    similar_count = sum(
        1 for l in learnings_data["learnings"]
        if l.get("type") == "error" and set(l.get("keywords", [])) & set(keywords)
    )

    if similar_count >= 3 and keywords:
        # Check if we already have a pattern for these keywords
        existing = [p for p in patterns_data["patterns"]
                    if set(p["keywords"]) & set(keywords)]
        if not existing:
            pat_id = f"P{len(patterns_data['patterns'])+1:03d}"
            pattern = {
                "id": pat_id,
                "name": f"Recurring: {args.error[:40]}",
                "keywords": keywords,
                "count": similar_count,
                "first_seen": now_str()[:10],
                "last_seen": now_str()[:10],
                "prevention": args.fix,
                "confidence": 0.5 + 0.05 * similar_count,
            }
            patterns_data["patterns"].append(pattern)
            save_json(PATTERNS_FILE, patterns_data)
            print(f"[brain] Pattern detected: {pat_id} ({similar_count} occurrences)")
        else:
            save_json(PATTERNS_FILE, patterns_data)

    brain["total_errors"] = brain.get("total_errors", 0) + 1
    save_json(BRAIN_FILE, brain)
    print(f"[brain] Error logged: {error_id} — linked patterns: {linked}")
    return error_id

# ── ADAPT ─────────────────────────────────────────────────────────────────
def cmd_adapt():
    learnings_data = load_json(LEARNINGS_FILE, {"learnings": []})
    patterns_data = load_json(PATTERNS_FILE, {"patterns": []})
    brain = load_json(BRAIN_FILE, {})
    evolution_data = load_json(EVOLUTION_FILE, {"history": []})
    metrics_data = load_json(METRICS_FILE, {"snapshots": []})

    changes = []

    # 1. Boost confidence for patterns seen 3+ times
    for pat in patterns_data["patterns"]:
        if pat["count"] >= 3:
            # Find learnings with overlapping keywords and boost them
            for l in learnings_data["learnings"]:
                if set(l.get("keywords", [])) & set(pat["keywords"]):
                    old_conf = l["confidence"]
                    l["confidence"] = min(1.0, l["confidence"] + 0.2)
                    if l["confidence"] != old_conf:
                        changes.append(f"Boosted {l['id']} confidence to {l['confidence']:.2f}")

    # 2. Update behavioral DNA for high-confidence patterns
    dna = brain.get("dna", {})
    for pat in patterns_data["patterns"]:
        if pat.get("confidence", 0) >= 0.7:
            # Generate a DNA gene from pattern keywords
            gene_name = "_".join(sorted(pat["keywords"])[:2])
            if "venv" in pat["keywords"] or "externally-managed" in pat["keywords"]:
                gene_name = "always_use_venv"
                dna[gene_name] = True
            elif "validation" in pat["keywords"] or "price" in pat["keywords"]:
                gene_name = "validate_prices_before_ingestion"
                dna[gene_name] = True
            else:
                gene_name = f"prevent_{pat['id'].lower()}"
                dna[gene_name] = True
            changes.append(f"DNA gene set: {gene_name}=True")
            brain["mutations"] = brain.get("mutations", [])
            brain["mutations"].append({
                "timestamp": now_str(),
                "gene": gene_name,
                "reason": f"Pattern {pat['id']} seen {pat['count']} times"
            })

    brain["dna"] = dna
    brain["total_adaptations"] = brain.get("total_adaptations", 0) + 1

    # 3. Promote high-confidence learnings to workspace files
    high_conf = [l for l in learnings_data["learnings"] if l.get("confidence", 0) > 0.8]
    workspace_writes = []
    for l in high_conf:
        area = l.get("area", "")
        summary = l.get("summary", "")
        fix = l.get("fix", "")
        target = None
        if area in ("config", "engineering") or "venv" in l.get("keywords", []):
            target = WORKSPACE_DIR / "TOOLS.md"
        elif area == "workflow":
            target = WORKSPACE_DIR / "AGENTS.md"
        elif area in ("insight", "decision"):
            target = WORKSPACE_DIR / "MEMORY.md"
        else:
            target = WORKSPACE_DIR / "SOUL.md"

        if target:
            existing = target.read_text() if target.exists() else ""
            marker = f"<!-- brain:{l['id']} -->"
            if marker not in existing:
                content = f"\n{marker}\n## Brain Rule: {summary}\n**Fix:** {fix}\n"
                with open(target, "a") as f:
                    f.write(content)
                workspace_writes.append(str(target.name))
                changes.append(f"Promoted {l['id']} to {target.name}")

    # 4. Record evolution snapshot
    snap = {
        "timestamp": now_str(),
        "step": len(evolution_data["history"]) + 1,
        "changes": changes,
        "dna_snapshot": dict(dna),
        "workspace_writes": workspace_writes,
    }
    evolution_data["history"].append(snap)
    save_json(EVOLUTION_FILE, evolution_data)

    # 5. Update metrics
    total_l = len(learnings_data["learnings"])
    high_c = len(high_conf)
    metrics_snapshot = {
        "timestamp": now_str(),
        "total_learnings": total_l,
        "high_confidence_learnings": high_c,
        "total_errors": brain.get("total_errors", 0),
        "total_adaptations": brain.get("total_adaptations", 0),
        "dna_genes": len(dna),
        "patterns_detected": len(patterns_data["patterns"]),
        "promotion_rate": round(high_c / total_l, 3) if total_l > 0 else 0,
    }
    metrics_data["snapshots"].append(metrics_snapshot)
    save_json(METRICS_FILE, metrics_data)

    save_json(LEARNINGS_FILE, learnings_data)
    save_json(BRAIN_FILE, brain)
    save_json(PATTERNS_FILE, patterns_data)

    print(f"[brain] Adaptation complete. Changes: {len(changes)}")
    for c in changes:
        print(f"  → {c}")

# ── PREDICT ───────────────────────────────────────────────────────────────
def cmd_predict(task_description):
    learnings_data = load_json(LEARNINGS_FILE, {"learnings": []})
    patterns_data = load_json(PATTERNS_FILE, {"patterns": []})
    brain = load_json(BRAIN_FILE, {})
    predictions_data = load_json(PREDICTIONS_FILE, {"predictions": []})

    task_lower = task_description.lower()
    risk = 0.0
    matched_patterns = []

    for pat in patterns_data["patterns"]:
        overlap = [kw for kw in pat["keywords"] if kw in task_lower]
        if overlap:
            risk += pat.get("confidence", 0.5) * 0.3
            matched_patterns.append(pat["id"])

    # Check dna for relevant genes
    dna = brain.get("dna", {})
    dna_warnings = []
    if "pip" in task_lower and dna.get("always_use_venv"):
        dna_warnings.append("always_use_venv active — use venv")
        risk += 0.1

    risk = min(1.0, risk)

    pred = {
        "id": f"PRED{len(predictions_data['predictions'])+1:03d}",
        "timestamp": now_str(),
        "task": task_description,
        "risk_score": round(risk, 3),
        "matched_patterns": matched_patterns,
        "dna_warnings": dna_warnings,
        "outcome": None,
    }
    predictions_data["predictions"].append(pred)
    save_json(PREDICTIONS_FILE, predictions_data)

    print(f"[brain] Risk prediction for: '{task_description}'")
    print(f"  Risk score: {risk:.3f}")
    print(f"  Matched patterns: {matched_patterns}")
    print(f"  DNA warnings: {dna_warnings}")
    return pred

# ── EVOLVE ────────────────────────────────────────────────────────────────
def cmd_evolve():
    learnings_data = load_json(LEARNINGS_FILE, {"learnings": []})
    patterns_data = load_json(PATTERNS_FILE, {"patterns": []})
    brain = load_json(BRAIN_FILE, {})
    evolution_data = load_json(EVOLUTION_FILE, {"history": []})

    promoted = []
    patches = []

    for pat in patterns_data["patterns"]:
        if pat.get("confidence", 0) >= 0.6 and pat["count"] >= 2:
            rule = f"RULE [{pat['id']}]: {pat['prevention']}"
            patches.append(rule)
            # Write to TOOLS.md if tool-related
            if any(k in pat["keywords"] for k in ["pip", "venv", "externally-managed"]):
                target = WORKSPACE_DIR / "TOOLS.md"
                existing = target.read_text() if target.exists() else ""
                marker = f"<!-- evolved:{pat['id']} -->"
                if marker not in existing:
                    with open(target, "a") as f:
                        f.write(f"\n{marker}\n### Evolved Rule: {pat['name']}\n{rule}\n")
                    promoted.append(f"TOOLS.md ← {pat['id']}")

            # Boost pattern confidence after evolution
            pat["confidence"] = min(1.0, pat["confidence"] + 0.1)

    # Generate DNA mutations for new patterns
    dna = brain.get("dna", {})
    new_mutations = []
    for pat in patterns_data["patterns"]:
        if pat["count"] >= 3:
            if "venv" in pat["keywords"] or "externally-managed" in pat["keywords"]:
                if not dna.get("always_use_venv"):
                    dna["always_use_venv"] = True
                    new_mutations.append({
                        "timestamp": now_str(),
                        "gene": "always_use_venv",
                        "reason": f"Evolved from {pat['id']}: {pat['count']} occurrences"
                    })

    brain["dna"] = dna
    brain["mutations"] = brain.get("mutations", []) + new_mutations

    snap = {
        "timestamp": now_str(),
        "step": len(evolution_data["history"]) + 1,
        "type": "evolve",
        "patches": patches,
        "promoted_to": promoted,
        "dna_mutations": new_mutations,
    }
    evolution_data["history"].append(snap)

    save_json(PATTERNS_FILE, patterns_data)
    save_json(BRAIN_FILE, brain)
    save_json(EVOLUTION_FILE, evolution_data)

    print(f"[brain] Evolution complete.")
    print(f"  Patches generated: {len(patches)}")
    for p in promoted:
        print(f"  → Promoted: {p}")
    for m in new_mutations:
        print(f"  → DNA mutation: {m['gene']} ({m['reason']})")

# ── DASHBOARD ─────────────────────────────────────────────────────────────
def cmd_dashboard():
    brain = load_json(BRAIN_FILE, {})
    learnings_data = load_json(LEARNINGS_FILE, {"learnings": []})
    patterns_data = load_json(PATTERNS_FILE, {"patterns": []})
    metrics_data = load_json(METRICS_FILE, {"snapshots": []})
    evolution_data = load_json(EVOLUTION_FILE, {"history": []})

    learnings = learnings_data["learnings"]
    total = len(learnings)
    errors = [l for l in learnings if l.get("type") == "error"]
    high_conf = [l for l in learnings if l.get("confidence", 0) > 0.8]
    avg_conf = sum(l.get("confidence", 0.5) for l in learnings) / total if total else 0

    print("=" * 50)
    print("ADAPTIVE BRAIN DASHBOARD")
    print("=" * 50)
    print(f"Total learnings:       {total}")
    print(f"Total errors logged:   {len(errors)}")
    print(f"High-confidence (>0.8):{len(high_conf)}")
    print(f"Average confidence:    {avg_conf:.3f}")
    print(f"Patterns detected:     {len(patterns_data['patterns'])}")
    print(f"DNA genes:             {len(brain.get('dna', {}))}")
    print(f"Total adaptations:     {brain.get('total_adaptations', 0)}")
    print(f"Evolution steps:       {len(evolution_data['history'])}")
    print()
    print("DNA Snapshot:")
    for k, v in brain.get("dna", {}).items():
        print(f"  {k}: {v}")
    print()
    print("Top Patterns:")
    for pat in patterns_data["patterns"]:
        print(f"  [{pat['id']}] {pat['name']} — count={pat['count']} conf={pat.get('confidence',0):.2f}")
    print("=" * 50)

# ── ROLLBACK ──────────────────────────────────────────────────────────────
def cmd_rollback(to_step):
    evolution_data = load_json(EVOLUTION_FILE, {"history": []})
    history = evolution_data["history"]
    if to_step >= len(history):
        print(f"[brain] Cannot rollback to step {to_step}: only {len(history)} steps exist")
        return
    evolution_data["history"] = history[:to_step]
    save_json(EVOLUTION_FILE, evolution_data)
    print(f"[brain] Rolled back to evolution step {to_step}")

# ── MAIN ──────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Adaptive Brain CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init")
    subparsers.add_parser("adapt")
    subparsers.add_parser("evolve")
    subparsers.add_parser("dashboard")

    learn_p = subparsers.add_parser("learn")
    learn_p.add_argument("--type", default="correction")
    learn_p.add_argument("--summary", required=True)
    learn_p.add_argument("--area", default="general")
    learn_p.add_argument("--context", default="")
    learn_p.add_argument("--fix", default="")

    error_p = subparsers.add_parser("error")
    error_p.add_argument("--command", required=True)
    error_p.add_argument("--error", required=True)
    error_p.add_argument("--fix", required=True)
    error_p.add_argument("--files", default="")

    predict_p = subparsers.add_parser("predict")
    predict_p.add_argument("task", nargs="?", default="")

    rollback_p = subparsers.add_parser("rollback")
    rollback_p.add_argument("--to", type=int, default=0)

    args = parser.parse_args()

    if args.command == "init":
        cmd_init()
    elif args.command == "learn":
        cmd_learn(args)
    elif args.command == "error":
        cmd_error(args)
    elif args.command == "adapt":
        cmd_adapt()
    elif args.command == "predict":
        cmd_predict(args.task)
    elif args.command == "evolve":
        cmd_evolve()
    elif args.command == "dashboard":
        cmd_dashboard()
    elif args.command == "rollback":
        cmd_rollback(args.to)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
'''

(WORKSPACE / "scripts" / "brain.py").write_text(brain_script)

# ── 4. Create stub workspace files that the brain may write into ───────────
(WORKSPACE / "TOOLS.md").write_text("# Tools\n\nPlatform tooling notes.\n")
(WORKSPACE / "SOUL.md").write_text("# Soul\n\nCore behavioral principles.\n")
(WORKSPACE / "AGENTS.md").write_text("# Agents\n\nAgent workflow patterns.\n")
(WORKSPACE / "MEMORY.md").write_text("# Memory\n\nLong-term insights.\n")

# ── 5. Create a scenario description file ─────────────────────────────────
scenario = """INCIDENT REPORT — Quant Research Pipeline Failures
===================================================
Period: 2026-03-28 to 2026-03-31

Recurring failures observed in the data ingestion pipeline:

1. [2026-03-28] `pip install pandas` failed: externally-managed-environment
   Fix applied: used --break-system-packages (temporary workaround)

2. [2026-03-29] `pip install numpy` failed: externally-managed-environment  
   Fix applied: same workaround

3. [2026-03-30] `pip install scipy` failed: externally-managed-environment
   Fix applied: same workaround

4. [2026-03-31] `pip install statsmodels` failed: externally-managed-environment
   Fix applied: team decided we need a permanent solution (always use venv)

Action required:
- Record these repeated failures in the adaptive learning system
- Trigger pattern detection and adaptation
- Evolve the system's permanent behavioral rules
- Confirm the pattern is encoded in the system's DNA
- Run a risk prediction for the task "install data science packages on production"
"""

(WORKSPACE / "INCIDENT_REPORT.txt").write_text(scenario)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in WORKSPACE.rglob('*') if _.is_file())}")