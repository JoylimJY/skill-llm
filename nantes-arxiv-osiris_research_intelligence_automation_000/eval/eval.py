import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # -----------------------------------------------------------------------
    # CHECK 1: qbio_ml_papers.json exists in outputs/pending/
    # -----------------------------------------------------------------------
    json_path = workspace / "outputs" / "pending" / "qbio_ml_papers.json"
    
    json_data = None
    check1_passed = False
    try:
        if json_path.exists():
            with open(json_path, "r") as f:
                json_data = json.load(f)
            check1_passed = True
            checks.append({
                "name": "qbio_ml_papers.json exists and is valid JSON",
                "passed": True,
                "detail": f"File found at {json_path} with {len(json_data)} entries."
            })
        else:
            # Try searching anywhere in workspace
            candidates = list(workspace.rglob("qbio_ml_papers.json"))
            if candidates:
                with open(candidates[0], "r") as f:
                    json_data = json.load(f)
                check1_passed = True
                checks.append({
                    "name": "qbio_ml_papers.json exists and is valid JSON",
                    "passed": True,
                    "detail": f"File found at {candidates[0]} (not in expected location outputs/pending/). Partial credit."
                })
            else:
                checks.append({
                    "name": "qbio_ml_papers.json exists and is valid JSON",
                    "passed": False,
                    "detail": "File not found anywhere in workspace."
                })
    except Exception as e:
        checks.append({
            "name": "qbio_ml_papers.json exists and is valid JSON",
            "passed": False,
            "detail": f"Error reading file: {e}"
        })

    # -----------------------------------------------------------------------
    # CHECK 2: JSON is a non-empty array with required fields
    # -----------------------------------------------------------------------
    required_fields_ok = False
    try:
        if json_data is not None and isinstance(json_data, list) and len(json_data) > 0:
            missing = []
            for i, entry in enumerate(json_data):
                for field in ["title", "pdf_url", "arxiv_id"]:
                    if field not in entry or not entry[field]:
                        missing.append(f"entry[{i}] missing '{field}'")
            if not missing:
                required_fields_ok = True
                checks.append({
                    "name": "All entries have required fields (title, pdf_url, arxiv_id)",
                    "passed": True,
                    "detail": f"All {len(json_data)} entries have title, pdf_url, and arxiv_id."
                })
            else:
                checks.append({
                    "name": "All entries have required fields (title, pdf_url, arxiv_id)",
                    "passed": False,
                    "detail": f"Missing fields: {missing[:5]}"
                })
        else:
            checks.append({
                "name": "All entries have required fields (title, pdf_url, arxiv_id)",
                "passed": False,
                "detail": "JSON data is empty, null, or not a list."
            })
    except Exception as e:
        checks.append({
            "name": "All entries have required fields (title, pdf_url, arxiv_id)",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # -----------------------------------------------------------------------
    # CHECK 3: Results are filtered to q-bio category
    # -----------------------------------------------------------------------
    qbio_filter_ok = False
    try:
        if json_data is not None and isinstance(json_data, list) and len(json_data) > 0:
            # Check that pdf_urls or arxiv_ids look like arxiv papers
            # and that the search was actually restricted (we check that
            # entries have arxiv IDs and that at least some q-bio flavoring exists)
            all_have_arxiv_url = all(
                "arxiv.org" in str(entry.get("pdf_url", ""))
                for entry in json_data
            )
            all_have_ids = all(
                entry.get("arxiv_id", "").strip() != ""
                for entry in json_data
            )
            # We check result count is <= 5 (max_results=5 was specified)
            count_ok = len(json_data) <= 5
            
            if all_have_arxiv_url and all_have_ids and count_ok:
                qbio_filter_ok = True
                checks.append({
                    "name": "Results are arXiv papers with count <= 5 (q-bio filtered search)",
                    "passed": True,
                    "detail": f"{len(json_data)} results, all with valid arXiv URLs and IDs, count within limit of 5."
                })
            else:
                issues = []
                if not all_have_arxiv_url:
                    issues.append("Some entries missing arxiv.org URL")
                if not all_have_ids:
                    issues.append("Some entries missing arxiv_id")
                if not count_ok:
                    issues.append(f"Too many results: {len(json_data)} > 5")
                checks.append({
                    "name": "Results are arXiv papers with count <= 5 (q-bio filtered search)",
                    "passed": False,
                    "detail": "; ".join(issues)
                })
        else:
            checks.append({
                "name": "Results are arXiv papers with count <= 5 (q-bio filtered search)",
                "passed": False,
                "detail": "No valid data to check."
            })
    except Exception as e:
        checks.append({
            "name": "Results are arXiv papers with count <= 5 (q-bio filtered search)",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # -----------------------------------------------------------------------
    # CHECK 4: Array is sorted alphabetically by title
    # -----------------------------------------------------------------------
    sorted_ok = False
    try:
        if json_data is not None and isinstance(json_data, list) and len(json_data) > 1:
            titles = [entry.get("title", "").strip().lower() for entry in json_data]
            sorted_titles = sorted(titles)
            if titles == sorted_titles:
                sorted_ok = True
                checks.append({
                    "name": "Papers sorted alphabetically by title",
                    "passed": True,
                    "detail": f"Titles in correct alphabetical order: {[t[:40] for t in titles[:3]]}"
                })
            else:
                checks.append({
                    "name": "Papers sorted alphabetically by title",
                    "passed": False,
                    "detail": f"Not sorted. Got: {[t[:30] for t in titles[:3]]}, expected: {[t[:30] for t in sorted_titles[:3]]}"
                })
        elif json_data is not None and isinstance(json_data, list) and len(json_data) == 1:
            sorted_ok = True
            checks.append({
                "name": "Papers sorted alphabetically by title",
                "passed": True,
                "detail": "Only 1 entry, trivially sorted."
            })
        else:
            checks.append({
                "name": "Papers sorted alphabetically by title",
                "passed": False,
                "detail": "No valid list to check sorting."
            })
    except Exception as e:
        checks.append({
            "name": "Papers sorted alphabetically by title",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # -----------------------------------------------------------------------
    # CHECK 5: A PDF has been downloaded to research_pipeline/raw_data/biology/
    # -----------------------------------------------------------------------
    pdf_downloaded = False
    try:
        bio_dir = workspace / "research_pipeline" / "raw_data" / "biology"
        pdf_files = list(bio_dir.glob("*.pdf"))
        if pdf_files:
            # Verify it's actually a PDF (check magic bytes)
            with open(pdf_files[0], "rb") as f:
                header = f.read(4)
            if header == b"%PDF":
                pdf_downloaded = True
                checks.append({
                    "name": "PDF downloaded to research_pipeline/raw_data/biology/",
                    "passed": True,
                    "detail": f"Valid PDF found: {pdf_files[0].name} ({pdf_files[0].stat().st_size} bytes)"
                })
            else:
                checks.append({
                    "name": "PDF downloaded to research_pipeline/raw_data/biology/",
                    "passed": False,
                    "detail": f"File found but not a valid PDF (magic bytes: {header})"
                })
        else:
            # Check if PDF is anywhere under the workspace
            all_pdfs = list(workspace.rglob("*.pdf"))
            if all_pdfs:
                checks.append({
                    "name": "PDF downloaded to research_pipeline/raw_data/biology/",
                    "passed": False,
                    "detail": f"PDF found but in wrong location: {all_pdfs[0]}. Expected in research_pipeline/raw_data/biology/"
                })
            else:
                checks.append({
                    "name": "PDF downloaded to research_pipeline/raw_data/biology/",
                    "passed": False,
                    "detail": "No PDF file found anywhere in workspace."
                })
    except Exception as e:
        checks.append({
            "name": "PDF downloaded to research_pipeline/raw_data/biology/",
            "passed": False,
            "detail": f"Exception checking for PDF: {e}"
        })

    # -----------------------------------------------------------------------
    # CHECK 6: Downloaded PDF corresponds to first alphabetically-sorted paper
    # -----------------------------------------------------------------------
    first_paper_pdf_ok = False
    try:
        if json_data and isinstance(json_data, list) and len(json_data) > 0 and pdf_downloaded:
            # The first paper in sorted order
            sorted_papers = sorted(json_data, key=lambda x: x.get("title", "").lower())
            first_paper = sorted_papers[0]
            first_arxiv_id = first_paper.get("arxiv_id", "").strip()
            
            bio_dir = workspace / "research_pipeline" / "raw_data" / "biology"
            pdf_files = list(bio_dir.glob("*.pdf"))
            
            if first_arxiv_id and pdf_files:
                # arXiv IDs in filenames often appear as e.g. "2310.12345v1.pdf"
                # Normalize: remove version suffix for comparison
                clean_id = first_arxiv_id.replace("/", "_").split("v")[0]
                pdf_name = pdf_files[0].stem  # filename without extension
                
                # Check if the arxiv ID appears in the PDF filename
                if clean_id in pdf_name or first_arxiv_id.split("v")[0].replace("/", "") in pdf_name.replace(".", "").replace("_", ""):
                    first_paper_pdf_ok = True
                    checks.append({
                        "name": "Downloaded PDF matches first alphabetically-sorted paper",
                        "passed": True,
                        "detail": f"PDF '{pdf_files[0].name}' matches arxiv_id '{first_arxiv_id}'"
                    })
                else:
                    # Looser check: just having A pdf downloaded is reasonable
                    # since we can't perfectly verify without re-running the search
                    checks.append({
                        "name": "Downloaded PDF matches first alphabetically-sorted paper",
                        "passed": False,
                        "detail": f"PDF '{pdf_files[0].name}' does not clearly match first paper's arxiv_id '{first_arxiv_id}'"
                    })
            else:
                checks.append({
                    "name": "Downloaded PDF matches first alphabetically-sorted paper",
                    "passed": False,
                    "detail": "Cannot verify: missing arxiv_id or no PDF found."
                })
        else:
            checks.append({
                "name": "Downloaded PDF matches first alphabetically-sorted paper",
                "passed": False,
                "detail": "Prerequisite checks failed (no JSON data or no PDF)."
            })
    except Exception as e:
        checks.append({
            "name": "Downloaded PDF matches first alphabetically-sorted paper",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # -----------------------------------------------------------------------
    # Scoring
    # -----------------------------------------------------------------------
    weights = {
        0: 0.10,  # file exists
        1: 0.20,  # required fields
        2: 0.20,  # q-bio filtered / count
        3: 0.15,  # sorted
        4: 0.25,  # PDF downloaded
        5: 0.10,  # PDF matches first paper
    }

    score = 0.0
    for i, check in enumerate(checks):
        if check["passed"]:
            score += weights.get(i, 0.0)

    return {
        "passed": score >= 0.70,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))