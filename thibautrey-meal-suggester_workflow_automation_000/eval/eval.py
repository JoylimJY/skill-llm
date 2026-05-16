import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    ws = Path(workspace)
    checks = []
    total = 0
    passed_count = 0

    def add_check(name, passed, detail):
        nonlocal passed_count
        checks.append({"name": name, "passed": passed, "detail": detail})
        if passed:
            passed_count += 1

    # --- Read files ---
    stock_path = ws / "inventory" / "stock.md"
    history_path = ws / "inventory" / "history.md"
    shopping_path = ws / "inventory" / "shopping-list.md"

    stock_text = ""
    history_text = ""
    shopping_text = ""

    try:
        stock_text = stock_path.read_text(encoding="utf-8")
    except Exception as e:
        add_check("stock.md readable", False, f"Could not read stock.md: {e}")

    try:
        history_text = history_path.read_text(encoding="utf-8")
    except Exception as e:
        add_check("history.md readable", False, f"Could not read history.md: {e}")

    try:
        shopping_text = shopping_path.read_text(encoding="utf-8")
    except Exception as e:
        add_check("shopping-list.md readable", False, f"Could not read shopping-list.md: {e}")

    # =======================
    # STOCK CHECKS
    # =======================

    # CHECK 1: lardons reduced or removed
    # Original: lardons (bacon bits): 200g — agent told 100g were used (see task prompt)
    # After 2025-02-07 Carbonara used 100g, remaining should be 100g or item should reflect reduction
    try:
        lardons_match = re.search(r'lardons.*?(\d+)\s*g', stock_text, re.IGNORECASE)
        if lardons_match:
            qty = int(lardons_match.group(1))
            # should be reduced from 200g — any value < 200g is acceptable, ideally 100g
            passed = qty < 200
            add_check(
                "stock.md: lardons quantity reduced",
                passed,
                f"Found lardons at {qty}g. Expected < 200g after usage."
            )
        else:
            # lardons may have been removed entirely (if 0 remaining)
            lardons_present = bool(re.search(r'lardon', stock_text, re.IGNORECASE))
            add_check(
                "stock.md: lardons quantity reduced",
                not lardons_present,  # removed entirely is also valid
                "lardons line not found and not removed — stock not updated."
            )
    except Exception as e:
        add_check("stock.md: lardons quantity reduced", False, f"Error: {e}")

    # CHECK 2: chickpeas reduced
    # Original: chickpeas (canned): 3 cans — task says 1 can used in the new meal
    try:
        chickpeas_match = re.search(r'chickpeas.*?(\d+)\s*can', stock_text, re.IGNORECASE)
        if chickpeas_match:
            qty = int(chickpeas_match.group(1))
            passed = qty < 3
            add_check(
                "stock.md: chickpeas reduced",
                passed,
                f"Found chickpeas at {qty} cans. Expected < 3 after usage."
            )
        else:
            add_check("stock.md: chickpeas reduced", False, "chickpeas line not found in stock.")
    except Exception as e:
        add_check("stock.md: chickpeas reduced", False, f"Error: {e}")

    # CHECK 3: carrots reduced
    # Original: carrots: 4 — task says 1 carrot used
    try:
        carrots_match = re.search(r'carrots?\s*:\s*(\d+)', stock_text, re.IGNORECASE)
        if carrots_match:
            qty = int(carrots_match.group(1))
            passed = qty < 4
            add_check(
                "stock.md: carrots reduced",
                passed,
                f"Found carrots at {qty}. Expected < 4 after usage."
            )
        else:
            add_check("stock.md: carrots reduced", False, "carrots line not found in stock.")
    except Exception as e:
        add_check("stock.md: carrots reduced", False, f"Error: {e}")

    # CHECK 4: stock last updated date updated (should be more recent than 2025-02-09)
    try:
        date_match = re.search(r'Last updated:\s*(\d{4}-\d{2}-\d{2})', stock_text, re.IGNORECASE)
        if date_match:
            date_str = date_match.group(1)
            from dateutil.parser import parse as parse_date
            updated_date = parse_date(date_str).date()
            from datetime import date
            original_date = date(2025, 2, 9)
            passed = updated_date > original_date
            add_check(
                "stock.md: last updated date refreshed",
                passed,
                f"Last updated shows {date_str}. Expected a date after 2025-02-09."
            )
        else:
            add_check("stock.md: last updated date refreshed", False, "No 'Last updated' date found in stock.md.")
    except Exception as e:
        add_check("stock.md: last updated date refreshed", False, f"Error parsing date: {e}")

    # =======================
    # HISTORY CHECKS
    # =======================

    # CHECK 5: New history entry exists for the new meal (Chickpea & Carrot stir-fry or similar)
    try:
        # The task involves cooking with lardons, chickpeas, and a carrot — agent should log a 2025-02-10 entry
        new_entry_present = bool(re.search(r'2025-02-10', history_text, re.IGNORECASE))
        add_check(
            "history.md: new entry for 2025-02-10 added",
            new_entry_present,
            "Expected a history entry dated 2025-02-10 in history.md."
        )
    except Exception as e:
        add_check("history.md: new entry for 2025-02-10 added", False, f"Error: {e}")

    # CHECK 6: History entry contains ingredients used (lardons, chickpeas, carrot)
    try:
        # Look for the section after 2025-02-10
        after_date = re.split(r'## 2025-02-10', history_text, flags=re.IGNORECASE)
        if len(after_date) > 1:
            entry_block = after_date[1].split("##")[0]  # stop at next section
            has_lardons = bool(re.search(r'lardon', entry_block, re.IGNORECASE))
            has_chickpeas = bool(re.search(r'chickpea', entry_block, re.IGNORECASE))
            has_carrot = bool(re.search(r'carrot', entry_block, re.IGNORECASE))
            passed = has_lardons and has_chickpeas and has_carrot
            add_check(
                "history.md: ingredients logged in new entry",
                passed,
                f"Ingredients in entry — lardons:{has_lardons}, chickpeas:{has_chickpeas}, carrot:{has_carrot}."
            )
        else:
            add_check("history.md: ingredients logged in new entry", False, "Could not find 2025-02-10 block in history.md.")
    except Exception as e:
        add_check("history.md: ingredients logged in new entry", False, f"Error: {e}")

    # CHECK 7: Feedback present in history entry (liked/would-repeat or similar sentiment)
    try:
        after_date = re.split(r'## 2025-02-10', history_text, flags=re.IGNORECASE)
        if len(after_date) > 1:
            entry_block = after_date[1].split("##")[0]
            has_feedback = bool(re.search(
                r'(feedback|liked|loved|would.repeat|opinion|rating|great|good|enjoyed)',
                entry_block, re.IGNORECASE
            ))
            add_check(
                "history.md: feedback/rating present in new entry",
                has_feedback,
                "Expected a feedback or rating indicator in the 2025-02-10 history entry."
            )
        else:
            add_check("history.md: feedback/rating present in new entry", False, "Could not find 2025-02-10 block.")
    except Exception as e:
        add_check("history.md: feedback/rating present in new entry", False, f"Error: {e}")

    # =======================
    # SHOPPING LIST CHECKS
    # =======================

    # CHECK 8: Shopping list updated with a more recent date
    try:
        date_match = re.search(r'Last updated:\s*(\d{4}-\d{2}-\d{2})', shopping_text, re.IGNORECASE)
        if date_match:
            date_str = date_match.group(1)
            from dateutil.parser import parse as parse_date
            from datetime import date
            updated_date = parse_date(date_str).date()
            original_date = date(2025, 2, 7)
            passed = updated_date > original_date
            add_check(
                "shopping-list.md: date updated",
                passed,
                f"Shopping list date is {date_str}. Expected after 2025-02-07."
            )
        else:
            add_check("shopping-list.md: date updated", False, "No 'Last updated' date found in shopping-list.md.")
    except Exception as e:
        add_check("shopping-list.md: date updated", False, f"Error: {e}")

    # CHECK 9: Shopping list mentions lardons (now running low after two uses)
    try:
        has_lardons = bool(re.search(r'lardon', shopping_text, re.IGNORECASE))
        add_check(
            "shopping-list.md: lardons flagged for restock",
            has_lardons,
            "Expected lardons to appear in shopping list after repeated usage depleted stock."
        )
    except Exception as e:
        add_check("shopping-list.md: lardons flagged for restock", False, f"Error: {e}")

    # CHECK 10: Shopping list mentions chickpeas
    try:
        has_chickpeas = bool(re.search(r'chickpea', shopping_text, re.IGNORECASE))
        add_check(
            "shopping-list.md: chickpeas flagged for restock",
            has_chickpeas,
            "Expected chickpeas to appear in shopping list after usage."
        )
    except Exception as e:
        add_check("shopping-list.md: chickpeas flagged for restock", False, f"Error: {e}")

    total = len(checks)
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = passed_count >= 8  # require at least 8/10

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))