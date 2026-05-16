import sys
import json
import os
import re
import hashlib
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

checks = []
total_score = 0.0
max_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global total_score, max_score
    max_score += weight
    if passed:
        total_score += weight

# ─── Expected clean sequence (same logic as gen_inputs_script) ────────────────
CLEAN_SEQ = (
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

# ─── CHECK 1: Model state file exists in correct location ────────────────────
# The SKILL.md says state_file is ./scripts/.model_loaded but startup writes to ./.model_loaded
# The agent must write "loaded" to EITHER location that satisfies the skill's check.
# We accept both: ./scripts/.model_loaded OR ./.model_loaded (root) - but content must be "loaded"
state_file_root = Path(workspace) / ".model_loaded"
state_file_scripts = Path(workspace) / "scripts" / ".model_loaded"

root_ok = False
scripts_ok = False

try:
    if state_file_root.exists():
        content = state_file_root.read_text().strip()
        root_ok = (content == "loaded")
except Exception as e:
    root_ok = False

try:
    if state_file_scripts.exists():
        content = state_file_scripts.read_text().strip()
        scripts_ok = (content == "loaded")
except Exception as e:
    scripts_ok = False

model_state_ok = root_ok or scripts_ok
add_check(
    "model_state_file_written",
    model_state_ok,
    f"./model_loaded content='loaded': {root_ok}, ./scripts/.model_loaded content='loaded': {scripts_ok}. "
    f"At least one must have content 'loaded'.",
    weight=1.0
)

# ─── CHECK 2: Output report file exists ──────────────────────────────────────
report_files = list(Path(workspace).rglob("dna_analysis_report.json"))
report_file = None
if report_files:
    # Prefer one not in old_runs
    for f in report_files:
        if "old_runs" not in str(f):
            report_file = f
            break
    if report_file is None:
        report_file = report_files[0]

add_check(
    "output_report_exists",
    report_file is not None,
    f"Found dna_analysis_report.json at: {report_file}" if report_file else "dna_analysis_report.json not found anywhere in workspace.",
    weight=1.0
)

# ─── Parse the report ─────────────────────────────────────────────────────────
report_data = None
if report_file is not None:
    try:
        with open(report_file, "r") as f:
            report_data = json.load(f)
        add_check("report_valid_json", True, f"Report parsed successfully from {report_file}", weight=0.5)
    except Exception as e:
        add_check("report_valid_json", False, f"Failed to parse JSON: {e}", weight=0.5)

# ─── CHECK 3: analyze_dna_sequence results present and correct ────────────────
if report_data is not None:
    try:
        # Find the analysis section - could be nested or at top level
        analysis = None
        if "analyze_dna_sequence" in report_data:
            analysis = report_data["analyze_dna_sequence"]
        elif "analysis" in report_data:
            analysis = report_data["analysis"]
        elif "sequence_analysis" in report_data:
            analysis = report_data["sequence_analysis"]
        # Also try top-level keys
        elif "length" in report_data and "GC_content" in report_data:
            analysis = report_data
        
        if analysis is None:
            add_check("analysis_section_present", False, 
                      "Could not find analyze_dna_sequence results in report (tried keys: analyze_dna_sequence, analysis, sequence_analysis, top-level)",
                      weight=1.5)
        else:
            add_check("analysis_section_present", True, "Found analysis section in report.", weight=0.5)
            
            # Verify sequence was correctly cleaned: only ACGTN uppercase
            # Check the sequence hash if present
            expected_hash = hashlib.md5(CLEAN_SEQ.encode()).hexdigest()
            
            # Check length
            expected_len = len(CLEAN_SEQ)
            reported_len = analysis.get("length", None)
            length_ok = (reported_len == expected_len)
            add_check(
                "correct_sequence_length",
                length_ok,
                f"Expected length {expected_len}, got {reported_len}. This verifies proper stripping of FASTA headers, line numbers, spaces, and lowercase conversion.",
                weight=2.0
            )
            
            # Check GC content
            g = CLEAN_SEQ.count("G")
            c = CLEAN_SEQ.count("C")
            expected_gc = round((g + c) / len(CLEAN_SEQ) * 100, 4)
            reported_gc = analysis.get("GC_content", None)
            gc_ok = (reported_gc is not None and abs(float(reported_gc) - expected_gc) < 0.01)
            add_check(
                "correct_gc_content",
                gc_ok,
                f"Expected GC_content={expected_gc}, got {reported_gc}.",
                weight=1.5
            )
            
            # Check sequence hash (proves exact correct input was used)
            reported_hash = analysis.get("sequence_hash", None)
            hash_ok = (reported_hash == expected_hash)
            add_check(
                "correct_sequence_hash",
                hash_ok,
                f"Expected md5={expected_hash}, got {reported_hash}. Hash mismatch means sequence was not cleaned correctly.",
                weight=2.0
            )
    except Exception as e:
        add_check("analysis_section_present", False, f"Exception parsing analysis: {e}", weight=1.5)

# ─── CHECK 4: predict_next_base results present ───────────────────────────────
if report_data is not None:
    try:
        prediction = None
        if "predict_next_base" in report_data:
            prediction = report_data["predict_next_base"]
        elif "prediction" in report_data:
            prediction = report_data["prediction"]
        elif "next_base_prediction" in report_data:
            prediction = report_data["next_base_prediction"]
        
        pred_ok = (
            prediction is not None and
            isinstance(prediction, dict) and
            "predictions" in prediction and
            isinstance(prediction["predictions"], list) and
            len(prediction["predictions"]) > 0
        )
        add_check(
            "predict_next_base_present",
            pred_ok,
            f"predict_next_base results found and valid: {pred_ok}. "
            f"Section: {prediction is not None}",
            weight=1.5
        )
        
        if pred_ok:
            # Verify predictions contain base and probability keys
            first_pred = prediction["predictions"][0]
            has_base = "base" in first_pred
            has_prob = "probability" in first_pred
            add_check(
                "prediction_structure_valid",
                has_base and has_prob,
                f"First prediction has 'base': {has_base}, 'probability': {has_prob}",
                weight=0.5
            )
    except Exception as e:
        add_check("predict_next_base_present", False, f"Exception: {e}", weight=1.5)

# ─── CHECK 5: extract_sequence_features results present ──────────────────────
if report_data is not None:
    try:
        features = None
        if "extract_sequence_features" in report_data:
            features = report_data["extract_sequence_features"]
        elif "features" in report_data:
            features = report_data["features"]
        elif "sequence_features" in report_data:
            features = report_data["sequence_features"]
        
        feat_ok = (
            features is not None and
            isinstance(features, dict) and
            "complexity_score" in features and
            "cpg_count" in features and
            "dinucleotide_frequencies" in features
        )
        add_check(
            "extract_features_present",
            feat_ok,
            f"extract_sequence_features results found with expected keys: {feat_ok}. "
            f"Keys present: {list(features.keys()) if features else 'N/A'}",
            weight=1.5
        )
        
        if feat_ok:
            # Verify CpG count is correct
            expected_cpg = CLEAN_SEQ.count("CG")
            reported_cpg = features.get("cpg_count", None)
            cpg_ok = (reported_cpg == expected_cpg)
            add_check(
                "correct_cpg_count",
                cpg_ok,
                f"Expected CpG count={expected_cpg}, got {reported_cpg}.",
                weight=1.0
            )
    except Exception as e:
        add_check("extract_features_present", False, f"Exception: {e}", weight=1.5)

# ─── CHECK 6: All three functions called (completeness) ──────────────────────
if report_data is not None:
    all_three = False
    try:
        has_analysis = any(k in report_data for k in ["analyze_dna_sequence", "analysis", "sequence_analysis", "length"])
        has_prediction = any(k in report_data for k in ["predict_next_base", "prediction", "next_base_prediction"])
        has_features = any(k in report_data for k in ["extract_sequence_features", "features", "sequence_features"])
        all_three = has_analysis and has_prediction and has_features
        add_check(
            "all_three_functions_called",
            all_three,
            f"analyze_dna_sequence: {has_analysis}, predict_next_base: {has_prediction}, extract_sequence_features: {has_features}",
            weight=2.0
        )
    except Exception as e:
        add_check("all_three_functions_called", False, f"Exception: {e}", weight=2.0)

# ─── Final score ──────────────────────────────────────────────────────────────
final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": all_passed,
    "score": final_score,
    "checks": checks
}, indent=2))