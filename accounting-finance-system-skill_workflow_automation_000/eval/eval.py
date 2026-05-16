#!/usr/bin/env python3
"""
Evaluation script for the SAP AP reconciliation guidance DOCX task.

Checks:
1. A .docx file named 'ap_reconciliation_guidance.docx' exists somewhere in the workspace.
2. The file is a valid DOCX (readable by python-docx).
3. An intermediate JSON input file (analysis.json or similar) exists and has all required schema fields.
4. The JSON has at least one source with type 'official-doc'.
5. The JSON has at least one source with all citation metadata fields (title, publisher, url, accessed).
6. The DOCX was produced with --format q-and-a (detected by presence of 'Answer: Recommended Actions'
   or 'How To Confirm Success' headings, which the q-and-a builder uses but memo does not).
7. The JSON question field is non-empty and relevant to AP/reconciliation.
8. The JSON recommended_steps has at least one step.
9. The JSON system_context references SAP or S/4HANA.
10. The DOCX does NOT appear to be a zero-byte or stub file.
"""

import sys
import json
import traceback
from pathlib import Path

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


def find_files(workspace: Path, pattern: str):
    return list(workspace.rglob(pattern))


def extract_docx_text(path: Path) -> str:
    try:
        doc = DocxDocument(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        return f"__ERROR__: {e}"


def run_checks(workspace: Path):
    checks = []

    # ── Check 1: target DOCX exists ─────────────────────────────────────────
    docx_files = find_files(workspace, "ap_reconciliation_guidance.docx")
    docx_found = len(docx_files) > 0
    checks.append({
        "name": "output_docx_exists",
        "passed": docx_found,
        "detail": f"Found {len(docx_files)} file(s) named ap_reconciliation_guidance.docx" if docx_found
                  else "No file named ap_reconciliation_guidance.docx found anywhere in workspace"
    })
    docx_path = docx_files[0] if docx_found else None

    # ── Check 2: DOCX is valid and non-empty ────────────────────────────────
    if docx_path and DOCX_AVAILABLE:
        text = extract_docx_text(docx_path)
        valid_docx = not text.startswith("__ERROR__") and len(text.strip()) > 50
        checks.append({
            "name": "output_docx_valid_and_non_empty",
            "passed": valid_docx,
            "detail": f"DOCX text length={len(text.strip())}; {'valid' if valid_docx else 'invalid or too short'}"
        })
    else:
        checks.append({
            "name": "output_docx_valid_and_non_empty",
            "passed": False,
            "detail": "DOCX not found or python-docx unavailable"
        })
        text = ""

    # ── Check 3: JSON input file exists ─────────────────────────────────────
    json_files = (
        find_files(workspace, "analysis.json") +
        find_files(workspace, "*.json")
    )
    # exclude example_report_input.json (pre-existing distractor)
    json_files = [
        f for f in json_files
        if f.name != "example_report_input.json"
        and "references" not in str(f)
    ]
    # deduplicate
    seen = set()
    unique_json = []
    for f in json_files:
        if str(f) not in seen:
            seen.add(str(f))
            unique_json.append(f)

    json_found = len(unique_json) > 0
    checks.append({
        "name": "input_json_exists",
        "passed": json_found,
        "detail": f"Found JSON candidates: {[str(f) for f in unique_json]}" if json_found
                  else "No agent-created JSON input file found"
    })

    # ── Load best JSON candidate ─────────────────────────────────────────────
    data = None
    if json_found:
        # prefer 'analysis.json', then pick the most recently modified
        preferred = [f for f in unique_json if f.name == "analysis.json"]
        candidate = preferred[0] if preferred else sorted(unique_json, key=lambda f: f.stat().st_mtime, reverse=True)[0]
        try:
            with open(candidate, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as e:
            checks.append({
                "name": "input_json_parseable",
                "passed": False,
                "detail": f"JSON parse error: {e}"
            })
            data = None
        else:
            checks.append({
                "name": "input_json_parseable",
                "passed": True,
                "detail": f"Successfully parsed {candidate}"
            })
    else:
        checks.append({
            "name": "input_json_parseable",
            "passed": False,
            "detail": "No JSON candidate to parse"
        })

    # ── Check 4: required schema fields present ──────────────────────────────
    if data is not None:
        has_question = bool(data.get("question", "").strip())
        has_sources = isinstance(data.get("sources"), list) and len(data["sources"]) >= 1
        has_steps = isinstance(data.get("recommended_steps"), list) and len(data["recommended_steps"]) >= 1
        schema_ok = has_question and has_sources and has_steps
        checks.append({
            "name": "json_required_fields_present",
            "passed": schema_ok,
            "detail": f"question={'yes' if has_question else 'MISSING'}, "
                      f"sources={'yes ('+str(len(data.get('sources',[])))+')'  if has_sources else 'MISSING'}, "
                      f"recommended_steps={'yes ('+str(len(data.get('recommended_steps',[])))+')'  if has_steps else 'MISSING'}"
        })
    else:
        checks.append({
            "name": "json_required_fields_present",
            "passed": False,
            "detail": "No data to check"
        })

    # ── Check 5: at least one official-doc source ────────────────────────────
    if data is not None:
        sources = data.get("sources", [])
        official_sources = [
            s for s in sources
            if isinstance(s, dict) and s.get("type", "").lower() == "official-doc"
        ]
        has_official = len(official_sources) >= 1
        checks.append({
            "name": "source_has_official_doc_type",
            "passed": has_official,
            "detail": f"Found {len(official_sources)} source(s) with type='official-doc'"
        })
    else:
        checks.append({
            "name": "source_has_official_doc_type",
            "passed": False,
            "detail": "No data available"
        })

    # ── Check 6: source citation metadata completeness ───────────────────────
    if data is not None:
        sources = data.get("sources", [])
        complete_sources = []
        for s in sources:
            if isinstance(s, dict):
                has_all = all([
                    s.get("title", "").strip(),
                    s.get("publisher", "").strip(),
                    s.get("url", "").strip(),
                    s.get("accessed", "").strip(),
                ])
                if has_all:
                    complete_sources.append(s.get("title"))
        meta_ok = len(complete_sources) >= 1
        checks.append({
            "name": "source_citation_metadata_complete",
            "passed": meta_ok,
            "detail": f"{len(complete_sources)} source(s) have title+publisher+url+accessed: {complete_sources}"
        })
    else:
        checks.append({
            "name": "source_citation_metadata_complete",
            "passed": False,
            "detail": "No data available"
        })

    # ── Check 7: DOCX produced in q-and-a format ─────────────────────────────
    # The q-and-a builder uses headings: "Answer: Recommended Actions" and "How To Confirm Success"
    # The memo builder uses "Recommended Steps" and "Validation Checks"
    qa_markers = ["Answer: Recommended Actions", "How To Confirm Success"]
    memo_exclusive_markers = ["Validation Checks"]  # used only by memo builder
    if docx_path and DOCX_AVAILABLE:
        full_text = text  # already extracted above
        has_qa_marker = any(m.lower() in full_text.lower() for m in qa_markers)
        has_memo_only = any(m.lower() in full_text.lower() for m in memo_exclusive_markers)
        # q-and-a format: has qa markers AND does NOT have memo-exclusive markers
        is_qa_format = has_qa_marker and not has_memo_only
        checks.append({
            "name": "docx_uses_qa_and_a_format",
            "passed": is_qa_format,
            "detail": (
                f"Q&A markers found: {has_qa_marker} "
                f"| Memo-exclusive markers found: {has_memo_only} "
                f"| Verdict: {'q-and-a format confirmed' if is_qa_format else 'NOT q-and-a format — wrong --format flag used or memo format applied'}"
            )
        })
    else:
        checks.append({
            "name": "docx_uses_qa_and_a_format",
            "passed": False,
            "detail": "DOCX not available for format check"
        })

    # ── Check 8: question is relevant to AP reconciliation ───────────────────
    if data is not None:
        q = data.get("question", "").lower()
        keywords = ["reconcil", "ap", "accounts payable", "vendor", "period", "close", "sap", "s/4"]
        matched = [kw for kw in keywords if kw in q]
        relevant = len(matched) >= 2
        checks.append({
            "name": "question_relevant_to_ap_reconciliation",
            "passed": relevant,
            "detail": f"Question: '{data.get('question','')}' | Matched keywords: {matched}"
        })
    else:
        checks.append({
            "name": "question_relevant_to_ap_reconciliation",
            "passed": False,
            "detail": "No data available"
        })

    # ── Check 9: system_context references SAP ───────────────────────────────
    if data is not None:
        ctx = data.get("system_context", {})
        ctx_str = json.dumps(ctx).lower()
        sap_mentioned = "sap" in ctx_str or "s/4" in ctx_str or "s4hana" in ctx_str
        checks.append({
            "name": "system_context_references_sap",
            "passed": sap_mentioned,
            "detail": f"system_context content: {ctx}"
        })
    else:
        checks.append({
            "name": "system_context_references_sap",
            "passed": False,
            "detail": "No data available"
        })

    # ── Check 10: DOCX mentions SAP/S4HANA in content ───────────────────────
    if docx_path and DOCX_AVAILABLE:
        sap_in_doc = "sap" in text.lower() or "s/4" in text.lower() or "s4hana" in text.lower()
        checks.append({
            "name": "docx_content_mentions_sap",
            "passed": sap_in_doc,
            "detail": "SAP/S4HANA found in DOCX text" if sap_in_doc else "No SAP reference found in DOCX body"
        })
    else:
        checks.append({
            "name": "docx_content_mentions_sap",
            "passed": False,
            "detail": "DOCX not available"
        })

    # ── Scoring ──────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])

    # weighted: format check and schema checks count double
    weighted_scores = {
        "output_docx_exists": 2,
        "output_docx_valid_and_non_empty": 1,
        "input_json_exists": 1,
        "input_json_parseable": 1,
        "json_required_fields_present": 2,
        "source_has_official_doc_type": 2,
        "source_citation_metadata_complete": 2,
        "docx_uses_qa_and_a_format": 3,   # proprietary trap — highest weight
        "question_relevant_to_ap_reconciliation": 1,
        "system_context_references_sap": 1,
        "docx_content_mentions_sap": 1,
    }
    max_weight = sum(weighted_scores.values())
    earned_weight = sum(
        weighted_scores.get(c["name"], 1)
        for c in checks if c["passed"]
    )
    score = round(earned_weight / max_weight, 4)
    overall_passed = all(
        c["passed"] for c in checks
        if c["name"] in {
            "output_docx_exists",
            "output_docx_valid_and_non_empty",
            "json_required_fields_present",
            "source_has_official_doc_type",
            "docx_uses_qa_and_a_format",
        }
    )

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks,
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation", "passed": False, "detail": "No workspace path argument provided"}
        ]}))
        sys.exit(0)

    workspace = Path(sys.argv[1])
    if not workspace.exists():
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "workspace_exists", "passed": False, "detail": f"Workspace {workspace} does not exist"}
        ]}))
        sys.exit(0)

    try:
        result = run_checks(workspace)
    except Exception:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [
                {"name": "eval_runtime_error", "passed": False, "detail": traceback.format_exc()}
            ]
        }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()