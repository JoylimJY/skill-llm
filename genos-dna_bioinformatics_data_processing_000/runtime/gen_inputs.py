import os
import json
import random
import hashlib

random.seed(42)

# Create workspace directory structure
os.makedirs("/workspace/scripts", exist_ok=True)
os.makedirs("/workspace/models/Genos-1___2B", exist_ok=True)
os.makedirs("/workspace/data/raw_sequences", exist_ok=True)
os.makedirs("/workspace/data/processed", exist_ok=True)
os.makedirs("/workspace/lab_notes", exist_ok=True)
os.makedirs("/workspace/configs", exist_ok=True)
os.makedirs("/workspace/results/old_runs", exist_ok=True)
os.makedirs("/workspace/utils", exist_ok=True)

# ─── Create the actual genos_dna.py script (the "existing" skill script) ──────
genos_dna_content = '''#!/usr/bin/env python3
"""
Genos DNA Sequence Analysis Module
Simulates the Genos-1.2B model for DNA sequence analysis.
"""

import os
import sys
import json
import hashlib

_MODEL_LOADED = False
_MODEL_PATH = None

def load_model(model_path=None):
    """Load the Genos-1.2B model."""
    global _MODEL_LOADED, _MODEL_PATH
    if model_path is None:
        model_path = os.environ.get("GENOS_MODEL_PATH", "./models/Genos-1___2B")
    _MODEL_PATH = model_path
    if not os.path.isdir(model_path):
        raise FileNotFoundError(f"Model directory not found: {model_path}. "
                                 f"Ensure GENOS_MODEL_PATH is set correctly.")
    _MODEL_LOADED = True
    return True

def _check_loaded():
    if not _MODEL_LOADED:
        raise RuntimeError("Model not loaded. Call load_model() first.")

def _validate_sequence(seq):
    """Validate that sequence contains only ACGTN characters."""
    invalid = set(seq.upper()) - set("ACGTN")
    if invalid:
        raise ValueError(f"Invalid characters in sequence: {invalid}. "
                         f"Only A, C, G, T, N are supported.")
    return seq.upper()

def analyze_dna_sequence(sequence):
    """
    Analyze a DNA sequence and return base composition statistics.
    Returns dict with keys: length, A_count, C_count, G_count, T_count, N_count,
                            GC_content, AT_content, sequence_hash
    """
    _check_loaded()
    seq = _validate_sequence(sequence)
    length = len(seq)
    if length == 0:
        raise ValueError("Sequence cannot be empty.")
    counts = {b: seq.count(b) for b in "ACGTN"}
    gc = (counts["G"] + counts["C"]) / length * 100
    at = (counts["A"] + counts["T"]) / length * 100
    seq_hash = hashlib.md5(seq.encode()).hexdigest()
    return {
        "length": length,
        "A_count": counts["A"],
        "C_count": counts["C"],
        "G_count": counts["G"],
        "T_count": counts["T"],
        "N_count": counts["N"],
        "GC_content": round(gc, 4),
        "AT_content": round(at, 4),
        "sequence_hash": seq_hash
    }

def predict_next_base(sequence, n_predictions=5):
    """
    Predict the next n likely bases following the given sequence.
    Returns dict with keys: predictions (list of dicts with base and probability)
    """
    _check_loaded()
    seq = _validate_sequence(sequence)
    if len(seq) < 3:
        raise ValueError("Sequence must be at least 3 bases long for prediction.")
    # Deterministic pseudo-prediction based on last 3 bases
    seed_val = sum(ord(c) * (i+1) for i, c in enumerate(seq[-3:]))
    bases = ["A", "C", "G", "T"]
    rng = __import__("random")
    rng.seed(seed_val)
    raw = [rng.random() for _ in bases]
    total = sum(raw)
    probs = [round(r / total, 4) for r in raw]
    # Normalize so sum == 1.0
    probs[-1] = round(1.0 - sum(probs[:-1]), 4)
    predictions = []
    for _ in range(n_predictions):
        pick_seed = seed_val + _
        rng.seed(pick_seed)
        idx = rng.choices(range(4), weights=probs, k=1)[0]
        predictions.append({"base": bases[idx], "probability": probs[idx]})
    return {
        "input_length": len(seq),
        "last_3_bases": seq[-3:],
        "predictions": predictions,
        "base_probabilities": dict(zip(bases, probs))
    }

def extract_sequence_features(sequence):
    """
    Extract advanced features from DNA sequence.
    Returns dict with: dinucleotide_frequencies, cpg_count, cpg_ratio,
                       homopolymer_runs, complexity_score
    """
    _check_loaded()
    seq = _validate_sequence(sequence)
    if len(seq) < 4:
        raise ValueError("Sequence must be at least 4 bases long for feature extraction.")
    # Dinucleotide frequencies
    dinucs = {}
    for i in range(len(seq) - 1):
        dn = seq[i:i+2]
        dinucs[dn] = dinucs.get(dn, 0) + 1
    total_dn = sum(dinucs.values())
    dinuc_freq = {k: round(v / total_dn, 4) for k, v in sorted(dinucs.items())}
    # CpG count
    cpg_count = seq.count("CG")
    cpg_ratio = round(cpg_count / total_dn, 4) if total_dn > 0 else 0.0
    # Homopolymer runs (stretches of same base >= 3)
    homopolymers = []
    i = 0
    while i < len(seq):
        j = i
        while j < len(seq) and seq[j] == seq[i]:
            j += 1
        if j - i >= 3:
            homopolymers.append({"base": seq[i], "start": i, "length": j - i})
        i = j
    # Sequence complexity (Shannon entropy)
    from math import log2
    counts = {b: seq.count(b) for b in "ACGT"}
    n = len(seq)
    entropy = 0.0
    for c in counts.values():
        if c > 0:
            p = c / n
            entropy -= p * log2(p)
    complexity_score = round(entropy / 2.0, 4)  # normalized to [0,1] range
    return {
        "dinucleotide_frequencies": dinuc_freq,
        "cpg_count": cpg_count,
        "cpg_ratio": cpg_ratio,
        "homopolymer_runs": homopolymers,
        "complexity_score": complexity_score
    }
'''

with open("/workspace/scripts/genos_dna.py", "w") as f:
    f.write(genos_dna_content)

# ─── Model directory stub files ───────────────────────────────────────────────
with open("/workspace/models/Genos-1___2B/config.json", "w") as f:
    json.dump({
        "model_type": "genos_moe",
        "vocab_size": 128,
        "num_parameters": "1.2B",
        "architecture": "MoE",
        "max_context_length": 1000000
    }, f, indent=2)

with open("/workspace/models/Genos-1___2B/tokenizer_config.json", "w") as f:
    json.dump({"bases": ["A", "C", "G", "T", "N"]}, f)

# ─── THE MAIN INPUT: Messy FASTA-format sequence file ─────────────────────────
# The agent must clean this before analysis.
# Canonical clean sequence (what should be analyzed):
clean_seq = (
    "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"
    "ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGAT"
    "CGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCG"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"
    "GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAG"
    "NNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN"
    "ACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTAC"
    "GTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGT"
    "CGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"
)

# Build a messy FASTA with:
# - FASTA headers (>)
# - Line numbers inserted  
# - Lowercase letters
# - Spaces and tabs mid-sequence
# - Numeric characters (simulating quality scores mixed in)
# - Blank lines
# - A comment line
messy_fasta = """>chr1_sample_region_GRCh38_position_1234567 | Lab ID: ZJL-2024-0042 | Quality: PASS
; This sequence was extracted from patient sample #7 on 2024-03-15
1   ATGCGATCGATCGATCGATCGATCGATcgatcgatcgatcgATCGATCGATCGATCGATCGATCGATCG
2   ATCGATCGATCGATCGATCGATCGATCGATCGATCGatcgatcgatcgatcgatcgatcgatcgatcgat
3   CGCGCGCGCGCGCGCGCGCGCGCGCGCGcgcgcgcgcgcgcgcgcgcgcgcgcgcgcgcgcgcgcgcgcg
4   CGCGCGCGCGCGCGCGCGCGCGCGCGCGcgcgcgcgcgcgcgcgcgcgcgcgcgcgcgcgcgcgcgcgcg

5   AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
6   TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
7   GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGctag
8   NNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNnnnnn
9   nnnnnnnnnnnnnnn
10  ACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTacgtac
11  gtacgtacgtacgtacgtacgtacgtacgtacgtacgtacgtacgtacgtacgtacgtacgtacgtacgt
12  CGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATcgatcg
"""

with open("/workspace/data/raw_sequences/sample_GRCh38_chr1_ZJL2024.fasta", "w") as f:
    f.write(messy_fasta)

# ─── Distractor files ─────────────────────────────────────────────────────────

# Lab notes
with open("/workspace/lab_notes/experiment_log_2024.txt", "w") as f:
    f.write("Lab Experiment Log - ZJL Genomics Lab\n")
    f.write("Date: 2024-03-15\nSample: Patient #7\n")
    f.write("Notes: Sequence extracted via Illumina HiSeq 4000\n")
    f.write("Coverage: 30x, PHRED score > 30 for 95% of bases\n")

with open("/workspace/lab_notes/sample_metadata.csv", "w") as f:
    f.write("sample_id,patient_id,date,platform,coverage\n")
    f.write("ZJL-2024-0042,P7,2024-03-15,HiSeq4000,30x\n")
    f.write("ZJL-2024-0041,P6,2024-03-14,HiSeq4000,25x\n")

# Old/wrong config files to confuse the agent
with open("/workspace/configs/old_model_config.json", "w") as f:
    json.dump({"model_path": "./models/Genos-1.2B", "state_file": "./.state"}, f)

with open("/workspace/configs/pipeline_config.yaml", "w") as f:
    f.write("pipeline:\n  input_dir: ./data/raw_sequences\n  output_dir: ./results\n")
    f.write("  model: genos_v1\n  batch_size: 32\n")

# Distractor scripts
with open("/workspace/utils/sequence_utils.py", "w") as f:
    f.write("# Utility functions - legacy code, do not use\n")
    f.write("def old_gc_content(seq):\n    return (seq.count('G')+seq.count('C'))/len(seq)\n")

with open("/workspace/utils/fasta_parser.py", "w") as f:
    f.write("# Basic FASTA parser - not compatible with Genos\n")
    f.write("def parse_fasta(path):\n    seqs={}\n    return seqs\n")

# Old results
with open("/workspace/results/old_runs/run_2024_01_10_summary.txt", "w") as f:
    f.write("Old run summary - DO NOT USE\nGC content: 48.2%\nThis run used a deprecated model.\n")

with open("/workspace/results/old_runs/run_2024_02_28_output.json", "w") as f:
    json.dump({"status": "deprecated", "model_version": "genos-0.9", "gc_content": 0.482}, f)

# A red-herring .model_loaded in the WRONG location (root)
# This file has wrong content to test if agent checks properly
with open("/workspace/.model_loaded", "w") as f:
    f.write("error")  # Wrong content - should be "loaded"

# Another distractor in scripts dir - empty or wrong
with open("/workspace/scripts/.model_loaded", "w") as f:
    f.write("")  # Empty - also wrong

with open("/workspace/scripts/README_legacy.txt", "w") as f:
    f.write("Legacy script notes - archived 2023-12\n")
    f.write("Do not use genos_v0 functions.\n")

# Data distractor
with open("/workspace/data/raw_sequences/reference_genome_index.txt", "w") as f:
    f.write("Reference index file - not a sequence\nchromosome_count: 23\n")

with open("/workspace/data/processed/batch_results_old.csv", "w") as f:
    f.write("seq_id,length,gc\nseq1,1000,0.52\nseq2,850,0.48\n")

# A partial/broken config.json in root (distractor)
with open("/workspace/config.json.bak", "w") as f:
    json.dump({"model_path": "./models/Genos-1.2B"}, f)  # Wrong model path (missing triple underscore)

print("Workspace generated successfully.")
print(f"Clean sequence length: {len(clean_seq)}")
print("Messy FASTA file created at: /workspace/data/raw_sequences/sample_GRCh38_chr1_ZJL2024.fasta")