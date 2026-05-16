import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    max_score = 10.0

    # --- Find the output file ---
    output_files = list(workspace.rglob("nova_roundtable_analysis.md"))
    if not output_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False, "detail": "nova_roundtable_analysis.md not found anywhere in workspace"}]
        }

    output_path = output_files[0]
    try:
        content = output_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_readable", "passed": False, "detail": f"Could not read file: {e}"}]
        }

    content_lower = content.lower()

    # CHECK 1: File exists and is non-trivial
    file_size_ok = len(content) > 800
    checks.append({
        "name": "output_file_substantial",
        "passed": file_size_ok,
        "detail": f"File length: {len(content)} chars (need >800)"
    })
    if file_size_ok:
        total_score += 0.5

    # CHECK 2: Two rounds of discussion present
    round1_present = bool(re.search(r'##\s*🗣️?\s*第一轮|##\s*Round\s*1|##\s*🗣️\s*Round', content, re.IGNORECASE))
    round2_present = bool(re.search(r'##\s*🗣️?\s*第二轮|##\s*Round\s*2|##\s*🗣️\s*Round\s*2', content, re.IGNORECASE))
    # Also accept English variants
    if not round1_present:
        round1_present = bool(re.search(r'round\s*1|第一轮', content_lower))
    if not round2_present:
        round2_present = bool(re.search(r'round\s*2|第二轮', content_lower))

    two_rounds = round1_present and round2_present
    checks.append({
        "name": "two_rounds_present",
        "passed": two_rounds,
        "detail": f"Round 1 found: {round1_present}, Round 2 found: {round2_present}"
    })
    if two_rounds:
        total_score += 1.0

    # CHECK 3: Mandatory roles for large trade (>$1k): 
    # RiskGuardian, FinanceAnalyst, MarketAnalyst, HistorianAnalyst, DevilsAdvocate, SkepticalOperator
    mandatory_roles = {
        "RiskGuardian": ["riskguardian", "risk guardian", "⚠️"],
        "FinanceAnalyst": ["financeanalyst", "finance analyst", "💰"],
        "MarketAnalyst": ["marketanalyst", "market analyst", "📉"],
        "HistorianAnalyst": ["historiananalyst", "historian analyst", "historian", "📚"],
        "DevilsAdvocate": ["devilsadvocate", "devil's advocate", "devils advocate", "😈"],
        "SkepticalOperator": ["skepticaloperator", "skeptical operator", "🤔"],
    }

    roles_found = {}
    for role, patterns in mandatory_roles.items():
        found = any(p in content_lower for p in patterns)
        # Also check original case for emoji-based detection
        found = found or any(p in content for p in patterns if not p.isascii())
        roles_found[role] = found

    all_mandatory_roles_present = all(roles_found.values())
    roles_detail = ", ".join([f"{k}:{'✓' if v else '✗'}" for k, v in roles_found.items()])
    checks.append({
        "name": "all_six_mandatory_roles_present",
        "passed": all_mandatory_roles_present,
        "detail": f"Mandatory roles: {roles_detail}"
    })
    if all_mandatory_roles_present:
        total_score += 2.0
    else:
        # Partial credit: each role found = 0.3 points
        found_count = sum(1 for v in roles_found.values() if v)
        partial = round(found_count * 0.3, 2)
        total_score += partial

    # CHECK 4: At least 6 distinct roles total (participant count rule for >$1k)
    # Count role headers (lines starting with ### containing a role or emoji)
    role_headers = re.findall(r'###\s+.{1,50}', content)
    # Count unique role mentions (broader)
    all_role_names = [
        "riskguardian", "financeanalyst", "marketanalyst", "historiananalyst",
        "devilsadvocate", "skepticaloperator", "growthrategist", "techenginer",
        "productmanager", "datascientist", "securityauditor", "creativedirector",
        "useradvocate", "legalcounsel", "qualityarchitect",
        "risk guardian", "finance analyst", "market analyst", "historian analyst",
        "devil's advocate", "skeptical operator", "growth strategist",
        "tech engineer", "product manager", "data scientist", "security auditor",
        "creative director", "user advocate", "legal counsel", "quality architect"
    ]
    unique_roles_in_content = set()
    for rname in all_role_names:
        if rname in content_lower:
            unique_roles_in_content.add(rname)

    # More robust: count ### headers that look like role introductions
    header_count = len(role_headers)
    # Divide by 2 (two rounds) to get approximate unique roles
    estimated_unique = max(len(unique_roles_in_content), header_count // 2) if header_count > 0 else len(unique_roles_in_content)
    # Also just count total distinct role-name occurrences
    six_or_more = estimated_unique >= 5 or header_count >= 10  # 6 roles × ~2 rounds = 12 headers minimum, but lenient
    checks.append({
        "name": "at_least_six_participants",
        "passed": six_or_more,
        "detail": f"Estimated unique roles: {estimated_unique}, total role section headers: {header_count}"
    })
    if six_or_more:
        total_score += 1.0

    # CHECK 5: Consensus section present with action items
    consensus_present = bool(re.search(r'##\s*📊?\s*consensus|##\s*📊\s*consensus|consensus', content_lower))
    action_items_present = bool(re.search(r'-\s*\[\s*\]\s*.{5,}', content))  # checkbox format
    checks.append({
        "name": "consensus_section_present",
        "passed": consensus_present,
        "detail": f"Consensus section found: {consensus_present}"
    })
    if consensus_present:
        total_score += 0.5

    checks.append({
        "name": "action_items_checkbox_format",
        "passed": action_items_present,
        "detail": f"Checkbox action items '- [ ]' found: {action_items_present}"
    })
    if action_items_present:
        total_score += 1.0

    # CHECK 6: Priority scoring formula applied correctly
    # Formula: priority = (impact × 0.4) + (confidence × 0.35) + ((100 - effort) × 0.25)
    # Pre-computed expected values:
    expected_scores = {
        "audit": round(90 * 0.4 + 85 * 0.35 + (100 - 40) * 0.25, 2),        # 36 + 29.75 + 15 = 80.75
        "reduce_position": round(70 * 0.4 + 95 * 0.35 + (100 - 10) * 0.25, 2),  # 28 + 33.25 + 22.5 = 83.75
        "nebula_research": round(75 * 0.4 + 90 * 0.35 + (100 - 20) * 0.25, 2),  # 30 + 31.5 + 20 = 81.5
        "stop_loss": round(65 * 0.4 + 80 * 0.35 + (100 - 15) * 0.25, 2),        # 26 + 28 + 21.25 = 75.25
    }
    # 80.75, 83.75, 81.5, 75.25

    scores_found = []
    formula_scores_correct = 0
    for score_val in expected_scores.values():
        # Look for the numeric value in content (allow minor rounding: ±0.5)
        pattern = str(score_val).replace(".", r"\.")
        found_exact = bool(re.search(pattern, content))
        # Also check for rounded integer
        found_int = bool(re.search(r'\b' + str(int(round(score_val))) + r'\b', content))
        # Check for values within ±1
        for delta in [x * 0.1 for x in range(-5, 6)]:
            candidate = round(score_val + delta, 1)
            if str(candidate) in content or str(int(candidate)) in content:
                found_exact = True
                break
        if found_exact or found_int:
            formula_scores_correct += 1
            scores_found.append(score_val)

    formula_applied = formula_scores_correct >= 2  # At least 2 of 4 correct scores present
    checks.append({
        "name": "priority_formula_correctly_applied",
        "passed": formula_applied,
        "detail": (
            f"Expected scores: {list(expected_scores.values())}. "
            f"Found {formula_scores_correct}/4 correct computed scores in output. "
            f"Scores found: {scores_found}"
        )
    })
    if formula_applied:
        total_score += 2.0
    elif formula_scores_correct == 1:
        total_score += 0.5

    # CHECK 7: HistorianAnalyst specifically present (triggered by historical lessons rule)
    historian_present = any(p in content_lower for p in ["historiananalyst", "historian analyst", "historian", "📚"])
    historian_present = historian_present or "📚" in content
    checks.append({
        "name": "historian_analyst_present_for_historical_lessons",
        "passed": historian_present,
        "detail": f"HistorianAnalyst found: {historian_present} (mandatory per SKILL.md: '有历史教训的领域 → 必须含 HistorianAnalyst')"
    })
    if historian_present:
        total_score += 0.5

    # CHECK 8: Genuine disagreement (at least two roles must express opposing sentiments)
    # Heuristic: look for negative/cautionary language alongside positive language
    has_caution = bool(re.search(r'do not|don\'t|avoid|risk|danger|warning|caution|halt|stop|wait|no|against|concern|worried|skepti|红旗|风险|谨慎|反对|不建议', content_lower))
    has_positive = bool(re.search(r'opportunit|potential|upside|benefit|grow|profit|proceed|yes|favor|support|recommend|建议|机会|收益|潜力', content_lower))
    genuine_disagreement = has_caution and has_positive
    checks.append({
        "name": "genuine_disagreement_between_roles",
        "passed": genuine_disagreement,
        "detail": f"Cautionary language: {has_caution}, Positive language: {has_positive}"
    })
    if genuine_disagreement:
        total_score += 0.5

    # CHECK 9: Pre-trade mandatory trio present (RiskGuardian, FinanceAnalyst, SkepticalOperator)
    pretrade_trio = (
        roles_found.get("RiskGuardian", False) and
        roles_found.get("FinanceAnalyst", False) and
        roles_found.get("SkepticalOperator", False)
    )
    checks.append({
        "name": "pre_trade_mandatory_trio_present",
        "passed": pretrade_trio,
        "detail": f"pre_trade trio (RiskGuardian + FinanceAnalyst + SkepticalOperator): {pretrade_trio}"
    })
    if pretrade_trio:
        total_score += 0.5

    # Normalize score to 0-10
    final_score = min(round(total_score, 2), 10.0)
    passed = final_score >= 6.0 and formula_applied and two_rounds and consensus_present

    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))