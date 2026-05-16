import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def find_doc(workspace):
    """Find the architecture doc - search for any .md file that looks like the deliverable."""
    ws = Path(workspace)
    candidates = list(ws.rglob("payment_pipeline_architecture.md"))
    if candidates:
        return candidates[0]
    return None

def run_eval(workspace):
    checks = []
    total = 0
    passed_count = 0

    doc_path = find_doc(workspace)

    # Check 1: File exists
    c = check("file_exists", doc_path is not None and doc_path.exists(),
              f"Found at {doc_path}" if doc_path else "payment_pipeline_architecture.md not found anywhere in workspace")
    checks.append(c)
    total += 1
    if c["passed"]: passed_count += 1

    if not doc_path or not doc_path.exists():
        score = passed_count / total
        return {"passed": False, "score": score, "checks": checks}

    try:
        content = doc_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("file_readable", False, str(e)))
        return {"passed": False, "score": 0.0, "checks": checks}

    # Check 2: Has Overview section
    has_overview = bool(re.search(r'^##\s+Overview', content, re.MULTILINE | re.IGNORECASE))
    c = check("has_overview_section", has_overview,
              "Found '## Overview' section" if has_overview else "Missing '## Overview' section")
    checks.append(c)
    total += 1
    if c["passed"]: passed_count += 1

    # Check 3: Has Mermaid diagram block
    has_mermaid = "```mermaid" in content
    c = check("has_mermaid_block", has_mermaid,
              "Found mermaid code block" if has_mermaid else "No ```mermaid block found")
    checks.append(c)
    total += 1
    if c["passed"]: passed_count += 1

    # Check 4: Mermaid uses flowchart TD (not just any diagram)
    has_flowchart_td = bool(re.search(r'```mermaid\s*\n\s*flowchart\s+TD', content))
    c = check("mermaid_flowchart_td", has_flowchart_td,
              "Mermaid block uses 'flowchart TD'" if has_flowchart_td else "Mermaid diagram must use 'flowchart TD' syntax")
    checks.append(c)
    total += 1
    if c["passed"]: passed_count += 1

    # Check 5: Has Components section(s) with proper subsections
    has_components = bool(re.search(r'^##\s+Components', content, re.MULTILINE | re.IGNORECASE))
    c = check("has_components_section", has_components,
              "Found '## Components' section" if has_components else "Missing '## Components' section")
    checks.append(c)
    total += 1
    if c["passed"]: passed_count += 1

    # Check 6: Component subsections include Purpose, Location, Key Functions
    has_purpose = bool(re.search(r'\*\*Purpose\*\*', content))
    has_location = bool(re.search(r'\*\*Location\*\*', content))
    has_key_functions = bool(re.search(r'\*\*Key Functions\*\*', content))
    component_fields_ok = has_purpose and has_location and has_key_functions
    c = check("component_subsection_fields", component_fields_ok,
              f"Purpose={has_purpose}, Location={has_location}, KeyFunctions={has_key_functions}")
    checks.append(c)
    total += 1
    if c["passed"]: passed_count += 1

    # Check 7: Interactions subsections present with "Receives input from" and "Sends output to"
    has_interactions = bool(re.search(r'\*\*Interactions\*\*', content))
    has_receives = bool(re.search(r'Receives input from', content, re.IGNORECASE))
    has_sends = bool(re.search(r'Sends output to', content, re.IGNORECASE))
    interactions_ok = has_interactions and has_receives and has_sends
    c = check("interactions_subsection", interactions_ok,
              f"Interactions={has_interactions}, ReceivesFrom={has_receives}, SendsTo={has_sends}")
    checks.append(c)
    total += 1
    if c["passed"]: passed_count += 1

    # Check 8: Data Flow section
    has_data_flow = bool(re.search(r'^##\s+Data\s+Flow', content, re.MULTILINE | re.IGNORECASE))
    c = check("has_data_flow_section", has_data_flow,
              "Found '## Data Flow' section" if has_data_flow else "Missing '## Data Flow' section")
    checks.append(c)
    total += 1
    if c["passed"]: passed_count += 1

    # Check 9: Configuration section
    has_config = bool(re.search(r'^##\s+Configuration', content, re.MULTILINE | re.IGNORECASE))
    c = check("has_configuration_section", has_config,
              "Found '## Configuration' section" if has_config else "Missing '## Configuration' section")
    checks.append(c)
    total += 1
    if c["passed"]: passed_count += 1

    # Check 10: Code References table with 3-column format: Component | File | Key Symbols
    has_code_refs = bool(re.search(r'^##\s+Code\s+References', content, re.MULTILINE | re.IGNORECASE))
    c = check("has_code_references_section", has_code_refs,
              "Found '## Code References' section" if has_code_refs else "Missing '## Code References' section")
    checks.append(c)
    total += 1
    if c["passed"]: passed_count += 1

    # Check 11: Code References table has the right columns
    table_header_ok = bool(re.search(r'Component.*\|.*File.*\|.*Key Symbols', content, re.IGNORECASE))
    c = check("code_references_table_columns", table_header_ok,
              "Table has Component | File | Key Symbols columns" if table_header_ok
              else "Code References table missing correct columns (Component | File | Key Symbols)")
    checks.append(c)
    total += 1
    if c["passed"]: passed_count += 1

    # Check 12: Glossary section
    has_glossary = bool(re.search(r'^##\s+Glossary', content, re.MULTILINE | re.IGNORECASE))
    c = check("has_glossary_section", has_glossary,
              "Found '## Glossary' section" if has_glossary else "Missing '## Glossary' section")
    checks.append(c)
    total += 1
    if c["passed"]: passed_count += 1

    # Check 13: No absolute paths (no leading /workspace or /home etc in file references)
    # Look for absolute paths in backtick references
    abs_path_matches = re.findall(r'`/[a-zA-Z]', content)
    no_absolute_paths = len(abs_path_matches) == 0
    c = check("no_absolute_paths", no_absolute_paths,
              "No absolute paths found in document" if no_absolute_paths
              else f"Found absolute paths: {abs_path_matches[:3]}")
    checks.append(c)
    total += 1
    if c["passed"]: passed_count += 1

    # Check 14: No line number references (e.g., "line 42", "L42", ":42")
    line_num_matches = re.findall(r'(?:line\s+\d+|:\d{2,}|L\d{2,})', content, re.IGNORECASE)
    no_line_numbers = len(line_num_matches) == 0
    c = check("no_line_numbers", no_line_numbers,
              "No line number references found" if no_line_numbers
              else f"Found line number references: {line_num_matches[:3]}")
    checks.append(c)
    total += 1
    if c["passed"]: passed_count += 1

    # Check 15: No large inline code blocks (no triple-backtick blocks with >3 lines of code content)
    # The SKILL.md says "Never paste code" - detect multi-line code blocks that look like source code
    code_block_matches = re.findall(r'```(?!mermaid)[a-zA-Z]*\n(.*?)\n```', content, re.DOTALL)
    large_code_blocks = [b for b in code_block_matches if len(b.strip().splitlines()) > 3]
    no_code_pasting = len(large_code_blocks) == 0
    c = check("no_code_pasting", no_code_pasting,
              "No large inline code blocks found (code not pasted)" if no_code_pasting
              else f"Found {len(large_code_blocks)} inline code block(s) with >3 lines — SKILL.md forbids pasting code")
    checks.append(c)
    total += 1
    if c["passed"]: passed_count += 1

    # Check 16: References key system components by name (PaymentRouter, FraudEngine, LedgerService, Notifier)
    mentions_router = "PaymentRouter" in content
    mentions_fraud = "FraudEngine" in content
    mentions_ledger = "LedgerService" in content
    mentions_notifier = "Notifier" in content
    key_components_mentioned = mentions_router and mentions_fraud and mentions_ledger and mentions_notifier
    c = check("key_components_referenced", key_components_mentioned,
              f"PaymentRouter={mentions_router}, FraudEngine={mentions_fraud}, LedgerService={mentions_ledger}, Notifier={mentions_notifier}")
    checks.append(c)
    total += 1
    if c["passed"]: passed_count += 1

    # Check 17: References key source files using relative paths (src/gateway/router.py etc.)
    mentions_gateway_file = bool(re.search(r'src/gateway/router\.py', content))
    mentions_fraud_file = bool(re.search(r'src/fraud/engine\.py', content))
    mentions_ledger_file = bool(re.search(r'src/ledger/ledger_service\.py', content))
    relative_files_ok = mentions_gateway_file and mentions_fraud_file and mentions_ledger_file
    c = check("relative_file_paths_referenced", relative_files_ok,
              f"gateway/router={mentions_gateway_file}, fraud/engine={mentions_fraud_file}, ledger/ledger_service={mentions_ledger_file}")
    checks.append(c)
    total += 1
    if c["passed"]: passed_count += 1

    score = round(passed_count / total, 4)
    overall_passed = passed_count >= int(total * 0.82)  # must pass at least 82% of checks

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))