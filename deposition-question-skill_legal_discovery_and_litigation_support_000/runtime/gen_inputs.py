#!/usr/bin/env python3
"""
Generates the sandbox workspace for the Relativity Deposition Question Builder task.
Creates:
  - A realistic directory structure with distractor files
  - PDFs that simulate Relativity productions (with document IDs in the bottom-right)
  - Some pages with TWO numeric IDs in the bottom-right (the proprietary trap)
  - scripts/extract_relativity_pages.py  (the real extraction tool)
  - references/deposition_output_template.md
"""

import os
import json
import random
import textwrap
from pathlib import Path

# ── deterministic seed ──────────────────────────────────────────────────────
random.seed(42)

WORKSPACE = Path("/workspace")

# ── helper: make dirs ────────────────────────────────────────────────────────
def mkdirs(*paths):
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)

# ── directory skeleton ───────────────────────────────────────────────────────
mkdirs(
    WORKSPACE / "productions" / "batch_001",
    WORKSPACE / "productions" / "batch_002",
    WORKSPACE / "productions" / "archive" / "old_exports",
    WORKSPACE / "scripts",
    WORKSPACE / "references",
    WORKSPACE / "case_notes",
    WORKSPACE / "pleadings",
    WORKSPACE / "correspondence",
    WORKSPACE / "expert_reports",
    WORKSPACE / "deposition_prep" / "prior_deps",
)

# ── distractor files ─────────────────────────────────────────────────────────
distractor_texts = {
    WORKSPACE / "case_notes" / "timeline_draft.txt":
        "Initial patient intake: 2022-01-15\nFirst billing cycle: 2022-02-01\nComplaint filed: 2023-06-30\n",
    WORKSPACE / "case_notes" / "witness_list.txt":
        "1. Dr. Harold Finch  2. Ms. Rita Caldwell  3. CFO John Mercer\n",
    WORKSPACE / "pleadings" / "complaint.txt":
        "Plaintiff alleges that defendant systematically upcoded procedures between 2021-2023.\n",
    WORKSPACE / "pleadings" / "answer.txt":
        "Defendant denies all allegations and asserts affirmative defenses.\n",
    WORKSPACE / "correspondence" / "meet_and_confer_2024-03.txt":
        "Parties discussed scope of production on March 12, 2024.\n",
    WORKSPACE / "correspondence" / "production_cover_letter.txt":
        "Enclosed please find Bates-numbered documents HLTH000001 through HLTH000350.\n",
    WORKSPACE / "expert_reports" / "billing_expert_draft.txt":
        "Preliminary opinion: Over 40% of CPT codes appear inconsistent with documented diagnoses.\n",
    WORKSPACE / "deposition_prep" / "prior_deps" / "finch_dep_summary.txt":
        "Witness claimed no knowledge of billing software configuration.\n",
    WORKSPACE / "deposition_prep" / "prior_deps" / "caldwell_dep_summary.txt":
        "Witness confirmed she approved all superbills before submission.\n",
    WORKSPACE / "productions" / "archive" / "old_exports" / "README_old.txt":
        "These exports are from the first production set and have been superseded.\n",
    WORKSPACE / "productions" / "archive" / "old_exports" / "manifest_v1.csv":
        "doc_id,page_count,custodian\n00001,3,Finch\n00002,2,Caldwell\n",
}

for path, content in distractor_texts.items():
    path.write_text(content)

# ── PDF generation using reportlab ──────────────────────────────────────────
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas as rl_canvas

W, H = LETTER  # 612 x 792

def make_pdf(filepath: Path, pages: list[dict]):
    """
    pages: list of dicts with keys:
      - body_text: str  (main content of the page)
      - bottom_right: str  (text placed in bottom-right corner, simulating Relativity stamp)
    """
    c = rl_canvas.Canvas(str(filepath), pagesize=LETTER)
    for page in pages:
        # body text
        text_obj = c.beginText(72, H - 72)
        text_obj.setFont("Helvetica", 10)
        for line in page["body_text"].splitlines():
            text_obj.textLine(line)
        c.drawText(text_obj)
        # bottom-right stamp (Relativity document ID area)
        c.setFont("Helvetica", 8)
        stamp = page["bottom_right"]
        c.drawRightString(W - 36, 36, stamp)
        c.showPage()
    c.save()

# ── Define PDFs with realistic legal/billing content ────────────────────────
#
# DOCUMENT IDs used (as they appear in bottom-right):
#   Single ID pages  → "HLTH 00089"  means doc_id = 89
#   Dual ID pages    → "HLTH 00142  HLTH 00089"  → agent must pick smaller = 89
#
# PDFs:
#   batch_001/billing_records_A.pdf  → doc IDs: 89 (pages 1-2), 142 (page 3 — single)
#   batch_001/billing_records_B.pdf  → doc IDs: 201 (pages 1-2 dual: 201 & 178 → pick 178), 201 page 3 single
#   batch_002/internal_memo.pdf      → doc IDs: 55 (single), 55+67 dual (pick 55), 67 single
#   batch_002/approval_chain.pdf     → doc IDs: 310 single, 310+289 dual (pick 289), 289 single

# ── PDF 1: billing_records_A.pdf ─────────────────────────────────────────────
pdf1_pages = [
    {
        "body_text": textwrap.dedent("""\
            PATIENT BILLING RECORD - ACCOUNT 77423
            Date of Service: 2022-03-10
            Provider: Dr. Harold Finch, MD
            CPT Code: 99215 - Office visit, high complexity
            Diagnosis: Z00.00 (Routine adult health exam)
            Charge: $450.00
            
            Supervisor signature: Rita Caldwell
            Notes: Patient seen for 10 minutes. Standard follow-up.
            CPT 99215 requires high medical decision making or 40+ min visit.
            Documented time does not support this billing level.
        """),
        "bottom_right": "HLTH 00089",
    },
    {
        "body_text": textwrap.dedent("""\
            PATIENT BILLING RECORD - ACCOUNT 77423 (continued)
            Addendum by Dr. Finch (added 2022-04-02):
            'Patient presented with multiple chronic conditions requiring
            extensive review of records and coordination of care.'
            This addendum was added 23 days after the date of service.
            Insurance reimbursement for 99215: $312.00
            
            Original chart note (2022-03-10): '10 min follow-up, no acute issues.'
        """),
        "bottom_right": "HLTH 00142  HLTH 00089",   # ← DUAL ID TRAP: pick 89
    },
    {
        "body_text": textwrap.dedent("""\
            SUPERBILL SUMMARY - BATCH MARCH 2022
            Prepared by: Rita Caldwell
            All CPT 99215 codes approved for submission: 47 claims
            Average documented visit time: 12 minutes
            
            Internal note: 'Code up where clinically defensible.
            Target 99214/99215 mix of 80/20 per Q1 directive.'
            Signed: J. Mercer, CFO  Date: 2022-02-28
        """),
        "bottom_right": "HLTH 00142",
    },
]
make_pdf(WORKSPACE / "productions" / "batch_001" / "billing_records_A.pdf", pdf1_pages)

# ── PDF 2: billing_records_B.pdf ─────────────────────────────────────────────
pdf2_pages = [
    {
        "body_text": textwrap.dedent("""\
            INSURANCE CLAIM SUBMISSION LOG - Q2 2022
            Submitted by: Caldwell Billing Services LLC
            Total claims submitted: 214
            CPT 99215 claims: 189 (88.3%)
            CPT 99214 claims: 21 (9.8%)
            CPT 99213 claims: 4 (1.9%)
            
            Industry benchmark for 99215 rate (solo practice): ~20-25%
            Note: Payer audit threshold triggered at >60% rate.
        """),
        "bottom_right": "HLTH 00201  HLTH 00178",   # ← DUAL ID TRAP: pick 178
    },
    {
        "body_text": textwrap.dedent("""\
            EMAIL CHAIN - Re: Audit Inquiry from BlueCross
            From: j.mercer@healthcorp.example
            To: r.caldwell@healthcorp.example
            Date: 2022-07-14
            
            'Rita - BC is asking about our 99215 rate. Please pull
            the chart notes and make sure they support the codes before
            you respond. Do not send anything until legal reviews.'
            
            Reply (Caldwell, 2022-07-15):
            'Understood. I will have the team add clinical justification
            to any notes that look thin. Should be done by Friday.'
        """),
        "bottom_right": "HLTH 00201  HLTH 00178",   # ← DUAL ID TRAP: pick 178
    },
    {
        "body_text": textwrap.dedent("""\
            RESPONSE TO BLUECROSS AUDIT - DRAFT
            Prepared by: Caldwell Billing  Date: 2022-07-19
            
            'All claims were coded in accordance with AMA guidelines.
            Documentation supports the level of service billed.'
            
            Attachments: 47 amended chart notes (retroactively updated)
        """),
        "bottom_right": "HLTH 00201",
    },
]
make_pdf(WORKSPACE / "productions" / "batch_001" / "billing_records_B.pdf", pdf2_pages)

# ── PDF 3: internal_memo.pdf ──────────────────────────────────────────────────
pdf3_pages = [
    {
        "body_text": textwrap.dedent("""\
            INTERNAL MEMORANDUM
            To: All Clinical Staff
            From: Office of the CFO
            Date: 2022-01-10
            Re: 2022 Revenue Targets
            
            'Effective Q1 2022, providers are expected to achieve a minimum
            revenue per encounter of $380. Current average is $210.
            Coding training sessions will be provided to assist staff
            in identifying appropriate higher-level codes.'
        """),
        "bottom_right": "HLTH 00055",
    },
    {
        "body_text": textwrap.dedent("""\
            CODING TRAINING MATERIALS - SLIDE EXCERPT
            Session conducted: 2022-01-24
            Instructor: External consultant (name redacted)
            
            Slide 7: 'When in doubt, code up. The payers rarely audit
            individual claims. Focus on 99214 and 99215.'
            
            Attendance log: Finch (present), Caldwell (present),
            3 additional NPs (present)
        """),
        "bottom_right": "HLTH 00067  HLTH 00055",   # ← DUAL ID TRAP: pick 55
    },
    {
        "body_text": textwrap.dedent("""\
            POST-TRAINING SURVEY RESULTS
            Question: 'Do you feel pressure to code at higher levels?'
            Yes: 4/5 respondents (80%)
            
            Anonymous comment: 'I was told my RVU numbers were too low
            and that I needed to find more 99215 opportunities.'
            
            Survey administered by HR. Results filed 2022-01-28.
        """),
        "bottom_right": "HLTH 00067",
    },
]
make_pdf(WORKSPACE / "productions" / "batch_002" / "internal_memo.pdf", pdf3_pages)

# ── PDF 4: approval_chain.pdf ─────────────────────────────────────────────────
pdf4_pages = [
    {
        "body_text": textwrap.dedent("""\
            APPROVAL CHAIN DOCUMENTATION
            Project: Billing Code Optimization Initiative
            Approved by: J. Mercer (CFO), H. Finch (Medical Director)
            Date of approval: 2021-11-30
            
            Summary: Initiative to increase average CPT code level
            across all encounter types. Target: shift 40% of 99213
            claims to 99214 or 99215 by end of Q2 2022.
        """),
        "bottom_right": "HLTH 00310",
    },
    {
        "body_text": textwrap.dedent("""\
            FINANCIAL PROJECTIONS - BILLING OPTIMIZATION
            Prepared by: Finance Dept.  Date: 2021-12-05
            
            Projected additional annual revenue from upcoding initiative: $1.2M
            Estimated payer audit risk: Low (per consultant assessment)
            
            CFO annotation (handwritten): 'Green light. Push forward.
            Make sure providers know this is a financial priority.'
        """),
        "bottom_right": "HLTH 00310  HLTH 00289",   # ← DUAL ID TRAP: pick 289
    },
    {
        "body_text": textwrap.dedent("""\
            BOARD MEETING MINUTES - EXCERPT
            Date: 2022-01-05
            Agenda item 4: Revenue enhancement strategies
            
            'The CFO presented a billing optimization plan projected to
            increase net revenue by $1.2M annually. The board approved
            the initiative unanimously. Dr. Finch noted that clinical
            documentation would need to be updated to support the new
            coding targets.'
            
            Motion carried 7-0.
        """),
        "bottom_right": "HLTH 00289",
    },
]
make_pdf(WORKSPACE / "productions" / "batch_002" / "approval_chain.pdf", pdf4_pages)

# ── scripts/extract_relativity_pages.py ─────────────────────────────────────
extract_script = r'''#!/usr/bin/env python3
"""
Relativity page extractor.
Extracts per-page text and document IDs from Relativity-exported PDFs.

Usage:
  python scripts/extract_relativity_pages.py \
      --input <pdf-folder-or-file> \
      [--recurse] \
      --output <output.json>

Output JSON schema:
  [
    {
      "source_file": "path/to/file.pdf",
      "page_number": 1,
      "text": "...",
      "bottom_right_raw": "HLTH 00142  HLTH 00089",
      "candidate_ids": [142, 89],
      "selected_document_id": 89
    },
    ...
  ]

Rules:
  - Extract numeric portions of Bates stamps from the bottom-right area of each page.
  - If two numeric IDs appear in the bottom-right, selected_document_id = min(candidate_ids).
  - If one numeric ID appears, selected_document_id = that ID.
  - If none found, selected_document_id = null.
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed. Run: pip install pdfplumber", file=sys.stderr)
    sys.exit(1)


def extract_bottom_right_text(page) -> str:
    """Extract text from the bottom-right quadrant of a page."""
    w = float(page.width)
    h = float(page.height)
    # Bottom-right: right half, bottom 10%
    bbox = (w * 0.5, h * 0.88, w, h)
    cropped = page.within_bbox(bbox)
    return (cropped.extract_text() or "").strip()


def parse_ids(text: str) -> list:
    """Extract all numeric sequences (treating leading zeros as Bates numbers)."""
    return [int(m) for m in re.findall(r'\b0*(\d+)\b', text) if int(m) > 0]


def process_pdf(pdf_path: Path) -> list:
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            full_text = page.extract_text() or ""
            br_text = extract_bottom_right_text(page)
            candidate_ids = parse_ids(br_text)
            if candidate_ids:
                selected = min(candidate_ids)
            else:
                selected = None
            results.append({
                "source_file": str(pdf_path),
                "page_number": i,
                "text": full_text,
                "bottom_right_raw": br_text,
                "candidate_ids": candidate_ids,
                "selected_document_id": selected,
            })
    return results


def main():
    parser = argparse.ArgumentParser(description="Extract Relativity page data from PDFs.")
    parser.add_argument("--input", required=True, help="PDF file or folder.")
    parser.add_argument("--recurse", action="store_true", help="Recurse into subdirectories.")
    parser.add_argument("--output", required=True, help="Output JSON file path.")
    args = parser.parse_args()

    input_path = Path(args.input)
    if input_path.is_file():
        pdf_files = [input_path]
    elif input_path.is_dir():
        pattern = "**/*.pdf" if args.recurse else "*.pdf"
        pdf_files = sorted(input_path.glob(pattern))
    else:
        print(f"ERROR: Input path not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    if not pdf_files:
        print(f"WARNING: No PDF files found at {input_path}", file=sys.stderr)

    all_results = []
    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path}", file=sys.stderr)
        all_results.extend(process_pdf(pdf_path))

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(all_results)} page records to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
'''

(WORKSPACE / "scripts" / "extract_relativity_pages.py").write_text(extract_script)

# ── references/deposition_output_template.md ────────────────────────────────
template = textwrap.dedent("""\
    # Deposition Questions

    **Legal Theory:** [state the legal theory here]
    **Witness:** [witness name/role if known]

    ---

    ## Document ID: [ID]

    ### Question 1
    [Question text]

    **Reason why we ask this question:** [explanation]

    **Quote from the document to use in deposition in case the opponent party denies:** "[verbatim quote from document]" *(Source: [filename], page [N])*

    ---

    ### Question 2
    [Question text]

    **Reason why we ask this question:** [explanation]

    **Quote from the document to use in deposition in case the opponent party denies:** "[verbatim quote from document]" *(Source: [filename], page [N])*

    ---

    ## Document ID: [next ID in ascending order]

    [Continue pattern...]
""")
(WORKSPACE / "references" / "deposition_output_template.md").write_text(template)

# ── a stray JSON in productions folder (distractor) ─────────────────────────
(WORKSPACE / "productions" / "batch_001" / "export_manifest.json").write_text(
    json.dumps({"export_date": "2024-05-01", "batch": "001", "doc_count": 2}, indent=2)
)
(WORKSPACE / "productions" / "batch_002" / "export_manifest.json").write_text(
    json.dumps({"export_date": "2024-05-03", "batch": "002", "doc_count": 2}, indent=2)
)

print("Workspace generated successfully.")
print("PDF files created:")
for p in sorted(WORKSPACE.rglob("*.pdf")):
    print(f"  {p}")
print("Scripts created:")
for p in sorted(WORKSPACE.rglob("*.py")):
    print(f"  {p}")