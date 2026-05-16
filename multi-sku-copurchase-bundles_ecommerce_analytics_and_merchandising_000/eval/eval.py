import sys
import json
import re
from pathlib import Path

def find_output_file(workspace: Path):
    """Find bundle_recommendations.md anywhere in workspace."""
    candidates = list(workspace.rglob("bundle_recommendations.md"))
    return candidates[0] if candidates else None

def run_checks(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    score_parts = []

    # ── Locate the output file ───────────────────────────────────────────────
    output_file = find_output_file(workspace)
    file_found = output_file is not None
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found at {output_file}" if file_found else "bundle_recommendations.md not found anywhere in workspace"
    })
    if not file_found:
        return checks, 0.0

    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return checks, 0.0

    checks.append({"name": "file_readable", "passed": True, "detail": f"File size: {len(content)} chars"})

    # ── Check 1: Methodology note present ────────────────────────────────────
    has_methodology = bool(re.search(
        r'(order[\s_]?id|grouped by order|group.*order|basket|minimum.*order|time window|support|confidence|lift|metric)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "methodology_note_present",
        "passed": has_methodology,
        "detail": "Methodology note found (order grouping, metrics, thresholds)" if has_methodology
                  else "No methodology note found — must explain grouping, time window, thresholds, metric reported"
    })
    score_parts.append(0.15 if has_methodology else 0.0)

    # ── Check 2: At least two bundle cards with EXACT 5-line labeled structure
    hero_pattern = re.compile(r'\[Hero SKU\]\s*[—–-]', re.IGNORECASE)
    acc_a_pattern = re.compile(r'\[Accessory A\]\s*[—–-]', re.IGNORECASE)
    acc_b_pattern = re.compile(r'\[Accessory B\]\s*[—–-]', re.IGNORECASE)
    price_pattern = re.compile(r'\[Bundle discount price\]\s*[—–-]', re.IGNORECASE)
    hook_pattern  = re.compile(r'\[One-click checkout hook\]\s*[—–-]', re.IGNORECASE)

    hero_count  = len(hero_pattern.findall(content))
    acc_a_count = len(acc_a_pattern.findall(content))
    acc_b_count = len(acc_b_pattern.findall(content))
    price_count = len(price_pattern.findall(content))
    hook_count  = len(hook_pattern.findall(content))

    at_least_two_bundles = hero_count >= 2
    all_five_labels_present = (
        hero_count >= 2 and acc_a_count >= 2 and acc_b_count >= 2
        and price_count >= 2 and hook_count >= 2
    )
    checks.append({
        "name": "at_least_two_bundle_cards",
        "passed": at_least_two_bundles,
        "detail": f"[Hero SKU] blocks found: {hero_count} (need ≥2)"
    })
    score_parts.append(0.10 if at_least_two_bundles else 0.0)

    checks.append({
        "name": "all_five_labeled_lines_per_card",
        "passed": all_five_labels_present,
        "detail": (
            f"[Hero SKU]:{hero_count} [Accessory A]:{acc_a_count} [Accessory B]:{acc_b_count} "
            f"[Bundle discount price]:{price_count} [One-click checkout hook]:{hook_count} — all must be ≥2"
        )
    })
    score_parts.append(0.20 if all_five_labels_present else 0.0)

    # ── Check 3: Supplementary Markdown table with correct 5 columns ─────────
    # Look for a table with the required column headers
    table_header_pattern = re.compile(
        r'\|\s*(If customer buys|If.*buys?)\s*\(A\)\s*\|.*Recommend.*\(B\)\s*\|.*Association metric.*\|.*PDP.*\|.*Discount',
        re.IGNORECASE
    )
    has_table_header = bool(table_header_pattern.search(content))

    # Count table data rows (lines starting with | that are not separator or header)
    table_rows = re.findall(r'^\|[^|\-]+\|[^|\-]+\|[^|\-]+\|[^|\-]+\|[^|\-]+\|', content, re.MULTILINE)
    has_four_data_rows = len(table_rows) >= 4

    checks.append({
        "name": "supplementary_table_correct_headers",
        "passed": has_table_header,
        "detail": "5-column table with required headers found" if has_table_header
                  else "Missing table: need 'If customer buys (A) | Recommend (B) | Association metric (value) | PDP / FBT placement | Discount / hook summary'"
    })
    score_parts.append(0.10 if has_table_header else 0.0)

    checks.append({
        "name": "supplementary_table_at_least_four_rows",
        "passed": has_four_data_rows,
        "detail": f"Found {len(table_rows)} data rows in table (need ≥4)"
    })
    score_parts.append(0.10 if has_four_data_rows else 0.0)

    # ── Check 4: Association metrics (support/confidence/lift) with values ────
    has_metric_values = bool(re.search(
        r'(support|confidence|lift)\s*[=:≈]\s*[\d.]+|[\d.]+\s*\(?(support|confidence|lift)\)?',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "association_metric_values_present",
        "passed": has_metric_values,
        "detail": "Numeric association metric values found (support/confidence/lift)" if has_metric_values
                  else "No numeric association metric values found — must report e.g. confidence=0.82 or lift: 3.1"
    })
    score_parts.append(0.10 if has_metric_values else 0.0)

    # ── Check 5: Logic chain subsection ──────────────────────────────────────
    has_logic_chain_header = bool(re.search(
        r'logic\s+chain', content, re.IGNORECASE
    ))
    # Arrow or numbered rules: "A → B" or "1. A → B" or "priority"
    has_arrow_or_numbered_rules = bool(re.search(
        r'(→|->|⟹|priority\s*\d|^\s*\d+\.\s+\w.*→)',
        content, re.IGNORECASE | re.MULTILINE
    ))
    checks.append({
        "name": "logic_chain_subsection_present",
        "passed": has_logic_chain_header,
        "detail": "'Logic chain' subsection found" if has_logic_chain_header
                  else "Missing 'Logic chain' subsection — must end with numbered/arrow rules"
    })
    score_parts.append(0.10 if has_logic_chain_header else 0.0)

    checks.append({
        "name": "logic_chain_uses_arrow_or_numbered_rules",
        "passed": has_arrow_or_numbered_rules,
        "detail": "Arrow (→ or ->) or numbered priority rules found in logic chain" if has_arrow_or_numbered_rules
                  else "Logic chain must use arrow (→/->) or numbered rules with priority notation"
    })
    score_parts.append(0.10 if has_arrow_or_numbered_rules else 0.0)

    # ── Check 6: Real SKUs from the input CSV are referenced ─────────────────
    known_skus = ["TENT-2P-GRN", "SLEEP-BAG-20F", "PAD-FOAM-RL",
                  "BOOT-HK42", "SOCK-WL01", "POLE-ALU-PR",
                  "HEADLAMP-CR", "FILTER-H2O", "PACK-45L-BK",
                  "STOVE-CMP", "FUEL-CANN"]
    found_skus = [sku for sku in known_skus if sku in content]
    has_real_skus = len(found_skus) >= 4
    checks.append({
        "name": "real_skus_from_input_data_used",
        "passed": has_real_skus,
        "detail": f"Found {len(found_skus)} real SKUs: {found_skus[:6]}... (need ≥4)"
    })
    score_parts.append(0.05 if has_real_skus else 0.0)

    # ── Final score ──────────────────────────────────────────────────────────
    total_score = round(sum(score_parts), 3)
    return checks, total_score

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks, score = run_checks(workspace)
    except Exception as e:
        checks = [{"name": "eval_error", "passed": False, "detail": str(e)}]
        score = 0.0

    passed = score >= 0.70 and all(
        c["passed"] for c in checks
        if c["name"] in ("output_file_exists", "at_least_two_bundle_cards", "all_five_labeled_lines_per_card", "logic_chain_subsection_present")
    )

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()