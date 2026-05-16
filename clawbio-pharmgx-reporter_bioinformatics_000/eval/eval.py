import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # ── 1. Find the output markdown report ──────────────────────────────────
    # The agent was asked to produce pharmgx_report.md
    # The tool is invoked as: python pharmgx_reporter.py --input <file> --output pharmgx_report
    # which produces pharmgx_report.md
    report_files = list(workspace_path.rglob("pharmgx_report.md"))
    report_found = len(report_files) > 0

    checks.append({
        "name": "report_file_exists",
        "passed": report_found,
        "detail": f"Found pharmgx_report.md at: {[str(f) for f in report_files]}" if report_found
                  else "pharmgx_report.md not found anywhere in workspace."
    })

    if not report_found:
        # Try to find ANY .md file that might be the report
        all_md = list(workspace_path.rglob("*.md"))
        non_distractor_md = [f for f in all_md if "pharmgx" in f.name.lower() or "report" in f.name.lower()]
        checks.append({
            "name": "report_file_alternate_search",
            "passed": False,
            "detail": f"No pharmgx_report.md found. Other .md files: {[str(f) for f in all_md[:10]]}"
        })
        score = 0.0 if not non_distractor_md else 0.1
        return {"passed": False, "score": score, "checks": checks}

    report_path = report_files[0]

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "report_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "report_readable",
        "passed": True,
        "detail": f"Report is {len(content)} characters long."
    })

    content_lower = content.lower()

    # ── 2. Check report is non-trivial (has substantial content) ─────────────
    is_substantial = len(content) > 500
    checks.append({
        "name": "report_substantial_content",
        "passed": is_substantial,
        "detail": f"Report length: {len(content)} chars. Expected > 500."
    })

    # ── 3. Check pharmacogenomic genes are mentioned ──────────────────────────
    expected_genes = ["CYP2C19", "CYP2D6", "CYP2C9", "VKORC1", "SLCO1B1", "TPMT"]
    genes_found = [g for g in expected_genes if g.lower() in content_lower]
    gene_coverage = len(genes_found) >= 3
    checks.append({
        "name": "pharmacogenomic_genes_present",
        "passed": gene_coverage,
        "detail": f"Genes found in report: {genes_found} (need at least 3 of {expected_genes})"
    })

    # ── 4. Check for metabolizer phenotype language ───────────────────────────
    metabolizer_terms = ["metabolizer", "phenotype", "intermediate", "poor", "rapid", "normal", "ultrarapid"]
    metabolizer_hits = [t for t in metabolizer_terms if t in content_lower]
    has_metabolizer = len(metabolizer_hits) >= 2
    checks.append({
        "name": "metabolizer_phenotype_content",
        "passed": has_metabolizer,
        "detail": f"Metabolizer terms found: {metabolizer_hits}"
    })

    # ── 5. Check for drug recommendations / CPIC content ─────────────────────
    drug_terms = [
        "clopidogrel", "warfarin", "simvastatin", "codeine", "citalopram",
        "amitriptyline", "omeprazole", "fluorouracil", "azathioprine",
        "drug", "recommendation", "cpic", "medication", "dose"
    ]
    drug_hits = [t for t in drug_terms if t in content_lower]
    has_drugs = len(drug_hits) >= 3
    checks.append({
        "name": "drug_recommendations_present",
        "passed": has_drugs,
        "detail": f"Drug/recommendation terms found: {drug_hits[:10]}"
    })

    # ── 6. Check for star allele notation (e.g., *1, *2, *3) ─────────────────
    star_allele_pattern = re.search(r'\*\d+', content)
    has_star_alleles = star_allele_pattern is not None
    checks.append({
        "name": "star_allele_notation_present",
        "passed": has_star_alleles,
        "detail": f"Star allele notation found: {bool(star_allele_pattern)}. "
                  f"Example match: {star_allele_pattern.group(0) if star_allele_pattern else 'None'}"
    })

    # ── 7. Check markdown structure (headers) ────────────────────────────────
    markdown_headers = re.findall(r'^#{1,3}\s+.+', content, re.MULTILINE)
    has_structure = len(markdown_headers) >= 3
    checks.append({
        "name": "markdown_structure_headers",
        "passed": has_structure,
        "detail": f"Found {len(markdown_headers)} markdown headers: {markdown_headers[:5]}"
    })

    # ── 8. Check the correct input file was used (23andMe format parsed) ─────
    # If the tool ran successfully on the 23andMe file, the report should reference
    # at least one of the rsIDs we embedded, OR contain genotype data
    key_rsids = ["rs4244285", "rs3892097", "rs1799853", "rs9923231", "rs4149056"]
    rsid_hits = [r for r in key_rsids if r in content]
    # Also check for genotype notation
    genotype_pattern = re.search(r'\b[ACGT]{1,2}/[ACGT]{1,2}\b', content)
    has_genetic_data = len(rsid_hits) > 0 or genotype_pattern is not None
    checks.append({
        "name": "genetic_data_in_report",
        "passed": has_genetic_data,
        "detail": f"rsIDs found in report: {rsid_hits}. Genotype pattern present: {bool(genotype_pattern)}"
    })

    # ── 9. Check report is actually markdown (not just an error message) ──────
    not_error = "error" not in content_lower[:200] and "traceback" not in content_lower[:500]
    checks.append({
        "name": "report_not_error_output",
        "passed": not_error,
        "detail": f"First 200 chars: {content[:200]!r}"
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    critical_checks = [
        "report_file_exists",
        "report_substantial_content",
        "pharmacogenomic_genes_present",
        "metabolizer_phenotype_content",
        "drug_recommendations_present",
        "star_allele_notation_present",
    ]
    all_checks_map = {c["name"]: c["passed"] for c in checks}

    critical_passed = sum(1 for name in critical_checks if all_checks_map.get(name, False))
    total_passed = sum(1 for c in checks if c["passed"])

    score = round(
        0.6 * (critical_passed / len(critical_checks)) +
        0.4 * (total_passed / len(checks)),
        3
    )

    overall_passed = critical_passed >= 5 and all_checks_map.get("report_file_exists", False)

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))