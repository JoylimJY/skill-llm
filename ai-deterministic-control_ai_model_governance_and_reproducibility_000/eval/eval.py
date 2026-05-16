#!/usr/bin/env python3
"""Evaluation script for ai-deterministic-control task."""
import sys
import json
import pathlib
import datetime

workspace = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("/workspace")
home = pathlib.Path.home()

checks = []
total_score = 0.0
max_score = 0.0


def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global total_score, max_score
    max_score += weight
    if passed:
        total_score += weight


# ─── CHECK 1: Signal file updated with data_analysis preset ──────────────────
signal_path = home / ".openclaw" / "workspace" / ".detcontrol_signal.json"
try:
    signal_data = json.loads(signal_path.read_text())
    preset_ok = signal_data.get("preset") == "data_analysis"
    temp_ok = abs(signal_data.get("temperature", -1) - 0.15) < 0.001
    top_p_ok = abs(signal_data.get("top_p", -1) - 0.85) < 0.001
    seed_ok = signal_data.get("seed") == 42

    add_check(
        "signal_file_preset",
        preset_ok,
        f"Signal file preset={signal_data.get('preset')!r}, expected='data_analysis'",
        weight=1.5
    )
    add_check(
        "signal_file_temperature",
        temp_ok,
        f"Signal file temperature={signal_data.get('temperature')}, expected=0.15",
        weight=1.5
    )
    add_check(
        "signal_file_top_p",
        top_p_ok,
        f"Signal file top_p={signal_data.get('top_p')}, expected=0.85",
        weight=0.5
    )
    add_check(
        "signal_file_seed",
        seed_ok,
        f"Signal file seed={signal_data.get('seed')}, expected=42",
        weight=0.5
    )
except Exception as e:
    add_check("signal_file_preset", False, f"Could not read signal file: {e}", weight=1.5)
    add_check("signal_file_temperature", False, f"Could not read signal file: {e}", weight=1.5)
    add_check("signal_file_top_p", False, f"Signal file missing/unreadable", weight=0.5)
    add_check("signal_file_seed", False, f"Signal file missing/unreadable", weight=0.5)


# ─── CHECK 2: openclaw.json was updated for glm-5 with injected params ────────
openclaw_path = home / ".openclaw" / "openclaw.json"
try:
    openclaw = json.loads(openclaw_path.read_text())
    glm5 = openclaw.get("models", {}).get("glm-5", {})

    inj_temp = glm5.get("temperature")
    inj_top_p = glm5.get("top_p")
    inj_seed = glm5.get("seed")
    injected_at = glm5.get("injected_at")

    temp_inject_ok = inj_temp is not None and abs(inj_temp - 0.15) < 0.001
    top_p_inject_ok = inj_top_p is not None and abs(inj_top_p - 0.85) < 0.001
    seed_inject_ok = inj_seed == 42
    injected_at_ok = injected_at is not None  # timestamp must be present

    add_check(
        "inject_glm5_temperature",
        temp_inject_ok,
        f"glm-5 temperature in openclaw.json={inj_temp}, expected=0.15",
        weight=1.5
    )
    add_check(
        "inject_glm5_top_p",
        top_p_inject_ok,
        f"glm-5 top_p in openclaw.json={inj_top_p}, expected=0.85",
        weight=0.5
    )
    add_check(
        "inject_glm5_seed",
        seed_inject_ok,
        f"glm-5 seed in openclaw.json={inj_seed}, expected=42",
        weight=0.5
    )
    add_check(
        "inject_glm5_injected_at",
        injected_at_ok,
        f"glm-5 injected_at present: {injected_at}",
        weight=0.5
    )

    # Verify other models were NOT corrupted
    gpt4 = openclaw.get("models", {}).get("gpt-4", {})
    gpt4_intact = gpt4.get("temperature") == 0.5
    add_check(
        "inject_no_corruption",
        gpt4_intact,
        f"gpt-4 temperature unchanged: {gpt4.get('temperature')}",
        weight=0.5
    )

    # Verify backup was created
    backup_dir = home / ".openclaw" / "detcontrol" / "backups"
    bak_files = list(backup_dir.glob("openclaw_*.json.bak")) if backup_dir.exists() else []
    add_check(
        "inject_backup_created",
        len(bak_files) > 0,
        f"Backup files found: {[f.name for f in bak_files]}",
        weight=0.5
    )

except Exception as e:
    for check_name in ["inject_glm5_temperature", "inject_glm5_top_p", "inject_glm5_seed",
                       "inject_glm5_injected_at", "inject_no_corruption", "inject_backup_created"]:
        weight = 1.5 if check_name == "inject_glm5_temperature" else 0.5
        add_check(check_name, False, f"Could not evaluate openclaw.json: {e}", weight=weight)


# ─── CHECK 3: consistency_audit_report.json exists and has correct structure ──
report_candidates = list(workspace.rglob("consistency_audit_report.json"))
if not report_candidates:
    add_check("report_exists", False, "consistency_audit_report.json not found anywhere under /workspace", weight=2.0)
    add_check("report_composite_score", False, "Report missing, cannot check score", weight=1.0)
    add_check("report_status_field", False, "Report missing, cannot check status field", weight=0.5)
    add_check("report_samples_count", False, "Report missing, cannot check samples count", weight=0.5)
    add_check("report_prompt_present", False, "Report missing, cannot check prompt", weight=0.5)
    add_check("report_temperature_matches", False, "Report missing", weight=0.5)
else:
    report_path = report_candidates[0]
    add_check("report_exists", True, f"Found at {report_path}", weight=2.0)

    try:
        report = json.loads(report_path.read_text())

        # Check prompt
        prompt_in_report = report.get("prompt", "")
        prompt_ok = "quarterly risk" in prompt_in_report.lower() or "equity portfolio" in prompt_in_report.lower()
        add_check(
            "report_prompt_present",
            prompt_ok,
            f"Prompt in report: {prompt_in_report!r[:80]}",
            weight=0.5
        )

        # Check samples = 5
        samples_ok = report.get("samples") == 5
        add_check(
            "report_samples_count",
            samples_ok,
            f"Samples count={report.get('samples')}, expected=5",
            weight=0.5
        )

        # Check composite_score is present and is a float
        comp = report.get("composite_score")
        comp_ok = comp is not None and isinstance(comp, (int, float))
        add_check(
            "report_composite_score",
            comp_ok,
            f"composite_score={comp}",
            weight=1.0
        )

        # Check status field is one of OK/WARN/CRITICAL (proprietary thresholds)
        status = report.get("status", "")
        status_ok = status in ("OK", "WARN", "CRITICAL")
        add_check(
            "report_status_field",
            status_ok,
            f"status={status!r}, must be one of OK/WARN/CRITICAL",
            weight=0.5
        )

        # Check that temperature in report matches data_analysis preset (0.15)
        rpt_temp = report.get("temperature")
        temp_match = rpt_temp is not None and abs(rpt_temp - 0.15) < 0.001
        add_check(
            "report_temperature_matches",
            temp_match,
            f"Report temperature={rpt_temp}, expected 0.15 (data_analysis preset)",
            weight=0.5
        )

        # Check composite score formula consistency:
        # composite = 0.4 * char_sim + 0.6 * semantic_sim
        char_s = report.get("char_similarity")
        sem_s = report.get("semantic_similarity")
        if char_s is not None and sem_s is not None and comp is not None:
            expected_comp = round(0.4 * char_s + 0.6 * sem_s, 4)
            formula_ok = abs(expected_comp - comp) < 0.01
            add_check(
                "report_composite_formula",
                formula_ok,
                f"0.4*{char_s}+0.6*{sem_s}={expected_comp}, reported={comp}",
                weight=1.0
            )
        else:
            add_check(
                "report_composite_formula",
                False,
                f"Missing char_similarity={char_s} or semantic_similarity={sem_s} in report",
                weight=1.0
            )

    except Exception as e:
        for name in ["report_prompt_present", "report_samples_count", "report_composite_score",
                     "report_status_field", "report_temperature_matches", "report_composite_formula"]:
            weight = 1.0 if "composite" in name else 0.5
            add_check(name, False, f"Failed to parse report: {e}", weight=weight)


# ─── FINAL SCORING ────────────────────────────────────────────────────────────
passed_all = all(c["passed"] for c in checks)
final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0

output = {
    "passed": passed_all,
    "score": final_score,
    "checks": checks
}
print(json.dumps(output, indent=2))