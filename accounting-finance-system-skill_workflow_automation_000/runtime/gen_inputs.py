import os
import json
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "internal/finance/sap",
    "internal/finance/legacy",
    "internal/it/integrations",
    "internal/hr",
    "docs/archive/2023",
    "docs/archive/2024",
    "docs/templates",
    "output",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────
distractors = {
    "internal/finance/sap/ap_period_notes_2024Q4.txt": textwrap.dedent("""\
        Period-end AP notes Q4 2024
        - Ensure all GR/IR clearing done before day 3
        - Run F.13 for clearing
        - Check FBL1N for open items
        """),
    "internal/finance/sap/sap_transaction_codes_cheatsheet.csv": textwrap.dedent("""\
        TCode,Description
        FB60,Enter Vendor Invoice
        FBL1N,Vendor Line Items
        F.13,Automatic Clearing
        F110,Payment Run
        """),
    "internal/finance/legacy/old_ap_process.docx.bak": "BINARY_STUB_NOT_VALID",
    "internal/finance/legacy/reconciliation_steps_draft.txt": textwrap.dedent("""\
        DRAFT - incomplete - do not use
        1. Pull aging report
        2. Cross reference to GL
        3. ???
        """),
    "internal/it/integrations/sap_idoc_config.xml": textwrap.dedent("""\
        <?xml version="1.0"?>
        <IDOCConfig><Partner>VENDOR_001</Partner><MessageType>INVOIC</MessageType></IDOCConfig>
        """),
    "internal/it/integrations/middleware_log_sample.log": textwrap.dedent("""\
        2024-11-01 08:12:33 INFO  IDOC 000001234 posted successfully
        2024-11-01 08:15:01 ERROR IDOC 000001235 failed: duplicate invoice check
        """),
    "internal/hr/employee_roles_finance.csv": textwrap.dedent("""\
        Employee,Role,System_Access
        Jane Doe,AP Specialist,SAP S4HANA Cloud - AP
        John Smith,GL Accountant,SAP S4HANA Cloud - GL
        Alice Brown,Finance Manager,SAP S4HANA Cloud - Full
        """),
    "docs/archive/2023/ap_close_checklist_2023.md": textwrap.dedent("""\
        # AP Close Checklist 2023
        - [ ] Post all vendor invoices
        - [ ] Clear GR/IR accounts
        - [ ] Reconcile vendor subledger to GL
        - [ ] Obtain manager sign-off
        """),
    "docs/archive/2024/ap_close_checklist_2024.md": textwrap.dedent("""\
        # AP Close Checklist 2024
        - [ ] Post all vendor invoices (deadline: day 2)
        - [ ] Clear GR/IR accounts (FB60 + F.13)
        - [ ] Run vendor balance confirmation
        - [ ] Reconcile vendor subledger to GL (FBL1N vs. FS10N)
        - [ ] Obtain controller sign-off
        """),
    "docs/templates/blank_memo.txt": textwrap.dedent("""\
        TO:
        FROM:
        DATE:
        RE:

        [body]
        """),
    "docs/templates/qa_template_old.txt": textwrap.dedent("""\
        Q: [question]
        A: [answer]
        """),
}

for rel_path, content in distractors.items():
    fpath = WORKSPACE / rel_path
    fpath.write_text(content, encoding="utf-8")

# ── reference files (skill machinery) ──────────────────────────────────────
(WORKSPACE / "references/clarification-question-bank.md").write_text(textwrap.dedent("""\
    # Clarification Question Bank

    Ask only the questions needed to remove decision risk. Do not ask all questions by default.

    ## System Identity

    - What system and exact version/edition are you using?
    - Is this production, sandbox, or test environment?
    - Are there customizations, add-ons, or integrations that affect this workflow?

    ## Business Objective

    - What exact outcome do you need (create, post, reverse, reconcile, report, close)?
    - What deadline or period are you working under?
    - What is the impact if this is not resolved today?

    ## Process Scope

    - Which module/process is involved (AP, AR, GL, fixed assets, billing, close, reporting)?
    - What is the current step where the issue occurs?
    - What have you already tried?

    ## Security And Permissions

    - What role/profile are you using?
    - Are there any permission errors or missing menu/actions?
    - Can an admin grant temporary access if needed?

    ## Data Context

    - Which company/entity, ledger, book, or business unit is affected?
    - Which transaction type and volume are involved?
    - Is there sample data or a transaction ID to reproduce the issue?

    ## Configuration Context

    - Are there accounting period locks, workflow approvals, or posting controls enabled?
    - Are there relevant setup options already enabled/disabled?
    - Is this a one-time case or standard recurring process?

    ## Output Preference

    - Confirm output format: `quick memo` or `simple q-and-a`.
    - Confirm required detail level: short operational steps or deeper explanation.
"""), encoding="utf-8")

(WORKSPACE / "references/source-priority.md").write_text(textwrap.dedent("""\
    # Source Priority And Evidence Rules

    Use sources in this order whenever available.

    ## Priority Order

    1. Official vendor documentation and release notes (highest trust)
    2. Official vendor knowledge base and support articles
    3. Major implementation partner or consultant publications (Big 4 and known system integrators)
    4. Reputable practitioner resources and community posts (supporting context only)

    ## Rules

    - Prefer version-specific guidance over generic guidance.
    - Prefer newer guidance when process behavior changed across versions.
    - Do not rely on a single non-official source for final recommendations.
    - Label assumptions when documentation does not fully resolve the scenario.

    ## Citation Minimum

    For each cited source, capture:

    - Source title
    - Publisher/author
    - URL
    - Published or updated date when available
    - Accessed date

    ## Contradictions

    If sources conflict:

    - Prioritize official vendor guidance.
    - Document the conflict briefly.
    - Recommend the lowest-risk path and include fallback steps.
"""), encoding="utf-8")

(WORKSPACE / "references/report-json-schema.md").write_text(textwrap.dedent("""\
    # Report JSON Schema

    Use this schema to build the input for `scripts/build_system_guidance_docx.py`.

    ## Required Fields

    - `question` (string): User question or task objective.
    - `sources` (array): At least one source object.
    - `recommended_steps` (array): At least one recommended action.

    ## Optional Top-Level Fields

    - `title` (string)
    - `prepared_for` (string)
    - `prepared_by` (string)
    - `date` (string)
    - `analysis_summary` (string)
    - `assumptions` (array of strings)
    - `validation_checks` (array of strings)
    - `risks_open_items` (array of strings)
    - `open_questions` (array of strings)
    - `system_context` (object)
    - `clarifications` (array)

    ## Source Object

    - `title` (string)
    - `publisher` (string)
    - `url` (string)
    - `published_or_updated` (string)
    - `accessed` (string)
    - `type` (string, example: `official-doc`, `consultant-article`)

    ## Recommended Step Object

    Each step may be either a string or object.

    Object form:

    - `step` (string) or `action` (string)
    - `rationale` (string, optional)
    - `source_refs` (array, optional): Reference numbers aligned to source order (1-based)

    ## Clarification Item

    Each item may be either a string or object.

    Object form:

    - `question` (string)
    - `answer` (string)

    ## Minimal Example

    See [example_report_input.json](example_report_input.json).
"""), encoding="utf-8")

(WORKSPACE / "references/example_report_input.json").write_text(json.dumps({
    "title": "NetSuite AP Workflow Guidance",
    "prepared_for": "Finance Operations",
    "prepared_by": "Codex",
    "date": "2026-03-07",
    "question": "How do we create and approve a recurring vendor bill in NetSuite?",
    "system_context": {
        "system": "NetSuite",
        "version": "2025.2",
        "module": "Accounts Payable",
        "environment": "Production",
        "role": "AP Specialist"
    },
    "clarifications": [
        {"question": "Do you use approval routing?", "answer": "Yes, manager approval is required above $5,000."},
        {"question": "Is recurring billing enabled?", "answer": "Yes, memorized transactions are enabled."}
    ],
    "analysis_summary": "Use memorized transactions for recurring bills and apply approval routing rules before posting.",
    "assumptions": [
        "Role has permission to create memorized vendor bills.",
        "Approval workflow is active for AP transactions."
    ],
    "recommended_steps": [
        {
            "step": "Navigate to Transactions > Payables > Enter Bills and create a baseline vendor bill template.",
            "rationale": "A complete template ensures recurring entries inherit coding and approvals.",
            "source_refs": [1]
        },
        {
            "step": "Save the bill as a memorized transaction with schedule settings.",
            "rationale": "Schedule drives automatic recurring bill creation.",
            "source_refs": [1, 2]
        },
        {
            "step": "Submit generated bills through approval routing before posting.",
            "rationale": "Posting control prevents unauthorized expense recognition.",
            "source_refs": [2]
        }
    ],
    "validation_checks": [
        "Confirm recurring bill appears on scheduled date.",
        "Confirm approval status moves to Approved before posting.",
        "Confirm GL impact matches the template account mapping."
    ],
    "risks_open_items": [
        "Permission gaps can block memorized transaction setup.",
        "Workflow thresholds may reroute approvals unexpectedly."
    ],
    "sources": [
        {
            "title": "Creating Vendor Bills",
            "publisher": "Oracle NetSuite Help Center",
            "url": "https://docs.oracle.com/en/cloud/saas/netsuite",
            "published_or_updated": "2025-10-01",
            "accessed": "2026-03-07",
            "type": "official-doc"
        },
        {
            "title": "Accounts Payable Workflow Configuration",
            "publisher": "Oracle NetSuite Help Center",
            "url": "https://docs.oracle.com/en/cloud/saas/netsuite",
            "published_or_updated": "2025-09-15",
            "accessed": "2026-03-07",
            "type": "official-doc"
        }
    ],
    "open_questions": [
        "Should bills under $5,000 bypass manager approval?"
    ]
}, indent=2), encoding="utf-8")

# ── the real build script ───────────────────────────────────────────────────
(WORKSPACE / "scripts/build_system_guidance_docx.py").write_text(textwrap.dedent('''\
    #!/usr/bin/env python3
    """
    Build a DOCX system-guidance document from a structured JSON input.
    Usage:
        python scripts/build_system_guidance_docx.py \\
            --input-json <path/to/analysis.json> \\
            --output-docx <path/to/output.docx> \\
            --format <memo|q-and-a>
    """
    import argparse
    import json
    import sys
    from pathlib import Path

    try:
        from docx import Document
        from docx.shared import Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError:
        print("ERROR: python-docx is not installed. Run: pip install python-docx", file=sys.stderr)
        sys.exit(1)

    VALID_FORMATS = {"memo", "q-and-a"}

    def heading(doc, text, level=1):
        p = doc.add_heading(text, level=level)
        return p

    def body(doc, text):
        doc.add_paragraph(str(text))

    def build_memo(doc, data):
        heading(doc, data.get("title", "System Guidance Memo"), level=1)

        meta_lines = []
        if data.get("prepared_for"):
            meta_lines.append(f"Prepared for: {data[\'prepared_for\']}")
        if data.get("prepared_by"):
            meta_lines.append(f"Prepared by: {data[\'prepared_by\']}")
        if data.get("date"):
            meta_lines.append(f"Date: {data[\'date\']}")
        for line in meta_lines:
            body(doc, line)

        heading(doc, "Request Summary", level=2)
        body(doc, data.get("question", ""))

        ctx = data.get("system_context", {})
        if ctx:
            heading(doc, "System Context", level=2)
            for k, v in ctx.items():
                body(doc, f"{k.replace(\'_\', \' \').title()}: {v}")

        clarifications = data.get("clarifications", [])
        if clarifications:
            heading(doc, "Clarifications & Assumptions", level=2)
            for item in clarifications:
                if isinstance(item, dict):
                    body(doc, f"Q: {item.get(\'question\', \'\')}  |  A: {item.get(\'answer\', \'\')}")
                else:
                    body(doc, str(item))

        assumptions = data.get("assumptions", [])
        if assumptions:
            heading(doc, "Assumptions", level=2)
            for a in assumptions:
                doc.add_paragraph(str(a), style="List Bullet")

        if data.get("analysis_summary"):
            heading(doc, "Analysis Summary", level=2)
            body(doc, data["analysis_summary"])

        steps = data.get("recommended_steps", [])
        if steps:
            heading(doc, "Recommended Steps", level=2)
            for i, s in enumerate(steps, 1):
                if isinstance(s, dict):
                    step_text = s.get("step") or s.get("action", "")
                    rationale = s.get("rationale", "")
                    refs = s.get("source_refs", [])
                    ref_str = f" [Sources: {refs}]" if refs else ""
                    doc.add_paragraph(f"{i}. {step_text}{ref_str}", style="List Number")
                    if rationale:
                        body(doc, f"   Rationale: {rationale}")
                else:
                    doc.add_paragraph(f"{i}. {s}", style="List Number")

        checks = data.get("validation_checks", [])
        if checks:
            heading(doc, "Validation Checks", level=2)
            for c in checks:
                doc.add_paragraph(str(c), style="List Bullet")

        risks = data.get("risks_open_items", [])
        if risks:
            heading(doc, "Risks & Open Items", level=2)
            for r in risks:
                doc.add_paragraph(str(r), style="List Bullet")

        sources = data.get("sources", [])
        if sources:
            heading(doc, "Sources", level=2)
            for i, src in enumerate(sources, 1):
                if isinstance(src, dict):
                    parts = [f"[{i}] {src.get(\'title\', \'Untitled\')}"]
                    if src.get("publisher"):
                        parts.append(f"Publisher: {src[\'publisher\']}")
                    if src.get("url"):
                        parts.append(f"URL: {src[\'url\']}")
                    if src.get("published_or_updated"):
                        parts.append(f"Updated: {src[\'published_or_updated\']}")
                    if src.get("accessed"):
                        parts.append(f"Accessed: {src[\'accessed\']}")
                    if src.get("type"):
                        parts.append(f"Type: {src[\'type\']}")
                    body(doc, "  |  ".join(parts))
                else:
                    body(doc, str(src))

        open_q = data.get("open_questions", [])
        if open_q:
            heading(doc, "Open Questions", level=2)
            for q in open_q:
                doc.add_paragraph(str(q), style="List Bullet")

    def build_qa(doc, data):
        heading(doc, data.get("title", "System Guidance Q&A"), level=1)

        meta_lines = []
        if data.get("prepared_for"):
            meta_lines.append(f"Prepared for: {data[\'prepared_for\']}")
        if data.get("prepared_by"):
            meta_lines.append(f"Prepared by: {data[\'prepared_by\']}")
        if data.get("date"):
            meta_lines.append(f"Date: {data[\'date\']}")
        for line in meta_lines:
            body(doc, line)

        heading(doc, "Question", level=2)
        body(doc, data.get("question", ""))

        ctx = data.get("system_context", {})
        if ctx:
            heading(doc, "System Context", level=2)
            for k, v in ctx.items():
                body(doc, f"{k.replace(\'_\', \' \').title()}: {v}")

        clarifications = data.get("clarifications", [])
        if clarifications:
            heading(doc, "Clarifications", level=2)
            for item in clarifications:
                if isinstance(item, dict):
                    heading(doc, f"Q: {item.get(\'question\', \'\')}", level=3)
                    body(doc, f"A: {item.get(\'answer\', \'\')}")
                else:
                    body(doc, str(item))

        assumptions = data.get("assumptions", [])
        if assumptions:
            heading(doc, "Assumptions", level=2)
            for a in assumptions:
                doc.add_paragraph(str(a), style="List Bullet")

        steps = data.get("recommended_steps", [])
        if steps:
            heading(doc, "Answer: Recommended Actions", level=2)
            for i, s in enumerate(steps, 1):
                if isinstance(s, dict):
                    step_text = s.get("step") or s.get("action", "")
                    rationale = s.get("rationale", "")
                    refs = s.get("source_refs", [])
                    ref_str = f" [Sources: {refs}]" if refs else ""
                    doc.add_paragraph(f"{i}. {step_text}{ref_str}", style="List Number")
                    if rationale:
                        body(doc, f"   Rationale: {rationale}")
                else:
                    doc.add_paragraph(f"{i}. {s}", style="List Number")

        checks = data.get("validation_checks", [])
        if checks:
            heading(doc, "How To Confirm Success", level=2)
            for c in checks:
                doc.add_paragraph(str(c), style="List Bullet")

        risks = data.get("risks_open_items", [])
        if risks:
            heading(doc, "Risks & Open Items", level=2)
            for r in risks:
                doc.add_paragraph(str(r), style="List Bullet")

        sources = data.get("sources", [])
        if sources:
            heading(doc, "Sources", level=2)
            for i, src in enumerate(sources, 1):
                if isinstance(src, dict):
                    parts = [f"[{i}] {src.get(\'title\', \'Untitled\')}"]
                    if src.get("publisher"):
                        parts.append(f"Publisher: {src[\'publisher\']}")
                    if src.get("url"):
                        parts.append(f"URL: {src[\'url\']}")
                    if src.get("published_or_updated"):
                        parts.append(f"Updated: {src[\'published_or_updated\']}")
                    if src.get("accessed"):
                        parts.append(f"Accessed: {src[\'accessed\']}")
                    if src.get("type"):
                        parts.append(f"Type: {src[\'type\']}")
                    body(doc, "  |  ".join(parts))
                else:
                    body(doc, str(src))

        open_q = data.get("open_questions", [])
        if open_q:
            heading(doc, "Open Questions", level=2)
            for q in open_q:
                doc.add_paragraph(str(q), style="List Bullet")

    def main():
        parser = argparse.ArgumentParser(description="Build system guidance DOCX")
        parser.add_argument("--input-json", required=True, help="Path to input JSON file")
        parser.add_argument("--output-docx", required=True, help="Path for output DOCX file")
        parser.add_argument("--format", required=True, choices=list(VALID_FORMATS),
                            help="Document format: memo or q-and-a")
        args = parser.parse_args()

        input_path = Path(args.input_json)
        if not input_path.exists():
            print(f"ERROR: Input JSON not found: {input_path}", file=sys.stderr)
            sys.exit(1)

        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate required fields
        errors = []
        if not data.get("question"):
            errors.append("Missing required field: question")
        if not data.get("sources"):
            errors.append("Missing required field: sources (must have at least one entry)")
        if not data.get("recommended_steps"):
            errors.append("Missing required field: recommended_steps (must have at least one entry)")
        if errors:
            for e in errors:
                print(f"VALIDATION ERROR: {e}", file=sys.stderr)
            sys.exit(1)

        output_path = Path(args.output_docx)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = Document()
        fmt = args.format  # already validated to be "memo" or "q-and-a"
        if fmt == "memo":
            build_memo(doc, data)
        elif fmt == "q-and-a":
            build_qa(doc, data)

        doc.save(str(output_path))
        print(f"SUCCESS: Document saved to {output_path}")

    if __name__ == "__main__":
        main()
'''), encoding="utf-8")

print("Workspace scaffolded successfully.")
print(f"Files created under: {WORKSPACE}")