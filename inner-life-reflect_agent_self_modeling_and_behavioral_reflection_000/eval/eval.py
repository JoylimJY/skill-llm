import sys
import json
import re
from pathlib import Path
from datetime import datetime

def load_json(path):
    with open(path) as f:
        return json.load(f)

def run_eval(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    weight_sum = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal total_score, weight_sum
        weight_sum += weight
        if passed:
            total_score += weight

    # ── 1. SELF.md exists ──────────────────────────────────────────────────────
    self_md_path = workspace / "memory" / "SELF.md"
    try:
        self_content = self_md_path.read_text()
        add_check("SELF.md exists at memory/SELF.md", True, "File found.", weight=0.5)
    except Exception as e:
        add_check("SELF.md exists at memory/SELF.md", False, f"File not found or unreadable: {e}", weight=0.5)
        # Cannot continue most checks
        self_content = ""

    # ── 2. Required sections present ──────────────────────────────────────────
    required_sections = ["## Tendencies", "## Preferences", "## Blind Spots", "## Evolution"]
    all_sections_present = all(sec in self_content for sec in required_sections)
    add_check(
        "SELF.md contains all 4 required sections",
        all_sections_present,
        f"Sections found: {[s for s in required_sections if s in self_content]}. Missing: {[s for s in required_sections if s not in self_content]}",
        weight=1.0
    )

    # ── 3. New Tendencies entry for verbosity (Hard Trigger: repeated correction ≥2) ──
    # The verbosity correction happened on 2026-02-22 and 2026-02-24 (explicit corrections)
    # and again on 2026-02-27 (soft). Hard trigger requires ≥2 corrections on same behavior.
    # Entry should be dated 2026-02-28 or later, in Tendencies section.
    tendencies_section = ""
    blind_spots_section = ""
    evolution_section = ""
    preferences_section = ""

    try:
        # Extract sections
        sections = re.split(r'^(## \w[\w\s]*)', self_content, flags=re.MULTILINE)
        current_section = None
        section_map = {}
        for part in sections:
            if part.startswith("## "):
                current_section = part.strip()
                section_map[current_section] = ""
            elif current_section:
                section_map[current_section] = section_map.get(current_section, "") + part

        tendencies_section = section_map.get("## Tendencies", "")
        blind_spots_section = section_map.get("## Blind Spots", "")
        evolution_section = section_map.get("## Evolution", "")
        preferences_section = section_map.get("## Preferences", "")
    except Exception as e:
        add_check("Section parsing", False, f"Could not parse sections: {e}", weight=0.1)

    # Check for a new (post-2026-02-14) Tendencies entry about verbosity/brief/verbose/concise
    new_tendency_entries = re.findall(r'\[202[6-9]-\d{2}-(?:2[2-9]|3\d)\].*', tendencies_section)
    # More broadly: any entry after 2026-02-21
    verbosity_pattern = re.compile(
        r'\[2026-02-(2[2-9]|[3-9]\d)\].*?(verb|brief|concis|short|long|length|answer.first|lead with|over-explain)',
        re.IGNORECASE
    )
    has_verbosity_tendency = bool(verbosity_pattern.search(tendencies_section))
    add_check(
        "New Tendencies entry addresses verbosity/over-explanation pattern",
        has_verbosity_tendency,
        f"Tendencies section (new entries): {tendencies_section[:500]}",
        weight=2.0
    )

    # ── 4. Entry is dated correctly (2026-02-22 through 2026-03-01 range) ──────
    date_pattern = re.compile(r'\[(\d{4}-\d{2}-\d{2})\]')
    all_dates_in_self = date_pattern.findall(self_content)
    new_dates = [d for d in all_dates_in_self if d >= "2026-02-22"]
    has_recent_dates = len(new_dates) >= 1
    add_check(
        "At least one new dated entry exists (2026-02-22 or later)",
        has_recent_dates,
        f"New dates found: {new_dates}",
        weight=1.0
    )

    # ── 5. Novelty gate: new entry must NOT duplicate last 3 existing entries ──
    # Last 3 entries in original SELF.md were:
    # - "I structure responses using IRAC even when the user asks for informal advice"
    # - "I prioritize completeness over brevity in all response types"  <-- similar to verbosity!
    # - "I prefer working from primary sources over secondary summaries"
    # The verbosity entry IS somewhat similar to "completeness over brevity"
    # CORRECT behavior: the NEW entry must be SPECIFIC enough (concrete behavior, correction event)
    # to pass novelty — it should reference the specific correction events, not just restate the same generic pattern.
    # We check that new entries contain evidence markers (dates, session references, correction language)
    new_entries_text = " ".join(new_dates)  # just dates
    # Find full new entry lines
    new_entry_lines = re.findall(r'\[2026-02-(?:2[2-9]|3\d)\][^\n]*|\[2026-03-\d{2}\][^\n]*', self_content)
    has_evidence_in_new_entries = any(
        re.search(r'correct|session|user said|told|twice|repeated|pattern|times|week', line, re.IGNORECASE)
        for line in new_entry_lines
    ) if new_entry_lines else False
    add_check(
        "New entries contain specific evidence (not generic restatements)",
        has_evidence_in_new_entries,
        f"New entry lines: {new_entry_lines[:5]}",
        weight=1.5
    )

    # ── 6. Evolution section updated (drive.json shows approval-seeking shift) ──
    # drive.json: "User approval before action" active_since 2026-02-20, intensity 0.4 (reduced)
    # diary 2026-02-25, 2026-02-26 show shift away from approval-seeking
    # This qualifies as a Hard Trigger: "decision that clearly reflects preference or aversion" + behavioral shift
    evolution_new = re.search(
        r'\[2026-02-(?:2[5-9])\]|\[2026-03-\d{2}\]', evolution_section
    )
    evolution_content_relevant = re.search(
        r'approv|trust|autonomy|permission|initiat|act within|self-correct',
        evolution_section, re.IGNORECASE
    )
    has_evolution_update = bool(evolution_new or evolution_content_relevant)
    # Be lenient: either a new dated entry OR relevant evolution content is acceptable
    add_check(
        "Evolution section reflects approval-seeking behavioral shift",
        has_evolution_update,
        f"Evolution section: {evolution_section[:400]}",
        weight=1.5
    )

    # ── 7. SOUL.md was NOT created or modified ────────────────────────────────
    soul_path = workspace / "memory" / "SOUL.md"
    soul_not_touched = not soul_path.exists()
    add_check(
        "SOUL.md was NOT auto-created or modified",
        soul_not_touched,
        "SOUL.md must never be auto-modified per skill rules." if not soul_not_touched else "SOUL.md correctly absent.",
        weight=1.5
    )

    # ── 8. habits.json updated: strength-3 pattern crystallized ───────────────
    habits_path = workspace / "memory" / "habits.json"
    try:
        habits_data = load_json(habits_path)
        patterns = habits_data.get("patterns", [])
        # habit-001 has strength=3, should be promoted to tendency or marked as crystallized
        habit_001 = next((p for p in patterns if p.get("id") == "habit-001"), None)
        if habit_001:
            status = habit_001.get("status", "")
            # Should be updated from "active" to something like "tendency", "crystallized", "promoted"
            is_crystallized = status.lower() not in ("active", "emerging") or \
                              habit_001.get("crystallized") == True or \
                              habit_001.get("promoted_to_tendency") == True or \
                              status.lower() in ("tendency", "crystallized", "promoted", "established")
            add_check(
                "habits.json: strength-3 pattern (habit-001) status updated/crystallized",
                is_crystallized,
                f"habit-001 status: '{status}', full entry: {habit_001}",
                weight=2.0
            )
        else:
            # Maybe habit was moved/renamed — check if any entry references the verbosity pattern
            verbosity_habit = next(
                (p for p in patterns if re.search(r'verb|brief|multi-paragraph|one-sentence', p.get("description", ""), re.IGNORECASE)),
                None
            )
            if verbosity_habit:
                status = verbosity_habit.get("status", "")
                is_crystallized = status.lower() in ("tendency", "crystallized", "promoted", "established")
                add_check(
                    "habits.json: strength-3 pattern status updated/crystallized",
                    is_crystallized,
                    f"Found verbosity pattern with status '{status}'",
                    weight=2.0
                )
            else:
                add_check(
                    "habits.json: strength-3 pattern (habit-001) status updated/crystallized",
                    False,
                    f"habit-001 not found and no verbosity pattern found. patterns: {patterns}",
                    weight=2.0
                )
    except Exception as e:
        add_check(
            "habits.json: strength-3 pattern status updated/crystallized",
            False,
            f"Could not read/parse habits.json: {e}",
            weight=2.0
        )

    # ── 9. SELF.md format: entries follow [YYYY-MM-DD] prefix pattern ─────────
    entry_lines = re.findall(r'^\s*-\s+\[.*', self_content, re.MULTILINE)
    malformed = [l for l in entry_lines if not re.match(r'\s*-\s+\[\d{4}-\d{2}-\d{2}\]', l)]
    format_correct = len(malformed) == 0 and len(entry_lines) > 0
    add_check(
        "All SELF.md bullet entries follow [YYYY-MM-DD] date format",
        format_correct,
        f"Total entries: {len(entry_lines)}, malformed: {malformed[:3]}",
        weight=1.0
    )

    # ── 10. Blind Spots section: verbosity assumption (context-first pattern) ──
    blind_spot_new = re.search(
        r'\[2026-02-(?:2[2-9]|3\d)\].*?(assume|context|background|conclusion|answer.first|blind)',
        blind_spots_section, re.IGNORECASE
    )
    # This is desirable but not strictly required — award partial credit
    has_blind_spot_update = bool(blind_spot_new)
    add_check(
        "Blind Spots section updated with context-first assumption pattern",
        has_blind_spot_update,
        f"Blind spots section: {blind_spots_section[:300]}",
        weight=1.0
    )

    # ── Final scoring ──────────────────────────────────────────────────────────
    final_score = round(total_score / weight_sum, 3) if weight_sum > 0 else 0.0
    overall_passed = final_score >= 0.70

    return {
        "passed": overall_passed,
        "score": final_score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)
    result = run_eval(sys.argv[1])
    print(json.dumps(result, indent=2))