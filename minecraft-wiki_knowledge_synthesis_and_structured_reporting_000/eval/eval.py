import json
import sys
import os
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    total_score = 0.0

    # Find the output file
    target_filename = "endgame_loadout_report.json"
    found_files = list(Path(workspace_dir).rglob(target_filename))

    if not found_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": f"Could not find {target_filename} anywhere in workspace."}]
        }

    report_path = found_files[0]
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {report_path}"})

    try:
        with open(report_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [
                {"name": "file_exists", "passed": True, "detail": str(report_path)},
                {"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"}
            ]
        }

    checks.append({"name": "valid_json", "passed": True, "detail": "File is valid JSON."})

    def find_value(obj, *keys):
        """Navigate nested dict with fallback."""
        for key in keys:
            if isinstance(obj, dict) and key in obj:
                obj = obj[key]
            else:
                return None
        return obj

    def to_str(val):
        return str(val).lower().strip() if val is not None else ""

    # ---- CHECK 1: Diamond Y level ----
    # Must be -58 (or "y=-58", "-58", "negative 58", etc.) for 1.18+/1.21
    diamond_y = None
    try:
        rg = data.get("resource_gathering", data.get("mining", data.get("resources", {})))
        diamonds = rg.get("diamonds", rg.get("diamond", {})) if isinstance(rg, dict) else {}
        diamond_y = diamonds.get("optimal_y_level", diamonds.get("y_level", diamonds.get("best_y", None)))
    except Exception:
        pass

    diamond_correct = False
    if diamond_y is not None:
        s = to_str(diamond_y)
        if "-58" in s or "−58" in s or "minus 58" in s or "negative 58" in s:
            diamond_correct = True

    checks.append({
        "name": "diamond_y_level_correct",
        "passed": diamond_correct,
        "detail": f"Diamond Y level found: '{diamond_y}'. Expected: -58 (peak in 1.18+ / 1.21)."
    })
    if diamond_correct:
        total_score += 0.10

    # ---- CHECK 2: Ancient Debris Y level ----
    # Must be Y=8 (optimal), acceptable: 8 or "8" or "Y=8"
    debris_y = None
    try:
        rg = data.get("resource_gathering", data.get("mining", data.get("resources", {})))
        debris = rg.get("ancient_debris", rg.get("ancient debris", {})) if isinstance(rg, dict) else {}
        debris_y = debris.get("optimal_y_level", debris.get("y_level", debris.get("best_y", None)))
    except Exception:
        pass

    debris_correct = False
    if debris_y is not None:
        s = to_str(debris_y)
        if "8" in s:
            debris_correct = True

    checks.append({
        "name": "ancient_debris_y_level_correct",
        "passed": debris_correct,
        "detail": f"Ancient Debris Y level found: '{debris_y}'. Expected: Y=8 (optimal per SKILL.md)."
    })
    if debris_correct:
        total_score += 0.10

    # ---- CHECK 3: Ancient Debris explosion immunity ----
    debris_immune = None
    try:
        rg = data.get("resource_gathering", data.get("mining", data.get("resources", {})))
        debris = rg.get("ancient_debris", rg.get("ancient debris", {})) if isinstance(rg, dict) else {}
        debris_immune = debris.get("explosion_immune", debris.get("explosion_resistant", debris.get("immune_to_explosions", None)))
    except Exception:
        pass

    immune_correct = False
    if debris_immune is not None:
        s = to_str(debris_immune)
        if s in ("true", "yes", "1") or "immune" in s or "true" in s:
            immune_correct = True

    checks.append({
        "name": "ancient_debris_explosion_immune",
        "passed": immune_correct,
        "detail": f"Ancient debris explosion_immune: '{debris_immune}'. Expected: true."
    })
    if immune_correct:
        total_score += 0.05

    # ---- CHECK 4: Armor material costs (diamond pieces) ----
    # Helmet=5, Chestplate=8, Leggings=7, Boots=4
    expected_costs = {
        "helmet": 5,
        "chestplate": 8,
        "leggings": 7,
        "boots": 4
    }

    cost_section = None
    try:
        cost_section = data.get("full_netherite_armor_material_cost",
                        data.get("armor_material_cost",
                        data.get("material_costs",
                        data.get("crafting_costs", {}))))
    except Exception:
        cost_section = {}

    cost_correct_count = 0
    for piece, expected in expected_costs.items():
        val = None
        try:
            if isinstance(cost_section, dict):
                val = cost_section.get(f"{piece}_diamonds",
                      cost_section.get(piece, {}).get("diamonds", None) if isinstance(cost_section.get(piece), dict) else None)
                if val is None:
                    val = cost_section.get(piece, None)
        except Exception:
            pass
        try:
            if int(str(val)) == expected:
                cost_correct_count += 1
        except Exception:
            pass

    costs_all_correct = (cost_correct_count == 4)
    checks.append({
        "name": "armor_diamond_costs_correct",
        "passed": costs_all_correct,
        "detail": f"Got {cost_correct_count}/4 correct armor diamond costs. Expected: Helmet=5, Chestplate=8, Leggings=7, Boots=4."
    })
    if costs_all_correct:
        total_score += 0.10
    elif cost_correct_count >= 2:
        total_score += 0.05

    # ---- CHECK 5: Total diamonds for full armor = 5+8+7+4 = 24 ----
    total_diamonds = None
    try:
        if isinstance(cost_section, dict):
            total_diamonds = cost_section.get("total_diamonds_for_full_set",
                            cost_section.get("total_diamonds", None))
    except Exception:
        pass

    total_diamonds_correct = False
    try:
        if total_diamonds is not None and int(str(total_diamonds)) == 24:
            total_diamonds_correct = True
    except Exception:
        pass

    checks.append({
        "name": "total_diamonds_for_full_armor_correct",
        "passed": total_diamonds_correct,
        "detail": f"Total diamonds for full set: '{total_diamonds}'. Expected: 24 (5+8+7+4)."
    })
    if total_diamonds_correct:
        total_score += 0.05

    # ---- CHECK 6: Protection family mutual exclusivity ----
    # No armor piece should have MORE THAN ONE of: Protection, Fire Protection, Blast Protection, Projectile Protection
    protection_family = {"protection", "fire protection", "blast protection", "projectile protection"}

    armor_section = data.get("optimal_armor_enchantments",
                   data.get("armor_enchantments",
                   data.get("armor", {})))

    protection_violation = False
    protection_detail = []
    if isinstance(armor_section, dict):
        for piece in ["helmet", "chestplate", "leggings", "boots"]:
            enchants_raw = armor_section.get(piece, [])
            if isinstance(enchants_raw, list):
                enchants_lower = [str(e).lower().strip() for e in enchants_raw]
                found_prot = [e for e in enchants_lower if any(p in e for p in protection_family)]
                if len(found_prot) > 1:
                    protection_violation = True
                    protection_detail.append(f"{piece} has multiple protection enchants: {found_prot}")

    protection_ok = not protection_violation
    checks.append({
        "name": "protection_family_exclusivity",
        "passed": protection_ok,
        "detail": f"No armor piece has multiple mutually exclusive protection enchants. Violations: {protection_detail if protection_detail else 'none'}"
    })
    if protection_ok:
        total_score += 0.15

    # ---- CHECK 7: Frost Walker and Protection incompatibility on boots ----
    # Frost Walker and Depth Strider are mutually exclusive (both are boot enchants that conflict)
    # Check boots don't have both Frost Walker AND Depth Strider
    frost_depth_conflict = False
    try:
        if isinstance(armor_section, dict):
            boots_enchants = [str(e).lower() for e in armor_section.get("boots", [])]
            has_frost = any("frost walker" in e or "frost_walker" in e for e in boots_enchants)
            has_depth = any("depth strider" in e or "depth_strider" in e for e in boots_enchants)
            if has_frost and has_depth:
                frost_depth_conflict = True
    except Exception:
        pass

    checks.append({
        "name": "frost_walker_depth_strider_exclusivity",
        "passed": not frost_depth_conflict,
        "detail": f"Boots should not have both Frost Walker and Depth Strider. Conflict detected: {frost_depth_conflict}"
    })
    if not frost_depth_conflict:
        total_score += 0.05

    # ---- CHECK 8: Sword does NOT have Sharpness + Smite together ----
    # Sharpness ↔ Smite ↔ Bane of Arthropods are mutually exclusive
    sword_section = data.get("optimal_sword_enchantments",
                   data.get("sword_enchantments",
                   data.get("sword", {})))

    sword_enchants = []
    if isinstance(sword_section, dict):
        sword_enchants = [str(e).lower() for e in sword_section.get("sword",
                         sword_section.get("enchantments",
                         sword_section.get("enchants", [])))]
    elif isinstance(sword_section, list):
        sword_enchants = [str(e).lower() for e in sword_section]

    sharpness_smite_family = ["sharpness", "smite", "bane of arthropods"]
    found_dmg_enchants = [e for e in sword_enchants if any(dmg in e for dmg in sharpness_smite_family)]
    sword_dmg_ok = len(found_dmg_enchants) <= 1

    checks.append({
        "name": "sword_damage_enchant_exclusivity",
        "passed": sword_dmg_ok,
        "detail": f"Sword should have at most one of Sharpness/Smite/Bane of Arthropods. Found: {found_dmg_enchants}"
    })
    if sword_dmg_ok:
        total_score += 0.10

    # ---- CHECK 9: Pickaxe does NOT have Fortune + Silk Touch together ----
    pickaxe_section = data.get("optimal_pickaxe_enchantments",
                     data.get("pickaxe_enchantments",
                     data.get("pickaxe", {})))

    pickaxe_enchants = []
    if isinstance(pickaxe_section, dict):
        pickaxe_enchants = [str(e).lower() for e in pickaxe_section.get("pickaxe",
                           pickaxe_section.get("enchantments",
                           pickaxe_section.get("enchants", [])))]
    elif isinstance(pickaxe_section, list):
        pickaxe_enchants = [str(e).lower() for e in pickaxe_section]

    has_fortune = any("fortune" in e for e in pickaxe_enchants)
    has_silk = any("silk touch" in e or "silk_touch" in e for e in pickaxe_enchants)
    pickaxe_conflict_ok = not (has_fortune and has_silk)

    checks.append({
        "name": "pickaxe_fortune_silk_touch_exclusivity",
        "passed": pickaxe_conflict_ok,
        "detail": f"Pickaxe should not have both Fortune and Silk Touch. Fortune={has_fortune}, Silk Touch={has_silk}."
    })
    if pickaxe_conflict_ok:
        total_score += 0.10

    # ---- CHECK 10: Bow does NOT have both Infinity AND Mending ----
    bow_section = data.get("optimal_bow_enchantments",
                 data.get("bow_enchantments",
                 data.get("bow", {})))

    bow_enchants = []
    if isinstance(bow_section, dict):
        bow_enchants = [str(e).lower() for e in bow_section.get("bow",
                       bow_section.get("enchantments",
                       bow_section.get("enchants", [])))]
    elif isinstance(bow_section, list):
        bow_enchants = [str(e).lower() for e in bow_section]

    has_infinity = any("infinity" in e for e in bow_enchants)
    has_mending = any("mending" in e for e in bow_enchants)
    bow_conflict_ok = not (has_infinity and has_mending)

    checks.append({
        "name": "bow_infinity_mending_exclusivity",
        "passed": bow_conflict_ok,
        "detail": f"Bow should not have both Infinity and Mending (they are mutually exclusive). Infinity={has_infinity}, Mending={has_mending}."
    })
    if bow_conflict_ok:
        total_score += 0.10

    # ---- CHECK 11: Mending classified as treasure enchant (NOT obtainable from enchanting table) ----
    treasure_section = data.get("treasure_enchantments",
                      data.get("treasure_only_enchantments",
                      data.get("enchantment_sources", {})))

    mending_is_treasure = False
    try:
        if isinstance(treasure_section, dict):
            mending_val = treasure_section.get("mending", None)
            if mending_val is not None:
                s = to_str(mending_val)
                if "treasure" in s or "fishing" in s or "chest" in s or "trade" in s or "not table" in s or "cannot" in s or "only" in s:
                    mending_is_treasure = True
                # Also accept boolean true if key is something like "is_treasure_only"
                if s in ("true", "yes"):
                    mending_is_treasure = True
    except Exception:
        pass

    # Also check if there's a list of treasure enchants that includes mending
    if not mending_is_treasure:
        try:
            if isinstance(treasure_section, list):
                if any("mending" in str(e).lower() for e in treasure_section):
                    mending_is_treasure = True
        except Exception:
            pass

    checks.append({
        "name": "mending_is_treasure_enchant",
        "passed": mending_is_treasure,
        "detail": f"Mending must be identified as a treasure enchantment (not obtainable from enchanting table). treasure_section mending value: '{treasure_section.get('mending', 'NOT FOUND') if isinstance(treasure_section, dict) else 'N/A'}'."
    })
    if mending_is_treasure:
        total_score += 0.10

    # ---- CHECK 12: Version correctly stated as 1.21 Java Edition ----
    meta = data.get("meta", data.get("metadata", data.get("version_info", {})))
    version_correct = False
    if isinstance(meta, dict):
        version_str = to_str(meta.get("game_version", meta.get("version", meta.get("minecraft_version", ""))))
        if "1.21" in version_str and ("java" in version_str or "java edition" in version_str.lower()):
            version_correct = True
    # Also check top-level
    if not version_correct:
        top_version = to_str(data.get("game_version", data.get("version", "")))
        if "1.21" in top_version and "java" in top_version:
            version_correct = True

    checks.append({
        "name": "version_java_1_21",
        "passed": version_correct,
        "detail": f"Report should specify Java Edition 1.21. Detected version field: '{meta.get('game_version', 'N/A') if isinstance(meta, dict) else 'N/A'}'."
    })
    if version_correct:
        total_score += 0.05

    # ---- Final result ----
    total_score = round(min(total_score, 1.0), 4)
    # Must pass at least 8 of 12 checks to pass overall
    num_passed = sum(1 for c in checks if c["passed"])
    # Core critical checks: protection exclusivity, sword dmg exclusivity, pickaxe fortune/silk, bow infinity/mending
    critical_checks = [
        "protection_family_exclusivity",
        "sword_damage_enchant_exclusivity",
        "pickaxe_fortune_silk_touch_exclusivity",
        "bow_infinity_mending_exclusivity",
        "mending_is_treasure_enchant"
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )

    overall_passed = (num_passed >= 8) and critical_passed and total_score >= 0.65

    return {
        "passed": overall_passed,
        "score": total_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))