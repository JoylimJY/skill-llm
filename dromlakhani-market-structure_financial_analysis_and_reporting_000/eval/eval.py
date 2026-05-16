import sys
import json
import re
from pathlib import Path

def find_analysis_file(workspace: Path):
    candidates = list(workspace.rglob("market_analysis_XAUUSD.md"))
    if not candidates:
        candidates = list(workspace.rglob("market_analysis_xauusd.md"))
    if not candidates:
        candidates = list(workspace.rglob("market_analysis*.md"))
    return candidates[0] if candidates else None

def run_eval(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    
    # ── Locate output file ───────────────────────────────────────────────────
    fpath = find_analysis_file(workspace)
    
    if fpath is None:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False,
                        "detail": "No market_analysis_XAUUSD.md file found anywhere in workspace."}]
        }

    try:
        content = fpath.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False,
                        "detail": f"Could not read file: {e}"}]
        }

    content_lower = content.lower()

    # ── CHECK 1: Required section headers present ────────────────────────────
    required_sections = [
        r"##\s+market structure analysis",
        r"###\s+.*macro bias",
        r"###\s+.*current structure",
        r"###\s+.*key zones",
        r"###\s+.*trade narrative",
        r"###\s+.*trigger",
        r"###\s+.*invalidation",
        r"###\s+.*target",
    ]
    missing_sections = []
    for pat in required_sections:
        if not re.search(pat, content_lower):
            missing_sections.append(pat)
    
    sections_ok = len(missing_sections) == 0
    checks.append({
        "name": "required_sections_present",
        "passed": sections_ok,
        "detail": f"Missing sections: {missing_sections}" if missing_sections else "All 8 required sections present."
    })

    # ── CHECK 2: Instrument + Timeframe in header ────────────────────────────
    header_ok = bool(re.search(r"xauusd|xau.*usd|gold", content_lower)) and \
                bool(re.search(r"4h|4-hour|4 hour", content_lower))
    checks.append({
        "name": "instrument_and_timeframe_identified",
        "passed": header_ok,
        "detail": "XAUUSD and 4H timeframe present in analysis." if header_ok
                  else "Missing instrument (XAUUSD/Gold) or timeframe (4H) in analysis."
    })

    # ── CHECK 3: Macro Bias is Bearish ───────────────────────────────────────
    # After CHoCH at candle 17, markdown underway; bias must shift to Bearish
    macro_section = ""
    m = re.search(r"###\s+.*macro bias(.*?)###", content_lower, re.DOTALL)
    if m:
        macro_section = m.group(1)
    else:
        # try to get content after macro bias heading
        m2 = re.search(r"###\s+.*macro bias(.*?)$", content_lower, re.DOTALL)
        if m2:
            macro_section = m2.group(1)[:500]

    bias_bearish = bool(re.search(r"\bbearish\b", macro_section))
    checks.append({
        "name": "macro_bias_is_bearish",
        "passed": bias_bearish,
        "detail": "Macro bias correctly identified as Bearish (post-CHoCH markdown)." if bias_bearish
                  else f"Macro bias should be Bearish after CHoCH and BOS ↓. Found section: '{macro_section[:200]}'"
    })

    # ── CHECK 4: CHoCH is explicitly identified ──────────────────────────────
    choch_mentioned = bool(re.search(r"\bchoch\b|change of character", content_lower))
    checks.append({
        "name": "choch_identified",
        "passed": choch_mentioned,
        "detail": "CHoCH explicitly identified in analysis." if choch_mentioned
                  else "CHoCH (Change of Character) must be identified — price broke below most recent HL at 1935."
    })

    # ── CHECK 5: CHoCH level is approximately correct (1925–1940 range) ──────
    choch_level_ok = False
    choch_detail = "No numeric level found near CHoCH discussion."
    # Look for numbers near choch mentions
    choch_context = ""
    for m in re.finditer(r"choch|change of character", content_lower):
        start = max(0, m.start() - 200)
        end = min(len(content_lower), m.end() + 200)
        choch_context += content_lower[start:end]
    
    # The CHoCH level should reference either the HL that was broken (~1935) 
    # or the candle close (~1928) or the zone around 1925-1940
    nums = re.findall(r"1[89]\d{2}(?:\.\d+)?", choch_context)
    for n in nums:
        v = float(n)
        if 1925.0 <= v <= 1945.0:
            choch_level_ok = True
            choch_detail = f"CHoCH level {v} is within expected range 1925–1945 (HL at 1935, break candle at 1928)."
            break
    if not choch_level_ok and nums:
        choch_detail = f"CHoCH-adjacent numbers found {nums} but none in range 1925–1945."
    
    checks.append({
        "name": "choch_level_approximately_correct",
        "passed": choch_level_ok,
        "detail": choch_detail
    })

    # ── CHECK 6: BOS is identified (at least one BOS ↑ and one BOS ↓) ────────
    bos_mentioned = bool(re.search(r"\bbos\b|break of structure", content_lower))
    bos_up = bool(re.search(r"bos\s*[↑^]|bos.*bull|bullish.*bos|bos.*up|break.*above", content_lower))
    bos_down = bool(re.search(r"bos\s*[↓v]|bos.*bear|bearish.*bos|bos.*down|break.*below", content_lower))
    bos_ok = bos_mentioned and (bos_up or bos_down)
    checks.append({
        "name": "bos_identified",
        "passed": bos_ok,
        "detail": f"BOS identified (up={bos_up}, down={bos_down})." if bos_ok
                  else "BOS (Break of Structure) events must be labeled with direction."
    })

    # ── CHECK 7: Phase is Markdown (or Distribution leading to Markdown) ──────
    phase_ok = bool(re.search(r"\bmarkdown\b", content_lower)) or \
               bool(re.search(r"\bdistribution\b", content_lower))
    checks.append({
        "name": "phase_identified_as_markdown_or_distribution",
        "passed": phase_ok,
        "detail": "Phase correctly identified as Markdown or Distribution." if phase_ok
                  else "Phase must be 'Markdown' (or Distribution→Markdown). Post-CHoCH structure confirms markdown."
    })

    # ── CHECK 8: Order Block identified with approximate level ───────────────
    ob_mentioned = bool(re.search(r"\border block\b|\bobb\b|\b\bOB\b", content) or 
                        re.search(r"order block", content_lower))
    # Bearish OB should be near 1960–1971 range (candle 16 body)
    ob_level_ok = False
    ob_detail = "No order block level found in expected zone."
    
    # Search for OB-adjacent numbers
    ob_contexts = []
    for m in re.finditer(r"order block|bearish ob|\bob\b", content_lower):
        start = max(0, m.start() - 150)
        end = min(len(content_lower), m.end() + 150)
        ob_contexts.append(content_lower[start:end])
    ob_text = " ".join(ob_contexts)
    
    # Also check bullish OB area (1897-1910 range for candle 4)
    ob_nums = re.findall(r"1[89]\d{2}(?:\.\d+)?", ob_text)
    for n in ob_nums:
        v = float(n)
        # Bearish OB: candle 16 body 1962–1968.5
        if 1955.0 <= v <= 1975.0:
            ob_level_ok = True
            ob_detail = f"Bearish OB level {v} within expected range 1955–1975 (candle 16 body 1962–1968.5)."
            break
        # Bullish OB: candle 4 body 1900.5–1906
        if 1897.0 <= v <= 1912.0:
            ob_level_ok = True
            ob_detail = f"Bullish OB level {v} within expected range 1897–1912 (candle 4 body 1900.5–1906)."
            break

    checks.append({
        "name": "order_block_identified_with_level",
        "passed": ob_mentioned and ob_level_ok,
        "detail": ob_detail if ob_mentioned else "Order Block not mentioned in analysis."
    })

    # ── CHECK 9: FVG identified with approximate zone ────────────────────────
    fvg_mentioned = bool(re.search(r"\bfvg\b|fair value gap|imbalance", content_lower))
    fvg_level_ok = False
    fvg_detail = "No FVG level found near expected zone 1925–1935."
    
    if fvg_mentioned:
        fvg_contexts = []
        for m in re.finditer(r"fvg|fair value gap|imbalance", content_lower):
            start = max(0, m.start() - 200)
            end = min(len(content_lower), m.end() + 200)
            fvg_contexts.append(content_lower[start:end])
        fvg_text = " ".join(fvg_contexts)
        fvg_nums = re.findall(r"1[89]\d{2}(?:\.\d+)?", fvg_text)
        for n in fvg_nums:
            v = float(n)
            # Bullish FVG: candle[5].high=1928.0 to candle[7].low=1930.5
            if 1925.0 <= v <= 1938.0:
                fvg_level_ok = True
                fvg_detail = f"FVG level {v} within expected zone 1925–1938 (actual FVG: 1928.0–1930.5)."
                break

    checks.append({
        "name": "fvg_identified_with_level",
        "passed": fvg_mentioned and fvg_level_ok,
        "detail": fvg_detail if fvg_mentioned else "FVG (Fair Value Gap / Imbalance) not mentioned in analysis."
    })

    # ── CHECK 10: Premium / Discount correctly assessed as DISCOUNT ──────────
    # Current price ~1898, range HH~1975.5, major low ~1888, midpoint ~1931
    # Current price below midpoint → DISCOUNT
    discount_ok = bool(re.search(r"\bdiscount\b", content_lower))
    premium_wrong = bool(re.search(r"(?:current|price).*\bpremium\b|\bpremium\b.*(?:current|now|price)", content_lower))
    
    checks.append({
        "name": "current_price_in_discount_zone",
        "passed": discount_ok and not premium_wrong,
        "detail": "Current price correctly identified as being in DISCOUNT zone (below 50% equilibrium ~1931)." if (discount_ok and not premium_wrong)
                  else f"Current price (~1898) is in DISCOUNT (below 50% of ~1975 to ~1888). discount_found={discount_ok}, premium_mislabeled={premium_wrong}."
    })

    # ── CHECK 11: Liquidity zones mentioned (BSL / SSL) ──────────────────────
    liq_ok = bool(re.search(r"\bbsl\b|buy.?side liquidity|buy side liquidity", content_lower)) or \
              bool(re.search(r"\bssl\b|sell.?side liquidity|sell side liquidity", content_lower))
    checks.append({
        "name": "liquidity_zones_identified",
        "passed": liq_ok,
        "detail": "BSL or SSL liquidity zones identified." if liq_ok
                  else "Liquidity zones (BSL above highs / SSL below lows) must be identified."
    })

    # ── CHECK 12: Invalidation level is below current structure (~1885–1905) ─
    # Invalidation for any bullish retracement idea OR for bearish continuation
    # should reference a structural level — typically the swing low ~1888
    inv_ok = False
    inv_detail = "No appropriate invalidation level found."
    inv_section = ""
    m = re.search(r"###\s+.*invalidation(.*?)(?:###|$)", content_lower, re.DOTALL)
    if m:
        inv_section = m.group(1)[:400]
    
    inv_nums = re.findall(r"1[89]\d{2}(?:\.\d+)?", inv_section)
    for n in inv_nums:
        v = float(n)
        if 1870.0 <= v <= 1910.0:
            inv_ok = True
            inv_detail = f"Invalidation level {v} appropriately references structural low zone 1870–1910."
            break
    
    checks.append({
        "name": "invalidation_level_references_structural_low",
        "passed": inv_ok,
        "detail": inv_detail
    })

    # ── CHECK 13: HH/HL/LH/LL swing labels used ──────────────────────────────
    swing_labels = []
    for label in ["hh", "hl", "lh", "ll"]:
        if re.search(r'\b' + label + r'\b', content_lower):
            swing_labels.append(label.upper())
    
    swing_ok = len(swing_labels) >= 3
    checks.append({
        "name": "swing_structure_labels_used",
        "passed": swing_ok,
        "detail": f"Swing labels found: {swing_labels}. Need at least 3 of HH/HL/LH/LL." if swing_ok
                  else f"Only {swing_labels} found. Need HH, HL, LH, LL labels for swing structure."
    })

    # ── CHECK 14: Target references BSL or a structural high ─────────────────
    target_section = ""
    m = re.search(r"###\s+.*target(.*?)(?:###|$)", content_lower, re.DOTALL)
    if m:
        target_section = m.group(1)[:400]
    
    target_nums = re.findall(r"1[89]\d{2}(?:\.\d+)?|2\d{3}(?:\.\d+)?", target_section)
    target_ok = False
    target_detail = "No clear target level found."
    for n in target_nums:
        v = float(n)
        # Target could be a prior low / extended markdown OR reference to BSL above
        if v <= 1890.0 or v >= 1920.0:
            target_ok = True
            target_detail = f"Target level {v} references a meaningful structural level (prior low, SSL area, or BSL)."
            break
    # Also accept textual targets
    if not target_ok:
        if re.search(r"ssl|sell.?side|swing low|equal low|eql|previous low|prior low", target_section):
            target_ok = True
            target_detail = "Target references SSL / previous low zone — structurally valid."
    
    checks.append({
        "name": "target_level_identified",
        "passed": target_ok,
        "detail": target_detail
    })

    # ── Scoring ──────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    
    # Must pass at minimum these critical checks to pass overall
    critical = ["macro_bias_is_bearish", "choch_identified", "bos_identified",
                "phase_identified_as_markdown_or_distribution", "required_sections_present",
                "current_price_in_discount_zone"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical)
    
    overall_passed = critical_passed and score >= 0.72

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "invocation", "passed": False,
                                      "detail": "Usage: eval.py <workspace_dir>"}]}))
        sys.exit(1)
    
    result = run_eval(sys.argv[1])
    print(json.dumps(result, indent=2))