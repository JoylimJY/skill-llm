import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
downloads = Path("/root/Downloads")

checks = []
score_parts = []

EXPECTED_HEADERS = [
    "Product", "Entity", "Operation", "Campaign ID", "Ad Group ID",
    "Portfolio ID", "Ad ID", "Keyword ID", "Product Targeting ID",
    "Campaign Name", "Ad Group Name", "Start Date", "End Date",
    "Targeting Type", "State", "Daily Budget", "SKU", "ASIN",
    "Ad Group Default Bid", "Bid", "Custom Text", "Campaign Type",
    "Targeting Expression"
]

CAMPAIGN_NAME = "ResistanceBands-Q3"
DEFAULT_BID = 0.85
DAILY_BUDGET = 40.00

EXACT_BID = round(DEFAULT_BID * 1.2, 2)   # 1.02
PHRASE_BID = round(DEFAULT_BID * 1.0, 2)  # 0.85
BROAD_BID  = round(DEFAULT_BID * 0.7, 2)  # 0.595 → 0.60 or 0.595

EXPECTED_AD_GROUPS = {"Tier1-Exact", "Tier1-Phrase", "Tier2-Phrase", "Tier3-Broad"}

# Keywords that appear in 3+ ASINs (Tier 1 by overlap rule):
# "resistance bands"      → B09,B08,B07 = 3 ASINs → Tier 1
# "resistance band set"   → B09,B08,B07,B09GYMBAND001 = 4 ASINs → Tier 1
# "loop resistance bands" → B09,B07,B09GYMBAND001,B08WORKOUTSET1 = 4 ASINs → Tier 1
# "physical therapy bands"→ B09,B07,B09GYMBAND001 = 3 ASINs → Tier 1
# "pull up assist bands"  → B08,B09GYMBAND001 = 2 ASINs → Tier 2
# "exercise resistance bands" → B07,B08WORKOUTSET1 = 2 ASINs (medium vol=18000, medium comp) → Tier 2
EXPECTED_TIER1_KW = {"resistance bands", "resistance band set", "loop resistance bands", "physical therapy bands"}
EXPECTED_NEGATIVE_KW = {"nike shoes", "adidas running shoes"}


def find_output_file():
    """Search for the output file in likely locations."""
    # Primary location
    target = downloads / "launchfast-ppc-bulk-20240801.txt"
    if target.exists():
        return target
    # Search broadly
    for p in list(downloads.rglob("launchfast-ppc-bulk*.txt")) + list(workspace.rglob("launchfast-ppc-bulk*.txt")):
        return p
    return None


def parse_tsv(path):
    """Parse TSV file, return (headers, rows)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return [], []
    headers = lines[0].split("\t")
    rows = [line.split("\t") for line in lines[1:] if line.strip()]
    return headers, rows


def row_as_dict(headers, row):
    d = {}
    for i, h in enumerate(headers):
        d[h] = row[i] if i < len(row) else ""
    return d


# ── Check 1: File exists ──────────────────────────────────────────────────────
output_file = find_output_file()
c1_passed = output_file is not None
checks.append({
    "name": "output_file_exists",
    "passed": c1_passed,
    "detail": f"Found at {output_file}" if c1_passed else "launchfast-ppc-bulk-20240801.txt not found in ~/Downloads or workspace"
})
score_parts.append((c1_passed, 1.5))

if not c1_passed:
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

try:
    headers, rows = parse_tsv(output_file)
except Exception as e:
    checks.append({"name": "file_parseable", "passed": False, "detail": str(e)})
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

# ── Check 2: Tab-separated (not comma-separated) ──────────────────────────────
raw_first_line = output_file.read_text(encoding="utf-8").splitlines()[0]
c2_passed = "\t" in raw_first_line and "," not in raw_first_line[:50]
checks.append({
    "name": "file_is_tab_separated",
    "passed": c2_passed,
    "detail": f"First line delimiter check. Tabs found: {chr(9) in raw_first_line}"
})
score_parts.append((c2_passed, 1.5))

# ── Check 3: Exact 23-column header in correct order ─────────────────────────
c3_passed = headers == EXPECTED_HEADERS
checks.append({
    "name": "correct_column_headers_exact_order",
    "passed": c3_passed,
    "detail": f"Expected {len(EXPECTED_HEADERS)} columns in exact order. Got: {headers[:5]}..." if not c3_passed else "Headers match exactly"
})
score_parts.append((c3_passed, 2.0))

# ── Check 4: Campaign row present ────────────────────────────────────────────
try:
    campaign_rows = [row_as_dict(headers, r) for r in rows if len(r) > 2 and r[1] == "Campaign" and r[2] == "Create"]
    c4_passed = any(r.get("Campaign Name") == CAMPAIGN_NAME for r in campaign_rows)
    c4_detail = f"Campaign rows: {len(campaign_rows)}, matching name: {[r.get('Campaign Name') for r in campaign_rows]}"
except Exception as e:
    c4_passed = False
    c4_detail = str(e)
checks.append({"name": "campaign_row_exists", "passed": c4_passed, "detail": c4_detail})
score_parts.append((c4_passed, 1.0))

# ── Check 5: All 4 required Ad Groups present ─────────────────────────────────
try:
    ag_rows = [row_as_dict(headers, r) for r in rows if len(r) > 2 and r[1] == "Ad Group" and r[2] == "Create"]
    found_ag_names = {r.get("Ad Group Name", "") for r in ag_rows}
    c5_passed = EXPECTED_AD_GROUPS.issubset(found_ag_names)
    c5_detail = f"Found ad groups: {found_ag_names}. Required: {EXPECTED_AD_GROUPS}"
except Exception as e:
    c5_passed = False
    c5_detail = str(e)
checks.append({"name": "all_four_ad_groups_present", "passed": c5_passed, "detail": c5_detail})
score_parts.append((c5_passed, 1.5))

# ── Check 6: Keyword rows exist ───────────────────────────────────────────────
try:
    kw_rows = [row_as_dict(headers, r) for r in rows if len(r) > 2 and r[1] == "Keyword" and r[2] == "Create"]
    c6_passed = len(kw_rows) >= 10
    c6_detail = f"Keyword rows found: {len(kw_rows)}"
except Exception as e:
    c6_passed = False
    c6_detail = str(e)
checks.append({"name": "keyword_rows_present", "passed": c6_passed, "detail": c6_detail})
score_parts.append((c6_passed, 1.0))

# ── Check 7: Tier 1 keywords appear in BOTH Tier1-Exact AND Tier1-Phrase ─────
try:
    tier1_exact_kws = {r.get("Targeting Expression", "").lower() for r in kw_rows if r.get("Ad Group Name") == "Tier1-Exact"}
    tier1_phrase_kws = {r.get("Targeting Expression", "").lower() for r in kw_rows if r.get("Ad Group Name") == "Tier1-Phrase"}

    overlap_kws_lower = {k.lower() for k in EXPECTED_TIER1_KW}
    c7a = overlap_kws_lower.issubset(tier1_exact_kws)
    c7b = overlap_kws_lower.issubset(tier1_phrase_kws)
    c7_passed = c7a and c7b
    c7_detail = (
        f"Tier1-Exact has {len(tier1_exact_kws)} kws (expected overlap kws present: {c7a}). "
        f"Tier1-Phrase has {len(tier1_phrase_kws)} kws (expected: {c7b}). "
        f"Missing from Exact: {overlap_kws_lower - tier1_exact_kws}. "
        f"Missing from Phrase: {overlap_kws_lower - tier1_phrase_kws}"
    )
except Exception as e:
    c7_passed = False
    c7_detail = str(e)
checks.append({"name": "tier1_keywords_in_both_exact_and_phrase", "passed": c7_passed, "detail": c7_detail})
score_parts.append((c7_passed, 2.0))

# ── Check 8: Bid multipliers correctly applied ────────────────────────────────
try:
    bid_errors = []

    for r in kw_rows:
        ag = r.get("Ad Group Name", "")
        bid_str = r.get("Bid", "").replace("$", "").strip()
        if not bid_str:
            continue
        try:
            bid_val = float(bid_str)
        except ValueError:
            continue

        if ag == "Tier1-Exact":
            expected = round(EXACT_BID, 2)
            if abs(bid_val - expected) > 0.02:
                bid_errors.append(f"{ag}: got {bid_val}, expected ~{expected}")
        elif ag in ("Tier1-Phrase", "Tier2-Phrase"):
            expected = round(PHRASE_BID, 2)
            if abs(bid_val - expected) > 0.02:
                bid_errors.append(f"{ag}: got {bid_val}, expected ~{expected}")
        elif ag == "Tier3-Broad":
            expected = round(BROAD_BID, 2)
            if abs(bid_val - expected) > 0.03:
                bid_errors.append(f"{ag}: got {bid_val}, expected ~{expected}")

    c8_passed = len(bid_errors) == 0
    c8_detail = f"Bid errors: {bid_errors[:5]}" if bid_errors else f"All bids correctly multiplied (Exact={EXACT_BID}, Phrase={PHRASE_BID}, Broad={BROAD_BID})"
except Exception as e:
    c8_passed = False
    c8_detail = str(e)
checks.append({"name": "bid_multipliers_correctly_applied", "passed": c8_passed, "detail": c8_detail})
score_parts.append((c8_passed, 2.0))

# ── Check 9: Negative keywords exclude irrelevant brand names ─────────────────
try:
    all_rows_dicts = [row_as_dict(headers, r) for r in rows]
    neg_kw_rows = [r for r in all_rows_dicts if "negative" in r.get("Entity", "").lower() or
                   "Negative" in r.get("Targeting Type", "") or
                   "negative" in r.get("Targeting Expression", "").lower() or
                   (r.get("Entity", "") == "Keyword" and "negative" in r.get("Campaign Name", "").lower())]

    # Also check for "negative exact" in any column
    all_text = output_file.read_text(encoding="utf-8").lower()
    c9_passed = ("nike shoes" in all_text and "adidas running shoes" in all_text and
                 ("negative" in all_text))
    c9_detail = f"Negative keyword rows found: {len(neg_kw_rows)}. Nike/Adidas present: {'nike shoes' in all_text}/{' adidas running shoes' in all_text}"
except Exception as e:
    c9_passed = False
    c9_detail = str(e)
checks.append({"name": "negative_keywords_flagged", "passed": c9_passed, "detail": c9_detail})
score_parts.append((c9_passed, 1.5))

# ── Check 10: Daily budget in campaign row ────────────────────────────────────
try:
    budget_ok = False
    for r in campaign_rows:
        budget_str = r.get("Daily Budget", "").replace("$", "").strip()
        if budget_str:
            try:
                if abs(float(budget_str) - DAILY_BUDGET) < 0.01:
                    budget_ok = True
            except ValueError:
                pass
    c10_passed = budget_ok
    c10_detail = f"Daily budget check: expected {DAILY_BUDGET}, campaign rows budgets: {[r.get('Daily Budget') for r in campaign_rows]}"
except Exception as e:
    c10_passed = False
    c10_detail = str(e)
checks.append({"name": "daily_budget_in_campaign_row", "passed": c10_passed, "detail": c10_detail})
score_parts.append((c10_passed, 1.0))

# ── Check 11: Tier2/Tier3 broad group has keywords ───────────────────────────
try:
    broad_kws = {r.get("Targeting Expression", "").lower() for r in kw_rows if r.get("Ad Group Name") == "Tier3-Broad"}
    c11_passed = len(broad_kws) >= 3
    c11_detail = f"Tier3-Broad keywords: {len(broad_kws)} — {list(broad_kws)[:5]}"
except Exception as e:
    c11_passed = False
    c11_detail = str(e)
checks.append({"name": "tier3_broad_group_populated", "passed": c11_passed, "detail": c11_detail})
score_parts.append((c11_passed, 1.0))

# ── Check 12: Product column = "Sponsored Products" for all rows ─────────────
try:
    non_sp_rows = [r for r in rows if len(r) > 0 and r[0] not in ("", "Sponsored Products", "Product")]
    c12_passed = len(non_sp_rows) == 0
    c12_detail = f"Rows with incorrect Product column: {len(non_sp_rows)}"
except Exception as e:
    c12_passed = False
    c12_detail = str(e)
checks.append({"name": "product_column_correct", "passed": c12_passed, "detail": c12_detail})
score_parts.append((c12_passed, 0.5))

# ── Scoring ───────────────────────────────────────────────────────────────────
total_weight = sum(w for _, w in score_parts)
earned = sum(w for (passed, w) in score_parts if passed)
final_score = round(earned / total_weight, 3)

# Must pass critical checks to overall pass
critical_passed = c1_passed and c2_passed and c3_passed and c7_passed and c8_passed
overall_passed = critical_passed and final_score >= 0.70

result = {
    "passed": overall_passed,
    "score": final_score,
    "checks": checks
}
print(json.dumps(result, indent=2))