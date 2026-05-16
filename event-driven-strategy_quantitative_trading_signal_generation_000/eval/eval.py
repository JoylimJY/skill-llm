import sys
import json
import math
from pathlib import Path

def find_output(workspace: Path):
    """Search for trading_signals.json anywhere in the workspace."""
    candidates = list(workspace.rglob("trading_signals.json"))
    if candidates:
        return candidates[0]
    return None

def safe_float(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default

def check_close(a, b, rel=0.05):
    """Within 5% relative tolerance."""
    if a is None or b is None:
        return False
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) / abs(b) <= rel

def run_eval(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    total_score = 0.0

    # ── locate output file ────────────────────────────────────────────────────
    output_path = find_output(workspace)
    file_found = output_path is not None
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": str(output_path) if file_found else "trading_signals.json not found anywhere in workspace"
    })
    if not file_found:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ── parse JSON ────────────────────────────────────────────────────────────
    try:
        data = json.loads(output_path.read_text(encoding="utf-8"))
    except Exception as e:
        checks.append({"name": "json_parseable", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "json_parseable", "passed": True, "detail": "OK"})

    # ── top-level structure ───────────────────────────────────────────────────
    has_success = isinstance(data.get("success"), bool) and data["success"] is True
    checks.append({
        "name": "top_level_success_true",
        "passed": has_success,
        "detail": f"success={data.get('success')}"
    })

    has_skill = data.get("skill") == "event_driven_strategy_skill"
    checks.append({
        "name": "skill_field_correct",
        "passed": has_skill,
        "detail": f"skill={data.get('skill')}"
    })

    signals = data.get("signals") or data.get("event_signals") or data.get("trading_signals") or []
    has_signals_list = isinstance(signals, list) and len(signals) >= 4
    checks.append({
        "name": "signals_list_has_at_least_4_entries",
        "passed": has_signals_list,
        "detail": f"found {len(signals)} signal entries"
    })

    if not has_signals_list:
        final_passed = False
        print(json.dumps({"passed": final_passed, "score": total_score, "checks": checks}))
        return

    # index by ticker
    sig_map = {}
    for s in signals:
        ticker = s.get("stock") or s.get("ticker") or s.get("stock_code") or ""
        sig_map[ticker] = s

    # ══════════════════════════════════════════════════════════════════════════
    # EVT-001  002371.SZ  earnings (A class)
    # 预期差 = (1.52 - 1.41) / 1.41 = 0.07801...
    # 调整因子 = 0.88 × 0.92 = 0.8096
    # 有效预期差 = 0.07801 × 0.8096 = 0.06316...
    # 催化剂强度 = 3 × 1.8 × 1.1 = 5.94
    # 入场信号强度 = 0.06316 × 5.94 × 0.75 = 0.28161...
    # stop_loss = -2.5%,  risk_reward ≥ 1:2.5 (SKILL: 1:2.5-1:3.5)
    # ══════════════════════════════════════════════════════════════════════════
    s1 = sig_map.get("002371.SZ", {})
    
    # expectation gap check
    expected_gap_001 = (1.52 - 1.41) / 1.41  # ~0.0780
    adj_factor_001 = 0.88 * 0.92              # 0.8096
    eff_gap_001 = expected_gap_001* adj_factor_001  # ~0.0632
    
    raw_gap_val = (
        s1.get("expectation_gap") or 
        s1.get("effective_expectation_gap") or
        s1.get("expected_gap") or
        (s1.get("event_analysis") or {}).get("expectation_gap") or
        None
    )
    # accept as string "+X.X%" or numeric
    def parse_pct(v):
        if v is None: return None
        if isinstance(v, (int, float)): return float(v)
        s = str(v).replace("%","").replace("+","").strip()
        try: return float(s)/100.0
        except: return None

    gap_val_001 = parse_pct(raw_gap_val)
    gap_001_ok = check_close(gap_val_001, eff_gap_001, rel=0.08) if gap_val_001 is not None else False
    checks.append({
        "name": "EVT001_effective_expectation_gap",
        "passed": gap_001_ok,
        "detail": f"expected ~{eff_gap_001:.4f} got {gap_val_001}"
    })

    cat_001 = safe_float(s1.get("catalyst_strength") or (s1.get("event_analysis") or {}).get("catalyst_strength"))
    expected_cat_001 = 3 * 1.8 * 1.1  # 5.94
    cat_001_ok = check_close(cat_001, expected_cat_001, rel=0.08)
    checks.append({
        "name": "EVT001_catalyst_strength",
        "passed": cat_001_ok,
        "detail": f"expected ~{expected_cat_001:.2f} got {cat_001}"
    })

    entry_sig_001 = eff_gap_001 * expected_cat_001 * 0.75  # ~0.2816
    raw_entry_001 = safe_float(
        s1.get("entry_signal_strength") or 
        s1.get("signal_strength") or
        (s1.get("event_analysis") or {}).get("entry_signal_strength")
    )
    entry_001_ok = check_close(raw_entry_001, entry_sig_001, rel=0.08) if raw_entry_001 is not None else False
    checks.append({
        "name": "EVT001_entry_signal_strength",
        "passed": entry_001_ok,
        "detail": f"expected ~{entry_sig_001:.4f} got {raw_entry_001}"
    })

    # event class check
    evt_class_001 = str(s1.get("event_class") or s1.get("event_category_class") or "").upper()
    class_001_ok = "A" in evt_class_001
    checks.append({
        "name": "EVT001_event_class_A",
        "passed": class_001_ok,
        "detail": f"event_class={evt_class_001}"
    })

    # stop_loss = -2.5%
    sl_001 = str(s1.get("stop_loss") or (s1.get("event_analysis") or {}).get("stop_loss") or "")
    sl_001_ok = "-2.5" in sl_001 or "-0.025" in sl_001
    checks.append({
        "name": "EVT001_stop_loss_2p5_pct",
        "passed": sl_001_ok,
        "detail": f"stop_loss field={sl_001}"
    })

    # ══════════════════════════════════════════════════════════════════════════
    # EVT-002  600519.SH  major_acquisition (A class)
    # expectation gap uses deal premium:
    # 预期差 = (18.5 - 12.0) / 12.0 = 0.5417
    # 调整因子 = 0.80 × 0.85 = 0.68
    # 有效预期差 = 0.5417 × 0.68 = 0.3683
    # 催化剂强度 = 3 × 2.0 × 1.05 = 6.30
    # 入场信号强度 = 0.3683 × 6.30 × 0.60 = 1.3922
    # ══════════════════════════════════════════════════════════════════════════
    s2 = sig_map.get("600519.SH", {})

    expected_gap_002 = (18.5 - 12.0) / 12.0
    adj_factor_002 = 0.80 * 0.85
    eff_gap_002 = expected_gap_002 * adj_factor_002
    expected_cat_002 = 3 * 2.0 * 1.05
    entry_sig_002 = eff_gap_002 * expected_cat_002 * 0.60

    raw_gap_002 = parse_pct(
        s2.get("expectation_gap") or 
        s2.get("effective_expectation_gap") or
        (s2.get("event_analysis") or {}).get("expectation_gap")
    )
    gap_002_ok = check_close(raw_gap_002, eff_gap_002, rel=0.08) if raw_gap_002 is not None else False
    checks.append({
        "name": "EVT002_effective_expectation_gap",
        "passed": gap_002_ok,
        "detail": f"expected ~{eff_gap_002:.4f} got {raw_gap_002}"
    })

    cat_002 = safe_float(s2.get("catalyst_strength") or (s2.get("event_analysis") or {}).get("catalyst_strength"))
    cat_002_ok = check_close(cat_002, expected_cat_002, rel=0.08)
    checks.append({
        "name": "EVT002_catalyst_strength",
        "passed": cat_002_ok,
        "detail": f"expected ~{expected_cat_002:.2f} got {cat_002}"
    })

    evt_class_002 = str(s2.get("event_class") or s2.get("event_category_class") or "").upper()
    class_002_ok = "A" in evt_class_002
    checks.append({
        "name": "EVT002_event_class_A",
        "passed": class_002_ok,
        "detail": f"event_class={evt_class_002}"
    })

    # ══════════════════════════════════════════════════════════════════════════
    # EVT-003  000001.SZ  management_change (B class)
    # 预期差 = (0.85 - 0.87) / 0.87 = -0.02299
    # 调整因子 = 0.71 × 0.78 = 0.5538
    # 有效预期差 = -0.02299 × 0.5538 = -0.01274
    # 催化剂强度 = 2 × 1.5 × 0.95 = 2.85
    # 入场信号强度 = -0.01274 × 2.85 × 0.40 = -0.01452  (negative → avoid/short signal)
    # ══════════════════════════════════════════════════════════════════════════
    s3 = sig_map.get("000001.SZ", {})

    expected_gap_003 = (0.85 - 0.87) / 0.87
    adj_factor_003 = 0.71 * 0.78
    eff_gap_003 = expected_gap_003 * adj_factor_003
    expected_cat_003 = 2 * 1.5 * 0.95

    cat_003 = safe_float(s3.get("catalyst_strength") or (s3.get("event_analysis") or {}).get("catalyst_strength"))
    cat_003_ok = check_close(cat_003, expected_cat_003, rel=0.08)
    checks.append({
        "name": "EVT003_catalyst_strength",
        "passed": cat_003_ok,
        "detail": f"expected ~{expected_cat_003:.2f} got {cat_003}"
    })

    evt_class_003 = str(s3.get("event_class") or s3.get("event_category_class") or "").upper()
    class_003_ok = "B" in evt_class_003
    checks.append({
        "name": "EVT003_event_class_B",
        "passed": class_003_ok,
        "detail": f"event_class={evt_class_003}"
    })

    # ══════════════════════════════════════════════════════════════════════════
    # EVT-004  300760.SZ  nmpa_approval (A class) — strongest signal
    # 预期差 = (2.10 - 1.75) / 1.75 = 0.20
    # 调整因子 = 0.93 × 0.88 = 0.8184
    # 有效预期差 = 0.20 × 0.8184 = 0.16368
    # 催化剂强度 = 3 × 1.9 × 1.15 = 6.555
    # 入场信号强度 = 0.16368 × 6.555 × 0.85 = 0.91158
    # ══════════════════════════════════════════════════════════════════════════
    s4 = sig_map.get("300760.SZ", {})

    expected_gap_004 = (2.10 - 1.75) / 1.75
    adj_factor_004 = 0.93 * 0.88
    eff_gap_004 = expected_gap_004 * adj_factor_004
    expected_cat_004 = 3 * 1.9 * 1.15
    entry_sig_004 = eff_gap_004 * expected_cat_004 * 0.85

    raw_gap_004 = parse_pct(
        s4.get("expectation_gap") or 
        s4.get("effective_expectation_gap") or
        (s4.get("event_analysis") or {}).get("expectation_gap")
    )
    gap_004_ok = check_close(raw_gap_004, eff_gap_004, rel=0.08) if raw_gap_004 is not None else False
    checks.append({
        "name": "EVT004_effective_expectation_gap",
        "passed": gap_004_ok,
        "detail": f"expected ~{eff_gap_004:.4f} got {raw_gap_004}"
    })

    cat_004 = safe_float(s4.get("catalyst_strength") or (s4.get("event_analysis") or {}).get("catalyst_strength"))
    cat_004_ok = check_close(cat_004, expected_cat_004, rel=0.08)
    checks.append({
        "name": "EVT004_catalyst_strength",
        "passed": cat_004_ok,
        "detail": f"expected ~{expected_cat_004:.3f} got {cat_004}"
    })

    raw_entry_004 = safe_float(
        s4.get("entry_signal_strength") or 
        s4.get("signal_strength") or
        (s4.get("event_analysis") or {}).get("entry_signal_strength")
    )
    entry_004_ok = check_close(raw_entry_004, entry_sig_004, rel=0.08) if raw_entry_004 is not None else False
    checks.append({
        "name": "EVT004_entry_signal_strength",
        "passed": entry_004_ok,
        "detail": f"expected ~{entry_sig_004:.4f} got {raw_entry_004}"
    })

    evt_class_004 = str(s4.get("event_class") or s4.get("event_category_class") or "").upper()
    class_004_ok = "A" in evt_class_004
    checks.append({
        "name": "EVT004_event_class_A",
        "passed": class_004_ok,
        "detail": f"event_class={evt_class_004}"
    })

    # ══════════════════════════════════════════════════════════════════════════
    # EVT-005  002594.SZ  analyst_conference (C class)
    # signal should be LOW / avoid trading
    # 催化剂强度 = 1 × 1.2 × 0.82 = 0.984
    # ══════════════════════════════════════════════════════════════════════════
    s5 = sig_map.get("002594.SZ", {})

    expected_cat_005 = 1 * 1.2 * 0.82
    cat_005 = safe_float(s5.get("catalyst_strength") or (s5.get("event_analysis") or {}).get("catalyst_strength"))
    cat_005_ok = check_close(cat_005, expected_cat_005, rel=0.08)
    checks.append({
        "name": "EVT005_catalyst_strength",
        "passed": cat_005_ok,
        "detail": f"expected ~{expected_cat_005:.3f} got {cat_005}"
    })

    evt_class_005 = str(s5.get("event_class") or s5.get("event_category_class") or "").upper()
    class_005_ok = "C" in evt_class_005
    checks.append({
        "name": "EVT005_event_class_C",
        "passed": class_005_ok,
        "detail": f"event_class={evt_class_005}"
    })

    # ── risk control: max single event position ≤ 5% mentioned in each signal ─
    positions_ok_count = 0
    for s in signals:
        max_pos = str(s.get("max_position") or s.get("max_position_pct") or 
                      (s.get("event_analysis") or {}).get("max_position") or "")
        if "5" in max_pos or "0.05" in max_pos:
            positions_ok_count += 1
    positions_ok = positions_ok_count >= 3
    checks.append({
        "name": "risk_control_max_position_5pct_present",
        "passed": positions_ok,
        "detail": f"{positions_ok_count}/5 signals mention 5% max position"
    })

    # ── time stop: 3 trading days post-event ─────────────────────────────────
    time_stops_ok = 0
    for s in signals:
        ts = str(s.get("time_stop") or s.get("exit_timing") or 
                 (s.get("event_analysis") or {}).get("exit_timing") or
                 (s.get("event_analysis") or {}).get("time_stop") or "")
        if "3" in ts:
            time_stops_ok += 1
    time_stop_ok = time_stops_ok >= 3
    checks.append({
        "name": "risk_control_time_stop_3_days",
        "passed": time_stop_ok,
        "detail": f"{time_stops_ok}/5 signals mention 3-day time stop"
    })

    # ── entry timing for A-class earnings: 1-3 days before ───────────────────
    entry_timing_001 = str(s1.get("entry_timing") or (s1.get("event_analysis") or {}).get("entry_timing") or "")
    entry_timing_ok = ("1" in entry_timing_001 and "3" in entry_timing_001) or "前" in entry_timing_001
    checks.append({
        "name": "EVT001_entry_timing_1to3_days_before",
        "passed": entry_timing_ok,
        "detail": f"entry_timing={entry_timing_001}"
    })

    # ── risk_reward_ratio within 1:2.5 to 1:3.5 for strong A-class ───────────
    rr_001 = str(s1.get("risk_reward_ratio") or (s1.get("event_analysis") or {}).get("risk_reward_ratio") or "")
    # accept "1:X" where X in [2.5, 3.5]
    import re
    rr_match = re.search(r'1\s*:\s*([\d.]+)', rr_001)
    if rr_match:
        rr_val = float(rr_match.group(1))
        rr_ok = 2.5 <= rr_val <= 3.5
    else:
        rr_ok = False
    checks.append({
        "name": "EVT001_risk_reward_ratio_within_2p5_to_3p5",
        "passed": rr_ok,
        "detail": f"risk_reward_ratio field='{rr_001}'"
    })

    # ── scoring ───────────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)
    overall_passed = score >= 0.70

    print(json.dumps({
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace_dir)