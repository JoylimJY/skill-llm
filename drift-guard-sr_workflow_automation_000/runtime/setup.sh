#!/usr/bin/env bash
set -euo pipefail

# ── Clone the Drift Guard skill from the public registry ────────────────────
cd /workspace

# The skill is published as an OpenClaw-compatible package.
# We fetch it directly from the public GitHub repository.
git clone https://github.com/TheShadowRose/drift-guard-sr.git skill_src 2>/dev/null || true

# If clone succeeded, copy scripts to workspace root
if [ -d "skill_src" ]; then
    cp skill_src/*.py /workspace/ 2>/dev/null || true
    cp skill_src/config_example.py /workspace/ 2>/dev/null || true
    ls -la /workspace/*.py 2>/dev/null || echo "No .py files copied from skill_src"
fi

# ── If GitHub clone fails (network issues), provide stub scripts ────────────
# These stubs implement the EXACT documented behavior so the eval is deterministic.

if [ ! -f "/workspace/config_example.py" ]; then
cat > /workspace/config_example.py << 'PYEOF'
CONFIG = {
    "baseline_file": "baseline.json",
    "history_file": "drift_history.json",
    "thresholds": {
        "warning": 0.3,
        "critical": 0.6,
        "emergency": 0.9,
    },
    "weights": {
        "char_count": 1.0,
        "word_count": 1.0,
        "sentence_count": 1.0,
        "avg_sentence_length": 1.0,
        "vocabulary_diversity": 2.0,
        "sycophancy_score": 3.0,
        "hedging_score": 2.0,
        "validation_score": 2.0,
        "exclamation_count": 1.5,
        "technical_score": 2.0,
    },
    "sycophancy_markers": [
        "absolutely", "completely", "totally", "definitely", "certainly",
        "of course", "you're right", "great point", "excellent", "perfect",
        "i agree", "well said", "good point", "exactly", "precisely",
    ],
    "hedging_markers": [
        "perhaps", "maybe", "might", "possibly", "could be", "uncertain",
        "not sure", "i think", "i believe", "seems like", "appears to",
        "arguably", "potentially", "somewhat", "rather", "fairly",
    ],
    "validation_markers": [
        "amazing", "wonderful", "fantastic", "brilliant", "incredible",
        "impressive", "outstanding", "superb", "great job", "well done",
        "kudos", "bravo", "excellent work", "good work", "nice work",
    ],
    "technical_markers": [
        "algorithm", "implementation", "architecture", "optimization", "complexity",
        "framework", "infrastructure", "protocol", "interface", "abstraction",
        "clause", "provision", "indemnification", "liability", "arbitration",
        "jurisdiction", "enforceability", "warranty", "covenant", "estoppel",
    ],
}
PYEOF
echo "config_example.py created (stub)"
fi

if [ ! -f "/workspace/drift_baseline.py" ]; then
cat > /workspace/drift_baseline.py << 'PYEOF'
#!/usr/bin/env python3
"""Drift Guard - Baseline Capture Tool"""
import json
import sys
import re
import os
import argparse
from pathlib import Path
from datetime import datetime

def load_config():
    try:
        sys.path.insert(0, '/workspace')
        from config import CONFIG
        return CONFIG
    except ImportError:
        print("ERROR: config.py not found. Run: cp config_example.py config.py", file=sys.stderr)
        sys.exit(1)

def compute_metrics(text, config):
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    unique_words = set(w.lower() for w in words)

    text_lower = text.lower()

    def marker_score(markers):
        count = sum(text_lower.count(m) for m in markers)
        return count / max(len(words), 1)

    avg_sl = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)

    return {
        "char_count": len(text),
        "word_count": len(words),
        "sentence_count": len(sentences),
        "avg_sentence_length": round(avg_sl, 3),
        "vocabulary_diversity": round(len(unique_words) / max(len(words), 1), 4),
        "sycophancy_score": round(marker_score(config["sycophancy_markers"]), 4),
        "hedging_score": round(marker_score(config["hedging_markers"]), 4),
        "validation_score": round(marker_score(config["validation_markers"]), 4),
        "exclamation_count": text.count("!"),
        "technical_score": round(marker_score(config["technical_markers"]), 4),
    }

def capture(files, output):
    config = load_config()
    all_metrics = []
    for fp in files:
        text = Path(fp).read_text(encoding="utf-8")
        m = compute_metrics(text, config)
        m["source_file"] = str(fp)
        all_metrics.append(m)

    # Average each metric
    keys = [k for k in all_metrics[0].keys() if k != "source_file"]
    baseline = {}
    for k in keys:
        vals = [m[k] for m in all_metrics]
        baseline[k] = round(sum(vals) / len(vals), 4)

    result = {
        "created_at": datetime.utcnow().isoformat(),
        "sample_count": len(all_metrics),
        "metrics": baseline,
        "samples": all_metrics,
    }
    Path(output).write_text(json.dumps(result, indent=2))
    print(f"Baseline captured from {len(files)} files -> {output}")

def compare(baseline1, baseline2):
    b1 = json.loads(Path(baseline1).read_text())
    b2 = json.loads(Path(baseline2).read_text())
    print(f"Comparing {baseline1} vs {baseline2}")
    for k in b1["metrics"]:
        v1 = b1["metrics"][k]
        v2 = b2["metrics"].get(k, 0)
        delta = v2 - v1
        print(f"  {k}: {v1} -> {v2} (delta: {delta:+.4f})")

def main():
    parser = argparse.ArgumentParser(description="Drift Guard Baseline Tool")
    sub = parser.add_subparsers(dest="command")

    cap = sub.add_parser("capture")
    cap.add_argument("--files", nargs="+", required=True)
    cap.add_argument("--output", required=True)

    cmp = sub.add_parser("compare")
    cmp.add_argument("baseline1")
    cmp.add_argument("baseline2")

    args = parser.parse_args()
    if args.command == "capture":
        capture(args.files, args.output)
    elif args.command == "compare":
        compare(args.baseline1, args.baseline2)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
PYEOF
echo "drift_baseline.py created (stub)"
fi

if [ ! -f "/workspace/drift_guard.py" ]; then
cat > /workspace/drift_guard.py << 'PYEOF'
#!/usr/bin/env python3
"""Drift Guard - Continuous Monitoring Engine"""
import json
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime

def load_config():
    try:
        sys.path.insert(0, '/workspace')
        from config import CONFIG
        return CONFIG
    except ImportError:
        print("ERROR: config.py not found.", file=sys.stderr)
        sys.exit(1)

def compute_metrics(text, config):
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    unique_words = set(w.lower() for w in words)
    text_lower = text.lower()

    def marker_score(markers):
        count = sum(text_lower.count(m) for m in markers)
        return count / max(len(words), 1)

    avg_sl = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)

    return {
        "char_count": len(text),
        "word_count": len(words),
        "sentence_count": len(sentences),
        "avg_sentence_length": round(avg_sl, 3),
        "vocabulary_diversity": round(len(unique_words) / max(len(words), 1), 4),
        "sycophancy_score": round(marker_score(config["sycophancy_markers"]), 4),
        "hedging_score": round(marker_score(config["hedging_markers"]), 4),
        "validation_score": round(marker_score(config["validation_markers"]), 4),
        "exclamation_count": text.count("!"),
        "technical_score": round(marker_score(config["technical_markers"]), 4),
    }

def compute_drift(current, baseline_metrics, weights):
    total_weight = 0
    weighted_diff = 0
    for k, weight in weights.items():
        if k not in baseline_metrics or k not in current:
            continue
        base_val = baseline_metrics[k]
        curr_val = current[k]
        if base_val == 0 and curr_val == 0:
            pct_diff = 0.0
        elif base_val == 0:
            pct_diff = 1.0
        else:
            pct_diff = min(abs(curr_val - base_val) / abs(base_val), 1.0)
        weighted_diff += pct_diff * weight
        total_weight += weight
    return round(weighted_diff / total_weight, 4) if total_weight > 0 else 0.0

class DriftGuard:
    def __init__(self, config):
        self.config = config
        self.baseline = None
        bf = config.get("baseline_file", "baseline.json")
        if Path(bf).exists():
            data = json.loads(Path(bf).read_text())
            self.baseline = data["metrics"]

    def monitor(self, text):
        config = self.config
        metrics = compute_metrics(text, config)
        drift_score = 0.0
        if self.baseline:
            drift_score = compute_drift(metrics, self.baseline, config["weights"])

        thresholds = config["thresholds"]
        if drift_score >= thresholds["emergency"]:
            alert_level = "emergency"
        elif drift_score >= thresholds["critical"]:
            alert_level = "critical"
        elif drift_score >= thresholds["warning"]:
            alert_level = "warning"
        else:
            alert_level = "normal"

        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "drift_score": drift_score,
            "alert_level": alert_level,
            "metrics": metrics,
        }

        # Append to history
        hf = config.get("history_file", "drift_history.json")
        history = []
        if Path(hf).exists():
            history = json.loads(Path(hf).read_text())
        history.append(result)
        Path(hf).write_text(json.dumps(history, indent=2))

        return result

def main():
    parser = argparse.ArgumentParser(description="Drift Guard Monitor")
    parser.add_argument("file", nargs="?", help="Response file to analyze")
    parser.add_argument("--stdin", action="store_true", help="Read from stdin")
    args = parser.parse_args()

    from config import CONFIG
    dg = DriftGuard(CONFIG)

    if args.stdin:
        text = sys.stdin.read()
    elif args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    else:
        print("ERROR: provide file or --stdin", file=sys.stderr)
        sys.exit(1)

    result = dg.monitor(text)
    score = result["drift_score"]
    level = result["alert_level"].upper()
    print(f"Drift score: {score:.3f} ({level})")
    if level in ("WARNING", "CRITICAL", "EMERGENCY"):
        print(f"ALERT: Agent drift detected ({score:.3f})")

if __name__ == "__main__":
    main()
PYEOF
echo "drift_guard.py created (stub)"
fi

if [ ! -f "/workspace/drift_report.py" ]; then
cat > /workspace/drift_report.py << 'PYEOF'
#!/usr/bin/env python3
"""Drift Guard - Trend Analysis & Reporting"""
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta
import statistics

def load_config():
    try:
        sys.path.insert(0, '/workspace')
        from config import CONFIG
        return CONFIG
    except ImportError:
        print("ERROR: config.py not found.", file=sys.stderr)
        sys.exit(1)

def detect_anomalies(scores):
    if len(scores) < 3:
        return []
    mean = statistics.mean(scores)
    stdev = statistics.stdev(scores) if len(scores) > 1 else 0
    return [i for i, s in enumerate(scores) if stdev > 0 and abs(s - mean) > 2 * stdev]

def main():
    parser = argparse.ArgumentParser(description="Drift Guard Report")
    parser.add_argument("--hours", type=float, default=None, help="Filter to last N hours")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    config = load_config()
    hf = config.get("history_file", "drift_history.json")

    if not Path(hf).exists():
        print("No drift history found.", file=sys.stderr)
        sys.exit(1)

    history = json.loads(Path(hf).read_text())

    if args.hours is not None:
        cutoff = datetime.utcnow() - timedelta(hours=args.hours)
        history = [
            h for h in history
            if datetime.fromisoformat(h["timestamp"]) >= cutoff
        ]

    if not history:
        print("No measurements in time range.")
        return

    scores = [h["drift_score"] for h in history]
    levels = [h["alert_level"] for h in history]
    mean_drift = statistics.mean(scores)
    max_drift = max(scores)
    min_drift = min(scores)
    trend = "worsening" if len(scores) > 1 and scores[-1] > scores[0] else "improving"
    anomaly_indices = detect_anomalies(scores)

    # Per-metric averages
    metric_keys = list(history[0]["metrics"].keys()) if history else []
    metric_avgs = {}
    for k in metric_keys:
        vals = [h["metrics"].get(k, 0) for h in history]
        metric_avgs[k] = round(statistics.mean(vals), 4)

    alert_counts = {}
    for lv in levels:
        alert_counts[lv] = alert_counts.get(lv, 0) + 1

    report = {
        "measurement_count": len(history),
        "time_range_hours": args.hours,
        "mean_drift_score": round(mean_drift, 4),
        "max_drift_score": round(max_drift, 4),
        "min_drift_score": round(min_drift, 4),
        "trend": trend,
        "anomaly_count": len(anomaly_indices),
        "anomaly_indices": anomaly_indices,
        "alert_counts": alert_counts,
        "metric_averages": metric_avgs,
        "measurements": history,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(f"=== Drift Guard Report ===")
        print(f"Measurements: {report['measurement_count']}")
        print(f"Mean Drift:   {report['mean_drift_score']:.4f}")
        print(f"Max Drift:    {report['max_drift_score']:.4f}")
        print(f"Min Drift:    {report['min_drift_score']:.4f}")
        print(f"Trend:        {report['trend']}")
        print(f"Anomalies:    {report['anomaly_count']}")
        print(f"Alert Counts: {report['alert_counts']}")
        print(f"\nMetric Averages:")
        for k, v in report["metric_averages"].items():
            print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
PYEOF
echo "drift_report.py created (stub)"
fi

chmod +x /workspace/drift_baseline.py
chmod +x /workspace/drift_guard.py
chmod +x /workspace/drift_report.py

echo "Drift Guard scripts ready in /workspace"
ls -la /workspace/*.py