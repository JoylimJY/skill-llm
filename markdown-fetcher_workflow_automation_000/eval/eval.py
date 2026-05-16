#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path

def load_access_log(log_path):
    entries = []
    try:
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        pass
    return entries

def find_file(workspace, filename):
    """Search workspace recursively for a file by name."""
    matches = list(Path(workspace).rglob(filename))
    if matches:
        return matches[0]
    return None

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    
    LOG_FILE = os.path.join(workspace, "logs", "mock_access.log")
    
    access_log = load_access_log(LOG_FILE)
    
    # ================================================================
    # EXPECTED BEHAVIOR PER URL:
    # URL1 (neural-plasticity-2024):
    #   markdown.new -> 503 (fail)
    #   defuddle.md -> 404 (fail)  
    #   r.jina.ai -> 200 (SUCCESS) -> content from r.jina.ai
    #
    # URL2 (quantum-entanglement-review):
    #   markdown.new -> 503 (fail)
    #   defuddle.md -> 503 (fail)
    #   r.jina.ai -> 200 (SUCCESS) -> content from r.jina.ai
    #
    # URL3 (crispr-advances-2024):
    #   markdown.new -> 503 (fail)
    #   defuddle.md -> 200 (SUCCESS) -> content from defuddle.md
    #   (r.jina.ai should NOT be called for URL3 if defuddle succeeded)
    # ================================================================
    
    EXPECTED_FILES = {
        "neural_plasticity_2024.md": {
            "url": "example-research.org/articles/neural-plasticity-2024",
            "expected_service_success": "r.jina.ai",
            "required_content_fragments": ["Neural Plasticity", "synaptic", "BDNF"],
            "content_key": "neural-plasticity-2024"
        },
        "quantum_entanglement_review.md": {
            "url": "scijournal.net/papers/quantum-entanglement-review",
            "expected_service_success": "r.jina.ai",
            "required_content_fragments": ["Quantum Entanglement", "Bell", "entanglement"],
            "content_key": "quantum-entanglement-review"
        },
        "crispr_advances_2024.md": {
            "url": "biotech-weekly.com/crispr-advances-2024",
            "expected_service_success": "defuddle.md",
            "required_content_fragments": ["CRISPR", "sickle cell", "base editing"],
            "content_key": "crispr-advances-2024"
        }
    }
    
    FULL_URLS = {
        "neural-plasticity-2024": "https://example-research.org/articles/neural-plasticity-2024",
        "quantum-entanglement-review": "https://scijournal.net/papers/quantum-entanglement-review",
        "crispr-advances-2024": "https://biotech-weekly.com/crispr-advances-2024",
    }
    
    # ---- CHECK 1: All three output files exist ----
    all_files_exist = True
    missing_files = []
    found_files = {}
    for filename in EXPECTED_FILES:
        found = find_file(workspace, filename)
        if found:
            found_files[filename] = found
        else:
            all_files_exist = False
            missing_files.append(filename)
    
    checks.append({
        "name": "all_three_markdown_files_exist",
        "passed": all_files_exist,
        "detail": f"Found: {list(found_files.keys())}, Missing: {missing_files}"
    })
    
    # ---- CHECK 2: Each file has correct Markdown content ----
    content_checks_passed = 0
    content_check_details = []
    for filename, meta in EXPECTED_FILES.items():
        if filename not in found_files:
            content_check_details.append(f"{filename}: FILE MISSING")
            continue
        try:
            content = found_files[filename].read_text(encoding="utf-8", errors="replace")
            missing_fragments = []
            for fragment in meta["required_content_fragments"]:
                if fragment.lower() not in content.lower():
                    missing_fragments.append(fragment)
            if not missing_fragments and len(content) > 200:
                content_checks_passed += 1
                content_check_details.append(f"{filename}: OK (len={len(content)})")
            else:
                content_check_details.append(
                    f"{filename}: FAIL missing_fragments={missing_fragments}, len={len(content)}"
                )
        except Exception as e:
            content_check_details.append(f"{filename}: ERROR {e}")
    
    checks.append({
        "name": "markdown_files_have_correct_content",
        "passed": content_checks_passed == 3,
        "detail": "; ".join(content_check_details)
    })
    
    # ---- CHECK 3: markdown.new was attempted FIRST for each URL (priority order compliance) ----
    # Check that markdown.new was tried for all 3 URLs
    markdown_new_urls_tried = set()
    for entry in access_log:
        if entry.get("service") == "markdown.new":
            url = entry.get("url", "")
            for key, full_url in FULL_URLS.items():
                if full_url in url or full_url.replace("https://", "") in url:
                    markdown_new_urls_tried.add(key)
    
    markdown_new_tried_all = len(markdown_new_urls_tried) >= 3
    checks.append({
        "name": "markdown_new_attempted_first_for_all_urls",
        "passed": markdown_new_tried_all,
        "detail": f"markdown.new was tried for URLs: {markdown_new_urls_tried} (need all 3: {set(FULL_URLS.keys())})"
    })
    
    # ---- CHECK 4: defuddle.md was attempted for all URLs after markdown.new failed ----
    defuddle_urls_tried = set()
    for entry in access_log:
        if entry.get("service") == "defuddle.md":
            url = entry.get("url", "")
            for key, full_url in FULL_URLS.items():
                if full_url in url or full_url.replace("https://", "") in url:
                    defuddle_urls_tried.add(key)
    
    defuddle_tried_all = len(defuddle_urls_tried) >= 3
    checks.append({
        "name": "defuddle_md_attempted_as_second_fallback",
        "passed": defuddle_tried_all,
        "detail": f"defuddle.md was tried for URLs: {defuddle_urls_tried} (need all 3)"
    })
    
    # ---- CHECK 5: Priority order respected - markdown.new called BEFORE defuddle.md BEFORE r.jina.ai per URL ----
    order_respected = True
    order_details = []
    
    for url_key, full_url in FULL_URLS.items():
        url_entries = []
        for entry in access_log:
            entry_url = entry.get("url", "")
            if full_url in entry_url or full_url.replace("https://", "") in entry_url:
                url_entries.append(entry)
        
        if not url_entries:
            order_details.append(f"{url_key}: NO LOG ENTRIES FOUND")
            order_respected = False
            continue
        
        services_in_order = [e["service"] for e in url_entries]
        
        # Verify markdown.new comes before defuddle.md comes before r.jina.ai (when present)
        service_first_seen = {}
        for i, svc in enumerate(services_in_order):
            if svc not in service_first_seen:
                service_first_seen[svc] = i
        
        valid_order = True
        if "defuddle.md" in service_first_seen and "markdown.new" in service_first_seen:
            if service_first_seen["defuddle.md"] < service_first_seen["markdown.new"]:
                valid_order = False
                order_details.append(f"{url_key}: WRONG ORDER - defuddle.md before markdown.new")
        
        if "r.jina.ai" in service_first_seen and "markdown.new" in service_first_seen:
            if service_first_seen["r.jina.ai"] < service_first_seen["markdown.new"]:
                valid_order = False
                order_details.append(f"{url_key}: WRONG ORDER - r.jina.ai before markdown.new")
        
        if "r.jina.ai" in service_first_seen and "defuddle.md" in service_first_seen:
            if service_first_seen["r.jina.ai"] < service_first_seen["defuddle.md"]:
                valid_order = False
                order_details.append(f"{url_key}: WRONG ORDER - r.jina.ai before defuddle.md")
        
        if valid_order:
            order_details.append(f"{url_key}: order OK -> {services_in_order}")
        else:
            order_respected = False
    
    checks.append({
        "name": "priority_order_respected_per_url",
        "passed": order_respected,
        "detail": "; ".join(order_details)
    })
    
    # ---- CHECK 6: r.jina.ai NOT called for crispr URL (defuddle.md succeeded) ----
    rjina_called_for_crispr = False
    for entry in access_log:
        if entry.get("service") == "r.jina.ai":
            url = entry.get("url", "")
            if "crispr" in url or "biotech-weekly" in url:
                rjina_called_for_crispr = True
                break
    
    checks.append({
        "name": "no_unnecessary_rjina_call_when_defuddle_succeeded",
        "passed": not rjina_called_for_crispr,
        "detail": (
            "r.jina.ai was NOT called for crispr URL after defuddle.md succeeded (correct)"
            if not rjina_called_for_crispr
            else "r.jina.ai was INCORRECTLY called for crispr URL even though defuddle.md returned 200"
        )
    })
    
    # ---- CHECK 7: r.jina.ai was successfully used for neural-plasticity and quantum URLs ----
    rjina_success_urls = set()
    for entry in access_log:
        if entry.get("service") == "r.jina.ai" and entry.get("status") == 200:
            url = entry.get("url", "")
            if "neural-plasticity" in url or "example-research" in url:
                rjina_success_urls.add("neural-plasticity-2024")
            if "quantum-entanglement" in url or "scijournal" in url:
                rjina_success_urls.add("quantum-entanglement-review")
    
    rjina_used_correctly = len(rjina_success_urls) >= 2
    checks.append({
        "name": "rjina_used_as_fallback_for_defuddle_failures",
        "passed": rjina_used_correctly,
        "detail": f"r.jina.ai successfully used for: {rjina_success_urls} (need neural-plasticity-2024 and quantum-entanglement-review)"
    })
    
    # ---- Final scoring ----
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total
    
    # Overall pass: must pass files exist + content correct + order respected + unnecessary call avoided
    critical_checks = [
        "all_three_markdown_files_exist",
        "markdown_files_have_correct_content",
        "priority_order_respected_per_url",
        "no_unnecessary_rjina_call_when_defuddle_succeeded",
    ]
    overall_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    
    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()