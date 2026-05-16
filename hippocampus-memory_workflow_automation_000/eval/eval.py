import json
import sys
import math
from pathlib import Path
from datetime import date

def run_eval(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    
    REFERENCE_DATE = date(2025, 2, 15)
    DECAY_FACTOR = 0.99
    CORE_THRESHOLD = 0.7

    # ── Helper ───────────────────────────────────────────────────────────────
    def decay(importance: float, last_accessed_str: str) -> float:
        """Apply decay: importance * 0.99^days_since_lastAccessed"""
        try:
            la = date.fromisoformat(last_accessed_str)
        except Exception:
            la = date.fromisoformat(last_accessed_str[:10])
        days = (REFERENCE_DATE - la).days
        return importance * (DECAY_FACTOR ** days)

    # Expected values (pre-computed):
    # mem_001: importance=0.85, lastAccessed=2025-02-10, days=5  → 0.85*0.99^5
    # mem_002: importance=0.85, lastAccessed=2025-01-15, days=31 → 0.85*0.99^31
    # mem_003: importance=0.75, lastAccessed=2025-02-14, days=1  → 0.75*0.99^1
    # mem_004: importance=0.50, lastAccessed=2025-01-01, days=45 → 0.50*0.99^45
    # mem_005: importance=1.05 → clamp to 1.0, lastAccessed=2025-01-20, days=26 → 1.0*0.99^26
    # mem_006: importance=0.40, lastAccessed=2024-12-01, days=76 → 0.40*0.99^76
    # mem_007: importance=0.70, lastAccessed=2025-02-01, days=14 → 0.70*0.99^14
    # mem_008: importance=0.35, lastAccessed=2025-01-25, days=21 → 0.35*0.99^21

    expected_decayed = {
        "mem_001": decay(0.85, "2025-02-10"),   # ~0.8083
        "mem_002": decay(0.85, "2025-01-15"),   # ~0.6228
        "mem_003": decay(0.75, "2025-02-14"),   # ~0.7425
        "mem_004": decay(0.50, "2025-01-01"),   # ~0.3189
        "mem_005": decay(1.0,  "2025-01-20"),   # ~0.7697  (clamped)
        "mem_006": decay(0.40, "2024-12-01"),   # ~0.1853
        "mem_007": decay(0.70, "2025-02-01"),   # ~0.6081
        "mem_008": decay(0.35, "2025-01-25"),   # ~0.2828
    }
    core_ids = {k for k, v in expected_decayed.items() if v >= CORE_THRESHOLD}
    # core_ids should be: mem_001, mem_003, mem_005

    # ── CHECK 1: index.json exists and is valid JSON ─────────────────────────
    index_path = workspace / "memory" / "index.json"
    try:
        index_data = json.loads(index_path.read_text())
        checks.append({"name": "index.json_exists_and_valid", "passed": True,
                        "detail": "index.json found and is valid JSON"})
    except Exception as e:
        checks.append({"name": "index.json_exists_and_valid", "passed": False,
                        "detail": f"index.json missing or invalid: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── CHECK 2: decayLastRun updated to 2025-02-15 ─────────────────────────
    decay_last = index_data.get("decayLastRun", "")
    decay_run_ok = (decay_last == "2025-02-15")
    checks.append({"name": "decayLastRun_updated",
                   "passed": decay_run_ok,
                   "detail": f"decayLastRun='{decay_last}', expected '2025-02-15'"})

    # ── CHECK 3: mem_005 importance clamped before decay ────────────────────
    memories_by_id = {}
    try:
        for m in index_data.get("memories", []):
            memories_by_id[m["id"]] = m
    except Exception as e:
        checks.append({"name": "memories_parseable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    mem005 = memories_by_id.get("mem_005", {})
    mem005_imp = mem005.get("importance", 9999)
    mem005_clamped_ok = mem005_imp <= 1.0
    checks.append({
        "name": "mem_005_importance_clamped_to_1.0",
        "passed": mem005_clamped_ok,
        "detail": f"mem_005 importance={mem005_imp:.6f}, must be ≤1.0 after clamping pre-decay"
    })

    # ── CHECK 4: All 8 memories still present ───────────────────────────────
    all_ids = set(memories_by_id.keys())
    expected_ids = {"mem_001","mem_002","mem_003","mem_004","mem_005","mem_006","mem_007","mem_008"}
    all_present = expected_ids.issubset(all_ids)
    checks.append({"name": "all_8_memories_present",
                   "passed": all_present,
                   "detail": f"Found IDs: {sorted(all_ids)}"})

    # ── CHECK 5: Decay applied correctly to each memory (tolerance ±0.005) ──
    TOLERANCE = 0.005
    decay_correct_count = 0
    decay_details = []
    for mid, exp_val in expected_decayed.items():
        mem = memories_by_id.get(mid, {})
        actual_imp = mem.get("importance", -1)
        ok = abs(actual_imp - exp_val) <= TOLERANCE
        if ok:
            decay_correct_count += 1
        decay_details.append(
            f"{mid}: actual={actual_imp:.5f}, expected={exp_val:.5f}, ok={ok}"
        )

    all_decay_ok = (decay_correct_count == 8)
    checks.append({
        "name": "decay_applied_correctly_all_memories",
        "passed": all_decay_ok,
        "detail": f"{decay_correct_count}/8 correct. Details: {'; '.join(decay_details)}"
    })

    # ── CHECK 6: mem_007 has required fields filled in ───────────────────────
    mem007 = memories_by_id.get("mem_007", {})
    mem007_has_times = "timesReinforced" in mem007
    mem007_has_keywords = "keywords" in mem007 and isinstance(mem007.get("keywords"), list)
    mem007_schema_ok = mem007_has_times and mem007_has_keywords
    checks.append({
        "name": "mem_007_missing_fields_repaired",
        "passed": mem007_schema_ok,
        "detail": f"timesReinforced present={mem007_has_times}, keywords present={mem007_has_keywords}"
    })

    # ── CHECK 7: core-memories.json exists ──────────────────────────────────
    core_candidates = list(workspace.rglob("core-memories.json"))
    if not core_candidates:
        checks.append({"name": "core-memories.json_exists", "passed": False,
                        "detail": "core-memories.json not found anywhere in workspace"})
        score = sum(1 for c in checks if c["passed"]) / len(checks)
        return {"passed": False, "score": round(score, 3), "checks": checks}
    
    core_path = core_candidates[0]
    try:
        core_data = json.loads(core_path.read_text())
        checks.append({"name": "core-memories.json_exists", "passed": True,
                        "detail": f"Found at {core_path}"})
    except Exception as e:
        checks.append({"name": "core-memories.json_exists", "passed": False,
                        "detail": f"Found but invalid JSON: {e}"})
        score = sum(1 for c in checks if c["passed"]) / len(checks)
        return {"passed": False, "score": round(score, 3), "checks": checks}

    # ── CHECK 8: core-memories.json contains exactly the right memories ──────
    # Core = importance after decay >= 0.7
    # Expected: mem_001 (~0.808), mem_003 (~0.743), mem_005 (~0.770)
    try:
        if isinstance(core_data, list):
            core_ids_found = {m.get("id") for m in core_data if isinstance(m, dict)}
        elif isinstance(core_data, dict):
            # could be wrapped in {"memories": [...]}
            mems = core_data.get("memories", core_data.get("core", []))
            if isinstance(mems, list):
                core_ids_found = {m.get("id") for m in mems if isinstance(m, dict)}
            else:
                core_ids_found = set()
        else:
            core_ids_found = set()
    except Exception as e:
        core_ids_found = set()

    # Must contain exactly mem_001, mem_003, mem_005
    correct_cores_present = core_ids.issubset(core_ids_found)
    no_false_positives = len(core_ids_found - core_ids) == 0
    core_exact = correct_cores_present and no_false_positives
    checks.append({
        "name": "core-memories.json_correct_entries",
        "passed": core_exact,
        "detail": (
            f"Found IDs: {sorted(core_ids_found)}, "
            f"Expected exactly: {sorted(core_ids)} (importance ≥ {CORE_THRESHOLD} after decay). "
            f"Missing: {sorted(core_ids - core_ids_found)}, "
            f"Unexpected: {sorted(core_ids_found - core_ids)}"
        )
    })

    # ── CHECK 9: core-memories.json importance values reflect decayed scores ─
    core_importance_ok = True
    core_imp_details = []
    try:
        if isinstance(core_data, list):
            core_list = core_data
        elif isinstance(core_data, dict):
            core_list = core_data.get("memories", core_data.get("core", []))
        else:
            core_list = []
        
        for m in core_list:
            mid = m.get("id")
            if mid in expected_decayed:
                actual = m.get("importance", -1)
                exp = expected_decayed[mid]
                ok = abs(actual - exp) <= TOLERANCE
                if not ok:
                    core_importance_ok = False
                core_imp_details.append(f"{mid}: actual={actual:.5f}, expected={exp:.5f}, ok={ok}")
    except Exception as e:
        core_importance_ok = False
        core_imp_details.append(f"Error: {e}")

    checks.append({
        "name": "core-memories.json_decayed_importances_correct",
        "passed": core_importance_ok,
        "detail": "; ".join(core_imp_details) if core_imp_details else "no entries checked"
    })

    # ── Final score ──────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)
    
    # Must pass all critical checks to overall pass
    critical = [
        "index.json_exists_and_valid",
        "decayLastRun_updated",
        "mem_005_importance_clamped_to_1.0",
        "decay_applied_correctly_all_memories",
        "core-memories.json_correct_entries",
        "core-memories.json_decayed_importances_correct",
    ]
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == k), False)
        for k in critical
    )

    return {
        "passed": critical_passed and score >= 0.85,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(ws)
    print(json.dumps(result, indent=2))