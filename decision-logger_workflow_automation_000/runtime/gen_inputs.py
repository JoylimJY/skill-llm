import os
import random
import textwrap
from pathlib import Path

random.seed(42)

BASE = Path("/workspace")

# ── directory skeleton ───────────────────────────────────────────────
dirs = [
    "memory/board-meetings/archive/2024",
    "memory/board-meetings/archive/2025",
    "memory/stakeholder-updates",
    "memory/hr-records",
    "scripts",
    "templates",
    "config",
    "reports/Q1-2026",
    "reports/Q2-2026",
    "docs/regulatory",
    "docs/ip",
]
for d in dirs:
    (BASE / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────
distractor_files = {
    "config/app_config.yaml": "env: production\nlog_level: INFO\ndb_host: localhost\n",
    "config/feature_flags.json": '{"enable_new_dashboard": false, "beta_api": true}\n',
    "docs/regulatory/fda_submission_checklist.md": "# FDA 510(k) Checklist\n- [ ] Predicate device identified\n- [ ] Performance testing complete\n",
    "docs/ip/patent_filing_log.csv": "patent_id,status,filed_date\nUS2024-001,pending,2024-03-12\nUS2024-002,granted,2024-09-01\n",
    "reports/Q1-2026/financial_summary.md": "# Q1 2026 Financial Summary\nRevenue: $2.1M\nBurn rate: $480K/mo\n",
    "reports/Q2-2026/pipeline_status.md": "# Q2 2026 Pipeline\n- Phase 2 trial: on track\n- Companion Dx: delayed 6 weeks\n",
    "memory/stakeholder-updates/2026-04-15-investor-update.md": "# Investor Update April 2026\nKey message: Series B milestone hit.\n",
    "memory/hr-records/headcount_plan_2026.md": "# Headcount Plan 2026\nEngineering: +4\nClinical: +2\n",
    "scripts/meeting_scheduler.py": "#!/usr/bin/env python3\n# Placeholder scheduler\nprint('No meetings scheduled')\n",
    "templates/agenda_template.md": "# Board Meeting Agenda\n1. Opening\n2. Financial Review\n3. Strategic Items\n4. AOB\n",
    "templates/stakeholder-report.md": "# Stakeholder Report Template\n**Date:** \n**Author:** \n",
    "memory/board-meetings/archive/2024/2024-09-10-raw.md": textwrap.dedent("""\
        # Board Meeting Raw Transcript — 2024-09-10
        ## Agenda: Series A Fundraising Strategy
        Phase 2 contributions: ...archived content...
        Phase 3 critique: ...archived content...
        """),
    "memory/board-meetings/archive/2025/2025-01-22-raw.md": textwrap.dedent("""\
        # Board Meeting Raw Transcript — 2025-01-22
        ## Agenda: Clinical Trial Site Selection
        Phase 2 contributions: ...archived content...
        """),
}

for rel_path, content in distractor_files.items():
    p = BASE / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

# ── decision_tracker.py (the real CLI tool) ──────────────────────────
decision_tracker_code = textwrap.dedent('''\
    #!/usr/bin/env python3
    """
    decision_tracker.py  —  CLI for the Decision Logger skill.

    Parses memory/board-meetings/decisions.md and provides:
      --demo        : print a formatted sample
      --summary     : overview of all decisions + overdue count
      --overdue     : list action items past their due date
      --conflicts   : scan for topic contradictions & DO_NOT_RESURFACE
      --owner NAME  : filter decisions by owner
      --search KW   : search decisions by keyword
    """
    import argparse
    import re
    import sys
    from datetime import date, datetime
    from pathlib import Path

    DECISIONS_FILE = Path("memory/board-meetings/decisions.md")

    # ── helpers ──────────────────────────────────────────────────────────
    def _load_raw() -> str:
        if not DECISIONS_FILE.exists():
            return ""
        return DECISIONS_FILE.read_text(encoding="utf-8")

    def _parse_blocks(raw: str) -> list[dict]:
        """Split decisions.md into per-decision dicts."""
        blocks = re.split(r"(?=^## \\[\\d{4}-\\d{2}-\\d{2}\\])", raw, flags=re.MULTILINE)
        entries = []
        for block in blocks:
            block = block.strip()
            if not block.startswith("## ["):
                continue
            m = re.match(r"## \\[(\\d{4}-\\d{2}-\\d{2})\\] — (.+)", block)
            if not m:
                continue
            entry = {
                "date": m.group(1),
                "title": m.group(2).strip(),
                "raw": block,
            }
            # owner
            om = re.search(r"\\*\\*Owner:\\*\\*\\s*(.+)", block)
            entry["owner"] = om.group(1).strip() if om else ""
            # deadline
            dm = re.search(r"\\*\\*Deadline:\\*\\*\\s*(\\d{4}-\\d{2}-\\d{2})", block)
            entry["deadline"] = dm.group(1) if dm else ""
            # superseded_by
            sm = re.search(r"\\*\\*Superseded by:\\*\\*\\s*(.+)", block)
            entry["superseded_by"] = sm.group(1).strip() if sm else ""
            # action items
            actions = re.findall(
                r"- \\[( |x)\\] (.+?) — Owner: (.+?) — Due: (\\d{4}-\\d{2}-\\d{2})",
                block,
            )
            entry["actions"] = actions  # (status, text, owner, due)
            # rejected proposals
            rejected = re.findall(r"- (.+?) — .+?\\[DO_NOT_RESURFACE\\]", block)
            entry["rejected_dnr"] = rejected
            entries.append(entry)
        return entries

    def _is_active(e: dict) -> bool:
        return not e["superseded_by"] or e["superseded_by"].strip() in ("", "N/A")

    def cmd_summary():
        raw = _load_raw()
        if not raw:
            print("No decisions logged yet.")
            return
        entries = _parse_blocks(raw)
        active = [e for e in entries if _is_active(e)]
        today = date.today()
        overdue_count = 0
        for e in active:
            for status, text, owner, due_str in e["actions"]:
                if status == " ":
                    try:
                        due = datetime.strptime(due_str, "%Y-%m-%d").date()
                        if due < today:
                            overdue_count += 1
                    except ValueError:
                        pass
        print(f"Total decisions : {len(entries)}")
        print(f"Active decisions: {len(active)}")
        print(f"Overdue actions : {overdue_count}")
        print()
        for e in entries[-10:]:
            status = "SUPERSEDED" if not _is_active(e) else "active"
            print(f"  [{e[\'date\']}] {e[\'title\']} — {status} — Owner: {e[\'owner\']}")

    def cmd_overdue():
        raw = _load_raw()
        entries = _parse_blocks(raw)
        today = date.today()
        found = False
        for e in entries:
            if not _is_active(e):
                continue
            for status, text, owner, due_str in e["actions"]:
                if status == " ":
                    try:
                        due = datetime.strptime(due_str, "%Y-%m-%d").date()
                        if due < today:
                            print(f"OVERDUE [{e[\'date\']}] {text} — Owner: {owner} — Due: {due_str}")
                            found = True
                    except ValueError:
                        pass
        if not found:
            print("No overdue action items.")

    def cmd_conflicts():
        raw = _load_raw()
        entries = _parse_blocks(raw)
        active = [e for e in entries if _is_active(e)]
        issues = []
        # DO_NOT_RESURFACE: collect all rejected proposals across ALL entries
        all_dnr: list[tuple[str, str]] = []
        for e in entries:
            for prop in e["rejected_dnr"]:
                all_dnr.append((e["date"], prop.strip().lower()))
        # Check active decisions\' titles against DNR list (simple keyword overlap)
        for e in active:
            title_lower = e["title"].lower()
            decision_line = ""
            dm = re.search(r"\\*\\*Decision:\\*\\*\\s*(.+)", e["raw"])
            if dm:
                decision_line = dm.group(1).strip().lower()
            for dnr_date, dnr_prop in all_dnr:
                if dnr_date == e["date"]:
                    continue  # same entry
                # crude overlap: share >=2 words
                words_dnr = set(re.findall(r"\\w{4,}", dnr_prop))
                words_dec = set(re.findall(r"\\w{4,}", title_lower + " " + decision_line))
                if len(words_dnr & words_dec) >= 2:
                    issues.append(
                        f"🚫 DO_NOT_RESURFACE: \'{dnr_prop}\' was rejected on {dnr_date} "
                        f"but appears related to active entry [{e[\'date\']}] \'{e[\'title\']}\'"
                    )
        # Topic contradictions: same owner, different deadline on similar title
        for i, a in enumerate(active):
            for b in active[i + 1:]:
                wa = set(re.findall(r"\\w{4,}", a["title"].lower()))
                wb = set(re.findall(r"\\w{4,}", b["title"].lower()))
                if len(wa & wb) >= 2 and a["owner"] == b["owner"] and a["owner"]:
                    issues.append(
                        f"⚠️  TOPIC CONFLICT: [{a[\'date\']}] \'{a[\'title\']}\' vs "
                        f"[{b[\'date\']}] \'{b[\'title\']}\' — same owner \'{a[\'owner\']}\'"
                    )
        if issues:
            for i in issues:
                print(i)
        else:
            print("No conflicts detected.")

    def cmd_owner(name: str):
        raw = _load_raw()
        entries = _parse_blocks(raw)
        results = [e for e in entries if name.lower() in e["owner"].lower()]
        if not results:
            print(f"No decisions found for owner: {name}")
            return
        for e in results:
            print(f"[{e[\'date\']}] {e[\'title\']} — Owner: {e[\'owner\']}")

    def cmd_search(keyword: str):
        raw = _load_raw()
        entries = _parse_blocks(raw)
        kw = keyword.lower()
        results = [e for e in entries if kw in e["raw"].lower()]
        if not results:
            print(f"No decisions found matching: {keyword}")
            return
        for e in results:
            print(f"[{e[\'date\']}] {e[\'title\']} — Owner: {e[\'owner\']}")

    def cmd_demo():
        demo = """
    ## [2026-01-15] — Q1 Pricing Strategy

    **Decision:** Adopt flat-fee annual licensing at $24,000/year for hospital networks.
    **Owner:** CMO
    **Deadline:** 2026-02-01
    **Review:** 2026-04-01
    **Rationale:** Predictable revenue; easier procurement for hospital CFOs.

    **User Override:** Blank

    **Rejected:**
    - Tiered subscription by test volume — too complex for procurement teams [DO_NOT_RESURFACE]

    **Action Items:**
    - [ ] Draft pricing sheet — Owner: CMO — Due: 2026-01-25 — Review: 2026-02-15

    **Supersedes:** N/A
    **Superseded by:**
    **Raw transcript:** memory/board-meetings/2026-01-15-raw.md
    """.strip()
        print(demo)

    def main():
        parser = argparse.ArgumentParser(description="Decision Tracker CLI")
        parser.add_argument("--demo", action="store_true")
        parser.add_argument("--summary", action="store_true")
        parser.add_argument("--overdue", action="store_true")
        parser.add_argument("--conflicts", action="store_true")
        parser.add_argument("--owner", type=str, default="")
        parser.add_argument("--search", type=str, default="")
        args = parser.parse_args()

        if args.demo:
            cmd_demo()
        elif args.summary:
            cmd_summary()
        elif args.overdue:
            cmd_overdue()
        elif args.conflicts:
            cmd_conflicts()
        elif args.owner:
            cmd_owner(args.owner)
        elif args.search:
            cmd_search(args.search)
        else:
            parser.print_help()

    if __name__ == "__main__":
        main()
''')

(BASE / "scripts/decision_tracker.py").write_text(decision_tracker_code)

# ── existing decisions.md (Layer 2) with a DO_NOT_RESURFACE trap ─────
decisions_md = textwrap.dedent("""\
    # Approved Decisions — NovaDx Biotech

    ---

    ## [2025-11-04] — R&D Budget Allocation FY2026

    **Decision:** Allocate $3.2M to R&D for FY2026, with 60% directed to Phase 3 clinical trials and 40% to companion diagnostics development.
    **Owner:** CTO
    **Deadline:** 2025-12-01
    **Review:** 2026-03-01
    **Rationale:** Phase 3 data is gate-critical for FDA submission; companion Dx opens adjacent revenue stream.

    **User Override:** Blank

    **Rejected:**
    - Shift 70% to companion Dx and defer Phase 3 — too risky given FDA timeline [DO_NOT_RESURFACE]

    **Action Items:**
    - [x] Issue budget allocation memo — Owner: CTO — Completed: 2025-11-10 — Result: Memo distributed to all dept heads
    - [ ] Set up quarterly R&D review cadence — Owner: CTO — Due: 2025-12-15 — Review: 2026-01-15

    **Supersedes:** N/A
    **Superseded by:**
    **Raw transcript:** memory/board-meetings/2025-11-04-raw.md

    ---

    ## [2026-01-15] — Diagnostic Kit Pricing Model

    **Decision:** Adopt flat-fee annual licensing at $24,000/year per hospital network site.
    **Owner:** CMO
    **Deadline:** 2026-02-15
    **Review:** 2026-04-15
    **Rationale:** Predictable revenue; simplifies hospital procurement cycles and avoids usage-tracking overhead.

    **User Override:** Blank

    **Rejected:**
    - Tiered subscription pricing based on test volume — procurement teams flagged complexity; finance flagged unpredictable cash flow [DO_NOT_RESURFACE]
    - Per-test transactional model — rejected due to revenue volatility [DO_NOT_RESURFACE]

    **Action Items:**
    - [x] Draft hospital pricing sheet — Owner: CMO — Completed: 2026-02-10 — Result: Pricing sheet approved and sent to 3 pilot accounts
    - [ ] Negotiate pilot contracts with 2 regional hospital networks — Owner: CMO — Due: 2026-03-01 — Review: 2026-04-01

    **Supersedes:** N/A
    **Superseded by:**
    **Raw transcript:** memory/board-meetings/2026-01-15-raw.md

    ---

    ## [2026-02-20] — Clinical Trial Partnership — Phase 3

    **Decision:** Partner exclusively with Meridian Clinical Research for Phase 3 multi-site trial coordination.
    **Owner:** CMO
    **Deadline:** 2026-03-15
    **Review:** 2026-06-01
    **Rationale:** Meridian has 12 qualified sites pre-approved by FDA; reduces site activation time by ~3 months.

    **User Override:** Founder added exclusivity clause not recommended by agents — founder believes exclusivity protects IP during trial.

    **Rejected:**
    - Multi-CRO approach with TrialBridge + Meridian — coordination overhead too high for current team size [DO_NOT_RESURFACE]

    **Action Items:**
    - [ ] Execute MSA with Meridian — Owner: CMO — Due: 2026-03-15 — Review: 2026-04-15
    - [ ] Brief internal clinical team on Meridian protocols — Owner: CTO — Due: 2026-03-20 — Review: 2026-04-20

    **Supersedes:** N/A
    **Superseded by:**
    **Raw transcript:** memory/board-meetings/2026-02-20-raw.md

    ---
""")

(BASE / "memory/board-meetings/decisions.md").write_text(decisions_md)

# ── templates/decision-entry.md ──────────────────────────────────────
decision_entry_template = textwrap.dedent("""\
    ## [YYYY-MM-DD] — [AGENDA ITEM TITLE]

    **Decision:** [One clear statement of what was decided.]
    **Owner:** [One person or role — accountable for execution.]
    **Deadline:** [YYYY-MM-DD]
    **Review:** [YYYY-MM-DD]
    **Rationale:** [Why this over alternatives. 1-2 sentences.]

    **User Override:** [If founder changed agent recommendation — what and why. Blank if not applicable.]

    **Rejected:**
    - [Proposal] — [reason] [DO_NOT_RESURFACE]

    **Action Items:**
    - [ ] [Action] — Owner: [name] — Due: [YYYY-MM-DD] — Review: [YYYY-MM-DD]

    **Supersedes:** [DATE of previous decision on same topic, if any]
    **Superseded by:** [Filled in retroactively if overridden later]
    **Raw transcript:** memory/board-meetings/[DATE]-raw.md
""")

(BASE / "templates/decision-entry.md").write_text(decision_entry_template)

# ── meeting outcome brief (the "raw" input data the agent receives) ──
# This file is NOT the Layer 1 raw transcript. It's the input brief.
meeting_brief = textwrap.dedent("""\
    # NovaDx Board Meeting — 2026-04-28
    ## Internal Brief for Decision Logging

    Meeting concluded 16:45. Founder approved all three items below.

    ---

    ### Agenda Item 1: R&D Budget Reallocation — Mid-Year Adjustment

    **Outcome:** The board approved a mid-year reallocation: increase companion diagnostics budget from 40% to 55% of R&D spend (reducing Phase 3 allocation to 45%). This supersedes the November 2025 R&D budget decision.
    **Owner:** CTO
    **Deadline:** 2026-05-15
    **Review:** 2026-07-01
    **Rationale:** Companion Dx partnership opportunity with Roche emerged; board assessed it as higher near-term ROI than accelerating Phase 3 by one quarter.
    **Founder override:** None — founder agreed with agent recommendation.
    **Rejected proposals (not to be revisited):**
    - Pause Phase 3 entirely and redirect 100% to companion Dx — too high regulatory risk
    **Action items:**
    - Revise internal R&D budget model — Owner: CTO — Due: 2026-05-10 — Review: 2026-06-10
    - Notify Meridian of potential Phase 3 timeline shift — Owner: CMO — Due: 2026-05-15 — Review: 2026-06-15

    ---

    ### Agenda Item 2: Diagnostic Kit Pricing Model — Market Expansion Revision

    **Outcome:** The board approved moving to a tiered pricing structure: Tier 1 ($18,000/year, up to 500 tests/month), Tier 2 ($28,000/year, up to 1,500 tests/month), Tier 3 ($42,000/year, unlimited). This supersedes the January 2026 flat-fee pricing decision.
    **Owner:** CMO
    **Deadline:** 2026-05-30
    **Review:** 2026-07-30
    **Rationale:** Three large hospital networks indicated the flat fee was too high for low-volume sites; tiered model opens the mid-market without cannibalizing premium accounts.
    **Founder override:** Founder explicitly approved re-opening tiered pricing despite prior rejection, citing new market data from the Q1 pilot. Founder said: "The market data from the pilot changes everything — reopen tiered pricing from 2026-01-15."
    **Rejected proposals (not to be revisited):**
    - Per-test transactional model (reconfirmed rejection) — still too volatile
    **Action items:**
    - Redesign pricing sheet with three tiers — Owner: CMO — Due: 2026-05-20 — Review: 2026-06-20
    - Update pilot contracts with Tier 1 pricing — Owner: CMO — Due: 2026-05-25 — Review: 2026-06-25
    - Brief sales team on new pricing tiers — Owner: CSO — Due: 2026-05-30 — Review: 2026-06-30

    ---

    ### Agenda Item 3: Series B Extension Round

    **Outcome:** Approved opening a $5M extension to the Series B at same valuation cap, targeting 2 existing investors (Helion Ventures, Apex Bio Fund).
    **Owner:** CEO
    **Deadline:** 2026-06-30
    **Review:** 2026-08-01
    **Rationale:** 14-month runway extension to reach Phase 3 data readout without down-round risk; existing investors pre-committed in principle.
    **Founder override:** Founder reduced target from $8M (agent recommended) to $5M to avoid dilution — founder said "We only need the runway, not a war chest."
    **Rejected proposals (not to be revisited):**
    - Full Series C at higher valuation — too early, insufficient clinical data
    - Bridge loan structure — rejected, unfavorable terms
    **Action items:**
    - Draft term sheet for Series B extension — Owner: CEO — Due: 2026-05-15 — Review: 2026-06-15
    - Schedule diligence calls with Helion and Apex — Owner: CEO — Due: 2026-05-10 — Review: 2026-06-01

    ---

    Phase 3/4 agent contributions and debate available separately. Founder has given approval to proceed with logging.
""")

(BASE / "memory/board-meetings/2026-04-28-meeting-brief.md").write_text(meeting_brief)

print("Workspace generated successfully.")
print("Files created:")
import subprocess
subprocess.run(["find", "/workspace", "-type", "f", "-not", "-path", "*/__pycache__/*"], 
               capture_output=False)