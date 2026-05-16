import sys
import json
import unicodedata
from pathlib import Path

def make_result(passed, score, checks):
    return {"passed": passed, "score": score, "checks": checks}

def check(name, condition, detail_pass, detail_fail):
    return {"name": name, "passed": bool(condition), "detail": detail_pass if condition else detail_fail}

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    # --- Find aurora_protocol.codex anywhere in workspace ---
    matches = list(Path(workspace).rglob("aurora_protocol.codex"))
    file_found = len(matches) > 0
    checks.append(check(
        "aurora_protocol.codex exists",
        file_found,
        f"Found at {matches[0]}",
        "File aurora_protocol.codex not found anywhere in workspace"
    ))

    if not file_found:
        return make_result(False, 0.0, checks)

    codex_path = matches[0]
    try:
        content = codex_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "File readable", "passed": False, "detail": str(e)})
        return make_result(False, 0.0, checks)

    checks.append(check("File readable and non-empty", len(content.strip()) > 0,
                         f"File has {len(content)} chars", "File is empty"))

    # === OPERATOR SYMBOL VERIFICATION ===
    # These are the exact Unicode codepoints from SKILL.md
    # The proprietary trap: agents must use exact Unicode, not ASCII approximations

    REQUIRED_OPERATORS = {
        "⊕": "Instantiation (U+2295)",
        "⦰": "Annulation (U+29B0)",
        "⫸": "Convergence (U+2AF8)",
        "⨎": "Fracture (U+2A0E)",
        "⟐": "Scrutiny (U+27D0)",
        "⧇": "Confinement (U+29C7)",
        "⇞": "Intensification (U+21DE)",
        "⊖": "Stasis (U+2296)",
        "⟡": "Divergence Seed (U+27E1)",
        "⧖": "Mnemonic Seed (U+29D6)",
        "↺": "Reflexive Seed (U+21BA)",
    }

    # --- Check all 4 scenarios are labeled ---
    scenario_labels_found = []
    for i in range(1, 5):
        found = (
            f"Scenario {i}" in content or
            f"SCENARIO {i}" in content or
            f"scenario {i}" in content or
            f"Scenario{i}" in content or
            f"SCENARIO{i}" in content
        )
        scenario_labels_found.append(found)

    all_scenarios_labeled = all(scenario_labels_found)
    checks.append(check(
        "All 4 scenarios labeled in file",
        all_scenarios_labeled,
        "All 4 scenario labels found",
        f"Missing scenario labels: {[i+1 for i,v in enumerate(scenario_labels_found) if not v]}"
    ))

    # === SCENARIO-SPECIFIC OPERATOR CHECKS ===

    # --- SCENARIO 1: "THE ANCHORING TRAP" ---
    # Required: ⟐ (Scrutiny) to examine/expose skeleton, ⦰ (Annulation) to destroy anchoring, ⊕ (Instantiation) to create fresh frame
    # Strategy: find the section between Scenario 1 and Scenario 2 markers
    try:
        import re
        # Extract scenario blocks by splitting on scenario headers
        # We look for each scenario block
        def extract_scenario_block(text, scenario_num):
            patterns = [
                rf'(?:Scenario|SCENARIO)\s*{scenario_num}.*?(?=(?:Scenario|SCENARIO)\s*{scenario_num+1}|\Z)',
            ]
            for p in patterns:
                m = re.search(p, text, re.DOTALL | re.IGNORECASE)
                if m:
                    return m.group(0)
            return ""

        s1 = extract_scenario_block(content, 1)
        s2 = extract_scenario_block(content, 2)
        s3 = extract_scenario_block(content, 3)
        # s4 is everything after Scenario 4
        s4_match = re.search(r'(?:Scenario|SCENARIO)\s*4.*', content, re.DOTALL | re.IGNORECASE)
        s4 = s4_match.group(0) if s4_match else ""

    except Exception as e:
        s1, s2, s3, s4 = "", "", "", ""

    # Scenario 1 checks
    s1_scrutiny = "⟐" in s1
    s1_annulation = "⦰" in s1
    s1_instantiation = "⊕" in s1
    checks.append(check(
        "Scenario 1: Scrutiny operator (⟐) present",
        s1_scrutiny,
        "⟐ found in Scenario 1",
        "⟐ (Scrutiny) missing from Scenario 1 — required to expose hidden skeleton of mental model"
    ))
    checks.append(check(
        "Scenario 1: Annulation operator (⦰) present",
        s1_annulation,
        "⦰ found in Scenario 1",
        "⦰ (Annulation) missing from Scenario 1 — required to destroy anchoring pattern"
    ))
    checks.append(check(
        "Scenario 1: Instantiation operator (⊕) present",
        s1_instantiation,
        "⊕ found in Scenario 1",
        "⊕ (Instantiation) missing from Scenario 1 — required to manifest fresh analytical frame"
    ))

    # Sequence ordering for Scenario 1: ⟐ must appear before ⦰, which must appear before ⊕
    s1_order_correct = False
    try:
        pos_scrutiny = s1.index("⟐")
        pos_annulation = s1.index("⦰")
        pos_instantiation = s1.index("⊕")
        s1_order_correct = (pos_scrutiny < pos_annulation < pos_instantiation)
    except (ValueError, Exception):
        s1_order_correct = False

    checks.append(check(
        "Scenario 1: Correct operator ordering (⟐ → ⦰ → ⊕)",
        s1_order_correct,
        "Operators appear in correct sequence order in Scenario 1",
        "Operators in Scenario 1 are not in required order: Scrutiny(⟐) → Annulation(⦰) → Instantiation(⊕)"
    ))

    # Scenario 2 checks: Full Divergence Protocol
    # Must use ⟡ (Divergence Seed) first, then ⦰ (Annulation), then ⊕ (Instantiation), then ⧖ (Mnemonic Seed)
    s2_divergence_seed = "⟡" in s2
    s2_annulation = "⦰" in s2
    s2_instantiation = "⊕" in s2
    s2_mnemonic_seed = "⧖" in s2

    checks.append(check(
        "Scenario 2: Divergence Seed (⟡) present",
        s2_divergence_seed,
        "⟡ found in Scenario 2",
        "⟡ (Divergence Seed) missing — this is the specific meta-catalyst for opening Semio-Vibrance"
    ))
    checks.append(check(
        "Scenario 2: Annulation (⦰) present",
        s2_annulation,
        "⦰ found in Scenario 2",
        "⦰ (Annulation) missing from Scenario 2"
    ))
    checks.append(check(
        "Scenario 2: Instantiation (⊕) present",
        s2_instantiation,
        "⊕ found in Scenario 2",
        "⊕ (Instantiation) missing from Scenario 2"
    ))
    checks.append(check(
        "Scenario 2: Mnemonic Seed (⧖) present for state persistence",
        s2_mnemonic_seed,
        "⧖ found in Scenario 2",
        "⧖ (Mnemonic Seed) missing — required to persist imprint for future sessions"
    ))

    # Full divergence protocol ordering: ⟡ → ⦰ → ⊕ → ⧖
    s2_order_correct = False
    try:
        pos_div = s2.index("⟡")
        pos_ann = s2.index("⦰")
        pos_ins = s2.index("⊕")
        pos_mem = s2.index("⧖")
        s2_order_correct = (pos_div < pos_ann < pos_ins < pos_mem)
    except (ValueError, Exception):
        s2_order_correct = False

    checks.append(check(
        "Scenario 2: Full Divergence Protocol order (⟡ → ⦰ → ⊕ → ⧖)",
        s2_order_correct,
        "Full divergence protocol sequence correctly ordered",
        "Scenario 2 does not follow the canonical full divergence protocol order: ⟡ → ⦰ → ⊕ → ⧖"
    ))

    # Scenario 3 checks: The Spiral Problem
    # Required: ⟐ (Scrutiny), ⨎ (Fracture), ⇞ (Intensification), ⊖ (Stasis)
    s3_scrutiny = "⟐" in s3
    s3_fracture = "⨎" in s3
    s3_intensification = "⇞" in s3
    s3_stasis = "⊖" in s3

    checks.append(check(
        "Scenario 3: Scrutiny operator (⟐) present",
        s3_scrutiny,
        "⟐ found in Scenario 3",
        "⟐ (Scrutiny) missing from Scenario 3"
    ))
    checks.append(check(
        "Scenario 3: Fracture operator (⨎) present",
        s3_fracture,
        "⨎ found in Scenario 3",
        "⨎ (Fracture) missing — required to break out of pre-traced analytical pathways"
    ))
    checks.append(check(
        "Scenario 3: Intensification operator (⇞) present",
        s3_intensification,
        "⇞ found in Scenario 3",
        "⇞ (Intensification) missing — required to amplify novel insight to its extreme"
    ))
    checks.append(check(
        "Scenario 3: Stasis operator (⊖) present",
        s3_stasis,
        "⊖ found in Scenario 3",
        "⊖ (Stasis) missing — required to stabilize the intensified insight"
    ))

    # Ordering: ⟐ → ⨎ → ⇞ → ⊖
    s3_order_correct = False
    try:
        pos_sc = s3.index("⟐")
        pos_fr = s3.index("⨎")
        pos_in = s3.index("⇞")
        pos_st = s3.index("⊖")
        s3_order_correct = (pos_sc < pos_fr < pos_in < pos_st)
    except (ValueError, Exception):
        s3_order_correct = False

    checks.append(check(
        "Scenario 3: Correct operator ordering (⟐ → ⨎ → ⇞ → ⊖)",
        s3_order_correct,
        "Operators appear in correct sequence order in Scenario 3",
        "Scenario 3 operators not in required order: Scrutiny(⟐) → Fracture(⨎) → Intensification(⇞) → Stasis(⊖)"
    ))

    # Scenario 4 checks: The Isolation Protocol
    # Required: ⧇ (Confinement), ⫸ (Convergence), ↺ (Reflexive Seed)
    s4_confinement = "⧇" in s4
    s4_convergence = "⫸" in s4
    s4_reflexive = "↺" in s4

    checks.append(check(
        "Scenario 4: Confinement operator (⧇) present",
        s4_confinement,
        "⧇ found in Scenario 4",
        "⧇ (Confinement) missing — required to create sealed cognitive workspace"
    ))
    checks.append(check(
        "Scenario 4: Convergence operator (⫸) present",
        s4_convergence,
        "⫸ found in Scenario 4",
        "⫸ (Convergence) missing — required to convert raw intelligence into actionable insight"
    ))
    checks.append(check(
        "Scenario 4: Reflexive Seed (↺) present",
        s4_reflexive,
        "↺ found in Scenario 4",
        "↺ (Reflexive Seed) missing — required to introspect on the process after conversion"
    ))

    # Ordering for Scenario 4: ⧇ → ⫸ → ↺
    s4_order_correct = False
    try:
        pos_co = s4.index("⧇")
        pos_cv = s4.index("⫸")
        pos_rf = s4.index("↺")
        s4_order_correct = (pos_co < pos_cv < pos_rf)
    except (ValueError, Exception):
        s4_order_correct = False

    checks.append(check(
        "Scenario 4: Correct operator ordering (⧇ → ⫸ → ↺)",
        s4_order_correct,
        "Operators appear in correct sequence order in Scenario 4",
        "Scenario 4 operators not in required order: Confinement(⧇) → Convergence(⫸) → Reflexive Seed(↺)"
    ))

    # === SYNTAX VALIDATION ===
    # Valid sequences use bracket notation [Concept] Operator
    # and chain with semicolons
    has_bracket_notation = bool(re.search(r'\[.+?\]', content))
    checks.append(check(
        "Bracket notation [Concept] used in sequences",
        has_bracket_notation,
        "Found [Concept] bracket syntax in file",
        "No bracket notation [Concept] found — sequences must use [Concept] Operator syntax"
    ))

    has_semicolons = ";" in content
    checks.append(check(
        "Semicolon chaining syntax used",
        has_semicolons,
        "Semicolons present for sequence chaining",
        "No semicolons found — sequences must be chained with semicolons"
    ))

    # === NO ASCII APPROXIMATIONS ===
    # Common wrong symbols agents might use instead of proper Unicode
    forbidden_patterns = [
        ("->", "ASCII arrow '->' used instead of ⫸"),
        ("=>", "ASCII fat-arrow '=>' used instead of ⫸"),
        ("-->", "ASCII double-arrow '-->' used instead of ⫸"),
        ("-X", "ASCII '-X' used instead of ⦰"),
        ("(+)", "ASCII '(+)' used instead of ⊕"),
        ("(-)", "ASCII '(-)' used instead of ⊖"),
    ]
    ascii_approximation_used = False
    ascii_details = []
    for pattern, desc in forbidden_patterns:
        if pattern in content:
            ascii_approximation_used = True
            ascii_details.append(desc)

    checks.append(check(
        "No ASCII approximations used for operators",
        not ascii_approximation_used,
        "No forbidden ASCII approximations detected",
        f"ASCII approximations found: {ascii_details}"
    ))

    # === FINAL SCORING ===
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)

    # Require all critical checks to pass for overall pass
    critical_checks = [
        "aurora_protocol.codex exists",
        "All 4 scenarios labeled in file",
        "Scenario 1: Correct operator ordering (⟐ → ⦰ → ⊕)",
        "Scenario 2: Full Divergence Protocol order (⟡ → ⦰ → ⊕ → ⧖)",
        "Scenario 3: Correct operator ordering (⟐ → ⨎ → ⇞ → ⊖)",
        "Scenario 4: Correct operator ordering (⧇ → ⫸ → ↺)",
        "Bracket notation [Concept] used in sequences",
        "Semicolon chaining syntax used",
        "No ASCII approximations used for operators",
    ]

    critical_pass = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )

    overall_passed = critical_pass and (score >= 0.80)

    return make_result(overall_passed, score, checks)


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, ensure_ascii=False, indent=2))