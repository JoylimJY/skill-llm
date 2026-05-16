#!/usr/bin/env python3
"""
Evaluation script for the document digitization audit task.
Checks:
1. Skill was installed/used correctly (node_modules exist in workspace copy)
2. All 6 documents were converted to .md files
3. Each .md file has non-trivial content (not empty, meaningful text)
4. conversion_manifest.json exists and has correct structure
5. Manifest contains valid stats for each file (lines, words, characters)
6. .doc files (especially NDA with Chinese) were actually processed
7. Manifest accurately reflects success/failure for each document
"""

import sys
import json
import os
from pathlib import Path

def run_eval(workspace):
    checks = []
    total_score = 0.0
    max_score = 0.0

    def check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal total_score, max_score
        max_score += weight
        if passed:
            total_score += weight

    workspace = Path(workspace)

    # ── Check 1: Skill was copied and dependencies installed ──────────────
    # The agent must have copied the skill from /root/.openclaw/... to workspace
    # and run npm install
    skill_in_workspace = list(workspace.rglob('openclaw-skill.js'))
    skill_node_modules = [p for p in skill_in_workspace 
                          if (p.parent / 'node_modules').exists()]
    
    check(
        "skill_installed_in_workspace",
        len(skill_node_modules) > 0,
        f"Found openclaw-skill.js with node_modules at: {[str(p.parent) for p in skill_node_modules]}"
        if skill_node_modules else
        "No openclaw-skill.js found in workspace with node_modules installed. "
        "Agent must copy skill from /root/.openclaw/workspace/office-to-md-v2/office-to-md "
        "and run npm install.",
        weight=2.0
    )

    # ── Check 2: All 6 target documents converted to .md ──────────────────
    target_docs = [
        "contracts/active/merger_agreement_v3.docx",
        "archive/hr/onboarding/employment_contract_2024.docx",
        "archive/finance/reports/Q4_2023_financial_summary.pdf",
        "presentations/board/2024_strategy_board_deck.pptx",
        "contracts/expired/service_agreement_2019.doc",
        "archive/legal/2023/q3/nda_template_chinese_client.doc",
    ]
    
    expected_md_files = [
        str(workspace / doc.rsplit('.', 1)[0] + '.md')
        for doc in target_docs
    ]
    
    md_conversion_results = {}
    for doc, md_path in zip(target_docs, expected_md_files):
        exists = os.path.exists(md_path)
        content = ""
        if exists:
            try:
                with open(md_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            except Exception as e:
                content = f"ERROR reading: {e}"
        md_conversion_results[doc] = {
            "md_path": md_path,
            "exists": exists,
            "content_len": len(content),
            "content_sample": content[:100] if content else ""
        }

    converted_count = sum(1 for r in md_conversion_results.values() if r["exists"] and r["content_len"] > 10)
    
    check(
        "all_six_documents_converted",
        converted_count == 6,
        f"{converted_count}/6 documents converted to .md. Details: " +
        "; ".join(f"{k}: {'✓' if v['exists'] and v['content_len']>10 else '✗'} ({v['content_len']}chars)" 
                  for k, v in md_conversion_results.items()),
        weight=3.0
    )

    # Check individual conversions with partial credit
    for doc, result in md_conversion_results.items():
        doc_name = doc.split('/')[-1]
        ext = doc.split('.')[-1]
        passed = result["exists"] and result["content_len"] > 10
        check(
            f"conversion_{doc_name}",
            passed,
            f"MD file {'exists' if result['exists'] else 'missing'}, "
            f"content length: {result['content_len']}, "
            f"sample: {result['content_sample'][:60]}",
            weight=1.0
        )

    # ── Check 3: .doc files specifically converted (requires word-extractor) ──
    doc_nda_md = workspace / "archive/legal/2023/q3/nda_template_chinese_client.md"
    doc_service_md = workspace / "contracts/expired/service_agreement_2019.md"
    
    nda_content = ""
    service_content = ""
    try:
        if doc_nda_md.exists():
            nda_content = doc_nda_md.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        nda_content = ""
    
    try:
        if doc_service_md.exists():
            service_content = doc_service_md.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        service_content = ""

    # NDA should contain either Chinese chars or the English content
    nda_has_content = len(nda_content) > 20 and (
        "NDA" in nda_content or 
        "Non-Disclosure" in nda_content or 
        "Disclosure" in nda_content or
        "保密" in nda_content or
        "agreement" in nda_content.lower() or
        len(nda_content) > 50
    )
    
    check(
        "doc_nda_has_meaningful_content",
        nda_has_content,
        f"NDA .doc -> .md content check. Length: {len(nda_content)}, "
        f"Sample: {nda_content[:80] if nda_content else 'EMPTY'}",
        weight=1.5
    )

    service_has_content = len(service_content) > 20 and (
        "SERVICE" in service_content.upper() or 
        "Agreement" in service_content or
        "payment" in service_content.lower() or
        len(service_content) > 50
    )
    
    check(
        "doc_service_agreement_has_meaningful_content",
        service_has_content,
        f"Service agreement .doc -> .md content check. Length: {len(service_content)}, "
        f"Sample: {service_content[:80] if service_content else 'EMPTY'}",
        weight=1.5
    )

    # ── Check 4: conversion_manifest.json exists ──────────────────────────
    manifest_candidates = list(workspace.rglob('conversion_manifest.json'))
    manifest_path = manifest_candidates[0] if manifest_candidates else None
    
    check(
        "conversion_manifest_exists",
        manifest_path is not None,
        f"conversion_manifest.json found at: {manifest_path}" 
        if manifest_path else "conversion_manifest.json not found anywhere in workspace",
        weight=2.0
    )

    # ── Check 5: Manifest has correct structure ────────────────────────────
    manifest = None
    manifest_parse_error = None
    if manifest_path:
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        except Exception as e:
            manifest_parse_error = str(e)

    check(
        "manifest_is_valid_json",
        manifest is not None,
        f"Manifest parsed successfully" if manifest else f"Manifest JSON parse error: {manifest_parse_error}",
        weight=1.0
    )

    # ── Check 6: Manifest has entries for all 6 documents ─────────────────
    if manifest is not None:
        # The manifest should be a list or dict with entries for each document
        # Accept various reasonable structures:
        # - List of objects: [{file: ..., success: ..., ...}]
        # - Dict with file keys: {filename: {stats: ...}, ...}
        
        manifest_entries = []
        if isinstance(manifest, list):
            manifest_entries = manifest
        elif isinstance(manifest, dict):
            # Could be {results: [...]} or {file1: {...}, file2: {...}}
            if 'results' in manifest:
                manifest_entries = manifest['results']
            elif 'conversions' in manifest:
                manifest_entries = manifest['conversions']
            elif 'documents' in manifest:
                manifest_entries = manifest['documents']
            else:
                # Treat dict values as entries
                manifest_entries = list(manifest.values())

        # Check we have roughly 6 entries (or 6 meaningful keys)
        entry_count = len(manifest_entries)
        
        # Also check if manifest has any string keys pointing to the target docs
        def manifest_covers_docs(m, docs):
            """Check if manifest references all target documents by name."""
            manifest_str = json.dumps(m).lower()
            covered = 0
            for doc in docs:
                basename = doc.split('/')[-1].replace('.doc', '').replace('.docx', '').replace('.pdf', '').replace('.pptx', '').lower()
                if basename in manifest_str or doc.split('/')[-1].lower() in manifest_str:
                    covered += 1
            return covered

        docs_covered = manifest_covers_docs(manifest, target_docs)
        
        check(
            "manifest_covers_all_six_documents",
            docs_covered >= 5,  # Allow 5/6 in case of one failed conversion
            f"Manifest references {docs_covered}/6 target document names. "
            f"Entry count: {entry_count}. Manifest keys: {list(manifest.keys())[:10] if isinstance(manifest, dict) else 'list'}",
            weight=2.0
        )

        # ── Check 7: Manifest has meaningful statistics ────────────────────
        manifest_str = json.dumps(manifest)
        has_stats = (
            'lines' in manifest_str or 
            'words' in manifest_str or 
            'characters' in manifest_str or
            'stats' in manifest_str or
            'word_count' in manifest_str or
            'line_count' in manifest_str
        )
        
        check(
            "manifest_contains_statistics",
            has_stats,
            f"Manifest contains text statistics (lines/words/characters): {has_stats}. "
            f"Manifest sample: {manifest_str[:200]}",
            weight=1.5
        )

        # ── Check 8: Success/failure status in manifest ────────────────────
        has_status = (
            'success' in manifest_str or 
            'status' in manifest_str or
            'failed' in manifest_str or
            'error' in manifest_str or
            'converted' in manifest_str
        )
        
        check(
            "manifest_has_success_status",
            has_status,
            f"Manifest tracks conversion success/failure status: {has_status}",
            weight=1.0
        )

        # ── Check 9: At least one numeric stat value is non-zero and plausible ──
        try:
            import re
            numbers = [int(x) for x in re.findall(r'\b(\d{2,6})\b', manifest_str)]
            has_plausible_stats = any(n > 5 for n in numbers)
            check(
                "manifest_has_plausible_numeric_stats",
                has_plausible_stats,
                f"Manifest contains plausible numeric values (>5): {sorted(set(numbers))[:10]}",
                weight=1.0
            )
        except Exception as e:
            check(
                "manifest_has_plausible_numeric_stats",
                False,
                f"Error checking numeric stats: {e}",
                weight=1.0
            )
    else:
        # Manifest not available - add failing checks
        for name, weight in [
            ("manifest_covers_all_six_documents", 2.0),
            ("manifest_contains_statistics", 1.5),
            ("manifest_has_success_status", 1.0),
            ("manifest_has_plausible_numeric_stats", 1.0),
        ]:
            check(name, False, "Manifest not available for evaluation", weight=weight)

    # ── Check 10: PPTX conversion worked (requires python-pptx) ──────────
    pptx_md = workspace / "presentations/board/2024_strategy_board_deck.md"
    pptx_content = ""
    try:
        if pptx_md.exists():
            pptx_content = pptx_md.read_text(encoding='utf-8', errors='replace')
    except Exception:
        pass
    
    pptx_meaningful = len(pptx_content) > 30 and (
        "Strategic" in pptx_content or 
        "Board" in pptx_content or
        "2024" in pptx_content or
        "Revenue" in pptx_content or
        "roadmap" in pptx_content.lower() or
        len(pptx_content) > 100
    )
    
    check(
        "pptx_conversion_meaningful_content",
        pptx_meaningful,
        f"PPTX .md content check (requires python-pptx). Length: {len(pptx_content)}, "
        f"Sample: {pptx_content[:100] if pptx_content else 'EMPTY'}",
        weight=1.5
    )

    # ── Final scoring ──────────────────────────────────────────────────────
    final_score = round(total_score / max_score, 3) if max_score > 0 else 0.0
    overall_passed = (
        final_score >= 0.70 and
        # Must have converted at least 5/6 documents
        converted_count >= 5 and
        # Must have manifest
        manifest is not None and
        # Skill must have been properly installed
        len(skill_node_modules) > 0
    )

    return {
        "passed": overall_passed,
        "score": final_score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "setup", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    result = run_eval(sys.argv[1])
    print(json.dumps(result, indent=2))