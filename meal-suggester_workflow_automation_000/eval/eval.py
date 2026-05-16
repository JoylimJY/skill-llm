import sys
import json
import re
from pathlib import Path

workspace = sys.argv[1]
base = Path(workspace) / "meal-suggester"

checks = []

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# ─── 1. stock.md — lardons consumed/depleted ───────────────────────────────
try:
    stock_text = (base / "inventory" / "stock.md").read_text()
    # lardons should be removed or zeroed (agent cooked with ALL lardons: 200g used)
    lardons_gone = (
        "lardons" not in stock_text.lower()
        or re.search(r'lardons\s*[—\-–]\s*0', stock_text, re.IGNORECASE) is not None
        or re.search(r'lardons\s*[—\-–]\s*none', stock_text, re.IGNORECASE) is not None
        or re.search(r'~~.*lardons.*~~', stock_text, re.IGNORECASE) is not None
    )
    check(
        "stock.md: lardons removed or zeroed after use",
        lardons_gone,
        f"lardons entry: {[l for l in stock_text.splitlines() if 'lardon' in l.lower()] or 'not found'}"
    )
except Exception as e:
    check("stock.md: lardons removed or zeroed after use", False, f"Error reading stock.md: {e}")

# ─── 2. stock.md — pois chiches reduced or depleted ────────────────────────
try:
    stock_text = (base / "inventory" / "stock.md").read_text()
    lines = [l for l in stock_text.splitlines() if 'pois chiches' in l.lower() or 'chickpea' in l.lower()]
    original_had_2_cans = True  # was "2 cans"
    # Agent should either reduce (1 can) or remove entirely
    if not lines:
        # removed entirely — acceptable if fully consumed
        check("stock.md: pois chiches reduced/removed after use", True, "pois chiches removed from stock")
    else:
        line = lines[0]
        # check it's no longer "2 cans" (i.e., reduced)
        still_2 = bool(re.search(r'\b2\s*cans?\b', line, re.IGNORECASE))
        check(
            "stock.md: pois chiches reduced/removed after use",
            not still_2,
            f"pois chiches line: '{line}'"
        )
except Exception as e:
    check("stock.md: pois chiches reduced/removed after use", False, f"Error: {e}")

# ─── 3. stock.md — carrot reduced ──────────────────────────────────────────
try:
    stock_text = (base / "inventory" / "stock.md").read_text()
    lines = [l for l in stock_text.splitlines() if 'carrot' in l.lower() or 'carotte' in l.lower()]
    if not lines:
        check("stock.md: carrot reduced/removed after use", True, "carrot removed from stock entirely")
    else:
        line = lines[0]
        # was "3", should now be less (2 or 1 or 0) or removed
        still_3 = bool(re.search(r'\b3\b', line))
        check(
            "stock.md: carrot reduced/removed after use",
            not still_3,
            f"carrot line: '{line}'"
        )
except Exception as e:
    check("stock.md: carrot reduced/removed after use", False, f"Error: {e}")

# ─── 4. history.md — new entry added with feedback vocabulary ──────────────
try:
    history_text = (base / "inventory" / "history.md").read_text()
    # Must have a new entry for the weekend meals (2025-06-07 or 2025-06-08 range, or any date after 2025-05-30)
    new_entry_dates = re.findall(r'##\s*(\d{4}-\d{2}-\d{2})', history_text)
    dates_after_cutoff = [d for d in new_entry_dates if d > "2025-05-30"]
    check(
        "history.md: new entry added after 2025-05-30",
        len(dates_after_cutoff) >= 1,
        f"Dates found after cutoff: {dates_after_cutoff}"
    )
except Exception as e:
    check("history.md: new entry added after 2025-05-30", False, f"Error: {e}")

# ─── 5. history.md — uses skill-defined feedback vocabulary ────────────────
try:
    history_text = (base / "inventory" / "history.md").read_text()
    valid_feedback_words = ["liked", "disliked", "would-repeat"]
    found = [w for w in valid_feedback_words if w in history_text.lower()]
    # The new entry must include at least one feedback tag from the skill's vocabulary
    # Check that at least one of the defined feedback tags appears in a new (post-2025-05-30) entry block
    # We'll look for any occurrence in the full file (existing entries also have them, so we check for "would-repeat" as it's the most distinctive)
    # More robust: find all feedback lines in new entries
    new_section_match = re.search(
        r'##\s*(202[5-9]-\d{2}-\d{2}|20[3-9]\d-\d{2}-\d{2}).*?(?=\n##\s*\d{4}|\Z)',
        history_text,
        re.DOTALL
    )
    if new_section_match:
        new_section = new_section_match.group(0)
        found_in_new = [w for w in valid_feedback_words if w in new_section.lower()]
        check(
            "history.md: new entry uses skill feedback vocabulary (liked/disliked/would-repeat)",
            len(found_in_new) >= 1,
            f"Feedback words found in new entry: {found_in_new}"
        )
    else:
        # fallback: just check the entire file has the vocab
        check(
            "history.md: new entry uses skill feedback vocabulary (liked/disliked/would-repeat)",
            len(found) >= 1,
            f"Feedback words found in file: {found}"
        )
except Exception as e:
    check("history.md: new entry uses skill feedback vocabulary (liked/disliked/would-repeat)", False, f"Error: {e}")

# ─── 6. history.md — ingredients used are logged in the new entry ──────────
try:
    history_text = (base / "inventory" / "history.md").read_text()
    # At least two of the used ingredients should appear in the history entry
    used_ingredients = ["lardons", "pois chiches", "carrot", "carotte"]
    found_ingr = [i for i in used_ingredients if i.lower() in history_text.lower()]
    check(
        "history.md: used ingredients logged in history",
        len(found_ingr) >= 2,
        f"Found used ingredients in history: {found_ingr}"
    )
except Exception as e:
    check("history.md: used ingredients logged in history", False, f"Error: {e}")

# ─── 7. shopping-list.md — depleted/low items added ───────────────────────
try:
    shopping_text = (base / "inventory" / "shopping-list.md").read_text()
    # lardons was fully used, must appear in shopping list
    lardons_in_shopping = "lardons" in shopping_text.lower()
    check(
        "shopping-list.md: lardons added to shopping list (depleted)",
        lardons_in_shopping,
        f"'lardons' found in shopping list: {lardons_in_shopping}"
    )
except Exception as e:
    check("shopping-list.md: lardons added to shopping list (depleted)", False, f"Error: {e}")

# ─── 8. shopping-list.md — pois chiches or carrot also flagged ────────────
try:
    shopping_text = (base / "inventory" / "shopping-list.md").read_text()
    chickpea_flag = ("pois chiches" in shopping_text.lower() or "chickpea" in shopping_text.lower())
    carrot_flag = ("carrot" in shopping_text.lower() or "carotte" in shopping_text.lower())
    check(
        "shopping-list.md: at least one more depleted ingredient flagged (pois chiches or carrot)",
        chickpea_flag or carrot_flag,
        f"pois chiches: {chickpea_flag}, carrot: {carrot_flag}"
    )
except Exception as e:
    check("shopping-list.md: at least one more depleted ingredient flagged", False, f"Error: {e}")

# ─── 9. stock.md last-updated date reflects recent activity ────────────────
try:
    stock_text = (base / "inventory" / "stock.md").read_text()
    # Should have a date more recent than 2025-06-01 (the original date)
    dates_found = re.findall(r'\d{4}-\d{2}-\d{2}', stock_text)
    updated = any(d > "2025-06-01" for d in dates_found)
    check(
        "stock.md: _Last updated_ date reflects recent modification",
        updated,
        f"Dates found in stock.md: {dates_found}"
    )
except Exception as e:
    check("stock.md: _Last updated_ date reflects recent modification", False, f"Error: {e}")

# ─── 10. No forbidden files were created in unexpected locations ────────────
try:
    unexpected = []
    for f in base.rglob("*"):
        if f.is_file() and f.suffix in [".py", ".sh"] and f.parent.name not in ["scripts"]:
            unexpected.append(str(f.relative_to(base)))
    check(
        "No unexpected script files created outside scripts/ directory",
        len(unexpected) == 0,
        f"Unexpected script files: {unexpected if unexpected else 'none'}"
    )
except Exception as e:
    check("No unexpected script files outside scripts/", False, f"Error: {e}")

# ─── Score ──────────────────────────────────────────────────────────────────
passed_count = sum(1 for c in checks if c["passed"])
total = len(checks)
score = round(passed_count / total, 3)
overall = passed_count >= 7  # must pass at least 7/10

result = {
    "passed": overall,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))