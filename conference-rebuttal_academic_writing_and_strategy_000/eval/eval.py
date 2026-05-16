import sys
import json
import re
from pathlib import Path

def load_rebuttal(workspace):
    candidates = list(Path(workspace).rglob("rebuttal.md"))
    if not candidates:
        return None, "rebuttal.md not found anywhere in workspace"
    # prefer root-level
    root = Path(workspace) / "rebuttal.md"
    if root.exists():
        return root.read_text(encoding="utf-8"), str(root)
    return candidates[0].read_text(encoding="utf-8"), str(candidates[0])

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace):
    checks = []
    content, path_info = load_rebuttal(workspace)

    if content is None:
        checks.append(check("file_exists", False, path_info))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(check("file_exists", True, f"Found at {path_info}"))
    content_lower = content.lower()

    # ── CHECK 1: Four-layer structure present ─────────────────────────────────
    # Must have: Overall/Opening, To AC, Reviewer-specific sections
    has_overall = bool(re.search(r'(overall|opening|dear reviewer|we are encouraged)', content_lower))
    has_ac = bool(re.search(r'(to\s+ac|area\s+chair|dear\s+ac|ac\s+summary|speed.?read|overview)', content_lower))
    has_r1 = bool(re.search(r'(to\s+r1|reviewer\s+1|dear\s+r1|response\s+to\s+r1)', content_lower))
    has_r2 = bool(re.search(r'(to\s+r2|reviewer\s+2|dear\s+r2|response\s+to\s+r2)', content_lower))
    has_r3 = bool(re.search(r'(to\s+r3|reviewer\s+3|dear\s+r3|response\s+to\s+r3)', content_lower))
    four_layer = has_overall and has_ac and has_r1 and has_r2 and has_r3
    checks.append(check("four_layer_architecture",
                         four_layer,
                         f"overall={has_overall}, to_ac={has_ac}, r1={has_r1}, r2={has_r2}, r3={has_r3}"))

    # ── CHECK 2: Reviewer ordering — R1 (Champion, score=7) before R3 (Adversary, score=3) ──
    r1_pos = content_lower.find("to r1") if "to r1" in content_lower else content_lower.find("reviewer 1")
    r3_pos = content_lower.find("to r3") if "to r3" in content_lower else content_lower.find("reviewer 3")
    # Also check "response to r1" style
    for pattern in [r'response to r1', r'dear r1', r'## r1', r'# r1']:
        m = re.search(pattern, content_lower)
        if m and (r1_pos < 0 or m.start() < r1_pos):
            r1_pos = m.start()
    for pattern in [r'response to r3', r'dear r3', r'## r3', r'# r3']:
        m = re.search(pattern, content_lower)
        if m and (r3_pos < 0 or m.start() < r3_pos):
            r3_pos = m.start()
    ordering_correct = (r1_pos >= 0 and r3_pos >= 0 and r1_pos < r3_pos)
    checks.append(check("reviewer_ordering_champion_first",
                         ordering_correct,
                         f"R1 position={r1_pos}, R3 position={r3_pos}. R1(champion,score=7) must appear before R3(adversary,score=3)"))

    # ── CHECK 3: Opening "borrow quotes" formula — positive quotes from each reviewer ──
    # R1 said "well motivated", R2 said "reasonable and clever", R3 said "conceptually elegant and practically impactful"
    opening_section = content[:2000]  # first ~2000 chars covers opening/overall
    opening_lower = opening_section.lower()
    has_r1_quote = bool(re.search(r'well.motivated|well motivated', opening_lower))
    has_r2_quote = bool(re.search(r'reasonable and clever|reasonable.*clever', opening_lower))
    has_r3_quote = bool(re.search(r'conceptually elegant|practically impactful', opening_lower))
    borrowed_quotes = has_r1_quote and has_r2_quote and has_r3_quote
    checks.append(check("opening_borrows_reviewer_quotes",
                         borrowed_quotes,
                         f"Opening must cite R1('well motivated'), R2('reasonable and clever'), R3('conceptually elegant/practically impactful'). Found: r1={has_r1_quote}, r2={has_r2_quote}, r3={has_r3_quote}"))

    # ── CHECK 4: Blockquote usage (> syntax) for reviewer text ───────────────
    blockquote_count = len(re.findall(r'^\s*>', content, re.MULTILINE))
    has_blockquotes = blockquote_count >= 3  # at least one per reviewer
    checks.append(check("blockquote_citations",
                         has_blockquotes,
                         f"Found {blockquote_count} blockquote lines (need ≥3, one per reviewer section)"))

    # ── CHECK 5: Five-step formula — "already updated" signals (not just promises) ──
    # Must say something like "updated in Section X / Lines Y-Z / Appendix" rather than "will add"
    already_signals = re.findall(
        r'(updated|added|included|incorporated|appended|now\s+appear|can\s+be\s+found).{0,60}(appendix|section|lines?|table)',
        content_lower)
    will_only = re.findall(r'we\s+will\s+(add|include|update|append)', content_lower)
    has_already = len(already_signals) >= 2
    checks.append(check("already_done_not_just_promises",
                         has_already,
                         f"Found {len(already_signals)} 'already updated' signals vs {len(will_only)} 'will add' promises. Need ≥2 'already done' references."))

    # ── CHECK 6: Precise quantification — overhead numbers ───────────────────
    # Should mention 2.2ms and/or <1% from the timing data
    has_ms = bool(re.search(r'2\.2\s*ms', content))
    has_pct = bool(re.search(r'<\s*1\s*%|less\s+than\s+1\s*%|<1%', content))
    has_quantification = has_ms or has_pct
    checks.append(check("precise_quantification",
                         has_quantification,
                         f"Must include precise timing data (2.2ms and/or <1%). Found: 2.2ms={has_ms}, <1%={has_pct}"))

    # ── CHECK 7: Merging shared concerns — R2 and R3 both ask about overhead ──
    # The rebuttal should have a unified response or cross-reference for the overhead question
    shared_overhead_merged = bool(re.search(
        r'(r2.*r3|r3.*r2|both.*reviewer|reviewer.*both).{0,200}(overhead|latency|wall.?clock)',
        content_lower, re.DOTALL))
    # Alternative: a single "Joint Response" or "Shared Concern" block
    joint_block = bool(re.search(r'(joint|shared|common|both).{0,30}(concern|question|response|weakness)',
                                  content_lower))
    merged = shared_overhead_merged or joint_block
    checks.append(check("merged_shared_concern_overhead",
                         merged,
                         f"R2-W1/Q1 and R3-W4/Q3 both ask about overhead — must be merged or cross-referenced. shared_ref={shared_overhead_merged}, joint_block={joint_block}"))

    # ── CHECK 8: Defending existing ablation (R3-W3 is a misunderstanding) ──
    # R3 claims no ablation on K exists, but Table 2 already has it; rebuttal must point to it
    has_ablation_defense = bool(re.search(
        r'(table\s*2|ablation.{0,50}(already|exist|included|present|section|lines))',
        content_lower))
    checks.append(check("defends_existing_ablation_r3w3",
                         has_ablation_defense,
                         "Must defend that kernel bank size ablation already exists in Table 2 (R3-W3 is a misunderstanding)"))

    # ── CHECK 9: AC summary letter has compressed per-issue format ────────────
    # Find AC section and check for list/bullet structure
    ac_match = re.search(r'(to\s+ac|area\s+chair|dear\s+ac|ac\s+summary)(.*?)(##|---|\Z)',
                          content, re.IGNORECASE | re.DOTALL)
    if ac_match:
        ac_section = ac_match.group(2)
        bullet_count = len(re.findall(r'^\s*[-*•]|\d+\.', ac_section, re.MULTILINE))
        ac_has_list = bullet_count >= 4  # enough bullets to cover the major concerns
        checks.append(check("ac_letter_compressed_list_format",
                             ac_has_list,
                             f"AC letter must use bullet/list format compressing all issues. Found {bullet_count} list items."))
    else:
        checks.append(check("ac_letter_compressed_list_format",
                             False,
                             "Could not locate AC letter section to verify list format"))

    # ── CHECK 10: Cross-reference between reviewers (alliance tactic) ─────────
    # R1 positively notes the paper is well-motivated; R2/R3 both question it
    # OR: R2 and R3 share overhead concern — cross-reference them
    cross_ref = bool(re.search(
        r'(as\s+(also\s+)?(noted|highlighted|mentioned|acknowledged|confirmed)\s+by\s+r[123]'
        r'|r[123]\s+(also|similarly)\s+(note|highlight|mention|acknowledge)'
        r'|both\s+r[123]\s+and\s+r[123])',
        content_lower))
    checks.append(check("cross_reviewer_referencing",
                         cross_ref,
                         "Must cross-reference reviewers (e.g., 'as also noted by R2 and R3') to create alliance/coalition effect"))

    # ── SCORING ───────────────────────────────────────────────────────────────
    weights = {
        "file_exists": 0.05,
        "four_layer_architecture": 0.15,
        "reviewer_ordering_champion_first": 0.10,
        "opening_borrows_reviewer_quotes": 0.15,
        "blockquote_citations": 0.05,
        "already_done_not_just_promises": 0.10,
        "precise_quantification": 0.10,
        "merged_shared_concern_overhead": 0.10,
        "defends_existing_ablation_r3w3": 0.10,
        "ac_letter_compressed_list_format": 0.05,
        "cross_reviewer_referencing": 0.05,
    }
    score = sum(weights.get(c["name"], 0) for c in checks if c["passed"])
    passed = score >= 0.70

    return {"passed": passed, "score": round(score, 3), "checks": checks}

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        result = run_eval(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": str(e)}]
        }
    print(json.dumps(result, indent=2))