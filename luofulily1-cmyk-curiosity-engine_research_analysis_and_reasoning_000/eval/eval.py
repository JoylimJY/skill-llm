import sys
import json
import re
from pathlib import Path

def run_eval(workspace_dir: str):
    checks = []
    total_score = 0.0
    weight_sum = 0.0

    workspace = Path(workspace_dir)

    # ── Locate the output file ──────────────────────────────────────────────
    candidates = list(workspace.rglob("curiosity_report.md"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found {len(candidates)} file(s) named curiosity_report.md" if file_found
                  else "No file named curiosity_report.md found anywhere in workspace"
    })
    if not file_found:
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = candidates[0]
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── CHECK 1: Header marker ──────────────────────────────────────────────
    # SKILL.md: "🔍 Curiosity Engine Active" header required for full loop
    header_present = "Curiosity Engine Active" in content
    checks.append({
        "name": "header_curiosity_engine_active",
        "passed": header_present,
        "detail": "'🔍 Curiosity Engine Active' header found" if header_present
                  else "Missing '🔍 Curiosity Engine Active' header — required by full OODA-C loop format"
    })

    # ── CHECK 2: Confidence rating with change notation ──────────────────────
    # SKILL.md: "📊 Confidence: X/10 (changed from Y/10 after exploration)"
    confidence_pattern = re.search(
        r'📊\s*Confidence\s*:\s*(\d+(?:\.\d+)?)\s*/\s*10.*changed from\s*(\d+(?:\.\d+)?)\s*/\s*10',
        content, re.IGNORECASE
    )
    confidence_ok = confidence_pattern is not None
    checks.append({
        "name": "confidence_rating_with_change_notation",
        "passed": confidence_ok,
        "detail": f"Found confidence with change: {confidence_pattern.group(0)[:60]}" if confidence_ok
                  else "Missing '📊 Confidence: X/10 (changed from Y/10 after exploration)' — "
                       "agent must show confidence change after exploration"
    })

    # ── CHECK 3: Surprises section ──────────────────────────────────────────
    # SKILL.md: "🔍 Surprises: [anything unexpected you found]"
    surprises_present = bool(re.search(r'🔍\s*Surprises?\s*:', content, re.IGNORECASE))
    checks.append({
        "name": "surprises_section_present",
        "passed": surprises_present,
        "detail": "🔍 Surprises section found" if surprises_present
                  else "Missing '🔍 Surprises:' section in output format"
    })

    # ── CHECK 4: Open Threads section with numbered items ───────────────────
    # SKILL.md: "🧵 Open Threads:\n  1. [question]\n  2. [question]"
    open_threads_header = bool(re.search(r'🧵\s*Open Threads?\s*:', content, re.IGNORECASE))
    open_threads_numbered = len(re.findall(r'^\s*\d+\.\s+.+', content, re.MULTILINE)) >= 2
    open_threads_ok = open_threads_header and open_threads_numbered
    checks.append({
        "name": "open_threads_with_numbered_items",
        "passed": open_threads_ok,
        "detail": f"🧵 Open Threads header: {open_threads_header}, numbered items (≥2): {open_threads_numbered}"
    })

    # ── CHECK 5: Anomaly addressed (Klebsiella 2021 spike) ─────────────────
    klebsiella_anomaly = bool(re.search(
        r'(?:klebsiella|klebs).{0,80}(?:2021|spike|34|anomal|outlier|contamin)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "klebsiella_2021_anomaly_addressed",
        "passed": klebsiella_anomaly,
        "detail": "Klebsiella 2021 resistance spike anomaly discussed" if klebsiella_anomaly
                  else "Agent failed to identify or discuss the major Klebsiella 2021 spike (34.7% vs ~9% trend)"
    })

    # ── CHECK 6: Data gap addressed (2020 E. coli missing) ──────────────────
    gap_addressed = bool(re.search(
        r'(?:2020).{0,100}(?:e\.?\s*coli|missing|gap|incomplete|absent|unavailabl)',
        content, re.IGNORECASE
    ) or re.search(
        r'(?:e\.?\s*coli).{0,100}(?:2020).{0,100}(?:miss|gap|incomplet)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "data_gap_2020_ecoli_identified",
        "passed": gap_addressed,
        "detail": "2020 E. coli data gap identified" if gap_addressed
                  else "Agent failed to identify missing 2020 E. coli data — a key knowledge gap"
    })

    # ── CHECK 7: MRSA contradiction addressed ──────────────────────────────
    mrsa_conflict = bool(re.search(
        r'(?:mrsa|methicillin).{0,150}(?:conflict|contradic|inconsist|discrepanc|two|dual|both|differ|prelim|revis)',
        content, re.IGNORECASE
    ) or re.search(
        r'(?:26\.8|31\.2).{0,80}(?:mrsa|methicillin|2022)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "mrsa_2022_contradiction_addressed",
        "passed": mrsa_conflict,
        "detail": "MRSA 2022 duplicate/conflicting entries addressed" if mrsa_conflict
                  else "Agent failed to flag conflicting MRSA 2022 resistance rates (26.8% vs 31.2%)"
    })

    # ── CHECK 8: Knowledge gap categorization (✅/⚠️/❌ or KNOWN/ASSUMED/UNKNOWN) ─
    # SKILL.md Protocol C: categorize as KNOWN, ASSUMED, UNKNOWN
    gap_map_found = bool(re.search(
        r'(?:✅|KNOWN|confirmed|verified).{0,50}(?:⚠️|ASSUM|believe|unverif|uncertain)',
        content, re.IGNORECASE | re.DOTALL
    ) or re.search(
        r'(?:⚠️\s*ASSUM|ASSUMED\s*:|assumed:)',
        content, re.IGNORECASE
    ) or re.search(
        r'(?:❌\s*UNKNOWN|UNKNOWN\s*:|unknown:)',
        content, re.IGNORECASE
    ) or (
        # At least two of the three categories present
        sum([
            bool(re.search(r'(?:✅|KNOWN\b)', content, re.IGNORECASE)),
            bool(re.search(r'(?:⚠️|ASSUMED\b)', content, re.IGNORECASE)),
            bool(re.search(r'(?:❌|UNKNOWN\b)', content, re.IGNORECASE)),
        ]) >= 2
    ))
    checks.append({
        "name": "knowledge_gap_categorization_protocol_c",
        "passed": gap_map_found,
        "detail": "Knowledge gap map (KNOWN/ASSUMED/UNKNOWN or ✅/⚠️/❌) present" if gap_map_found
                  else "Missing Protocol C gap categorization — no KNOWN/ASSUMED/UNKNOWN or ✅/⚠️/❌ categories found"
    })

    # ── CHECK 9: Self-questioning (Protocol A — at least 2 distinct questions raised) ─
    # Agent should generate investigative questions beyond what was asked
    question_count = len(re.findall(r'\?', content))
    self_ask_ok = question_count >= 3
    checks.append({
        "name": "self_questioning_protocol_a",
        "passed": self_ask_ok,
        "detail": f"Found {question_count} questions in report (need ≥3 for Protocol A evidence)"
    })

    # ── CHECK 10: Anti-pattern — no loop mechanics reporting ────────────────
    # SKILL.md: "Reporting the loop mechanics — show results, not the process"
    # Agent should NOT write phrases like "Now I will run Protocol A" or "Step 3: DOUBT"
    loop_mechanics_leaked = bool(re.search(
        r'(?:Protocol [ABC]|OODA-C|Step \d.*(?:OBSERVE|ORIENT|DOUBT|ACT|CURIOSE)|'
        r'running.*loop|Now I will.*(?:observe|orient|doubt)|'
        r'(?:OBSERVE|ORIENT|DOUBT|ACT|CURIOSE)\s*(?:—|:|\n))',
        content, re.IGNORECASE
    ))
    no_mechanics_leak = not loop_mechanics_leaked
    checks.append({
        "name": "no_loop_mechanics_exposed",
        "passed": no_mechanics_leak,
        "detail": "Report correctly hides loop mechanics (shows results not process)" if no_mechanics_leak
                  else "ANTI-PATTERN VIOLATION: Agent exposed internal loop mechanics (Protocol A/B/C labels, OODA-C steps) in output"
    })

    # ── CHECK 11: Assumptions challenged (Protocol B) ───────────────────────
    assumption_challenge = bool(re.search(
        r'(?:assum.{0,30}(?:wrong|incorrect|challenged|if not|however|but|alternatively|what if)|'
        r'what if.{0,60}(?:wrong|not|instead|different)|'
        r'alternatively.{0,60}(?:could|might|may|explain))',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "assumption_challenging_protocol_b",
        "passed": assumption_challenge,
        "detail": "Evidence of assumption challenging found" if assumption_challenge
                  else "No evidence of Protocol B assumption challenging (what if X is wrong?)"
    })

    # ── CHECK 12: Surprise explicitly flagged ──────────────────────────────
    # SKILL.md Surprise Detector: flag counter-intuitive findings with 🔍
    surprise_flagged = bool(re.search(
        r'(?:🔍.{0,200}(?:unexpect|surpris|counter|contradict|anomal|unusual)|'
        r'(?:unexpect|surpris|counter-intuitive|striking).{0,100})',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "surprise_explicitly_flagged",
        "passed": surprise_flagged,
        "detail": "Surprise/unexpected finding explicitly flagged" if surprise_flagged
                  else "No surprise explicitly flagged — agent should note counter-intuitive findings"
    })

    # ── CHECK 13: Report substantive length (not a stub) ───────────────────
    word_count = len(content.split())
    substantial = word_count >= 300
    checks.append({
        "name": "report_substantive_length",
        "passed": substantial,
        "detail": f"Word count: {word_count} ({'sufficient' if substantial else 'too short — stub response'})"
    })

    # ── Scoring ─────────────────────────────────────────────────────────────
    weights = {
        "output_file_exists":                    1.0,
        "header_curiosity_engine_active":         1.5,
        "confidence_rating_with_change_notation": 2.0,  # highest-weight proprietary trap
        "surprises_section_present":              1.5,
        "open_threads_with_numbered_items":       1.5,
        "klebsiella_2021_anomaly_addressed":      2.0,
        "data_gap_2020_ecoli_identified":         1.5,
        "mrsa_2022_contradiction_addressed":      1.5,
        "knowledge_gap_categorization_protocol_c":2.0,  # proprietary trap
        "self_questioning_protocol_a":            1.0,
        "no_loop_mechanics_exposed":              2.0,  # anti-pattern trap
        "assumption_challenging_protocol_b":      1.5,
        "surprise_explicitly_flagged":            1.0,
        "report_substantive_length":              0.5,
    }

    earned = 0.0
    total_w = sum(weights.values())
    for check in checks:
        w = weights.get(check["name"], 1.0)
        if check["passed"]:
            earned += w

    score = round(earned / total_w, 4)
    passed = score >= 0.70

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))