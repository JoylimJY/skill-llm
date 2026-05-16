#!/bin/bash
set -e

echo "=== Setting up ai-deterministic-control skill ==="

# Create the skill package directory
mkdir -p /opt/detcontrol/detcontrol

# Write the main CLI module
cat > /opt/detcontrol/detcontrol/__init__.py << 'PYEOF'
__version__ = "1.0.0"
PYEOF

cat > /opt/detcontrol/detcontrol/algorithms.py << 'PYEOF'
"""Core algorithms: Levenshtein + TF-IDF composite scoring."""
import math
import re
from collections import Counter


def levenshtein_similarity(s1: str, s2: str) -> float:
    """Returns normalized similarity [0,1] based on edit distance."""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    len1, len2 = len(s1), len(s2)
    dp = list(range(len2 + 1))
    for i in range(1, len1 + 1):
        prev = dp[:]
        dp[0] = i
        for j in range(1, len2 + 1):
            if s1[i-1] == s2[j-1]:
                dp[j] = prev[j-1]
            else:
                dp[j] = 1 + min(prev[j], dp[j-1], prev[j-1])
    distance = dp[len2]
    max_len = max(len1, len2)
    return 1.0 - distance / max_len


def tokenize(text: str):
    return re.findall(r'\w+', text.lower())


def tfidf_cosine_similarity(docs: list) -> float:
    """
    Compute average pairwise TF-IDF cosine similarity across all docs.
    Returns average similarity [0,1].
    """
    if len(docs) < 2:
        return 1.0

    # Build vocabulary
    tokenized = [tokenize(d) for d in docs]
    vocab = set(w for tokens in tokenized for w in tokens)
    vocab = sorted(vocab)
    word_index = {w: i for i, w in enumerate(vocab)}

    N = len(docs)

    # Compute TF
    tf_vectors = []
    for tokens in tokenized:
        cnt = Counter(tokens)
        total = len(tokens) if tokens else 1
        vec = [cnt.get(w, 0) / total for w in vocab]
        tf_vectors.append(vec)

    # Compute IDF
    idf = []
    for w in vocab:
        df = sum(1 for tokens in tokenized if w in tokens)
        idf.append(math.log((N + 1) / (df + 1)) + 1)

    # TF-IDF vectors
    tfidf_vecs = []
    for tf_vec in tf_vectors:
        tfidf_vecs.append([tf_vec[i] * idf[i] for i in range(len(vocab))])

    def cosine(v1, v2):
        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = math.sqrt(sum(a*a for a in v1))
        n2 = math.sqrt(sum(b*b for b in v2))
        if n1 == 0 or n2 == 0:
            return 0.0
        return dot / (n1 * n2)

    # All pairwise
    pairs = []
    for i in range(N):
        for j in range(i+1, N):
            pairs.append(cosine(tfidf_vecs[i], tfidf_vecs[j]))

    return sum(pairs) / len(pairs) if pairs else 1.0


def composite_score(char_sim: float, semantic_sim: float) -> float:
    """0.4 * char_similarity + 0.6 * semantic_similarity"""
    return 0.4 * char_sim + 0.6 * semantic_sim


def classify_score(score: float) -> str:
    if score >= 0.8:
        return "OK"
    elif score >= 0.6:
        return "WARN"
    else:
        return "CRITICAL"
PYEOF

cat > /opt/detcontrol/detcontrol/state.py << 'PYEOF'
"""State management: read/write current parameters."""
import json
import pathlib
import datetime

STATE_DIR = pathlib.Path.home() / ".openclaw" / "detcontrol"
STATE_FILE = STATE_DIR / "state.json"
SIGNAL_FILE = pathlib.Path.home() / ".openclaw" / "workspace" / ".detcontrol_signal.json"

DEFAULTS = {
    "temperature": 0.7,
    "top_p": 0.9,
    "seed": None,
    "preset": None
}

PRESETS = {
    "code_generation":  {"temperature": 0.1,  "top_p": 0.85, "seed": 42,   "description": "代码/SQL/正则生成"},
    "config_generation":{"temperature": 0.2,  "top_p": 0.85, "seed": 42,   "description": "JSON/YAML 配置文件"},
    "data_analysis":    {"temperature": 0.15, "top_p": 0.85, "seed": 42,   "description": "数据分析报告"},
    "translation":      {"temperature": 0.1,  "top_p": 0.85, "seed": 42,   "description": "翻译任务"},
    "conversation":     {"temperature": 0.5,  "top_p": 0.9,  "seed": None, "description": "日常对话"},
    "creative_writing": {"temperature": 0.8,  "top_p": 0.95, "seed": None, "description": "创意写作/头脑风暴"},
}


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return dict(DEFAULTS)


def save_state(state: dict):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def write_signal(preset_name: str, params: dict):
    SIGNAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    signal = {
        "preset": preset_name,
        "temperature": params["temperature"],
        "top_p": params["top_p"],
        "seed": params.get("seed"),
        "applied_at": datetime.datetime.now().isoformat()
    }
    SIGNAL_FILE.write_text(json.dumps(signal, indent=2))
    return signal
PYEOF

cat > /opt/detcontrol/detcontrol/monitor.py << 'PYEOF'
"""Monitoring: sliding window trend + Z-score anomaly detection."""
import json
import math
import pathlib
import datetime

MONITOR_DIR = pathlib.Path.home() / ".openclaw" / "detcontrol" / "monitor"
METRICS_FILE = MONITOR_DIR / "metrics.jsonl"


def record_metric(score: float, label: str = "check"):
    MONITOR_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "score": score,
        "label": label
    }
    with open(METRICS_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def load_metrics(days: int = 7) -> list:
    if not METRICS_FILE.exists():
        return []
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    results = []
    for line in METRICS_FILE.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            ts = datetime.datetime.fromisoformat(entry["timestamp"])
            if ts >= cutoff:
                results.append(entry)
        except Exception:
            pass
    return results


def trend_analysis(metrics: list) -> dict:
    if not metrics:
        return {"trend": "NO_DATA", "window_size": 0, "mean": None, "std": None}
    scores = [m["score"] for m in metrics]
    n = len(scores)
    mean = sum(scores) / n
    std = math.sqrt(sum((s - mean)**2 for s in scores) / n) if n > 1 else 0.0
    # Simple linear trend
    if n < 2:
        trend = "STABLE"
    else:
        mid = n // 2
        first_half = sum(scores[:mid]) / mid
        second_half = sum(scores[mid:]) / (n - mid)
        if second_half - first_half > 0.05:
            trend = "IMPROVING"
        elif first_half - second_half > 0.05:
            trend = "DEGRADING"
        else:
            trend = "STABLE"
    return {"trend": trend, "window_size": n, "mean": round(mean, 4), "std": round(std, 4)}


def detect_anomalies(metrics: list, z_threshold: float = 2.0) -> list:
    if len(metrics) < 3:
        return []
    scores = [m["score"] for m in metrics]
    n = len(scores)
    mean = sum(scores) / n
    std = math.sqrt(sum((s - mean)**2 for s in scores) / n)
    if std == 0:
        return []
    anomalies = []
    for m in metrics:
        z = abs(m["score"] - mean) / std
        if z > z_threshold:
            anomalies.append({**m, "z_score": round(z, 4)})
    return anomalies
PYEOF

cat > /opt/detcontrol/detcontrol/inject.py << 'PYEOF'
"""Parameter injection into openclaw.json."""
import json
import pathlib
import shutil
import datetime

OPENCLAW_JSON = pathlib.Path.home() / ".openclaw" / "openclaw.json"
BACKUP_DIR = pathlib.Path.home() / ".openclaw" / "detcontrol" / "backups"


def inject_model_params(model_name: str, params: dict) -> dict:
    """
    Backup -> read -> update -> validate -> write openclaw.json.
    Returns result dict with backup_path and updated config.
    """
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Backup
    if OPENCLAW_JSON.exists():
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"openclaw_{ts}.json.bak"
        shutil.copy2(OPENCLAW_JSON, backup_path)
    else:
        backup_path = None
        # Create minimal structure
        OPENCLAW_JSON.parent.mkdir(parents=True, exist_ok=True)
        OPENCLAW_JSON.write_text(json.dumps({"version": "1.0", "models": {}, "global": {}}, indent=2))

    # Step 2: Read
    try:
        config = json.loads(OPENCLAW_JSON.read_text())
    except json.JSONDecodeError as e:
        if backup_path:
            shutil.copy2(backup_path, OPENCLAW_JSON)
        raise RuntimeError(f"JSON parse failed, restored backup: {e}")

    # Step 3: Update
    if "models" not in config:
        config["models"] = {}
    if model_name not in config["models"]:
        config["models"][model_name] = {}

    config["models"][model_name]["temperature"] = params.get("temperature")
    config["models"][model_name]["top_p"] = params.get("top_p")
    config["models"][model_name]["seed"] = params.get("seed")
    config["models"][model_name]["injected_at"] = datetime.datetime.now().isoformat()

    # Step 4: Validate JSON
    try:
        validated = json.dumps(config, indent=2)
        json.loads(validated)  # re-parse to confirm valid
    except Exception as e:
        if backup_path:
            shutil.copy2(backup_path, OPENCLAW_JSON)
        raise RuntimeError(f"JSON validation failed, restored backup: {e}")

    # Step 5: Write
    OPENCLAW_JSON.write_text(validated)

    return {
        "status": "success",
        "model": model_name,
        "backup_path": str(backup_path) if backup_path else None,
        "injected_params": {
            "temperature": params.get("temperature"),
            "top_p": params.get("top_p"),
            "seed": params.get("seed"),
        }
    }


def restore_backup(backup_path: str):
    src = pathlib.Path(backup_path)
    if not src.exists():
        raise FileNotFoundError(f"Backup not found: {backup_path}")
    shutil.copy2(src, OPENCLAW_JSON)
    return {"status": "restored", "from": backup_path}
PYEOF

cat > /opt/detcontrol/detcontrol/cli.py << 'PYEOF'
"""CLI entry point for detcontrol."""
import click
import json
import pathlib
import datetime
import sys

from .state import PRESETS, DEFAULTS, load_state, save_state, write_signal
from .algorithms import (
    levenshtein_similarity, tfidf_cosine_similarity,
    composite_score, classify_score
)
from .monitor import record_metric, load_metrics, trend_analysis, detect_anomalies
from .inject import inject_model_params, restore_backup


@click.group()
def cli():
    """AI Deterministic Control Tool - v1.0.0"""
    pass


# ── set ──────────────────────────────────────────────────────────────────────
@cli.command("set")
@click.option("--temp", type=float, default=None)
@click.option("--top-p", type=float, default=None)
@click.option("--seed", type=int, default=None)
def set_params(temp, top_p, seed):
    """Set temperature / top_p / seed parameters."""
    state = load_state()
    if temp is not None:
        state["temperature"] = temp
    if top_p is not None:
        state["top_p"] = top_p
    if seed is not None:
        state["seed"] = seed
    save_state(state)
    click.echo(json.dumps({"status": "ok", "state": state}, indent=2))


# ── preset ───────────────────────────────────────────────────────────────────
@cli.group("preset")
def preset():
    """Manage presets."""
    pass


@preset.command("list")
def preset_list():
    rows = []
    for name, p in PRESETS.items():
        rows.append({"name": name, "temperature": p["temperature"], "description": p["description"]})
    click.echo(json.dumps(rows, indent=2))


@preset.command("apply")
@click.argument("preset_name")
def preset_apply(preset_name):
    """Apply a named preset."""
    if preset_name not in PRESETS:
        click.echo(json.dumps({"error": f"Unknown preset: {preset_name}"}), err=True)
        sys.exit(1)
    params = PRESETS[preset_name]
    state = load_state()
    state["temperature"] = params["temperature"]
    state["top_p"] = params["top_p"]
    state["seed"] = params.get("seed")
    state["preset"] = preset_name
    save_state(state)
    signal = write_signal(preset_name, params)
    click.echo(json.dumps({"status": "applied", "preset": preset_name, "params": params, "signal": signal}, indent=2))


# ── check ────────────────────────────────────────────────────────────────────
@cli.command("check")
@click.option("--prompt", required=True, help="Prompt to test consistency")
@click.option("--samples", default=5, type=int, help="Number of simulated samples")
@click.option("--output", default=None, help="Save JSON report to file")
def check(prompt, samples, output):
    """Run consistency check: Levenshtein + TF-IDF composite score."""
    import random
    state = load_state()
    temperature = state.get("temperature", 0.7)
    seed_val = state.get("seed")

    rng = random.Random(seed_val if seed_val is not None else 12345)

    # Simulate samples: deterministic when seed is set
    base_words = prompt.split()
    generated_samples = []
    for i in range(samples):
        # Simulate minor paraphrase variation based on temperature
        variance = temperature * 0.3
        words = list(base_words)
        if rng.random() < variance:
            words = words[::-1]
        if rng.random() < variance * 0.5:
            words.append("综合分析结果如下")
        generated_samples.append(" ".join(words))

    # Compute pairwise char similarity
    char_sims = []
    for i in range(len(generated_samples)):
        for j in range(i+1, len(generated_samples)):
            char_sims.append(levenshtein_similarity(generated_samples[i], generated_samples[j]))
    avg_char = sum(char_sims) / len(char_sims) if char_sims else 1.0

    # Semantic similarity
    avg_semantic = tfidf_cosine_similarity(generated_samples)

    # Composite
    comp = composite_score(avg_char, avg_semantic)
    status = classify_score(comp)

    record_metric(comp, label="check")

    result = {
        "prompt": prompt,
        "samples": samples,
        "temperature": temperature,
        "seed": seed_val,
        "char_similarity": round(avg_char, 4),
        "semantic_similarity": round(avg_semantic, 4),
        "composite_score": round(comp, 4),
        "status": status,
        "generated_samples": generated_samples,
        "timestamp": datetime.datetime.now().isoformat()
    }

    click.echo(json.dumps(result, indent=2))

    if output:
        out_path = pathlib.Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2))
        click.echo(f"\nReport saved to: {output}", err=True)


# ── report / monitor ──────────────────────────────────────────────────────────
@cli.command("report")
@click.option("--format", "fmt", default="json", type=click.Choice(["json", "markdown"]))
@click.option("--days", default=7, type=int)
def report(fmt, days):
    """Generate monitoring report."""
    metrics = load_metrics(days)
    trend = trend_analysis(metrics)
    anomalies = detect_anomalies(metrics)

    if fmt == "json":
        data = {"days": days, "metrics_count": len(metrics), "trend": trend, "anomalies": anomalies}
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"# Deterministic Control Report (Last {days} days)")
        click.echo(f"- Metrics collected: {len(metrics)}")
        click.echo(f"- Trend: {trend['trend']}")
        click.echo(f"- Mean score: {trend['mean']}")
        click.echo(f"- Anomalies detected: {len(anomalies)}")


@cli.group("monitor")
def monitor():
    """Monitoring commands."""
    pass


@monitor.command("trend")
@click.option("--days", default=7, type=int)
def monitor_trend(days):
    metrics = load_metrics(days)
    result = trend_analysis(metrics)
    click.echo(json.dumps(result, indent=2))


@monitor.command("anomalies")
@click.option("--days", default=7, type=int)
def monitor_anomalies(days):
    metrics = load_metrics(days)
    result = detect_anomalies(metrics)
    click.echo(json.dumps(result, indent=2))


# ── inject ────────────────────────────────────────────────────────────────────
@cli.command("inject")
@click.option("--model", required=True, help="Model name to inject params for")
def inject(model):
    """Inject current parameters into openclaw.json for a specific model."""
    state = load_state()
    params = {
        "temperature": state.get("temperature"),
        "top_p": state.get("top_p"),
        "seed": state.get("seed"),
    }
    result = inject_model_params(model, params)
    click.echo(json.dumps(result, indent=2))


# ── reset ─────────────────────────────────────────────────────────────────────
@cli.command("reset")
@click.option("--all", "reset_all", is_flag=True, default=False)
def reset(reset_all):
    """Reset parameters to defaults."""
    if reset_all:
        save_state(dict(DEFAULTS))
        click.echo(json.dumps({"status": "reset", "state": DEFAULTS}, indent=2))
    else:
        click.echo(json.dumps({"status": "no-op", "hint": "Use --all to reset all parameters"}))


def main():
    cli()
PYEOF

cat > /opt/detcontrol/setup.py << 'PYEOF'
from setuptools import setup, find_packages
setup(
    name="ai-deterministic-control",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "detcontrol=detcontrol.cli:main",
        ]
    },
    install_requires=["click", "scikit-learn", "numpy"],
)
PYEOF

cd /opt/detcontrol && pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple -q

echo "=== detcontrol installed ==="
detcontrol --help

# Ensure openclaw workspace dir exists
mkdir -p ~/.openclaw/workspace

echo "=== Setup complete ==="