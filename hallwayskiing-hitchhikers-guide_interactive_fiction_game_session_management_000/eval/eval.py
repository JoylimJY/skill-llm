import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0
    weights = {}

    def check(name: str, weight: float, passed: bool, detail: str):
        checks.append({"name": name, "passed": passed, "detail": detail})
        weights[name] = weight
        return passed

    # ── Load save file ────────────────────────────────────────────────────────
    save_path = ws / "assets" / "hitchhikers_save.json"
    try:
        state = json.loads(save_path.read_text())
    except Exception as e:
        checks.append({"name": "save_file_readable", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ── Check 1: Location set to Vogon Constructor Ship - Hold ────────────────
    loc = state.get("location", "")
    c1 = check(
        "location_vogon_ship",
        weight=15,
        passed="Vogon Constructor Ship" in loc and "Hold" in loc,
        detail=f"location='{loc}'. Expected to contain 'Vogon Constructor Ship' and 'Hold'."
    )

    # ── Check 2: earth_demolished flag is True ────────────────────────────────
    flags = state.get("flags", {})
    c2 = check(
        "flag_earth_demolished",
        weight=8,
        passed=flags.get("earth_demolished") is True,
        detail=f"flags.earth_demolished={flags.get('earth_demolished')}. Expected True."
    )

    # ── Check 3: ford_found flag is True ─────────────────────────────────────
    c3 = check(
        "flag_ford_found",
        weight=8,
        passed=flags.get("ford_found") is True,
        detail=f"flags.ford_found={flags.get('ford_found')}. Expected True."
    )

    # ── Check 4: Towel in inventory ───────────────────────────────────────────
    inventory = state.get("inventory", [])
    towel_in_inv = any("Towel" in item or "towel" in item.lower() for item in inventory)
    c4 = check(
        "towel_in_inventory",
        weight=10,
        passed=towel_in_inv,
        detail=f"inventory={inventory}. Expected 'Towel' to be present."
    )

    # ── Check 5: has_towel flag is True (Towel Rule from mechanics.md) ────────
    c5 = check(
        "flag_has_towel",
        weight=10,
        passed=flags.get("has_towel") is True,
        detail=f"flags.has_towel={flags.get('has_towel')}. Expected True per Towel Rule in mechanics.md."
    )

    # ── Check 6: Jynnan Tonnyx in inventory ───────────────────────────────────
    jynnan_in_inv = any("Jynnan" in item for item in inventory)
    c6 = check(
        "jynnan_tonnyx_in_inventory",
        weight=10,
        passed=jynnan_in_inv,
        detail=f"inventory={inventory}. Expected 'Jynnan Tonnyx' to be present."
    )

    # ── Check 7: improbability >= 42 ─────────────────────────────────────────
    improbability = state.get("improbability", 0)
    c7 = check(
        "improbability_at_least_42",
        weight=12,
        passed=improbability >= 42,
        detail=f"improbability={improbability}. Expected >= 42 per mechanics.md rescue sequence."
    )

    # ── Check 8: panic stat set (5 or 7 per dice rule) ───────────────────────
    stats = state.get("stats", {})
    panic = stats.get("panic", -1)
    c8 = check(
        "panic_stat_set_correctly",
        weight=8,
        passed=panic in (5, 7),
        detail=f"stats.panic={panic}. Expected 5 or 7 per dice roll outcome in mechanics.md."
    )

    # ── Check 9: history has at least 2 entries (original + rescue entry) ─────
    history = state.get("history", [])
    # The rescue entry should mention being rescued / Ford / demolition / Vogon
    rescue_keywords = ["rescU", "rescued", "demolit", "Vogon", "Ford", "ship", "Earth"]
    rescue_entry_found = any(
        any(kw.lower() in entry.lower() for kw in rescue_keywords)
        for entry in history[1:]  # skip original
    ) if len(history) > 1 else False
    c9 = check(
        "history_rescue_entry_present",
        weight=7,
        passed=rescue_entry_found and len(history) >= 2,
        detail=f"history has {len(history)} entries. Rescue-related entry found: {rescue_entry_found}. Entries: {history}"
    )

    # ── Check 10: GUIDE.md has Vogon entry ───────────────────────────────────
    guide_path = ws / "assets" / "GUIDE.md"
    try:
        guide_text = guide_path.read_text()
        vogon_entry = bool(re.search(r"##\s+Entry:\s+Vogon", guide_text, re.IGNORECASE))
        c10 = check(
            "guide_entry_vogon_ship",
            weight=6,
            passed=vogon_entry,
            detail=f"assets/GUIDE.md has Vogon entry: {vogon_entry}. (Snippet: {guide_text[:300]}...)"
        )
    except Exception as e:
        c10 = check("guide_entry_vogon_ship", weight=6, passed=False, detail=str(e))

    # ── Check 11: GUIDE.md has Jynnan Tonnyx entry ───────────────────────────
    try:
        guide_text = guide_path.read_text()
        jynnan_entry = bool(re.search(r"##\s+Entry:\s+Jynnan", guide_text, re.IGNORECASE))
        c11 = check(
            "guide_entry_jynnan_tonnyx",
            weight=6,
            passed=jynnan_entry,
            detail=f"assets/GUIDE.md has Jynnan Tonnyx entry: {jynnan_entry}."
        )
    except Exception as e:
        c11 = check("guide_entry_jynnan_tonnyx", weight=6, passed=False, detail=str(e))

    # ── Scoring ───────────────────────────────────────────────────────────────
    total_weight = sum(weights.values())
    earned = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    score = round(earned / total_weight, 4)

    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "args", "passed": False, "detail": "No workspace path provided."}
        ]}))
        sys.exit(1)
    evaluate(sys.argv[1])