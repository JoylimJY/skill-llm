import os
import json
import random
import textwrap

random.seed(42)

BASE = "/workspace"

# ── Skill package layout (mirrors what SKILL.md expects) ──────────────────────
skill_root = os.path.join(BASE, "20260318", "scientific-skills", "Evidence Insight", "key-takeaways")
scripts_dir = os.path.join(skill_root, "scripts")
refs_dir    = os.path.join(skill_root, "references", "examples")
os.makedirs(scripts_dir, exist_ok=True)
os.makedirs(refs_dir,    exist_ok=True)

# ── scripts/main.py  ─────────────────────────────────────────────────────────
main_py = r'''#!/usr/bin/env python3
"""Key Takeaways extractor – packaged skill entry point."""
import argparse, json, os, sys, re
from pathlib import Path

# ── tiny NLP helpers ─────────────────────────────────────────────────────────
_ACTION_PATTERNS = re.compile(
    r"\b(action|todo|follow[ -]up|assigned to|please|must|should|will|deadline|by \w+day)\b",
    re.IGNORECASE,
)
_DECISION_PATTERNS = re.compile(
    r"\b(decided|approved|agreed|confirmed|resolved|chosen|selected|rejected|will proceed)\b",
    re.IGNORECASE,
)


def _sentences(text: str):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if len(s.strip()) > 15]


def _score(sentence: str) -> float:
    """Very small heuristic relevance score."""
    s = sentence.lower()
    score = 0.0
    for kw in ("revenue", "growth", "launch", "delay", "budget", "hire", "risk",
                "strategy", "partner", "milestone", "objective", "result", "plan",
                "increase", "decrease", "critical", "priority", "deadline", "new"):
        if kw in s:
            score += 1.0
    score += len(s) * 0.002          # slight length bonus
    return score


class Key_Takeaways:                  # noqa: N801  (name required by SKILL.md)
    """Extracts and presents key takeaways from text documents."""

    def process(self, source, *, style="default", max_points=7, audience="general"):
        """Return a structured takeaway dict."""
        if isinstance(source, (str, Path)):
            path = Path(source)
            if path.exists():
                text = path.read_text(encoding="utf-8", errors="replace")
            else:
                text = str(source)
        else:
            text = str(source)

        audience_note = f"[audience: {audience}]" if audience != "general" else ""
        sentences = _sentences(text)

        actions   = [s for s in sentences if _ACTION_PATTERNS.search(s)]
        decisions = [s for s in sentences if _DECISION_PATTERNS.search(s)]
        others    = [s for s in sentences
                     if s not in actions and s not in decisions]

        # rank and cap key points
        ranked = sorted(others, key=_score, reverse=True)
        key_pts = ranked[:max_points]
        if audience_note:
            key_pts = [f"{p} {audience_note}" for p in key_pts]

        if style == "executive":
            body = " ".join(key_pts[:3]) if key_pts else text[:200]
            return {
                "summary": body.strip(),
                "action_items": actions[:5],
                "decisions": decisions[:5],
            }

        return {
            "key_points":   key_pts,
            "action_items": actions[:5],
            "decisions":    decisions[:5],
        }

    def export(self, result, *, format="json", output_path=None):  # noqa: A002
        if format == "json":
            out = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            lines = []
            for k, v in result.items():
                lines.append(f"=== {k.upper()} ===")
                if isinstance(v, list):
                    lines.extend(f"- {item}" for item in v)
                else:
                    lines.append(str(v))
            out = "\n".join(lines)

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_text(out, encoding="utf-8")
        return out


# ── CLI ───────────────────────────────────────────────────────────────────────
def _load_config(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _process_one(tool, src_path: Path, cfg: dict, out_path: Path):
    style    = cfg.get("style", "default")
    max_pts  = int(cfg.get("max_points", 7))
    audience = cfg.get("audience", "general")
    fmt      = cfg.get("format", "json")

    result = tool.process(src_path, style=style, max_points=max_pts, audience=audience)

    if fmt == "json":
        out_path = out_path.with_suffix(".json")
    else:
        out_path = out_path.with_suffix(".txt")

    tool.export(result, format=fmt, output_path=str(out_path))
    return out_path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Key Takeaways extractor")
    parser.add_argument("--input",   "-i", help="Single input file")
    parser.add_argument("--output",  "-o", help="Output file path")
    parser.add_argument("--batch",   "-b", help="Input directory for batch mode")
    parser.add_argument("--config",  "-c", help="JSON config file")
    parser.add_argument("--style",         default="default",
                        choices=["default", "executive"])
    parser.add_argument("--max-points",    type=int, default=7)
    parser.add_argument("--audience",      default="general")
    parser.add_argument("--format",        default="json",
                        choices=["json", "txt"])
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)

    tool = Key_Takeaways()

    # config file overrides CLI defaults
    cfg: dict = {}
    if args.config:
        cfg = _load_config(args.config)

    # CLI flags override config file
    cfg.setdefault("style",      args.style)
    cfg.setdefault("max_points", args.max_points)
    cfg.setdefault("audience",   args.audience)
    cfg.setdefault("format",     args.format)

    if args.style      != "default":   cfg["style"]      = args.style
    if args.max_points != 7:           cfg["max_points"]  = args.max_points
    if args.audience   != "general":   cfg["audience"]    = args.audience
    if args.format     != "json":      cfg["format"]      = args.format

    # ── batch mode ────────────────────────────────────────────────────────────
    if args.batch:
        in_dir  = Path(args.batch)
        out_dir = Path(args.output) if args.output else Path("output_dir")
        out_dir.mkdir(parents=True, exist_ok=True)

        errors = []
        for src in sorted(in_dir.glob("*.txt")):
            out_path = out_dir / src.stem
            try:
                final = _process_one(tool, src, cfg, out_path)
                if args.verbose:
                    print(f"OK  {src.name} -> {final.name}")
            except Exception as exc:         # noqa: BLE001
                msg = f"{src.name}: {exc}"
                errors.append(msg)
                if args.verbose:
                    print(f"ERR {msg}", file=sys.stderr)

        if errors:
            err_log = out_dir / "errors.log"
            err_log.write_text("\n".join(errors), encoding="utf-8")
            if args.verbose:
                print(f"{len(errors)} error(s) logged to {err_log}")
        return

    # ── single-file mode ──────────────────────────────────────────────────────
    if not args.input:
        parser.print_help()
        sys.exit(1)

    src_path = Path(args.input)
    if not src_path.exists():
        print(f"ERROR: input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    out_path = Path(args.output) if args.output else Path(src_path.stem + "_takeaways")
    _process_one(tool, src_path, cfg, out_path)
    if args.verbose:
        print(f"Done -> {out_path}")


if __name__ == "__main__":
    main()
'''

with open(os.path.join(scripts_dir, "main.py"), "w") as f:
    f.write(main_py)

# ── references/guide.md ──────────────────────────────────────────────────────
guide_md = textwrap.dedent("""\
    # Key Takeaways – Reference Guide

    ## Config File Format
    ```json
    {
      "style":      "default | executive",
      "max_points": 5,
      "audience":   "general | non-technical | technical",
      "format":     "json | txt"
    }
    ```

    ## Output Schema (default style)
    ```json
    {
      "key_points":   ["..."],
      "action_items": ["..."],
      "decisions":    ["..."]
    }
    ```

    ## Output Schema (executive style)
    ```json
    {
      "summary":      "...",
      "action_items": ["..."],
      "decisions":    ["..."]
    }
    ```
    """)
with open(os.path.join(refs_dir, "..", "guide.md"), "w") as f:
    f.write(guide_md)

# ── raw_docs/  (documents to be batch-processed) ─────────────────────────────
raw_docs = os.path.join(skill_root, "raw_docs")
os.makedirs(raw_docs, exist_ok=True)

docs = {
    "memo_q1_strategy.txt": textwrap.dedent("""\
        Q1 Strategy Briefing – Confidential

        Revenue for Q1 reached $4.2M, a 17% increase year-over-year.
        The new product line exceeded launch targets by 22% in pilot markets.
        Customer acquisition cost decreased by 11% following the digital campaign.
        Operational costs rose 8% due to supply-chain disruptions; mitigation plan approved.
        The board confirmed the expansion into APAC markets will proceed in Q2.
        Action: CFO to present revised budget to leadership by March 31.
        Action: Head of Sales must finalise regional partner agreements within 30 days.
        Decided: Headcount freeze lifted; hiring resumes for engineering and data roles.
        Agreed: External audit firm retained for full-year compliance review.
        Risk: Regulatory approval for new product in EU still pending.
    """),
    "memo_product_launch.txt": textwrap.dedent("""\
        Product Launch Update – Internal

        The flagship product is on track for a Q3 general availability release.
        Beta testing revealed three critical bugs; all resolved as of last sprint.
        Marketing campaign strategy approved for digital-first rollout.
        Partnership with two tier-one distributors confirmed for North America.
        New pricing strategy agreed upon after competitive analysis.
        Action: Engineering lead to deliver final QA sign-off by July 15.
        Action: Marketing team must submit campaign assets by July 1.
        Decided: Premium tier pricing set at $299/year; freemium tier retained.
        Supply chain confirmed adequate inventory for initial 50,000 units.
        Risk: Competitor product release expected same quarter.
    """),
    "memo_board_risk.txt": textwrap.dedent("""\
        Board Risk Assessment Summary

        Cyber-security posture upgraded; third-party pen-test passed with minor findings.
        ESG compliance report completed; carbon footprint reduced 14% vs prior year.
        Legal team confirmed all IP registrations are current across key jurisdictions.
        Three legacy systems identified for decommission; migration plan approved.
        Talent retention risk elevated; voluntary attrition at 18% – above benchmark.
        Action: HR to roll out retention bonus programme for top 15% performers by Q2.
        Action: CTO must present legacy migration timeline to board by next quarter.
        Confirmed: Insurance coverage renewed and expanded to include cyber liability.
        Resolved: Outstanding litigation with former vendor settled out of court.
        New data-centre lease signed; capacity increase of 40% available from June.
    """),
    "memo_partnership.txt": textwrap.dedent("""\
        Strategic Partnership Review

        Three partnership proposals evaluated; one selected for deep-dive due diligence.
        The proposed partner brings $12M in co-investment and access to 200k end-users.
        Synergy analysis projects a 25% increase in addressable market within 18 months.
        Legal review of term sheet is ongoing; NDA executed.
        Technology integration roadmap drafted; API compatibility confirmed.
        Action: BD Director to lead due diligence workstream starting next Monday.
        Action: Legal must return redlined term sheet within 10 business days.
        Agreed: Joint go-to-market strategy to be finalised before public announcement.
        Decision: No exclusivity clause to be included in final agreement.
        Risk: Partner has outstanding regulatory inquiry in one jurisdiction.
    """),
    "memo_hr_offsite.txt": textwrap.dedent("""\
        HR & People Offsite Notes

        Engagement survey results show overall score of 74/100, up 6 points.
        Learning & development budget increased by 20% for the fiscal year.
        New hybrid work policy effective from next month; three days in-office required.
        Leadership development programme launched for senior managers.
        Performance review cycle shifted from annual to bi-annual cadence.
        Action: HR Business Partners must communicate new policy to all teams by Friday.
        Action: L&D team to publish course catalogue by end of month.
        Decided: All director-level hires now require panel interviews with CEO.
        Confirmed: Mental health support contract renewed with expanded coverage.
        Risk: Policy change may increase voluntary exits in remote-heavy teams.
    """),
}

for fname, content in docs.items():
    with open(os.path.join(raw_docs, fname), "w") as f:
        f.write(content)

# ── distractor files (to test contextual awareness) ──────────────────────────
# Mimicking a realistic workspace with unrelated noise files
distractors = {
    os.path.join(BASE, "archive", "old_config.json"): '{"max_points": 99, "format": "txt"}',
    os.path.join(BASE, "archive", "legacy_summary.txt"): "Old summary – do not use.",
    os.path.join(BASE, "tmp", "scratch.md"): "# Scratch\nNotes go here.",
    os.path.join(BASE, "tmp", "config_draft.json"): '{"style": "executive", "audience": "technical"}',
    os.path.join(BASE, "data", "raw", "unrelated_report.csv"): "month,sales\nJan,100\nFeb,110",
    os.path.join(BASE, "data", "processed", "sales_agg.json"): '{"total": 210}',
    os.path.join(BASE, "logs", "run_20260101.log"): "INFO: start\nINFO: end",
    os.path.join(BASE, "logs", "run_20260201.log"): "INFO: start\nERROR: timeout\nINFO: end",
    os.path.join(BASE, "docs", "architecture.md"): "# Architecture\nSee diagrams.",
    os.path.join(BASE, "docs", "api_reference.md"): "# API Reference\nEndpoints listed here.",
    os.path.join(BASE, "configs", "prod.json"): '{"env": "prod", "debug": false}',
    os.path.join(BASE, "configs", "dev.json"): '{"env": "dev", "debug": true}',
}

for path, content in distractors.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Skill root: {skill_root}")
print(f"Raw docs  : {raw_docs}")