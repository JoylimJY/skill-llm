#!/usr/bin/env python3
"""
Generate the sandbox workspace for the model-resource-profiler task.
"""
import json
import gzip
import os
import random
from pathlib import Path

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
random.seed(42)

# ── Directory skeleton ────────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "artifacts/run_20240315_bert_large",
    "artifacts/run_20240315_bert_large/checkpoints",
    "artifacts/run_old_20240101",
    "artifacts/run_old_20240101/logs",
    "configs/trainer",
    "configs/model",
    "logs/slurm",
    "notebooks",
    "data/tokenized",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────
distractors = {
    "configs/trainer/deepspeed_z2.json": json.dumps({"zero_optimization": {"stage": 2}, "fp16": {"enabled": True}}),
    "configs/model/bert_large.json": json.dumps({"hidden_size": 1024, "num_layers": 24, "num_heads": 16}),
    "logs/slurm/job_4821.out": "Epoch 1/3  loss=2.341  lr=1e-4\nEpoch 2/3  loss=1.872  lr=9e-5\n",
    "logs/slurm/job_4821.err": "WARNING:root:CUDA OOM avoided via gradient checkpointing\n",
    "artifacts/run_old_20240101/logs/summary.txt": "Old run — deprecated. Do not use.\n",
    "artifacts/run_old_20240101/perf_stats.csv": "step,loss,throughput\n100,2.1,312\n200,1.8,308\n",
    "notebooks/exploratory_analysis.ipynb": json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    "data/tokenized/shard_000.bin.stub": "binary stub placeholder\n",
    "artifacts/run_20240315_bert_large/checkpoints/step_1000.ckpt.stub": "checkpoint placeholder\n",
    "configs/trainer/fsdp_config.yaml": "sharding_strategy: FULL_SHARD\ncpu_offload: false\n",
    "artifacts/run_20240315_bert_large/trainer_args.json": json.dumps({
        "model": "bert-large-uncased", "batch_size": 32, "seq_len": 512,
        "precision": "bf16", "parallelism": "fsdp"
    }),
}
for rel, content in distractors.items():
    p = WORKSPACE / rel
    p.write_text(content)

# ── Memory snapshot JSON ──────────────────────────────────────────────────────
# Realistic Torch CUDA memory snapshot structure
memory_snapshot = {
    "device_traces": [],
    "segments": [
        {
            "device": 0,
            "address": 140234567890,
            "total_size": 2147483648,   # 2 GiB reserved
            "requested_size": 1879048192,  # ~1.75 GiB allocated
            "active_size": 1572864000,     # ~1.5 GiB active
            "stream": 0,
            "segment_type": "large",
            "blocks": [
                {"size": 536870912, "state": "active_allocated", "requested_size": 536870912},
                {"size": 524288000, "state": "active_allocated", "requested_size": 500000000},
                {"size": 268435456, "state": "inactive",         "requested_size": 0},
                {"size": 243269632, "state": "active_allocated", "requested_size": 240000000},
                {"size": 268435456, "state": "inactive",         "requested_size": 0},
                {"size": 305659904, "state": "active_allocated", "requested_size": 295723008},
            ],
        },
        {
            "device": 0,
            "address": 140236715373,
            "total_size": 524288000,     # 500 MiB reserved
            "requested_size": 314572800, # 300 MiB allocated
            "active_size": 209715200,    # 200 MiB active
            "stream": 1,
            "segment_type": "large",
            "blocks": [
                {"size": 209715200, "state": "active_allocated", "requested_size": 200000000},
                {"size": 104857600, "state": "inactive",         "requested_size": 0},
            ],
        },
        {
            "device": 0,
            "address": 140237239661,
            "total_size": 10485760,      # 10 MiB reserved (small pool)
            "requested_size": 5242880,
            "active_size": 4194304,
            "stream": 0,
            "segment_type": "small",
            "blocks": [
                {"size": 4194304, "state": "active_allocated", "requested_size": 4000000},
                {"size": 6291456, "state": "inactive",         "requested_size": 0},
            ],
        },
    ],
    "allocator_settings": {
        "max_split_size": 512,
        "garbage_collection_threshold": 0.8,
        "expandable_segments": False,
    },
    "stats": [
        {
            "device": 0,
            "num_alloc_retries": 14,
            "num_ooms": 0,
            "num_sync_all_streams": 3,
            "allocated_bytes": {"current": 1879048192, "peak": 2516582400},
            "reserved_bytes": {"current": 2682257408, "peak": 3221225472},
            "active_bytes": {"current": 1572864000, "peak": 2000000000},
        }
    ],
}

mem_path = WORKSPACE / "artifacts/run_20240315_bert_large/memory_snapshot.json"
mem_path.write_text(json.dumps(memory_snapshot, indent=2))

# ── CPU trace JSON.GZ (Chrome trace format) ───────────────────────────────────
# Realistic PyTorch profiler Chrome trace with traceEvents
trace_events = []

# Build a varied set of ops
ops = [
    ("aten::linear",       1, 45000),   # (name, tid, duration_us)
    ("aten::linear",       1, 43200),
    ("aten::linear",       1, 41800),
    ("aten::mm",           1, 38500),
    ("aten::mm",           1, 37200),
    ("aten::mm",           1, 36900),
    ("aten::addmm",        1, 22100),
    ("aten::addmm",        1, 21500),
    ("aten::layer_norm",   1, 18300),
    ("aten::layer_norm",   1, 17900),
    ("aten::layer_norm",   1, 17500),
    ("aten::softmax",      1,  9800),
    ("aten::softmax",      1,  9600),
    ("aten::dropout",      1,  3200),
    ("aten::dropout",      1,  3100),
    ("aten::relu",         1,  2400),
    ("aten::relu",         1,  2300),
    ("DataLoader::next",   2, 85000),   # expensive dataloader
    ("DataLoader::next",   2, 83000),
    ("aten::copy_",        2,  5500),
    ("aten::copy_",        2,  5300),
    ("Optimizer::step",    1, 61000),
    ("Optimizer::step",    1, 59000),
    ("aten::adam",         1, 28000),
    ("aten::adam",         1, 27500),
    ("ProfilerStep#1",     0, 500000),
    ("ProfilerStep#2",     0, 498000),
]

ts = 1000  # start timestamp in microseconds
for name, tid, dur in ops:
    trace_events.append({
        "ph": "X",
        "cat": "cpu_op",
        "name": name,
        "pid": 1,
        "tid": tid,
        "ts": ts,
        "dur": dur,
        "args": {"Input dims": [], "Input type": [], "Concrete Inputs": []}
    })
    ts += dur + random.randint(50, 500)

# Add some metadata events
trace_events.insert(0, {"ph": "M", "pid": 1, "tid": 1, "name": "process_name", "args": {"name": "python"}})
trace_events.insert(1, {"ph": "M", "pid": 1, "tid": 2, "name": "thread_name",  "args": {"name": "DataLoader_0"}})

chrome_trace = {"traceEvents": trace_events}

trace_path = WORKSPACE / "artifacts/run_20240315_bert_large/cpu_trace.json.gz"
with gzip.open(trace_path, "wt", encoding="utf-8") as f:
    json.dump(chrome_trace, f)

# ── Analysis script ───────────────────────────────────────────────────────────
analyze_script = r'''#!/usr/bin/env python3
"""
scripts/analyze_profile.py
Deterministic resource profiler analyzer for Torch CUDA memory snapshots and
PyTorch Chrome-format CPU traces.
"""
import argparse
import gzip
import json
import sys
from pathlib import Path
from collections import defaultdict


def load_json(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        sys.exit(f"ERROR: File not found: {path}")
    if p.suffix == ".gz" or path.endswith(".json.gz"):
        with gzip.open(p, "rt", encoding="utf-8") as f:
            return json.load(f)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def analyze_memory(data: dict) -> dict:
    segments = data.get("segments", [])
    stats_list = data.get("stats", [])
    alloc_settings = data.get("allocator_settings", {})

    total_reserved = sum(s.get("total_size", 0) for s in segments)
    total_allocated = sum(s.get("requested_size", 0) for s in segments)
    total_active = sum(s.get("active_size", 0) for s in segments)

    # Fragmentation: inactive bytes / reserved bytes
    total_inactive = sum(
        b.get("size", 0)
        for s in segments
        for b in s.get("blocks", [])
        if b.get("state") == "inactive"
    )
    frag_ratio = total_inactive / total_reserved if total_reserved > 0 else 0.0

    # Largest segments
    sorted_segs = sorted(segments, key=lambda s: s.get("total_size", 0), reverse=True)
    top_segments = [
        {
            "device": s.get("device"),
            "type": s.get("segment_type"),
            "total_size_bytes": s.get("total_size", 0),
            "active_size_bytes": s.get("active_size", 0),
            "stream": s.get("stream"),
        }
        for s in sorted_segs[:3]
    ]

    # Allocator churn
    alloc_retries = 0
    num_ooms = 0
    if stats_list:
        s0 = stats_list[0]
        alloc_retries = s0.get("num_alloc_retries", 0)
        num_ooms = s0.get("num_ooms", 0)

    fragmentation_risk = "HIGH" if frag_ratio > 0.20 else ("MEDIUM" if frag_ratio > 0.10 else "LOW")

    return {
        "total_reserved_bytes": total_reserved,
        "total_allocated_bytes": total_allocated,
        "total_active_bytes": total_active,
        "total_inactive_bytes": total_inactive,
        "fragmentation_ratio": round(frag_ratio, 4),
        "fragmentation_risk": fragmentation_risk,
        "num_segments": len(segments),
        "top_segments": top_segments,
        "alloc_retries": alloc_retries,
        "num_ooms": num_ooms,
        "allocator_settings": alloc_settings,
    }


def analyze_cpu(data: dict) -> dict:
    events = data.get("traceEvents", [])
    # Only X-phase (complete) cpu_op events
    cpu_ops = [e for e in events if e.get("ph") == "X" and e.get("cat") == "cpu_op"]

    # Aggregate by name
    op_totals = defaultdict(lambda: {"total_us": 0, "count": 0})
    for e in cpu_ops:
        name = e.get("name", "unknown")
        dur = e.get("dur", 0)
        op_totals[name]["total_us"] += dur
        op_totals[name]["count"] += 1

    # Sort by total duration descending
    top_ops = sorted(op_totals.items(), key=lambda kv: kv[1]["total_us"], reverse=True)[:10]
    top_ops_list = [
        {"name": k, "total_us": v["total_us"], "count": v["count"],
         "avg_us": round(v["total_us"] / v["count"], 1)}
        for k, v in top_ops
    ]

    # Per-thread breakdown
    thread_totals = defaultdict(int)
    for e in cpu_ops:
        thread_totals[str(e.get("tid", "?"))] += e.get("dur", 0)
    top_threads = sorted(thread_totals.items(), key=lambda kv: kv[1], reverse=True)

    # Trace window
    ts_values = [e.get("ts", 0) for e in cpu_ops]
    dur_values = [e.get("dur", 0) for e in cpu_ops]
    if ts_values:
        trace_start_us = min(ts_values)
        trace_end_us = max(t + d for t, d in zip(ts_values, dur_values))
        trace_window_us = trace_end_us - trace_start_us
    else:
        trace_start_us = trace_end_us = trace_window_us = 0

    # Dominant family detection
    family_map = {
        "linear": "matmul_linear",
        "mm": "matmul_linear",
        "addmm": "matmul_linear",
        "layer_norm": "normalization",
        "softmax": "normalization",
        "relu": "activation",
        "dropout": "regularization",
        "adam": "optimizer",
        "Optimizer": "optimizer",
        "DataLoader": "dataloader",
        "copy_": "data_movement",
    }
    family_totals = defaultdict(int)
    for name, agg in op_totals.items():
        assigned = "other"
        for kw, fam in family_map.items():
            if kw in name:
                assigned = fam
                break
        family_totals[assigned] += agg["total_us"]
    dominant_family = max(family_totals, key=family_totals.get) if family_totals else "unknown"

    return {
        "event_count": len(cpu_ops),
        "trace_start_us": trace_start_us,
        "trace_end_us": trace_end_us,
        "trace_window_us": trace_window_us,
        "top_ops": top_ops_list,
        "top_threads": [{"tid": t, "total_us": d} for t, d in top_threads],
        "family_totals": dict(family_totals),
        "dominant_family": dominant_family,
    }


def build_markdown(mem_result: dict | None, cpu_result: dict | None) -> str:
    lines = ["# Model Resource Profiler Report", ""]

    if mem_result:
        lines += [
            "## Memory Analysis",
            "",
            f"- **Reserved**: {mem_result['total_reserved_bytes']:,} bytes ({mem_result['total_reserved_bytes']/1e9:.2f} GB)",
            f"- **Allocated (requested)**: {mem_result['total_allocated_bytes']:,} bytes ({mem_result['total_allocated_bytes']/1e9:.2f} GB)",
            f"- **Active**: {mem_result['total_active_bytes']:,} bytes ({mem_result['total_active_bytes']/1e9:.2f} GB)",
            f"- **Inactive (fragmented)**: {mem_result['total_inactive_bytes']:,} bytes",
            f"- **Fragmentation Ratio**: {mem_result['fragmentation_ratio']:.2%}",
            f"- **Fragmentation Risk**: {mem_result['fragmentation_risk']}",
            f"- **Segments**: {mem_result['num_segments']}",
            f"- **Alloc Retries**: {mem_result['alloc_retries']}",
            f"- **OOMs**: {mem_result['num_ooms']}",
            "",
            "### Top Segments",
            "",
        ]
        for i, seg in enumerate(mem_result["top_segments"], 1):
            lines.append(
                f"{i}. Device={seg['device']} type={seg['type']} "
                f"reserved={seg['total_size_bytes']:,}B active={seg['active_size_bytes']:,}B stream={seg['stream']}"
            )
        lines.append("")

    if cpu_result:
        lines += [
            "## CPU Trace Analysis",
            "",
            f"- **Event Count**: {cpu_result['event_count']}",
            f"- **Trace Window**: {cpu_result['trace_window_us']:,} µs",
            f"- **Dominant Family**: {cpu_result['dominant_family']}",
            "",
            "### Top CPU Operations (by total duration)",
            "",
        ]
        for i, op in enumerate(cpu_result["top_ops"], 1):
            lines.append(
                f"{i}. `{op['name']}` — total={op['total_us']:,} µs  "
                f"count={op['count']}  avg={op['avg_us']} µs"
            )
        lines.append("")
        lines += ["### Thread Breakdown", ""]
        for t in cpu_result["top_threads"]:
            lines.append(f"- Thread {t['tid']}: {t['total_us']:,} µs")
        lines.append("")

    lines += [
        "## Diagnosis & Recommendations",
        "",
    ]
    if mem_result and mem_result["fragmentation_risk"] in ("HIGH", "MEDIUM"):
        lines.append(
            f"- **[MEMORY]** Fragmentation risk is {mem_result['fragmentation_risk']} "
            f"({mem_result['fragmentation_ratio']:.2%} inactive). "
            "Consider enabling expandable segments or reducing max_split_size."
        )
    if mem_result and mem_result["alloc_retries"] > 5:
        lines.append(
            f"- **[MEMORY]** {mem_result['alloc_retries']} allocator retries detected — "
            "potential memory pressure. Profile with smaller batch or gradient checkpointing."
        )
    if cpu_result and cpu_result["dominant_family"] == "dataloader":
        lines.append(
            "- **[CPU]** DataLoader dominates CPU time. "
            "Increase `num_workers`, enable `pin_memory`, or prefetch asynchronously."
        )
    if cpu_result and cpu_result["dominant_family"] in ("matmul_linear",):
        lines.append(
            "- **[CPU]** Matmul/linear ops dominate. Verify tensor cores are active "
            "(bf16/fp16 precision, contiguous tensors)."
        )
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Model resource profiler analyzer")
    parser.add_argument("--memory-json", dest="memory_json", default=None)
    parser.add_argument("--cpu-trace",   dest="cpu_trace",   default=None)
    parser.add_argument("--md-out",      dest="md_out",      default=None)
    parser.add_argument("--json-out",    dest="json_out",    default=None)
    args = parser.parse_args()

    if not args.memory_json and not args.cpu_trace:
        sys.exit("ERROR: Provide at least one of --memory-json or --cpu-trace.")

    mem_result = None
    cpu_result = None

    if args.memory_json:
        data = load_json(args.memory_json)
        mem_result = analyze_memory(data)

    if args.cpu_trace:
        data = load_json(args.cpu_trace)
        cpu_result = analyze_cpu(data)

    # Build outputs
    report = {}
    if mem_result:
        report["memory"] = mem_result
    if cpu_result:
        report["cpu"] = cpu_result

    md_content = build_markdown(mem_result, cpu_result)

    if args.md_out:
        Path(args.md_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.md_out).write_text(md_content, encoding="utf-8")
        print(f"Markdown report written to: {args.md_out}")
    else:
        print(md_content)

    if args.json_out:
        Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_out).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"JSON report written to: {args.json_out}")


if __name__ == "__main__":
    main()
'''

(WORKSPACE / "scripts" / "analyze_profile.py").write_text(analyze_script)

# ── Interpretation rubric ─────────────────────────────────────────────────────
interp_md = """# Interpretation Rubric

## Memory Fragmentation
- **HIGH** (>20% inactive/reserved): Immediate action required. Enable expandable_segments or reduce max_split_size.
- **MEDIUM** (10–20%): Monitor. Evaluate gradient checkpointing.
- **LOW** (<10%): Acceptable.

## Allocator Churn
- More than 5 retries per training step: Suspect memory pressure or large ephemeral tensors.
- Any OOM event: Critical — reduce batch size or enable offloading.

## CPU Hotspots
- Dominant DataLoader family: I/O-bound training — increase num_workers.
- Dominant matmul_linear family: Compute-bound — verify tensor cores and mixed precision.
- Dominant optimizer family: Large model or frequent updates — consider gradient accumulation.

## Confidence Levels
- HIGH: Both memory and CPU artifacts present, same run.
- MEDIUM: Single artifact only.
- LOW: Aggregated stats without per-layer breakdown.
"""
(WORKSPACE / "references" / "interpretation.md").write_text(interp_md)

print("Workspace generation complete.")
print(f"Memory snapshot: {mem_path}")
print(f"CPU trace:       {trace_path}")