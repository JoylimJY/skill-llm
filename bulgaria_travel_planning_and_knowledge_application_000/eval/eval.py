import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    def add_check(name: str, passed: bool, detail: str):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ── PART 1: Find the trip plan file ──
    trip_plan_files = list(workspace.rglob("kowalski_trip_plan.md"))
    # Also search in root home in case agent placed it there
    home_dir = Path("/root")
    trip_plan_files += list(home_dir.rglob("kowalski_trip_plan.md"))
    # Deduplicate
    trip_plan_files = list({str(f): f for f in trip_plan_files}.values())

    if not trip_plan_files:
        add_check("trip_plan_file_exists", False, "kowalski_trip_plan.md not found anywhere in workspace or home.")
        # Still check memory
        trip_plan_content = ""
    else:
        trip_plan_content = trip_plan_files[0].read_text(encoding="utf-8", errors="replace")
        add_check("trip_plan_file_exists", True, f"Found at: {trip_plan_files[0]}")

    # ── PART 2: Check memory.md was created/updated ──
    memory_path = Path("/root/bulgaria/memory.md")
    if not memory_path.exists():
        add_check("memory_md_exists", False, "~/bulgaria/memory.md does not exist.")
        memory_content = ""
    else:
        memory_content = memory_path.read_text(encoding="utf-8", errors="replace")
        # Check it's not just the template (must have actual values)
        is_template = "<!-- e.g. Beach" in memory_content or memory_content.strip() == ""
        if is_template:
            add_check("memory_md_exists", False, "~/bulgaria/memory.md appears to be the unmodified template.")
        else:
            add_check("memory_md_exists", True, "~/bulgaria/memory.md exists and appears populated.")

    # ── PART 3: Memory.md has correct traveler_style ──
    combined = trip_plan_content + "\n" + memory_content
    try:
        # traveler_style should be Beach (or Beach + Foodie combo acceptable)
        has_beach_style = bool(re.search(r'(Beach|beach)', memory_content))
        add_check(
            "memory_traveler_style_beach",
            has_beach_style,
            "memory.md traveler_style should include 'Beach' given client profile." if not has_beach_style
            else "memory.md correctly identifies Beach traveler style."
        )
    except Exception as e:
        add_check("memory_traveler_style_beach", False, f"Error checking traveler style: {e}")

    # ── PART 4: Memory.md avoids field (must mention Sunny Beach in avoid) ──
    try:
        has_sunny_beach_avoid = bool(re.search(r'(?i)(sunny\s*beach)', memory_content))
        # It should appear in avoid/dislikes section
        avoid_section = re.search(r'(?i)(avoid|dislikes?)[^\n]*\n([^\n]*\n){0,3}', memory_content)
        sunny_in_avoid = False
        if avoid_section:
            sunny_in_avoid = bool(re.search(r'(?i)sunny\s*beach', avoid_section.group(0)))
        # Accept if it's in the avoid field OR the memory mentions it negatively
        add_check(
            "memory_avoids_sunny_beach",
            has_sunny_beach_avoid,
            "memory.md should record Sunny Beach in the 'avoid' field." if not has_sunny_beach_avoid
            else "memory.md correctly records Sunny Beach avoidance."
        )
    except Exception as e:
        add_check("memory_avoids_sunny_beach", False, f"Error: {e}")

    # ── PART 5: Traveler dates in memory ──
    try:
        has_dates = bool(re.search(r'2025[-/]06[-/]1[5-9]|2025[-/]06[-/]18|june.*2025|2025.*june', memory_content, re.IGNORECASE))
        add_check(
            "memory_has_travel_dates",
            has_dates,
            "memory.md should include travel dates (June 2025)." if not has_dates
            else "memory.md includes travel dates."
        )
    except Exception as e:
        add_check("memory_has_travel_dates", False, f"Error: {e}")

    # ── PART 6: Trip plan explicitly warns against Sunny Beach ──
    try:
        warns_sunny_beach = bool(re.search(r'(?i)sunny\s*beach', trip_plan_content))
        # Must be a warning/avoidance, not a recommendation
        if warns_sunny_beach:
            # Check context: should be negative (avoid, warn, not recommended, etc.)
            snippets = re.findall(r'.{0,80}sunny\s*beach.{0,80}', trip_plan_content, re.IGNORECASE)
            negative_keywords = ['avoid', 'not', 'warn', 'skip', 'crowded', 'tourist', 'mass', 'instead', 'recommend against', 'unsuitable', 'bad', 'poor', 'stay away']
            is_negative = any(
                any(kw in snip.lower() for kw in negative_keywords)
                for snip in snippets
            )
            add_check(
                "trip_plan_warns_sunny_beach",
                is_negative,
                f"Sunny Beach mentioned but not clearly flagged as a trap. Context: {snippets}" if not is_negative
                else f"Trip plan correctly warns against Sunny Beach. Context: {snippets[0] if snippets else ''}"
            )
        else:
            add_check(
                "trip_plan_warns_sunny_beach",
                False,
                "Trip plan never mentions Sunny Beach at all — should warn client since they mentioned it."
            )
    except Exception as e:
        add_check("trip_plan_warns_sunny_beach", False, f"Error: {e}")

    # ── PART 7: Trip plan recommends quiet Black Sea destinations (Sozopol / Sinemorets) ──
    try:
        quiet_beach_pattern = r'(?i)(sozopol|sinemorets|kavatsite)'
        has_quiet_beach = bool(re.search(quiet_beach_pattern, trip_plan_content))
        add_check(
            "trip_plan_recommends_quiet_beach",
            has_quiet_beach,
            "Trip plan should recommend quiet alternatives (Sozopol, Sinemorets) per beaches.md and skill rules." if not has_quiet_beach
            else "Trip plan recommends quiet Black Sea destinations."
        )
    except Exception as e:
        add_check("trip_plan_recommends_quiet_beach", False, f"Error: {e}")

    # ── PART 8: Specific food recommendations (banitsa AND/OR shopska AND/OR grilled fish) ──
    try:
        specific_foods = ['banitsa', 'shopska', 'grilled fish', 'rakia', 'kavarma', 'tarator', 'kebapche', 'mekitsi']
        found_foods = [f for f in specific_foods if f.lower() in trip_plan_content.lower()]
        # Must have at least 3 specific foods (Core Rule 1: Specific Beats Generic)
        has_specific_food = len(found_foods) >= 3
        add_check(
            "trip_plan_specific_food_recommendations",
            has_specific_food,
            f"Trip plan must name specific dishes (at least 3). Found: {found_foods}. Core Rule 1: Specific Beats Generic."
            if not has_specific_food
            else f"Trip plan correctly names specific dishes: {found_foods}"
        )
    except Exception as e:
        add_check("trip_plan_specific_food_recommendations", False, f"Error: {e}")

    # ── PART 9: June timing acknowledged as good for Black Sea ──
    try:
        seasonal_reality = bool(re.search(
            r'(?i)(june|september|peak.*season|season.*peak|feel.*best|best.*june|black sea.*june|june.*black sea)',
            trip_plan_content
        ))
        add_check(
            "trip_plan_seasonal_reality",
            seasonal_reality,
            "Trip plan should acknowledge June is a good time for Black Sea (Core Rule 3: Seasonal Reality)." if not seasonal_reality
            else "Trip plan addresses seasonal reality for June."
        )
    except Exception as e:
        add_check("trip_plan_seasonal_reality", False, f"Error: {e}")

    # ── PART 10: Addresses train vs bus friction (Andrzej asked about trains) ──
    try:
        transport_friction = bool(re.search(
            r'(?i)(bus(es)?|intercity bus|train.*not|not.*train|bus.*faster|faster.*bus|bus.*better|better.*bus|etap|biomet|bus.*useful)',
            trip_plan_content
        ))
        add_check(
            "trip_plan_addresses_transport_friction",
            transport_friction,
            "Trip plan must address the trains vs buses question (Core Rule 5: Practical Friction) — buses are often better." if not transport_friction
            else "Trip plan correctly addresses transport friction (buses vs trains)."
        )
    except Exception as e:
        add_check("trip_plan_addresses_transport_friction", False, f"Error: {e}")

    # ── PART 11: Cultural site included (daughter's interest) ──
    try:
        cultural_sites = r'(?i)(sofia|plovdiv|rila|koprivshtitsa|old town|monastery|museum|alexander nevsky|kapana)'
        has_cultural = bool(re.search(cultural_sites, trip_plan_content))
        add_check(
            "trip_plan_includes_cultural_site",
            has_cultural,
            "Trip plan should include at least one cultural/historic site for the daughter." if not has_cultural
            else "Trip plan includes cultural/historic site(s)."
        )
    except Exception as e:
        add_check("trip_plan_includes_cultural_site", False, f"Error: {e}")

    # ── PART 12: No generic food advice (must not say just "try Bulgarian food") ──
    try:
        generic_phrase = bool(re.search(
            r'(?i)\btry Bulgarian food\b|\bexplore Bulgarian cuisine\b|\bsample local food\b',
            trip_plan_content
        ))
        add_check(
            "trip_plan_no_generic_food_advice",
            not generic_phrase,
            "Trip plan uses generic food advice ('try Bulgarian food') — violates Core Rule 1: Specific Beats Generic." if generic_phrase
            else "Trip plan avoids generic food advice."
        )
    except Exception as e:
        add_check("trip_plan_no_generic_food_advice", False, f"Error: {e}")

    # ── Score calculation ──
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = score >= 0.75  # Must pass at least 75% of checks

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))