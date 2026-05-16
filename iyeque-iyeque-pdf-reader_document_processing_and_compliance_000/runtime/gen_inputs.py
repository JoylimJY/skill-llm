import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "skills/pdf-reader",
    "regulatory/submissions/2024/Q1",
    "regulatory/submissions/2024/Q2",
    "regulatory/archive/2023",
    "regulatory/templates",
    "data/raw/clinical_trials",
    "data/processed",
    "logs",
    "config",
    "reports/drafts",
    "reports/final",
    "tools/scripts",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
(workspace / "config" / "db_config.yaml").write_text(
    "host: localhost\nport: 5432\ndb: compliance_db\n"
)
(workspace / "config" / "audit_settings.json").write_text(
    json.dumps({"max_audit_pages": 2, "output_format": "json"}, indent=2)
)
(workspace / "logs" / "audit_2024_01.log").write_text(
    "2024-01-10 INFO Audit started\n2024-01-10 INFO 3 documents processed\n"
)
(workspace / "logs" / "errors.log").write_text(
    "2024-01-10 ERROR File missing: trial_004.pdf\n"
)
(workspace / "regulatory" / "templates" / "submission_template.txt").write_text(
    "TITLE: {title}\nAUTHOR: {author}\nDATE: {date}\nSUMMARY: {summary}\n"
)
(workspace / "regulatory" / "archive" / "2023" / "index.csv").write_text(
    "doc_id,filename,status\n001,trial_2023_01.pdf,archived\n002,trial_2023_02.pdf,archived\n"
)
(workspace / "data" / "processed" / "metadata_cache.json").write_text(
    json.dumps({"last_run": "2024-01-09", "count": 0})
)
(workspace / "tools" / "scripts" / "batch_rename.sh").write_text(
    "#!/bin/bash\nfor f in *.pdf; do mv \"$f\" \"renamed_$f\"; done\n"
)
(workspace / "reports" / "drafts" / "draft_audit_notes.txt").write_text(
    "Notes: Need to confirm author fields match EMA submission requirements.\n"
)
(workspace / "regulatory" / "submissions" / "2024" / "Q2" / "placeholder.txt").write_text(
    "Q2 submissions pending.\n"
)

# ── reader.py (the skill script) ─────────────────────────────────────────────
reader_py = r'''#!/usr/bin/env python3
import sys
import json
import argparse

try:
    import pymupdf as fitz
except ImportError:
    import fitz


def extract(file_path, max_pages=None):
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        print(f"Error opening file: {e}", file=sys.stderr)
        sys.exit(1)

    if doc.is_encrypted:
        print("Error: PDF is encrypted and requires a password.", file=sys.stderr)
        sys.exit(1)

    pages = doc.page_count if max_pages is None else min(max_pages, doc.page_count)
    text_parts = []
    for i in range(pages):
        page = doc[i]
        text_parts.append(page.get_text())
    print("".join(text_parts), end="")


def metadata(file_path):
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        print(f"Error opening file: {e}", file=sys.stderr)
        sys.exit(1)

    if doc.is_encrypted:
        print("Error: PDF is encrypted and requires a password.", file=sys.stderr)
        sys.exit(1)

    meta = doc.metadata
    output = {
        "title":        meta.get("title", ""),
        "author":       meta.get("author", ""),
        "subject":      meta.get("subject", ""),
        "creator":      meta.get("creator", ""),
        "producer":     meta.get("producer", ""),
        "creationDate": meta.get("creationDate", ""),
        "modDate":      meta.get("modDate", ""),
        "format":       doc.name + " / " + str(doc.pdf_version()),
        "encryption":   doc.encryption_method if doc.is_encrypted else "none",
        "page_count":   doc.page_count,
    }
    print(json.dumps(output, indent=2))


def main():
    parser = argparse.ArgumentParser(description="PDF Reader Skill")
    subparsers = parser.add_subparsers(dest="command")

    extract_parser = subparsers.add_parser("extract")
    extract_parser.add_argument("file_path")
    extract_parser.add_argument("--max_pages", type=int, default=None)

    meta_parser = subparsers.add_parser("metadata")
    meta_parser.add_argument("file_path")

    args = parser.parse_args()

    if args.command == "extract":
        extract(args.file_path, args.max_pages)
    elif args.command == "metadata":
        metadata(args.file_path)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
'''
(workspace / "skills" / "pdf-reader" / "reader.py").write_text(reader_py)

# ── Generate realistic clinical-trial PDFs ───────────────────────────────────
# We use reportlab to create multi-page PDFs with real metadata

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import io

TRIALS = [
    {
        "filename": "trial_CT2024_001.pdf",
        "title": "Phase III Efficacy of Compound XR-77 in Hypertension",
        "author": "Dr. Elena Marchetti",
        "subject": "Clinical Trial Summary",
        "creator": "TrialSoft v4.2",
        "pages": [
            # page 1 – abstract (should be captured)
            (
                "CLINICAL TRIAL REPORT\n\n"
                "Title: Phase III Efficacy of Compound XR-77 in Hypertension\n"
                "Sponsor: Helix Pharma AG\n"
                "Protocol No.: HX-2024-001\n\n"
                "ABSTRACT\n"
                "This study evaluated the efficacy and safety of Compound XR-77 "
                "in 1200 adult patients with primary hypertension over 52 weeks. "
                "Primary endpoint: reduction in systolic blood pressure >= 10 mmHg. "
                "Result: achieved in 78.3% of subjects vs 31.2% placebo (p<0.001).\n"
            ),
            # page 2 – methods (should be captured)
            (
                "METHODS\n\n"
                "Design: Randomised, double-blind, placebo-controlled.\n"
                "Dosing: XR-77 20 mg once daily for 52 weeks.\n"
                "Endpoints: SBP reduction, DBP reduction, adverse events.\n"
                "Statistical analysis: ANCOVA with baseline covariate.\n"
            ),
            # page 3 – results (should NOT be captured with max_pages=2)
            (
                "RESULTS\n\n"
                "Mean SBP reduction: 14.7 mmHg (XR-77) vs 4.5 mmHg (placebo).\n"
                "Adverse events: mild headache 12%, nausea 8%, placebo 11%/7%.\n"
                "No serious cardiac events attributable to study drug.\n"
            ),
            # page 4 – conclusion (should NOT be captured)
            (
                "CONCLUSION\n\n"
                "Compound XR-77 demonstrates superior antihypertensive efficacy "
                "with a favourable safety profile. Regulatory submission recommended.\n"
            ),
        ],
    },
    {
        "filename": "trial_CT2024_002.pdf",
        "title": "Safety Profile of BioAgent MR-22 in Type-2 Diabetes",
        "author": "Prof. Takeshi Yamamoto",
        "subject": "Adverse Event Analysis",
        "creator": "MedDoc Suite 3.1",
        "pages": [
            (
                "SAFETY ANALYSIS REPORT\n\n"
                "Title: Safety Profile of BioAgent MR-22 in Type-2 Diabetes\n"
                "Sponsor: Olympus Therapeutics Ltd.\n"
                "Protocol No.: OT-2024-022\n\n"
                "EXECUTIVE SUMMARY\n"
                "BioAgent MR-22 was administered to 850 patients with T2DM over "
                "26 weeks. The primary safety endpoint was incidence of severe "
                "hypoglycaemia. Observed rate: 0.8% (MR-22) vs 0.7% (standard care).\n"
            ),
            (
                "PATIENT POPULATION\n\n"
                "Inclusion: Adults 18-75, HbA1c 7.5-10%, no renal impairment.\n"
                "Exclusion: eGFR < 45, active hepatic disease, pregnancy.\n"
                "Mean age: 58.3 years; 54% male; mean BMI 29.1 kg/m2.\n"
            ),
            (
                "ADVERSE EVENTS TABLE\n\n"
                "Severe hypoglycaemia: 7 events (0.8%)\n"
                "GI disorders: 63 events (7.4%)\n"
                "Injection-site reactions: 42 events (4.9%)\n"
                "Withdrawals due to AE: 18 patients (2.1%)\n"
            ),
            (
                "REGULATORY IMPLICATIONS\n\n"
                "MR-22 safety profile is consistent with class expectations. "
                "Risk management plan to address GI tolerability. "
                "EMA submission package prepared for Q3 2024.\n"
            ),
        ],
    },
    {
        "filename": "trial_CT2024_003.pdf",
        "title": "Pharmacokinetics of Oral Formulation ZL-9 in Paediatric Cohort",
        "author": "Dr. Amara Osei-Bonsu",
        "subject": "PK Study Report",
        "creator": "ClinicalWriter Pro 2.0",
        "pages": [
            (
                "PHARMACOKINETIC STUDY REPORT\n\n"
                "Title: Pharmacokinetics of Oral Formulation ZL-9 in Paediatric Cohort\n"
                "Sponsor: NovaBio Sciences\n"
                "Protocol No.: NB-2024-009\n\n"
                "SYNOPSIS\n"
                "ZL-9 oral solution was evaluated in 120 paediatric patients (6-17 yrs) "
                "with juvenile idiopathic arthritis. Cmax, Tmax, AUC0-24 and t1/2 "
                "were determined after single and multiple dosing.\n"
            ),
            (
                "PK PARAMETERS (SINGLE DOSE)\n\n"
                "Cmax: 245 ng/mL (CV 28%)\n"
                "Tmax: 1.5 h (range 0.75-3.0 h)\n"
                "AUC0-24: 1820 ng*h/mL\n"
                "t1/2: 6.8 h\n"
                "Vd/F: 12.3 L/kg\n"
                "CL/F: 1.8 L/h/kg\n"
            ),
            (
                "PK PARAMETERS (MULTIPLE DOSE)\n\n"
                "Accumulation ratio: 1.35\n"
                "Steady-state Cmax: 331 ng/mL\n"
                "Steady-state AUC0-24: 2457 ng*h/mL\n"
            ),
            (
                "CONCLUSIONS\n\n"
                "ZL-9 exhibits predictable linear PK in paediatric patients. "
                "Weight-based dosing of 2 mg/kg twice daily is recommended. "
                "No dose adjustment required for mild hepatic impairment.\n"
            ),
        ],
    },
]


def make_pdf(trial: dict) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    # Set metadata
    c.setTitle(trial["title"])
    c.setAuthor(trial["author"])
    c.setSubject(trial["subject"])
    c.setCreator(trial["creator"])

    for page_text in trial["pages"]:
        c.setFont("Helvetica", 11)
        text_obj = c.beginText(2 * cm, h - 2 * cm)
        for line in page_text.split("\n"):
            text_obj.textLine(line)
        c.drawText(text_obj)
        c.showPage()

    c.save()
    return buf.getvalue()


output_dir = workspace / "data" / "raw" / "clinical_trials"
for trial in TRIALS:
    pdf_bytes = make_pdf(trial)
    (output_dir / trial["filename"]).write_bytes(pdf_bytes)

# ── Write expected trial metadata for eval reference (hidden in plain distractor) ──
expected_ref = {t["filename"]: {"title": t["title"], "author": t["author"], "subject": t["subject"]} for t in TRIALS}
(workspace / "config" / "_trial_ref.json").write_text(json.dumps(expected_ref, indent=2))

print("Workspace generation complete.")
print(f"PDFs created: {[t['filename'] for t in TRIALS]}")