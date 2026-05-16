import json
import sys
import subprocess
from pathlib import Path

workspace = Path(sys.argv[1])
brain_dir = Path.home() / ".adaptive-brain"

checks = []

def check(name, condition, detail):
    checks.append({"name": name, "passed": bool(condition), "detail": detail})
    return bool(condition)

# ── 1. Brain was initialized ───────────────────────────────────────────────
try:
    brain_file = brain_dir / "brain.json"
    brain = json.loads(brain_file.read_text())
    check(
        "brain_initialized",
        brain.get("version") == 1,
        f"brain.json exists with version={brain.get('version')}"
    )
except Exception as e:
    check("brain_initialized", False, f"Could not read brain.json: {e}")

# ── 2. Errors were logged (at least 3 pip/externally-managed errors) ──────
try:
    learnings_file = brain_dir / "learnings.json"
    learnings_data = json.loads(learnings_file.read_text())
    learnings = learnings_data.get("learnings", [])
    
    error_entries = [l for l in learnings if l.get("type") == "error"]
    pip_errors = [
        l for l in error_entries
        if "externally-managed" in l.get("error", "") or 
           "externally-managed" in str(l.get("keywords", []))
    ]
    
    enough_errors = len(pip_errors) >= 3
    check(
        "minimum_3_pip_errors_logged",
        enough_errors,
        f"Found {len(pip_errors)} pip/externally-managed error entries (need ≥3). "
        f"Total error entries: {len(error_entries)}"
    )
except Exception as e:
    check("minimum_3_pip_errors_logged", False, f"Could not read learnings.json: {e}")

# ── 3. Pattern was detected (3+ occurrences triggers clustering) ───────────
try:
    patterns_file = brain_dir / "patterns.json"
    patterns_data = json.loads(patterns_file.read_text())
    patterns = patterns_data.get("patterns", [])
    
    pip_patterns = [
        p for p in patterns
        if any(kw in p.get("keywords", []) for kw in ["pip", "externally-managed", "venv"])
    ]
    
    has_pattern = len(pip_patterns) > 0
    pattern_count_ok = any(p.get("count", 0) >= 3 for p in pip_patterns) if pip_patterns else False
    
    check(
        "pip_pattern_detected",
        has_pattern,
        f"Found {len(pip_patterns)} pip-related pattern(s). Patterns: {[p.get('id') for p in pip_patterns]}"
    )
    check(
        "pattern_count_3_or_more",
        pattern_count_ok,
        f"Pattern count ≥3: {[p.get('count') for p in pip_patterns]}"
    )
except Exception as e:
    check("pip_pattern_detected", False, f"Could not read patterns.json: {e}")
    check("pattern_count_3_or_more", False, f"Error: {e}")

# ── 4. Adapt was run (evolution history has at least one entry) ────────────
try:
    evolution_file = brain_dir / "evolution.json"
    evolution_data = json.loads(evolution_file.read_text())
    history = evolution_data.get("history", [])
    
    adapt_ran = len(history) >= 1
    check(
        "adapt_cycle_ran",
        adapt_ran,
        f"Evolution history has {len(history)} entries"
    )
    
    # Check that confidence was boosted during adapt
    learnings_data = json.loads((brain_dir / "learnings.json").read_text())
    learnings = learnings_data.get("learnings", [])
    boosted = [l for l in learnings if l.get("confidence", 0.5) > 0.5]
    check(
        "confidence_boosted_after_adapt",
        len(boosted) >= 1,
        f"{len(boosted)} learnings have confidence > 0.5 (initial value)"
    )
except Exception as e:
    check("adapt_cycle_ran", False, f"Could not read evolution.json: {e}")
    check("confidence_boosted_after_adapt", False, f"Error: {e}")

# ── 5. DNA encodes always_use_venv gene ───────────────────────────────────
try:
    brain = json.loads((brain_dir / "brain.json").read_text())
    dna = brain.get("dna", {})
    
    has_venv_gene = dna.get("always_use_venv") == True
    check(
        "dna_always_use_venv_gene",
        has_venv_gene,
        f"DNA genes present: {list(dna.keys())}. 'always_use_venv' = {dna.get('always_use_venv')}"
    )
    
    mutations = brain.get("mutations", [])
    venv_mutations = [m for m in mutations if m.get("gene") == "always_use_venv"]
    check(
        "dna_mutation_recorded",
        len(venv_mutations) >= 1,
        f"Found {len(venv_mutations)} 'always_use_venv' mutations in history"
    )
except Exception as e:
    check("dna_always_use_venv_gene", False, f"Error: {e}")
    check("dna_mutation_recorded", False, f"Error: {e}")

# ── 6. Evolve was run and patches were written to TOOLS.md ────────────────
try:
    evolution_file = brain_dir / "evolution.json"
    evolution_data = json.loads(evolution_file.read_text())
    history = evolution_data.get("history", [])
    
    evolve_steps = [h for h in history if h.get("type") == "evolve"]
    check(
        "evolve_cycle_ran",
        len(evolve_steps) >= 1,
        f"Found {len(evolve_steps)} evolve-type steps in evolution history"
    )
    
    tools_md = workspace / "TOOLS.md"
    if tools_md.exists():
        content = tools_md.read_text()
        has_evolved_marker = "<!-- evolved:" in content or "<!-- brain:" in content
        has_venv_rule = "venv" in content.lower() or "externally" in content.lower()
        check(
            "tools_md_has_brain_rule",
            has_evolved_marker or has_venv_rule,
            f"TOOLS.md has brain rule: marker={has_evolved_marker}, venv_rule={has_venv_rule}. "
            f"Content length: {len(content)} chars"
        )
    else:
        check("tools_md_has_brain_rule", False, "TOOLS.md does not exist")
except Exception as e:
    check("evolve_cycle_ran", False, f"Error: {e}")
    check("tools_md_has_brain_rule", False, f"Error: {e}")

# ── 7. Prediction was run for a pip/package install task ──────────────────
try:
    predictions_file = brain_dir / "predictions.json"
    predictions_data = json.loads(predictions_file.read_text())
    predictions = predictions_data.get("predictions", [])
    
    has_predictions = len(predictions) >= 1
    
    # Check for a prediction related to package install or production
    relevant_preds = [
        p for p in predictions
        if any(kw in p.get("task", "").lower() 
               for kw in ["install", "pip", "package", "production", "deploy"])
    ]
    
    check(
        "prediction_was_run",
        has_predictions,
        f"Found {len(predictions)} prediction(s) total"
    )
    check(
        "relevant_prediction_for_install_task",
        len(relevant_preds) >= 1,
        f"Found {len(relevant_preds)} prediction(s) for install/production tasks. "
        f"Tasks: {[p.get('task', '')[:50] for p in predictions]}"
    )
    
    # Check that risk score is non-zero (patterns were matched)
    if relevant_preds:
        best = max(relevant_preds, key=lambda p: p.get("risk_score", 0))
        check(
            "prediction_risk_score_nonzero",
            best.get("risk_score", 0) > 0,
            f"Best risk score for relevant prediction: {best.get('risk_score', 0):.3f}"
        )
    else:
        check("prediction_risk_score_nonzero", False, "No relevant predictions found")
except Exception as e:
    check("prediction_was_run", False, f"Could not read predictions.json: {e}")
    check("relevant_prediction_for_install_task", False, f"Error: {e}")
    check("prediction_risk_score_nonzero", False, f"Error: {e}")

# ── 8. Metrics were tracked ───────────────────────────────────────────────
try:
    metrics_file = brain_dir / "metrics.json"
    metrics_data = json.loads(metrics_file.read_text())
    snapshots = metrics_data.get("snapshots", [])
    
    check(
        "metrics_snapshots_recorded",
        len(snapshots) >= 1,
        f"Found {len(snapshots)} metrics snapshot(s)"
    )
    
    if snapshots:
        last = snapshots[-1]
        check(
            "metrics_track_errors_and_learnings",
            last.get("total_errors", 0) >= 3 and last.get("total_learnings", 0) >= 3,
            f"Last snapshot: errors={last.get('total_errors')}, "
            f"learnings={last.get('total_learnings')}, "
            f"patterns={last.get('patterns_detected')}"
        )
except Exception as e:
    check("metrics_snapshots_recorded", False, f"Could not read metrics.json: {e}")
    check("metrics_track_errors_and_learnings", False, f"Error: {e}")

# ── Final scoring ──────────────────────────────────────────────────────────
passed_checks = sum(1 for c in checks if c["passed"])
total_checks = len(checks)
score = round(passed_checks / total_checks, 3)
all_passed = passed_checks == total_checks

print(json.dumps({
    "passed": all_passed,
    "score": score,
    "checks": checks
}, indent=2))