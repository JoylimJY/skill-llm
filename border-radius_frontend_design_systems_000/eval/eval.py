import sys
import json
import re
from pathlib import Path

def find_output_file(workspace):
    matches = list(Path(workspace).rglob("border_radius_reference.json"))
    return matches[0] if matches else None

def run_checks(workspace):
    checks = []
    score_parts = []

    filepath = find_output_file(workspace)
    if not filepath:
        checks.append({"name": "output_file_exists", "passed": False, "detail": "border_radius_reference.json not found anywhere in workspace."})
        return checks, 0.0

    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found at {filepath}"})

    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"Failed to parse JSON: {e}"})
        return checks, 0.1

    checks.append({"name": "valid_json", "passed": True, "detail": "File is valid JSON."})

    # Helper: find component data case-insensitively
    def get_component(name_lower):
        for k, v in data.items():
            if k.lower().replace(" ", "").replace("_", "") == name_lower.lower().replace(" ", "").replace("_", ""):
                return v
        return None

    # ---- CHECK 1: PillBadge — Full pill → 9999px all, rounded-full ----
    c1 = get_component("PillBadge")
    css_ok = False
    tw_ok = False
    detail = "PillBadge component not found."
    if c1 is not None:
        css_val = str(c1.get("css", "")).strip()
        tw_val = str(c1.get("tailwind", "")).strip()
        # Accept border-radius: 9999px; (all equal, uniform)
        css_ok = bool(re.search(r"border-radius:\s*9999px;", css_val))
        tw_ok = tw_val == "rounded-full"
        detail = f"css='{css_val}', tailwind='{tw_val}'"
    checks.append({"name": "PillBadge_css", "passed": css_ok, "detail": detail})
    checks.append({"name": "PillBadge_tailwind_rounded_full", "passed": tw_ok, "detail": detail})
    score_parts.extend([css_ok, tw_ok])

    # ---- CHECK 2: BlobCard — Blob preset → 30px 70px 70px 30px ----
    c2 = get_component("BlobCard")
    css_ok = False
    tw_ok = False
    detail = "BlobCard component not found."
    if c2 is not None:
        css_val = str(c2.get("css", "")).strip()
        tw_val = str(c2.get("tailwind", "")).strip()
        css_ok = bool(re.search(r"border-radius:\s*30px\s+70px\s+70px\s+30px;", css_val))
        tw_ok = tw_val == "rounded-[30px_70px_70px_30px]"
        detail = f"css='{css_val}', tailwind='{tw_val}'"
    checks.append({"name": "BlobCard_css", "passed": css_ok, "detail": detail})
    checks.append({"name": "BlobCard_tailwind_underscores", "passed": tw_ok, "detail": detail})
    score_parts.extend([css_ok, tw_ok])

    # ---- CHECK 3: LeafIcon — Leaf preset → 0px 50px 0px 50px ----
    c3 = get_component("LeafIcon")
    css_ok = False
    tw_ok = False
    detail = "LeafIcon component not found."
    if c3 is not None:
        css_val = str(c3.get("css", "")).strip()
        tw_val = str(c3.get("tailwind", "")).strip()
        css_ok = bool(re.search(r"border-radius:\s*0px\s+50px\s+0px\s+50px;", css_val))
        tw_ok = tw_val == "rounded-[0px_50px_0px_50px]"
        detail = f"css='{css_val}', tailwind='{tw_val}'"
    checks.append({"name": "LeafIcon_css", "passed": css_ok, "detail": detail})
    checks.append({"name": "LeafIcon_tailwind_underscores", "passed": tw_ok, "detail": detail})
    score_parts.extend([css_ok, tw_ok])

    # ---- CHECK 4: StandardCard — 12px all → rounded-[12px] ----
    c4 = get_component("StandardCard")
    css_ok = False
    tw_ok = False
    detail = "StandardCard component not found."
    if c4 is not None:
        css_val = str(c4.get("css", "")).strip()
        tw_val = str(c4.get("tailwind", "")).strip()
        # Uniform → border-radius: 12px;
        css_ok = bool(re.search(r"border-radius:\s*12px;", css_val))
        tw_ok = tw_val == "rounded-[12px]"
        detail = f"css='{css_val}', tailwind='{tw_val}'"
    checks.append({"name": "StandardCard_css", "passed": css_ok, "detail": detail})
    checks.append({"name": "StandardCard_tailwind_arbitrary", "passed": tw_ok, "detail": detail})
    score_parts.extend([css_ok, tw_ok])

    # ---- CHECK 5: HeroImage — 0px 40px 40px 0px mixed ----
    c5 = get_component("HeroImage")
    css_ok = False
    tw_ok = False
    detail = "HeroImage component not found."
    if c5 is not None:
        css_val = str(c5.get("css", "")).strip()
        tw_val = str(c5.get("tailwind", "")).strip()
        css_ok = bool(re.search(r"border-radius:\s*0px\s+40px\s+40px\s+0px;", css_val))
        tw_ok = tw_val == "rounded-[0px_40px_40px_0px]"
        detail = f"css='{css_val}', tailwind='{tw_val}'"
    checks.append({"name": "HeroImage_css", "passed": css_ok, "detail": detail})
    checks.append({"name": "HeroImage_tailwind_mixed", "passed": tw_ok, "detail": detail})
    score_parts.extend([css_ok, tw_ok])

    # ---- CHECK 6: BrokenInput — negative -5px → clamped to 0px all corners ----
    c6 = get_component("BrokenInput")
    css_ok = False
    tw_ok = False
    correction_noted = False
    detail = "BrokenInput component not found."
    if c6 is not None:
        css_val = str(c6.get("css", "")).strip()
        tw_val = str(c6.get("tailwind", "")).strip()
        raw = json.dumps(c6).lower()
        # CSS: border-radius: 0px; (all uniform zero)
        css_ok = bool(re.search(r"border-radius:\s*0px;", css_val))
        # Tailwind: rounded-none (all equal, value is 0)
        tw_ok = tw_val == "rounded-none"
        # There should be some note about correction / negative not allowed
        correction_noted = any(kw in raw for kw in ["negative", "corrected", "clamped", "cannot", "invalid", "note", "warning"])
        detail = f"css='{css_val}', tailwind='{tw_val}', correction_noted={correction_noted}"
    checks.append({"name": "BrokenInput_negative_clamped_css", "passed": css_ok, "detail": detail})
    checks.append({"name": "BrokenInput_tailwind_rounded_none", "passed": tw_ok, "detail": detail})
    checks.append({"name": "BrokenInput_correction_noted", "passed": correction_noted, "detail": detail})
    score_parts.extend([css_ok, tw_ok, correction_noted])

    # ---- CHECK 7: OverflowWidget — 10500px → capped at 9999px → rounded-full ----
    c7 = get_component("OverflowWidget")
    css_ok = False
    tw_ok = False
    detail = "OverflowWidget component not found."
    if c7 is not None:
        css_val = str(c7.get("css", "")).strip()
        tw_val = str(c7.get("tailwind", "")).strip()
        # Capped at 9999 → all equal → border-radius: 9999px;
        css_ok = bool(re.search(r"border-radius:\s*9999px;", css_val))
        tw_ok = tw_val == "rounded-full"
        detail = f"css='{css_val}', tailwind='{tw_val}'"
    checks.append({"name": "OverflowWidget_capped_css", "passed": css_ok, "detail": detail})
    checks.append({"name": "OverflowWidget_tailwind_rounded_full", "passed": tw_ok, "detail": detail})
    score_parts.extend([css_ok, tw_ok])

    # ---- CHECK 8: TabPanel — 16px 16px 0px 0px mixed ----
    c8 = get_component("TabPanel")
    css_ok = False
    tw_ok = False
    detail = "TabPanel component not found."
    if c8 is not None:
        css_val = str(c8.get("css", "")).strip()
        tw_val = str(c8.get("tailwind", "")).strip()
        css_ok = bool(re.search(r"border-radius:\s*16px\s+16px\s+0px\s+0px;", css_val))
        tw_ok = tw_val == "rounded-[16px_16px_0px_0px]"
        detail = f"css='{css_val}', tailwind='{tw_val}'"
    checks.append({"name": "TabPanel_css", "passed": css_ok, "detail": detail})
    checks.append({"name": "TabPanel_tailwind_mixed", "passed": tw_ok, "detail": detail})
    score_parts.extend([css_ok, tw_ok])

    # ---- CHECK 9: RemUnit — 1.5rem → CSS outputs it, Tailwind arbitrary class OMITTED ----
    c9 = get_component("RemUnit")
    css_ok = False
    tw_omitted = False
    detail = "RemUnit component not found."
    if c9 is not None:
        css_val = str(c9.get("css", "")).strip()
        tw_val = c9.get("tailwind", None)
        # CSS should contain 1.5rem
        css_ok = bool(re.search(r"border-radius:\s*1\.5rem;", css_val))
        # Tailwind should be absent, null, empty, or explicitly say "omitted"/"n/a"/"not applicable"
        if tw_val is None:
            tw_omitted = True
        else:
            tw_str = str(tw_val).strip().lower()
            tw_omitted = tw_str in ["", "n/a", "omitted", "not applicable", "none", "null"] or \
                         "omit" in tw_str or "not px" in tw_str or "non-px" in tw_str or \
                         not bool(re.search(r"rounded-\[", tw_str))
        detail = f"css='{css_val}', tailwind='{tw_val}', tw_omitted={tw_omitted}"
    checks.append({"name": "RemUnit_css_preserves_rem", "passed": css_ok, "detail": detail})
    checks.append({"name": "RemUnit_tailwind_omitted_for_non_px", "passed": tw_omitted, "detail": detail})
    score_parts.extend([css_ok, tw_omitted])

    # Compute final score
    total = len(score_parts)
    passed_count = sum(1 for x in score_parts if x)
    final_score = round(passed_count / total, 4) if total > 0 else 0.0

    all_passed = all(c["passed"] for c in checks)
    return checks, final_score

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks, score = run_checks(workspace)
    except Exception as e:
        checks = [{"name": "eval_crash", "passed": False, "detail": str(e)}]
        score = 0.0

    all_passed = all(c["passed"] for c in checks)
    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()